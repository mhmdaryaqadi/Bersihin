import sys
import os
import ctypes

# Inisialisasi path pencarian modul agar modul di dalam src/ dapat diimpor langsung
base_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(base_dir, 'src')
sys.path.insert(0, src_dir)
sys.path.insert(0, os.path.join(src_dir, 'core'))
sys.path.insert(0, os.path.join(src_dir, 'auth'))
sys.path.insert(0, os.path.join(src_dir, 'ui'))

def is_admin():
    """Memeriksa apakah aplikasi berjalan dengan hak akses Administrator."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except:
        return False

import socket
import threading

# Global variables for single instance socket communication
app_instance = None
server_socket = None

def check_single_instance(port=49201):
    global server_socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(('127.0.0.1', port))
        s.listen(1)
        server_socket = s
        
        def listen_loop():
            while True:
                try:
                    conn, addr = s.accept()
                    data = conn.recv(1024).decode('utf-8')
                    if data == "restore":
                        global app_instance
                        if app_instance:
                            app_instance.after(0, app_instance.restore_from_tray)
                    conn.close()
                except Exception:
                    break
                    
        t = threading.Thread(target=listen_loop, daemon=True)
        t.start()
        return True
    except socket.error:
        # Another instance is running, connect and notify it to restore
        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect(('127.0.0.1', port))
            client.sendall(b"restore")
            client.close()
        except Exception:
            pass
        sys.exit(0)

def main():
    global app_instance
    
    # Check single instance using local TCP port
    check_single_instance()

    # Inisialisasi ID model pengguna agar ikon taskbar terkelompok dengan benar
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("antigravity.bersihin.cleaner.v1")
    except Exception:
        pass

    from gui import App
    start_minimized = "--startup" in sys.argv
    app = App(start_minimized=start_minimized)
    app_instance = app
    app.mainloop()

if __name__ == "__main__":
    main()
