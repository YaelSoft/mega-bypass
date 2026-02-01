import os
import datetime
import uuid
import logging
from flask import Flask, request, jsonify, render_template_string
import pymongo
import certifi

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# --- AYARLAR ---
MONGO_URI = os.environ.get("MONGO_URI")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "YASIN_BABA_33")
TELEGRAM_LINK = "https://t.me/yasin33"
V = "82.0" # Sürüm zorlayıcı

# --- DB ---
db = None
try:
    if MONGO_URI:
        client = pymongo.MongoClient(MONGO_URI, tlsCAFile=certifi.where(), serverSelectionTimeoutMS=5000)
        db = client['mega_leech']
        users_col, jobs_col, deliveries_col, accounts_col = db['users'], db['jobs'], db['deliveries'], db['accounts']
        logger.info(f"✅ DB Connected V{V}")
except Exception as e: logger.error(f"❌ DB Error: {e}")

def get_tr_time(): return (datetime.datetime.utcnow() + datetime.timedelta(hours=3)).strftime("%d.%m %H:%M")
def get_now_ts(): return datetime.datetime.utcnow().timestamp()

# --- CSS (CYBERPUNK FULL) ---
SHARED_CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Rajdhani:wght@700&family=Roboto+Mono&display=swap');
:root {{ --bg: #050505; --card: #111; --border: #222; --primary: #00ff9d; --text: #fff; }}
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{ background: var(--bg); color: var(--text); font-family: 'Rajdhani', sans-serif; padding: 20px; display: flex; flex-direction: column; align-items: center; }}
.container {{ width: 100%; max-width: 650px; }}
h1 {{ color: var(--primary); text-align: center; text-transform: uppercase; letter-spacing: 3px; margin-bottom: 20px; text-shadow: 0 0 15px var(--primary); }}
.card {{ background: var(--card); border: 1px solid var(--border); border-radius: 10px; padding: 20px; margin-bottom: 15px; position: relative; }}
.card::after {{ content: ''; position: absolute; left: 0; top: 0; width: 4px; height: 100%; background: var(--primary); }}
input, textarea {{ width: 100%; background: #000; border: 1px solid #333; color: #fff; padding: 12px; border-radius: 5px; margin-bottom: 10px; outline: none; font-family: 'Roboto Mono', monospace; }}
.btn {{ width: 100%; background: var(--primary); color: #000; font-weight: 800; padding: 15px; border: none; border-radius: 5px; cursor: pointer; text-transform: uppercase; transition: 0.2s; }}
.btn:hover {{ background: #fff; box-shadow: 0 0 20px var(--primary); }}
.stat-row {{ display: flex; justify-content: space-between; margin-bottom: 10px; }}
.badge {{ background: #222; padding: 5px 10px; border-radius: 4px; font-size: 0.8em; }}
a {{ color: var(--primary); text-decoration: none; }}
</style>
"""

# --- HTML TEMPLATES ---
HTML_LOGIN = f"<!DOCTYPE html><html><head><title>GİRİŞ</title>{SHARED_CSS}</head><body style='justify-content:center'><div class='card' style='width:400px;text-align:center'><h1>YAEL SAVER</h1><input id='k' type='password' placeholder='ANAHTAR'><button class='btn' onclick='go()'>SİSTEME SIZ</button><br><br><a href='{TELEGRAM_LINK}'>ANAHTAR SATIN AL</a></div><script>function go(){{location.href='/panel?k='+document.getElementById('k').value}}</script></body></html>"

HTML_PANEL = f"""
<!DOCTYPE html><html><head><title>PANEL</title>{SHARED_CSS}</head><body>
<div class="container"><h1>YAEL SAVER</h1>
<div id="dash" class="card">Yükleniyor...</div>
<div class="card"><h3>YENİ İNDİRME</h3><input id="link" placeholder="MEGA Linki..."><button class="btn" onclick="add()">İŞLEMİ BAŞLAT</button></div>
<div id="jobs"></div></div>
<script>
const k=new URLSearchParams(window.location.search).get('k')||localStorage.getItem('ukey');
if(k)localStorage.setItem('ukey',k); else location.href='/';
function load(){{
    fetch('/api/data',{{headers:{{'X-Key':k}}}}).then(r=>r.json()).then(d=>{{
        if(d.error) return document.getElementById('dash').innerHTML='HATA: '+d.error;
        let u=d.user; document.getElementById('dash').innerHTML=`<div class='stat-row'><b>${{u.name}}</b> <span style='color:#0f0'>${{u.days}} GÜN</span></div><div class='stat-row'><span>KOTA: ${{u.used.toFixed(2)}} / ${{u.total}} GB</span></div>`;
        let h=''; d.jobs.forEach(j=>{{ h+=`<div class='card' style='padding:15px'><div class='stat-row'><b>#${{j.id}}</b><small>${{j.date}}</small></div><div style='font-size:0.8em;color:#666;overflow:hidden;text-overflow:ellipsis;white-space:nowrap'>${{j.link}}</div><div class='stat-row' style='margin-top:10px'><span>${{j.log||'Sırada'}}</span> ${{j.status=='TAMAMLANDI'?'<a href="/teslimat/'+j.did+'">İNDİR</a>':j.status}}</div></div>` }});
        document.getElementById('jobs').innerHTML=h;
    }})
}}
function add(){{ fetch('/api/add',{{method:'POST',headers:{{'X-Key':k,'Content-Type':'application/json'}},body:JSON.stringify({{link:document.getElementById('link').value}})}}).then(r=>r.json()).then(d=>{{alert(d.msg);load()}})}}
setInterval(load,4000); load();
</script></body></html>"""

HTML_ADMIN = f"""
<!DOCTYPE html><html><head><title>ADMİN</title>{SHARED_CSS}</head><body>
<div class="container"><h1>PATRON PANELİ</h1>
<div id="stats" class="card">Yükleniyor...</div>
<div class="card"><h3>HESAP HAVUZU</h3><textarea id="accs" rows="4" placeholder="email:sifre"></textarea><button class="btn" onclick="addAcc()">MEGA HESAPLARI YÜKLE</button></div>
<div class="card" style="border-color:#0f0"><h3>LİSANS OLUŞTUR</h3>
<input id="u_n" placeholder="Müşteri Adı"><input id="u_k" placeholder="Özel Key (Opsiyonel)">
<div style="display:flex;gap:10px"><input type="number" id="u_g" placeholder="GB"><input type="number" id="u_d" placeholder="GÜN"></div>
<button class="btn" onclick="addUser()">LİSANSI OLUŞTUR</button></div>
<div id="users"></div></div>
<script>
const p=prompt("Admin Şifresi:");
function load(){{
    fetch('/api/admin/data?p='+p).then(r=>r.json()).then(d=>{{
        if(d.error) return alert("Şifre Yanlış!");
        document.getElementById('stats').innerHTML=`Aktif Mega: ${{d.stats.acc_active}} | Toplam Müşteri: ${{d.users.length}}`;
        let h=''; d.users.forEach(u=>{{ h+=`<div class='card'><b>${{u.name}}</b> (${{u.key}})<br>${{u.used.toFixed(1)}}/${{u.total}} GB | ${{u.days}} Gün <button onclick="del('${{u.key}}')" style='background:red;color:white;border:none;padding:5px;cursor:pointer'>SİL</button></div>` }});
        document.getElementById('users').innerHTML=h;
    }})
}}
function addAcc(){{ fetch('/api/admin/add_acc',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{p,accs:document.getElementById('accs').value}})}}).then(load) }}
function addUser(){{ fetch('/api/admin/add_user',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{p,name:document.getElementById('u_n').value,key:document.getElementById('u_k').value,gb:document.getElementById('u_g').value,days:document.getElementById('u_d').value}})}}).then(load) }}
function del(k){{ if(confirm('Sil?')) fetch('/api/admin/del_user',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{p,key:k}})}}).then(load) }}
load();
</script></body></html>"""

# --- API ROUTES ---
@app.route('/')
def home(): return render_template_string(HTML_LOGIN)
@app.route('/panel')
def panel(): return render_template_string(HTML_PANEL)
@app.route('/admin')
def admin(): return render_template_string(HTML_ADMIN)
@app.route('/teslimat/<id>')
def deliv(id): d=deliveries_col.find_one({{"id":id}}); return render_template_string(d['html']) if d else "HATA"

@app.route('/api/data')
def api_data():
    k=request.headers.get('X-Key'); u=users_col.find_one({{"key":k}})
    if not u: return jsonify({{"error":"Key Yok"}})
    jobs=list(jobs_col.find({{"user_key":k}},{{'_id':0}}).sort("_id",-1).limit(10))
    days=int((u['expire_date']-get_now_ts())/86400)
    return jsonify({{"user":{{"name":u['name'],"total":u['quota_gb'],"used":u.get('used_gb',0),"days":days if days>0 else 0}},"jobs":jobs}})

@app.route('/api/add', methods=['POST'])
def api_add():
    k=request.headers.get('X-Key'); u=users_col.find_one({{"key":k}})
    if not u or get_now_ts()>u['expire_date']: return jsonify({{"msg":"Süre Bitti"}})
    jobs_col.insert_one({{"job_id":str(uuid.uuid4())[:8],"user_key":k,"link":request.json.get('link'),"status":"SIRADA","date":get_tr_time()}})
    return jsonify({{"msg":"Başlatıldı 🚀"}})

@app.route('/api/worker/get_job')
def w_get():
    j=jobs_col.find_one({{"status":"SIRADA"}})
    if not j: return jsonify({{"found":False}})
    acc=accounts_col.find_one({{"status":"ACTIVE"}})
    if not acc: return jsonify({{"found":False}})
    jobs_col.update_one({{"job_id":j['job_id']}},{{"$set":{{"status":"ISLENIYOR"}}}})
    return jsonify({{"found":True,"job":j['job_id'],"link":j['link'],"acc":{{"email":acc['email'],"pass":acc['pass']}}}})

@app.route('/api/worker/done', methods=['POST'])
def w_done():
    d=request.json; s=d.get('error') or "TAMAMLANDI"
    if not d.get('error'):
        did=str(uuid.uuid4())[:8]; deliveries_col.insert_one({{"id":did,"html":d['html']}})
        jobs_col.update_one({{"job_id":d['id']}},{{"$set":{{"status":s,"delivery_id":did}}}})
        job=jobs_col.find_one({{"job_id":d['id']}})
        if job: users_col.update_one({{"key":job['user_key']}},{{"$inc":{{"used_gb":float(d.get('size',0))}}}})
    else: jobs_col.update_one({{"job_id":d['id']}},{{"$set":{{"status":s}}}})
    return jsonify({{"ok":True}})

@app.route('/api/admin/data')
def ad_d():
    if request.args.get('p')!=ADMIN_PASSWORD: return jsonify({{"error":"Auth"}})
    u_list=[]; now=get_now_ts()
    for u in users_col.find():
        days=int((u['expire_date']-now)/86400)
        u_list.append({{"name":u['name'],"key":u['key'],"total":u['quota_gb'],"used":u.get('used_gb',0),"days":days if days>0 else 0}})
    return jsonify({{"stats":{{"acc_active":accounts_col.count_documents({{"status":"ACTIVE"}})}},"users":u_list}})

@app.route('/api/admin/add_acc',methods=['POST'])
def ad_aa():
    if request.json.get('p')!=ADMIN_PASSWORD: return jsonify({{"msg":"Err"}})
    for l in request.json['accs'].split('\n'):
        if ':' in l: e,p=l.split(':',1); accounts_col.update_one({{"email":e.strip()}},{{"$set":{{"pass":p.strip(),"status":"ACTIVE"}}}},upsert=True)
    return jsonify({{"msg":"OK"}})

@app.route('/api/admin/add_user',methods=['POST'])
def ad_au():
    d=request.json; 
    if d.get('p')!=ADMIN_PASSWORD: return jsonify({{"msg":"Err"}})
    k=d.get('key') or str(uuid.uuid4())[:8]; exp=get_now_ts()+(int(d.get('days',30))*86400)
    users_col.insert_one({{"name":d.get('name'),"key":k,"quota_gb":float(d.get('gb',50)),"used_gb":0,"expire_date":exp}})
    return jsonify({{"msg":f"Key: {k}"}})

@app.route('/api/admin/del_user',methods=['POST'])
def ad_du():
    if request.json.get('p')!=ADMIN_PASSWORD: return jsonify({{"msg":"Err"}})
    users_col.delete_one({{"key":request.json.get('key')}})
    return jsonify({{"msg":"OK"}})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
