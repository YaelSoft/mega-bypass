import os
import uuid
import datetime
import math
import pymongo
from flask import Flask, render_template_string, request, jsonify, session, redirect
from pymongo import MongoClient

app = Flask(__name__)
app.secret_key = "V49_MEMORY_SECRET"

MONGO_URI = os.environ.get("MONGO_URI")
ADMIN_PASSWORD = "YASIN_BABA_123"

client = MongoClient(MONGO_URI)
db = client['mega_leech']
queue = db['queue']
accounts_col = db['accounts']
proxies_col = db['proxies']
licenses_col = db['licenses']

def format_size(s):
    if s == 0: return "0 B"
    n = ("B", "KB", "MB", "GB", "TB")
    i = int(math.floor(math.log(s, 1024)))
    p = math.pow(1024, i)
    return "%s %s" % (round(s / p, 2), n[i])

def format_date(d):
    if not d: return "Süresiz"
    return d.strftime("%d.%m.%Y")

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="tr" class="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>M-CLOUD V49</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <script>
        tailwind.config = {
            darkMode: 'class',
            theme: { extend: { colors: { primary: '#6366f1', dark: '#0f172a' } } }
        }
    </script>
    <style>body { background-color: #020617; color: #e2e8f0; font-family: 'Segoe UI', sans-serif; }</style>
</head>
<body class="bg-gray-900 text-white min-h-screen">
    
    <nav class="bg-gray-800 p-4 border-b border-gray-700">
        <div class="container mx-auto flex justify-between items-center">
            <div class="font-bold text-xl text-blue-500">M-CLOUD <span class="text-xs text-white">V49 PRO</span></div>
            {% if session.user_key or session.admin %}<a href="/logout" class="text-sm text-gray-400">Çıkış</a>{% endif %}
        </div>
    </nav>

    <main class="container mx-auto p-6">
        {% if page == 'login' %}
        <div class="flex justify-center mt-20">
            <div class="bg-gray-800 p-8 rounded-lg shadow-lg w-96">
                <h2 class="text-center text-2xl font-bold mb-4">Giriş Yap</h2>
                <form action="/auth" method="POST">
                    <input type="password" name="auth_key" class="w-full p-3 bg-gray-900 rounded mb-4 text-white border border-gray-700" placeholder="Lisans Anahtarı" required>
                    <button class="w-full bg-blue-600 hover:bg-blue-700 py-3 rounded font-bold">GİRİŞ</button>
                </form>
                {% if error %}<p class="text-red-500 text-center mt-4 text-sm">{{ error }}</p>{% endif %}
            </div>
        </div>
        {% endif %}

        {% if page == 'user' %}
        <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div class="space-y-6">
                <div class="bg-gray-800 p-6 rounded-lg border border-gray-700">
                    <h3 class="text-gray-400 text-xs font-bold mb-4">LİSANS</h3>
                    <div class="text-center text-4xl font-bold mb-2">{{ percent }}%</div>
                    <div class="text-center text-xs text-gray-500 mb-4">KOTA DOLULUĞU</div>
                    <div class="flex justify-between text-sm p-2 bg-gray-900 rounded"><span>Kalan:</span> <span class="font-bold">{{ remaining_fmt }}</span></div>
                </div>
            </div>

            <div class="lg:col-span-2">
                <div class="bg-gray-800 p-8 rounded-lg border border-gray-700">
                    <h2 class="text-xl font-bold mb-4">Dosya İndir</h2>
                    <div class="flex gap-2 mb-4">
                        <input type="text" id="megaLink" class="flex-grow p-3 bg-gray-900 border border-gray-700 rounded text-white" placeholder="https://mega.nz/...">
                        <button onclick="startTask()" id="startBtn" class="bg-blue-600 px-6 rounded font-bold">İNDİR</button>
                    </div>

                    <div id="console" class="hidden bg-black p-4 rounded font-mono text-sm h-64 overflow-y-auto mb-4 border border-gray-700">
                        <div id="logs" class="space-y-1"></div>
                    </div>

                    <div id="resultArea" class="hidden text-center bg-green-900/20 p-6 rounded border border-green-500/30">
                        <h3 class="text-xl font-bold text-green-400 mb-2">Dosya Hazır!</h3>
                        <a id="dlButton" href="#" class="bg-green-600 px-8 py-3 rounded font-bold inline-block hover:bg-green-700">İNDİR</a>
                        <button onclick="clearTask()" class="block mx-auto mt-4 text-xs text-gray-500 hover:text-white">Yeni İşlem</button>
                    </div>
                </div>
            </div>
        </div>

        <script>
            let hwid = localStorage.getItem('hwid') || Math.random().toString(36).substring(7);
            localStorage.setItem('hwid', hwid);
            let taskId = localStorage.getItem('activeTaskId'); // HAFIZADAN ÇEK
            let timer = null;

            // SAYFA YÜKLENİNCE KONTROL ET
            window.onload = function() {
                if(taskId) {
                    console.log("Eski görev bulundu: " + taskId);
                    restoreTask();
                }
            };

            function addLog(msg, color="text-green-400") {
                const div = document.createElement('div');
                div.className = color;
                div.innerText = "> " + msg;
                document.getElementById('logs').appendChild(div);
                document.getElementById('logs').scrollTop = 9999;
            }

            async function startTask() {
                const link = document.getElementById('megaLink').value;
                if(!link) return alert("Link gir!");
                
                document.getElementById('startBtn').disabled = true;
                document.getElementById('console').classList.remove('hidden');
                document.getElementById('resultArea').classList.add('hidden');
                document.getElementById('logs').innerHTML = '';
                addLog("Başlatılıyor...", "text-blue-400");

                try {
                    const req = await fetch('/api/task', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({link: link, token: '{{ key }}', hwid: hwid})
                    });
                    const res = await req.json();
                    if(res.success) {
                        taskId = res.taskId;
                        localStorage.setItem('activeTaskId', taskId); // HAFIZAYA KAYDET
                        startPolling();
                    } else {
                        addLog("HATA: " + res.msg, "text-red-500");
                        document.getElementById('startBtn').disabled = false;
                    }
                } catch(e) { alert("Sunucu Hatası"); }
            }

            function restoreTask() {
                document.getElementById('startBtn').disabled = true;
                document.getElementById('console').classList.remove('hidden');
                addLog("Önceki işlem devam ettiriliyor...", "text-yellow-400");
                startPolling();
            }

            function startPolling() {
                if(timer) clearInterval(timer);
                timer = setInterval(async () => {
                    if(!taskId) return;
                    try {
                        const req = await fetch('/api/status/' + taskId);
                        const res = await req.json();
                        
                        if(res.log) {
                            const lastLog = document.getElementById('logs').lastElementChild;
                            if(!lastLog || lastLog.innerText !== "> " + res.log) {
                                addLog(res.log, res.status.includes('HATA') ? 'text-red-400' : 'text-green-400');
                            }
                        }

                        if(res.status === 'TAMAMLANDI') {
                            clearInterval(timer);
                            document.getElementById('console').classList.add('hidden');
                            document.getElementById('resultArea').classList.remove('hidden');
                            document.getElementById('dlButton').href = res.result.url;
                            // İşlem bitti ama link kalsın, kullanıcı clearTask ile silsin
                        } else if(res.status && res.status.includes('HATA')) {
                            clearInterval(timer);
                            addLog("BAŞARISIZ.", "text-red-500 font-bold");
                            localStorage.removeItem('activeTaskId');
                            document.getElementById('startBtn').disabled = false;
                        }
                    } catch(e) {}
                }, 2000);
            }

            function clearTask() {
                taskId = null;
                localStorage.removeItem('activeTaskId');
                location.reload();
            }
        </script>
        {% endif %}

        {% if page == 'admin' %}
        <div class="grid grid-cols-4 gap-4 mb-6">
            <div class="bg-gray-800 p-4 rounded border-t-4 border-blue-500 text-center">
                <div class="text-2xl font-bold">{{ stats.queue }}</div>
                <div class="text-xs text-gray-400">KUYRUK</div>
            </div>
            <div class="col-span-3 flex justify-end items-center">
                 <a href="/admin/clear_queue" class="bg-red-600 px-6 py-3 rounded font-bold hover:bg-red-700">KUYRUĞU SIFIRLA</a>
            </div>
        </div>
        
        <div class="grid grid-cols-2 gap-6">
            <div class="bg-gray-800 p-6 rounded">
                <h3 class="font-bold mb-2">HESAPLAR</h3>
                <form action="/admin/add_account" method="POST">
                    <textarea name="accounts" class="w-full bg-gray-900 p-2 h-32 mb-2 text-white border border-gray-700" placeholder="email:pass"></textarea>
                    <button class="bg-green-600 w-full py-2 rounded font-bold">YÜKLE</button>
                </form>
            </div>
            <div class="bg-gray-800 p-6 rounded">
                <h3 class="font-bold mb-2">PROXYLER</h3>
                <form action="/admin/add_proxy" method="POST">
                    <textarea name="proxies" class="w-full bg-gray-900 p-2 h-32 mb-2 text-white border border-gray-700" placeholder="http://user:pass@ip:port"></textarea>
                    <button class="bg-purple-600 w-full py-2 rounded font-bold">YÜKLE</button>
                </form>
            </div>
        </div>
        <div class="mt-6 bg-gray-800 p-6 rounded">
            <h3 class="font-bold mb-2">LİSANS OLUŞTUR</h3>
            <form action="/admin/generate" method="POST" class="flex gap-2">
                <input type="number" name="count" value="1" class="bg-gray-900 p-2 text-white border border-gray-700 w-20">
                <input type="number" name="gb_limit" value="50" class="bg-gray-900 p-2 text-white border border-gray-700 w-20" placeholder="GB">
                <input type="number" name="days" value="30" class="bg-gray-900 p-2 text-white border border-gray-700 w-20" placeholder="Gün">
                <button class="bg-blue-600 px-4 rounded font-bold">OLUŞTUR</button>
            </form>
             {% if new_keys %}<textarea class="w-full bg-black text-green-400 mt-4 h-24 p-2" readonly>{% for k in new_keys %}{{ k }}&#13;&#10;{% endfor %}</textarea>{% endif %}
        </div>
        {% endif %}

    </main>
</body>
</html>
"""

# ==================== BACKEND (AYNI KALDI) ====================
# (Admin login, queue reset vb kodlar buraya gelecek, 
# yer kaplamasın diye V48'deki backend kısmının aynısını kullanabilirsin 
# veya yukarıdaki V48 kodunun backend kısmını alıp HTML_TEMPLATE'i bununla değiştir)

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
    return render_template_string(HTML_TEMPLATE, page='login', error="Hatalı Anahtar")

def render_dashboard_user(key):
    lic = licenses_col.find_one({"key": key})
    if not lic: session.clear(); return redirect('/')
    used = lic.get('total_usage', 0); limit = lic.get('quota_limit', 0)
    remaining = limit - used if limit > 0 else 0
    percent = min(100, int((used / limit) * 100)) if limit > 0 else 0
    return render_template_string(HTML_TEMPLATE, page='user', key=key, percent=percent, remaining_fmt=format_size(remaining), session=session)

def render_dashboard_admin():
    stats = {"queue": queue.count_documents({"status": "SIRADA"})}
    return render_template_string(HTML_TEMPLATE, page='admin', stats=stats, session=session, new_keys=session.pop('new_keys', None))

@app.route('/admin/clear_queue')
def clear_queue():
    if session.get('admin'): queue.delete_many({})
    return redirect('/')

# Diğer route'lar (generate, add_account, add_proxy, api_task...) V48 ile aynı
# Lütfen V48'in alt kısmını buraya yapıştır.
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
    proxies_col.delete_many({}) 
    for line in request.form.get('proxies', '').split('\n'):
        if line.strip(): proxies_col.insert_one({"ip": line.strip()})
    return redirect('/')

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

@app.route('/logout')
def logout(): session.clear(); return redirect('/')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
