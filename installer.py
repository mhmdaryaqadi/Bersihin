import os
import sys
import shutil
import subprocess
import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk

# Set dark theme
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class InstallerApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Bersihin Setup Wizard")
        self.geometry("600x420")
        self.resizable(False, False)
        
        # Center the window
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width - 600) // 2
        y = (screen_height - 420) // 2
        self.geometry(f"600x420+{x}+{y}")
        
        # Determine resource path (bundled by PyInstaller)
        if getattr(sys, 'frozen', False):
            self.src_folder = os.path.join(sys._MEIPASS, "Bersihin")
        else:
            self.src_folder = os.path.abspath("Bersihin")
            
        # Default Install Path: Program Files folder
        program_files = os.environ.get("ProgramFiles", "C:\\Program Files")
        self.default_install_path = os.path.join(program_files, "Bersihin")
        
        # Current step: 0 = License, 1 = Options, 2 = Installing, 3 = Finished
        self.current_step = 0
        
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        self.show_step_license()
        
    def show_step_license(self):
        # Step 0: License Agreement
        self.frame = ctk.CTkFrame(self, fg_color="transparent")
        self.frame.grid(row=0, column=0, padx=25, pady=20, sticky="nsew")
        self.frame.grid_columnconfigure(0, weight=1)
        self.frame.grid_rowconfigure(1, weight=1)
        
        # Header
        lbl_title = ctk.CTkLabel(
            self.frame, text="Persetujuan Lisensi Pengguna", 
            font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold"),
            text_color="#FFFFFF"
        )
        lbl_title.grid(row=0, column=0, sticky="w", pady=(0, 10))
        
        # License text in scrollable text
        license_box = ctk.CTkTextbox(self.frame, fg_color="#1E1E1E", font=ctk.CTkFont(family="Segoe UI", size=11))
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
        
        # Agreement checkbox
        self.agree_var = tk.BooleanVar(value=False)
        self.cb_agree = ctk.CTkCheckBox(
            self.frame, text="Saya menyetujui seluruh ketentuan di atas",
            variable=self.agree_var, command=self.toggle_agree,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            fg_color="#3B82F6"
        )
        self.cb_agree.grid(row=2, column=0, sticky="w", pady=15)
        
        # Control Buttons
        self.btn_frame = ctk.CTkFrame(self.frame, fg_color="transparent")
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
        self.frame.destroy()
        
        # Step 1: Install Path and Shortcuts Options
        self.frame = ctk.CTkFrame(self, fg_color="transparent")
        self.frame.grid(row=0, column=0, padx=25, pady=20, sticky="nsew")
        self.frame.grid_columnconfigure(0, weight=1)
        
        lbl_title = ctk.CTkLabel(
            self.frame, text="Pilihan Instalasi", 
            font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold"),
            text_color="#FFFFFF"
        )
        lbl_title.grid(row=0, column=0, sticky="w", pady=(0, 20))
        
        # Folder Destination path
        lbl_folder = ctk.CTkLabel(
            self.frame, text="Folder Tujuan:",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color="#CCCCCC"
        )
        lbl_folder.grid(row=1, column=0, sticky="w", pady=(5, 2))
        
        self.path_frame = ctk.CTkFrame(self.frame, fg_color="transparent")
        self.path_frame.grid(row=2, column=0, sticky="ew", pady=(0, 15))
        self.path_frame.grid_columnconfigure(0, weight=1)
        
        self.entry_path = ctk.CTkEntry(self.path_frame, fg_color="#1E1E1E")
        self.entry_path.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self.entry_path.insert(0, self.default_install_path)
        
        btn_browse = ctk.CTkButton(
            self.path_frame, text="Telusuri...", width=90,
            fg_color="#475569", hover_color="#334155",
            command=self.browse_folder
        )
        btn_browse.grid(row=0, column=1)
        
        # Shortcut Option (Automatically checked)
        self.shortcut_var = tk.BooleanVar(value=True)
        cb_shortcut = ctk.CTkCheckBox(
            self.frame, text="Tambahkan ke Desktop (Buat Shortcut)",
            variable=self.shortcut_var,
            font=ctk.CTkFont(family="Segoe UI", size=13),
            fg_color="#3B82F6"
        )
        cb_shortcut.grid(row=3, column=0, sticky="w", pady=15)
        
        # Control Buttons
        self.btn_frame = ctk.CTkFrame(self.frame, fg_color="transparent")
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
        self.frame.destroy()
        self.show_step_license()
        
    def run_install(self):
        self.install_path = self.entry_path.get().strip()
        if not self.install_path:
            messagebox.showerror("Error", "Folder tujuan tidak boleh kosong.")
            return
            
        self.frame.destroy()
        
        # Step 2: Installation Progress
        self.frame = ctk.CTkFrame(self, fg_color="transparent")
        self.frame.grid(row=0, column=0, padx=25, pady=20, sticky="nsew")
        self.frame.grid_columnconfigure(0, weight=1)
        
        lbl_title = ctk.CTkLabel(
            self.frame, text="Memasang Bersihin...", 
            font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold"),
            text_color="#FFFFFF"
        )
        lbl_title.grid(row=0, column=0, sticky="w", pady=(0, 20))
        
        self.lbl_progress = ctk.CTkLabel(
            self.frame, text="Menyiapkan berkas instalasi...",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color="#CCCCCC"
        )
        self.lbl_progress.grid(row=1, column=0, sticky="w", pady=5)
        
        self.progress = ctk.CTkProgressBar(self.frame, progress_color="#3B82F6")
        self.progress.grid(row=2, column=0, sticky="ew", pady=15)
        self.progress.set(0)
        
        self.after(500, self.do_copy_files)
        
    def do_copy_files(self):
        try:
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
                        shutil.rmtree(d)
                    shutil.copytree(s, d)
                else:
                    shutil.copy2(s, d)
                    
            self.progress.set(0.7)
            
            if self.shortcut_var.get():
                self.lbl_progress.configure(text="Membuat shortcut di Desktop...")
                self.create_desktop_shortcut()
                
            self.progress.set(0.9)
            
            self.after(500, self.show_step_finished)
            
        except Exception as e:
            messagebox.showerror("Error", f"Terjadi kesalahan saat menginstal:\n{e}")
            self.destroy()
            
    def create_desktop_shortcut(self):
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        shortcut_path = os.path.join(desktop, "Bersihin.lnk")
        target_path = os.path.join(self.install_path, "Bersihin.exe")
        icon_path = os.path.join(self.install_path, "assets", "logo.ico")
        
        ps_command = (
            f"$s = (New-Object -ComObject WScript.Shell).CreateShortcut('{shortcut_path}'); "
            f"$s.TargetPath = '{target_path}'; "
            f"$s.WorkingDirectory = '{self.install_path}'; "
            f"$s.IconLocation = '{icon_path}'; "
            f"$s.Save();"
        )
        
        try:
            subprocess.run(["powershell", "-Command", ps_command], capture_output=True, check=True, creationflags=subprocess.CREATE_NO_WINDOW)
        except Exception as e:
            print("Failed to create shortcut:", e)
            
    def show_step_finished(self):
        self.progress.set(1.0)
        self.frame.destroy()
        
        # Step 3: Finished Screen
        self.frame = ctk.CTkFrame(self, fg_color="transparent")
        self.frame.grid(row=0, column=0, padx=25, pady=20, sticky="nsew")
        self.frame.grid_columnconfigure(0, weight=1)
        
        lbl_title = ctk.CTkLabel(
            self.frame, text="Instalasi Selesai!", 
            font=ctk.CTkFont(family="Segoe UI", size=22, weight="bold"),
            text_color="#10B981"
        )
        lbl_title.grid(row=0, column=0, sticky="w", pady=(0, 15))
        
        lbl_desc = ctk.CTkLabel(
            self.frame, text=f"Aplikasi Bersihin berhasil dipasang pada komputer Anda.\n\n"
                             f"Lokasi instalasi:\n{self.install_path}",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color="#CCCCCC", justify="left"
        )
        lbl_desc.grid(row=1, column=0, sticky="w", pady=(0, 25))
        
        self.run_now_var = tk.BooleanVar(value=True)
        cb_run = ctk.CTkCheckBox(
            self.frame, text="Jalankan Bersihin Sekarang",
            variable=self.run_now_var,
            font=ctk.CTkFont(family="Segoe UI", size=13),
            fg_color="#3B82F6"
        )
        cb_run.grid(row=2, column=0, sticky="w", pady=10)
        
        # Finish Button
        btn_finish = ctk.CTkButton(
            self.frame, text="Selesai", width=120, height=35,
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

if __name__ == "__main__":
    app = InstallerApp()
    app.mainloop()
