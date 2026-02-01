import os
import datetime
import uuid
import logging
from flask import Flask, request, jsonify, render_template_string
import pymongo
import certifi

# Hataları görmek için logları açıyoruz
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# --- AYARLAR ---
MONGO_URI = os.environ.get("MONGO_URI")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "YASIN_BABA_33")
TELEGRAM_LINK = "https://t.me/YaelSoft"

# --- DB BAĞLANTISI ---
db = None
try:
    if MONGO_URI:
        client = pymongo.MongoClient(MONGO_URI, tlsCAFile=certifi.where(), serverSelectionTimeoutMS=5000)
        db = client['mega_leech']
        users_col = db['users']
        jobs_col = db['jobs']
        deliveries_col = db['deliveries'] 
        accounts_col = db['accounts']
        logger.info("✅ MongoDB Bağlantısı Başarılı")
    else:
        logger.warning("⚠️ MONGO_URI EKSİK")
except Exception as e:
    logger.error(f"❌ DB Hatası: {e}")

def get_tr_time():
    return (datetime.datetime.utcnow() + datetime.timedelta(hours=3)).strftime("%d.%m %H:%M")

def get_now_ts():
    return datetime.datetime.utcnow().timestamp()

# --- CSS (TASARIM BURADA - SİLME!) ---
SHARED_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Rajdhani:wght@500;700&family=Roboto+Mono:wght@400;500&display=swap');
:root { --bg: #050505; --card: #111; --border: #222; --primary: #00ff9d; --danger: #ff0055; --text: #fff; }
* { box-sizing: border-box; margin: 0; padding: 0; }
body { background: var(--bg); color: var(--text); font-family: 'Rajdhani', sans-serif; display: flex; flex-direction: column; align-items: center; min-height: 100vh; padding: 20px; }
.container { width: 100%; max-width: 600px; animation: fadeIn 0.5s ease; }
h1 { font-size: 2.5rem; color: var(--primary); text-align: center; margin-bottom: 20px; text-transform: uppercase; letter-spacing: 2px; text-shadow: 0 0 20px rgba(0,255,157,0.4); }
.card { background: var(--card); border: 1px solid var(--border); border-radius: 12px; padding: 20px; margin-bottom: 15px; box-shadow: 0 10px 30px rgba(0,0,0,0.5); }
input, textarea, select { width: 100%; background: #000; border: 1px solid #333; color: #fff; padding: 12px; border-radius: 6px; font-family: 'Roboto Mono', monospace; margin-bottom: 10px; outline: none; transition: 0.3s; font-size: 1rem; }
input:focus { border-color: var(--primary); box-shadow: 0 0 10px rgba(0,255,157,0.2); }
.btn { width: 100%; background: var(--primary); color: #000; font-weight: 800; padding: 15px; border: none; border-radius: 6px; cursor: pointer; text-transform: uppercase; font-size: 1rem; transition: 0.3s; clip-path: polygon(0 0, 100% 0, 100% 85%, 95% 100%, 0 100%); }
.btn:hover { transform: translateY(-2px); box-shadow: 0 0 20px var(--primary); }
.btn:active { transform: scale(0.98); }
.stat-row { display: flex; justify-content: space-between; margin-bottom: 5px; font-size: 0.9em; }
.vip-box { background: linear-gradient(45deg, #111, #222); border: 1px solid #ffcc00; color: #ffcc00; text-align: center; padding: 15px; border-radius: 8px; cursor: pointer; animation: pulse 2s infinite; }
@keyframes pulse { 0% { box-shadow: 0 0 0 0 rgba(255, 204, 0, 0.4); } 70% { box-shadow: 0 0 0 10px rgba(255, 204, 0, 0); } 100% { box-shadow: 0 0 0 0 rgba(255, 204, 0, 0); } }
@keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
a { text-decoration: none; color: inherit; }
</style>
"""

HTML_LOGIN = f"""
<!DOCTYPE html><html><head><title>GİRİŞ</title>{SHARED_CSS}</head>
<body style="justify-content:center">
<div class="card" style="width:100%;max-width:400px;text-align:center;border-top:3px solid var(--primary)">
    <h1>YAEL<span style="color:#fff">SAVER</span></h1>
    <input id="k" type="password" placeholder="🔑 GİRİŞ ANAHTARI" style="text-align:center">
    <button class="btn" onclick="go()">SİSTEME GİR</button>
    <br><br><a href="{TELEGRAM_LINK}" style="color:var(--primary);text-decoration:underline">ANAHTAR AL</a>
</div>
<script>
function go(){{
    let k = document.getElementById('k').value;
    if(k) location.href='/panel?k='+k; else alert('Anahtar gir!');
}}
</script></body></html>"""

HTML_PANEL = f"""
<!DOCTYPE html><html><head><title>PANEL</title>{SHARED_CSS}</head>
<body>
<div class="container">
    <h1>YAEL<span style="color:#fff">SAVER</span></h1>
    
    <div id="dash" class="card" style="text-align:center;color:#888">Veriler Yükleniyor...</div>

    <div class="card">
        <h3>YENİ İNDİRME</h3>
        <input id="link" placeholder="MEGA.NZ Linki...">
        <button class="btn" onclick="add()">🚀 BAŞLAT</button>
    </div>
    
    <a href="{TELEGRAM_LINK}" target="_blank">
        <div class="vip-box">
            <h3 style="margin:0">👑 VIP / LIMIT ARTTIR</h3>
        </div>
    </a>
    <br>
    <div id="jobs"></div>
</div>
<script>
const k = new URLSearchParams(window.location.search).get('k') || localStorage.getItem('ukey');
if(k) localStorage.setItem('ukey', k); else location.href = "/";

function load(){{
    fetch('/api/data', {{ headers: {{ 'X-Key': k }} }})
    .then(r => r.json())
    .then(d => {{
        if(d.error) return document.getElementById('dash').innerHTML = `<h3 style='color:red'>${{d.error}}</h3><a href='/'>Çıkış</a>`;
        
        let u = d.user;
        let p = (u.used / u.total) * 100; if(p>100) p=100;
        
        document.getElementById('dash').innerHTML = `
            <div class="stat-row"><b style="font-size:1.2em;color:#fff">${{u.name}}</b> <span style="color:${{u.days>0?'#0f0':'#f00'}}">${{u.days}} GÜN</span></div>
            <div class="stat-row"><span>${{u.used.toFixed(2)}} GB</span> <span>${{u.total}} GB</span></div>
            <div style="background:#333;height:8px;border-radius:4px;overflow:hidden;margin-top:5px"><div style="width:${{p}}%;background:var(--primary);height:100%"></div></div>
        `;

        let h = "";
        d.jobs.forEach(j => {{
            let st = j.status == 'TAMAMLANDI' ? `<a href="/teslimat/${{j.did}}" target="_blank" style="color:#0f0;font-weight:bold;text-decoration:underline">İNDİR</a>` : `<span style="color:#fa0">${{j.status}}</span>`;
            if(j.status.includes('HATA')) st = `<span style="color:#f00">${{j.status}}</span>`;
            
            h += `<div class="card" style="padding:15px;border-left:3px solid var(--primary)">
                <div class="stat-row"><b>#${{j.id}}</b> <small>${{j.date}}</small></div>
                <div style="color:#888;font-size:0.8em;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;margin-bottom:10px">${{j.link}}</div>
                <div class="stat-row" style="border-top:1px solid #222;padding-top:10px;align-items:center">
                    <span style="font-size:0.8em;color:#aaa">${{j.log||'Bekleniyor...'}}</span>
                    <div>${{st}}</div>
                </div>
            </div>`;
        }});
        document.getElementById('jobs').innerHTML = h;
    }})
    .catch(e => document.getElementById('dash').innerHTML = "<span style='color:red'>Bağlantı Hatası! Sayfayı Yenile.</span>");
}}

function add(){{
    let l = document.getElementById('link').value;
    if(!l) return alert('Link gir!');
    fetch('/api/add', {{method:'POST', headers:{{'X-Key':k,'Content-Type':'application/json'}}, body:JSON.stringify({{link:l}})}})
    .then(r=>r.json()).then(d=>{{
        if(d.buy_link && confirm(d.msg)) window.open(d.buy_link);
        else {{ alert(d.msg); document.getElementById('link').value=""; load(); }}
    }});
}}
setInterval(load, 3000); load();
</script></body></html>"""

HTML_ADMIN = f"""<!DOCTYPE html><html><head><title>ADMIN</title>{SHARED_CSS}</head><body>
<div class="container"><h1>ADMIN</h1>
<div id="stats" class="card">Yükleniyor...</div>
<div class="card"><textarea id="accs" placeholder="email:sifre"></textarea><button class="btn" onclick="addAcc()">Hesap Ekle</button></div>
<div class="card"><input id="u_n" placeholder="Ad"><input id="u_k" placeholder="Key"><input id="u_g" placeholder="GB"><input id="u_d" placeholder="Gün"><button class="btn" onclick="addUser()">Müşteri Ekle</button></div>
<div id="users"></div></div>
<script>
const p = prompt("Şifre:");
function load(){{
    fetch('/api/admin/data?p='+p).then(r=>r.json()).then(d=>{{
        if(d.error) return document.body.innerHTML="HATA";
        document.getElementById('stats').innerHTML=`Mega: ${{d.stats.acc_active}} | User: ${{d.users.length}}`;
        let h=""; d.users.forEach(u=>{{h+=`<div class="card"><b>${{u.name}}</b> (${{u.key}})<br>${{u.used.toFixed(1)}}/${{u.total}} GB | ${{u.days}} Gün<br><button onclick="del('${{u.key}}')" style="background:#f00;color:#fff;border:none;padding:5px">Sil</button></div>`}});
        document.getElementById('users').innerHTML=h;
    }})
}}
function addAcc(){{fetch('/api/admin/add_acc',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{p:p,accs:document.getElementById('accs').value}})}}).then(load)}}
function addUser(){{fetch('/api/admin/add_user',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{p:p,name:document.getElementById('u_n').value,key:document.getElementById('u_k').value,gb:document.getElementById('u_g').value,days:document.getElementById('u_d').value}})}}).then(load)}}
function del(k){{if(confirm('Sil?'))fetch('/api/admin/del_user',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{p:p,key:k}})}}).then(load)}}
load();
</script></body></html>"""

# --- ROUTING ---
@app.route('/')
def home(): return render_template_string(HTML_LOGIN)
@app.route('/panel')
def panel(): return render_template_string(HTML_PANEL)
@app.route('/admin')
def admin(): return render_template_string(HTML_ADMIN)
@app.route('/teslimat/<id>')
def deliv(id):
    d=deliveries_col.find_one({"id":id}); return render_template_string(d['html']) if d else "Dosya Yok"

# --- API (PANEL) ---
@app.route('/api/data')
def api_data():
    if not db: return jsonify({"error":"DB YOK"})
    k=request.headers.get('X-Key')
    u=users_col.find_one({"key":k})
    if not u: return jsonify({"error":"GEÇERSİZ KEY"})
    jobs=list(jobs_col.find({"user_key":k},{'_id':0}).sort("_id",-1).limit(20))
    days=int((u['expire_date']-get_now_ts())/86400)
    return jsonify({"user":{"name":u['name'],"total":u['quota_gb'],"used":u.get('used_gb',0),"days":days if days>0 else 0},"jobs":jobs})

@app.route('/api/add', methods=['POST'])
def api_add():
    k=request.headers.get('X-Key'); u=users_col.find_one({"key":k})
    if not u: return jsonify({"msg":"Giriş Yap"})
    if get_now_ts()>u['expire_date']: return jsonify({"msg":"SÜRE BİTTİ","buy_link":TELEGRAM_LINK})
    if u.get('used_gb',0)>=u['quota_gb']: return jsonify({"msg":"KOTA BİTTİ","buy_link":TELEGRAM_LINK})
    jobs_col.insert_one({"job_id":str(uuid.uuid4())[:8],"user_key":k,"link":request.json.get('link'),"status":"SIRADA","date":get_tr_time()})
    return jsonify({"msg":"Başlatıldı 🚀"})

# --- API (WORKER) - BU EKSİK OLURSA ÇALIŞMAZ ---
@app.route('/api/worker/get_job')
def w_get():
    if not db: return jsonify({"found":False})
    j=jobs_col.find_one({"status":"SIRADA"})
    if not j: return jsonify({"found":False})
    acc=accounts_col.find_one({"status":"ACTIVE"})
    if not acc:
        old=accounts_col.find_one({"status":"COOLDOWN"},sort=[("cooldown_start",1)])
        if old: accounts_col.update_one({"_id":old["_id"]},{"$set":{"status":"ACTIVE"}}); acc=old
        else: return jsonify({"found":False})
    jobs_col.update_one({"job_id":j['job_id']},{"$set":{"status":"ISLENIYOR"}})
    return jsonify({"found":True,"job":j['job_id'],"link":j['link'],"acc":{"email":acc['email'],"pass":acc['pass']}})

@app.route('/api/worker/done', methods=['POST'])
def w_done():
    d=request.json; s=d.get('error') or "TAMAMLANDI"
    if not d.get('error'):
        did=str(uuid.uuid4())[:8]; deliveries_col.insert_one({"id":did,"html":d['html']})
        jobs_col.update_one({"job_id":d['id']},{"$set":{"status":s,"delivery_id":did}})
        job=jobs_col.find_one({"job_id":d['id']})
        if job: users_col.update_one({"key":job['user_key']},{"$inc":{"used_gb":float(d.get('size',0))}})
    else: jobs_col.update_one({"job_id":d['id']},{"$set":{"status":s}})
    return jsonify({"ok":True})

@app.route('/api/worker/update', methods=['POST'])
def w_upd():
    if db: jobs_col.update_one({"job_id":request.json['id']},{"$set":{"progress_log":request.json['msg']}})
    return jsonify({"ok":True})

@app.route('/api/worker/report_quota', methods=['POST'])
def w_quota():
    if db: accounts_col.update_one({"email":request.json.get('email')},{"$set":{"status":"COOLDOWN","cooldown_start":datetime.datetime.utcnow()}})
    return jsonify({"ok":True})

# --- API (ADMIN) ---
@app.route('/api/admin/data')
def ad_d():
    if request.args.get('p')!=ADMIN_PASSWORD: return jsonify({"error":"Auth"})
    u_list=[]; now=get_now_ts()
    for u in users_col.find():
        days=int((u['expire_date']-now)/86400)
        u_list.append({"name":u['name'],"key":u['key'],"total":u['quota_gb'],"used":u.get('used_gb',0),"days":days if days>0 else 0})
    return jsonify({"stats":{"acc_active":accounts_col.count_documents({"status":"ACTIVE"})},"users":u_list})

@app.route('/api/admin/add_acc',methods=['POST'])
def ad_aa():
    if request.json.get('p')!=ADMIN_PASSWORD: return jsonify({"msg":"Err"})
    c=0
    for l in request.json['accs'].split('\n'):
        if ':' in l: e,p=l.split(':',1); accounts_col.update_one({"email":e.strip()},{"$set":{"pass":p.strip(),"status":"ACTIVE"}},upsert=True); c+=1
    return jsonify({"msg":f"{c} Eklendi"})

@app.route('/api/admin/add_user',methods=['POST'])
def ad_au():
    d=request.json; 
    if d.get('p')!=ADMIN_PASSWORD: return jsonify({"msg":"Err"})
    exp=get_now_ts()+(int(d.get('days',30))*86400)
    users_col.insert_one({"name":d.get('name'),"key":d.get('key') or str(uuid.uuid4())[:8],"quota_gb":float(d.get('gb',50)),"used_gb":0,"expire_date":exp})
    return jsonify({"msg":"OK"})

@app.route('/api/admin/del_user',methods=['POST'])
def ad_du():
    if request.json.get('p')!=ADMIN_PASSWORD: return jsonify({"msg":"Err"}); 
    users_col.delete_one({"key":request.json.get('key')})
    return jsonify({"msg":"OK"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))