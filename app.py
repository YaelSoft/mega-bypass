import certifi
from flask import Flask, request, jsonify, render_template_string
from pymongo import MongoClient
import os
import datetime
import uuid
import random
import string

app = Flask(__name__)

# --- AYARLAR (RENDER'DAN ÇEKİLİR) ---
# Eğer Render'da ayar bulamazsa varsayılanları kullanır
MONGO_URI = os.environ.get("MONGO_URI")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "Ata_Yasin5353")
TELEGRAM_USER = os.environ.get("TELEGRAM_USER", "YaelDesign") 
YAELSAVER_LINK = "https://t.me/YaelSaverBot"

# Mongo Bağlantısı
if not MONGO_URI:
    print("HATA: MONGO_URI bulunamadı! Render ayarlarına ekleyin.")
    client = None
    db = None
else:
    try:
        client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
        db = client['mega_leech']
        users_col = db['users']       
        jobs_col = db['jobs']         
        deliveries_col = db['deliveries']
    except Exception as e:
        print(f"Mongo Bağlantı Hatası: {e}")

def get_tr_time():
    return (datetime.datetime.utcnow() + datetime.timedelta(hours=3)).strftime("%d.%m.%Y %H:%M")

# --- CSS (ULTIMATE DESIGN & LANDING PAGE) ---
SHARED_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Rajdhani:wght@300;500;700&display=swap');
    @import url('https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css');
    
    :root { --p: #00f3ff; --s: #00ff9d; --d: #ff0055; --bg: #050505; --card: rgba(15, 15, 15, 0.95); }
    
    * { box-sizing: border-box; transition: all 0.2s ease; }
    
    body {
        background-color: var(--bg);
        background-image: radial-gradient(circle at 50% 50%, rgba(0, 243, 255, 0.05), transparent 60%);
        color: #fff; font-family: 'Rajdhani', sans-serif;
        margin: 0; min-height: 100vh; display: flex; flex-direction: column; align-items: center; justify-content: center;
        overflow-x: hidden;
    }
    
    body::after {
        content: ""; position: fixed; top: 0; left: 0; width: 100%; height: 100%;
        background: linear-gradient(rgba(18, 16, 16, 0) 50%, rgba(0, 0, 0, 0.25) 50%), linear-gradient(90deg, rgba(255, 0, 0, 0.06), rgba(0, 255, 0, 0.02), rgba(0, 0, 255, 0.06));
        background-size: 100% 2px, 3px 100%; pointer-events: none; z-index: -1;
    }

    .glass-panel {
        background: var(--card); border: 1px solid rgba(0, 243, 255, 0.2);
        box-shadow: 0 0 40px rgba(0, 0, 0, 0.8), inset 0 0 20px rgba(0, 243, 255, 0.05);
        backdrop-filter: blur(10px); padding: 40px; border-radius: 12px;
        width: 90%; max-width: 500px; text-align: center; position: relative; margin: 20px 0;
    }

    h1 { font-family: 'Orbitron', sans-serif; letter-spacing: 2px; color: var(--p); text-shadow: 0 0 15px rgba(0, 243, 255, 0.4); margin: 0; }
    h2 { color: #fff; font-size: 1.2rem; margin-top: 5px; color: #888; font-weight: 300; }
    
    /* Login Page Özelleri */
    .feature-list { text-align: left; margin: 30px 0; border-top: 1px solid #222; border-bottom: 1px solid #222; padding: 20px 0; }
    .feature-item { margin-bottom: 10px; font-size: 1.1rem; display: flex; align-items: center; gap: 10px; }
    .feature-item i { color: var(--s); width: 25px; }

    .cta-btn {
        background: var(--s); color: #000; font-family: 'Orbitron'; font-weight: bold;
        padding: 15px 30px; border-radius: 50px; text-decoration: none; display: inline-block;
        font-size: 1.1rem; box-shadow: 0 0 20px rgba(0, 255, 157, 0.4);
        animation: pulse-btn 2s infinite; margin-bottom: 20px;
    }
    @keyframes pulse-btn { 0% { transform: scale(1); } 50% { transform: scale(1.05); } 100% { transform: scale(1); } }
    
    .ad-box {
        background: linear-gradient(45deg, #1a1a1a, #2a2a2a); border-left: 4px solid #0088cc;
        padding: 15px; margin: 20px 0; text-align: left; border-radius: 8px; font-size: 0.9rem;
    }

    .login-area { background: rgba(0,0,0,0.3); padding: 20px; border-radius: 8px; margin-top: 20px; }

    /* Input & Button Standart */
    input {
        width: 100%; padding: 12px; background: rgba(0,0,0,0.6); border: 1px solid #333;
        color: var(--p); font-family: 'Rajdhani'; font-size: 1.1rem; text-align: center;
        border-radius: 6px; letter-spacing: 1px; margin-bottom: 10px;
    }
    input:focus { outline: none; border-color: var(--p); }
    
    button.sys-btn {
        width: 100%; padding: 12px; background: rgba(0, 243, 255, 0.1); border: 1px solid var(--p);
        color: var(--p); font-family: 'Orbitron'; font-weight: bold; cursor: pointer; border-radius: 6px;
    }
    button.sys-btn:hover { background: var(--p); color: #000; }

    .status-dot { height: 10px; width: 10px; background-color: var(--s); border-radius: 50%; display: inline-block; margin-right: 5px; box-shadow: 0 0 10px var(--s); }
    .blink { animation: blinker 1.5s linear infinite; }
    @keyframes blinker { 50% { opacity: 0; } }

    /* Panel İçi */
    .job-item { background: rgba(255,255,255,0.03); border-left: 3px solid #333; padding: 15px; margin-bottom: 10px; text-align: left; }
    .status-badge { font-size: 0.75rem; padding: 3px 8px; border-radius: 4px; background: #222; border: 1px solid #444; float: right; }
</style>
"""

# --- HTML TEMPLATES ---

HTML_LOGIN = f"""<!DOCTYPE html><html><head><title>YAEL DOWNLOADER</title>{SHARED_CSS}</head><body>

<div style="text-align:center; margin-bottom:20px;">
    <h1 style="font-size: 2.5rem;">YAEL <span style="color:#fff">VIP</span></h1>
    <h2><span class="status-dot blink"></span>SİSTEM AKTİF VE HAZIR</h2>
</div>

<div class="glass-panel">
    
    <div class="feature-list">
        <div class="feature-item"><i class="fas fa-bolt"></i> <span>MEGA.NZ KOTA SINIRI YOK</span></div>
        <div class="feature-item"><i class="fas fa-shield-alt"></i> <span>2000+ PROXY İLE GİZLİLİK</span></div>
        <div class="feature-item"><i class="fas fa-rocket"></i> <span>ANINDA ZIP İNDİRME</span></div>
        <div class="feature-item"><i class="fas fa-crown"></i> <span>VIP ÜYELERE ÖZEL PANEL</span></div>
    </div>

    <p style="color:#aaa; margin-bottom:20px;">Bu sistem özel üyelik gerektirir. Hemen VIP satın alıp sınırsız indirmeye başlayın.</p>
    
    <a href="https://t.me/{TELEGRAM_USER}" target="_blank" class="cta-btn">
        <i class="fab fa-telegram-plane"></i> VIP SATIN AL
    </a>
    
    <div style="margin-top:10px;">
        <a href="https://instagram.com" target="_blank" style="color:#666; text-decoration:none; margin:0 10px; font-size:0.9rem"><i class="fab fa-instagram"></i> Instagram</a>
        <a href="https://t.me/{TELEGRAM_USER}" target="_blank" style="color:#666; text-decoration:none; margin:0 10px; font-size:0.9rem"><i class="fab fa-telegram"></i> Telegram</a>
    </div>

    <div class="ad-box">
        <strong style="color:#0088cc"><i class="fab fa-telegram"></i> YAEL SAVER BOT</strong><br>
        Telegram'da kaydetme engeli olan (yasaklı) içerikleri indirmek mi istiyorsun? 
        <br><a href="{YAELSAVER_LINK}" target="_blank" style="color:#fff; text-decoration:underline; font-size:0.8rem; display:block; margin-top:5px;">BOTU DENEMEK İÇİN TIKLA</a>
    </div>

    <div class="login-area">
        <p style="color:var(--p); font-size:0.9rem; margin-top:0; margin-bottom:10px; text-transform:uppercase; letter-spacing:1px;">MÜŞTERİ GİRİŞİ</p>
        <input type="password" id="k" placeholder="ANAHTARINIZI GİRİN...">
        <button class="sys-btn" onclick="go()">SİSTEME GİR</button>
    </div>

</div>

<p style="color:#444; font-size:0.8rem; margin-top:20px;">&copy; 2026 YAEL SOFTWARE SOLUTIONS. ALL RIGHTS RESERVED.</p>

<script>
function go(){{
    let k=document.getElementById('k').value;
    if(!k) return alert("Anahtar girmediniz!");
    
    let hwid=localStorage.getItem('hwid')||crypto.randomUUID(); localStorage.setItem('hwid',hwid);
    document.querySelector('.sys-btn').innerText = "DOĞRULANIYOR...";
    
    fetch('/api/login',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{key:k,hwid:hwid}})}})
    .then(r=>r.json()).then(d=>{{
        if(d.ok){{localStorage.setItem('ukey',k); location.href='/panel'}}
        else {{alert(d.msg); document.querySelector('.sys-btn').innerText = "SİSTEME GİR";}}
    }});
}}
</script></body></html>"""

HTML_PANEL = f"""<!DOCTYPE html><html><head><title>PANEL - YAEL VIP</title>{SHARED_CSS}</head><body>
<div class="glass-panel" style="max-width:800px">
    <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid #333; padding-bottom:15px; margin-bottom:20px;">
        <h2 style="margin:0; color:var(--p)">VIP KONTROL PANELİ</h2>
        <div style="font-size:0.9rem; color:#666">v.6.3</div>
    </div>

    <div style="display:flex; justify-content:space-between; margin-bottom:20px; font-size:0.9rem; color:#aaa;">
        <div>👤 ÜYE: <span id="uid" style="color:white; font-family:monospace">...</span></div>
        <div>⏳ KALAN SÜRE: <span id="days" style="color:var(--s); font-weight:bold">...</span> GÜN</div>
    </div>
    
    <div style="margin-bottom:5px; display:flex; justify-content:space-between; font-size:0.8rem; color:#888;">
        <span>KOTA KULLANIMI</span>
        <span><span id="used">0</span> / <span id="limit">0</span> GB</span>
    </div>
    <div style="width:100%; height:6px; background:#222; margin-bottom:30px; border-radius:3px; overflow:hidden">
        <div id="bar" style="width:0%; height:100%; background:var(--p); box-shadow:0 0 10px var(--p); transition:width 1s"></div>
    </div>

    <input id="link" placeholder="MEGA.NZ LİNKİNİ BURAYA YAPIŞTIR..." style="font-size:1rem; padding:15px;">
    <button class="sys-btn" onclick="add()" style="font-size:1.1rem; padding:15px;">🚀 İNDİRMEYİ BAŞLAT</button>
    <p style="font-size:0.8rem; color:#555; margin-top:10px;">* Klasör (/folder/) veya dosya linki desteklenir.</p>

    <div style="display:flex; justify-content:space-between; margin-top:40px; margin-bottom:10px; border-bottom:1px solid #333; padding-bottom:10px;">
        <span style="color:#fff; font-weight:bold; letter-spacing:1px;">İŞLEM GEÇMİŞİ</span>
        <span onclick="clearHist()" style="color:var(--d); cursor:pointer; font-size:0.75rem; border:1px solid #333; padding:2px 8px; border-radius:4px;">TEMİZLE</span>
    </div>
    
    <div id="jobs"></div>
    
    <button onclick="logout()" style="background:transparent; border:1px solid #333; color:#666; width:auto; padding:8px 20px; margin-top:30px; font-size:0.8rem; border-radius:4px; cursor:pointer;">ÇIKIŞ YAP</button>
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
            let log = j.log || "Sırada bekliyor...";
            
            if(st=='ISLENIYOR') {{
                badge = "İŞLENİYOR";
                act = `<span onclick="stop('${{j.id}}')" style="color:var(--d); cursor:pointer; margin-left:10px; font-size:0.8rem">[İPTAL]</span>`;
            }} else if(st=='TAMAMLANDI') {{
                badge = "HAZIR";
                act = `<a href="/teslimat/${{j.did}}" target="_blank" style="color:var(--s); text-decoration:none; margin-left:10px; font-weight:bold; border:1px solid var(--s); padding:2px 10px; border-radius:4px;">İNDİR</a>`;
            }}

            h+=`<div class="job-item" style="border-left-color:${{st=='TAMAMLANDI'?'var(--s)':(st=='HATA'?'var(--d)':'var(--p)')}}">
                <div style="display:flex; justify-content:space-between; margin-bottom:5px;">
                    <span style="font-weight:bold; color:#fff; font-size:0.9rem; overflow:hidden; white-space:nowrap; width:65%">${{j.link}}</span>
                    <span class="status-badge" style="color:${{st=='TAMAMLANDI'?'var(--s)':'#aaa'}}">${{badge}}</span>
                </div>
                <div style="font-family:monospace; font-size:0.8rem; color:#888; background:rgba(0,0,0,0.3); padding:5px; border-radius:4px;">> ${{log}}</div>
                <div style="text-align:right; margin-top:5px; font-size:0.75rem; color:#555">
                    ${{j.date}} ${{act}}
                </div>
            </div>`;
        }});
        document.getElementById('jobs').innerHTML = h || '<div style="color:#444; padding:20px; text-align:center;">Henüz işlem yok.</div>';
    }});
}}

function add(){{
    let l=document.getElementById('link').value;
    if(!l) return alert("Link girmedin!");
    fetch('/api/add',{{method:'POST',headers:{{'X-Key':k,'Content-Type':'application/json'}},body:JSON.stringify({{link:l}})}})
    .then(r=>r.json()).then(d=>{{ alert(d.msg); load(); document.getElementById('link').value=''; }});
}}
function stop(id){{ if(confirm('Durdurulsun mu?')) fetch('/api/stop',{{method:'POST',headers:{{'X-Key':k,'Content-Type':'application/json'}},body:JSON.stringify({{id:id}})}}).then(()=>load()); }}
function clearHist(){{ if(confirm('Geçmiş silinsin mi?')) fetch('/api/clear',{{headers:{{'X-Key':k}}}}).then(()=>load()); }}
function logout(){{ localStorage.removeItem('ukey'); location.href='/login'; }}
setInterval(load, 3000); load();
</script></body></html>"""

HTML_ADMIN = f"""<!DOCTYPE html><html><head><title>ADMIN</title>{SHARED_CSS}</head><body>
<div class="glass-panel" style="max-width:900px">
    <h1>YÖNETİCİ KONSOLU</h1>
    
    <div style="display:flex; gap:10px; margin-top:30px; background:rgba(0,0,0,0.5); padding:20px; border-radius:8px;">
        <input id="l" type="number" placeholder="LİMİT (GB)" value="50">
        <input id="d" type="number" placeholder="SÜRE (GÜN)" value="30">
        <button class="sys-btn" onclick="create()" style="width:150px">OLUŞTUR</button>
    </div>
    <div id="res" style="color:var(--s); font-family:monospace; font-size:1.5rem; margin:20px 0; background:#000; padding:10px; border-radius:4px;"></div>

    <h3 style="text-align:left; color:#666; border-bottom:1px solid #333; padding-bottom:10px;">MÜŞTERİ LİSTESİ</h3>
    <table id="tbl" style="width:100%; font-size:0.9rem; color:#ccc; text-align:left; border-collapse:collapse;"></table>
</div>
<script>
const p = prompt("YÖNETİCİ ŞİFRESİ:");
function load(){{
    fetch('/api/admin/users?p='+p).then(r=>r.json()).then(d=>{{
        if(d.err) return document.body.innerHTML="<h1>YETKİSİZ</h1>";
        let h="<tr><th style='color:var(--p); padding:10px;'>ANAHTAR</th><th>KOTA</th><th>KALAN GÜN</th><th>DURUM</th><th>İŞLEM</th></tr>";
        d.users.forEach(u=>{{
            let btn = u.banned ? `<button onclick="ban('${{u.key}}',0)" style="color:#0f0; background:none; border:1px solid #0f0; cursor:pointer">AÇ</button>` : `<button onclick="ban('${{u.key}}',1)" style="color:#f00; background:none; border:1px solid #f00; cursor:pointer">BAN</button>`;
            h+=`<tr style="border-bottom:1px solid #222">
                <td style="padding:10px; font-family:monospace">${{u.key}}</td>
                <td>${{u.used.toFixed(1)}} / ${{u.limit}} GB</td>
                <td>${{u.days_left}}</td>
                <td style="color:${{u.banned?'#f00':'#0f0'}}">${{u.banned?'BANLI':'AKTİF'}}</td>
                <td>${{btn}}</td>
            </tr>`;
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
    if not u or u.get('banned'): return jsonify({"ok":False,"msg":"Geçersiz veya Banlı Anahtar"})
    if u.get('expire_date') and datetime.datetime.utcnow() > u['expire_date']:
        return jsonify({"ok":False,"msg":"SÜRENİZ DOLDU! Telegram'dan yenileyin."})
    if not u.get('hwid'): users_col.update_one({"key":d['key']},{"$set":{"hwid":d['hwid']}})
    elif u['hwid']!=d['hwid']: return jsonify({"ok":False,"msg":"Farklı cihazda oturum açılamaz!"})
    return jsonify({"ok":True})

@app.route('/api/data')
def api_data():
    k=request.headers.get('X-Key'); u=users_col.find_one({"key":k})
    if not u: return jsonify({"err":True})
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
    if u.get('used_gb',0) >= u.get('limit_gb',10): return jsonify({"msg":"KOTA DOLU! Ek paket alın."})
    if u.get('expire_date') and datetime.datetime.utcnow() > u['expire_date']: return jsonify({"msg":"SÜRENİZ BİTMİŞ!"})
    jid=str(uuid.uuid4())[:8]
    jobs_col.insert_one({"job_id":jid,"user_key":k,"link":request.json.get('link'),"status":"SIRADA","date":get_tr_time(),"stop_requested":False})
    return jsonify({"msg":"İşlem Sıraya Alındı 🚀"})

@app.route('/api/stop', methods=['POST'])
def api_stop():
    jobs_col.update_one({"job_id":request.json.get('id')},{"$set":{"status":"DURDURULUYOR...","stop_requested":True}})
    return jsonify({"ok":True})

@app.route('/api/clear', methods=['GET'])
def api_clear():
    k=request.headers.get('X-Key')
    if k: jobs_col.delete_many({"user_key":k})
    return jsonify({"ok":True})

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
        res.append({"key": u['key'], "limit": u.get('limit_gb',0), "used": u.get('used_gb',0), "days_left": days, "banned": u.get('banned',False)})
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
