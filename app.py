import certifi
from flask import Flask, request, jsonify, render_template_string
from pymongo import MongoClient
import os
import datetime
import uuid
import random
import string

app = Flask(__name__)

# --- AYARLAR ---
ADMIN_PASSWORD = "Ata_Yasin5353"
MONGO_URI = os.environ.get("MONGO_URI") 
client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
db = client['mega_leech']
users_col = db['users']       
jobs_col = db['jobs']         
deliveries_col = db['deliveries'] 

def get_tr_time():
    return (datetime.datetime.utcnow() + datetime.timedelta(hours=3)).strftime("%d.%m.%Y %H:%M")

def get_expiry_date(days):
    return datetime.datetime.utcnow() + datetime.timedelta(days=int(days))

# --- CSS (ULTIMATE DESIGN) ---
SHARED_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Rajdhani:wght@300;500;700&display=swap');
    
    :root { --p: #00f3ff; --s: #00ff9d; --d: #ff0055; --bg: #050505; --card: rgba(15, 15, 15, 0.95); }
    
    * { box-sizing: border-box; transition: all 0.2s ease; }
    
    body {
        background-color: var(--bg);
        background-image: radial-gradient(circle at 50% 50%, rgba(0, 243, 255, 0.05), transparent 60%);
        color: #fff; font-family: 'Rajdhani', sans-serif;
        margin: 0; min-height: 100vh; display: flex; flex-direction: column; align-items: center; justify-content: center;
        overflow-x: hidden;
    }
    
    /* Hareketli Izgara */
    body::after {
        content: ""; position: fixed; top: 0; left: 0; width: 100%; height: 100%;
        background: linear-gradient(rgba(18, 16, 16, 0) 50%, rgba(0, 0, 0, 0.25) 50%), linear-gradient(90deg, rgba(255, 0, 0, 0.06), rgba(0, 255, 0, 0.02), rgba(0, 0, 255, 0.06));
        background-size: 100% 2px, 3px 100%; pointer-events: none; z-index: -1;
    }

    .glass-panel {
        background: var(--card); border: 1px solid rgba(0, 243, 255, 0.2);
        box-shadow: 0 0 40px rgba(0, 0, 0, 0.8), inset 0 0 20px rgba(0, 243, 255, 0.05);
        backdrop-filter: blur(10px); padding: 40px; border-radius: 12px;
        width: 90%; max-width: 600px; text-align: center; position: relative;
    }
    
    .glass-panel::before {
        content: ''; position: absolute; top: -1px; left: -1px; right: -1px; bottom: -1px;
        border-radius: 12px; padding: 1px; 
        background: linear-gradient(45deg, transparent, var(--p), transparent);
        -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
        -webkit-mask-composite: xor; mask-composite: exclude; pointer-events: none;
    }

    h1, h2 { font-family: 'Orbitron', sans-serif; text-transform: uppercase; letter-spacing: 3px; color: var(--p); text-shadow: 0 0 20px rgba(0, 243, 255, 0.4); margin-bottom: 5px; }
    
    input, select {
        width: 100%; padding: 15px; background: rgba(0,0,0,0.6); border: 1px solid #333;
        color: var(--p); font-family: 'Rajdhani'; font-size: 1.1rem; text-align: center;
        margin: 10px 0; border-radius: 6px; letter-spacing: 1px;
    }
    input:focus { outline: none; border-color: var(--p); box-shadow: 0 0 15px rgba(0, 243, 255, 0.2); }

    button {
        width: 100%; padding: 15px; background: rgba(0, 243, 255, 0.1); border: 1px solid var(--p);
        color: var(--p); font-family: 'Orbitron'; font-weight: bold; font-size: 1rem;
        cursor: pointer; margin-top: 10px; border-radius: 6px; text-transform: uppercase;
    }
    button:hover { background: var(--p); color: #000; box-shadow: 0 0 20px var(--p); transform: translateY(-2px); }

    .btn-danger { border-color: var(--d); color: var(--d); background: rgba(255, 0, 85, 0.1); }
    .btn-danger:hover { background: var(--d); color: #fff; box-shadow: 0 0 20px var(--d); }

    .stat-box { display: flex; justify-content: space-between; border-bottom: 1px solid #333; padding-bottom: 15px; margin-bottom: 20px; font-size: 0.9rem; color: #aaa; }
    .stat-val { color: var(--s); font-weight: bold; font-size: 1.1rem; }

    .job-item {
        background: rgba(255,255,255,0.03); border-left: 3px solid #333;
        padding: 15px; margin-bottom: 10px; text-align: left; position: relative;
    }
    .status-badge { font-size: 0.75rem; padding: 3px 8px; border-radius: 4px; background: #222; border: 1px solid #444; float: right; }
    
    .term {
        font-family: monospace; font-size: 0.8rem; color: #888; margin-top: 8px;
        background: #080808; padding: 8px; border-radius: 4px; border: 1px solid #222;
        overflow: hidden; white-space: nowrap; text-overflow: ellipsis;
    }
    
    /* Durum Renkleri */
    .st-ISLENIYOR { border-color: var(--p); } .st-ISLENIYOR .status-badge { color: var(--p); border-color: var(--p); animation: pulse 2s infinite; }
    .st-TAMAMLANDI { border-color: var(--s); } .st-TAMAMLANDI .status-badge { color: var(--s); border-color: var(--s); }
    .st-HATA { border-color: var(--d); } .st-HATA .status-badge { color: var(--d); border-color: var(--d); }
    
    @keyframes pulse { 0% { box-shadow: 0 0 0 0 rgba(0, 243, 255, 0.4); } 70% { box-shadow: 0 0 0 10px rgba(0, 243, 255, 0); } 100% { box-shadow: 0 0 0 0 rgba(0, 243, 255, 0); } }

    table { width: 100%; border-collapse: collapse; margin-top: 20px; font-size: 0.85rem; }
    th, td { padding: 10px; border: 1px solid #333; text-align: left; color: #ccc; }
    th { color: var(--p); }
</style>
"""

# --- HTML TEMPLATES ---
HTML_LOGIN = f"""<!DOCTYPE html><html><head><title>GİRİŞ - YAEL</title>{SHARED_CSS}</head><body>
<div class="glass-panel">
    <h1>SİSTEM GİRİŞİ</h1>
    <p style="color:#666; margin-bottom:30px">GÜVENLİ ERİŞİM PROTOKOLÜ</p>
    <input type="password" id="k" placeholder="ERİŞİM ANAHTARI">
    <button onclick="go()">BAĞLAN</button>
</div>
<script>
function go(){{
    let k=document.getElementById('k').value;
    let hwid=localStorage.getItem('hwid')||crypto.randomUUID(); localStorage.setItem('hwid',hwid);
    document.querySelector('button').innerText = "DOĞRULANIYOR...";
    fetch('/api/login',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{key:k,hwid:hwid}})}})
    .then(r=>r.json()).then(d=>{{
        if(d.ok){{localStorage.setItem('ukey',k); location.href='/panel'}}
        else {{alert(d.msg); document.querySelector('button').innerText = "BAĞLAN";}}
    }});
}}
</script></body></html>"""

HTML_PANEL = f"""<!DOCTYPE html><html><head><title>KONTROL PANELİ</title>{SHARED_CSS}</head><body>
<div class="glass-panel" style="max-width:800px">
    <div class="stat-box">
        <div>KULLANICI: <span id="uid" style="color:white">...</span></div>
        <div>KALAN SÜRE: <span id="days" class="stat-val">...</span> GÜN</div>
    </div>
    <div class="stat-box" style="border:none; margin-bottom:5px;">
        <div>KOTA KULLANIMI</div>
        <div class="stat-val"><span id="used">0</span> / <span id="limit">0</span> GB</div>
    </div>
    
    <div style="width:100%; height:4px; background:#222; margin-bottom:30px; border-radius:2px; overflow:hidden">
        <div id="bar" style="width:0%; height:100%; background:var(--p); box-shadow:0 0 10px var(--p); transition:width 1s"></div>
    </div>

    <input id="link" placeholder="MEGA.NZ LİNKİNİ BURAYA YAPIŞTIR...">
    <button onclick="add()">🚀 İNDİRMEYİ BAŞLAT</button>

    <div style="display:flex; justify-content:space-between; margin-top:40px; margin-bottom:10px; border-bottom:1px solid #333; padding-bottom:10px;">
        <span style="color:#666; font-weight:bold">İŞLEM GEÇMİŞİ</span>
        <span onclick="clearHist()" style="color:var(--d); cursor:pointer; font-size:0.8rem">⚠️ GEÇMİŞİ TEMİZLE</span>
    </div>
    
    <div id="jobs"></div>
    
    <button onclick="logout()" class="btn-danger" style="margin-top:30px; width:auto; padding:10px 30px;">ÇIKIŞ YAP</button>
</div>

<script>
const k=localStorage.getItem('ukey'); if(!k) location.href='/login';
document.getElementById('uid').innerText = k.substring(0,8)+'...';

function load(){{
    fetch('/api/data',{{headers:{{'X-Key':k}}}}).then(r=>r.json()).then(d=>{{
        if(d.err) return location.href='/login';
        
        document.getElementById('used').innerText = d.used.toFixed(2);
        document.getElementById('limit').innerText = d.limit;
        document.getElementById('days').innerText = d.days_left;
        
        let pct = (d.used/d.limit)*100;
        document.getElementById('bar').style.width = pct + '%';
        if(pct>90) document.getElementById('bar').style.background = 'var(--d)';

        let h="";
        d.jobs.forEach(j=>{{
            let st = j.status;
            let badge = st;
            let act = "";
            let log = j.log || "Bekleniyor...";
            
            if(st=='ISLENIYOR') {{
                badge = "İŞLENİYOR";
                act = `<span onclick="stop('${{j.id}}')" style="color:var(--d); cursor:pointer; margin-left:10px; font-size:0.8rem">[DURDUR]</span>`;
            }} else if(st=='TAMAMLANDI') {{
                badge = "HAZIR";
                act = `<a href="/teslimat/${{j.did}}" target="_blank" style="color:var(--s); text-decoration:none; margin-left:10px; font-weight:bold">[İNDİR]</a>`;
            }}

            h+=`<div class="job-item st-${{st}}">
                <div style="display:flex; justify-content:space-between">
                    <span style="font-weight:bold; color:#fff; overflow:hidden; white-space:nowrap; width:70%">${{j.link}}</span>
                    <span class="status-badge">${{badge}}</span>
                </div>
                <div class="term">> ${{log}}</div>
                <div style="text-align:right; margin-top:5px; font-size:0.8rem; color:#666">
                    ${{j.date}} ${{act}}
                </div>
            </div>`;
        }});
        document.getElementById('jobs').innerHTML = h || '<div style="color:#444; padding:20px">Henüz işlem yok.</div>';
    }});
}}

function add(){{
    let l=document.getElementById('link').value;
    if(!l) return alert("Link girmedin!");
    fetch('/api/add',{{method:'POST',headers:{{'X-Key':k,'Content-Type':'application/json'}},body:JSON.stringify({{link:l}})}})
    .then(r=>r.json()).then(d=>{{ alert(d.msg); load(); document.getElementById('link').value=''; }});
}}
function stop(id){{ if(confirm('Durdurulsun mu?')) fetch('/api/stop',{{method:'POST',headers:{{'X-Key':k,'Content-Type':'application/json'}},body:JSON.stringify({{id:id}})}}).then(()=>load()); }}
function clearHist(){{ if(confirm('Tüm geçmiş silinecek?')) fetch('/api/clear',{{headers:{{'X-Key':k}}}}).then(()=>load()); }}
function logout(){{ localStorage.removeItem('ukey'); location.href='/login'; }}
setInterval(load, 3000); load();
</script></body></html>"""

HTML_ADMIN = f"""<!DOCTYPE html><html><head><title>ADMIN</title>{SHARED_CSS}</head><body>
<div class="glass-panel" style="max-width:900px">
    <h1>YÖNETİCİ KONSOLU</h1>
    
    <div style="display:flex; gap:10px; margin-top:30px; background:rgba(0,0,0,0.5); padding:20px; border-radius:8px;">
        <input id="l" type="number" placeholder="LİMİT (GB)" value="20">
        <input id="d" type="number" placeholder="SÜRE (GÜN)" value="30">
        <button onclick="create()" style="width:150px">OLUŞTUR</button>
    </div>
    <div id="res" style="color:var(--s); font-family:monospace; font-size:1.2rem; margin:20px 0;"></div>

    <h3>MÜŞTERİ VERİTABANI</h3>
    <table id="tbl"></table>
</div>
<script>
const p = prompt("YÖNETİCİ ŞİFRESİ:");
function load(){{
    fetch('/api/admin/users?p='+p).then(r=>r.json()).then(d=>{{
        if(d.err) return document.body.innerHTML="<h1>YETKİSİZ</h1>";
        let h="<tr><th>ANAHTAR</th><th>GB</th><th>GÜN</th><th>DURUM</th><th>İŞLEM</th></tr>";
        d.users.forEach(u=>{{
            let btn = u.banned ? `<button onclick="ban('${{u.key}}',0)" style="color:#0f0;padding:5px">AÇ</button>` : `<button onclick="ban('${{u.key}}',1)" class="btn-danger" style="padding:5px">BAN</button>`;
            h+=`<tr><td>${{u.key}}</td><td>${{u.used.toFixed(1)}} / ${{u.limit}}</td><td>${{u.days_left}}</td><td>${{u.banned?'BANLI':'AKTİF'}}</td><td>${{btn}}</td></tr>`;
        }});
        document.getElementById('tbl').innerHTML=h;
    }});
}}
function create(){{
    let l=document.getElementById('l').value, d=document.getElementById('d').value;
    fetch(`/api/admin/create?p=${{p}}&l=${{l}}&d=${{d}}`).then(r=>r.text()).then(k=>{{
        document.getElementById('res').innerText = k; load();
    }});
}}
function ban(k,b){{ fetch('/api/admin/ban',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{p:p,k:k,b:b}})}}).then(()=>load()); }}
load();
</script></body></html>"""

@app.route('/')
def r1(): return render_template_string(HTML_LOGIN)
@app.route('/login')
def r2(): return render_template_string(HTML_LOGIN)
@app.route('/panel')
def r3(): return render_template_string(HTML_PANEL)
@app.route('/admin')
def r4(): return render_template_string(HTML_ADMIN)
@app.route('/teslimat/<id>')
def r5(id):
    d = deliveries_col.find_one({"id": id})
    if d: return render_template_string(d['html'])
    return "Dosya bulunamadı"

# --- API ---
@app.route('/api/login', methods=['POST'])
def api_login():
    d=request.json; u=users_col.find_one({"key":d['key']})
    if not u or u.get('banned'): return jsonify({"ok":False,"msg":"Geçersiz Anahtar"})
    
    # Süre Kontrolü
    if u.get('expire_date') and datetime.datetime.utcnow() > u['expire_date']:
        return jsonify({"ok":False,"msg":"SÜRENİZ DOLDU! Lütfen yenileyin."})

    if not u.get('hwid'): users_col.update_one({"key":d['key']},{"$set":{"hwid":d['hwid']}})
    elif u['hwid']!=d['hwid']: return jsonify({"ok":False,"msg":"Farklı cihazda oturum açılamaz!"})
    
    return jsonify({"ok":True})

@app.route('/api/data')
def api_data():
    k=request.headers.get('X-Key'); u=users_col.find_one({"key":k})
    if not u: return jsonify({"err":True})
    
    # Kalan Gün Hesaplama
    days_left = "Sınırsız"
    if u.get('expire_date'):
        diff = u['expire_date'] - datetime.datetime.utcnow()
        days_left = max(0, diff.days)

    jobs=list(jobs_col.find({"user_key":k},{'_id':0}).sort("_id",-1))
    return jsonify({
        "used":u.get('used_gb',0),
        "limit":u.get('limit_gb',10),
        "days_left": days_left,
        "jobs":[{"id":j['job_id'],"status":j['status'],"link":j['link'],"log":j.get('progress_log'),"did":j.get('delivery_id'),"date":j.get('date')} for j in jobs]
    })

@app.route('/api/add', methods=['POST'])
def api_add():
    k=request.headers.get('X-Key'); u=users_col.find_one({"key":k})
    if not u: return jsonify({"msg":"Giriş yapın"})
    
    # Kota ve Süre Kontrolü
    if u.get('used_gb',0) >= u.get('limit_gb',10): return jsonify({"msg":"KOTA DOLU!"})
    if u.get('expire_date') and datetime.datetime.utcnow() > u['expire_date']: return jsonify({"msg":"SÜRENİZ BİTMİŞ!"})

    jid=str(uuid.uuid4())[:8]
    jobs_col.insert_one({"job_id":jid,"user_key":k,"link":request.json.get('link'),"status":"SIRADA","date":get_tr_time(),"stop_requested":False})
    return jsonify({"msg":"Sıraya alındı"})

@app.route('/api/stop', methods=['POST'])
def api_stop():
    jobs_col.update_one({"job_id":request.json.get('id')},{"$set":{"status":"DURDURULUYOR...","stop_requested":True}})
    return jsonify({"ok":True})

@app.route('/api/clear', methods=['GET'])
def api_clear():
    k=request.headers.get('X-Key')
    if k: jobs_col.delete_many({"user_key":k})
    return jsonify({"ok":True})

# WORKER API
@app.route('/api/worker/get')
def w_get():
    j=jobs_col.find_one({"status":"SIRADA"})
    if j: 
        jobs_col.update_one({"job_id":j['job_id']},{"$set":{"status":"ISLENIYOR"}})
        return jsonify({"found":True,"job":j['job_id'],"link":j['link']})
    return jsonify({"found":False})

@app.route('/api/worker/update', methods=['POST'])
def w_upd():
    d=request.json; j=jobs_col.find_one({"job_id":d['id']})
    if j and j.get('stop_requested'): return jsonify({"stop":True})
    jobs_col.update_one({"job_id":d['id']},{"$set":{"progress_log":d['msg']}})
    return jsonify({"stop":False})

@app.route('/api/worker/done', methods=['POST'])
def w_done():
    d=request.json; jid=d['id']; j=jobs_col.find_one({"job_id":jid})
    if d.get('error'): jobs_col.update_one({"job_id":jid},{"$set":{"status":d['error']}})
    else:
        did=str(uuid.uuid4())[:8]
        deliveries_col.insert_one({"id":did,"html":d['html']})
        jobs_col.update_one({"job_id":jid},{"$set":{"status":"TAMAMLANDI","delivery_id":did}})
        users_col.update_one({"key":j['user_key']},{"$inc":{"used_gb":d['size']}})
    return jsonify({"ok":True})

# ADMIN API
@app.route('/api/admin/users')
def adm_u():
    if request.args.get('p')!=ADMIN_PASSWORD: return jsonify({"err":True})
    users = list(users_col.find())
    res = []
    now = datetime.datetime.utcnow()
    for u in users:
        days = "Sınırsız"
        if u.get('expire_date'):
            days = (u['expire_date'] - now).days
            if days < 0: days = "BİTTİ"
        res.append({
            "key": u['key'],
            "limit": u.get('limit_gb',0),
            "used": u.get('used_gb',0),
            "days_left": days,
            "banned": u.get('banned',False)
        })
    return jsonify({"users":res})

@app.route('/api/admin/create')
def adm_c():
    if request.args.get('p')!=ADMIN_PASSWORD: return "ERR"
    k="YAEL-"+''.join(random.choices(string.ascii_uppercase+string.digits,k=8))
    limit = int(request.args.get('l', 10))
    days = int(request.args.get('d', 30))
    exp = datetime.datetime.utcnow() + datetime.timedelta(days=days)
    
    users_col.insert_one({"key":k,"limit_gb":limit,"used_gb":0,"expire_date":exp,"hwid":None,"banned":False})
    return k

@app.route('/api/admin/ban', methods=['POST'])
def adm_b():
    d=request.json
    if d.get('p')!=ADMIN_PASSWORD: return jsonify({"err":True})
    users_col.update_one({"key":d['k']},{"$set":{"banned":bool(d['b'])}})
    return jsonify({"ok":True})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
