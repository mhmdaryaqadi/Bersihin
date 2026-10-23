# Bersihin: Sistem Optimasi, Manajemen Memori, dan Pemeliharaan Berkas Windows Tingkat Lanjut

[![Platform](https://img.shields.io/badge/Platform-Windows%2010%20%7C%2011-0078D6?style=for-the-badge&logo=windows)](https://github.com/mhmdaryaqadi/Bersihin)
[![Python Version](https://img.shields.io/badge/Python-3.11%20%7C%203.12%20%7C%203.14-3776AB?style=for-the-badge&logo=python)](https://www.python.org/)
[![UI Framework](https://img.shields.io/badge/UI-CustomTkinter-blueviolet?style=for-the-badge)](https://github.com/TomSchimansky/CustomTkinter)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)
[![Latest Release](https://img.shields.io/badge/Release-v1.0.1-brightgreen?style=for-the-badge&logo=github)](https://github.com/mhmdaryaqadi/Bersihin/releases)

---

## 📋 Daftar Isi
1. [Ringkasan Eksekutif](#-ringkasan-eksekutif)
2. [Latar Belakang & Filosofi Rekayasa](#-latar-belakang--filosofi-rekayasa)
3. [Arsitektur Perangkat Lunak](#-arsitektur-perangkat-lunak)
4. [Dekomposisi Fungsional & Mekanisme Teknis](#-dekomposisi-fungsional--mekanisme-teknis)
   - [4.1 Rekayasa Optimasi Memori (RAM Engine)](#41-rekayasa-optimasi-memori-ram-engine)
   - [4.2 Mesin Pembersih Berkas Berjenjang (Storage Sanitization)](#42-mesin-pembersih-berkas-berjenjang-storage-sanitization)
   - [4.3 Pemindai & Perbaikan Registri Terstruktur](#43-pemindai--perbaikan-registri-terstruktur)
   - [4.4 Game Mode Booster & HUD Overlay Cerdas](#44-game-mode-booster--hud-overlay-cerdas)
   - [4.5 Uninstaller Sisa Komprehensif (Deep Clean Residuals)](#45-uninstaller-sisa-komprehensif-deep-clean-residuals)
   - [4.6 Perkakas Analisis Berkas (Deduplikasi & Ukuran Raksasa)](#46-perkakas-analisis-berkas-deduplikasi--ukuran-raksasa)
5. [Infrastruktur Komunikasi & Ketahanan Sistem](#-infrastruktur-komunikasi--ketahanan-sistem)
   - [5.1 Single-Instance Inter-Process Communication (IPC)](#51-single-instance-inter-process-communication-ipc)
   - [5.2 Arsitektur Cloud Hibrida (Firebase REST & Offline Local DB)](#52-arsitektur-cloud-hibrida-firebase-rest--offline-local-db)
6. [Struktur Direktori Proyek](#-struktur-direktori-proyek)
7. [Spesifikasi Lingkungan & Panduan Pemasangan](#-spesifikasi-lingkungan--panduan-pemasangan)
   - [7.1 Prasyarat Sistem](#71-prasyarat-sistem)
   - [7.2 Menjalankan Lingkungan Pengembangan (Development Setup)](#72-menjalankan-lingkungan-pengembangan-development-setup)
   - [7.3 Kompilasi Distribusi Biner (PyInstaller)](#73-kompilasi-distribusi-biner-pyinstaller)
8. [Aspek Keamanan, Hak Akses (UAC), & Integritas Data](#-aspek-keamanan-hak-akses-uac--integritas-data)
9. [Kontributor & Lisensi](#-kontributor--lisensi)

---

## 🔬 Ringkasan Eksekutif

**Bersihin** adalah aplikasi pemeliharaan sistem operasi Microsoft Windows berskala penuh (*end-to-end system utility*) yang dirancang untuk mengatasi fenomena *software rot*, fragmentasi alokasi RAM, penumpukan residu uninstalasi, serta degradasi latensi komputasi harian maupun *gaming*.

Berbeda dengan perkakas pembersih konvensional yang kerap mengandalkan antarmuka wrapper statis atau perangkat lunak berbayar yang penuh iklan (*bloatware*), Bersihin dibangun di atas prinsip transparansi komputasi, akses langsung ke subsistem **Win32 API/NT Kernel**, serta pemisahan tegas antara pembersihan berkas berisiko rendah (*Rekomendasi*) dan data berstatus sensitif (*Advance*). 

Dilengkapi dengan arsitektur hibrida (kompatibilitas offline penuh dan telemetri berbasis cloud Firebase), Bersihin memberikan kendali penuh kepada pengguna atas kesehatan komputer secara terukur, akurat, dan aman.

---

## 💡 Latar Belakang & Filosofi Rekayasa

Penggunaan jangka panjang sistem operasi berbasis Windows sering kali mengakibatkan:
1. **Kebocoran Working Set & Fragmentasi Standby Cache**: Alokasi RAM yang ditahan oleh proses latar belakang yang telah tidak aktif sering kali tidak segera dikembalikan ke *free pool*, menurunkan responsivitas multitasking.
2. **Pencemaran Berkas Sementara (Artifact Littering)**: Pertumbuhan eksponensial berkas di `%TEMP%`, `SoftwareDistribution\Download`, `Prefetch`, serta cache browser Chromium yang menghabiskan ruang I/O solid-state drive (SSD).
3. **Residu Registri dan Uninstalasi yang Rusak**: Installer konvensional kerap meninggalkan referensi file DLL bersama (*orphaned SharedDLLs*) dan subkey uninstaller pada `HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall`.

Filosofi rekayasa **Bersihin** didasarkan pada tiga pilar utama:
* **Native & Deterministic**: Mengutamakan fungsi pustaka dinamis Windows bawaan (`kernel32.dll`, `ntdll.dll`, `psapi.dll`, `shell32.dll`, `advapi32.dll`) via `ctypes` untuk memastikan operasi berkecepatan tinggi tanpa overhead runtime berlebih.
* **Granular Safety & Non-Destructive**: Tidak melakukan penghapusan agresif terhadap dependensi sistem yang vital; pembersihan browser dipartisi menjadi cache statis vs riwayat/cookies login.
* **Modern & Ergonomic UX**: Menghadirkan antarmuka bertema gelap (*Dark Neumorphic/Glassmorphism*) menggunakan CustomTkinter, visualisasi telemetri real-time, integrasi system tray daemon, dan global gaming HUD overlay borderless.

---

## 🏗 Arsitektur Perangkat Lunak

Secara arsitektural, sistem mengadopsi model berlapis (*Layered Architecture*) dengan pemisahan tanggung jawab (*Separation of Concerns*) yang tegas:

```
┌────────────────────────────────────────────────────────────────────────┐
│                          PRESENTATION LAYER                            │
│   ┌───────────────────────────┐      ┌─────────────────────────────┐   │
│   │    Client GUI (App)       │      │   Admin GUI (AdminApp)      │   │
│   │  - Dashboard & Telemetry  │      │  - User Management Table    │   │
│   │  - Cleaners & Optimizers  │      │  - Remote Config / Updates  │   │
│   │  - Game Overlay HUD       │      │  - System Broadcast Engine  │   │
│   └─────────────┬─────────────┘      └──────────────┬──────────────┘   │
└─────────────────┼───────────────────────────────────┼──────────────────┘
                  ▼                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│                        CORE LOGIC & SERVICES                           │
│  ┌───────────────────────┐ ┌──────────────────────┐ ┌────────────────┐ │
│  │     File Cleaner      │ │    Memory Cleaner    │ │ Premium Tools  │ │
│  │ - Scan & Clean Engine │ │ - Working Set Flush  │ │ - Registry Cln │ │
│  │ - Multi-Browser Cache │ │ - Standby List Purge │ │ - MD5 De-dup   │ │
│  │ - Shell32 Recycle Bin │ │ - Process Suspension │ │ - Large Files  │ │
│  └───────────────────────┘ └──────────────────────┘ └────────────────┘ │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│                     SUBSYSTEM & OS INTEGRATION                         │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │ Windows Native APIs (ctypes / wintypes)                          │  │
│  │  - kernel32: SetSystemFileCacheSize, OpenProcessToken, Privileges│  │
│  │  - ntdll: NtSetSystemInformation (MemoryPurgeStandbyList)        │  │
│  │  - psapi: EmptyWorkingSet                                        │  │
│  │  - shell32: SHEmptyRecycleBinW, SHQueryRecycleBinW, UAC RunAs    │  │
│  │  - user32: RegisterHotKey (Global [Insert] Hook)                 │  │
│  │  - winreg: Registry Query, Traversal & Key Deletion              │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────┐  ┌───────────────────────────────┐  │
│  │ Single-Instance IPC Engine    │  │ Data & Cloud Backend Engine   │  │
│  │  - TCP Loopback (Port 49201)  │  │  - Firebase Realtime REST API │  │
│  │  - Restore from Tray Signal   │  │  - Offline local_db.json      │  │
│  └───────────────────────────────┘  └───────────────────────────────┘  │
└────────────────────────────────────────────────────────────────────────┘
```

---

## ⚙ Dekomposisi Fungsional & Mekanisme Teknis

### 4.1 Rekayasa Optimasi Memori (RAM Engine)
Modul [`memory_cleaner.py`](file:///E:/gabut/Pembersih/src/core/memory_cleaner.py) mengimplementasikan tiga tahap pembersihan memori fisik:
1. **Emptying Process Working Sets**: Mengakses *token privilege* `SeIncreaseQuotaPrivilege` melalui `advapi32.AdjustTokenPrivileges`, kemudian melakukan iterasi proses via `OpenProcess(PROCESS_QUERY_INFORMATION | PROCESS_SET_QUOTA)` dan memanggil fungsi native `psapi.EmptyWorkingSet()`.
2. **System File Cache Flush**: Memanggil `kernel32.SetSystemFileCacheSize(SIZE_T(-1), SIZE_T(-1), 0)` untuk menginstruksikan manajer memori Windows agar mengosongkan *cache* berkas sistem yang tidak aktif.
3. **Purge Standby Memory List**: Mengeskalasi hak akses proses dengan `SeProfileSingleProcessPrivilege`, kemudian mengeksekusi panggilan sistem tidak terdokumentasi (*undocumented native call*) `ntdll.NtSetSystemInformation` dengan kode operasi `SystemMemoryListInformation` (ID 80) dan perintah `MemoryPurgeStandbyList` (ID 4).

### 4.2 Mesin Pembersih Berkas Berjenjang (Storage Sanitization)
Modul [`file_cleaner.py`](file:///E:/gabut/Pembersih/src/core/file_cleaner.py) memisahkan sanitasi berkas menjadi dua kategori risiko guna melindungi integritas data pengguna:
* **Kategori Rekomendasi (Safe / Auto-checked)**:
  * File Temp Pengguna (`%TEMP%`) dan Sistem (`%WINDIR%\Temp`).
  * Windows Prefetch Cache (`%WINDIR%\Prefetch`).
  * Windows Update Download Cache (`%WINDIR%\SoftwareDistribution\Download`).
  * Laporan Crash & Minidumps sistem.
  * Windows Recycle Bin multi-drive via `shell32.SHEmptyRecycleBinW(None, None, 7)`.
* **Kategori Tindakan Lanjutan (Advance / Opt-in)**:
  * Cache Google Chrome (`User Data\Default\Cache`, `Code Cache`).
  * Cache Microsoft Edge (`User Data\Default\Cache`, `Code Cache`).
  * Riwayat Penjelajahan, Unduhan, dan Cookies Browser (dengan penghentian proses browser otomatis sebelum sanitasi database SQLite terkait).

### 4.3 Pemindai & Perbaikan Registri Terstruktur
Dikelola di [`premium_tools.py`](file:///E:/gabut/Pembersih/src/core/premium_tools.py), algoritma ini menganalisis integritas Windows Registry tanpa merusak entri vital:
* **Invalid Uninstall Entries**: Memindai pohon registri `SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall` (baik 64-bit maupun 32-bit `Wow6432Node` pada `HKLM` dan `HKCU`). Entri diverifikasi silang dengan memeriksa keberadaan fisik `InstallLocation` dan `DisplayIcon`. Jika berkas atau folder target tidak lagi eksis, entri ditandai sebagai referensi usang (*dead reference*).
* **Orphaned Shared DLLs**: Memeriksa `SOFTWARE\Microsoft\Windows\CurrentVersion\SharedDlls` untuk mendeteksi pustaka `.dll` terdaftar yang berkas fisiknya telah terhapus dari disk.

### 4.4 Game Mode Booster & HUD Overlay Cerdas
Diintegrasikan langsung ke dalam arsitektur loop utama di [`gui.py`](file:///E:/gabut/Pembersih/src/ui/gui.py):
* **Auto-Trigger Background Scanner**: Thread latar belakang memindai proses sistem setiap 3 detik. Apabila proses game yang terdaftar (seperti `cs2.exe`, `valorant.exe`, `gta5.exe`, atau game kustom pengguna) terdeteksi aktif, sistem akan secara otomatis memicu mode boost dan membuka Game HUD Overlay. Begitu proses game diakhiri, mode boost dinonaktifkan dan jendela overlay otomatis tertutup.
* **Global Win32 Hotkey**: Menggunakan `user32.RegisterHotKey(NULL, 1, 0, VK_INSERT)` di thread terisolasi untuk menangkap penekanan tombol `[Insert]` di level kernel secara global (dapat dipanggil saat game berjalan *fullscreen*).
* **High Performance Power Plan**: Mengalihkan konfigurasi daya sistem operasi ke skema *High Performance* GUID (`8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c`) menggunakan utilitas `powercfg`.
* **Penangguhan Aplikasi Latar Belakang (*Process Suspension*)**: Membekukan sementara proses aplikasi non-esensial yang boros sumber daya (`chrome.exe`, `spotify.exe`, `discord.exe`, dll.) melalui API `psutil.Process.suspend()`, serta memulihkannya kembali via `resume()` saat mode game diakhiri.
* **Penangguhan Windows Update Service**: Menghentikan sementara service `wuauserv` (`net stop wuauserv`) untuk meniadakan latensi tak terduga akibat pengunduhan background Windows Update.
* **DNS Cache Flushing**: Menjalankan pembersihan tabel DNS resolver (`ipconfig /flushdns`) guna meminimalkan lonjakan ping (*network jitter*).
* **Manajer Game Kustom**: Antarmuka interaktif bagi pengguna untuk mendaftarkan berkas executable (`.exe`) game baru yang disimpan secara persisten di registri pengguna (`HKCU\Software\Bersihin\CustomGames`).

### 4.5 Uninstaller Sisa Komprehensif (Deep Clean Residuals)
Menyediakan fitur **Hapus Total (Advanced Uninstall)**:
1. Menjalankan uninstaller resmi aplikasi terkait (`UninstallString`).
2. Menjalankan pemindaian heuristik rekursif terhadap sisa artefak:
   * Direktori `%AppData%` dan `%LocalAppData%` sesuai nama vendor atau aplikasi.
   * Direktori `%ProgramFiles%` dan `%ProgramFiles(x86)%`.
   * Entri Registry pada node `Software` di `HKCU` dan `HKLM`.
3. Menghapus seluruh residu yang tertinggal hingga tuntas.

### 4.6 Perkakas Analisis Berkas (Deduplikasi & Ukuran Raksasa)
* **Duplicate File Finder**: Melakukan traversal berkas secara bertahap:
  1. *Grouping by Size*: Hanya berkas dengan ukuran biner identik yang diproses lebih lanjut untuk menghemat alokasi I/O.
  2. *Cryptographic Hash Checking*: Menghitung nilai hash **MD5** menggunakan pembacaan *chunk* biner 64 KB untuk mendeteksi duplikasi konten secara 100% presisi.
* **Large File Finder**: Mengidentifikasi berkas berukuran raksasa berdasarkan ambang batas (*threshold*) yang dapat dikonfigurasi (misalnya berkas > 100 MB hingga > 1 GB) untuk mempermudah pemulihan ruang penyimpanan disk secara selektif.

---

## 🔒 Infrastruktur Komunikasi & Ketahanan Sistem

### 5.1 Single-Instance Inter-Process Communication (IPC)
Untuk mencegah *race condition* pada pembersihan berkas serta pengalokasian ganda ikon system tray, Bersihin mengimplementasikan mekanisme single-instance berbasis soket TCP loopback:
* Port lokal terdedikasi: `127.0.0.1:49201`.
* Instance pertama bertindak sebagai listener server.
* Jika instance kedua dijalankan oleh pengguna, instance tersebut akan menangkap pengecualian *socket collision*, mengirimkan payload sinyal `b"restore"`, dan segera melakukan terminasi (`sys.exit(0)`).
* Instance pertama menerima sinyal dan memulihkan jendela utama dari status terminimalkan (*System Tray*) ke layar aktif.

### 5.2 Arsitektur Cloud Hibrida (Firebase REST & Offline Local DB)
Dikelola melalui [`firebase_handler.py`](file:///E:/gabut/Pembersih/src/auth/firebase_handler.py):
* **Dual-State Connectivity**: Menggunakan panggilan murni REST API HTTPS (`urllib.request`) untuk berkomunikasi dengan Google Firebase Realtime Database tanpa membebani ukuran biner dengan dependensi SDK berat.
* **Graceful Local Fallback**: Apabila koneksi internet tidak tersedia atau kuota endpoint terlampaui, sistem secara otomatis mengalihkan autentikasi dan penyimpanan status ke berkas terenkripsi lokal [`local_db.json`](file:///E:/gabut/Pembersih/local_db.json).
* **Remote Fleet Administration**: Panel administrator ([`admin_main.py`](file:///E:/gabut/Pembersih/admin_main.py)) mampu melakukan push notifikasi *broadcast*, inspeksi total telemetri pembersihan seluruh perangkat klien, serta deployment instruksi pembaruan versi secara terpusat.

---

## 📁 Struktur Direktori Proyek

```
Bersihin/
│
├── assets/                          # Aset grafis aplikasi
│   ├── logo.ico                     # Ikon aplikasi dan Windows Executable
│   └── logo.png                     # Visual logo resolusi tinggi untuk UI
│
├── src/                             # Pohon kode sumber utama
│   ├── auth/                        # Lapisan autentikasi dan komunikasi data
│   │   ├── __init__.py
│   │   ├── firebase_config.py       # Konfigurasi endpoint dan API key Firebase
│   │   └── firebase_handler.py      # Engine REST API client & offline local database
│   │
│   ├── core/                        # Engine sistem dan logika pembersihan (Win32)
│   │   ├── __init__.py
│   │   ├── file_cleaner.py          # Pembersih berkas sementara, sampah, & browser
│   │   ├── memory_cleaner.py        # Optimasi RAM, cache berkas sistem, & standby list
│   │   └── premium_tools.py         # Pemindai registri, MD5 deduplikasi, & large files
│   │
│   └── ui/                          # Lapisan antarmuka pengguna (CustomTkinter)
│       ├── __init__.py
│       ├── admin_gui.py             # Konsol antarmuka administrator
│       └── gui.py                   # Antarmuka klien utama & Game Overlay HUD
│
├── main.py                          # Titik masuk utama aplikasi pengguna (Client Entry)
├── admin_main.py                    # Titik masuk aplikasi administrator (Admin Entry)
├── installer.py                     # Skrip antarmuka wizard instalasi Windows
├── build_exe.py                     # Automasi pembungkus biner executable aplikasi utama
├── build_setup.py                   # Automasi pembungkus paket berkas setup (BersihinSetup.exe)
├── requirements.txt                 # Manifest dependensi pustaka Python
├── .gitignore                       # Berkas pengecualian Git
└── README.md                        # Dokumentasi komprehensif proyek
```

---

## 💻 Spesifikasi Lingkungan & Panduan Pemasangan

### 7.1 Prasyarat Sistem
* **Sistem Operasi**: Microsoft Windows 10 atau Windows 11 (Arsitektur 64-bit direkomendasikan).
* **Hak Akses**: Hak akses **Administrator (Elevated UAC Privileges)** diperlukan untuk manipulasi token kernel, penghapusan cache sistem, modifikasi skema daya, dan pembersihan registri `HKLM`.
* **Runtime**: Python versi 3.10, 3.11, 3.12, atau 3.14 (Direkomendasikan 3.11+).

### 7.2 Menjalankan Lingkungan Pengembangan (Development Setup)

1. **Kloning Repositori**:
   ```bash
   git clone https://github.com/mhmdaryaqadi/Bersihin.git
   cd Bersihin
   ```

2. **Inisialisasi Lingkungan Virtual (Virtual Environment)**:
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

3. **Instalasi Dependensi**:
   ```powershell
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. **Eksekusi Aplikasi**:
   * *Aplikasi Pengguna*:
     ```powershell
     python main.py
     ```
   * *Konsol Administrator*:
     ```powershell
     python admin_main.py
     ```

### 7.3 Kompilasi Distribusi Biner (PyInstaller)

Proyek ini telah menyediakan skrip automasi terpadu untuk membungkus kode sumber menjadi biner executable independen:

1. **Membangun Biner Aplikasi Utama**:
   ```powershell
   python build_exe.py
   ```
   *Skrip ini akan memanggil PyInstaller dengan parameter `--uac-admin`, membundel seluruh modul dan dependensi UI ke dalam direktori distribusi `Bersihin/`.*

2. **Membangun Berkas Installer Setup (`BersihinSetup.exe`)**:
   ```powershell
   python build_setup.py
   ```
   *Skrip ini membungkus direktori aplikasi ke dalam satu file mandiri (`--onefile`) `BersihinSetup.exe` yang memiliki kemampuan mengekstrak instalasi, membuat desktop shortcut, dan mendaftarkan aplikasi secara resmi pada Control Panel (Add/Remove Programs).*

---

## 🛡 Aspek Keamanan, Hak Akses (UAC), & Integritas Data

1. **Elevasi Hak Akses Otomatis (UAC Re-launch)**:
   Pada permulaan eksekusi, [`main.py`](file:///E:/gabut/Pembersih/main.py) memverifikasi status privilese melalui `ctypes.windll.shell32.IsUserAnAdmin()`. Apabila belum berstatus Administrator, aplikasi secara otomatis meminta eskalasi menggunakan verb `"runas"` via `ShellExecuteW`.
2. **Pengecualian Berkas Berstatus Terkunci (*Locked / In-use Handling*)**:
   Operasi pembersihan berkas pada [`file_cleaner.py`](file:///E:/gabut/Pembersih/src/core/file_cleaner.py) secara konsisten mengimplementasikan penanganan eksepsi `PermissionError` dan `OSError`. Berkas yang sedang digunakan oleh kernel atau proses sistem operasi yang vital akan diabaikan secara otomatis tanpa menghentikan rangkaian tugas pembersihan.
3. **Penyimpanan Kredensial & Sesi Terisolasi**:
   Sesi login pengguna disimpan dalam format biner terisolasi (`session.json` dan `admin_session.json`) dengan pembatasan hak baca lokal, memastikan tidak ada token sensitif yang bocor ke direktori publik.

---

## 👥 Pengembang & Lisensi

* **Pencipta & Pengembang Utama**: [Arya AL](https://github.com/mhmdaryaqadi)
* **Lisensi**: Proyek ini dilisensikan di bawah naungan [MIT License](LICENSE) — Anda diizinkan untuk memodifikasi, mendistribusikan, dan mengembangkan lebih lanjut perangkat lunak ini dengan tetap menyertakan atribusi penulis asli.

---

<div align="center">
  <sub>Dibangun dengan dedikasi untuk performa komputasi Windows yang lebih bersih, cepat, dan transparan.</sub><br>
  <b>Bersihin © 2026 Arya AL. All Rights Reserved.</b>
</div>
