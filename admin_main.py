import sys
import os

# Inisialisasi path pencarian modul agar modul di dalam src/ dapat diimpor langsung
base_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(base_dir, 'src')
sys.path.insert(0, src_dir)
sys.path.insert(0, os.path.join(src_dir, 'core'))
sys.path.insert(0, os.path.join(src_dir, 'auth'))
sys.path.insert(0, os.path.join(src_dir, 'ui'))

def main():
    # Jalankan GUI admin utama
    try:
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("antigravity.bersihin.admin.v1")
    except Exception:
        pass

    from admin_gui import AdminApp
    app = AdminApp()
    app.mainloop()

if __name__ == "__main__":
    main()
