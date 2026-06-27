import os
import subprocess
import shutil
import sys

def build_setup():
    print("=== Memulai Proses Kompilasi Installer Bersihin ===")
    
    python_exe = os.path.join(".venv", "Scripts", "python.exe")
    if not os.path.exists(python_exe):
        print(f"Error: Virtual environment tidak ditemukan di {python_exe}!")
        sys.exit(1)
        
    # Pastikan folder Bersihin sudah dikompilasi
    if not os.path.exists("Bersihin") or not os.path.exists(os.path.join("Bersihin", "Bersihin.exe")):
        print("Error: Aplikasi Bersihin belum dikompilasi! Silakan jalankan build_exe.py terlebih dahulu.")
        sys.exit(1)
        
    cmd = [
        python_exe, "-m", "PyInstaller",
        "--noconfirm",
        "--onefile",
        "--windowed",
        "--name=BersihinSetup",
        "--icon=assets/logo.ico",
        "--add-data=Bersihin;Bersihin",
        "--paths=src",
        "--collect-all=customtkinter",
        "installer.py"
    ]
    
    print(f"Menjalankan perintah: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, check=True)
        if result.returncode == 0:
            print("\n=== Kompilasi Installer Berhasil! ===")
            
            dist_exe = os.path.join("dist", "BersihinSetup.exe")
            target_exe = "BersihinSetup.exe"
            
            if os.path.exists(dist_exe):
                print(f"Menyalin {dist_exe} ke folder root project...")
                shutil.copy2(dist_exe, target_exe)
                print(f"Sukses! File installer Anda sekarang berada di: {os.path.abspath(target_exe)}")
                
                # Pembersihan folder temporary build
                print("\nMembersihkan folder temporary build...")
                if os.path.exists("build"):
                    shutil.rmtree("build")
                if os.path.exists("BersihinSetup.spec"):
                    os.remove("BersihinSetup.spec")
                print("Pembersihan selesai.")
                print("\nInstaller siap digunakan! Silakan jalankan BersihinSetup.exe.")
            else:
                print("Error: File installer tidak ditemukan di folder dist setelah kompilasi!")
        else:
            print(f"Error: Kompilasi gagal dengan kode keluar {result.returncode}")
    except subprocess.CalledProcessError as e:
        print(f"\nTerjadi kesalahan saat menjalankan PyInstaller: {e}")
    except Exception as e:
        print(f"\nTerjadi kesalahan tidak terduga: {e}")

if __name__ == "__main__":
    build_setup()
