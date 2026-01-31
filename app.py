import os
import datetime
import uuid
import logging
from flask import Flask, request, jsonify, render_template_string
import pymongo
import certifi

# Loglama Ayarı
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

# --- CSS (CYBERPUNK NEON TASARIM) ---
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
.toast { visibility: hidden; min-width: 250px; background-color: #333; color: #fff; text-align: center; border-radius: 4px; padding: 16px; position: fixed; z-index: 1; left: 50%; bottom: 30px; transform: translateX(-50%); font-size: 17px; border: 1px solid var(--primary); box-shadow: 0 0 15px rgba(0,0,0,0.5); }
.toast.show { visibility: visible; animation: fadein 0.5s, fadeout 0.5s 2.5s; }
@keyframes fadein { from {bottom: 0; opacity: 0;} to {bottom: 30px; opacity: 1;} }
@keyframes fadeout { from {bottom: 30px; opacity: 1;} to {bottom: 0; opacity: 0;} }
a { text-decoration: none; color: inherit; }
.vip-box { background: linear-gradient(45deg, #111, #222); border: 1px solid #ffcc00; color: #ffcc00; text-align: center; padding: 15px; border-radius: 8px; cursor: pointer; animation: pulse 2s infinite; }
@keyframes pulse { 0% { box-shadow: 0 0 0 0 rgba(255, 204, 0, 0.4); } 70% { box-shadow: 0 0 0 10px rgba(255, 204, 0, 0); } 100% { box-shadow: 0 0 0 0 rgba(255, 204, 0, 0); } }
</style>
"""

# --- JS (TOAST) ---
SHARED_JS = """
<script>
function showToast(msg) {
    var x = document.getElementById("toast");
    x.innerText = msg;
    x.className = "toast show";
    setTimeout(function(){ x.className = x.className.replace("show", ""); }, 3000);
}
</script>
"""

# --- HTML TEMPLATES ---
HTML_LOGIN = f"""
<!DOCTYPE html>
<html>
<head><title>GİRİŞ</title>{SHARED_CSS}</head>
<body style="justify-content:center">
    <div class="card" style="width:100%;max-width:400px;text-align:center;border-top:3px solid var(--primary)">
        <h1 style="margin-bottom:5px">YAEL<span style="color:#fff">SAVER</span></h1>
        <p style="color:#666;margin-bottom:25px">VIP DOWNLOAD GATEWAY</p>
        <input id="k" type="password" placeholder="🔑 GİRİŞ ANAHTARI" style="text-align:center">
        <button class="btn" onclick="go()">GİRİŞ YAP</button>
        <div style="margin-top:20px">
            <a href="{TELEGRAM_LINK}" target="_blank" style="color:var(--primary);font-weight:bold;text-decoration:underline">ANAHTAR SATIN AL</a>
        </div>
    </div>
    <div id="toast" class="toast"></div>
    {SHARED_JS}
    <script>
        function go() {{
            let key = document.getElementById('k').value.trim();
            if(!key) return showToast("Lütfen anahtar girin!");
            location.href = '/panel?k=' + key;
        }}
    </script>
</body>
</html>
"""

HTML_PANEL = f"""
<!DOCTYPE html>
<html>
<head><title>PANEL</title>{SHARED_CSS}</head>
<body>
    <div class="container">
        <h1>YAEL<span style="color:#fff">SAVER</span></h1>
        
        <div id="dashboard" class="card" style="border-color:#333">
            <div style="text-align:center;padding:20px;color:#666">Veriler Yükleniyor...</div>
        </div>

        <div class="card">
            <h3 style="color:#fff;margin-bottom:10px">YENİ İNDİRME</h3>
            <input id="link" placeholder="MEGA.NZ Linki Yapıştır...">
            <button class="btn" onclick="addJob()">🚀 İNDİRMEYİ BAŞLAT</button>
        </div>

        <a href="{TELEGRAM_LINK}" target="_blank">
            <div class="vip-box">
                <h3 style="margin:0">👑 LİMİT ARTTIR / VIP AL</h3>
                <small>Paket Yükseltmek İçin Tıkla</small>
            </div>
        </a>
        <br>

        <div id="jobs"></div>
    </div>
    <div id="toast" class="toast"></div>
    {SHARED_JS}
    <script>
        const urlParams = new URLSearchParams(window.location.search);
        const k = urlParams.get('k') || localStorage.getItem('ukey');
        if(k) localStorage.setItem('ukey', k); else location.href = "/";

        function load() {{
            fetch('/api/data', {{ headers: {{ 'X-Key': k }} }})
            .then(r => r.json())
            .then(d => {{
                if(d.error) {{
                    document.getElementById('dashboard').innerHTML = `<div style='text-align:center;color:red'><h3>HATALI ANAHTAR</h3><a href='/' class='btn' style='display:inline-block;width:auto;padding:10px 20px;margin-top:10px'>ÇIKIŞ</a></div>`;
                    return;
                }}

                let u = d.user;
                let percent = (u.used / u.total) * 100;
                if(percent > 100) percent = 100;

                document.getElementById('dashboard').innerHTML = `
                    <div class="stat-row">
                        <b style="font-size:1.2em;color:#fff">${{u.name}}</b>
                        <span style="color:${{u.days>0?'var(--primary)':'red'}}">${{u.days}} GÜN KALDI</span>
                    </div>
                    <div class="stat-row" style="margin-top:10px">
                        <span>KULLANILAN: <b>${{u.used.toFixed(2)}} GB</b></span>
                        <span>TOPLAM: <b>${{u.total}} GB</b></span>
                    </div>
                    <div style="width:100%;background:#222;height:8px;border-radius:4px;margin-top:5px;overflow:hidden">
                        <div style="width:${{percent}}%;background:var(--primary);height:100%;transition:width 0.5s"></div>
                    </div>
                `;

                let h = "";
                d.jobs.forEach(j => {{
                    let st = j.status;
                    let stHtml = `<span style='color:#fa0'>${{st}}</span>`;
                    
                    if(st == 'TAMAMLANDI') stHtml = `<a href="/teslimat/${{j.did}}" target="_blank" style="color:var(--primary);font-weight:bold;text-decoration:underline">📥 DOSYAYI İNDİR</a>`;
                    else if(st.includes('HATA')) stHtml = `<span style='color:var(--danger)'>${{st}}</span>`;

                    h += `<div class="card" style="padding:15px;border-left:3px solid var(--primary)">
                        <div class="stat-row"><b style="color:#fff">#${{j.id}}</b><small style="color:#666">${{j.date}}</small></div>
                        <div style="color:#888;font-size:0.8em;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;margin-bottom:10px">${{j.link}}</div>
                        <div class="stat-row" style="border-top:1px solid #222;padding-top:10px;align-items:center">
                            <span style="font-family:'Roboto Mono';font-size:0.8em;color:#aaa">${{j.log||'Bekleniyor...'}}</span>
                            <div>${{stHtml}}</div>
                        </div>
                    </div>`;
                }});
                document.getElementById('jobs').innerHTML = h || "<div style='text-align:center;color:#444;margin-top:20px'>İşlem geçmişi boş.</div>";
            }})
            .catch(e => console.error(e));
        }}

        function addJob() {{
            let link = document.getElementById('link').value.trim();
            if(!link) return showToast("Link boş olamaz!");

            fetch('/api/add', {{
                method: 'POST',
                headers: {{ 'X-Key': k, 'Content-Type': 'application/json' }},
                body: JSON.stringify({{ link: link }})
            }})
            .then(r => r.json())
            .then(d => {{
                if(d.buy_link) {{
                    if(confirm(d.msg + "\\nTelegram'a gitmek ister misin?")) window.open(d.buy_link, "_blank");
                }} else {{
                    showToast(d.msg);
                    document.getElementById('link').value = "";
                    load();
                }}
            }})
        }}

        setInterval(load, 3000); load();
    </script>
</body>
</html>
"""

HTML_ADMIN = f"""
<!DOCTYPE html>
<html>
<head><title>PATRON</title>{SHARED_CSS}</head>
<body>
    <div class="container">
        <h1>ADMIN<span style="color:#fff">PANEL</span></h1>
        
        <div id="stats" class="card">Yükleniyor...</div>

        <div class="card">
            <h3>HAVUZ YÖNETİMİ</h3>
            <textarea id="accs" rows="5" placeholder="email:sifre (Her satıra bir tane)"></textarea>
            <button class="btn" onclick="addAcc()">HESAPLARI YÜKLE</button>
        </div>

        <div class="card" style="border-color:var(--primary)">
            <h3>MÜŞTERİ OLUŞTUR</h3>
            <input id="u_name" placeholder="Müşteri Adı">
            <input id="u_key" placeholder="Özel Anahtar (Boşsa Otomatik)">
            <div style="display:flex;gap:10px">
                <input type="number" id="u_gb" placeholder="GB Limit">
                <input type="number" id="u_days" placeholder="Gün Süresi">
            </div>
            <button class="btn" onclick="addUser()">OLUŞTUR VE SAT</button>
        </div>

        <div id="users"></div>
    </div>
    <div id="toast" class="toast"></div>
    {SHARED_JS}
    <script>
        const p = prompt("ADMIN ŞİFRESİ:");
        
        function load() {{
            fetch('/api/admin/data?p=' + p).then(r => r.json()).then(d => {{
                if(d.error) return document.body.innerHTML = "<h1 style='color:red;text-align:center'>ŞİFRE YANLIŞ</h1>";
                
                document.getElementById('stats').innerHTML = `
                    <div class="stat-row"><span>Toplam Mega Hesabı:</span> <b>${{d.stats.acc_total}}</b></div>
                    <div class="stat-row"><span>Aktif Hesaplar:</span> <b style="color:var(--primary)">${{d.stats.acc_active}}</b></div>
                    <div class="stat-row"><span>Toplam Müşteri:</span> <b>${{d.users.length}}</b></div>
                `;

                let h = "";
                d.users.forEach(u => {{
                    h += `<div class="card" style="padding:15px;background:#0a0a0a">
                        <div class="stat-row"><b style="color:#fff;font-size:1.1em">${{u.name}}</b> <span style="color:#666">${{u.key}}</span></div>
                        <div class="stat-row" style="border-bottom:1px solid #333;padding-bottom:5px;margin-bottom:10px">
                            <span>${{u.used.toFixed(1)}} / ${{u.total}} GB</span>
                            <span>Kalan: ${{u.days}} Gün</span>
                        </div>
                        <button class="btn" style="background:#333;padding:8px;font-size:0.8em" onclick="del('${{u.key}}')">MÜŞTERİYİ SİL</button>
                    </div>`;
                }});
                document.getElementById('users').innerHTML = h;
            }});
        }}

        function addAcc() {{
            let data = document.getElementById('accs').value;
            if(!data) return showToast("Boş veri girilemez!");
            fetch('/api/admin/add_acc', {{
                method: 'POST',
                headers: {{'Content-Type':'application/json'}},
                body: JSON.stringify({{ p: p, accs: data }})
            }}).then(r=>r.json()).then(d=>{{ showToast(d.msg); document.getElementById('accs').value=""; load(); }});
        }}

        function addUser() {{
            fetch('/api/admin/add_user', {{
                method: 'POST',
                headers: {{'Content-Type':'application/json'}},
                body: JSON.stringify({{
                    p: p,
                    name: document.getElementById('u_name').value,
                    key: document.getElementById('u_key').value,
                    gb: document.getElementById('u_gb').value,
                    days: document.getElementById('u_days').value
                }})
            }}).then(r=>r.json()).then(d=>{{ showToast(d.msg); load(); }});
        }}

        function del(k) {{
            if(confirm('Silmek istediğine emin misin?')) {{
                fetch('/api/admin/del_user', {{
                    method: 'POST',
                    headers: {{'Content-Type':'application/json'}},
                    body: JSON.stringify({{ p: p, key: k }})
                }}).then(()=>{{ showToast("Silindi"); load(); }});
            }}
        }}
        load();
    </script>
</body>
</html>
"""

# --- ROUTING ---
@app.route('/')
def home(): return render_template_string(HTML_LOGIN)
@app.route('/panel')
def panel(): return render_template_string(HTML_PANEL)
@app.route('/admin')
def admin(): return render_template_string(HTML_ADMIN)
@app.route('/teslimat/<id>')
def deliv(id):
    if not db: return "Sistem Bakımda"
    d = deliveries_col.find_one({"id": id})
    return render_template_string(d['html']) if d else "Dosya Bulunamadı"

# --- API (PANEL) ---
@app.route('/api/data')
def api_data():
    if not db: return jsonify({"error":"DB YOK"})
    k=request.headers.get('X-Key')
    u=users_col.find_one({"key":k})
    if not u: return jsonify({"error":"GEÇERSİZ ANAHTAR"})
    jobs=list(jobs_col.find({"user_key":k},{'_id':0}).sort("_id",-1).limit(20))
    now=get_now_ts(); days=int((u['expire_date']-now)/86400)
    return jsonify({"user":{"name":u['name'],"total":u['quota_gb'],"used":u.get('used_gb',0),"days":days if days>0 else 0},"jobs":jobs})

@app.route('/api/add', methods=['POST'])
def api_add():
    if not db: return jsonify({"msg":"Sistem Hatası"})
    k=request.headers.get('X-Key')
    u=users_col.find_one({"key":k})
    if not u: return jsonify({"msg":"Yetkisiz"})
    now=get_now_ts()
    if now>u['expire_date']: return jsonify({"msg":"⏳ SÜRE BİTTİ!","buy_link":TELEGRAM_LINK})
    if u.get('used_gb',0)>=u['quota_gb']: return jsonify({"msg":"💾 KOTA BİTTİ!","buy_link":TELEGRAM_LINK})
    jobs_col.insert_one({"job_id":str(uuid.uuid4())[:8],"user_key":k,"link":request.json.get('link'),"status":"SIRADA","date":get_tr_time()})
    return jsonify({"msg":"Sıraya Alındı 🚀"})

# --- API (WORKER) ---
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

@app.route('/api/worker/report_quota',methods=['POST'])
def w_q():
    if db: accounts_col.update_one({"email":request.json.get('email')},{"$set":{"status":"COOLDOWN","cooldown_start":datetime.datetime.utcnow()}})
    return jsonify({"ok":True})
@app.route('/api/worker/update',methods=['POST'])
def w_u():
    if db: jobs_col.update_one({"job_id":request.json['id']},{"$set":{"progress_log":request.json['msg']}})
    return jsonify({"ok":True})
@app.route('/api/worker/done',methods=['POST'])
def w_d():
    d=request.json; s=d.get('error') if d.get('error') else "TAMAMLANDI"
    if not d.get('error'):
        did=str(uuid.uuid4())[:8]; deliveries_col.insert_one({"id":did,"html":d['html']})
        jobs_col.update_one({"job_id":d['id']},{"$set":{"status":s,"delivery_id":did}})
        job=jobs_col.find_one({"job_id":d['id']})
        if job: users_col.update_one({"key":job['user_key']},{"$inc":{"used_gb":float(d.get('size',0))}})
    else: jobs_col.update_one({"job_id":d['id']},{"$set":{"status":s}})
    return jsonify({"ok":True})

# --- API (ADMIN) ---
@app.route('/api/admin/data')
def ad_d():
    if request.args.get('p')!=ADMIN_PASSWORD: return jsonify({"error":"Auth"})
    u_list=[]; now=get_now_ts()
    for u in users_col.find():
        days=int((u['expire_date']-now)/86400)
        u_list.append({"name":u['name'],"key":u['key'],"total":u['quota_gb'],"used":u.get('used_gb',0),"days":days if days>0 else 0})
    return jsonify({"stats":{"acc_total":accounts_col.count_documents({}),"acc_active":accounts_col.count_documents({"status":"ACTIVE"})},"users":u_list})

@app.route('/api/admin/add_acc',methods=['POST'])
def ad_aa():
    if request.json.get('p')!=ADMIN_PASSWORD: return jsonify({"msg":"Auth"})
    c=0
    for l in request.json.get('accs','').split('\n'):
        if ':' in l: e,p=l.split(':',1); accounts_col.update_one({"email":e.strip()},{"$set":{"pass":p.strip(),"status":"ACTIVE"}},upsert=True); c+=1
    return jsonify({"msg":f"{c} Hesap Eklendi"})

@app.route('/api/admin/add_user',methods=['POST'])
def ad_au():
    d=request.json; 
    if d.get('p')!=ADMIN_PASSWORD: return jsonify({"msg":"Auth"})
    k=d.get('key') or str(uuid.uuid4())[:8]; exp=get_now_ts()+(int(d.get('days',30))*86400)
    users_col.insert_one({"name":d.get('name'),"key":k,"quota_gb":float(d.get('gb',50)),"used_gb":0,"expire_date":exp})
    return jsonify({"msg":f"Kullanıcı: {k}"})

@app.route('/api/admin/del_user',methods=['POST'])
def ad_du():
    if request.json.get('p')!=ADMIN_PASSWORD: return jsonify({"msg":"Auth"}); 
    users_col.delete_one({"key":request.json.get('key')})
    return jsonify({"msg":"Silindi"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))