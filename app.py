import os
import datetime
import uuid
import logging
from flask import Flask, request, jsonify, render_template_string
import pymongo
import certifi

# Hataları Render loglarında görmek için
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

# --- CSS ---
SHARED_CSS = """<style>
@import url('https://fonts.googleapis.com/css2?family=Rajdhani:wght@500;700&family=Roboto+Mono:wght@400;500&display=swap');
:root { --bg: #050505; --card: #111; --border: #222; --primary: #00ff9d; --danger: #ff0055; --text: #fff; }
* { box-sizing: border-box; margin: 0; padding: 0; }
body { background: var(--bg); color: var(--text); font-family: 'Rajdhani', sans-serif; display: flex; flex-direction: column; align-items: center; min-height: 100vh; padding: 20px; }
.container { width: 100%; max-width: 600px; }
h1 { color: var(--primary); text-align: center; margin-bottom: 20px; text-shadow: 0 0 20px rgba(0,255,157,0.4); }
.card { background: var(--card); border: 1px solid var(--border); border-radius: 12px; padding: 20px; margin-bottom: 15px; }
input, textarea { width: 100%; background: #000; border: 1px solid #333; color: #fff; padding: 12px; border-radius: 6px; margin-bottom: 10px; }
.btn { width: 100%; background: var(--primary); color: #000; font-weight: 800; padding: 15px; border: none; border-radius: 6px; cursor: pointer; }
a { color: inherit; text-decoration: none; }
</style>"""

# --- HTML TEMPLATES (Kısaltılmış) ---
HTML_LOGIN = f"""<!DOCTYPE html><html><head><title>GİRİŞ</title>{SHARED_CSS}</head>
<body style="justify-content:center"><div class="card" style="text-align:center">
<h1>YAEL<span style="color:#fff">SAVER</span></h1><input id="k" type="password" placeholder="ANAHTAR">
<button class="btn" onclick="go()">GİRİŞ</button><br><br><a href="{TELEGRAM_LINK}">ANAHTAR AL</a></div>
<script>function go(){{location.href='/panel?k='+document.getElementById('k').value}}</script></body></html>"""

HTML_PANEL = f"""<!DOCTYPE html><html><head><title>PANEL</title>{SHARED_CSS}</head><body>
<div class="container"><h1>YAEL<span style="color:#fff">SAVER</span></h1>
<div id="dash" class="card">Yükleniyor...</div>
<div class="card"><input id="link" placeholder="MEGA Link"><button class="btn" onclick="add()">BAŞLAT</button></div>
<div id="jobs"></div></div>
<script>
const k=new URLSearchParams(window.location.search).get('k')||localStorage.getItem('ukey');
if(k)localStorage.setItem('ukey',k); else location.href='/';
function load(){{fetch('/api/data',{{headers:{{'X-Key':k}}}}).then(r=>r.json()).then(d=>{{
if(d.error) return document.getElementById('dash').innerHTML=d.error;
document.getElementById('dash').innerHTML=`<b>${{d.user.name}}</b> - Kalan: ${{d.user.days}} Gün | Kota: ${{d.user.used.toFixed(1)}}/${{d.user.total}} GB`;
let h='';d.jobs.forEach(j=>{{h+=`<div class="card" style="border-left:3px solid #0f0"><small>${{j.date}}</small><br>${{j.link}}<br>Durum: <b>${{j.status}}</b></div>`}});
document.getElementById('jobs').innerHTML=h;}})}}
function add(){{fetch('/api/add',{{method:'POST',headers:{{'X-Key':k,'Content-Type':'application/json'}},body:JSON.stringify({{link:document.getElementById('link').value}})}}).then(r=>r.json()).then(d=>{{alert(d.msg);load()}})}}
setInterval(load,3000);load();
</script></body></html>"""

# --- ROUTING ---
@app.route('/')
def home(): return render_template_string(HTML_LOGIN)
@app.route('/panel')
def panel(): return render_template_string(HTML_PANEL)

# --- API (PANEL) ---
@app.route('/api/data')
def api_data():
    if not db: return jsonify({"error":"DB YOK"})
    k=request.headers.get('X-Key')
    u=users_col.find_one({"key":k})
    if not u: return jsonify({"error":"GEÇERSİZ ANAHTAR"})
    jobs=list(jobs_col.find({"user_key":k},{'_id':0}).sort("_id",-1).limit(10))
    now=get_now_ts(); days=int((u['expire_date']-now)/86400)
    return jsonify({"user":{"name":u['name'],"total":u['quota_gb'],"used":u.get('used_gb',0),"days":days if days>0 else 0},"jobs":jobs})

@app.route('/api/add', methods=['POST'])
def api_add():
    k=request.headers.get('X-Key')
    u=users_col.find_one({"key":k})
    if not u: return jsonify({"msg":"Yetkisiz"})
    if get_now_ts()>u['expire_date']: return jsonify({"msg":"SÜRE BİTTİ"})
    if u.get('used_gb',0)>=u['quota_gb']: return jsonify({"msg":"KOTA BİTTİ"})
    jobs_col.insert_one({"job_id":str(uuid.uuid4())[:8],"user_key":k,"link":request.json.get('link'),"status":"SIRADA","date":get_tr_time()})
    return jsonify({"msg":"Sıraya Alındı"})

# --- API (WORKER - BURASI ÇOK ÖNEMLİ) ---
# Worker bu adrese istek atıyor, bu fonksiyon olmazsa 404 hatası alırsın!
@app.route('/api/worker/get_job')
def w_get():
    if not db: return jsonify({"found":False})
    j=jobs_col.find_one({"status":"SIRADA"})
    if not j: return jsonify({"found":False})
    
    acc=accounts_col.find_one({"status":"ACTIVE"})
    if not acc:
        old=accounts_col.find_one({"status":"COOLDOWN"},sort=[("cooldown_start",1)])
        if old: accounts_col.update_one({"_id":old["_id"]},{"$set":{"status":"ACTIVE"}}); acc=old
        else: return jsonify({"found":False,"msg":"Hesap Yok"})
        
    jobs_col.update_one({"job_id":j['job_id']},{"$set":{"status":"ISLENIYOR"}})
    return jsonify({"found":True,"job":j['job_id'],"link":j['link'],"acc":{"email":acc['email'],"pass":acc['pass']}})

@app.route('/api/worker/done', methods=['POST'])
def w_done():
    d=request.json
    s=d.get('error') if d.get('error') else "TAMAMLANDI"
    if not d.get('error'):
        did=str(uuid.uuid4())[:8]; deliveries_col.insert_one({"id":did,"html":d['html']})
        jobs_col.update_one({"job_id":d['id']},{"$set":{"status":s,"delivery_id":did}})
        job=jobs_col.find_one({"job_id":d['id']})
        if job: users_col.update_one({"key":job['user_key']},{"$inc":{"used_gb":float(d.get('size',0))}})
    else:
        jobs_col.update_one({"job_id":d['id']},{"$set":{"status":s}})
    return jsonify({"ok":True})

# --- ADMIN (Kısa) ---
@app.route('/admin')
def admin(): return "Admin API Aktif" # Admin HTML'ini kısalttım sığsın diye
@app.route('/api/admin/add_acc',methods=['POST'])
def aa(): 
    if request.json.get('p')!=ADMIN_PASSWORD: return jsonify({"msg":"Err"})
    for l in request.json['accs'].split('\n'):
        if ':' in l: e,p=l.split(':',1); accounts_col.update_one({"email":e.strip()},{"$set":{"pass":p.strip(),"status":"ACTIVE"}},upsert=True)
    return jsonify({"msg":"OK"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))