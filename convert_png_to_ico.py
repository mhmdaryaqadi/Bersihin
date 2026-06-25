import os
import shutil
from PIL import Image

def build_assets():
    png_source = r"C:\Users\Pongo\.gemini\antigravity-ide\brain\d9522300-b056-44a5-9290-29ecd5024520\bersihin_logo_1782393991449.png"
    png_dest = r"d:\gabut\Pembersih\logo.png"
    ico_dest = r"d:\gabut\Pembersih\logo.ico"
    
    if not os.path.exists(png_source):
        print(f"Error: Source PNG tidak ditemukan di {png_source}!")
        return
        
    try:
        # 1. Salin PNG ke folder project sebagai logo.png
        print("Menyalin PNG ke folder project...")
        shutil.copy2(png_source, png_dest)
        
        # 2. Konversi PNG ke ICO standard multi-resolusi menggunakan Pillow
        print("Mengonversi PNG ke ICO standard dengan Pillow...")
        img = Image.open(png_dest)
        # Windows merekomendasikan ukuran: 16, 32, 48, 256
        img.save(
            ico_dest, 
            format='ICO', 
            sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
        )
        print(f"Sukses! logo.png dan logo.ico berhasil dibuat di folder project.")
    except Exception as e:
        print(f"Terjadi kesalahan: {e}")

if __name__ == "__main__":
    build_assets()
