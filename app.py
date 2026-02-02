import os
import uuid
import datetime
import requests
import json
from flask import Flask, render_template_string, request, redirect, url_for, session, jsonify
from pymongo import MongoClient
from bson.objectid import ObjectId

app = Flask(__name__)
app.secret_key = os.urandom(24)

# ==================== AYARLAR ====================
MONGO_URI = os.environ.get("MONGO_URI")
ADMIN_PASS = os.environ.get("ADMIN_PASS", "Ata_Yasin536373")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
REPO_OWNER = os.environ.get("REPO_OWNER")
REPO_NAME = os.environ.get("REPO_NAME")

# DB Bağlantısı
client = MongoClient(MONGO_URI)
db = client['mega_leech']
queue_col = db['queue']
licenses_col = db['licenses']

# ==================== GITHUB TETİKLEYİCİ (MOTOR) ====================
def trigger_github(link, task_id):
    if not GITHUB_TOKEN or not REPO_OWNER:
        return False, "GitHub Ayarları Eksik!"

    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/dispatches"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    data = {
        "event_type": "indir_kocum",
        "client_payload": {"link": link, "task_id": task_id}
    }
    
    try:
        resp = requests.post(url, headers=headers, data=json.dumps(data), timeout=10)
        if resp.status_code == 204:
            return True, "GitHub Başlatıldı!"
        else:
            return False, f"GitHub Hatası: {resp.text}"
    except Exception as e:
        return False, str(e)

# ==================== HTML TASARIM (DARK MODE - VIP) ====================
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MEGA VIP DOWNLOADER</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
        body { background-color: #121212; color: #e0e0e0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
        .card { background-color: #1e1e1e; border: 1px solid #333; margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.3); }
        .form-control, .form-select { background-color: #2c2c2c; border: 1px solid #444; color: #fff; }
        .form-control:focus { background-color: #2c2c2c; color: #fff; border-color: #0d6efd; box-shadow: none; }
        .btn-primary { background-color: #0d6efd; border: none; }
        .btn-danger { background-color: #dc3545; }
        .status-badge { padding: 5px 10px; border-radius: 4px; font-size: 0.85em; font-weight: bold; }
        .badge-sırada { background-color: #ffc107; color: #000; }
        .badge-isleniyor { background-color: #0d6efd; color: #fff; animation: pulse 1.5s infinite; }
        .badge-tamamlandi { background-color: #198754; color: #fff; }
        .badge-hata { background-color: #dc3545; color: #fff; }
        @keyframes pulse { 0% { opacity: 1; } 50% { opacity: 0.6; } 100% { opacity: 1; } }
        .navbar { background-color: #1e1e1e; border-bottom: 1px solid #333; }
        .log-box { background: #000; color: #0f0; font-family: monospace; padding: 10px; border-radius: 5px; max-height: 150px; overflow-y: auto; font-size: 12px; }
        .nav-tabs .nav-link { color: #aaa; }
        .nav-tabs .nav-link.active { background-color: #2c2c2c; color: #fff; border-color: #333; }
    </style>
</head>
<body>

<nav class="navbar navbar-expand-lg navbar-dark mb-4">
  <div class="container">
    <a class="navbar-brand" href="#"><i class="fas fa-cloud-download-alt"></i> MEGA VIP</a>
    <div class="d-flex">
        {% if session.get('is_admin') %}
            <span class="badge bg-danger me-3 align-self-center">YÖNETİCİ MODU</span>
            <a href="/logout" class="btn btn-sm btn-outline-light">Çıkış</a>
        {% elif session.get('license_key') %}
            <span class="badge bg-success me-3 align-self-center">LİSANS: {{ session['license_key'] }}</span>
            <a href="/logout" class="btn btn-sm btn-outline-light">Çıkış</a>
        {% endif %}
    </div>
  </div>
</nav>

<div class="container">
    
    {% with messages = get_flashed_messages(with_categories=true) %}
      {% if messages %}
        {% for category, message in messages %}
          <div class="alert alert-{{ category }} alert-dismissible fade show" role="alert">
            {{ message }}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
          </div>
        {% endfor %}
      {% endif %}
    {% endwith %}

    {% if not session.get('license_key') and not session.get('is_admin') %}
    <div class="row justify-content-center mt-5">
        <div class="col-md-6">
            <div class="card p-4">
                <h3 class="text-center mb-4">Sisteme Giriş</h3>
                <form method="POST" action="/login">
                    <div class="mb-3">
                        <label>Lisans Anahtarı veya Yönetici Şifresi</label>
                        <input type="text" name="auth_key" class="form-control" placeholder="Anahtar giriniz..." required>
                    </div>
                    <button type="submit" class="btn btn-primary w-100">Giriş Yap</button>
                </form>
            </div>
        </div>
    </div>

    {% else %}
    
    <ul class="nav nav-tabs mb-3" id="myTab" role="tablist">
        <li class="nav-item">
            <button class="nav-link active" id="home-tab" data-bs-toggle="tab" data-bs-target="#home" type="button">🚀 İndirici</button>
        </li>
        {% if session.get('is_admin') %}
        <li class="nav-item">
            <button class="nav-link" id="admin-tab" data-bs-toggle="tab" data-bs-target="#admin" type="button">🛡️ Admin Paneli</button>
        </li>
        {% endif %}
    </ul>

    <div class="tab-content" id="myTabContent">
        
        <div class="tab-pane fade show active" id="home">
            <div class="row">
                <div class="col-md-4">
                    <div class="card p-3">
                        <h5><i class="fas fa-plus-circle"></i> Yeni İşlem</h5>
                        <form method="POST" action="/add_task">
                            <div class="mb-3">
                                <label>Mega Linki</label>
                                <input type="text" name="link" class="form-control" placeholder="https://mega.nz/..." required>
                            </div>
                            <div class="d-grid">
                                <button type="submit" class="btn btn-primary">İndirmeyi Başlat</button>
                            </div>
                        </form>
                        {% if not session.get('is_admin') %}
                        <hr>
                        <div class="small text-muted">
                            <p class="mb-1">Kalan Gün: <strong>{{ license_info.days_left }}</strong></p>
                            <p class="mb-1">Kota: <strong>{{ license_info.used_gb }} / {{ license_info.gb_limit }} GB</strong></p>
                            <div class="progress" style="height: 5px;">
                              <div class="progress-bar bg-info" role="progressbar" style="width: {{ (license_info.used_gb / license_info.gb_limit) * 100 }}%"></div>
                            </div>
                        </div>
                        {% endif %}
                    </div>
                </div>

                <div class="col-md-8">
                    <div class="card p-3">
                        <div class="d-flex justify-content-between align-items-center mb-3">
                            <h5><i class="fas fa-tasks"></i> İşlem Kuyruğu</h5>
                            <a href="/" class="btn btn-sm btn-outline-secondary"><i class="fas fa-sync"></i> Yenile</a>
                        </div>
                        <div class="table-responsive">
                            <table class="table table-dark table-hover table-sm">
                                <thead>
                                    <tr>
                                        <th>ID</th>
                                        <th>Durum</th>
                                        <th>Log</th>
                                        <th>Sonuç</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {% for task in tasks %}
                                    <tr>
                                        <td><small>{{ task.task_id[:5] }}</small></td>
                                        <td><span class="status-badge badge-{{ task.status|lower }}">{{ task.status }}</span></td>
                                        <td>
                                            {% if task.status == 'TAMAMLANDI' %}
                                                <a href="{{ task.result.url }}" target="_blank" class="btn btn-sm btn-success">
                                                    <i class="fas fa-download"></i> İNDİR
                                                </a>
                                            {% elif task.status == 'ISLENIYOR' %}
                                                <small class="text-info">{{ task.log }}</small>
                                            {% else %}
                                                <small class="text-muted">{{ task.log }}</small>
                                            {% endif %}
                                        </td>
                                        <td>
                                            {% if task.result and task.result.name %}
                                                <small>{{ task.result.name }}</small>
                                            {% endif %}
                                        </td>
                                    </tr>
                                    {% endfor %}
                                </tbody>
                            </table>
                            {% if not tasks %}
                                <p class="text-center text-muted">Henüz işlem yok.</p>
                            {% endif %}
                        </div>
                    </div>
                </div>
            </div>
        </div>

        {% if session.get('is_admin') %}
        <div class="tab-pane fade" id="admin">
            <div class="row">
                <div class="col-md-6">
                    <div class="card p-3">
                        <h5><i class="fas fa-key"></i> Lisans Oluştur</h5>
                        <form method="POST" action="/admin/create_license">
                            <div class="row">
                                <div class="col-6 mb-3">
                                    <label>Gün Sayısı</label>
                                    <input type="number" name="days" class="form-control" value="30">
                                </div>
                                <div class="col-6 mb-3">
                                    <label>GB Sınırı</label>
                                    <input type="number" name="gb_limit" class="form-control" value="50">
                                </div>
                            </div>
                            <button type="submit" class="btn btn-success w-100">Lisans Üret</button>
                        </form>
                    </div>
                    
                    <div class="card p-3 mt-3">
                        <h5><i class="fas fa-broom"></i> Sistem Kontrolü</h5>
                        <div class="d-flex gap-2">
                            <a href="/admin/clear_queue" class="btn btn-warning flex-fill" onclick="return confirm('Tüm kuyruk silinecek?')">
                                <i class="fas fa-trash"></i> Listeyi Temizle
                            </a>
                            <a href="/admin/stop_all" class="btn btn-danger flex-fill" onclick="return confirm('İşlemler durdurulacak?')">
                                <i class="fas fa-stop-circle"></i> İşlemleri Durdur
                            </a>
                        </div>
                    </div>
                </div>

                <div class="col-md-6">
                    <div class="card p-3">
                        <h5>Aktif Lisanslar</h5>
                        <div class="table-responsive" style="max-height: 400px; overflow-y: auto;">
                            <table class="table table-dark table-sm">
                                <thead>
                                    <tr>
                                        <th>Anahtar</th>
                                        <th>Kalan Gün</th>
                                        <th>Kota</th>
                                        <th>İşlem</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {% for lic in licenses %}
                                    <tr>
                                        <td><small>{{ lic.key }}</small></td>
                                        <td>{{ lic.days }}</td>
                                        <td>{{ lic.used_gb }}/{{ lic.gb_limit }}</td>
                                        <td>
                                            <a href="/admin/del_license/{{ lic.key }}" class="text-danger"><i class="fas fa-times"></i></a>
                                        </td>
                                    </tr>
                                    {% endfor %}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        {% endif %}

    </div>
    {% endif %}
</div>

<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
"""

# ==================== ROTALAR ====================
@app.route('/', methods=['GET'])
def index():
    if not session.get('license_key') and not session.get('is_admin'):
        return render_template_string(HTML_TEMPLATE)
    
    # Verileri Çek
    tasks = list(queue_col.find().sort('_id', -1).limit(20))
    licenses = []
    license_info = {}

    if session.get('is_admin'):
        licenses = list(licenses_col.find())
    else:
        # Kullanıcı lisans bilgilerini çek
        lic = licenses_col.find_one({"key": session['license_key']})
        if lic:
            # Gün hesaplama (Basit)
            create_date = lic.get('created_at', datetime.datetime.now())
            days_passed = (datetime.datetime.now() - create_date).days
            days_left = max(0, lic['days'] - days_passed)
            
            license_info = {
                "days_left": days_left,
                "used_gb": lic.get('used_gb', 0),
                "gb_limit": lic.get('gb_limit', 0)
            }

    return render_template_string(HTML_TEMPLATE, tasks=tasks, licenses=licenses, license_info=license_info)

@app.route('/login', methods=['POST'])
def login():
    key = request.form.get('auth_key')
    
    # Admin Girişi
    if key == ADMIN_PASS:
        session['is_admin'] = True
        return redirect('/')
    
    # Lisans Girişi
    lic = licenses_col.find_one({"key": key})
    if lic:
        # Tarih kontrolü yapılabilir
        session['license_key'] = key
        return redirect('/')
        
    return "Hatalı Anahtar!", 403

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

@app.route('/add_task', methods=['POST'])
def add_task():
    if not session.get('license_key') and not session.get('is_admin'):
        return redirect('/')
        
    link = request.form.get('link')
    
    # Kota Kontrolü (Admin hariç)
    if not session.get('is_admin'):
        lic = licenses_col.find_one({"key": session['license_key']})
        if lic and lic.get('used_gb', 0) >= lic.get('gb_limit', 0):
             return "KOTA DOLDU! Lütfen paketinizi yükseltin."

    task_id = str(uuid.uuid4())
    
    # DB'ye Ekle
    queue_col.insert_one({
        "task_id": task_id,
        "link": link,
        "status": "SIRADA",
        "log": "GitHub Sunucusu Bekleniyor...",
        "result": {},
        "owner": session.get('license_key', 'admin'),
        "created_at": datetime.datetime.now()
    })
    
    # GITHUB'I TETİKLE (MOTORU ÇALIŞTIR)
    success, msg = trigger_github(link, task_id)
    
    if success:
        # Kotadan düş (Tahmini 1 GB düşelim şimdilik, sonra güncellenir)
        if not session.get('is_admin'):
            licenses_col.update_one({"key": session['license_key']}, {"$inc": {"used_gb": 1}})
    else:
        queue_col.update_one({"task_id": task_id}, {"$set": {"status": "HATA", "log": msg}})
        
    return redirect('/')

# ==================== ADMIN İŞLEMLERİ ====================
@app.route('/admin/create_license', methods=['POST'])
def create_license():
    if not session.get('is_admin'): return "Yetkisiz", 403
    
    days = int(request.form.get('days'))
    gb = int(request.form.get('gb_limit'))
    key = str(uuid.uuid4())[:8].upper()
    
    licenses_col.insert_one({
        "key": key,
        "days": days,
        "gb_limit": gb,
        "used_gb": 0,
        "created_at": datetime.datetime.now()
    })
    return redirect('/')

@app.route('/admin/del_license/<key>')
def del_license(key):
    if not session.get('is_admin'): return "Yetkisiz", 403
    licenses_col.delete_one({"key": key})
    return redirect('/')

@app.route('/admin/clear_queue')
def clear_queue():
    if not session.get('is_admin'): return "Yetkisiz", 403
    queue_col.delete_many({}) # Hepsini sil
    return redirect('/')

@app.route('/admin/stop_all')
def stop_all():
    if not session.get('is_admin'): return "Yetkisiz", 403
    # Sadece durumunu HATA yapalım
    queue_col.update_many({"status": {"$in": ["SIRADA", "ISLENIYOR"]}}, {"$set": {"status": "DURDURULDU", "log": "Admin tarafından iptal edildi."}})
    return redirect('/')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
