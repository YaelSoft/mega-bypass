import os
import uuid
import datetime
import math
from flask import Flask, render_template_string, request, jsonify, session, redirect
from pymongo import MongoClient

app = Flask(__name__)
app.secret_key = "ULTIMATE_PANEL_KEY_V34"

# AYARLAR
MONGO_URI = os.environ.get("MONGO_URI")
ADMIN_PASSWORD = "Ata_Yasin5363"

# DB BAĞLANTISI
client = MongoClient(MONGO_URI)
db = client['mega_leech']
queue = db['queue']
accounts_col = db['accounts']
proxies_col = db['proxies']
licenses_col = db['licenses']

# --- YARDIMCI FONKSİYONLAR ---
def format_size(s):
    if s == 0: return "0 B"
    n = ("B", "KB", "MB", "GB", "TB")
    i = int(math.floor(math.log(s, 1024)))
    p = math.pow(1024, i)
    return "%s %s" % (round(s / p, 2), n[i])

# --- HTML ŞABLONU ---
HTML_BASE = """
<!DOCTYPE html><html lang="tr"><head><meta charset="UTF-8"><title>M-CLOUD PRO</title>
<script src="https://cdn.tailwindcss.com"></script>
<link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
<style>
    body { background-color: #0f172a; color: #e2e8f0; font-family: 'Inter', sans-serif; }
    .glass { background: rgba(30, 41, 59, 0.7); backdrop-filter: blur(10px); border: 1px solid rgba(255, 255, 255, 0.1); }
    .gradient-text { background: linear-gradient(45deg, #3b82f6, #8b5cf6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
</style>
</head>
<body class="min-h-screen flex flex-col">
    <nav class="border-b border-slate-700 bg-slate-900/80 backdrop-blur sticky top-0 z-50">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="flex items-center justify-between h-16">
                <div class="flex items-center gap-2">
                    <i class="fa-solid fa-cloud-bolt text-blue-500 text-2xl"></i>
                    <span class="font-bold text-xl tracking-wider">M-CLOUD</span>
                </div>
                <div class="flex items-center gap-4">
                    {% if session.user_key %}
                        <span class="text-xs bg-blue-900 text-blue-200 px-3 py-1 rounded-full border border-blue-700">Lisans: {{ session.user_key[:8] }}...</span>
                        <a href="/logout" class="text-sm text-slate-400 hover:text-white"><i class="fa-solid fa-power-off"></i> Çıkış</a>
                    {% elif session.admin %}
                        <span class="text-xs bg-red-900 text-red-200 px-3 py-1 rounded-full">YÖNETİCİ</span>
                        <a href="/logout" class="text-sm text-slate-400 hover:text-white">Çıkış</a>
                    {% else %}
                        <a href="/admin" class="text-xs text-slate-500 hover:text-slate-300">Yönetici Girişi</a>
                    {% endif %}
                </div>
            </div>
        </div>
    </nav>
    <main class="flex-grow container mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {{ content | safe }}
    </main>
    <footer class="border-t border-slate-800 bg-slate-900 py-6 mt-auto">
        <div class="text-center text-slate-500 text-sm">
            &copy; 2026 M-CLOUD Systems. Powered by <a href="#" class="text-blue-500 hover:underline">YaelSaver Technology</a>.
        </div>
    </footer>
</body></html>
"""

# --- SAYFALAR ---

@app.route('/', methods=['GET', 'POST'])
def index():
    # 1. GİRİŞ YAPILMAMIŞSA -> LOGIN EKRANI
    if not session.get('user_key') and not session.get('admin'):
        return render_template_string(HTML_BASE, content="""
        <div class="flex items-center justify-center h-[70vh]">
            <div class="glass p-10 rounded-2xl shadow-2xl w-full max-w-md relative overflow-hidden">
                <div class="absolute top-0 left-0 w-full h-2 bg-gradient-to-r from-blue-500 to-purple-600"></div>
                <h2 class="text-center text-3xl font-bold mb-2">Hoş Geldiniz</h2>
                <p class="text-center text-slate-400 mb-8 text-sm">Devam etmek için lisans anahtarınızı girin.</p>
                
                <form action="/login_user" method="POST" class="space-y-6">
                    <div>
                        <label class="block text-sm font-medium text-slate-300 mb-2">Lisans Anahtarı</label>
                        <input type="text" name="key" class="w-full p-4 bg-slate-800 border border-slate-600 rounded-xl text-white placeholder-slate-500 focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition" placeholder="VIP-XXXXXXXX" required>
                    </div>
                    <button class="w-full bg-blue-600 hover:bg-blue-700 text-white py-4 rounded-xl font-bold text-lg shadow-lg shadow-blue-500/30 transition transform hover:scale-[1.02]">Sisteme Giriş Yap</button>
                </form>
                
                <div class="mt-8 pt-6 border-t border-slate-700 text-center">
                    <p class="text-xs text-slate-500 mb-2">Lisansınız yok mu?</p>
                    <a href="https://t.me/YaelSoft" target="_blank" class="text-blue-400 hover:text-blue-300 text-sm font-semibold flex items-center justify-center gap-2">
                        <i class="fa-brands fa-telegram"></i> Satın Almak İçin Tıklayın
                    </a>
                </div>
            </div>
        </div>
        """)

    # 2. MÜŞTERİ PANELİ
    if session.get('user_key'):
        key = session['user_key']
        lic = licenses_col.find_one({"key": key})
        
        # Lisans Kontrolü (Silinmişse at)
        if not lic or not lic.get('isActive'): session.clear(); return redirect('/')

        # Hesaplamalar
        used = lic.get('total_usage', 0)
        limit = lic.get('quota_limit', 0)
        percent = min(100, int((used / limit) * 100)) if limit > 0 else 0
        
        expiry = lic.get('expiry_date')
        days_left = (expiry - datetime.datetime.now()).days if expiry else "Süresiz"
        if isinstance(days_left, int) and days_left < 0: days_left = 0

        # Müşteri Paneli HTML
        dashboard_html = f"""
        <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
            <div class="space-y-6">
                <div class="glass p-6 rounded-2xl">
                    <h3 class="text-slate-400 text-xs font-bold uppercase tracking-wider mb-4">LİSANS DURUMU</h3>
                    
                    <div class="mb-6">
                        <div class="flex justify-between text-sm mb-2">
                            <span class="text-slate-300">Kota Kullanımı</span>
                            <span class="text-white font-bold">{format_size(used)} / {format_size(limit)}</span>
                        </div>
                        <div class="w-full bg-slate-700 rounded-full h-3 overflow-hidden">
                            <div class="bg-gradient-to-r from-blue-500 to-cyan-400 h-3 rounded-full" style="width: {percent}%"></div>
                        </div>
                    </div>
                    
                    <div class="flex items-center justify-between p-4 bg-slate-800/50 rounded-xl border border-slate-700">
                        <div class="flex items-center gap-3">
                            <div class="w-10 h-10 rounded-full bg-purple-500/20 flex items-center justify-center text-purple-400"><i class="fa-regular fa-clock"></i></div>
                            <div>
                                <div class="text-xs text-slate-400">Kalan Süre</div>
                                <div class="font-bold text-white">{days_left} Gün</div>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="bg-gradient-to-br from-indigo-900 to-blue-900 p-6 rounded-2xl border border-blue-700/50 shadow-xl relative overflow-hidden group">
                    <div class="absolute -right-10 -top-10 w-32 h-32 bg-blue-500/20 rounded-full blur-2xl group-hover:bg-blue-500/30 transition"></div>
                    <h3 class="font-bold text-white text-lg mb-2 flex items-center gap-2"><i class="fa-solid fa-rocket"></i> YaelSaver PRO</h3>
                    <p class="text-blue-200 text-sm mb-4">Telegram'dan daha hızlı ve sınırsız içerik indirmek ister misiniz?</p>
                    <a href="https://t.me/YaelSaverBot" target="_blank" class="block w-full bg-white text-blue-900 text-center py-3 rounded-lg font-bold hover:bg-blue-50 transition shadow-lg">
                        BOTU BAŞLAT
                    </a>
                </div>
            </div>

            <div class="lg:col-span-2">
                <div class="glass p-8 rounded-2xl shadow-lg">
                    <h2 class="text-2xl font-bold text-white mb-6">Dosya İndir</h2>
                    
                    <div class="mb-6">
                        <label class="block text-sm font-medium text-slate-400 mb-2">Mega.nz Linki</label>
                        <div class="flex gap-2">
                            <input type="text" id="megaLink" class="flex-grow p-4 bg-slate-800 border border-slate-600 rounded-xl text-white placeholder-slate-600 focus:ring-2 focus:ring-green-500 outline-none" placeholder="https://mega.nz/file/...">
                            <button onclick="startDownload()" id="startBtn" class="bg-green-600 hover:bg-green-700 text-white px-8 rounded-xl font-bold transition flex items-center gap-2">
                                <i class="fa-solid fa-download"></i> İNDİR
                            </button>
                        </div>
                    </div>

                    <div id="statusArea" class="hidden p-6 bg-slate-800/80 rounded-xl border border-slate-700">
                        <div class="flex justify-between items-center mb-3">
                            <div class="flex items-center gap-3">
                                <div class="spinner-border animate-spin w-5 h-5 border-2 border-blue-500 border-t-transparent rounded-full"></div>
                                <span id="statusText" class="text-blue-400 font-mono text-sm">İşleniyor...</span>
                            </div>
                        </div>
                        <div class="w-full bg-slate-700 h-2 rounded-full overflow-hidden">
                            <div id="progressBar" class="bg-blue-500 h-2 rounded-full w-1/2 animate-pulse"></div>
                        </div>
                    </div>

                    <div id="resultArea" class="hidden mt-6 p-6 bg-green-900/20 border border-green-500/30 rounded-xl text-center">
                        <div class="w-16 h-16 bg-green-500/20 rounded-full flex items-center justify-center mx-auto mb-4">
                            <i class="fa-solid fa-check text-2xl text-green-500"></i>
                        </div>
                        <h3 class="text-lg font-bold text-white mb-1">Dosya Hazır!</h3>
                        <p id="fileName" class="text-sm text-green-300 font-mono mb-4">...</p>
                        <a id="dlButton" href="#" class="inline-block bg-green-600 hover:bg-green-700 text-white px-8 py-3 rounded-lg font-bold shadow-lg transition">
                            DOSYAYI KAYDET
                        </a>
                    </div>

                </div>
            </div>
        </div>

        <script>
            let currentTaskId = null;
            let pollInterval = null;
            let hwid = localStorage.getItem('hwid') || Math.random().toString(36).substring(7);
            localStorage.setItem('hwid', hwid);

            async function startDownload() {
                let link = document.getElementById('megaLink').value;
                if(!link) return;
                
                document.getElementById('startBtn').disabled = true;
                document.getElementById('statusArea').classList.remove('hidden');
                document.getElementById('resultArea').classList.add('hidden');
                document.getElementById('statusText').innerText = "Kuyruğa ekleniyor...";

                try {
                    let res = await fetch('/api/task', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({link: link, token: '{key}', hwid: hwid})
                    });
                    let data = await res.json();
                    
                    if(data.success) {
                        currentTaskId = data.taskId;
                        startPolling();
                    } else {
                        alert(data.msg);
                        resetUI();
                    }
                } catch(e) {
                    alert("Bağlantı Hatası");
                    resetUI();
                }
            }

            function startPolling() {
                pollInterval = setInterval(async () => {
                    if(!currentTaskId) return;
                    try {
                        let res = await fetch('/api/status/' + currentTaskId);
                        let data = await res.json();
                        
                        if(data.status === 'ISLENIYOR') {
                            document.getElementById('statusText').innerText = data.log;
                        } else if(data.status === 'TAMAMLANDI') {
                            clearInterval(pollInterval);
                            document.getElementById('statusArea').classList.add('hidden');
                            document.getElementById('resultArea').classList.remove('hidden');
                            document.getElementById('fileName').innerText = data.result.name;
                            document.getElementById('dlButton').href = data.result.url;
                            document.getElementById('startBtn').disabled = false;
                        } else if(data.status.includes('HATA')) {
                            clearInterval(pollInterval);
                            alert("HATA: " + data.log);
                            resetUI();
                        }
                    } catch(e) {}
                }, 2000);
            }

            function resetUI() {
                document.getElementById('statusArea').classList.add('hidden');
                document.getElementById('startBtn').disabled = false;
                if(pollInterval) clearInterval(pollInterval);
            }
        </script>
        """
        return render_template_string(HTML_BASE, content=dashboard_html, session=session)

    # 3. ADMIN PANELİ (Redirect)
    if session.get('admin'):
        return redirect('/admin')
    
    return redirect('/')

# --- KULLANICI GİRİŞ ---
@app.route('/login_user', methods=['POST'])
def login_user():
    key = request.form.get('key')
    l = licenses_col.find_one({"key": key})
    
    if not l: return "<h1>Geçersiz Lisans! <a href='/'>Geri</a></h1>"
    if not l.get('isActive'): return "<h1>Lisans Banlı! <a href='/'>Geri</a></h1>"
    
    # Süre ve Kota Kontrolü
    if l.get('expiry_date') and datetime.datetime.now() > l['expiry_date']: return "<h1>Süre Dolmuş! <a href='/'>Geri</a></h1>"
    if l.get('quota_limit', 0) > 0 and l.get('total_usage', 0) >= l['quota_limit']: return "<h1>Kota Dolmuş! <a href='/'>Geri</a></h1>"

    session['user_key'] = key
    return redirect('/')

# --- ADMIN PANELİ (V33 ile aynı, sadece tema uyumlu) ---
@app.route('/admin')
def admin_panel():
    if not session.get('admin'):
        # Admin Login Formu
        return render_template_string(HTML_BASE, content="""
        <div class="flex justify-center mt-20">
            <div class="glass p-8 rounded-xl w-96">
                <h2 class="text-center font-bold mb-4 text-red-500">YÖNETİCİ</h2>
                <form action="/admin_login" method="POST">
                    <input type="password" name="password" class="w-full p-3 bg-slate-800 rounded mb-4 text-white" placeholder="Şifre">
                    <button class="w-full bg-red-600 py-2 rounded font-bold">Giriş</button>
                </form>
            </div>
        </div>
        """)
    
    # Admin Dashboard (İçerik V33'teki tablonun aynısı, sadece class'ları güncelledim)
    # ... (Buraya V33'teki admin panel kodlarını entegre edebilirsin, yer kaplamasın diye kısalttım)
    # ... V33'teki 'admin' fonksiyonunun içindeki render_template_string'i HTML_BASE ile kullanman yeterli.
    return "<h1>Admin Paneli V33 Kodlarını Buraya Yapıştır (Sadece HTML_BASE içine)</h1> <a href='/logout'>Çıkış</a>"

@app.route('/admin_login', methods=['POST'])
def admin_login():
    if request.form.get('password') == ADMIN_PASSWORD:
        session['admin'] = True
        return redirect('/admin')
    return "Hatalı Şifre"

# --- API ENDPOINTS (WORKER İÇİN) ---
@app.route('/api/task', methods=['POST'])
def api_task():
    d = request.json
    l = licenses_col.find_one({"key": d['token']})
    
    # GÜVENLİK KONTROLLERİ
    if not l or not l['isActive']: return jsonify({"success": False, "msg": "Geçersiz Lisans"})
    if l.get('expiry_date') and datetime.datetime.now() > l['expiry_date']: return jsonify({"success": False, "msg": "Süre Doldu"})
    if l.get('quota_limit', 0) > 0 and l.get('total_usage', 0) >= l['quota_limit']: return jsonify({"success": False, "msg": "Kota Doldu"})
    
    # HWID KİLİDİ
    if l.get('hwid') and l['hwid'] != d['hwid']: return jsonify({"success": False, "msg": "Farklı Cihaz Tespit Edildi!"})
    if not l.get('hwid'): licenses_col.update_one({"key": d['token']}, {"$set": {"hwid": d['hwid']}})

    tid = str(uuid.uuid4())
    queue.insert_one({"task_id": tid, "link": d['link'], "owner": d['token'], "status": "SIRADA", "log": "Sıraya alındı..."})
    return jsonify({"success": True, "taskId": tid})

@app.route('/api/status/<tid>')
def status(tid): return jsonify(queue.find_one({"task_id": tid}, {"_id": 0}))

@app.route('/logout')
def logout(): session.clear(); return redirect('/')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
