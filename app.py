import os
import uuid
import time
import pymongo
from flask import Flask, render_template_string, request, jsonify, session, redirect
from pymongo import MongoClient

app = Flask(__name__)
app.secret_key = "COMMANDER_V55_SECRET"

# ==================== AYARLAR ====================
# Render Environment Variables kısmına MONGO_URI eklemeyi unutma!
MONGO_URI = os.environ.get("MONGO_URI")
ADMIN_PASSWORD = "YASIN_BABA_123" # Admin şifren

# ==================== DB BAĞLANTISI ====================
if not MONGO_URI:
    print("❌ HATA: MONGO_URI EKSİK! Render ayarlarına ekle.")

client = MongoClient(MONGO_URI)
db = client['mega_leech']
queue = db['queue']
accounts_col = db['accounts']
proxies_col = db['proxies']

# ==================== HTML ARAYÜZ (BASİT VE GÜÇLÜ) ====================
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MEGA COMMANDER V55</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <style>
        body { background-color: #0f172a; color: white; font-family: sans-serif; }
        .log-box { font-family: 'Courier New', monospace; font-size: 13px; }
        ::-webkit-scrollbar { width: 8px; }
        ::-webkit-scrollbar-track { background: #1e293b; }
        ::-webkit-scrollbar-thumb { background: #475569; border-radius: 4px; }
    </style>
</head>
<body class="min-h-screen p-4 md:p-8">

    {% if not session.logged_in %}
    <div class="flex items-center justify-center h-screen">
        <form action="/login" method="POST" class="bg-slate-800 p-8 rounded-xl shadow-2xl w-96 border border-slate-700">
            <h2 class="text-2xl font-bold mb-6 text-center text-blue-400"><i class="fa-solid fa-shield-halved"></i> GİRİŞ</h2>
            <input type="password" name="password" class="w-full p-3 bg-slate-900 border border-slate-600 rounded mb-4 text-white" placeholder="Şifre" required>
            <button class="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 rounded transition">GİRİŞ YAP</button>
        </form>
    </div>
    {% else %}

    <div class="max-w-6xl mx-auto grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        <div class="lg:col-span-2 space-y-6">
            <div class="bg-slate-800 p-6 rounded-xl border border-slate-700 shadow-lg">
                <div class="flex justify-between items-center mb-4">
                    <h2 class="text-xl font-bold text-green-400"><i class="fa-solid fa-cloud-arrow-down"></i> İNDİRME PANELİ</h2>
                    <a href="/logout" class="text-sm text-slate-400 hover:text-white">Çıkış</a>
                </div>
                
                <div class="flex gap-2 mb-4">
                    <input type="text" id="megaLink" class="flex-grow p-4 bg-slate-900 border border-slate-600 rounded-lg text-white focus:border-blue-500 outline-none" placeholder="https://mega.nz/...">
                    <button onclick="startTask()" id="startBtn" class="bg-green-600 hover:bg-green-700 px-8 rounded-lg font-bold transition">BAŞLAT</button>
                </div>

                <div id="logContainer" class="hidden">
                    <div class="bg-black rounded-t-lg p-2 flex justify-between items-center border-b border-slate-800">
                        <span class="text-xs text-slate-400">CANLI LOGLAR</span>
                        <div class="h-2 w-2 rounded-full bg-green-500 animate-pulse"></div>
                    </div>
                    <div id="logs" class="log-box bg-black/80 h-64 overflow-y-auto p-4 text-green-400 space-y-1 rounded-b-lg border border-slate-800"></div>
                </div>

                <div id="resultArea" class="hidden mt-6 text-center bg-green-900/20 p-6 rounded-xl border border-green-500/30">
                    <h3 class="text-2xl font-bold text-white mb-2">DOSYA HAZIR!</h3>
                    <a id="dlButton" href="#" class="inline-block bg-green-600 hover:bg-green-700 text-white px-8 py-4 rounded-xl font-bold shadow-lg transition my-4">
                        <i class="fa-solid fa-download"></i> İNDİR
                    </a>
                    <button onclick="location.reload()" class="block mx-auto text-slate-400 text-sm hover:text-white">Yeni İşlem</button>
                </div>
            </div>

            <div class="bg-red-900/20 p-4 rounded-xl border border-red-500/30 flex justify-between items-center">
                <div>
                    <h3 class="font-bold text-red-400">SİSTEM KİLİTLENDİ Mİ?</h3>
                    <p class="text-xs text-slate-400">Loglar akmıyorsa veya sistem donduysa buna bas.</p>
                </div>
                <a href="/reset" class="bg-red-600 hover:bg-red-700 text-white px-6 py-3 rounded-lg font-bold text-sm shadow-lg shadow-red-600/20">
                    <i class="fa-solid fa-skull"></i> SİSTEMİ SIFIRLA (RESET)
                </a>
            </div>
        </div>

        <div class="space-y-6">
            <div class="grid grid-cols-2 gap-4">
                <div class="bg-slate-800 p-4 rounded-xl text-center border-t-4 border-blue-500">
                    <div class="text-3xl font-bold">{{ acc_count }}</div>
                    <div class="text-xs text-slate-400">HESAP</div>
                </div>
                <div class="bg-slate-800 p-4 rounded-xl text-center border-t-4 border-purple-500">
                    <div class="text-3xl font-bold">{{ proxy_count }}</div>
                    <div class="text-xs text-slate-400">PROXY</div>
                </div>
            </div>

            <div class="bg-slate-800 p-5 rounded-xl border border-slate-700">
                <h3 class="font-bold text-sm mb-2 text-slate-300">HESAP EKLE</h3>
                <form action="/add_acc" method="POST">
                    <textarea name="data" class="w-full bg-slate-900 p-2 text-xs h-20 rounded border border-slate-600 text-white mb-2" placeholder="email:sifre"></textarea>
                    <button class="w-full bg-blue-600 py-2 rounded text-sm font-bold">EKLE</button>
                </form>
            </div>

            <div class="bg-slate-800 p-5 rounded-xl border border-slate-700">
                <h3 class="font-bold text-sm mb-2 text-slate-300">PROXY EKLE</h3>
                <form action="/add_proxy" method="POST">
                    <textarea name="data" class="w-full bg-slate-900 p-2 text-xs h-20 rounded border border-slate-600 text-white mb-2" placeholder="http://user:pass@ip:port"></textarea>
                    <button class="w-full bg-purple-600 py-2 rounded text-sm font-bold">EKLE</button>
                </form>
            </div>
        </div>
    </div>

    <script>
        let taskId = null;
        let timer = null;

        async function startTask() {
            const link = document.getElementById('megaLink').value;
            if(!link) return alert("Link boş olamaz!");

            // Arayüzü hazırla
            document.getElementById('startBtn').disabled = true;
            document.getElementById('startBtn').innerText = "BAĞLANIYOR...";
            document.getElementById('logContainer').classList.remove('hidden');
            document.getElementById('resultArea').classList.add('hidden');
            const logsDiv = document.getElementById('logs');
            logsDiv.innerHTML = '<div class="text-blue-400">> Sunucuya bağlanılıyor...</div>';

            try {
                const req = await fetch('/api/start', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({link: link})
                });
                const res = await req.json();

                if(res.success) {
                    taskId = res.taskId;
                    logsDiv.innerHTML += '<div class="text-yellow-400">> Görev Worker\\'a iletildi (ID: '+taskId.substr(0,4)+')</div>';
                    startPolling();
                } else {
                    logsDiv.innerHTML += '<div class="text-red-500 font-bold">> HATA: '+res.msg+'</div>';
                    resetUI();
                }
            } catch(e) {
                logsDiv.innerHTML += '<div class="text-red-500 font-bold">> SUNUCU HATASI. SAYFAYI YENİLEYİN.</div>';
            }
        }

        function startPolling() {
            if(timer) clearInterval(timer);
            timer = setInterval(async () => {
                if(!taskId) return;
                try {
                    const req = await fetch('/api/status/' + taskId);
                    const res = await req.json();

                    if(res.log) {
                        const logsDiv = document.getElementById('logs');
                        // Son log ekranda yoksa ekle
                        if(!logsDiv.lastElementChild || logsDiv.lastElementChild.innerText !== "> " + res.log) {
                            const color = res.status.includes('HATA') ? 'text-red-500' : 'text-green-400';
                            logsDiv.innerHTML += `<div class="${color}">> ${res.log}</div>`;
                            logsDiv.scrollTop = logsDiv.scrollHeight;
                        }
                    }

                    if(res.status === 'TAMAMLANDI') {
                        clearInterval(timer);
                        document.getElementById('logContainer').classList.add('hidden');
                        document.getElementById('resultArea').classList.remove('hidden');
                        document.getElementById('dlButton').href = res.result.url;
                        document.getElementById('startBtn').innerText = "TAMAMLANDI";
                    } else if(res.status.includes('HATA')) {
                        clearInterval(timer);
                        resetUI();
                    }
                } catch(e) {}
            }, 1000); // 1 Saniyede bir güncelle (HIZLI)
        }

        function resetUI() {
            document.getElementById('startBtn').disabled = false;
            document.getElementById('startBtn').innerText = "BAŞLAT";
        }
    </script>
    {% endif %}

</body>
</html>
"""

# ==================== BACKEND ====================
@app.route('/', methods=['GET'])
def index():
    if not session.get('logged_in'): return render_template_string(HTML_TEMPLATE)
    
    acc_count = accounts_col.count_documents({"status": "ACTIVE"})
    proxy_count = proxies_col.count_documents({})
    return render_template_string(HTML_TEMPLATE, acc_count=acc_count, proxy_count=proxy_count, session=session)

@app.route('/login', methods=['POST'])
def login():
    if request.form.get('password') == ADMIN_PASSWORD:
        session['logged_in'] = True
    return redirect('/')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# --- KONTROL MEKANİZMASI ---
@app.route('/reset')
def reset_system():
    if not session.get('logged_in'): return redirect('/')
    # SADECE KUYRUĞU SİL, HESAPLARI SİLME!
    queue.delete_many({}) 
    return redirect('/')

@app.route('/add_acc', methods=['POST'])
def add_acc():
    if not session.get('logged_in'): return redirect('/')
    raw = request.form.get('data', '')
    for line in raw.split('\n'):
        if ':' in line:
            u, p = line.strip().split(':', 1)
            if not accounts_col.find_one({"email": u}):
                accounts_col.insert_one({"email": u, "password": p, "status": "ACTIVE"})
    return redirect('/')

@app.route('/add_proxy', methods=['POST'])
def add_proxy():
    if not session.get('logged_in'): return redirect('/')
    proxies_col.delete_many({}) # Temizle ve yeni yükle
    raw = request.form.get('data', '')
    for line in raw.split('\n'):
        if line.strip():
            proxies_col.insert_one({"ip": line.strip()})
    return redirect('/')

# --- API (WORKER İÇİN) ---
@app.route('/api/start', methods=['POST'])
def api_start():
    if not session.get('logged_in'): return jsonify({"success": False, "msg": "Giriş yapın"})
    link = request.json.get('link')
    tid = str(uuid.uuid4())
    # Worker V54'e uygun kayıt
    queue.insert_one({
        "task_id": tid,
        "link": link,
        "status": "SIRADA",
        "log": "Worker bekleniyor...",
        "created_at": time.time()
    })
    return jsonify({"success": True, "taskId": tid})

@app.route('/api/status/<tid>')
def api_status(tid):
    job = queue.find_one({"task_id": tid}, {"_id": 0})
    if job: return jsonify(job)
    return jsonify({"status": "HATA", "log": "İşlem bulunamadı"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
