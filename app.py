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
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "Ata_Yasin536373")
TELEGRAM_USER = os.environ.get("TELEGRAM_USER", "YaelDesign") 
YAELSAVER_LINK = "https://t.me/YaelSaverBot"

if not MONGO_URI:
    client = None; db = None
else:
    try:
        client = MongoClient(MONGO_URI, tlsCAFile=certifi.where()); db = client['mega_leech']
        users_col = db['users']; jobs_col = db['jobs']; deliveries_col = db['deliveries']; accounts_col = db['accounts']
    except: pass

def get_tr_time(): return (datetime.datetime.utcnow() + datetime.timedelta(hours=3)).strftime("%d.%m %H:%M")

# --- CSS (CYBERPUNK PRO DESIGN) ---
SHARED_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&family=JetBrains+Mono:wght@400;700&display=swap');
    :root { --bg: #09090b; --card: #18181b; --border: #27272a; --primary: #3b82f6; --accent: #10b981; --text: #e4e4e7; --dim: #a1a1aa; }
    * { box-sizing: border-box; outline: none; }
    body { background: var(--bg); color: var(--text); font-family: 'Inter', sans-serif; margin: 0; min-height: 100vh; display: flex; flex-direction: column; align-items: center; }
    
    /* GİRİŞ EKRANI */
    .hero { text-align: center; padding: 60px 20px; width: 100%; max-width: 600px; animation: fadeIn 1s ease; }
    h1 { font-size: 3rem; font-weight: 800; letter-spacing: -2px; margin: 0; background: linear-gradient(to right, #fff, #666); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    .badge { background: rgba(59, 130, 246, 0.1); color: var(--primary); padding: 5px 12px; border-radius: 20px; font-size: 0.8rem; font-weight: 600; border: 1px solid rgba(59, 130, 246, 0.2); display: inline-block; margin-bottom: 15px; }
    
    .login-card { background: var(--card); border: 1px solid var(--border); border-radius: 16px; padding: 40px; box-shadow: 0 20px 40px -10px rgba(0,0,0,0.5); width: 100%; margin-top: 30px; }
    input { width: 100%; background: #000; border: 1px solid var(--border); padding: 15px; color: #fff; border-radius: 8px; font-family: 'JetBrains Mono'; margin-bottom: 15px; transition: 0.3s; }
    input:focus { border-color: var(--primary); box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.2); }
    
    .btn { width: 100%; background: var(--text); color: #000; padding: 15px; border-radius: 8px; font-weight: 700; border: none; cursor: pointer; transition: 0.2s; font-size: 1rem; }
    .btn:hover { transform: translateY(-2px); box-shadow: 0 10px 20px -5px rgba(255,255,255,0.2); }
    .btn-outline { background: transparent; border: 1px solid var(--border); color: var(--dim); margin-top: 10px; }
    .btn-outline:hover { border-color: var(--text); color: var(--text); }

    .features-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-top: 30px; text-align: left; }
    .feat { background: rgba(255,255,255,0.03); padding: 15px; border-radius: 8px; border: 1px solid var(--border); }
    .feat i { color: var(--accent); margin-right: 8px; }
    .feat h4 { margin: 0 0 5px 0; font-size: 0.9rem; color: #fff; }
    .feat p { margin: 0; font-size: 0.75rem; color: var(--dim); }

    /* PANEL */
    .dashboard { width: 100%; max-width: 1000px; padding: 20px; }
    .nav { display: flex; justify-content: space-between; align-items: center; padding: 20px 0; border-bottom: 1px solid var(--border); margin-bottom: 30px; }
    .stats-row { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }
    .stat-card { background: var(--card); border: 1px solid var(--border); padding: 20px; border-radius: 12px; }
    .stat-val { font-size: 1.8rem; font-weight: 700; color: #fff; font-family: 'JetBrains Mono'; margin: 5px 0; }
    .stat-lbl { font-size: 0.8rem; color: var(--dim); text-transform: uppercase; letter-spacing: 1px; }

    .action-area { background: var(--card); border: 1px solid var(--border); padding: 30px; border-radius: 16px; display: flex; gap: 10px; align-items: center; }
    
    .job-list { margin-top: 30px; }
    .job { background: var(--card); border: 1px solid var(--border); padding: 20px; border-radius: 12px; margin-bottom: 15px; display: flex; flex-direction: column; }
    .job-head { display: flex; justify-content: space-between; margin-bottom: 10px; }
    .status-badge { padding: 4px 10px; border-radius: 6px; font-size: 0.7rem; font-weight: bold; background: #222; color: #888; }
    .st-ISLENIYOR { background: rgba(59, 130, 246, 0.2); color: var(--primary); animation: pulse 2s infinite; }
    .st-TAMAMLANDI { background: rgba(16, 185, 129, 0.2); color: var(--accent); }
    .st-HATA { background: rgba(239, 68, 68, 0.2); color: #ef4444; }

    .progress-bar-bg { width: 100%; background: #222; height: 6px; border-radius: 3px; overflow: hidden; margin-top: 10px; }
    .progress-bar-fill { height: 100%; background: var(--accent); width: 0%; transition: width 0.5s; }

    @keyframes pulse { 0% { opacity: 1; } 50% { opacity: 0.5; } 100% { opacity: 1; } }
    @keyframes fadeIn { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
</style>
<script src="https://kit.fontawesome.com/a076d05399.js" crossorigin="anonymous"></script>
"""

HTML_LOGIN = f"""<!DOCTYPE html><html><head><title>YAEL VIP ACCESS</title>{SHARED_CSS}</head><body>
<div class="hero">
    <div class="badge">v6.7 PLATINUM</div>
    <h1>YAEL MEGA BYPASS</h1>
    <p style="color:var(--dim); font-size:1.1rem; margin-top:10px;">Profesyonel, Sınırsız ve Proxy Destekli Mega.nz İndirici</p>
    
    <div class="login-card">
        <input type="password" id="k" placeholder="VIP Erişim Anahtarınızı Girin">
        <button class="btn" onclick="go()">SİSTEME GİRİŞ YAP</button>
        <a href="https://t.me/{TELEGRAM_USER}" target="_blank" class="btn btn-outline" style="display:block; text-decoration:none; padding:12px;">VIP ÜYELİK SATIN AL</a>
    </div>

    <div class="features-grid">
        <div class="feat"><h4>🚀 Sınırsız Hız</h4><p>Mega kota sınırlarına takılmadan tam bant genişliği.</p></div>
        <div class="feat"><h4>🛡️ 2000+ Proxy</h4><p>Otomatik dönen proxy havuzu ile gizlilik.</p></div>
        <div class="feat"><h4>📦 Otomatik Zip</h4><p>Klasörleri sunucuda sıkıştırıp tek link yapar.</p></div>
        <div class="feat"><h4>⚡ Anlık Teslimat</h4><p>İndirme bittiği an özel linkiniz hazır.</p></div>
        <div class="feat"><h4>📂 Klasör Desteği</h4><p>Mega klasör linklerini sorunsuz indirir.</p></div>
        <div class="feat"><h4>🤖 YaelSaver Bot</h4><p>Telegram yasaklı içerikler için çözüm.</p></div>
    </div>
    
    <p style="margin-top:40px; color:#333; font-size:0.8rem">SYSTEM STATUS: <span style="color:var(--accent)">● OPERATIONAL</span></p>
</div>
<script>
function go(){{
    let k=document.getElementById('k').value;
    let hwid=localStorage.getItem('hwid')||crypto.randomUUID(); localStorage.setItem('hwid',hwid);
    document.querySelector('.btn').innerText = "DOĞRULANIYOR...";
    fetch('/api/login',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{key:k,hwid:hwid}})}})
    .then(r=>r.json()).then(d=>{{d.ok? (localStorage.setItem('ukey',k),location.href='/panel') : (alert(d.msg), document.querySelector('.btn').innerText = "SİSTEME GİRİŞ YAP")}});
}}</script></body></html>"""

HTML_PANEL = f"""<!DOCTYPE html><html><head><title>DASHBOARD</title>{SHARED_CSS}</head><body>
<div class="dashboard">
    <div class="nav">
        <div>
            <h2 style="margin:0">DASHBOARD</h2>
            <span style="color:var(--dim); font-size:0.8rem">Hoşgeldin, <span id="uid" style="color:#fff; font-family:'JetBrains Mono'">USER</span></span>
        </div>
        <div>
             <button onclick="logout()" style="background:none; border:none; color:var(--dim); cursor:pointer">ÇIKIŞ YAP</button>
        </div>
    </div>

    <div class="stats-row">
        <div class="stat-card">
            <div class="stat-lbl">KULLANILAN KOTA</div>
            <div class="stat-val"><span id="used">0</span> <span style="font-size:1rem; color:var(--dim)">GB</span></div>
            <div class="progress-bar-bg"><div id="bar" class="progress-bar-fill"></div></div>
        </div>
        <div class="stat-card">
            <div class="stat-lbl">TOPLAM LİMİT</div>
            <div class="stat-val"><span id="limit">0</span> <span style="font-size:1rem; color:var(--dim)">GB</span></div>
            <div style="font-size:0.8rem; color:var(--accent); margin-top:5px;">● Aktif Paket</div>
        </div>
        <div class="stat-card">
            <div class="stat-lbl">KALAN GÜN</div>
            <div class="stat-val" id="days">--</div>
            <div style="font-size:0.8rem; color:var(--dim); margin-top:5px;">Bitiş Tarihi: <span id="exp">--</span></div>
        </div>
    </div>

    <div class="action-area">
        <input id="link" placeholder="Mega.nz linkini (Dosya veya Klasör) buraya yapıştır..." style="margin:0;">
        <button class="btn" onclick="add()" style="width:200px; margin-bottom:0;">BAŞLAT 🚀</button>
    </div>

    <div style="display:flex; justify-content:space-between; align-items:flex-end; margin-top:30px; border-bottom:1px solid var(--border); padding-bottom:10px;">
        <h3 style="margin:0">İndirme Geçmişi</h3>
        <span onclick="clearHist()" style="color:var(--dim); cursor:pointer; font-size:0.8rem">Temizle</span>
    </div>

    <div id="jobs" class="job-list"></div>
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
        document.getElementById('exp').innerText = d.expire_date;
        
        let pct = (d.used/d.limit)*100;
        document.getElementById('bar').style.width = pct + '%';

        let h="";
        if(d.jobs.length == 0) h = "<div style='text-align:center; color:#333; padding:20px'>Henüz işlem yok. Yukarıdan link ekle.</div>";
        
        d.jobs.forEach(j=>{{
            let st_class = "st-" + (j.status=='ISLENIYOR'?'ISLENIYOR':(j.status=='TAMAMLANDI'?'TAMAMLANDI':'HATA'));
            let act = "";
            if(j.status=='TAMAMLANDI') act = `<a href="/teslimat/${{j.did}}" target="_blank" class="btn" style="padding:8px 20px; font-size:0.8rem; display:inline-block; width:auto; text-decoration:none">📥 DOSYAYI İNDİR</a>`;
            else if(j.status=='ISLENIYOR') act = `<button onclick="stop('${{j.id}}')" class="btn-outline" style="padding:5px 10px; font-size:0.7rem; width:auto;">İPTAL ET</button>`;
            
            h+=`<div class="job">
                <div class="job-head">
                    <span style="font-weight:600; font-family:'JetBrains Mono'; color:#fff; font-size:0.9rem; white-space:nowrap; overflow:hidden; width:70%">${{j.link}}</span>
                    <span class="status-badge ${{st_class}}">${{j.status}}</span>
                </div>
                <div style="color:var(--dim); font-size:0.8rem; font-family:'JetBrains Mono'; margin-bottom:10px;">> ${{j.log || "Kuyrukta..."}}</div>
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <span style="font-size:0.75rem; color:#444">${{j.date}}</span>
                    ${{act}}
                </div>
            </div>`;
        }});
        document.getElementById('jobs').innerHTML = h;
    }});
}}

function add(){{
    let l = document.getElementById('link').value;
    if(!l) return alert("Link boş olamaz!");
    document.querySelector('.btn').innerText = "EKLENİYOR...";
    fetch('/api/add',{{method:'POST',headers:{{'X-Key':k,'Content-Type':'application/json'}},body:JSON.stringify({{link:l}})}})
    .then(r=>r.json()).then(d=>{{ alert(d.msg); load(); document.getElementById('link').value=''; document.querySelector('.btn').innerText = "BAŞLAT 🚀";}});
}}
function stop(id){{ if(confirm('İşlem durdurulsun mu?')) fetch('/api/stop',{{method:'POST',headers:{{'X-Key':k,'Content-Type':'application/json'}},body:JSON.stringify({{id:id}})}}).then(()=>load()); }}
function clearHist(){{ if(confirm('Geçmiş temizlensin mi?')) fetch('/api/clear',{{headers:{{'X-Key':k}}}}).then(()=>load()); }}
function logout(){{ localStorage.removeItem('ukey'); location.href='/login'; }}
setInterval(load, 3000); load();
</script></body></html>"""

HTML_ADMIN = f"""<!DOCTYPE html><html><head><title>ADMIN</title>{SHARED_CSS}</head><body>
<div class="dashboard">
    <h1>YÖNETİCİ KONSOLU</h1>
    
    <div style="background:var(--card); padding:20px; border-radius:12px; border:1px solid var(--border); margin-bottom:20px;">
        <h3 style="margin-top:0">MEGA HESAP HAVUZU</h3>
        <textarea id="accs" rows="5" placeholder="email:pass" style="background:#000; border:1px solid #333; color:#fff; width:100%"></textarea>
        <button class="btn" onclick="addAcc()">HAVUZA YÜKLE</button>
        <div id="pool_count" style="margin-top:10px; color:var(--accent)">Yükleniyor...</div>
    </div>

    <div style="background:var(--card); padding:20px; border-radius:12px; border:1px solid var(--border); display:flex; gap:10px;">
        <input id="l" type="number" placeholder="GB Limiti" value="50">
        <input id="d" type="number" placeholder="Gün Süresi" value="30">
        <button class="btn" onclick="create()">ANAHTAR ÜRET</button>
    </div>
    <div id="res" style="font-family:'JetBrains Mono'; font-size:1.5rem; color:var(--accent); margin:20px 0; background:#000; padding:15px; border-radius:8px;"></div>
    
    <table id="tbl" style="width:100%; color:var(--dim); font-size:0.8rem; text-align:left;"></table>
</div>
<script>
const p = prompt("YÖNETİCİ ŞİFRESİ:");
function load(){{
    fetch('/api/admin/users?p='+p).then(r=>r.json()).then(d=>{{
        if(d.err) return;
        document.getElementById('pool_count').innerText = "AKTİF HESAP: " + d.pool_size;
        let h="<tr><th>KEY</th><th>KOTA</th><th>KALAN</th><th>DURUM</th><th>İŞLEM</th></tr>";
        d.users.forEach(u=>{{ h+=`<tr><td>${{u.key}}</td><td>${{u.used.toFixed(1)}}/${{u.limit}}</td><td>${{u.days_left}}</td><td>${{u.banned?'BAN':'OK'}}</td><td><button onclick="ban('${{u.key}}',${{u.banned?0:1}})" style="background:none; border:1px solid #444; color:#fff; cursor:pointer">X</button></td></tr>`; }});
        document.getElementById('tbl').innerHTML=h;
    }});
}}
function addAcc(){{ let a=document.getElementById('accs').value; fetch('/api/admin/add_acc',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{p:p,accs:a}})}}).then(r=>r.json()).then(d=>{{alert(d.msg);load()}}); }}
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
    return render_template_string(d['html']) if d else "Dosya bulunamadı."

# --- API ---
@app.route('/api/login', methods=['POST'])
def api_login():
    d=request.json; u=users_col.find_one({"key":d['key']})
    if not u or u.get('banned'): return jsonify({"ok":False,"msg":"Geçersiz Anahtar"})
    if u.get('expire_date') and datetime.datetime.utcnow() > u['expire_date']: return jsonify({"ok":False,"msg":"Süre Doldu"})
    if not u.get('hwid'): users_col.update_one({"key":d['key']},{"$set":{"hwid":d['hwid']}})
    elif u['hwid']!=d['hwid']: return jsonify({"ok":False,"msg":"Farklı Cihaz Tespit Edildi"})
    return jsonify({"ok":True})

@app.route('/api/data')
def api_data():
    k=request.headers.get('X-Key'); u=users_col.find_one({"key":k})
    if not u: return jsonify({"err":True})
    jobs=list(jobs_col.find({"user_key":k},{'_id':0}).sort("_id",-1))
    exp_str = u['expire_date'].strftime("%d.%m.%Y") if u.get('expire_date') else "Sınırsız"
    return jsonify({"used":u.get('used_gb',0),"limit":u.get('limit_gb',10),"days_left": (u['expire_date']-datetime.datetime.utcnow()).days if u.get('expire_date') else "∞","expire_date":exp_str,"jobs":[{"id":j['job_id'],"status":j['status'],"link":j['link'],"log":j.get('progress_log'),"did":j.get('delivery_id'),"date":j.get('date')} for j in jobs]})

@app.route('/api/add', methods=['POST'])
def api_add():
    k=request.headers.get('X-Key'); u=users_col.find_one({"key":k})
    if not u or u.get('used_gb',0)>=u.get('limit_gb',10): return jsonify({"msg":"KOTA LİMİTİ DOLDU!"})
    jobs_col.insert_one({"job_id":str(uuid.uuid4())[:8],"user_key":k,"link":request.json.get('link'),"status":"SIRADA","date":get_tr_time(),"stop_requested":False})
    return jsonify({"msg":"İndirme Sırasına Eklendi 🚀"})

@app.route('/api/stop', methods=['POST'])
def api_stop():
    jobs_col.update_one({"job_id":request.json.get('id')},{"$set":{"status":"DURDURULUYOR...","stop_requested":True}})
    return jsonify({"ok":True})
@app.route('/api/clear', methods=['GET'])
def api_clear():
    k=request.headers.get('X-Key'); jobs_col.delete_many({"user_key":k}); return jsonify({"ok":True})

# --- WORKER API ---
@app.route('/api/worker/get')
def w_get():
    j=jobs_col.find_one({"status":"SIRADA"})
    if j: 
        jobs_col.update_one({"job_id":j['job_id']},{"$set":{"status":"ISLENIYOR"}})
        acc = accounts_col.find_one({"status":"ACTIVE"})
        return jsonify({"found":True,"job":j['job_id'],"link":j['link'], "account": {"email":acc['email'], "pass":acc['pass']} if acc else None})
    return jsonify({"found":False})

@app.route('/api/worker/update', methods=['POST'])
def w_upd():
    d=request.json; jobs_col.update_one({"job_id":d['id']},{"$set":{"progress_log":d['msg']}})
    return jsonify({"stop":bool(jobs_col.find_one({"job_id":d['id']}).get('stop_requested'))})

@app.route('/api/worker/done', methods=['POST'])
def w_done():
    d=request.json; jid=d['id']; j=jobs_col.find_one({"job_id":jid})
    if d.get('error'): jobs_col.update_one({"job_id":jid},{"$set":{"status":d['error']}})
    else:
        did=str(uuid.uuid4())[:8]; deliveries_col.insert_one({"id":did,"html":d['html']})
        jobs_col.update_one({"job_id":jid},{"$set":{"status":"TAMAMLANDI","delivery_id":did}})
        users_col.update_one({"key":j['user_key']},{"$inc":{"used_gb":d['size']}}) # ARTIK NET ZIP BOYUTU GELİYOR
    return jsonify({"ok":True})

# --- ADMIN API ---
@app.route('/api/admin/users')
def adm_u():
    if request.args.get('p')!=ADMIN_PASSWORD: return jsonify({"err":True})
    users = list(users_col.find())
    return jsonify({"users":[{"key": u['key'], "limit": u.get('limit_gb',0), "used": u.get('used_gb',0), "days_left": (u['expire_date']-datetime.datetime.utcnow()).days if u.get('expire_date') else "∞", "banned": u.get('banned',False)} for u in users], "pool_size":accounts_col.count_documents({"status":"ACTIVE"})})

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
    count=0
    for l in d.get('accs','').split('\n'):
        if ':' in l and not accounts_col.find_one({"email":l.split(':')[0].strip()}):
            accounts_col.insert_one({"email":l.split(':')[0].strip(), "pass":l.split(':')[1].strip(), "status":"ACTIVE"}); count+=1
    return jsonify({"msg":f"{count} Hesap Eklendi"})

if __name__ == '__main__': app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
