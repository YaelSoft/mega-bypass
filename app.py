import os
import uuid
import datetime
import math
import pymongo
from flask import Flask, render_template_string, request, jsonify, session, redirect
from pymongo import MongoClient

app = Flask(__name__)
app.secret_key = "V48_CONTROL_CENTER_SECRET"

# ==================== AYARLAR ====================
# Render Environment Variables kısmına MONGO_URI eklemeyi unutma!
MONGO_URI = os.environ.get("MONGO_URI")
ADMIN_PASSWORD = "Ata_Yasin33"

# ==================== DB BAĞLANTISI ====================
if not MONGO_URI:
    print("❌ HATA: MONGO_URI EKSİK! Render ayarlarına ekle.")

client = MongoClient(MONGO_URI)
db = client['mega_leech']
queue = db['queue']
accounts_col = db['accounts']
proxies_col = db['proxies']
licenses_col = db['licenses']

# ==================== YARDIMCI FONKSİYONLAR ====================
def format_size(s):
    if s == 0: return "0 B"
    n = ("B", "KB", "MB", "GB", "TB")
    i = int(math.floor(math.log(s, 1024)))
    p = math.pow(1024, i)
    return "%s %s" % (round(s / p, 2), n[i])

def format_date(d):
    if not d: return "Süresiz"
    return d.strftime("%d.%m.%Y")

# ==================== HTML TEMPLATE (GELİŞMİŞ JS İLE) ====================
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="tr" class="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>M-CLOUD V48</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <script>
        tailwind.config = {
            darkMode: 'class',
            theme: { extend: { colors: { 
                primary: '#6366f1', 
                dark: '#0f172a', 
                darker: '#020617',
                glass: 'rgba(15, 23, 42, 0.8)' 
            } } }
        }
    </script>
    <style>
        body { background-color: #020617; color: #e2e8f0; font-family: 'Segoe UI', sans-serif; }
        .glass-panel { background: rgba(30, 41, 59, 0.7); backdrop-filter: blur(10px); border: 1px solid rgba(255, 255, 255, 0.08); }
        .loader { border-top-color: #6366f1; -webkit-animation: spinner 1.5s linear infinite; animation: spinner 1.5s linear infinite; }
        @keyframes spinner { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        #logs { scroll-behavior: smooth; }
        ::-webkit-scrollbar { width: 8px; }
        ::-webkit-scrollbar-track { background: #0f172a; }
        ::-webkit-scrollbar-thumb { background: #334155; border-radius: 4px; }
    </style>
</head>
<body class="flex flex-col min-h-screen bg-[url('https://images.unsplash.com/photo-1550751827-4bd374c3f58b?q=80&w=2070')] bg-cover bg-fixed bg-center">
    <div class="absolute inset-0 bg-darker/90 z-0"></div>

    <nav class="relative z-10 border-b border-white/5 bg-dark/90 backdrop-blur-md sticky top-0">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="flex items-center justify-between h-16">
                <div class="flex items-center gap-3">
                    <div class="w-8 h-8 bg-primary rounded flex items-center justify-center shadow-lg shadow-primary/30">
                        <i class="fa-solid fa-cloud-bolt text-white"></i>
                    </div>
                    <span class="font-bold text-xl tracking-wider text-white">M-CLOUD <span class="text-primary text-sm font-normal">V48</span></span>
                </div>
                <div>
                    {% if session.user_key or session.admin %}
                        <a href="/logout" class="text-slate-400 hover:text-white transition text-sm flex items-center gap-2">
                            <i class="fa-solid fa-right-from-bracket"></i> ÇIKIŞ
                        </a>
                    {% endif %}
                </div>
            </div>
        </div>
    </nav>

    <main class="relative z-10 flex-grow container mx-auto px-4 py-8">
        
        {% if page == 'login' %}
        <div class="flex items-center justify-center h-[70vh]">
            <div class="glass-panel p-8 rounded-2xl shadow-2xl w-full max-w-md border-t-4 border-primary">
                <h2 class="text-center text-2xl font-bold text-white mb-2">Sistem Girişi</h2>
                <p class="text-center text-slate-400 text-sm mb-8">Devam etmek için kimliğinizi doğrulayın.</p>
                
                <form action="/auth" method="POST" class="space-y-5">
                    <div class="relative">
                        <i class="fa-solid fa-key absolute left-4 top-4 text-slate-500"></i>
                        <input type="password" name="auth_key" class="w-full pl-10 pr-4 py-3 bg-dark/50 border border-slate-700 rounded-xl text-white focus:border-primary focus:ring-1 focus:ring-primary outline-none transition" placeholder="Lisans Anahtarı veya Admin Şifresi" required>
                    </div>
                    <button class="w-full bg-primary hover:bg-indigo-600 text-white py-3 rounded-xl font-bold shadow-lg shadow-indigo-500/20 transition transform active:scale-95">
                        GİRİŞ YAP
                    </button>
                </form>

                {% if error %}
                <div class="mt-4 p-3 bg-red-500/10 border border-red-500/20 text-red-400 text-sm rounded-lg text-center animate-pulse">
                    <i class="fa-solid fa-circle-exclamation mr-1"></i> {{ error }}
                </div>
                {% endif %}
            </div>
        </div>
        {% endif %}

        {% if page == 'user' %}
        <div class="grid grid-cols-1 lg:grid-cols-12 gap-6">
            
            <div class="lg:col-span-4 space-y-6">
                <div class="glass-panel p-6 rounded-2xl">
                    <h3 class="text-slate-400 text-xs font-bold uppercase tracking-widest mb-4">LİSANS DURUMU</h3>
                    <div class="text-center mb-6">
                        <div class="inline-flex items-center justify-center w-32 h-32 rounded-full border-4 border-slate-700 relative">
                            <div class="text-center z-10">
                                <span class="block text-2xl font-bold text-white">{{ percent }}%</span>
                                <span class="text-xs text-slate-400">Dolu</span>
                            </div>
                            <svg class="absolute top-0 left-0 w-full h-full -rotate-90 transform" viewBox="0 0 100 100">
                                <circle cx="50" cy="50" r="46" fill="transparent" stroke="#6366f1" stroke-width="8" stroke-dasharray="289" stroke-dashoffset="{{ 289 - (289 * percent / 100) }}"></circle>
                            </svg>
                        </div>
                    </div>
                    <div class="space-y-3 text-sm">
                        <div class="flex justify-between p-3 bg-dark/40 rounded-lg"><span class="text-slate-400">Anahtar</span><span class="font-mono text-white">{{ key[:8] }}...</span></div>
                        <div class="flex justify-between p-3 bg-dark/40 rounded-lg"><span class="text-slate-400">Kalan</span><span class="font-bold text-white">{{ remaining_fmt }}</span></div>
                        <div class="flex justify-between p-3 bg-dark/40 rounded-lg"><span class="text-slate-400">Bitiş</span><span class="font-bold text-yellow-400">{{ expiry_str }}</span></div>
                    </div>
                </div>
                
                <div class="glass-panel p-6 rounded-2xl border-indigo-500/30">
                    <h3 class="font-bold text-white text-lg mb-2"><i class="fa-brands fa-telegram text-blue-400"></i> YaelSaver Bot</h3>
                    <p class="text-slate-400 text-xs mb-4">Telegram üzerinden sınırsız indirme yapmak için botumuzu kullanabilirsiniz.</p>
                    <a href="https://t.me/YaelSaverBot" target="_blank" class="block w-full bg-blue-600 hover:bg-blue-700 text-white text-center py-2 rounded-lg font-bold transition">BOTU BAŞLAT</a>
                </div>
            </div>

            <div class="lg:col-span-8">
                <div class="glass-panel p-8 rounded-2xl h-full flex flex-col">
                    <h2 class="text-2xl font-bold text-white mb-1">Dosya İndir</h2>
                    <p class="text-slate-400 text-sm mb-6">Mega.nz linkini yapıştırın ve arkanıza yaslanın.</p>

                    <div class="flex gap-3 mb-6">
                        <input type="text" id="megaLink" class="flex-grow bg-dark/50 border border-slate-600 text-white rounded-xl px-5 py-4 focus:ring-2 focus:ring-primary outline-none transition" placeholder="https://mega.nz/...">
                        <button onclick="startTask()" id="startBtn" class="bg-primary hover:bg-indigo-600 text-white px-8 rounded-xl font-bold transition flex items-center gap-2">
                            <i class="fa-solid fa-cloud-arrow-down"></i> İNDİR
                        </button>
                    </div>

                    <div id="console" class="hidden flex-grow bg-black/80 rounded-xl p-4 font-mono text-sm border border-slate-800 relative flex flex-col">
                        <div class="flex justify-between items-center mb-2 border-b border-white/10 pb-2">
                            <span class="text-xs text-slate-500">CANLI TERMİNAL</span>
                            <div class="flex gap-1"><div class="w-2 h-2 rounded-full bg-red-500"></div><div class="w-2 h-2 rounded-full bg-yellow-500"></div><div class="w-2 h-2 rounded-full bg-green-500"></div></div>
                        </div>
                        <div id="logs" class="flex-grow overflow-y-auto h-64 space-y-1 text-green-400 text-xs p-2"></div>
                        <div id="progressBarContainer" class="mt-2 w-full bg-slate-800 h-1 rounded-full overflow-hidden hidden">
                            <div id="progressBar" class="bg-green-500 h-1 w-0 transition-all duration-300"></div>
                        </div>
                    </div>

                    <div id="resultArea" class="hidden mt-6 text-center animate-fade-in">
                        <div class="w-16 h-16 bg-green-500/20 rounded-full flex items-center justify-center mx-auto mb-4 border border-green-500/50">
                            <i class="fa-solid fa-check text-2xl text-green-500"></i>
                        </div>
                        <h3 class="text-xl font-bold text-white mb-2">İşlem Tamamlandı!</h3>
                        <a id="dlButton" href="#" class="inline-flex items-center gap-2 bg-green-600 hover:bg-green-700 text-white px-8 py-3 rounded-xl font-bold shadow-lg transition">
                            <i class="fa-solid fa-download"></i> DOSYAYI KAYDET
                        </a>
                        <button onclick="location.reload()" class="block mx-auto mt-4 text-slate-500 text-xs hover:text-white">Yeni İşlem</button>
                    </div>
                </div>
            </div>
        </div>

        <script>
            let hwid = localStorage.getItem('hwid') || Math.random().toString(36).substring(7);
            localStorage.setItem('hwid', hwid);
            let taskId = null;
            let timer = null;
            let retryCount = 0;

            function addLog(msg, color="text-green-400") {
                const logs = document.getElementById('logs');
                const div = document.createElement('div');
                const time = new Date().toLocaleTimeString();
                div.className = `${color} border-l-2 border-white/10 pl-2`;
                div.innerHTML = `<span class="text-slate-600">[${time}]</span> ${msg}`;
                logs.appendChild(div);
                logs.scrollTop = logs.scrollHeight;
            }

            async function startTask() {
                const link = document.getElementById('megaLink').value;
                if(!link) return alert("Lütfen bir link girin!");

                document.getElementById('startBtn').disabled = true;
                document.getElementById('startBtn').innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> BAĞLANIYOR';
                document.getElementById('console').classList.remove('hidden');
                document.getElementById('resultArea').classList.add('hidden');
                document.getElementById('logs').innerHTML = ''; // Temizle
                
                addLog("Sunucuya bağlanılıyor...", "text-blue-400");

                try {
                    const req = await fetch('/api/task', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({link: link, token: '{{ key }}', hwid: hwid})
                    });
                    const res = await req.json();

                    if(res.success) {
                        taskId = res.taskId;
                        addLog("Görev Worker'a iletildi.", "text-yellow-400");
                        addLog("Proxy ve Hesap atanıyor...", "text-slate-400");
                        document.getElementById('progressBarContainer').classList.remove('hidden');
                        retryCount = 0;
                        startPolling();
                    } else {
                        addLog("BAŞLATMA HATASI: " + res.msg, "text-red-500 font-bold");
                        resetBtn();
                    }
                } catch(e) {
                    addLog("SUNUCUYA ULAŞILAMIYOR!", "text-red-500 font-bold");
                    resetBtn();
                }
            }

            function startPolling() {
                if(timer) clearInterval(timer);
                let p = 5;
                
                timer = setInterval(async () => {
                    if(!taskId) return;
                    try {
                        const req = await fetch('/api/status/' + taskId);
                        const res = await req.json();
                        
                        // İlerleme Çubuğu Animasyonu
                        if(p < 90) p += Math.random() * 2;
                        document.getElementById('progressBar').style.width = p + '%';

                        if(res.log) {
                            // Son logu al, eğer ekranda yoksa ekle (Tekrarı önle)
                            const logsDiv = document.getElementById('logs');
                            if(!logsDiv.lastElementChild || !logsDiv.lastElementChild.innerText.includes(res.log)) {
                                addLog(res.log, res.status.includes('HATA') ? 'text-red-400' : 'text-green-400');
                            }
                        }

                        if(res.status === 'TAMAMLANDI') {
                            clearInterval(timer);
                            document.getElementById('progressBar').style.width = '100%';
                            addLog("✅ DOSYA HAZIRLANDI!", "text-green-500 font-bold bg-green-500/10 p-1 rounded");
                            setTimeout(() => {
                                document.getElementById('console').classList.add('hidden');
                                document.getElementById('resultArea').classList.remove('hidden');
                                document.getElementById('dlButton').href = res.result.url;
                            }, 1000);
                        } else if(res.status.includes('HATA')) {
                            clearInterval(timer);
                            addLog("❌ İŞLEM BAŞARISIZ.", "text-red-500 font-bold bg-red-500/10 p-1 rounded");
                            resetBtn();
                        }
                    } catch(e) {
                        retryCount++;
                        if(retryCount > 10) {
                            addLog("⚠️ Bağlantı koptu (Worker cevap vermiyor).", "text-orange-500");
                            clearInterval(timer);
                            resetBtn();
                        }
                    }
                }, 2000); // 2 saniyede bir kontrol et
            }

            function resetBtn() {
                document.getElementById('startBtn').disabled = false;
                document.getElementById('startBtn').innerHTML = '<i class="fa-solid fa-rotate-right"></i> TEKRAR DENE';
            }
        </script>
        {% endif %}

        {% if page == 'admin' %}
        <div class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
            <div class="glass-panel p-4 rounded-xl border-t-4 border-blue-500 text-center">
                <div class="text-xs text-slate-400">TOPLAM LİSANS</div>
                <div class="text-3xl font-bold text-white">{{ stats.total_lic }}</div>
            </div>
            <div class="glass-panel p-4 rounded-xl border-t-4 border-green-500 text-center">
                <div class="text-xs text-slate-400">SAĞLAM HESAP</div>
                <div class="text-3xl font-bold text-white">{{ stats.active_acc }}</div>
            </div>
            <div class="glass-panel p-4 rounded-xl border-t-4 border-purple-500 text-center">
                <div class="text-xs text-slate-400">PROXY SAYISI</div>
                <div class="text-3xl font-bold text-white">{{ stats.proxies }}</div>
            </div>
            <div class="glass-panel p-4 rounded-xl border-t-4 border-red-500 text-center">
                <div class="text-xs text-slate-400">BEKLEYEN İŞ</div>
                <div class="text-3xl font-bold text-white">{{ stats.queue }}</div>
            </div>
        </div>
        
        <div class="mb-8 flex justify-end">
            <a href="/admin/clear_queue" class="bg-red-600 hover:bg-red-700 text-white px-6 py-3 rounded-xl font-bold shadow-lg shadow-red-600/20 flex items-center gap-2 text-sm transition">
                <i class="fa-solid fa-trash-can"></i> TAKILAN İŞLERİ TEMİZLE (RESET)
            </a>
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
            <div class="space-y-6">
                <div class="glass-panel p-6 rounded-xl">
                    <h3 class="font-bold mb-4 text-green-400"><i class="fa-solid fa-users"></i> Mega Hesapları</h3>
                    <form action="/admin/add_account" method="POST">
                        <textarea name="accounts" class="w-full bg-dark/50 border border-slate-700 rounded p-3 text-xs h-32 text-white outline-none focus:border-green-500" placeholder="email:sifre"></textarea>
                        <button class="w-full bg-green-600 hover:bg-green-700 text-white py-2 rounded font-bold mt-2">HESAPLARI YÜKLE</button>
                    </form>
                </div>

                <div class="glass-panel p-6 rounded-xl">
                    <h3 class="font-bold mb-4 text-purple-400"><i class="fa-solid fa-globe"></i> Proxyler</h3>
                    <form action="/admin/add_proxy" method="POST">
                        <textarea name="proxies" class="w-full bg-dark/50 border border-slate-700 rounded p-3 text-xs h-32 text-white outline-none focus:border-purple-500" placeholder="http://user:pass@ip:port"></textarea>
                        <button class="w-full bg-purple-600 hover:bg-purple-700 text-white py-2 rounded font-bold mt-2">PROXYLERİ YÜKLE</button>
                    </form>
                </div>
            </div>

            <div class="glass-panel p-6 rounded-xl">
                <h3 class="font-bold mb-4 text-white"><i class="fa-solid fa-key"></i> Lisans Oluştur</h3>
                
                <form action="/admin/generate" method="POST" class="bg-dark/40 p-4 rounded-lg mb-6 grid grid-cols-3 gap-4">
                    <div><label class="text-xs text-slate-400">Adet</label><select name="count" class="w-full bg-dark border border-slate-600 rounded p-2 text-white"><option value="1">1</option><option value="5">5</option></select></div>
                    <div><label class="text-xs text-slate-400">GB</label><input type="number" name="gb_limit" value="50" class="w-full bg-dark border border-slate-600 rounded p-2 text-white"></div>
                    <div><label class="text-xs text-slate-400">Gün</label><input type="number" name="days" value="30" class="w-full bg-dark border border-slate-600 rounded p-2 text-white"></div>
                    <button class="col-span-3 bg-primary hover:bg-indigo-600 text-white py-2 rounded font-bold">OLUŞTUR</button>
                </form>

                {% if new_keys %}
                <div class="bg-black/50 p-3 rounded mb-4 border border-green-500/30">
                    <p class="text-green-400 text-xs mb-1">KOPYALA:</p>
                    <textarea class="w-full bg-transparent text-green-300 text-xs font-mono h-20 outline-none" readonly>{% for k in new_keys %}{{ k }}&#13;&#10;{% endfor %}</textarea>
                </div>
                {% endif %}

                <div class="overflow-x-auto">
                    <table class="w-full text-left text-xs text-slate-400">
                        <thead class="bg-dark/50 text-slate-200"><tr><th class="p-2">KEY</th><th class="p-2">GB</th><th class="p-2">GÜN</th><th class="p-2">DURUM</th></tr></thead>
                        <tbody class="divide-y divide-slate-700">
                            {% for l in licenses %}
                            <tr>
                                <td class="p-2 font-mono text-white">{{ l.key }}</td>
                                <td class="p-2">{{ l.usage_fmt }}/{{ l.limit_fmt }}</td>
                                <td class="p-2">{{ l.expiry_fmt }}</td>
                                <td class="p-2">
                                    {% if not l.isActive %}<span class="text-red-500">BAN</span>
                                    {% else %}<a href="/admin/delete/{{ l.key }}" class="text-slate-500 hover:text-red-500">SİL</a>{% endif %}
                                </td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
        {% endif %}

    </main>
</body>
</html>
"""

# ==================== BACKEND ====================

@app.route('/', methods=['GET'])
def index():
    if session.get('admin'): return render_dashboard_admin()
    if session.get('user_key'): return render_dashboard_user(session['user_key'])
    return render_template_string(HTML_TEMPLATE, page='login')

@app.route('/auth', methods=['POST'])
def auth():
    key = request.form.get('auth_key', '').strip()
    if key == ADMIN_PASSWORD:
        session['admin'] = True
        return redirect('/')
    l = licenses_col.find_one({"key": key})
    if l and l.get('isActive', True):
        session['user_key'] = key
        return redirect('/')
    return render_template_string(HTML_TEMPLATE, page='login', error="Geçersiz Giriş!")

def render_dashboard_user(key):
    lic = licenses_col.find_one({"key": key})
    if not lic: session.clear(); return redirect('/')
    used = lic.get('total_usage', 0)
    limit = lic.get('quota_limit', 0)
    percent = min(100, int((used / limit) * 100)) if limit > 0 else 0
    remaining = limit - used if limit > 0 else 0
    return render_template_string(HTML_TEMPLATE, page='user', key=key, percent=percent, remaining_fmt=format_size(remaining), expiry_str=format_date(lic.get('expiry_date')), session=session)

def render_dashboard_admin():
    lics = list(licenses_col.find().sort("_id", -1))
    for l in lics:
        l['usage_fmt'] = format_size(l.get('total_usage', 0))
        l['limit_fmt'] = format_size(l.get('quota_limit', 0))
        l['expiry_fmt'] = format_date(l.get('expiry_date'))
    stats = {
        "total_lic": len(lics),
        "active_acc": accounts_col.count_documents({"status": "ACTIVE"}),
        "proxies": proxies_col.count_documents({}),
        "queue": queue.count_documents({"status": "SIRADA"}),
    }
    return render_template_string(HTML_TEMPLATE, page='admin', licenses=lics, stats=stats, session=session, new_keys=session.pop('new_keys', None))

# ADMIN ACTIONS
@app.route('/admin/generate', methods=['POST'])
def generate():
    if not session.get('admin'): return redirect('/')
    try:
        count = int(request.form.get('count', 1))
        gb = int(request.form.get('gb_limit', 50))
        days = int(request.form.get('days', 30))
        keys = []
        for _ in range(count):
            k = f"VIP-{uuid.uuid4().hex[:8].upper()}"
            licenses_col.insert_one({"key": k, "isActive": True, "hwid": None, "total_usage": 0, "quota_limit": gb*(1024**3), "expiry_date": datetime.datetime.now()+datetime.timedelta(days=days)})
            keys.append(k)
        session['new_keys'] = keys
    except: pass
    return redirect('/')

@app.route('/admin/add_account', methods=['POST'])
def add_acc():
    if not session.get('admin'): return redirect('/')
    for line in request.form.get('accounts', '').split('\n'):
        if ':' in line:
            email, pwd = line.strip().split(':', 1)
            if not accounts_col.find_one({"email": email}):
                accounts_col.insert_one({"email": email, "password": pwd, "status": "ACTIVE"})
    return redirect('/')

@app.route('/admin/add_proxy', methods=['POST'])
def add_px():
    if not session.get('admin'): return redirect('/')
    proxies_col.delete_many({}) # ESKİLERİ SİL
    for line in request.form.get('proxies', '').split('\n'):
        if line.strip(): proxies_col.insert_one({"ip": line.strip()})
    return redirect('/')

@app.route('/admin/clear_queue')
def clear_queue():
    if not session.get('admin'): return redirect('/')
    queue.delete_many({}) # TÜM İŞLERİ SİL
    return redirect('/')

@app.route('/admin/delete/<k>')
def delete(k):
    if not session.get('admin'): return redirect('/')
    licenses_col.delete_one({"key": k})
    return redirect('/')

@app.route('/logout')
def logout(): session.clear(); return redirect('/')

# API FOR WORKER
@app.route('/api/task', methods=['POST'])
def api_task():
    d = request.json
    l = licenses_col.find_one({"key": d['token']})
    if not l or not l['isActive']: return jsonify({"success": False, "msg": "Yetkisiz!"})
    tid = str(uuid.uuid4())
    queue.insert_one({"task_id": tid, "link": d['link'], "owner": d['token'], "status": "SIRADA", "log": "Sıraya alındı..."})
    return jsonify({"success": True, "taskId": tid})

@app.route('/api/status/<tid>')
def status(tid): return jsonify(queue.find_one({"task_id": tid}, {"_id": 0}))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
