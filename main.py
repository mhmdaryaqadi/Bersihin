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
    # Inisialisasi ID model pengguna agar ikon taskbar terkelompok dengan benar
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
