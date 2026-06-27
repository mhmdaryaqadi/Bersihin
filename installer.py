import os
import sys
import shutil
import subprocess
import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
from PIL import Image, ImageTk
import winreg
import stat

# Set dark theme
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class InstallerApp(ctk.CTk):
    def __init__(self, is_uninstall=False):
        super().__init__()
        self.is_uninstall = is_uninstall
        
        if self.is_uninstall:
            self.title("Bersihin Uninstall Wizard")
        else:
            self.title("Bersihin Setup Wizard")
            
        self.geometry("680x440")
        self.resizable(False, False)
        
        # Center the window
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width - 680) // 2
        y = (screen_height - 440) // 2
        self.geometry(f"680x440+{x}+{y}")
        
        # Determine resource path (bundled by PyInstaller)
        if getattr(sys, 'frozen', False):
            self.src_folder = os.path.join(sys._MEIPASS, "Bersihin")
            self.logo_path = os.path.join(sys._MEIPASS, "assets", "logo.png")
            self.ico_path = os.path.join(sys._MEIPASS, "assets", "logo.ico")
        else:
            self.src_folder = os.path.abspath("Bersihin")
            self.logo_path = os.path.abspath(os.path.join("assets", "logo.png"))
            self.ico_path = os.path.abspath(os.path.join("assets", "logo.ico"))
            
        # Set Windows AppUserModelID for taskbar grouping
        import ctypes
        try:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("antigravity.bersihin.setup.v1")
        except Exception:
            pass
            
        # Set window icon and taskbar icon
        if os.path.exists(self.ico_path):
            try:
                self.iconbitmap(self.ico_path)
            except Exception as e:
                print("Failed to set window icon:", e)
                
        # Default Install Path
        program_files = os.environ.get("ProgramFiles", "C:\\Program Files")
        self.install_path = os.path.join(program_files, "Bersihin")
        
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        
        # Load logo image
        self.logo_img = None
        if os.path.exists(self.logo_path):
            try:
                img = Image.open(self.logo_path)
                self.logo_img = ctk.CTkImage(light_image=img, dark_image=img, size=(64, 64))
            except Exception as e:
                print("Failed to load logo image:", e)
                
        self.draw_sidebar()
        
        if self.is_uninstall:
            self.show_uninstall_confirm()
        else:
            self.show_step_license()
        
    def draw_sidebar(self):
        # Left Sidebar Frame
        self.sidebar_frame = ctk.CTkFrame(self, width=200, corner_radius=0, fg_color="#0F172A")
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_propagate(False)
        self.sidebar_frame.grid_columnconfigure(0, weight=1)
        
        # Logo Label
        if self.logo_img:
            self.lbl_logo = ctk.CTkLabel(self.sidebar_frame, image=self.logo_img, text="")
            self.lbl_logo.grid(row=0, column=0, pady=(35, 10))
        else:
            self.lbl_logo = ctk.CTkLabel(self.sidebar_frame, text="🛡️", font=ctk.CTkFont(size=40))
            self.lbl_logo.grid(row=0, column=0, pady=(35, 10))
            
        # Branded Header
        self.lbl_brand = ctk.CTkLabel(
            self.sidebar_frame, text="BERSIHIN",
            font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold"),
            text_color="#3B82F6"
        )
        self.lbl_brand.grid(row=1, column=0, pady=(0, 5))
        
        sub_text = "Uninstall Wizard" if self.is_uninstall else "Setup Wizard"
        self.lbl_sub = ctk.CTkLabel(
            self.sidebar_frame, text=sub_text,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color="#64748B"
        )
        self.lbl_sub.grid(row=2, column=0, pady=(0, 30))
        
        # Steps container
        self.steps_container = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        self.steps_container.grid(row=3, column=0, sticky="nsew", padx=10)
        self.steps_container.grid_columnconfigure(0, weight=1)
        
    def update_sidebar_steps(self, active_step_index):
        for w in self.steps_container.winfo_children():
            w.destroy()
            
        if self.is_uninstall:
            steps = [
                "1. Konfirmasi",
                "2. Penghapusan",
                "3. Selesai"
            ]
        else:
            steps = [
                "1. Persetujuan Lisensi",
                "2. Folder & Shortcut",
                "3. Pemasangan",
                "4. Selesai"
            ]
        
        for i, step_text in enumerate(steps):
            is_active = (i == active_step_index)
            color = "#3B82F6" if is_active else "#64748B"
            font_weight = "bold" if is_active else "normal"
            
            lbl = ctk.CTkLabel(
                self.steps_container, text=step_text,
                font=ctk.CTkFont(family="Segoe UI", size=13, weight=font_weight),
                text_color=color, anchor="w"
            )
            lbl.pack(fill="x", padx=15, pady=8)
            
    # --- INSTALLATION FLOW ---
    
    def show_step_license(self):
        self.update_sidebar_steps(0)
        
        self.content_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.content_frame.grid(row=0, column=1, padx=25, pady=20, sticky="nsew")
        self.content_frame.grid_columnconfigure(0, weight=1)
        self.content_frame.grid_rowconfigure(1, weight=1)
        
        lbl_title = ctk.CTkLabel(
            self.content_frame, text="Persetujuan Lisensi Pengguna", 
            font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold"),
            text_color="#FFFFFF"
        )
        lbl_title.grid(row=0, column=0, sticky="w", pady=(0, 10))
        
        license_box = ctk.CTkTextbox(self.content_frame, fg_color="#1E1E1E", font=ctk.CTkFont(family="Segoe UI", size=11))
        license_box.grid(row=1, column=0, sticky="nsew", pady=5)
        
        license_text = (
            "PERSETUJUAN LISENSI PENGGUNA AKHIR (EULA) - BERSIHIN\n\n"
            "Harap baca ketentuan lisensi ini dengan seksama sebelum melanjutkan instalasi.\n\n"
            "1. LISENSI APLIKASI\n"
            "Aplikasi Bersihin dilisensikan secara gratis untuk penggunaan pribadi. "
            "Anda diizinkan untuk menginstal dan menggunakan aplikasi ini pada perangkat komputer Anda.\n\n"
            "2. BATASAN PENGGUNAAN\n"
            "Anda tidak diperbolehkan melakukan rekayasa balik (reverse engineering), "
            "mendistribusikan ulang tanpa izin tertulis, atau memodifikasi modul inti "
            "aplikasi ini untuk tujuan komersial.\n\n"
            "3. BATASAN TANGGUNG JAWAB\n"
            "Aplikasi ini disediakan 'sebagaimana adanya' tanpa jaminan apa pun. "
            "Pengembang tidak bertanggung jawab atas kerusakan data, crash sistem, "
            "atau kehilangan data secara tidak sengaja yang disebabkan oleh penggunaan aplikasi ini. "
            "Gunakan fitur pembersihan registry dan disk secara bijak.\n\n"
            "Dengan mengeklik 'Saya Setuju' dan melanjutkan, Anda dianggap menyetujui semua ketentuan di atas."
        )
        license_box.insert("0.0", license_text)
        license_box.configure(state="disabled")
        
        self.agree_var = tk.BooleanVar(value=False)
        self.cb_agree = ctk.CTkCheckBox(
            self.content_frame, text="Saya menyetujui seluruh ketentuan di atas",
            variable=self.agree_var, command=self.toggle_agree,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            fg_color="#3B82F6"
        )
        self.cb_agree.grid(row=2, column=0, sticky="w", pady=15)
        
        self.btn_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.btn_frame.grid(row=3, column=0, sticky="ew", pady=(5, 0))
        
        self.btn_cancel = ctk.CTkButton(
            self.btn_frame, text="Batal", width=100, height=35,
            fg_color="#333333", hover_color="#444444", text_color="#FFFFFF",
            command=self.destroy
        )
        self.btn_cancel.pack(side="left")
        
        self.btn_next = ctk.CTkButton(
            self.btn_frame, text="Lanjut", width=100, height=35,
            fg_color="#3B82F6", hover_color="#2563EB", text_color="#FFFFFF",
            command=self.show_step_options
        )
        self.btn_next.pack(side="right")
        self.btn_next.configure(state="disabled")
        
    def toggle_agree(self):
        if self.agree_var.get():
            self.btn_next.configure(state="normal")
        else:
            self.btn_next.configure(state="disabled")
            
    def show_step_options(self):
        self.content_frame.destroy()
        self.update_sidebar_steps(1)
        
        self.content_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.content_frame.grid(row=0, column=1, padx=25, pady=20, sticky="nsew")
        self.content_frame.grid_columnconfigure(0, weight=1)
        
        lbl_title = ctk.CTkLabel(
            self.content_frame, text="Pilihan Instalasi", 
            font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold"),
            text_color="#FFFFFF"
        )
        lbl_title.grid(row=0, column=0, sticky="w", pady=(0, 20))
        
        lbl_folder = ctk.CTkLabel(
            self.content_frame, text="Folder Tujuan:",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color="#CCCCCC"
        )
        lbl_folder.grid(row=1, column=0, sticky="w", pady=(5, 2))
        
        self.path_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.path_frame.grid(row=2, column=0, sticky="ew", pady=(0, 15))
        self.path_frame.grid_columnconfigure(0, weight=1)
        
        self.entry_path = ctk.CTkEntry(self.path_frame, fg_color="#1E1E1E")
        self.entry_path.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self.entry_path.insert(0, self.install_path)
        
        btn_browse = ctk.CTkButton(
            self.path_frame, text="Telusuri...", width=90,
            fg_color="#475569", hover_color="#334155",
            command=self.browse_folder
        )
        btn_browse.grid(row=0, column=1)
        
        self.shortcut_var = tk.BooleanVar(value=True)
        cb_shortcut = ctk.CTkCheckBox(
            self.content_frame, text="Tambahkan ke Desktop (Buat Shortcut)",
            variable=self.shortcut_var,
            font=ctk.CTkFont(family="Segoe UI", size=13),
            fg_color="#3B82F6"
        )
        cb_shortcut.grid(row=3, column=0, sticky="w", pady=15)
        
        self.btn_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.btn_frame.grid(row=4, column=0, sticky="ew", pady=(35, 0))
        
        btn_back = ctk.CTkButton(
            self.btn_frame, text="Kembali", width=100, height=35,
            fg_color="#333333", hover_color="#444444", text_color="#FFFFFF",
            command=self.back_to_license
        )
        btn_back.pack(side="left")
        
        btn_install = ctk.CTkButton(
            self.btn_frame, text="Pasang (Install)", width=130, height=35,
            fg_color="#3B82F6", hover_color="#2563EB", text_color="#FFFFFF",
            command=self.run_install
        )
        btn_install.pack(side="right")
        
    def browse_folder(self):
        from tkinter import filedialog
        folder = filedialog.askdirectory(title="Pilih Folder Tujuan Instalasi")
        if folder:
            if not folder.endswith("Bersihin"):
                folder = os.path.join(folder, "Bersihin")
            self.entry_path.delete(0, tk.END)
            self.entry_path.insert(0, folder)
            
    def back_to_license(self):
        self.content_frame.destroy()
        self.show_step_license()
        
    def run_install(self):
        self.install_path = self.entry_path.get().strip()
        if not self.install_path:
            messagebox.showerror("Error", "Folder tujuan tidak boleh kosong.")
            return
            
        self.content_frame.destroy()
        self.update_sidebar_steps(2)
        
        self.content_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.content_frame.grid(row=0, column=1, padx=25, pady=20, sticky="nsew")
        self.content_frame.grid_columnconfigure(0, weight=1)
        
        lbl_title = ctk.CTkLabel(
            self.content_frame, text="Memasang Bersihin...", 
            font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold"),
            text_color="#FFFFFF"
        )
        lbl_title.grid(row=0, column=0, sticky="w", pady=(0, 20))
        
        self.lbl_progress = ctk.CTkLabel(
            self.content_frame, text="Menyiapkan berkas instalasi...",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color="#CCCCCC"
        )
        self.lbl_progress.grid(row=1, column=0, sticky="w", pady=5)
        
        self.progress = ctk.CTkProgressBar(self.content_frame, progress_color="#3B82F6")
        self.progress.grid(row=2, column=0, sticky="ew", pady=15)
        self.progress.set(0)
        
        self.after(500, self.do_copy_files)
        
    def do_copy_files(self):
        try:
            self.progress.set(0.1)
            self.lbl_progress.configure(text="Menghentikan aplikasi jika sedang berjalan...")
            
            # Close running Bersihin.exe instances and any process running from the target path using psutil
            try:
                import psutil
                for proc in psutil.process_iter(['name', 'exe']):
                    try:
                        if proc.info['name'] and proc.info['name'].lower() == "bersihin.exe":
                            proc.kill()
                        elif proc.info['exe'] and self.install_path.lower() in proc.info['exe'].lower():
                            proc.kill()
                    except Exception:
                        pass
            except Exception:
                pass
                
            try:
                subprocess.run(["taskkill", "/f", "/im", "Bersihin.exe"], capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
            except Exception:
                pass
                
            import time
            time.sleep(1.5)
            
            self.progress.set(0.2)
            self.lbl_progress.configure(text="Membuat direktori tujuan...")
            os.makedirs(self.install_path, exist_ok=True)
            
            self.progress.set(0.4)
            self.lbl_progress.configure(text="Menyalin berkas program...")
            
            if not os.path.exists(self.src_folder):
                messagebox.showerror("Error", f"Folder sumber instalasi tidak ditemukan di:\n{self.src_folder}")
                self.destroy()
                return
                
            for item in os.listdir(self.src_folder):
                s = os.path.join(self.src_folder, item)
                d = os.path.join(self.install_path, item)
                if os.path.isdir(s):
                    if os.path.exists(d):
                        for root, dirs, files in os.walk(d):
                            for file in files:
                                p = os.path.join(root, file)
                                try:
                                    os.chmod(p, stat.S_IWRITE)
                                except Exception:
                                    pass
                        shutil.rmtree(d, ignore_errors=True)
                    shutil.copytree(s, d)
                else:
                    if os.path.exists(d):
                        try:
                            os.chmod(d, stat.S_IWRITE)
                        except Exception:
                            pass
                    shutil.copy2(s, d)
            
            self.progress.set(0.6)
            self.lbl_progress.configure(text="Membuat uninstaller...")
            
            # Copy installer to Uninstall.exe
            if getattr(sys, 'frozen', False):
                shutil.copy2(sys.executable, os.path.join(self.install_path, "Uninstall.exe"))
            
            self.progress.set(0.7)
            
            if self.shortcut_var.get():
                self.lbl_progress.configure(text="Membuat shortcut di Desktop...")
                self.create_desktop_shortcut()
                
            self.progress.set(0.8)
            self.lbl_progress.configure(text="Mendaftarkan ke Windows Control Panel...")
            self.register_uninstall_registry()
            
            self.progress.set(0.9)
            self.after(500, self.show_step_finished)
            
        except Exception as e:
            messagebox.showerror("Error", f"Terjadi kesalahan saat menginstal:\n{e}")
            self.destroy()
            
    def create_desktop_shortcut(self):
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        shortcut_path = os.path.join(desktop, "Bersihin.lnk")
        target_path = os.path.join(self.install_path, "Bersihin.exe")
        
        ps_command = (
            f"$s = (New-Object -ComObject WScript.Shell).CreateShortcut('{shortcut_path}'); "
            f"$s.TargetPath = '{target_path}'; "
            f"$s.WorkingDirectory = '{self.install_path}'; "
            f"$s.IconLocation = '{target_path},0'; "
            f"$s.Save();"
        )
        
        try:
            subprocess.run(["powershell", "-Command", ps_command], capture_output=True, check=True, creationflags=subprocess.CREATE_NO_WINDOW)
        except Exception as e:
            print("Failed to create shortcut:", e)
            
    def register_uninstall_registry(self):
        try:
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Uninstall\Bersihin"
            key = winreg.CreateKeyEx(winreg.HKEY_LOCAL_MACHINE, key_path, 0, winreg.KEY_WRITE | winreg.KEY_WOW64_64KEY)
            
            uninst_exe = os.path.join(self.install_path, "Uninstall.exe")
            icon_path = os.path.join(self.install_path, "assets", "logo.ico")
            
            winreg.SetValueEx(key, "DisplayName", 0, winreg.REG_SZ, "Bersihin")
            winreg.SetValueEx(key, "UninstallString", 0, winreg.REG_SZ, f'"{uninst_exe}" /uninstall')
            winreg.SetValueEx(key, "DisplayIcon", 0, winreg.REG_SZ, icon_path)
            winreg.SetValueEx(key, "Publisher", 0, winreg.REG_SZ, "Arya AL")
            winreg.SetValueEx(key, "DisplayVersion", 0, winreg.REG_SZ, "1.0.0")
            winreg.SetValueEx(key, "InstallLocation", 0, winreg.REG_SZ, self.install_path)
            winreg.SetValueEx(key, "EstimatedSize", 0, winreg.REG_DWORD, 65000) # ~65 MB
            winreg.SetValueEx(key, "NoModify", 0, winreg.REG_DWORD, 1)
            winreg.SetValueEx(key, "NoRepair", 0, winreg.REG_DWORD, 1)
            
            winreg.CloseKey(key)
        except Exception as e:
            print("Failed to register uninstall registry:", e)
            
    def show_step_finished(self):
        self.progress.set(1.0)
        self.content_frame.destroy()
        self.update_sidebar_steps(3)
        
        self.content_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.content_frame.grid(row=0, column=1, padx=25, pady=20, sticky="nsew")
        self.content_frame.grid_columnconfigure(0, weight=1)
        
        lbl_title = ctk.CTkLabel(
            self.content_frame, text="Instalasi Selesai!", 
            font=ctk.CTkFont(family="Segoe UI", size=22, weight="bold"),
            text_color="#10B981"
        )
        lbl_title.grid(row=0, column=0, sticky="w", pady=(0, 15))
        
        lbl_desc = ctk.CTkLabel(
            self.content_frame, text=f"Aplikasi Bersihin berhasil dipasang pada komputer Anda.\n\n"
                                     f"Lokasi instalasi:\n{self.install_path}",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color="#CCCCCC", justify="left"
        )
        lbl_desc.grid(row=1, column=0, sticky="w", pady=(0, 25))
        
        self.run_now_var = tk.BooleanVar(value=True)
        cb_run = ctk.CTkCheckBox(
            self.content_frame, text="Jalankan Bersihin Sekarang",
            variable=self.run_now_var,
            font=ctk.CTkFont(family="Segoe UI", size=13),
            fg_color="#3B82F6"
        )
        cb_run.grid(row=2, column=0, sticky="w", pady=10)
        
        btn_finish = ctk.CTkButton(
            self.content_frame, text="Selesai", width=120, height=35,
            fg_color="#3B82F6", hover_color="#2563EB", text_color="#FFFFFF",
            command=self.finish_installer
        )
        btn_finish.grid(row=3, column=0, sticky="e", pady=(35, 0))
        
    def finish_installer(self):
        if self.run_now_var.get():
            exe_path = os.path.join(self.install_path, "Bersihin.exe")
            try:
                os.startfile(exe_path)
            except Exception:
                pass
        self.destroy()
        
    # --- UNINSTALLATION FLOW ---
    
    def show_uninstall_confirm(self):
        self.update_sidebar_steps(0)
        
        self.content_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.content_frame.grid(row=0, column=1, padx=25, pady=20, sticky="nsew")
        self.content_frame.grid_columnconfigure(0, weight=1)
        
        lbl_title = ctk.CTkLabel(
            self.content_frame, text="Hapus Instalan Bersihin", 
            font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold"),
            text_color="#FFFFFF"
        )
        lbl_title.grid(row=0, column=0, sticky="w", pady=(0, 20))
        
        lbl_desc = ctk.CTkLabel(
            self.content_frame, text="Apakah Anda yakin ingin menghapus aplikasi Bersihin beserta seluruh komponennya dari komputer Anda?",
            font=ctk.CTkFont(family="Segoe UI", size=14),
            text_color="#CCCCCC", justify="left", wraplength=420
        )
        lbl_desc.grid(row=1, column=0, sticky="w", pady=(0, 30))
        
        self.btn_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.btn_frame.grid(row=2, column=0, sticky="ew", pady=(30, 0))
        
        self.btn_cancel = ctk.CTkButton(
            self.btn_frame, text="Batal", width=100, height=35,
            fg_color="#333333", hover_color="#444444", text_color="#FFFFFF",
            command=self.destroy
        )
        self.btn_cancel.pack(side="left")
        
        self.btn_uninstall = ctk.CTkButton(
            self.btn_frame, text="Hapus (Uninstall)", width=130, height=35,
            fg_color="#EF4444", hover_color="#DC2626", text_color="#FFFFFF",
            command=self.run_uninstall
        )
        self.btn_uninstall.pack(side="right")
        
    def run_uninstall(self):
        self.content_frame.destroy()
        self.update_sidebar_steps(1)
        
        self.content_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.content_frame.grid(row=0, column=1, padx=25, pady=20, sticky="nsew")
        self.content_frame.grid_columnconfigure(0, weight=1)
        
        lbl_title = ctk.CTkLabel(
            self.content_frame, text="Menghapus Bersihin...", 
            font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold"),
            text_color="#FFFFFF"
        )
        lbl_title.grid(row=0, column=0, sticky="w", pady=(0, 20))
        
        self.lbl_progress = ctk.CTkLabel(
            self.content_frame, text="Menyiapkan berkas penghapusan...",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color="#CCCCCC"
        )
        self.lbl_progress.grid(row=1, column=0, sticky="w", pady=5)
        
        self.progress = ctk.CTkProgressBar(self.content_frame, progress_color="#EF4444")
        self.progress.grid(row=2, column=0, sticky="ew", pady=15)
        self.progress.set(0)
        
        self.after(500, self.do_uninstall_files)
        
    def do_uninstall_files(self):
        try:
            self.progress.set(0.2)
            self.lbl_progress.configure(text="Menghentikan aplikasi...")
            
            # Close active instances
            try:
                subprocess.run(["taskkill", "/f", "/im", "Bersihin.exe"], capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
            except Exception:
                pass
                
            try:
                import psutil
                for proc in psutil.process_iter(['name', 'exe']):
                    try:
                        if proc.info['name'] and proc.info['name'].lower() == "bersihin.exe":
                            proc.kill()
                        elif proc.info['exe'] and self.install_path.lower() in proc.info['exe'].lower():
                            proc.kill()
                    except Exception:
                        pass
            except Exception:
                pass
                
            import time
            time.sleep(1.0)
            
            self.progress.set(0.4)
            self.lbl_progress.configure(text="Menghapus shortcut Desktop...")
            
            # Delete Desktop Shortcut
            desktop = os.path.join(os.path.expanduser("~"), "Desktop")
            shortcut_path = os.path.join(desktop, "Bersihin.lnk")
            if os.path.exists(shortcut_path):
                try:
                    os.remove(shortcut_path)
                except Exception:
                    pass
            
            self.progress.set(0.6)
            self.lbl_progress.configure(text="Menghapus registrasi sistem...")
            
            # Remove Registry Keys
            try:
                key_path = r"Software\Microsoft\Windows\CurrentVersion\Uninstall"
                key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path, 0, winreg.KEY_WRITE | winreg.KEY_WOW64_64KEY)
                winreg.DeleteKey(key, "Bersihin")
                winreg.CloseKey(key)
            except Exception as e:
                print("Registry deletion failed:", e)
                
            self.progress.set(0.8)
            self.lbl_progress.configure(text="Menghapus file program...")
            
            # Trigger self-deleting batch file since Uninstall.exe cannot delete itself while running
            self.trigger_self_delete()
            
            self.progress.set(1.0)
            self.after(500, self.show_uninstall_finished)
            
        except Exception as e:
            messagebox.showerror("Error", f"Terjadi kesalahan saat menghapus:\n{e}")
            self.destroy()
            
    def trigger_self_delete(self):
        import tempfile
        temp_dir = tempfile.gettempdir()
        bat_path = os.path.join(temp_dir, "uninstall_bersihin.bat")
        
        # Batch script that waits for Uninstall.exe to exit, deletes the Bersihin directory, and self-deletes
        bat_content = (
            "@echo off\n"
            ":loop\n"
            'tasklist | findstr /i "Uninstall.exe" > nul\n'
            "if %errorlevel%==0 (\n"
            "    timeout /t 1 /nobreak > nul\n"
            "    goto loop\n"
            ")\n"
            f'rmdir /s /q "{self.install_path}"\n'
            'del "%~f0"\n'
        )
        
        try:
            with open(bat_path, "w") as f:
                f.write(bat_content)
                
            # Run batch file in detached, hidden state
            subprocess.Popen([bat_path], shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
        except Exception as e:
            print("Failed to write self-delete script:", e)
            
    def show_uninstall_finished(self):
        self.content_frame.destroy()
        self.update_sidebar_steps(2)
        
        self.content_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.content_frame.grid(row=0, column=1, padx=25, pady=20, sticky="nsew")
        self.content_frame.grid_columnconfigure(0, weight=1)
        
        lbl_title = ctk.CTkLabel(
            self.content_frame, text="Penghapusan Selesai", 
            font=ctk.CTkFont(family="Segoe UI", size=22, weight="bold"),
            text_color="#10B981"
        )
        lbl_title.grid(row=0, column=0, sticky="w", pady=(0, 15))
        
        lbl_desc = ctk.CTkLabel(
            self.content_frame, text="Aplikasi Bersihin beserta seluruh datanya telah berhasil dihapus dari komputer Anda.",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color="#CCCCCC", justify="left", wraplength=420
        )
        lbl_desc.grid(row=1, column=0, sticky="w", pady=(0, 25))
        
        btn_finish = ctk.CTkButton(
            self.content_frame, text="Selesai", width=120, height=35,
            fg_color="#3B82F6", hover_color="#2563EB", text_color="#FFFFFF",
            command=self.destroy
        )
        btn_finish.grid(row=2, column=0, sticky="e", pady=(35, 0))

if __name__ == "__main__":
    is_uninstall = "/uninstall" in sys.argv or "--uninstall" in sys.argv
    app = InstallerApp(is_uninstall=is_uninstall)
    app.mainloop()
