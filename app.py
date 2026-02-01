import os
import uuid
import datetime
import math
from flask import Flask, render_template_string, request, jsonify, session, redirect
from pymongo import MongoClient

app = Flask(__name__)
app.secret_key = "V35_PRESTIGE_SECRET_KEY"

# ==================== AYARLAR ====================
# Render Environment Variables kısmına MONGO_URI eklemeyi unutma!
MONGO_URI = os.environ.get("MONGO_URI")
ADMIN_PASSWORD = "YASIN_BABA_123"

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

# ==================== TEK HTML (CSS + JS + HTML) ====================
# Bu HTML hem Admin hem User hem Login ekranını içerir.
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="tr" class="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>M-CLOUD ENTERPRISE</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <script>
        tailwind.config = {
            darkMode: 'class',
            theme: { extend: { colors: { 
                primary: '#3b82f6', 
                dark: '#0f172a', 
                darker: '#020617',
                glass: 'rgba(30, 41, 59, 0.7)' 
            } } }
        }
    </script>
    <style>
        body { background-color: #020617; color: #e2e8f0; font-family: 'Segoe UI', sans-serif; }
        .glass-panel { background: rgba(30, 41, 59, 0.6); backdrop-filter: blur(12px); border: 1px solid rgba(255, 255, 255, 0.05); }
        .neon-text { text-shadow: 0 0 10px rgba(59, 130, 246, 0.5); }
        .loader { border-top-color: #3b82f6; -webkit-animation: spinner 1.5s linear infinite; animation: spinner 1.5s linear infinite; }
        @keyframes spinner { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        /* Scrollbar */
        ::-webkit-scrollbar { width: 8px; }
        ::-webkit-scrollbar-track { background: #0f172a; }
        ::-webkit-scrollbar-thumb { background: #334155; border-radius: 4px; }
        ::-webkit-scrollbar-thumb:hover { background: #475569; }
    </style>
</head>
<body class="flex flex-col min-h-screen bg-[url('https://wallpaperaccess.com/full/2156326.jpg')] bg-cover bg-fixed bg-center">
    <div class="absolute inset-0 bg-darker/90 z-0"></div> <nav class="relative z-10 border-b border-white/10 bg-dark/80 backdrop-blur-md sticky top-0">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="flex items-center justify-between h-16">
                <div class="flex items-center gap-3">
                    <div class="w-8 h-8 bg-primary rounded flex items-center justify-center shadow-lg shadow-primary/30">
                        <i class="fa-solid fa-cloud text-white"></i>
                    </div>
                    <span class="font-bold text-xl tracking-wider text-white">M-CLOUD <span class="text-primary text-sm font-normal">PRO</span></span>
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
                <h2 class="text-center text-2xl font-bold text-white mb-2">Sisteme Giriş</h2>
                <p class="text-center text-slate-400 text-sm mb-8">Lisans anahtarınızı veya yönetici şifrenizi girin.</p>
                
                <form action="/auth" method="POST" class="space-y-5">
                    <div class="relative">
                        <i class="fa-solid fa-key absolute left-4 top-4 text-slate-500"></i>
                        <input type="password" name="auth_key" class="w-full pl-10 pr-4 py-3 bg-dark/50 border border-slate-700 rounded-xl text-white focus:border-primary focus:ring-1 focus:ring-primary outline-none transition" placeholder="Anahtar / Şifre" required>
                    </div>
                    <button class="w-full bg-primary hover:bg-blue-600 text-white py-3 rounded-xl font-bold shadow-lg shadow-blue-500/20 transition transform active:scale-95">
                        GİRİŞ YAP
                    </button>
                </form>

                {% if error %}
                <div class="mt-4 p-3 bg-red-500/10 border border-red-500/20 text-red-400 text-sm rounded-lg text-center">
                    <i class="fa-solid fa-circle-exclamation mr-1"></i> {{ error }}
                </div>
                {% endif %}
            </div>
        </div>
        {% endif %}

        {% if page == 'user' %}
        <div class="grid grid-cols-1 lg:grid-cols-12 gap-6">
            
            <div class="lg:col-span-4 space-y-6">
                <div class="glass-panel p-6 rounded-2xl relative overflow-hidden group">
                    <div class="absolute -right-6 -top-6 w-24 h-24 bg-primary/20 rounded-full blur-xl group-hover:bg-primary/30 transition"></div>
                    
                    <h3 class="text-slate-400 text-xs font-bold uppercase tracking-widest mb-4">LİSANS DETAYLARI</h3>
                    <div class="text-center mb-6">
                        <div class="inline-flex items-center justify-center w-32 h-32 rounded-full border-4 border-slate-700 relative">
                            <div class="text-center z-10">
                                <span class="block text-2xl font-bold text-white">{{ percent }}%</span>
                                <span class="text-xs text-slate-400">Kullanılan</span>
                            </div>
                            <svg class="absolute top-0 left-0 w-full h-full -rotate-90 transform" viewBox="0 0 100 100">
                                <circle cx="50" cy="50" r="46" fill="transparent" stroke="#3b82f6" stroke-width="8" stroke-dasharray="289" stroke-dashoffset="{{ 289 - (289 * percent / 100) }}"></circle>
                            </svg>
                        </div>
                    </div>

                    <div class="space-y-3 text-sm">
                        <div class="flex justify-between p-3 bg-dark/40 rounded-lg">
                            <span class="text-slate-400">Anahtar</span>
                            <span class="font-mono text-white">{{ key[:8] }}...</span>
                        </div>
                        <div class="flex justify-between p-3 bg-dark/40 rounded-lg">
                            <span class="text-slate-400">Kalan Kota</span>
                            <span class="font-bold text-white">{{ remaining_fmt }}</span>
                        </div>
                        <div class="flex justify-between p-3 bg-dark/40 rounded-lg">
                            <span class="text-slate-400">Bitiş Tarihi</span>
                            <span class="font-bold text-yellow-400">{{ expiry_str }}</span>
                        </div>
                    </div>
                </div>

                <div class="bg-gradient-to-br from-indigo-900 via-purple-900 to-slate-900 p-6 rounded-2xl border border-purple-500/30 shadow-xl text-center">
                    <div class="w-12 h-12 bg-white/10 rounded-full flex items-center justify-center mx-auto mb-3">
                        <i class="fa-solid fa-bolt text-yellow-400 text-xl"></i>
                    </div>
                    <h3 class="font-bold text-white text-lg">YaelSaver Premium</h3>
                    <p class="text-indigo-200 text-xs mt-2 mb-4">Telegram içeriklerini ışık hızında indirmek için botumuzu deneyin.</p>
                    <a href="https://t.me/YaelSaverBot" target="_blank" class="block w-full bg-white text-purple-900 font-bold py-2 rounded-lg hover:bg-gray-100 transition">BOTU AÇ</a>
                </div>
            </div>

            <div class="lg:col-span-8">
                <div class="glass-panel p-8 rounded-2xl h-full flex flex-col">
                    <h2 class="text-2xl font-bold text-white mb-1"><i class="fa-solid fa-download text-primary mr-2"></i>Mega İndirici</h2>
                    <p class="text-slate-400 text-sm mb-8">Klasör veya dosya linkini yapıştırın, arkanıza yaslanın.</p>

                    <div class="flex gap-3 mb-8">
                        <input type="text" id="megaLink" class="flex-grow bg-dark/50 border border-slate-600 text-white rounded-xl px-5 py-4 focus:ring-2 focus:ring-primary outline-none transition" placeholder="https://mega.nz/...">
                        <button onclick="startTask()" id="startBtn" class="bg-primary hover:bg-blue-600 text-white px-8 rounded-xl font-bold shadow-lg shadow-blue-500/20 transition flex items-center gap-2">
                            <i class="fa-solid fa-play"></i> BAŞLAT
                        </button>
                    </div>

                    <div id="console" class="hidden flex-grow bg-black/80 rounded-xl p-6 font-mono text-sm border border-slate-800 overflow-hidden relative">
                        <div class="absolute top-2 right-4 flex gap-2">
                            <div class="w-3 h-3 rounded-full bg-red-500"></div>
                            <div class="w-3 h-3 rounded-full bg-yellow-500"></div>
                            <div class="w-3 h-3 rounded-full bg-green-500"></div>
                        </div>
                        <div id="logs" class="space-y-2 mt-4 text-green-400">
                            </div>
                        <div id="progressBarContainer" class="mt-6 w-full bg-slate-800 h-1 rounded-full overflow-hidden hidden">
                            <div id="progressBar" class="bg-green-500 h-1 w-0 transition-all duration-300"></div>
                        </div>
                    </div>

                    <div id="resultArea" class="hidden mt-6 text-center">
                        <a id="dlButton" href="#" class="inline-flex items-center gap-3 bg-green-600 hover:bg-green-700 text-white px-8 py-4 rounded-xl font-bold text-lg shadow-xl transition transform hover:-translate-y-1">
                            <i class="fa-solid fa-file-arrow-down"></i> DOSYAYI İNDİR
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

            async function startTask() {
                let link = document.getElementById('megaLink').value;
                if(!link) return alert("Link boş olamaz!");

                document.getElementById('startBtn').disabled = true;
                document.getElementById('startBtn').innerHTML = '<i class="fa-solid fa-circle-notch fa-spin"></i>';
                document.getElementById('console').classList.remove('hidden');
                addLog("Bağlantı kuruluyor...", "text-blue-400");

                try {
                    let req = await fetch('/api/task', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({link: link, token: '{{ key }}', hwid: hwid})
                    });
                    let res = await req.json();

                    if(res.success) {
                        taskId = res.taskId;
                        addLog("Görev kuyruğa eklendi. Worker bekleniyor...", "text-yellow-400");
                        document.getElementById('progressBarContainer').classList.remove('hidden');
                        startPolling();
                    } else {
                        addLog("HATA: " + res.msg, "text-red-500");
                        resetBtn();
                    }
                } catch(e) {
                    addLog("Sunucu hatası!", "text-red-500");
                    resetBtn();
                }
            }

            function startPolling() {
                let p = 0;
                timer = setInterval(async () => {
                    if(!taskId) return;
                    try {
                        let req = await fetch('/api/status/' + taskId);
                        let res = await req.json();

                        if(res.status === 'ISLENIYOR') {
                            addLog(res.log || "İşleniyor...", "text-slate-300");
                            p = (p < 90) ? p + 5 : 90; 
                            document.getElementById('progressBar').style.width = p + '%';
                        } else if(res.status === 'TAMAMLANDI') {
                            clearInterval(timer);
                            document.getElementById('progressBar').style.width = '100%';
                            addLog("İŞLEM TAMAMLANDI! Dosya hazır.", "text-green-400 font-bold");
                            setTimeout(() => {
                                document.getElementById('console').classList.add('hidden');
                                document.getElementById('resultArea').classList.remove('hidden');
                                document.getElementById('dlButton').href = res.result.url;
                            }, 1000);
                        } else if(res.status && res.status.includes('HATA')) {
                            clearInterval(timer);
                            addLog("HATA: " + res.log, "text-red-500 font-bold");
                            resetBtn();
                        }
                    } catch(e) {}
                }, 1500);
            }

            function addLog(msg, color) {
                let div = document.createElement('div');
                div.className = color;
                div.innerText = "> " + msg;
                let logs = document.getElementById('logs');
                logs.appendChild(div);
                logs.scrollTop = logs.scrollHeight;
                // Son logu güncelleme mantığı yerine ekleme yapıyoruz
            }

            function resetBtn() {
                document.getElementById('startBtn').disabled = false;
                document.getElementById('startBtn').innerHTML = '<i class="fa-solid fa-play"></i> BAŞLAT';
            }
        </script>
        {% endif %}

        {% if page == 'admin' %}
        <div class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
            <div class="glass-panel p-4 rounded-xl border-l-4 border-blue-500">
                <div class="text-xs text-slate-400">TOPLAM LİSANS</div>
                <div class="text-2xl font-bold text-white">{{ stats.total_lic }}</div>
            </div>
            <div class="glass-panel p-4 rounded-xl border-l-4 border-green-500">
                <div class="text-xs text-slate-400">AKTİF HESAP</div>
                <div class="text-2xl font-bold text-white">{{ stats.active_acc }}</div>
            </div>
            <div class="glass-panel p-4 rounded-xl border-l-4 border-red-500">
                <div class="text-xs text-slate-400">KOTASI DOLAN</div>
                <div class="text-2xl font-bold text-white">{{ stats.quota_acc }}</div>
            </div>
            <div class="glass-panel p-4 rounded-xl border-l-4 border-purple-500">
                <div class="text-xs text-slate-400">BEKLEYEN İŞ</div>
                <div class="text-2xl font-bold text-white">{{ stats.queue }}</div>
            </div>
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
            <div class="space-y-6">
                <div class="glass-panel p-6 rounded-xl">
                    <h3 class="font-bold mb-4 text-green-400 flex items-center gap-2"><i class="fa-solid fa-server"></i> Mega Hesapları</h3>
                    <form action="/admin/add_account" method="POST" class="mb-2">
                        <textarea name="accounts" class="w-full bg-dark/50 border border-slate-700 rounded p-2 text-xs h-24 text-white" placeholder="email:sifre (Alt alta)"></textarea>
                        <button class="w-full bg-green-600 hover:bg-green-700 text-white py-2 rounded text-xs font-bold mt-2">YÜKLE</button>
                    </form>
                    <a href="/admin/reset_accounts" class="block text-center text-xs text-yellow-500 hover:text-white mt-2">Tüm Kotaları Sıfırla</a>
                </div>

                <div class="glass-panel p-6 rounded-xl">
                    <h3 class="font-bold mb-4 text-purple-400 flex items-center gap-2"><i class="fa-solid fa-globe"></i> Proxyler</h3>
                    <form action="/admin/add_proxy" method="POST">
                        <textarea name="proxies" class="w-full bg-dark/50 border border-slate-700 rounded p-2 text-xs h-24 text-white" placeholder="ip:port (Alt alta)"></textarea>
                        <button class="w-full bg-purple-600 hover:bg-purple-700 text-white py-2 rounded text-xs font-bold mt-2">YÜKLE</button>
                    </form>
                </div>
            </div>

            <div class="lg:col-span-2 glass-panel p-6 rounded-xl">
                <h3 class="font-bold mb-4 text-white flex items-center gap-2"><i class="fa-solid fa-key"></i> Lisans Merkezi</h3>
                
                <form action="/admin/generate" method="POST" class="bg-dark/40 p-4 rounded-lg mb-6 flex gap-4 items-end">
                    <div><label class="text-xs text-slate-400">Adet</label><select name="count" class="bg-dark border border-slate-600 rounded p-2 text-sm text-white"><option value="1">1</option><option value="5">5</option><option value="10">10</option></select></div>
                    <div class="flex-grow"><label class="text-xs text-slate-400">Kota (GB)</label><input type="number" name="gb_limit" value="50" class="w-full bg-dark border border-slate-600 rounded p-2 text-sm text-white"></div>
                    <div class="flex-grow"><label class="text-xs text-slate-400">Gün</label><input type="number" name="days" value="30" class="w-full bg-dark border border-slate-600 rounded p-2 text-sm text-white"></div>
                    <button class="bg-primary hover:bg-blue-600 text-white px-6 py-2 rounded font-bold text-sm">OLUŞTUR</button>
                </form>

                {% if new_keys %}
                <div class="bg-black/50 p-4 rounded-lg mb-4 border border-green-500/30">
                    <p class="text-green-400 text-xs mb-2">YENİ LİSANSLAR (KOPYALA):</p>
                    <textarea class="w-full bg-transparent text-green-300 text-xs font-mono h-20 outline-none" readonly>{% for k in new_keys %}{{ k }}&#13;&#10;{% endfor %}</textarea>
                </div>
                {% endif %}

                <div class="overflow-x-auto">
                    <table class="w-full text-left text-xs text-slate-400">
                        <thead class="bg-dark/50 text-slate-200 uppercase">
                            <tr><th class="p-3">KEY</th><th class="p-3">DURUM</th><th class="p-3">KOTA</th><th class="p-3">BİTİŞ</th><th class="p-3">İŞLEM</th></tr>
                        </thead>
                        <tbody class="divide-y divide-slate-700">
                            {% for l in licenses %}
                            <tr class="hover:bg-slate-800/50">
                                <td class="p-3 font-mono text-white">{{ l.key }}</td>
                                <td class="p-3">
                                    {% if not l.isActive %}<span class="text-red-500 font-bold">BAN</span>
                                    {% elif l.is_expired %}<span class="text-orange-500">SÜRE</span>
                                    {% elif l.is_quota_full %}<span class="text-orange-500">KOTA</span>
                                    {% else %}<span class="text-green-500">AKTİF</span>{% endif %}
                                </td>
                                <td class="p-3">
                                    <div class="w-16 bg-slate-700 h-1.5 rounded-full mb-1"><div class="bg-blue-500 h-1.5 rounded-full" style="width:{{ l.percent }}%"></div></div>
                                    {{ l.usage_fmt }}
                                </td>
                                <td class="p-3">{{ l.expiry_fmt }}</td>
                                <td class="p-3 flex gap-2">
                                    {% if l.isActive %}<a href="/admin/ban/{{ l.key }}" class="text-red-400 hover:text-white">BAN</a>
                                    {% else %}<a href="/admin/unban/{{ l.key }}" class="text-green-400 hover:text-white">AÇ</a>{% endif %}
                                    <a href="/admin/reset_hwid/{{ l.key }}" class="text-blue-400 hover:text-white">RST</a>
                                    <a href="/admin/delete/{{ l.key }}" class="text-slate-500 hover:text-red-500">X</a>
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

# ==================== BACKEND MANTIĞI ====================

@app.route('/', methods=['GET'])
def index():
    # Session Kontrolü
    if session.get('admin'):
        return render_dashboard_admin()
    if session.get('user_key'):
        return render_dashboard_user(session['user_key'])
    
    # Giriş Sayfası
    return render_template_string(HTML_TEMPLATE, page='login')

@app.route('/auth', methods=['POST'])
def auth():
    key = request.form.get('auth_key', '').strip()
    
    # 1. Admin Kontrolü
    if key == ADMIN_PASSWORD:
        session['admin'] = True
        return redirect('/')
    
    # 2. Kullanıcı Kontrolü
    l = licenses_col.find_one({"key": key})
    if l:
        if not l.get('isActive', True):
            return render_template_string(HTML_TEMPLATE, page='login', error="Bu lisans anahtarı yasaklanmıştır.")
        
        # Süre Kontrolü
        if l.get('expiry_date') and datetime.datetime.now() > l['expiry_date']:
             return render_template_string(HTML_TEMPLATE, page='login', error="Lisans süresi dolmuştur.")
        
        session['user_key'] = key
        return redirect('/')
    
    return render_template_string(HTML_TEMPLATE, page='login', error="Geçersiz anahtar veya şifre.")

def render_dashboard_user(key):
    # Verileri Çek
    lic = licenses_col.find_one({"key": key})
    if not lic: session.clear(); return redirect('/')
    
    # Hesaplamalar
    used = lic.get('total_usage', 0)
    limit = lic.get('quota_limit', 0)
    percent = min(100, int((used / limit) * 100)) if limit > 0 else 0
    remaining = limit - used if limit > 0 else 0
    
    expiry = lic.get('expiry_date')
    expiry_str = format_date(expiry)
    
    return render_template_string(HTML_TEMPLATE, page='user', 
                                  key=key, 
                                  percent=percent, 
                                  remaining_fmt=format_size(remaining),
                                  expiry_str=expiry_str,
                                  session=session)

def render_dashboard_admin():
    # Admin verileri
    lics = list(licenses_col.find().sort("created_at", -1))
    now = datetime.datetime.now()
    
    for l in lics:
        l['usage_fmt'] = format_size(l.get('total_usage', 0))
        l['limit_fmt'] = format_size(l.get('quota_limit', 0))
        l['expiry_fmt'] = format_date(l.get('expiry_date'))
        
        l['is_expired'] = False
        if l.get('expiry_date') and now > l['expiry_date']: l['is_expired'] = True
        
        l['is_quota_full'] = False
        if l.get('quota_limit', 0) > 0 and l.get('total_usage', 0) >= l['quota_limit']: l['is_quota_full'] = True
        
        if l.get('quota_limit', 0) > 0:
            l['percent'] = min(100, int((l.get('total_usage', 0) / l['quota_limit']) * 100))
        else: l['percent'] = 0

    stats = {
        "total_lic": len(lics),
        "active_acc": accounts_col.count_documents({"status": "ACTIVE"}),
        "quota_acc": accounts_col.count_documents({"status": "QUOTA"}),
        "queue": queue.count_documents({"status": "SIRADA"}),
    }
    
    return render_template_string(HTML_TEMPLATE, page='admin', 
                                  licenses=lics, 
                                  stats=stats, 
                                  session=session, 
                                  new_keys=session.pop('new_keys', None))

# ==================== ADMIN ACTIONS ====================
@app.route('/admin/generate', methods=['POST'])
def generate():
    if not session.get('admin'): return redirect('/')
    try:
        count = int(request.form.get('count', 1))
        gb_limit = int(request.form.get('gb_limit', 50))
        days = int(request.form.get('days', 30))
        quota_bytes = gb_limit * (1024**3)
        expiry = datetime.datetime.now() + datetime.timedelta(days=days)
        keys = []
        for _ in range(count):
            k = f"VIP-{uuid.uuid4().hex[:8].upper()}"
            licenses_col.insert_one({
                "key": k, "isActive": True, "hwid": None, "total_usage": 0,
                "quota_limit": quota_bytes, "expiry_date": expiry, "created_at": datetime.datetime.now()
            })
            keys.append(k)
        session['new_keys'] = keys
    except: pass
    return redirect('/')

@app.route('/admin/add_account', methods=['POST'])
def add_acc():
    if not session.get('admin'): return redirect('/')
    raw = request.form.get('accounts', '')
    for line in raw.split('\n'):
        if ':' in line:
            email, pwd = line.strip().split(':', 1)
            if not accounts_col.find_one({"email": email}):
                accounts_col.insert_one({"email": email, "password": pwd, "status": "ACTIVE"})
    return redirect('/')

@app.route('/admin/add_proxy', methods=['POST'])
def add_px():
    if not session.get('admin'): return redirect('/')
    raw = request.form.get('proxies', '')
    proxies_col.delete_many({}) 
    for line in raw.split('\n'):
        if line.strip(): proxies_col.insert_one({"ip": line.strip()})
    return redirect('/')

@app.route('/admin/reset_accounts', methods=['GET'])
def reset_accs():
    if not session.get('admin'): return redirect('/')
    accounts_col.update_many({}, {"$set": {"status": "ACTIVE"}})
    return redirect('/')

@app.route('/admin/ban/<k>')
def ban(k): 
    if not session.get('admin'): return redirect('/')
    licenses_col.update_one({"key": k}, {"$set": {"isActive": False}})
    return redirect('/')

@app.route('/admin/unban/<k>')
def unban(k): 
    if not session.get('admin'): return redirect('/')
    licenses_col.update_one({"key": k}, {"$set": {"isActive": True}})
    return redirect('/')

@app.route('/admin/reset_hwid/<k>')
def reset_hwid(k): 
    if not session.get('admin'): return redirect('/')
    licenses_col.update_one({"key": k}, {"$set": {"hwid": None}})
    return redirect('/')

@app.route('/admin/delete/<k>')
def delete(k): 
    if not session.get('admin'): return redirect('/')
    licenses_col.delete_one({"key": k})
    return redirect('/')

@app.route('/logout')
def logout(): session.clear(); return redirect('/')

# ==================== API (WORKER ILE HABERLEŞME) ====================
@app.route('/api/task', methods=['POST'])
def api_task():
    d = request.json
    l = licenses_col.find_one({"key": d['token']})
    
    # Güvenlik Kontrolleri
    if not l or not l.get('isActive', True): return jsonify({"success": False, "msg": "Geçersiz/Banlı Lisans"})
    if l.get('expiry_date') and datetime.datetime.now() > l['expiry_date']: return jsonify({"success": False, "msg": "Süre Doldu"})
    if l.get('quota_limit', 0) > 0 and l.get('total_usage', 0) >= l['quota_limit']: return jsonify({"success": False, "msg": "Kota Doldu"})
    if l.get('hwid') and l['hwid'] != d['hwid']: return jsonify({"success": False, "msg": "Farklı Cihaz!"})
    if not l.get('hwid'): licenses_col.update_one({"key": d['token']}, {"$set": {"hwid": d['hwid']}})

    tid = str(uuid.uuid4())
    queue.insert_one({"task_id": tid, "link": d['link'], "owner": d['token'], "status": "SIRADA", "log": "Sıraya alındı..."})
    return jsonify({"success": True, "taskId": tid})

@app.route('/api/status/<tid>')
def status(tid): return jsonify(queue.find_one({"task_id": tid}, {"_id": 0}))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
