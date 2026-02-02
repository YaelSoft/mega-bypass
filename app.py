import os
import uuid
import datetime
from flask import Flask, render_template_string, request, redirect, session, flash
from pymongo import MongoClient

app = Flask(__name__)
app.secret_key = os.urandom(24)

# ==================== AYARLAR ====================
# Render Environment kısmına MONGO_URI ve ADMIN_PASS eklemeyi unutma
MONGO_URI = os.environ.get("MONGO_URI")
ADMIN_PASS = os.environ.get("ADMIN_PASS", "admin123") # Varsayılan şifre

client = MongoClient(MONGO_URI)
db = client['mega_leech']
queue_col = db['queue']
licenses_col = db['licenses']

# ==================== HTML TASARIM (DARK & GOLD VIP) ====================
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MEGA VIP DOWNLOADER</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        body { background-color: #0f172a; color: #e2e8f0; font-family: 'Segoe UI', sans-serif; }
        .navbar { background-color: #1e293b; border-bottom: 1px solid #334155; }
        .card { background-color: #1e293b; border: 1px solid #334155; border-radius: 10px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.5); }
        .form-control { background-color: #0f172a; border: 1px solid #334155; color: #fff; }
        .form-control:focus { background-color: #0f172a; color: #fff; border-color: #3b82f6; box-shadow: 0 0 0 0.25rem rgba(59, 130, 246, 0.25); }
        .btn-primary { background-color: #3b82f6; border: none; font-weight: 600; }
        .btn-primary:hover { background-color: #2563eb; }
        .text-gold { color: #fbbf24; }
        .badge-status { padding: 6px 12px; border-radius: 6px; font-size: 0.8em; font-weight: 600; }
        .bg-sirada { background-color: #f59e0b; color: #000; }
        .bg-isleniyor { background-color: #3b82f6; color: #fff; animation: pulse 1.5s infinite; }
        .bg-tamamlandi { background-color: #10b981; color: #fff; }
        .bg-hata { background-color: #ef4444; color: #fff; }
        @keyframes pulse { 0% { opacity: 1; } 50% { opacity: 0.7; } 100% { opacity: 1; } }
        .table-dark { background-color: #1e293b; }
        .table-dark td, .table-dark th { border-color: #334155; }
    </style>
</head>
<body>

<nav class="navbar navbar-expand-lg navbar-dark mb-4 py-3">
  <div class="container">
    <a class="navbar-brand fw-bold" href="#"><i class="fas fa-bolt text-gold"></i> MEGA <span class="text-gold">VIP</span></a>
    <div class="d-flex align-items-center">
        {% if session.get('is_admin') %}
            <span class="badge bg-danger me-3">YÖNETİCİ</span>
            <a href="/logout" class="btn btn-sm btn-outline-danger">Çıkış</a>
        {% elif session.get('license_key') %}
            <div class="me-3 text-end lh-1">
                <small class="d-block text-muted">Lisans</small>
                <span class="fw-bold text-gold">{{ session['license_key'] }}</span>
            </div>
            <a href="/logout" class="btn btn-sm btn-outline-secondary">Çıkış</a>
        {% endif %}
    </div>
  </div>
</nav>

<div class="container">
    {% for category, message in get_flashed_messages(with_categories=true) %}
      <div class="alert alert-{{ category }} alert-dismissible fade show" role="alert">
        {{ message }}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
      </div>
    {% endfor %}

    {% if not session.get('license_key') and not session.get('is_admin') %}
    <div class="row justify-content-center mt-5">
        <div class="col-md-5">
            <div class="card p-4">
                <div class="text-center mb-4">
                    <i class="fas fa-user-lock fa-3x text-gold mb-3"></i>
                    <h3>Giriş Yapın</h3>
                    <p class="text-muted">Lisans anahtarınız veya yönetici şifreniz</p>
                </div>
                <form method="POST" action="/login">
                    <div class="mb-3">
                        <input type="text" name="auth_key" class="form-control form-control-lg text-center" placeholder="XXXX-XXXX-XXXX" required>
                    </div>
                    <button type="submit" class="btn btn-primary w-100 btn-lg">Sisteme Gir</button>
                </form>
            </div>
        </div>
    </div>

    {% else %}
    
    <div class="row">
        <div class="col-lg-4 mb-4">
            <div class="card p-4 h-100">
                <h5 class="card-title mb-4"><i class="fas fa-plus-circle text-primary"></i> Yeni İndirme</h5>
                <form method="POST" action="/add_task">
                    <div class="mb-3">
                        <label class="form-label text-muted">Mega.nz Linki</label>
                        <input type="text" name="link" class="form-control" placeholder="https://mega.nz/..." required>
                    </div>
                    <button type="submit" class="btn btn-primary w-100"><i class="fas fa-cloud-download-alt"></i> Başlat</button>
                </form>

                {% if not session.get('is_admin') and license_info %}
                <hr class="my-4 border-secondary">
                <div class="d-flex justify-content-between mb-2">
                    <span>Kalan Gün:</span>
                    <span class="fw-bold">{{ license_info.days_left }}</span>
                </div>
                <div class="d-flex justify-content-between mb-2">
                    <span>Kota:</span>
                    <span class="fw-bold">{{ license_info.used_gb }} / {{ license_info.gb_limit }} GB</span>
                </div>
                <div class="progress bg-dark" style="height: 6px;">
                    <div class="progress-bar bg-warning" role="progressbar" style="width: {{ (license_info.used_gb / license_info.gb_limit) * 100 }}%"></div>
                </div>
                {% endif %}
            </div>
        </div>

        <div class="col-lg-8">
            <div class="card p-4">
                <div class="d-flex justify-content-between align-items-center mb-4">
                    <h5 class="card-title m-0"><i class="fas fa-list text-primary"></i> İşlem Listesi</h5>
                    <a href="/" class="btn btn-sm btn-outline-light"><i class="fas fa-sync"></i></a>
                </div>
                
                <div class="table-responsive">
                    <table class="table table-dark table-hover align-middle">
                        <thead>
                            <tr class="text-muted small text-uppercase">
                                <th>Durum</th>
                                <th>Bilgi</th>
                                <th class="text-end">İşlem</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for task in tasks %}
                            <tr>
                                <td style="width: 120px;">
                                    <span class="badge-status bg-{{ task.status|lower }}">{{ task.status }}</span>
                                </td>
                                <td>
                                    <div class="small text-muted">{{ task.task_id[:8] }}</div>
                                    <div>{{ task.log }}</div>
                                </td>
                                <td class="text-end">
                                    {% if task.status == 'TAMAMLANDI' and task.result.url %}
                                        <a href="{{ task.result.url }}" target="_blank" class="btn btn-sm btn-success fw-bold">
                                            <i class="fas fa-download"></i> İNDİR
                                        </a>
                                    {% endif %}
                                </td>
                            </tr>
                            {% else %}
                            <tr><td colspan="3" class="text-center text-muted py-4">Henüz işlem yok.</td></tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>

    {% if session.get('is_admin') %}
    <div class="row mt-4">
        <div class="col-12">
            <div class="card p-4 border-danger">
                <h5 class="text-danger mb-3"><i class="fas fa-shield-alt"></i> Yönetici Paneli</h5>
                <div class="row g-3">
                    <div class="col-md-4">
                        <form method="POST" action="/admin/create_license" class="p-3 bg-dark rounded">
                            <h6>Lisans Üret</h6>
                            <div class="input-group mb-2">
                                <input type="number" name="days" class="form-control" placeholder="Gün" value="30">
                                <input type="number" name="gb" class="form-control" placeholder="GB" value="50">
                            </div>
                            <button class="btn btn-sm btn-danger w-100">Oluştur</button>
                        </form>
                    </div>
                    <div class="col-md-8">
                        <h6>Aktif Lisanslar</h6>
                        <div style="max-height: 150px; overflow-y: auto;">
                            <table class="table table-sm table-dark">
                                {% for lic in all_licenses %}
                                <tr>
                                    <td><code class="text-gold">{{ lic.key }}</code></td>
                                    <td>{{ lic.days }} Gün</td>
                                    <td>{{ lic.used_gb }}/{{ lic.gb_limit }} GB</td>
                                    <td class="text-end"><a href="/admin/delete/{{ lic.key }}" class="text-danger">&times;</a></td>
                                </tr>
                                {% endfor %}
                            </table>
                        </div>
                    </div>
                    <div class="col-12 mt-2">
                         <a href="/admin/clear_queue" class="btn btn-sm btn-outline-warning">Kuyruğu Temizle</a>
                    </div>
                </div>
            </div>
        </div>
    </div>
    {% endif %}

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
    filter_query = {}
    if not session.get('is_admin'):
        filter_query["owner"] = session['license_key'] # Sadece kendi dosyaları
        
    tasks = list(queue_col.find(filter_query).sort('_id', -1).limit(20))
    
    license_info = None
    all_licenses = []
    
    if session.get('is_admin'):
        all_licenses = list(licenses_col.find())
    else:
        lic = licenses_col.find_one({"key": session['license_key']})
        if lic:
            days_passed = (datetime.datetime.now() - lic['created_at']).days
            license_info = {
                "days_left": max(0, lic['days'] - days_passed),
                "used_gb": lic.get('used_gb', 0),
                "gb_limit": lic.get('gb_limit', 0)
            }

    return render_template_string(HTML_TEMPLATE, tasks=tasks, license_info=license_info, all_licenses=all_licenses)

@app.route('/login', methods=['POST'])
def login():
    key = request.form.get('auth_key')
    if key == ADMIN_PASS:
        session['is_admin'] = True
        return redirect('/')
    
    lic = licenses_col.find_one({"key": key})
    if lic:
        session['license_key'] = key
        return redirect('/')
    
    flash("Geçersiz Anahtar!", "danger")
    return redirect('/')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

@app.route('/add_task', methods=['POST'])
def add_task():
    if not session.get('license_key') and not session.get('is_admin'): return redirect('/')
    
    link = request.form.get('link')
    
    # Lisans Kontrolü
    if not session.get('is_admin'):
        lic = licenses_col.find_one({"key": session['license_key']})
        if lic['used_gb'] >= lic['gb_limit']:
            flash("Kota Doldu!", "danger")
            return redirect('/')

    # Görevi Kuyruğa Ekle
    task_id = str(uuid.uuid4())
    queue_col.insert_one({
        "task_id": task_id,
        "link": link,
        "status": "SIRADA",
        "log": "Sunucu bekleniyor...",
        "result": {},
        "owner": session.get('license_key', 'admin'),
        "created_at": datetime.datetime.now()
    })
    
    # Kotadan düş (Tahmini)
    if not session.get('is_admin'):
        licenses_col.update_one({"key": session['license_key']}, {"$inc": {"used_gb": 1}})
        
    return redirect('/')

# Admin İşlemleri
@app.route('/admin/create_license', methods=['POST'])
def create_lic():
    if not session.get('is_admin'): return "403", 403
    key = str(uuid.uuid4())[:12].upper()
    licenses_col.insert_one({
        "key": key,
        "days": int(request.form.get('days')),
        "gb_limit": int(request.form.get('gb')),
        "used_gb": 0,
        "created_at": datetime.datetime.now()
    })
    return redirect('/')

@app.route('/admin/delete/<key>')
def del_lic(key):
    if not session.get('is_admin'): return "403", 403
    licenses_col.delete_one({"key": key})
    return redirect('/')

@app.route('/admin/clear_queue')
def clear_queue():
    if not session.get('is_admin'): return "403", 403
    queue_col.delete_many({})
    return redirect('/')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
