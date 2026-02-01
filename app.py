import os
import uuid
import datetime
from flask import Flask, render_template_string, request, jsonify, session, redirect
from pymongo import MongoClient

app = Flask(__name__)
app.secret_key = "RENDER_ADMIN_PANEL_KEY"

# MONGODB BAĞLANTISI
MONGO_URI = os.environ.get("MONGO_URI")
ADMIN_PASSWORD = "Ata_Yasin33"

client = MongoClient(MONGO_URI)
db = client['mega_leech']
queue = db['queue']
accounts_col = db['accounts'] # Mega Hesapları Burada
proxies_col = db['proxies']   # Senin Eklediğin Proxyler Burada

# --- HTML ŞABLONU ---
HTML = """
<!DOCTYPE html><html lang="tr"><head><meta charset="UTF-8"><title>M-CLOUD YÖNETİM</title>
<script src="https://cdn.tailwindcss.com"></script></head>
<body class="bg-gray-900 text-white font-sans min-h-screen">
    <nav class="p-4 border-b border-gray-700 flex justify-between bg-gray-800">
        <div class="font-bold text-xl text-blue-500">M-CLOUD <span class="text-white">PANEL</span></div>
        {% if session.admin %}<a href="/logout" class="text-red-400 text-sm">Çıkış</a>{% endif %}
    </nav>

    <div class="container mx-auto p-6">
        {% if not session.admin %}
        <div class="max-w-md mx-auto bg-gray-800 p-8 rounded shadow-lg mt-10">
            <h2 class="text-center text-xl font-bold mb-4">YÖNETİCİ GİRİŞİ</h2>
            <form method="POST" action="/login">
                <input type="password" name="password" class="w-full p-3 bg-gray-700 rounded mb-4 text-white" placeholder="Şifre">
                <button class="w-full bg-blue-600 py-2 rounded font-bold">GİRİŞ</button>
            </form>
        </div>
        {% else %}
        
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            
            <div class="bg-gray-800 p-6 rounded shadow border border-gray-700">
                <h3 class="font-bold text-lg mb-4 text-green-400">MEGA HESAPLARI ({{ acc_count }})</h3>
                <form method="POST" action="/admin/add_account" class="mb-4">
                    <textarea name="accounts" class="w-full p-2 bg-gray-900 rounded text-sm h-32" placeholder="email:sifre formatında alt alta yazın..."></textarea>
                    <button class="bg-green-600 px-4 py-2 rounded text-sm mt-2 w-full font-bold">HESAPLARI YÜKLE</button>
                </form>
                <div class="h-48 overflow-y-auto bg-gray-900 p-2 rounded text-xs">
                    {% for acc in accounts %}
                    <div class="flex justify-between border-b border-gray-800 py-1">
                        <span class="{{ 'text-red-500' if acc.status == 'QUOTA' else 'text-gray-300' }}">{{ acc.email }}</span>
                        <span>{{ acc.status }}</span>
                    </div>
                    {% endfor %}
                </div>
                <a href="/admin/reset_accounts" class="block text-center text-yellow-500 text-xs mt-2">Tüm Hesapları Sıfırla (Kota Aç)</a>
            </div>

            <div class="bg-gray-800 p-6 rounded shadow border border-gray-700">
                <h3 class="font-bold text-lg mb-4 text-purple-400">ÖZEL PROXY LİSTESİ ({{ proxy_count }})</h3>
                <form method="POST" action="/admin/add_proxy" class="mb-4">
                    <textarea name="proxies" class="w-full p-2 bg-gray-900 rounded text-sm h-32" placeholder="ip:port formatında alt alta yazın..."></textarea>
                    <button class="bg-purple-600 px-4 py-2 rounded text-sm mt-2 w-full font-bold">PROXYLERİ YÜKLE</button>
                </form>
                <div class="h-48 overflow-y-auto bg-gray-900 p-2 rounded text-xs font-mono">
                    {% for p in proxies %}
                    <div class="border-b border-gray-800 py-1">{{ p.ip }}</div>
                    {% endfor %}
                </div>
            </div>

        </div>

        <div class="mt-8 bg-gray-800 p-6 rounded shadow border border-gray-700">
            <h3 class="font-bold text-lg mb-4 text-blue-400">YENİ İNDİRME GÖREVİ</h3>
            <input type="text" id="link" class="w-full p-3 bg-gray-900 rounded mb-2" placeholder="Mega Linki...">
            <button onclick="addTask()" class="bg-blue-600 px-6 py-3 rounded font-bold w-full">BAŞLAT</button>
            <div id="status" class="mt-4 text-sm text-gray-400"></div>
        </div>

        {% endif %}
    </div>
    <script>
        async function addTask() {
            let l = document.getElementById('link').value;
            let r = await fetch('/api/task', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({link:l})});
            let d = await r.json();
            document.getElementById('status').innerText = d.success ? "Görev Worker'a iletildi! ID: " + d.taskId : "Hata!";
        }
    </script>
</body></html>
"""

@app.route('/', methods=['GET', 'POST'])
def index():
    return redirect('/admin') # Direkt admin paneline at

@app.route('/login', methods=['POST'])
def login():
    if request.form.get('password') == ADMIN_PASSWORD:
        session['admin'] = True
    return redirect('/admin')

@app.route('/admin')
def admin():
    accs = list(accounts_col.find())
    pxs = list(proxies_col.find())
    return render_template_string(HTML, accounts=accs, proxies=pxs, acc_count=len(accs), proxy_count=len(pxs), session=session)

@app.route('/admin/add_account', methods=['POST'])
def add_acc():
    if not session.get('admin'): return redirect('/')
    raw = request.form.get('accounts', '')
    for line in raw.split('\n'):
        if ':' in line:
            email, pwd = line.strip().split(':', 1)
            # Eğer hesap yoksa ekle
            if not accounts_col.find_one({"email": email}):
                accounts_col.insert_one({"email": email, "password": pwd, "status": "ACTIVE", "last_used": None})
    return redirect('/admin')

@app.route('/admin/add_proxy', methods=['POST'])
def add_px():
    if not session.get('admin'): return redirect('/')
    raw = request.form.get('proxies', '')
    proxies_col.delete_many({}) # Öncekileri temizle (İstersen kaldırırsın)
    for line in raw.split('\n'):
        if line.strip():
            proxies_col.insert_one({"ip": line.strip()})
    return redirect('/admin')

@app.route('/admin/reset_accounts', methods=['GET'])
def reset_accs():
    if not session.get('admin'): return redirect('/')
    accounts_col.update_many({}, {"$set": {"status": "ACTIVE"}})
    return redirect('/admin')

@app.route('/api/task', methods=['POST'])
def api_task():
    data = request.json
    tid = str(uuid.uuid4())
    queue.insert_one({"task_id": tid, "link": data['link'], "status": "SIRADA", "log": "Worker bekleniyor..."})
    return jsonify({"success": True, "taskId": tid})

@app.route('/api/status/<tid>')
def status(tid): return jsonify(queue.find_one({"task_id": tid}, {"_id": 0}))

@app.route('/logout')
def logout(): session.clear(); return redirect('/')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
