import os
import subprocess
import shutil
import sys

def build():
    print("=== Memulai Proses Kompilasi Antigravity Cleaner ===")
    
    # Menentukan path ke executable python di virtual environment
    python_exe = os.path.join(".venv", "Scripts", "python.exe")
    if not os.path.exists(python_exe):
        print(f"Error: Virtual environment tidak ditemukan di {python_exe}!")
        print("Silakan jalankan inisialisasi venv terlebih dahulu.")
        sys.exit(1)
        
    cmd = [
        python_exe, "-m", "PyInstaller",
        "--noconfirm",
        "--onefile",
        "--windowed",
        "--name=Bersihin",
        "--uac-admin",
        "--icon=assets/logo.ico",
        "--add-data=assets/logo.ico;assets",
        "--add-data=assets/logo.png;assets",
        "--paths=src",
        "--collect-all=customtkinter",
        "main.py"
    ]
    
    print(f"Menjalankan perintah: {' '.join(cmd)}")
    
    try:
        # Jalankan proses kompilasi
        result = subprocess.run(cmd, check=True)
        if result.returncode == 0:
            print("\n=== Kompilasi Berhasil! ===")
            
            # Cari file .exe yang dihasilkan di folder dist
            dist_exe = os.path.join("dist", "Bersihin.exe")
            target_exe = "Bersihin.exe"
            
            if os.path.exists(dist_exe):
                print(f"Menyalin {dist_exe} ke folder root project...")
                shutil.copy2(dist_exe, target_exe)
                print(f"Sukses! File executable Anda sekarang berada di: {os.path.abspath(target_exe)}")
                
                # Pembersihan folder temporary build untuk merapikan workspace
                print("\nMembersihkan folder temporary build...")
                if os.path.exists("build"):
                    shutil.rmtree("build")
                if os.path.exists("Bersihin.spec"):
                    os.remove("Bersihin.spec")
                # Hapus exe lama jika ada
                if os.path.exists("AntigravityCleaner.exe"):
                    try:
                        os.remove("AntigravityCleaner.exe")
                    except:
                        pass
                print("Pembersihan selesai.")
                print("\nAplikasi siap digunakan! Silakan jalankan Bersihin.exe.")
            else:
                print("Error: File .exe tidak ditemukan di folder dist setelah kompilasi!")
        else:
            print(f"Error: Kompilasi gagal dengan kode keluar {result.returncode}")
    except subprocess.CalledProcessError as e:
        print(f"\nTerjadi kesalahan saat menjalankan PyInstaller: {e}")
    except Exception as e:
        print(f"\nTerjadi kesalahan tidak terduga: {e}")

if __name__ == "__main__":
    build()
