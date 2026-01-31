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
MONGO_URI = os.environ.get("MONGO_URI")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "YASIN_BABA_33")
TELEGRAM_USER = os.environ.get("TELEGRAM_USER", "YaelDesign") 
YAELSAVER_LINK = "https://t.me/YaelSaverBot"

if not MONGO_URI:
    client = None
    db = None
else:
    try:
        client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
        db = client['mega_leech']
        users_col = db['users']       
        jobs_col = db['jobs']         
        deliveries_col = db['deliveries']
        # YENİ: Hesap Havuzu Koleksiyonu
        accounts_col = db['accounts']
    except Exception as e:
        print(f"Mongo Hatası: {e}")

def get_tr_time():
    return (datetime.datetime.utcnow() + datetime.timedelta(hours=3)).strftime("%d.%m.%Y %H:%M")

# --- CSS (AYNI KALDI) ---
SHARED_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Rajdhani:wght@300;500;700&display=swap');
    @import url('https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css');
    :root { --p: #00f3ff; --s: #00ff9d; --d: #ff0055; --bg: #050505; --card: rgba(15, 15, 15, 0.95); }
    * { box-sizing: border-box; transition: all 0.2s ease; }
    body { background-color: var(--bg); color: #fff; font-family: 'Rajdhani', sans-serif; min-height: 100vh; display: flex; flex-direction: column; align-items: center; justify-content: center; overflow-x: hidden; }
    .glass-panel { background: var(--card); border: 1px solid rgba(0, 243, 255, 0.2); box-shadow: 0 0 40px rgba(0, 0, 0, 0.8); padding: 40px; border-radius: 12px; width: 90%; max-width: 500px; text-align: center; margin: 20px 0; }
    h1 { font-family: 'Orbitron'; color: var(--p); text-shadow: 0 0 15px rgba(0, 243, 255, 0.4); margin: 0; }
    input, textarea { width: 100%; padding: 12px; background: rgba(0,0,0,0.6); border: 1px solid #333; color: var(--p); font-family: 'Rajdhani'; font-size: 1rem; border-radius: 6px; margin-bottom: 10px; }
    button.sys-btn { width: 100%; padding: 12px; background: rgba(0, 243, 255, 0.1); border: 1px solid var(--p); color: var(--p); font-family: 'Orbitron'; font-weight: bold; cursor: pointer; border-radius: 6px; }
    button.sys-btn:hover { background: var(--p); color: #000; }
    .job-item { background: rgba(255,255,255,0.03); border-left: 3px solid #333; padding: 15px; margin-bottom: 10px; text-align: left; }
    .feature-list { text-align: left; margin: 30px 0; border-top: 1px solid #222; border-bottom: 1px solid #222; padding: 20px 0; }
    .feature-item { margin-bottom: 10px; font-size: 1.1rem; display: flex; align-items: center; gap: 10px; }
    .feature-item i { color: var(--s); width: 25px; }
    .cta-btn { background: var(--s); color: #000; font-family: 'Orbitron'; font-weight: bold; padding: 15px 30px; border-radius: 50px; text-decoration: none; display: inline-block; font-size: 1.1rem; margin-bottom: 20px; }
    .ad-box { background: linear-gradient(45deg, #1a1a1a, #2a2a2a); border-left: 4px solid #0088cc; padding: 15px; margin: 20px 0; text-align: left; border-radius: 8px; font-size: 0.9rem; }
</style>
"""

HTML_LOGIN = f"""<!DOCTYPE html><html><head><title>YAEL DOWNLOADER</title>{SHARED_CSS}</head><body>
<div style="text-align:center; margin-bottom:20px;"><h1 style="font-size: 2.5rem;">YAEL <span style="color:#fff">VIP</span></h1><h2>SİSTEM AKTİF</h2></div>
<div class="glass-panel">
    <div class="feature-list">
        <div class="feature-item"><i class="fas fa-bolt"></i> <span>MEGA.NZ KOTA SINIRI YOK</span></div>
        <div class="feature-item"><i class="fas fa-shield-alt"></i> <span>PREMIUM HAVUZ SİSTEMİ</span></div>
        <div class="feature-item"><i class="fas fa-rocket"></i> <span>ANINDA ZIP İNDİRME</span></div>
    </div>
    <a href="https://t.me/{TELEGRAM_USER}" target="_blank" class="cta-btn"><i class="fab fa-telegram-plane"></i> VIP SATIN AL</a>
    <div class="ad-box"><strong style="color:#0088cc">YAEL SAVER BOT</strong><br>Telegram yasaklı içerikleri indir.<br><a href="{YAELSAVER_LINK}" target="_blank" style="color:#fff">TIKLA</a></div>
    <div style="background:rgba(0,0,0,0.3); padding:20px; border-radius:8px; margin-top:20px;">
        <p style="color:var(--p); margin-top:0;">MÜŞTERİ GİRİŞİ</p>
        <input type="password" id="k" placeholder="ANAHTARINIZ...">
        <button class="sys-btn" onclick="go()">SİSTEME GİR</button>
    </div>
</div>
<script>
function go(){{
    let k=document.getElementById('k').value;
    let hwid=localStorage.getItem('hwid')||crypto.randomUUID(); localStorage.setItem('hwid',hwid);
    fetch('/api/login',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{key:k,hwid:hwid}})}})
    .then(r=>r.json()).then(d=>{{d.ok? (localStorage.setItem('ukey',k),location.href='/panel') : alert(d.msg)}});
}}</script></body></html>"""

HTML_PANEL = f"""<!DOCTYPE html><html><head><title>PANEL</title>{SHARED_CSS}</head><body>
<div class="glass-panel" style="max-width:800px">
    <div style="display:flex; justify-content:space-between; margin-bottom:20px;"><h2 style="color:var(--p)">VIP KONTROL PANELİ</h2><span style="color:#666">v.6.5 (Pool)</span></div>
    <div style="display:flex; justify-content:space-between; color:#aaa; font-size:0.9rem"><div>ÜYE: <span id="uid">...</span></div><div>KOTA: <span id="used">0</span>/<span id="limit">0</span> GB</div></div>
    <div style="width:100%; height:6px; background:#222; margin:5px 0 30px 0;"><div id="bar" style="width:0%; height:100%; background:var(--p);"></div></div>
    <input id="link" placeholder="MEGA LİNKİ..." style="padding:15px;">
    <button class="sys-btn" onclick="add()">🚀 İNDİR</button>
    <div style="text-align:right; margin:20px 0;"><span onclick="clearHist()" style="color:var(--d); cursor:pointer; font-size:0.8rem">GEÇMİŞİ SİL</span></div>
    <div id="jobs"></div>
</div>
<script>
const k=localStorage.getItem('ukey'); if(!k) location.href='/login';
document.getElementById('uid').innerText = k.substring(0,8)+'...';
function load(){{
    fetch('/api/data',{{headers:{{'X-Key':k}}}}).then(r=>r.json()).then(d=>{{
        if(d.err) return location.href='/login';
        document.getElementById('used').innerText = d.used.toFixed(2); document.getElementById('limit').innerText = d.limit;
        document.getElementById('bar').style.width = (d.used/d.limit)*100 + '%';
        let h=""; d.jobs.forEach(j=>{{
            let act = j.status=='TAMAMLANDI' ? `<a href="/teslimat/${{j.did}}" target="_blank" style="color:var(--s)">[İNDİR]</a>` : (j.status=='ISLENIYOR' ? `<span onclick="stop('${{j.id}}')" style="color:var(--d); cursor:pointer">[İPTAL]</span>` : "");
            h+=`<div class="job-item"><div style="color:#fff; font-weight:bold">${{j.link.substring(0,50)}}... <span style="float:right; color:var(--s)">${{j.status}}</span></div><div style="color:#888; font-size:0.8rem; margin-top:5px;">> ${{j.log||"..."}}</div><div style="text-align:right; font-size:0.7rem; color:#555">${{j.date}} ${{act}}</div></div>`;
        }}); document.getElementById('jobs').innerHTML = h;
    }});
}}
function add(){{ fetch('/api/add',{{method:'POST',headers:{{'X-Key':k,'Content-Type':'application/json'}},body:JSON.stringify({{link:document.getElementById('link').value}})}}).then(r=>r.json()).then(d=>{{alert(d.msg);load()}}); }}
function stop(id){{ fetch('/api/stop',{{method:'POST',headers:{{'X-Key':k,'Content-Type':'application/json'}},body:JSON.stringify({{id:id}})}}).then(()=>load()); }}
function clearHist(){{ fetch('/api/clear',{{headers:{{'X-Key':k}}}}).then(()=>load()); }}
setInterval(load, 3000); load();
</script></body></html>"""

HTML_ADMIN = f"""<!DOCTYPE html><html><head><title>ADMIN</title>{SHARED_CSS}</head><body>
<div class="glass-panel" style="max-width:900px">
    <h1>YÖNETİCİ</h1>
    
    <div style="background:#111; padding:15px; border-radius:8px; margin-bottom:20px; border:1px solid #333">
        <h3 style="color:var(--s); margin-top:0">MEGA HESAP HAVUZU</h3>
        <p style="color:#666; font-size:0.8rem">Hesap oluşturucudan aldığın "email:sifre" listesini buraya yapıştır.</p>
        <textarea id="accs" rows="5" placeholder="email:pass&#10;email2:pass2..."></textarea>
        <button class="sys-btn" onclick="addAcc()">HAVUZA EKLE</button>
        <div id="pool_count" style="margin-top:10px; color:#fff">Yükleniyor...</div>
    </div>

    <div style="display:flex; gap:10px; margin-bottom:20px;">
        <input id="l" type="number" placeholder="GB" value="50">
        <input id="d" type="number" placeholder="GÜN" value="30">
        <button class="sys-btn" onclick="create()">KEY ÜRET</button>
    </div>
    <div id="res" style="color:var(--s); font-family:monospace; margin-bottom:20px;"></div>
    <table id="tbl" style="width:100%; color:#ccc; font-size:0.8rem;"></table>
</div>
<script>
const p = prompt("PASS:");
function load(){{
    fetch('/api/admin/users?p='+p).then(r=>r.json()).then(d=>{{
        if(d.err) return;
        document.getElementById('pool_count').innerText = "AKTİF HESAP SAYISI: " + d.pool_size;
        let h=""; d.users.forEach(u=>{{ h+=`<tr><td>${{u.key}}</td><td>${{u.used.toFixed(1)}}/${{u.limit}}</td><td>${{u.days_left}}</td><td>${{u.banned?'BAN':'OK'}}</td><td><button onclick="ban('${{u.key}}',${{u.banned?0:1}})">X</button></td></tr>`; }});
        document.getElementById('tbl').innerHTML=h;
    }});
}}
function addAcc(){{
    let a=document.getElementById('accs').value;
    fetch('/api/admin/add_acc',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{p:p,accs:a}})}})
    .then(r=>r.json()).then(d=>{{ alert(d.msg); document.getElementById('accs').value=''; load(); }});
}}
function create(){{ fetch(`/api/admin/create?p=${{p}}&l=${{document.getElementById('l').value}}&d=${{document.getElementById('d').value}}`).then(r=>r.text()).then(k=>{{document.getElementById('res').innerText=k;load()}}); }}
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
    return render_template_string(d['html']) if d else "Bulunamadı"

# --- API ---
@app.route('/api/login', methods=['POST'])
def api_login():
    d=request.json; u=users_col.find_one({"key":d['key']})
    if not u or u.get('banned'): return jsonify({"ok":False,"msg":"Hata"})
    if u.get('expire_date') and datetime.datetime.utcnow() > u['expire_date']: return jsonify({"ok":False,"msg":"Süre Bitti"})
    if not u.get('hwid'): users_col.update_one({"key":d['key']},{"$set":{"hwid":d['hwid']}})
    elif u['hwid']!=d['hwid']: return jsonify({"ok":False,"msg":"Cihaz Hatası"})
    return jsonify({"ok":True})

@app.route('/api/data')
def api_data():
    k=request.headers.get('X-Key'); u=users_col.find_one({"key":k})
    if not u: return jsonify({"err":True})
    jobs=list(jobs_col.find({"user_key":k},{'_id':0}).sort("_id",-1))
    return jsonify({"used":u.get('used_gb',0),"limit":u.get('limit_gb',10),"days_left": (u['expire_date']-datetime.datetime.utcnow()).days if u.get('expire_date') else "Sınırsız","jobs":[{"id":j['job_id'],"status":j['status'],"link":j['link'],"log":j.get('progress_log'),"did":j.get('delivery_id'),"date":j.get('date')} for j in jobs]})

@app.route('/api/add', methods=['POST'])
def api_add():
    k=request.headers.get('X-Key'); u=users_col.find_one({"key":k})
    if not u or u.get('used_gb',0)>=u.get('limit_gb',10): return jsonify({"msg":"Limit Dolu"})
    jobs_col.insert_one({"job_id":str(uuid.uuid4())[:8],"user_key":k,"link":request.json.get('link'),"status":"SIRADA","date":get_tr_time(),"stop_requested":False})
    return jsonify({"msg":"Sırada 🚀"})

@app.route('/api/stop', methods=['POST'])
def api_stop():
    jobs_col.update_one({"job_id":request.json.get('id')},{"$set":{"status":"DURDURULUYOR...","stop_requested":True}})
    return jsonify({"ok":True})
@app.route('/api/clear', methods=['GET'])
def api_clear():
    k=request.headers.get('X-Key'); jobs_col.delete_many({"user_key":k}); return jsonify({"ok":True})

# --- WORKER API (GÜNCELLENDİ) ---
@app.route('/api/worker/get')
def w_get():
    j=jobs_col.find_one({"status":"SIRADA"})
    if j: 
        jobs_col.update_one({"job_id":j['job_id']},{"$set":{"status":"ISLENIYOR"}})
        # HAVUZDAN HESAP VER
        acc = accounts_col.find_one({"status":"ACTIVE"})
        acc_data = {"email":acc['email'], "pass":acc['pass']} if acc else None
        return jsonify({"found":True,"job":j['job_id'],"link":j['link'], "account": acc_data})
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
        did=str(uuid.uuid4())[:8]; deliveries_col.insert_one({"id":did,"html":d['html']})
        jobs_col.update_one({"job_id":jid},{"$set":{"status":"TAMAMLANDI","delivery_id":did}})
        users_col.update_one({"key":j['user_key']},{"$inc":{"used_gb":d['size']}})
    return jsonify({"ok":True})

# --- ADMIN API (YENİ ÖZELLİKLER) ---
@app.route('/api/admin/users')
def adm_u():
    if request.args.get('p')!=ADMIN_PASSWORD: return jsonify({"err":True})
    users = list(users_col.find())
    pool_size = accounts_col.count_documents({"status":"ACTIVE"})
    res = [{"key": u['key'], "limit": u.get('limit_gb',0), "used": u.get('used_gb',0), "days_left": (u['expire_date']-datetime.datetime.utcnow()).days if u.get('expire_date') else "Sınırsız", "banned": u.get('banned',False)} for u in users]
    return jsonify({"users":res, "pool_size":pool_size})

@app.route('/api/admin/create')
def adm_c():
    if request.args.get('p')!=ADMIN_PASSWORD: return "ERR"
    k="YAEL-"+''.join(random.choices(string.ascii_uppercase+string.digits,k=8))
    users_col.insert_one({"key":k,"limit_gb":int(request.args.get('l',10)),"used_gb":0,"expire_date":datetime.datetime.utcnow()+datetime.timedelta(days=int(request.args.get('d',30))),"hwid":None,"banned":False})
    return k

@app.route('/api/admin/ban', methods=['POST'])
def adm_b():
    d=request.json; 
    if d.get('p')==ADMIN_PASSWORD: users_col.update_one({"key":d['k']},{"$set":{"banned":bool(d['b'])}})
    return jsonify({"ok":True})

@app.route('/api/admin/add_acc', methods=['POST'])
def adm_acc():
    d=request.json; 
    if d.get('p')!=ADMIN_PASSWORD: return jsonify({"msg":"Yetkisiz"})
    raw = d.get('accs','')
    count = 0
    for line in raw.split('\n'):
        if ':' in line:
            p = line.strip().split(':')
            if len(p)>=2:
                # Tekrar eklemeyi önle
                if not accounts_col.find_one({"email":p[0].strip()}):
                    accounts_col.insert_one({"email":p[0].strip(), "pass":p[1].strip(), "status":"ACTIVE"})
                    count+=1
    return jsonify({"msg":f"{count} Hesap Havuza Eklendi!"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
