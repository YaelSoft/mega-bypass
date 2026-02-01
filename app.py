import os
import datetime
import uuid
import logging
from flask import Flask, request, jsonify, render_template_string
import pymongo
import certifi

# Hataları loglara bas
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# --- AYARLAR ---
MONGO_URI = os.environ.get("MONGO_URI")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "YASIN_BABA_33")
TELEGRAM_LINK = "https://t.me/yasin33"
VERSION = "81.0" # Tarayıcıyı yenilemeye zorlamak için

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
        logger.info(f"✅ MongoDB Bağlantısı Başarılı (V{VERSION})")
except Exception as e:
    logger.error(f"❌ DB Hatası: {e}")

def get_tr_time():
    return (datetime.datetime.utcnow() + datetime.timedelta(hours=3)).strftime("%d.%m %H:%M")

def get_now_ts():
    return datetime.datetime.utcnow().timestamp()

# --- CSS (FULL NEON CYBERPUNK) ---
SHARED_CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Rajdhani:wght@500;700&family=Roboto+Mono:wght@400;500&display=swap');
:root {{ --bg: #050505; --card: #111; --border: #222; --primary: #00ff9d; --danger: #ff0055; --text: #fff; }}
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{ background: var(--bg); color: var(--text); font-family: 'Rajdhani', sans-serif; display: flex; flex-direction: column; align-items: center; min-height: 100vh; padding: 20px; }}
.container {{ width: 100%; max-width: 600px; animation: fadeIn 0.5s ease; }}
h1 {{ font-size: 2.5rem; color: var(--primary); text-align: center; margin-bottom: 20px; text-transform: uppercase; letter-spacing: 2px; text-shadow: 0 0 20px rgba(0,255,157,0.4); }}
.card {{ background: var(--card); border: 1px solid var(--border); border-radius: 12px; padding: 20px; margin-bottom: 15px; box-shadow: 0 10px 30px rgba(0,0,0,0.5); position: relative; overflow: hidden; }}
.card::before {{ content: ''; position: absolute; top: 0; left: 0; width: 3px; height: 100%; background: var(--primary); }}
input, textarea {{ width: 100%; background: #000; border: 1px solid #333; color: #fff; padding: 12px; border-radius: 6px; font-family: 'Roboto Mono', monospace; margin-bottom: 10px; outline: none; }}
input:focus {{ border-color: var(--primary); }}
.btn {{ width: 100%; background: var(--primary); color: #000; font-weight: 800; padding: 15px; border: none; border-radius: 6px; cursor: pointer; text-transform: uppercase; transition: 0.3s; }}
.btn:hover {{ transform: translateY(-2px); box-shadow: 0 0 20px var(--primary); }}
.stat-row {{ display: flex; justify-content: space-between; margin-bottom: 8px; }}
.progress-bg {{ background: #222; height: 100%; width: 100%; border-radius: 4px; overflow: hidden; }}
.progress-fill {{ background: var(--primary); height: 8px; transition: 0.5s; }}
.version-tag {{ font-size: 0.7em; color: #444; text-align: center; margin-top: 10px; }}
@keyframes fadeIn {{ from {{ opacity: 0; transform: translateY(10px); }} to {{ opacity: 1; transform: translateY(0); }} }}
a {{ text-decoration: none; color: inherit; }}
</style>
"""

# --- HTML TEMPLATES ---
HTML_LOGIN = f"""
<!DOCTYPE html><html><head><title>GİRİŞ V{VERSION}</title>{SHARED_CSS}</head>
<body style="justify-content:center">
<div class="card" style="width:100%;max-width:400px;text-align:center">
    <h1>YAEL<span style="color:#fff">SAVER</span></h1>
    <input id="k" type="password" placeholder="🔑 GİRİŞ ANAHTARI" style="text-align:center">
    <button class="btn" onclick="go()">SİSTEME GİRİŞ YAP</button>
    <br><br><a href="{TELEGRAM_LINK}" style="color:var(--primary);font-size:0.9em">🔑 ANAHTAR SATIN AL</a>
    <div class="version-tag">Build v{VERSION}</div>
</div>
<script>function go(){{ let k = document.getElementById('k').value; if(k) location.href='/panel?k='+k; }}</script>
</body></html>"""

HTML_PANEL = f"""
<!DOCTYPE html><html><head><title>PANEL V{VERSION}</title>{SHARED_CSS}</head>
<body>
<div class="container">
    <h1>YAEL<span style="color:#fff">SAVER</span></h1>
    <div id="dash" class="card"><div style="text-align:center;color:#555">Veriler Çekiliyor...</div></div>
    <div class="card">
        <h3 style="margin-bottom:10px">YENİ İŞLEM</h3>
        <input id="link" placeholder="MEGA.NZ Linki Yapıştırın...">
        <button class="btn" onclick="add()">🚀 İNDİRMEYİ BAŞLAT</button>
    </div>
    <div id="jobs"></div>
    <div class="version-tag">System v{VERSION}</div>
</div>
<script>
const k = new URLSearchParams(window.location.search).get('k') || localStorage.getItem('ukey');
if(k) localStorage.setItem('ukey', k); else location.href = "/";
function load(){{
    fetch('/api/data', {{ headers: {{ 'X-Key': k, 'v': '{VERSION}' }} }})
    .then(r => r.json())
    .then(d => {{
        if(d.error) {{ document.getElementById('dash').innerHTML = `<h3 style='color:red'>${{d.error}}</h3>`; return; }}
        let u = d.user; let p = (u.used / u.total) * 100; if(p>100) p=100;
        document.getElementById('dash').innerHTML = `
            <div class="stat-row"><b style="font-size:1.2em">${{u.name}}</b> <span style="color:#0f0">${{u.days}} GÜN</span></div>
            <div class="stat-row"><span>KOTA: ${{u.used.toFixed(2)}} / ${{u.total}} GB</span></div>
            <div class="progress-bg"><div class="progress-fill" style="width:${{p}}%"></div></div>`;
        let h = "";
        d.jobs.forEach(j => {{
            let st = j.status == 'TAMAMLANDI' ? `<a href="/teslimat/${{j.did}}" target="_blank" style="color:#0f0;font-weight:bold">📥 İNDİR</a>` : `<span style="color:#fa0">${{j.status}}</span>`;
            h += `<div class="card" style="padding:15px">
                <div class="stat-row"><b>#${{j.id}}</b> <small>${{j.date}}</small></div>
                <div style="color:#888;font-size:0.8em;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${{j.link}}</div>
                <div class="stat-row" style="margin-top:10px;font-size:0.8em"><span>${{j.log||'Sırada...'}}</span> ${{st}}</div>
            </div>`;
        }});
        document.getElementById('jobs').innerHTML = h;
    }}).catch(e => {{ document.getElementById('dash').innerHTML = "Bağlantı Hatası!"; }});
}}
function add(){{
    let l = document.getElementById('link').value; if(!l) return alert('Link gir!');
    fetch('/api/add', {{method:'POST', headers:{{'X-Key':k,'Content-Type':'application/json'}}, body:JSON.stringify({{link:l}})}})
    .then(r=>r.json()).then(d=>{{ alert(d.msg); load(); }});
}}
setInterval(load, 4000); load();
</script></body></html>"""

# --- API ROUTES ---
@app.route('/')
def home(): return render_template_string(HTML_LOGIN)
@app.route('/panel')
def panel(): return render_template_string(HTML_PANEL)
@app.route('/teslimat/<id>')
def deliv(id):
    d=deliveries_col.find_one({"id":id}); return render_template_string(d['html']) if d else "HATA"

@app.route('/api/data')
def api_data():
    if not db: return jsonify({"error":"DB BAĞLANTISI YOK"})
    k=request.headers.get('X-Key')
    u=users_col.find_one({"key":k})
    if not u: return jsonify({"error":"ANAHTAR GEÇERSİZ"})
    jobs=list(jobs_col.find({"user_key":k},{'_id':0}).sort("_id",-1).limit(15))
    days=int((u['expire_date']-get_now_ts())/86400)
    return jsonify({"user":{"name":u['name'],"total":u['quota_gb'],"used":u.get('used_gb',0.0),"days":days if days>0 else 0},"jobs":jobs})

@app.route('/api/add', methods=['POST'])
def api_add():
    k=request.headers.get('X-Key'); u=users_col.find_one({"key":k})
    if not u: return jsonify({"msg":"Yetkisiz"})
    if get_now_ts()>u['expire_date']: return jsonify({"msg":"SÜRE DOLDU"})
    jobs_col.insert_one({"job_id":str(uuid.uuid4())[:8],"user_key":k,"link":request.json.get('link'),"status":"SIRADA","date":get_tr_time()})
    return jsonify({"msg":"Başlatıldı! 🚀"})

# --- WORKER API ---
@app.route('/api/worker/get_job')
def w_get():
    if not db: return jsonify({"found":False})
    j=jobs_col.find_one({"status":"SIRADA"})
    if not j: return jsonify({"found":False})
    acc=accounts_col.find_one({"status":"ACTIVE"})
    if not acc: return jsonify({"found":False})
    jobs_col.update_one({"job_id":j['job_id']},{"$set":{"status":"ISLENIYOR"}})
    return jsonify({"found":True,"job":j['job_id'],"link":j['link'],"acc":{"email":acc['email'],"pass":acc['pass']}})

@app.route('/api/worker/done', methods=['POST'])
def w_done():
    d=request.json; s=d.get('error') or "TAMAMLANDI"
    if not d.get('error'):
        did=str(uuid.uuid4())[:8]; deliveries_col.insert_one({"id":did,"html":d['html']})
        jobs_col.update_one({"job_id":d['id']},{"$set":{"status":s,"delivery_id":did}})
        job=jobs_col.find_one({"job_id":d['id']})
        if job: users_col.update_one({"key":job['user_key']},{"$inc":{"used_gb":float(d.get('size',0.0))}})
    else: jobs_col.update_one({"job_id":d['id']},{"$set":{"status":s}})
    return jsonify({"ok":True})

# --- ADMIN API ---
@app.route('/admin')
def admin_page(): return "Admin API V81 Aktif"
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
    for l in request.json['accs'].split('\n'):
        if ':' in l: e,p=l.split(':',1); accounts_col.update_one({"email":e.strip()},{"$set":{"pass":p.strip(),"status":"ACTIVE"}},upsert=True)
    return jsonify({"msg":"Hesaplar Eklendi"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
