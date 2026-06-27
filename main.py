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

# Keep global reference to mutex to prevent garbage collection
app_mutex = None

def main():
    global app_mutex
    
    # Single Instance Check using Win32 Mutex
    MUTEX_NAME = "Global\\antigravity_bersihin_cleaner_mutex"
    try:
        app_mutex = ctypes.windll.kernel32.CreateMutexW(None, False, MUTEX_NAME)
        last_error = ctypes.windll.kernel32.GetLastError()
        if last_error == 183: # ERROR_ALREADY_EXISTS
            # Another instance is already running!
            # Find its window and restore it
            hwnd = ctypes.windll.user32.FindWindowW(None, "Bersihin")
            if hwnd:
                # SW_RESTORE = 9, SW_SHOW = 5
                ctypes.windll.user32.ShowWindow(hwnd, 9)
                ctypes.windll.user32.SetForegroundWindow(hwnd)
            sys.exit(0)
    except Exception as e:
        print("Single instance check error:", e)

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
