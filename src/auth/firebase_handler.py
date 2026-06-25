import os
import sys
import json
import time
import urllib.request
import urllib.error
import platform
import psutil
import http.server
import urllib.parse
import webbrowser
import threading
import firebase_config

# File database lokal untuk mode simulasi
LOCAL_DB_FILE = "local_db.json"

def is_mock_mode():
    """Mendeteksi apakah konfigurasi Firebase belum diisi."""
    return (
        firebase_config.API_KEY == "MASUKKAN_API_KEY_FIREBASE_ANDA" or
        "MASUKKAN_PROJECT_ID" in firebase_config.DATABASE_URL
    )

def _get_local_db():
    """Membaca database simulasi lokal."""
    if not os.path.exists(LOCAL_DB_FILE):
        # Default database
        default_db = {
            "users": {
                "admin123": {
                    "username": "admin",
                    "email": "admin@bersihin.com",
                    "role": "admin",
                    "status": "active",
                    "computer_name": "ADMIN-PC",
                    "os": "Windows-11",
                    "ram_total": 16 * (1024**3),
                    "ram_cleaned_mb": 1520,
                    "disk_cleaned_mb": 4200,
                    "last_active": time.time(),
                    "password_hash": "admin123" # Simulasi sandi sederhana
                }
            }
        }
        _save_local_db(default_db)
        return default_db
        
    try:
        with open(LOCAL_DB_FILE, 'r') as f:
            return json.load(f)
    except Exception:
        return {"users": {}}

def _save_local_db(data):
    """Menyimpan database simulasi lokal."""
    try:
        with open(LOCAL_DB_FILE, 'w') as f:
            json.dump(data, f, indent=4)
        return True
    except Exception:
        return False

def _make_rest_call(url, data=None, method='POST'):
    """Melakukan panggilan REST API menggunakan urllib bawaan."""
    req = urllib.request.Request(url, method=method)
    req.add_header('Content-Type', 'application/json')
    
    json_data = json.dumps(data).encode('utf-8') if data is not None else None
    
    try:
        with urllib.request.urlopen(req, data=json_data, timeout=8) as response:
            res_body = response.read().decode('utf-8')
            return json.loads(res_body) if res_body else {}, None
    except urllib.error.HTTPError as e:
        try:
            err_body = e.read().decode('utf-8')
            err_json = json.loads(err_body)
            # Dapatkan pesan error dari Firebase
            msg = err_json.get('error', {}).get('message', str(e))
            return None, msg
        except:
            return None, str(e)
    except Exception as e:
        return None, f"Koneksi gagal: {e}"

def register_user(email, password, username):
    """Mendaftarkan user baru."""
    email = email.strip().lower()
    if not email or not password or not username:
        return False, "Data pendaftaran tidak boleh kosong."
        
    if is_mock_mode():
        db = _get_local_db()
        # Periksa apakah email sudah terdaftar
        for uid, uinfo in db['users'].items():
            if uinfo['email'] == email:
                return False, "Email sudah terdaftar (Lokal)."
                
        # Buat UID baru
        new_uid = f"user_{int(time.time())}"
        db['users'][new_uid] = {
            "username": username,
            "email": email,
            "role": "admin" if email == "admin@bersihin.com" else "user", # admin@bersihin.com otomatis admin
            "status": "active",
            "computer_name": os.environ.get('COMPUTERNAME', 'Unknown-PC'),
            "os": f"{platform.system()}-{platform.release()}",
            "ram_total": psutil.virtual_memory().total,
            "ram_cleaned_mb": 0,
            "disk_cleaned_mb": 0,
            "last_active": time.time(),
            "password_hash": password # Hash simulasi
        }
        _save_local_db(db)
        return True, "Registrasi Sukses (Simulasi Lokal)."

    else:
        # Firebase Auth Sign Up
        auth_url = f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={firebase_config.API_KEY}"
        payload = {
            "email": email,
            "password": password,
            "returnSecureToken": True
        }
        res, err = _make_rest_call(auth_url, payload, 'POST')
        if err:
            # Terjemahkan pesan error umum
            if "EMAIL_EXISTS" in err:
                return False, "Email sudah terdaftar di database."
            elif "WEAK_PASSWORD" in err:
                return False, "Kata sandi terlalu lemah (minimal 6 karakter)."
            return False, f"Registrasi Firebase gagal: {err}"
            
        uid = res['localId']
        id_token = res['idToken']
        
        # Buat profil di Realtime Database
        profile_url = f"{firebase_config.DATABASE_URL.rstrip('/')}/users/{uid}.json?auth={id_token}"
        profile = {
            "username": username,
            "email": email,
            "role": "admin" if email == "admin@bersihin.com" else "user",
            "status": "active",
            "computer_name": os.environ.get('COMPUTERNAME', 'Unknown-PC'),
            "os": f"{platform.system()}-{platform.release()}",
            "ram_total": psutil.virtual_memory().total,
            "ram_cleaned_mb": 0,
            "disk_cleaned_mb": 0,
            "last_active": time.time()
        }
        _, db_err = _make_rest_call(profile_url, profile, 'PUT')
        if db_err:
            return False, f"Registrasi sukses tetapi gagal menyimpan profil: {db_err}"
            
        return True, "Registrasi Berhasil!"

def login_user(email, password):
    """Melakukan proses login."""
    email = email.strip().lower()
    if not email or not password:
        return None, "Email dan password tidak boleh kosong."
        
    if is_mock_mode():
        db = _get_local_db()
        for uid, uinfo in db['users'].items():
            if uinfo['email'] == email and uinfo['password_hash'] == password:
                if uinfo['status'] == 'blocked':
                    return None, "Akun Anda telah dinonaktifkan oleh Administrator (Lokal)."
                
                # Kembalikan profile
                return {
                    "uid": uid,
                    "username": uinfo['username'],
                    "email": uinfo['email'],
                    "role": uinfo['role'],
                    "status": uinfo['status'],
                    "idToken": "local_token_123"
                }, None
        return None, "Email atau kata sandi salah (Lokal)."
        
    else:
        # Firebase Auth Sign In
        auth_url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={firebase_config.API_KEY}"
        payload = {
            "email": email,
            "password": password,
            "returnSecureToken": True
        }
        res, err = _make_rest_call(auth_url, payload, 'POST')
        if err:
            if "EMAIL_NOT_FOUND" in err or "INVALID_PASSWORD" in err:
                return None, "Email atau kata sandi salah."
            elif "USER_DISABLED" in err:
                return None, "Akun Anda telah dinonaktifkan."
            return None, f"Login gagal: {err}"
            
        uid = res['localId']
        id_token = res['idToken']
        
        # Ambil profil dari database
        profile_url = f"{firebase_config.DATABASE_URL.rstrip('/')}/users/{uid}.json?auth={id_token}"
        profile, db_err = _make_rest_call(profile_url, method='GET')
        if db_err or not profile:
            return None, "Gagal mengambil data profil dari database."
            
        if profile.get('status') == 'blocked':
            return None, "Akun Anda telah dinonaktifkan oleh Administrator."
            
        profile['uid'] = uid
        profile['idToken'] = id_token
        return profile, None

def check_blocked_status(uid, id_token):
    """Memeriksa apakah user saat ini diblokir secara real-time."""
    if is_mock_mode():
        db = _get_local_db()
        uinfo = db['users'].get(uid)
        if uinfo and uinfo['status'] == 'blocked':
            return True
        return False
    else:
        profile_url = f"{firebase_config.DATABASE_URL.rstrip('/')}/users/{uid}/status.json?auth={id_token}"
        status, err = _make_rest_call(profile_url, method='GET')
        if not err and status == 'blocked':
            return True
        return False

def report_stats(uid, id_token, freed_ram_mb, freed_disk_mb):
    """Melaporkan statistik performa pembersihan ke Firebase."""
    if is_mock_mode():
        db = _get_local_db()
        uinfo = db['users'].get(uid)
        if uinfo:
            uinfo['ram_cleaned_mb'] = uinfo.get('ram_cleaned_mb', 0) + freed_ram_mb
            uinfo['disk_cleaned_mb'] = uinfo.get('disk_cleaned_mb', 0) + freed_disk_mb
            uinfo['last_active'] = time.time()
            # Update info dinamis
            uinfo['computer_name'] = os.environ.get('COMPUTERNAME', 'Unknown-PC')
            uinfo['os'] = f"{platform.system()}-{platform.release()}"
            _save_local_db(db)
        return True
    else:
        # Ambil data statistik lama dulu
        profile_url = f"{firebase_config.DATABASE_URL.rstrip('/')}/users/{uid}.json?auth={id_token}"
        profile, err = _make_rest_call(profile_url, method='GET')
        if err or not profile:
            return False
            
        old_ram = profile.get('ram_cleaned_mb', 0)
        old_disk = profile.get('disk_cleaned_mb', 0)
        
        # Kirim update PATCH
        update_data = {
            "ram_cleaned_mb": old_ram + freed_ram_mb,
            "disk_cleaned_mb": old_disk + freed_disk_mb,
            "last_active": time.time(),
            "computer_name": os.environ.get('COMPUTERNAME', 'Unknown-PC'),
            "os": f"{platform.system()}-{platform.release()}"
        }
        _, patch_err = _make_rest_call(profile_url, update_data, 'PATCH')
        return patch_err is None

def get_all_users_data(id_token):
    """Mengunduh seluruh daftar user (khusus Admin)."""
    if is_mock_mode():
        db = _get_local_db()
        # Kembalikan dengan format mirip Firebase {uid: data}
        return db['users'], None
    else:
        url = f"{firebase_config.DATABASE_URL.rstrip('/')}/users.json?auth={id_token}"
        users, err = _make_rest_call(url, method='GET')
        return users, err

def update_user_status_by_admin(admin_token, target_uid, new_status):
    """Mengubah status aktif/blokir user oleh Admin."""
    if is_mock_mode():
        db = _get_local_db()
        uinfo = db['users'].get(target_uid)
        if uinfo:
            uinfo['status'] = new_status
            _save_local_db(db)
            return True
        return False
    else:
        url = f"{firebase_config.DATABASE_URL.rstrip('/')}/users/{target_uid}/status.json?auth={admin_token}"
        _, err = _make_rest_call(url, new_status, 'PUT')
        return err is None

def update_user_role_by_admin(admin_token, target_uid, new_role):
    """Mengubah peran user (admin/user) oleh Admin."""
    if is_mock_mode():
        db = _get_local_db()
        uinfo = db['users'].get(target_uid)
        if uinfo:
            uinfo['role'] = new_role
            _save_local_db(db)
            return True
        return False
    else:
        url = f"{firebase_config.DATABASE_URL.rstrip('/')}/users/{target_uid}/role.json?auth={admin_token}"
        _, err = _make_rest_call(url, new_role, 'PUT')
        return err is None

def delete_user_by_admin(admin_token, target_uid):
    """Menghapus data user oleh Admin dari database."""
    if is_mock_mode():
        db = _get_local_db()
        if target_uid in db['users']:
            del db['users'][target_uid]
            _save_local_db(db)
            return True
        return False
    else:
        url = f"{firebase_config.DATABASE_URL.rstrip('/')}/users/{target_uid}.json?auth={admin_token}"
        _, err = _make_rest_call(url, method='DELETE')
        return err is None

class OAuthCallbackHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def do_GET(self):
        parsed_path = urllib.parse.urlparse(self.path)
        
        if parsed_path.path == '/':
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            
            html = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>Otentikasi Bersihin</title>
                <style>
                    body { font-family: 'Segoe UI', sans-serif; background-color: #121212; color: #fff; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
                    .card { background-color: #1e1e1e; padding: 30px; border-radius: 10px; text-align: center; max-width: 400px; box-shadow: 0 4px 15px rgba(0,0,0,0.5); }
                    h2 { color: #00E5FF; }
                    .loader { border: 4px solid #333; border-top: 4px solid #00E5FF; border-radius: 50%; width: 40px; height: 40px; animation: spin 1s linear infinite; margin: 20px auto; }
                    @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
                </style>
            </head>
            <body>
                <div class="card">
                    <h2>BERSIHIN</h2>
                    <p>Menghubungkan otentikasi Google...</p>
                    <div class="loader"></div>
                </div>
                <script>
                    if (window.location.hash) {
                        const params = new URLSearchParams(window.location.hash.substring(1));
                        const id_token = params.get('id_token');
                        if (id_token) {
                            window.location.href = '/callback?id_token=' + id_token;
                        } else {
                            window.location.href = '/error?msg=TokenNotFound';
                        }
                    } else {
                        setTimeout(() => {
                            if (!window.location.hash) {
                                window.location.href = '/error?msg=NoHashFragment';
                            }
                        }, 3000);
                    }
                </script>
            </body>
            </html>
            """
            self.wfile.write(html.encode('utf-8'))
            
        elif parsed_path.path == '/callback':
            query = urllib.parse.parse_qs(parsed_path.query)
            id_token = query.get('id_token', [None])[0]
            
            if id_token:
                self.server.received_token = id_token
                self.send_response(200)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.end_headers()
                
                html = """
                <!DOCTYPE html>
                <html>
                <head>
                    <title>Otentikasi Berhasil</title>
                    <style>
                        body { font-family: 'Segoe UI', sans-serif; background-color: #121212; color: #fff; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
                        .card { background-color: #1e1e1e; padding: 30px; border-radius: 10px; text-align: center; max-width: 400px; box-shadow: 0 4px 15px rgba(0,0,0,0.5); }
                        h2 { color: #4E9F3D; }
                        .check { font-size: 50px; color: #4E9F3D; margin: 15px 0; }
                    </style>
                </head>
                <body>
                    <div class="card">
                        <h2>Otentikasi Berhasil!</h2>
                        <div class="check">✓</div>
                        <p>Login Google sukses. Silakan tutup jendela ini dan kembali ke aplikasi Bersihin.</p>
                    </div>
                </body>
                </html>
                """
                self.wfile.write(html.encode('utf-8'))
            else:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"Token tidak ditemukan.")
                
        elif parsed_path.path == '/error':
            query = urllib.parse.parse_qs(parsed_path.query)
            msg = query.get('msg', ['Unknown'])[0]
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            
            html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Otentikasi Gagal</title>
                <style>
                    body {{ font-family: 'Segoe UI', sans-serif; background-color: #121212; color: #fff; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }}
                    .card {{ background-color: #1e1e1e; padding: 30px; border-radius: 10px; text-align: center; max-width: 400px; box-shadow: 0 4px 15px rgba(0,0,0,0.5); }}
                    h2 {{ color: #FF2E93; }}
                </style>
            </head>
            <body>
                <div class="card">
                    <h2>Otentikasi Gagal</h2>
                    <p>Error: {msg}</p>
                </div>
            </body>
            </html>
            """
            self.wfile.write(html.encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

def login_user_with_google(on_status_update=None):
    """Melakukan alur masuk dengan Google secara lengkap."""
    if is_mock_mode():
        if on_status_update:
            on_status_update("Mode Simulasi: Menunggu pilihan akun...")
        return None, "MOCK_MODE"

    port = 12124
    if on_status_update:
        on_status_update("Memulai server otentikasi lokal...")
        
    try:
        server = http.server.HTTPServer(('localhost', port), OAuthCallbackHandler)
        server.received_token = None
        server.timeout = 1
    except Exception as e:
        return None, f"Gagal menjalankan server lokal pada port {port}: {e}"

    is_running = True
    def serve():
        while is_running and server.received_token is None:
            server.handle_request()
    
    server_thread = threading.Thread(target=serve, daemon=True)
    server_thread.start()

    if on_status_update:
        on_status_update("Membuka browser untuk login Google...")
        
    client_id = firebase_config.GOOGLE_CLIENT_ID
    auth_url = (
        "https://accounts.google.com/o/oauth2/v2/auth?"
        f"client_id={client_id}&"
        "redirect_uri=http://localhost:12124&"
        "response_type=id_token&"
        "scope=openid%20email%20profile&"
        "nonce=bersihin_nonce_" + str(int(time.time()))
    )
    
    try:
        webbrowser.open(auth_url)
    except Exception as e:
        is_running = False
        server.server_close()
        return None, f"Gagal membuka web browser: {e}"

    start_time = time.time()
    max_wait = 120
    
    while server.received_token is None:
        elapsed = time.time() - start_time
        if elapsed > max_wait:
            break
        if on_status_update:
            on_status_update(f"Menunggu otentikasi browser ({int(max_wait - elapsed)}s)...")
        time.sleep(0.5)

    is_running = False
    received_id_token = server.received_token
    server.server_close()

    if not received_id_token:
        return None, "Otentikasi Google dibatalkan atau habis waktu."

    if on_status_update:
        on_status_update("Memverifikasi dengan Firebase...")
        
    auth_url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithIdp?key={firebase_config.API_KEY}"
    payload = {
        "postBody": f"id_token={received_id_token}&providerId=google.com",
        "requestUri": "http://localhost",
        "returnIdSecureToken": True,
        "returnSecureToken": True
    }
    
    res, err = _make_rest_call(auth_url, payload, 'POST')
    if err:
        return None, f"Verifikasi Firebase gagal: {err}"

    uid = res.get('localId')
    id_token = res.get('idToken')
    email = res.get('email', '').lower()
    display_name = res.get('displayName', 'Google User')

    if not uid or not id_token:
        return None, "Respon verifikasi Firebase tidak lengkap."

    if on_status_update:
        on_status_update("Sinkronisasi profil database...")
        
    profile_url = f"{firebase_config.DATABASE_URL.rstrip('/')}/users/{uid}.json?auth={id_token}"
    profile, db_err = _make_rest_call(profile_url, method='GET')
    
    if db_err:
        return None, f"Gagal mengambil profil database: {db_err}"

    if not profile:
        profile = {
            "username": display_name,
            "email": email,
            "role": "admin" if email in ["admin@bersihin.com", "muhammadaryaalqadi@gmail.com"] else "user",
            "status": "active",
            "computer_name": os.environ.get('COMPUTERNAME', 'Unknown-PC'),
            "os": f"{platform.system()}-{platform.release()}",
            "ram_total": psutil.virtual_memory().total,
            "ram_cleaned_mb": 0,
            "disk_cleaned_mb": 0,
            "last_active": time.time()
        }
        _, put_err = _make_rest_call(profile_url, profile, 'PUT')
        if put_err:
            return None, f"Gagal menyimpan profil pengguna baru: {put_err}"
    else:
        # Jika profil sudah ada tetapi terdaftar sebagai user, otomatis naikkan ke admin jika email masuk whitelist
        if email in ["admin@bersihin.com", "muhammadaryaalqadi@gmail.com"] and profile.get('role') != 'admin':
            profile['role'] = 'admin'
            _make_rest_call(profile_url, {"role": "admin"}, 'PATCH')
            
    if profile.get('status') == 'blocked':
        return None, "Akun Anda telah dinonaktifkan oleh Administrator."

    profile['uid'] = uid
    profile['idToken'] = id_token
    return profile, None

def login_mock_google(email, is_admin_requested=False):
    """Simulasi masuk menggunakan Akun Google dalam Mock Mode (Lokal)."""
    email = email.strip().lower()
    if not email:
        return None, "Email Google tidak boleh kosong."
        
    db = _get_local_db()
    
    target_uid = None
    for uid, uinfo in db['users'].items():
        if uinfo['email'] == email:
            target_uid = uid
            break
            
    if target_uid:
        uinfo = db['users'][target_uid]
        if uinfo['status'] == 'blocked':
            return None, "Akun Anda telah dinonaktifkan oleh Administrator (Lokal)."
            
        if email in ["admin@bersihin.com", "muhammadaryaalqadi@gmail.com"]:
            uinfo['role'] = 'admin'
            
        uinfo['last_active'] = time.time()
        _save_local_db(db)
        
        return {
            "uid": target_uid,
            "username": uinfo['username'],
            "email": uinfo['email'],
            "role": uinfo['role'],
            "status": uinfo['status'],
            "idToken": "local_token_google_123"
        }, None
    else:
        new_uid = f"google_user_{int(time.time())}"
        username = email.split('@')[0].capitalize() + " (Google)"
        role = "admin" if (email in ["admin@bersihin.com", "muhammadaryaalqadi@gmail.com"] or is_admin_requested) else "user"
        
        db['users'][new_uid] = {
            "username": username,
            "email": email,
            "role": role,
            "status": "active",
            "computer_name": os.environ.get('COMPUTERNAME', 'Unknown-PC'),
            "os": f"{platform.system()}-{platform.release()}",
            "ram_total": psutil.virtual_memory().total,
            "ram_cleaned_mb": 0,
            "disk_cleaned_mb": 0,
            "last_active": time.time(),
            "password_hash": "google_mock"
        }
        _save_local_db(db)
        
        return {
            "uid": new_uid,
            "username": username,
            "email": email,
            "role": role,
            "status": "active",
            "idToken": "local_token_google_123"
        }, None

