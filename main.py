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

def main():
    # Jika tidak berjalan sebagai administrator, minta akses admin secara otomatis
    if not is_admin():
        try:
            # Tentukan path eksekusi (Python interpreter atau file .exe hasil kompilasi)
            if getattr(sys, 'frozen', False):
                path = sys.executable
                args = " ".join(sys.argv[1:])
            else:
                path = sys.executable
                # Tambahkan script utama ke argumen jika dijalankan mentah via Python
                args = f'"{os.path.abspath(sys.argv[0])}" ' + " ".join(sys.argv[1:])
                
            # Jalankan ulang dengan hak akses 'runas' (UAC prompt)
            ctypes.windll.shell32.ShellExecuteW(None, "runas", path, args, None, 1)
            sys.exit(0)
        except Exception as e:
            # Jika user memilih 'No' atau terjadi kesalahan
            print(f"Error: Aplikasi ini membutuhkan hak akses Administrator untuk berjalan.")
            sys.exit(1)
            
    # Jika sudah memiliki akses admin, jalankan GUI utama
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("antigravity.bersihin.cleaner.v1")
    except Exception:
        pass

    from gui import App
    start_minimized = "--startup" in sys.argv
    app = App(start_minimized=start_minimized)
    app.mainloop()

if __name__ == "__main__":
    main()
