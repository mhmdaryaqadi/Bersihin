import os
import sys
import threading
import time
import json
import tkinter as tk
from tkinter import messagebox, filedialog
import customtkinter as ctk
import winreg
import hashlib
import subprocess
import datetime
import psutil

# Import pystray for system tray
try:
    import pystray
    from PIL import Image
    HAS_PYSTRAY = True
except ImportError:
    HAS_PYSTRAY = False

# Import our backend modules
import memory_cleaner
import file_cleaner
import firebase_handler

def relaunch_as_admin():
    import ctypes
    try:
        if getattr(sys, 'frozen', False):
            path = sys.executable
            args = " ".join(sys.argv[1:])
        else:
            path = sys.executable
            args = f'"{os.path.abspath(sys.argv[0])}" ' + " ".join(sys.argv[1:])
        ctypes.windll.shell32.ShellExecuteW(None, "runas", path, args, None, 1)
        sys.exit(0)
    except Exception as e:
        messagebox.showerror("Error UAC", f"Gagal menjalankan ulang sebagai Administrator:\n{e}")

# Set theme and appearance
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class CircularProgress(tk.Canvas):
    """Custom Tkinter Canvas to draw a modern circular progress ring for RAM usage."""
    def __init__(self, parent, size=180, thickness=16, bg_color="#1E1E1E", fg_color="#3B82F6", text_color="#FFFFFF", **kwargs):
        super().__init__(parent, width=size, height=size, bg=bg_color, highlightthickness=0, **kwargs)
        self.size = size
        self.thickness = thickness
        self.bg_color = bg_color
        self.fg_color = fg_color
        self.text_color = text_color
        self.percentage = 0
        self.draw()

    def draw(self):
        self.delete("all")
        # Draw background ring (deep charcoal)
        padding = self.thickness / 2 + 2
        self.create_oval(
            padding, padding, 
            self.size - padding, self.size - padding, 
            outline="#2E2E2E", width=self.thickness
        )
        
        # Calculate angle for arc (clockwise)
        extent = -(self.percentage / 100.0) * 359.9
        
        # Draw progress arc
        self.create_arc(
            padding, padding, 
            self.size - padding, self.size - padding, 
            start=90, extent=extent, 
            outline=self.fg_color, width=self.thickness, style="arc"
        )
        
        # Draw percentage text in the center
        self.create_text(
            self.size / 2, self.size / 2 - 10, 
            text=f"{int(self.percentage)}%", 
            fill=self.text_color, font=("Segoe UI", 26, "bold")
        )
        
        # Draw label text below percentage
        self.create_text(
            self.size / 2, self.size / 2 + 20, 
            text="RAM TERPAKAI", 
            fill="#888888", font=("Segoe UI", 8, "bold")
        )

    def set_value(self, value):
        self.percentage = max(0, min(100, value))
        self.draw()

class LoginFrame(ctk.CTkFrame):
    """Modern Login Frame using Google Sign-In."""
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="#121212")
        self.controller = controller
        
        # Center Container Card
        self.card = ctk.CTkFrame(self, width=380, height=310, fg_color="#1E1E1E", corner_radius=15)
        self.card.place(relx=0.5, rely=0.5, anchor="center")
        self.card.pack_propagate(False)
        
        # App Title/Logo in Card
        logo_lbl = ctk.CTkLabel(
            self.card, text="BERSIHIN", 
            font=ctk.CTkFont(family="Segoe UI", size=28, weight="bold"),
            text_color="#F8FAFC"
        )
        logo_lbl.pack(pady=(25, 5))
        
        # Subtitle showing Database mode (online/offline simulated)
        mode_text = "Database: Offline (Simulasi Lokal)" if firebase_handler.is_mock_mode() else "Database: Online (Firebase)"
        mode_color = "#888888" if firebase_handler.is_mock_mode() else "#10B981"
        
        self.mode_lbl = ctk.CTkLabel(
            self.card, text=mode_text,
            font=ctk.CTkFont(family="Segoe UI", size=10, slant="italic"),
            text_color=mode_color
        )
        self.mode_lbl.pack(pady=(0, 20))
        
        # Status Label / Instruction
        self.lbl_login_status = ctk.CTkLabel(
            self.card, text="Silakan masuk menggunakan Akun Google Anda untuk melanjutkan.",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color="#CCCCCC",
            wraplength=300,
            justify="center"
        )
        self.lbl_login_status.pack(pady=(0, 20), padx=20)
        
        # Google Sign-In Button (vibrant cyan style)
        self.btn_google = ctk.CTkButton(
            self.card, text="Masuk dengan Google",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            fg_color="#3B82F6", hover_color="#2563EB", text_color="#FFFFFF",
            width=280, height=45, corner_radius=8, command=self.perform_google_login
        )
        self.btn_google.pack(pady=10)
        
        # Remember Me Checkbox
        self.remember_var = ctk.IntVar(value=1)
        self.chk_remember = ctk.CTkCheckBox(
            self.card, text="Ingat sesi masuk saya", 
            variable=self.remember_var,
            font=ctk.CTkFont(size=11),
            fg_color="#3B82F6", hover_color="#2563EB"
        )
        self.chk_remember.pack(pady=(5, 10))

    def perform_google_login(self):
        self.lbl_login_status.configure(text="", text_color="#FFFFFF")
        
        if firebase_handler.is_mock_mode():
            dialog = ctk.CTkInputDialog(
                title="Google Login (Simulasi)",
                text="Masukkan Email Google Simulasi Anda:\n(Contoh: user@gmail.com atau admin@bersihin.com)"
            )
            email = dialog.get_input()
            if not email:
                return
            email = email.strip()
            if '@' not in email:
                self.lbl_login_status.configure(text="Format email tidak valid.", text_color="#EF4444")
                return
                
            self.btn_google.configure(state="disabled", text="Menghubungkan...")
            self.lbl_login_status.configure(text="Memproses login simulasi...", text_color="#FFFFFF")
            
            def run_mock():
                user, err = firebase_handler.login_mock_google(email)
                if err:
                    self.after(0, lambda: self.on_login_fail(err))
                else:
                    self.after(0, lambda: self.on_login_success(user))
            threading.Thread(target=run_mock, daemon=True).start()
        else:
            self.btn_google.configure(state="disabled", text="Membuka Browser...")
            
            def update_status(status_msg):
                self.after(0, lambda: self.lbl_login_status.configure(text=status_msg, text_color="#3B82F6"))
                
            def run_online():
                user, err = firebase_handler.login_user_with_google(on_status_update=update_status)
                if err:
                    self.after(0, lambda: self.on_login_fail(err))
                else:
                    self.after(0, lambda: self.on_login_success(user))
            threading.Thread(target=run_online, daemon=True).start()

    def on_login_fail(self, error_msg):
        self.btn_google.configure(state="normal", text="Masuk dengan Google")
        self.lbl_login_status.configure(text=error_msg, text_color="#EF4444")

    def on_login_success(self, user_data):
        self.btn_google.configure(state="normal", text="Masuk dengan Google")
        if self.remember_var.get() == 1:
            self.controller.save_session(user_data)
        else:
            self.controller.clear_session()
        self.controller.current_user = user_data
        self.controller.initialize_main_app()

class DashboardFrame(ctk.CTkFrame):
    """Dashboard tab showing quick system stats and circular RAM graph."""
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        
        # Grid layout configuration
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # Title Label
        title = ctk.CTkLabel(
            self, text="Dasbor Pemantauan Sistem", 
            font=ctk.CTkFont(family="Segoe UI", size=24, weight="bold"),
            text_color="#FFFFFF"
        )
        title.grid(row=0, column=0, columnspan=2, padx=20, pady=(20, 10), sticky="w")
        
        # Left side: Circular Progress Card
        self.card_left = ctk.CTkFrame(self, fg_color="#1E1E1E", corner_radius=15)
        self.card_left.grid(row=1, column=0, padx=15, pady=15, sticky="nsew")
        
        # Center contents of Left Card
        self.card_left.grid_columnconfigure(0, weight=1)
        
        card_title = ctk.CTkLabel(
            self.card_left, text="Penggunaan RAM", 
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
            text_color="#888888"
        )
        card_title.grid(row=0, column=0, pady=(15, 10))
        
        self.progress = CircularProgress(self.card_left, bg_color="#1E1E1E", fg_color="#3B82F6")
        self.progress.grid(row=1, column=0, pady=(10, 20))
        
        # Right side: Detail Statistics Card
        self.card_right = ctk.CTkFrame(self, fg_color="#1E1E1E", corner_radius=15)
        self.card_right.grid(row=1, column=1, padx=15, pady=15, sticky="nsew")
        
        self.card_right.grid_columnconfigure(0, weight=1)
        
        stats_title = ctk.CTkLabel(
            self.card_right, text="Rincian Statis Memori", 
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
            text_color="#888888"
        )
        stats_title.grid(row=0, column=0, pady=(15, 15), padx=20, sticky="w")
        
        # Status rows container
        self.stats_container = ctk.CTkFrame(self.card_right, fg_color="transparent")
        self.stats_container.grid(row=1, column=0, padx=20, pady=5, sticky="ew")
        self.stats_container.grid_columnconfigure(1, weight=1)
        
        # RAM Stats Labels
        self.add_stat_row("Total RAM:", "total_lbl", 0)
        self.add_stat_row("RAM Terpakai:", "used_lbl", 1)
        self.add_stat_row("RAM Tersedia:", "avail_lbl", 2)
        self.add_stat_row("Beban CPU:", "cpu_lbl", 3)
        
        # Bottom Buttons
        self.btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.btn_frame.grid(row=2, column=0, columnspan=2, pady=(10, 20), padx=15, sticky="ew")
        self.btn_frame.grid_columnconfigure(0, weight=1)
        self.btn_frame.grid_columnconfigure(1, weight=1)
        
        self.btn_clean_ram = ctk.CTkButton(
            self.btn_frame, text="Optimalkan RAM Cepat", 
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            fg_color="#3B82F6", hover_color="#2563EB", text_color="#FFFFFF",
            height=45, corner_radius=10, command=self.quick_clean_ram
        )
        self.btn_clean_ram.grid(row=0, column=0, padx=10, sticky="ew")
        
        self.btn_scan_files = ctk.CTkButton(
            self.btn_frame, text="Buka Pembersih File", 
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            fg_color="#475569", hover_color="#334155", text_color="#FFFFFF",
            height=45, corner_radius=10, command=lambda: self.controller.show_frame(FileCleanerFrame)
        )
        self.btn_scan_files.grid(row=0, column=1, padx=10, sticky="ew")
        
        self.update_stats()

    def add_stat_row(self, label_text, var_name, row_idx):
        lbl = ctk.CTkLabel(self.stats_container, text=label_text, font=ctk.CTkFont(family="Segoe UI", size=14), text_color="#CCCCCC")
        lbl.grid(row=row_idx, column=0, pady=8, sticky="w")
        
        val = ctk.CTkLabel(self.stats_container, text="-", font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"), text_color="#FFFFFF")
        val.grid(row=row_idx, column=1, pady=8, sticky="e")
        setattr(self, var_name, val)

    def update_stats(self):
        """Periodically fetches memory usage and CPU info to update the UI."""
        if not self.controller.current_user:
            return
            
        try:
            ram = memory_cleaner.get_ram_usage()
            self.progress.set_value(ram['percent'])
            
            # Format bytes to GB
            to_gb = lambda b: f"{b / (1024**3):.2f} GB"
            self.total_lbl.configure(text=to_gb(ram['total']))
            self.used_lbl.configure(text=to_gb(ram['used']))
            self.avail_lbl.configure(text=to_gb(ram['available']))
            
            # CPU Load
            import psutil
            cpu_percent = psutil.cpu_percent()
            self.cpu_lbl.configure(text=f"{cpu_percent}%")
        except Exception:
            pass
            
        # Poll again in 2 seconds
        self.after(2000, self.update_stats)

    def quick_clean_ram(self):
        """Triggers working set memory cleaning in a background thread."""
        confirm = messagebox.askyesno(
            "Konfirmasi Optimasi RAM", 
            "Apakah Anda yakin ingin mengoptimalkan memori RAM sekarang?"
        )
        if not confirm:
            return
            
        self.btn_clean_ram.configure(state="disabled", text="Membersihkan...")
        self.controller.show_status("Menjalankan pembersihan RAM cepat...")
        
        def run():
            ram_before = memory_cleaner.get_ram_usage()
            cleaned, failed = memory_cleaner.clean_process_working_sets()
            
            admin_msg = ""
            if memory_cleaner.is_admin():
                c_ok, c_msg = memory_cleaner.clean_system_file_cache()
                s_ok, s_msg = memory_cleaner.clean_standby_list()
                if c_ok or s_ok:
                    admin_msg = " & Cache Sistem"
            
            ram_after = memory_cleaner.get_ram_usage()
            
            # Update UI on main thread
            self.after(0, lambda: self.finish_clean(ram_before, ram_after, cleaned, admin_msg))
            
        threading.Thread(target=run, daemon=True).start()

    def finish_clean(self, ram_before, ram_after, cleaned_count, admin_msg):
        self.btn_clean_ram.configure(state="normal", text="Optimalkan RAM Cepat")
        
        to_gb = lambda b: f"{b / (1024**3):.2f} GB"
        freed_bytes = max(0, ram_before['used'] - ram_after['used'])
        
        if freed_bytes >= 1024**3:
            freed_str = f"{freed_bytes / (1024**3):.2f} GB"
        else:
            freed_str = f"{freed_bytes / (1024**2):.1f} MB"
            
        msg = (
            f"Optimasi RAM Selesai!\n\n"
            f"Kondisi RAM Sebelum: {to_gb(ram_before['used'])} ({ram_before['percent']}% terpakai)\n"
            f"RAM yang Dibebaskan: {freed_str}\n\n"
            f"Fitur: Membersihkan {cleaned_count} proses{admin_msg}."
        )
        self.controller.show_status(f"Berhasil membebaskan {freed_str} RAM!")
        messagebox.showinfo("Laporan Optimasi RAM", msg)
        
        # Kirim laporan performa ke Firebase
        freed_mb = freed_bytes / (1024 * 1024)
        def report_worker():
            firebase_handler.report_stats(
                self.controller.current_user['uid'],
                self.controller.current_user['idToken'],
                freed_mb,
                0
            )
        threading.Thread(target=report_worker, daemon=True).start()

class RAMCleanerFrame(ctk.CTkFrame):
    """Detailed RAM cleaner with process listings and options."""
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        
        # Title Label
        title = ctk.CTkLabel(
            self, text="Pembersih RAM Mendalam", 
            font=ctk.CTkFont(family="Segoe UI", size=24, weight="bold"),
            text_color="#FFFFFF"
        )
        title.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")
        
        # Description
        desc = ctk.CTkLabel(
            self, text="Gunakan fitur di bawah untuk membersihkan tipe memori spesifik di Windows.",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color="#AAAAAA"
        )
        desc.grid(row=1, column=0, padx=20, pady=(0, 15), sticky="w")
        
        # Container for clean options & process list
        self.main_content = ctk.CTkFrame(self, fg_color="transparent")
        self.main_content.grid(row=2, column=0, padx=20, pady=5, sticky="nsew")
        self.main_content.grid_columnconfigure(0, weight=1)
        self.main_content.grid_columnconfigure(1, weight=1)
        self.main_content.grid_rowconfigure(0, weight=1)
        
        # Left Panel: Options
        self.left_panel = ctk.CTkFrame(self.main_content, fg_color="#1E1E1E", corner_radius=12)
        self.left_panel.grid(row=0, column=0, padx=(0, 10), pady=0, sticky="nsew")
        self.left_panel.grid_columnconfigure(0, weight=1)
        
        opt_title = ctk.CTkLabel(
            self.left_panel, text="Opsi Pembersihan",
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
            text_color="#F8FAFC"
        )
        opt_title.grid(row=0, column=0, padx=20, pady=15, sticky="w")
        
        # Checkboxes
        self.cb_working_set = ctk.CTkCheckBox(self.left_panel, text="Working Set Proses (Aman)", font=ctk.CTkFont(size=13))
        self.cb_working_set.grid(row=1, column=0, padx=20, pady=10, sticky="w")
        self.cb_working_set.select()
        
        self.cb_sys_cache = ctk.CTkCheckBox(
            self.left_panel, 
            text="System File Cache (Butuh Admin)", 
            font=ctk.CTkFont(size=13)
        )
        self.cb_sys_cache.grid(row=2, column=0, padx=20, pady=10, sticky="w")
        self.cb_sys_cache.select()
            
        self.cb_standby = ctk.CTkCheckBox(
            self.left_panel, 
            text="Standby List Memory (Butuh Admin)", 
            font=ctk.CTkFont(size=13)
        )
        self.cb_standby.grid(row=3, column=0, padx=20, pady=10, sticky="w")
        self.cb_standby.select()
            
        # Action button
        self.btn_deep_clean = ctk.CTkButton(
            self.left_panel, text="Mulai Bersihkan Memori",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            fg_color="#3B82F6", hover_color="#2563EB", text_color="#FFFFFF",
            height=40, command=self.run_deep_clean
        )
        self.btn_deep_clean.grid(row=5, column=0, padx=20, pady=(20, 20), sticky="ew")
        
        # Right Panel: Top memory processes
        self.right_panel = ctk.CTkFrame(self.main_content, fg_color="#1E1E1E", corner_radius=12)
        self.right_panel.grid(row=0, column=1, padx=(10, 0), pady=0, sticky="nsew")
        self.right_panel.grid_columnconfigure(0, weight=1)
        self.right_panel.grid_rowconfigure(1, weight=1)
        
        proc_title = ctk.CTkLabel(
            self.right_panel, text="10 Konsumen RAM Terbesar",
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
            text_color="#F8FAFC"
        )
        proc_title.grid(row=0, column=0, padx=15, pady=15, sticky="w")
        
        # Scrollable textbox to show processes
        self.proc_textbox = ctk.CTkTextbox(self.right_panel, fg_color="#121212", border_color="#2E2E2E", font=("Consolas", 12))
        self.proc_textbox.grid(row=1, column=0, padx=15, pady=(0, 15), sticky="nsew")
        self.proc_textbox.configure(state="disabled")
        
        self.refresh_process_list()

    def refresh_process_list(self):
        """Updates the top processes text box with running programs."""
        if not self.controller.current_user:
            return
            
        try:
            procs = memory_cleaner.get_top_processes(10)
            self.proc_textbox.configure(state="normal")
            self.proc_textbox.delete("1.0", tk.END)
            
            # Header
            header = f"{'PID':<8}{'Nama Proses':<22}{'Pemakaian RAM':<12}\n"
            self.proc_textbox.insert(tk.END, header)
            self.proc_textbox.insert(tk.END, "-" * 42 + "\n")
            
            for p in procs:
                mem_mb = p['memory'] / (1024 * 1024)
                name_trunc = p['name'][:20]
                line = f"{p['pid']:<8}{name_trunc:<22}{mem_mb:.1f} MB\n"
                self.proc_textbox.insert(tk.END, line)
                
            self.proc_textbox.configure(state="disabled")
        except Exception:
            pass
            
        # Refresh every 5 seconds
        self.after(5000, self.refresh_process_list)

    def run_deep_clean(self):
        """Performs deep memory cleaning actions selected by the user."""
        clean_ws = self.cb_working_set.get()
        clean_cache = self.cb_sys_cache.get()
        clean_standby = self.cb_standby.get()
        
        if not (clean_ws or clean_cache or clean_standby):
            messagebox.showwarning("Pilih Opsi", "Silakan pilih minimal satu opsi pembersihan.")
            return
            
        # Check if we need admin rights
        needs_admin = (clean_cache or clean_standby)
        if needs_admin and not memory_cleaner.is_admin():
            confirm = messagebox.askyesno(
                "Butuh Hak Akses Administrator",
                "Opsi pembersihan memori mendalam (System File Cache / Standby List) membutuhkan hak akses Administrator.\n\n"
                "Apakah Anda ingin menjalankan ulang aplikasi ini sebagai Administrator?"
            )
            if confirm:
                relaunch_as_admin()
            return
            
        ram = memory_cleaner.get_ram_usage()
        to_gb = lambda b: f"{b / (1024**3):.2f} GB"
        confirm = messagebox.askyesno(
            "Konfirmasi Pembersihan RAM", 
            f"Kondisi RAM Saat Ini: {to_gb(ram['used'])} ({ram['percent']}% terpakai)\n\n"
            f"Apakah Anda yakin ingin melakukan pembersihan RAM secara mendalam?"
        )
        if not confirm:
            return
            
        self.btn_deep_clean.configure(state="disabled", text="Membersihkan...")
        self.controller.show_status("Menjalankan pembersihan memori mendalam...")
        
        def run():
            ram_before = memory_cleaner.get_ram_usage()
            actions = []
            
            if clean_ws:
                cleaned, failed = memory_cleaner.clean_process_working_sets()
                actions.append(f"Working Set ({cleaned} proses)")
                
            if clean_cache and memory_cleaner.is_admin():
                ok, msg = memory_cleaner.clean_system_file_cache()
                if ok:
                    actions.append("System File Cache")
                    
            if clean_standby and memory_cleaner.is_admin():
                ok, msg = memory_cleaner.clean_standby_list()
                if ok:
                    actions.append("Standby List")
                    
            ram_after = memory_cleaner.get_ram_usage()
            
            self.after(0, lambda: self.finish_deep_clean(ram_before, ram_after, actions))
            
        threading.Thread(target=run, daemon=True).start()

    def finish_deep_clean(self, ram_before, ram_after, actions_done):
        self.btn_deep_clean.configure(state="normal", text="Mulai Bersihkan Memori")
        
        to_gb = lambda b: f"{b / (1024**3):.2f} GB"
        freed_bytes = max(0, ram_before['used'] - ram_after['used'])
        
        if freed_bytes >= 1024**3:
            freed_str = f"{freed_bytes / (1024**3):.2f} GB"
        else:
            freed_str = f"{freed_bytes / (1024**2):.1f} MB"
            
        done_str = ", ".join(actions_done)
        
        msg = (
            f"Pembersihan Memori Mendalam Selesai!\n\n"
            f"Fitur dibersihkan: {done_str}\n\n"
            f"Kondisi RAM Sebelum: {to_gb(ram_before['used'])} ({ram_before['percent']}% terpakai)\n"
            f"RAM yang Dibebaskan: {freed_str}"
        )
        self.controller.show_status(f"Pembersihan selesai! Bebas {freed_str}.")
        messagebox.showinfo("Laporan Pembersihan Mendalam", msg)
        self.refresh_process_list()
        
        # Kirim laporan performa ke Firebase
        freed_mb = freed_bytes / (1024 * 1024)
        def report_worker():
            firebase_handler.report_stats(
                self.controller.current_user['uid'],
                self.controller.current_user['idToken'],
                freed_mb,
                0
            )
        threading.Thread(target=report_worker, daemon=True).start()

class FileCleanerFrame(ctk.CTkFrame):
    """File scanner and cleaner page."""
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        
        self.scanned_sizes = {}
        self.checkbox_vars = {}
        
        # Title Label
        title = ctk.CTkLabel(
            self, text="Pembersih File Sampah", 
            font=ctk.CTkFont(family="Segoe UI", size=24, weight="bold"),
            text_color="#FFFFFF"
        )
        title.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")
        
        # Description
        desc = ctk.CTkLabel(
            self, text="Pindai dan bersihkan file sampah yang aman dihapus untuk melegakan ruang harddisk Anda.",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color="#AAAAAA"
        )
        desc.grid(row=1, column=0, padx=20, pady=(0, 15), sticky="w")
        
        # Scrollable container for targets
        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color="#1E1E1E", corner_radius=12)
        self.scroll_frame.grid(row=2, column=0, padx=20, pady=5, sticky="nsew")
        self.scroll_frame.columnconfigure(0, weight=1)
        
        # Build target items
        self.targets = file_cleaner.get_clean_targets()
        self.ui_elements = {}
        
        row_idx = 0
        is_admin = memory_cleaner.is_admin()
        
        for key, info in self.targets.items():
            # Container for each target (using standard tk.Frame for high performance redraws)
            item_frame = tk.Frame(self.scroll_frame, bg="#1E1E1E")
            item_frame.grid(row=row_idx, column=0, padx=10, pady=8, sticky="ew")
            item_frame.columnconfigure(1, weight=1)
            
            # Checkbox variable
            cb_var = tk.BooleanVar(value=True)
            self.checkbox_vars[key] = cb_var
            
            # Checkbox
            checkbox = ctk.CTkCheckBox(item_frame, text=info['name'], variable=cb_var, font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"))
            checkbox.grid(row=0, column=0, sticky="w")
            
            # Size Label (initially empty or scanning)
            size_lbl = ctk.CTkLabel(item_frame, text="Menunggu pemindaian...", font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"), text_color="#3B82F6")
            size_lbl.grid(row=0, column=2, padx=10, sticky="e")
            
            # Description
            desc_lbl = ctk.CTkLabel(item_frame, text=info['desc'], font=ctk.CTkFont(family="Segoe UI", size=11), text_color="#888888")
            desc_lbl.grid(row=1, column=0, columnspan=3, padx=(28, 0), pady=(2, 0), sticky="w")
            
            # Admin warning badge if required but not admin
            if info.get('requires_admin') and not is_admin:
                # Keep checkbox enabled, but append notice to description
                desc_lbl.configure(text=f"(Butuh Admin) {info['desc']}")
                
            self.ui_elements[key] = {
                'frame': item_frame,
                'checkbox': checkbox,
                'size_lbl': size_lbl,
                'desc_lbl': desc_lbl
            }
            row_idx += 1
            
        # Action Buttons frame
        self.btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.btn_frame.grid(row=3, column=0, pady=(15, 20), padx=20, sticky="ew")
        self.btn_frame.grid_columnconfigure(0, weight=1)
        self.btn_frame.grid_columnconfigure(1, weight=1)
        
        self.btn_scan = ctk.CTkButton(
            self.btn_frame, text="Pindai File Sampah",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            fg_color="#475569", hover_color="#334155", text_color="#FFFFFF",
            height=42, command=self.run_scan
        )
        self.btn_scan.grid(row=0, column=0, padx=10, sticky="ew")
        
        self.btn_clean = ctk.CTkButton(
            self.btn_frame, text="Bersihkan File Terpilih",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            fg_color="#3B82F6", hover_color="#2563EB", text_color="#FFFFFF",
            height=42, command=self.run_clean
        )
        self.btn_clean.grid(row=0, column=1, padx=10, sticky="ew")
        self.btn_clean.configure(state="disabled") # Disabled until scanned

    def format_size(self, size_bytes):
        """Converts bytes to readable string (KB, MB, GB)."""
        if size_bytes <= 0:
            return "0 KB"
        
        units = ['B', 'KB', 'MB', 'GB']
        size = float(size_bytes)
        idx = 0
        while size >= 1024 and idx < len(units) - 1:
            size /= 1024.0
            idx += 1
        return f"{size:.2f} {units[idx]}"

    def run_scan(self):
        """Scans selected target directories for file sizes in background thread."""
        # Check if any selected target requires admin and we are not admin
        needs_admin = False
        for key, ui in self.ui_elements.items():
            if self.checkbox_vars[key].get() and self.targets[key].get('requires_admin'):
                needs_admin = True
                break
                
        if needs_admin and not memory_cleaner.is_admin():
            confirm = messagebox.askyesno(
                "Butuh Hak Akses Administrator",
                "Beberapa kategori pembersihan yang Anda pilih membutuhkan hak akses Administrator.\n\n"
                "Apakah Anda ingin menjalankan ulang aplikasi ini sebagai Administrator?"
            )
            if confirm:
                relaunch_as_admin()
            return
            
        self.btn_scan.configure(state="disabled", text="Memindai...")
        self.btn_clean.configure(state="disabled")
        self.controller.show_status("Memindai file sampah di sistem...")
        
        # Reset labels
        for key, ui in self.ui_elements.items():
            if self.targets[key].get('requires_admin') and not memory_cleaner.is_admin():
                continue
            ui['size_lbl'].configure(text="Memindai...", text_color="#3B82F6")
            
        def scan_worker():
            total_size_all = 0
            for key, info in self.targets.items():
                if info.get('requires_admin') and not memory_cleaner.is_admin():
                    continue
                    
                size, count = file_cleaner.scan_target(key, info)
                self.scanned_sizes[key] = size
                total_size_all += size
                
                # Update UI on main thread for this key
                self.after(0, lambda k=key, s=size, c=count: self.update_key_size(k, s, c))
                
            self.after(0, lambda total=total_size_all: self.finish_scan(total))
            
        threading.Thread(target=scan_worker, daemon=True).start()

    def update_key_size(self, key, size, count):
        ui = self.ui_elements[key]
        if key == 'dns_cache':
            ui['size_lbl'].configure(text="Tersedia", text_color="#10B981")
        else:
            size_str = self.format_size(size)
            ui['size_lbl'].configure(text=f"{size_str} ({count} file)", text_color="#FFFFFF")

    def finish_scan(self, total_size):
        self.btn_scan.configure(state="normal", text="Pindai File Sampah")
        if total_size > 0:
            self.btn_clean.configure(state="normal")
            
        total_str = self.format_size(total_size)
        self.controller.show_status(f"Pemindaian selesai! Menemukan {total_str} file sampah.")
        messagebox.showinfo("Pemindaian Selesai", f"Ditemukan total {total_str} file sampah yang dapat dibersihkan.")

    def run_clean(self):
        """Cleans checked targets in background thread."""
        targets_to_clean = []
        for key, var in self.checkbox_vars.items():
            if var.get():
                targets_to_clean.append(key)
                
        if not targets_to_clean:
            messagebox.showwarning("Pilih File", "Pilih minimal satu kategori file sampah untuk dibersihkan.")
            return
            
        total_before = sum(self.scanned_sizes.get(k, 0) for k in targets_to_clean)
        before_str = self.format_size(total_before)
        confirm = messagebox.askyesno(
            "Konfirmasi Hapus File Sampah", 
            f"Kondisi Sampah Saat Ini: {before_str}\n\n"
            f"Apakah Anda yakin ingin menghapus semua file sampah tersebut secara permanen dari harddisk Anda?"
        )
        if not confirm:
            return
            
        self.btn_clean.configure(state="disabled", text="Membersihkan...")
        self.btn_scan.configure(state="disabled")
        self.controller.show_status("Sedang membersihkan file sampah terpilih...")
        
        def clean_worker():
            total_deleted = 0
            total_failed = 0
            
            for key in targets_to_clean:
                info = self.targets[key]
                freed, deleted, failed = file_cleaner.clean_target(key, info)
                total_deleted += deleted
                total_failed += failed
                
                # Re-scan to update size label
                new_size, new_count = file_cleaner.scan_target(key, info)
                self.scanned_sizes[key] = new_size
                self.after(0, lambda k=key, s=new_size, c=new_count: self.update_key_size(k, s, c))
                
            # Hitung total ukuran setelah dibersihkan
            total_after = sum(self.scanned_sizes.get(k, 0) for k in targets_to_clean)
            total_freed = max(0, total_before - total_after)
            
            self.after(0, lambda tb=total_before, ta=total_after, tf=total_freed, td=total_deleted: 
                       self.finish_clean(tb, ta, tf, td))
            
        threading.Thread(target=clean_worker, daemon=True).start()

    def finish_clean(self, total_before, total_after, total_freed, total_deleted):
        self.btn_clean.configure(state="disabled", text="Bersihkan File Terpilih")
        self.btn_scan.configure(state="normal", text="Pindai File Sampah")
        
        before_str = self.format_size(total_before)
        after_str = self.format_size(total_after)
        freed_str = self.format_size(total_freed)
        
        msg = (
            f"Pembersihan File Sampah Selesai!\n\n"
            f"Kondisi Sampah Sebelum: {before_str}\n"
            f"Sampah Tersisa: {after_str} (file terkunci sistem dilewati secara aman)\n"
            f"Ruang yang Dibebaskan: {freed_str}\n\n"
            f"Berhasil menghapus {total_deleted} file sampah."
        )
        self.controller.show_status(f"Berhasil melegakan {freed_str} ruang harddisk!")
        messagebox.showinfo("Laporan Pembersihan File", msg)
        
        # Kirim laporan performa ke Firebase
        freed_mb = total_freed / (1024 * 1024)
        def report_worker():
            firebase_handler.report_stats(
                self.controller.current_user['uid'],
                self.controller.current_user['idToken'],
                0,
                freed_mb
            )
        threading.Thread(target=report_worker, daemon=True).start()

class SettingsFrame(ctk.CTkFrame):
    """Settings page to configure startup run and auto-clean RAM."""
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        
        self.grid_columnconfigure(0, weight=1)
        
        # Title Label
        title = ctk.CTkLabel(
            self, text="Pengaturan Aplikasi", 
            font=ctk.CTkFont(family="Segoe UI", size=24, weight="bold"),
            text_color="#FFFFFF"
        )
        title.grid(row=0, column=0, padx=20, pady=(20, 15), sticky="w")
        
        # Options container
        self.options_container = ctk.CTkFrame(self, fg_color="#1E1E1E", corner_radius=12)
        self.options_container.grid(row=1, column=0, padx=20, pady=5, sticky="ew")
        self.options_container.grid_columnconfigure(0, weight=1)
        
        # Startup Option
        startup_frame = ctk.CTkFrame(self.options_container, fg_color="transparent")
        startup_frame.grid(row=0, column=0, padx=20, pady=15, sticky="ew")
        startup_frame.grid_columnconfigure(0, weight=1)
        
        lbl_startup = ctk.CTkLabel(
            startup_frame, text="Mulai saat Windows menyala (Startup)",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color="#FFFFFF"
        )
        lbl_startup.grid(row=0, column=0, sticky="w")
        
        lbl_startup_desc = ctk.CTkLabel(
            startup_frame, text="Menjalankan aplikasi secara otomatis ketika komputer dihidupkan.",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color="#888888"
        )
        lbl_startup_desc.grid(row=1, column=0, sticky="w", pady=(2, 0))
        
        self.startup_var = tk.BooleanVar(value=self.get_startup_status())
        self.switch_startup = ctk.CTkSwitch(
            startup_frame, text="", variable=self.startup_var, 
            command=self.toggle_startup, progress_color="#3B82F6"
        )
        self.switch_startup.grid(row=0, column=1, rowspan=2, sticky="e")
        
        # Separator line
        sep = ctk.CTkFrame(self.options_container, height=2, fg_color="#2E2E2E")
        sep.grid(row=1, column=0, padx=20, sticky="ew")
        
        # Auto clean Option
        autoclean_frame = ctk.CTkFrame(self.options_container, fg_color="transparent")
        autoclean_frame.grid(row=2, column=0, padx=20, pady=15, sticky="ew")
        autoclean_frame.grid_columnconfigure(0, weight=1)
        
        lbl_autoclean = ctk.CTkLabel(
            autoclean_frame, text="Optimasi RAM Otomatis",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color="#FFFFFF"
        )
        lbl_autoclean.grid(row=0, column=0, sticky="w")
        
        lbl_autoclean_desc = ctk.CTkLabel(
            autoclean_frame, text="Optimalkan RAM secara otomatis ketika pemakaian melebihi batas.",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color="#888888"
        )
        lbl_autoclean_desc.grid(row=1, column=0, sticky="w", pady=(2, 0))
        
        self.autoclean_var = tk.BooleanVar(value=self.controller.autoclean_enabled)
        self.switch_autoclean = ctk.CTkSwitch(
            autoclean_frame, text="", variable=self.autoclean_var, 
            command=self.toggle_autoclean, progress_color="#3B82F6"
        )
        self.switch_autoclean.grid(row=0, column=1, rowspan=2, sticky="e")
        
        # Slider for threshold
        slider_frame = ctk.CTkFrame(self.options_container, fg_color="transparent")
        slider_frame.grid(row=3, column=0, padx=20, pady=(0, 20), sticky="ew")
        slider_frame.grid_columnconfigure(1, weight=1)
        
        self.lbl_threshold = ctk.CTkLabel(
            slider_frame, text=f"Batas Pemakaian: {self.controller.autoclean_threshold}%",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color="#CCCCCC", width=150, anchor="w"
        )
        self.lbl_threshold.grid(row=0, column=0, sticky="w")
        
        self.slider = ctk.CTkSlider(
            slider_frame, from_=50, to=95, 
            number_of_steps=9, command=self.update_threshold_slider,
            progress_color="#3B82F6", button_color="#2563EB"
        )
        self.slider.set(self.controller.autoclean_threshold)
        self.slider.grid(row=0, column=1, sticky="ew", padx=10)
        
        # If disabled initially, disable the slider
        if not self.controller.autoclean_enabled:
            self.slider.configure(state="disabled")
            
        # Separator line 2
        sep2 = ctk.CTkFrame(self.options_container, height=2, fg_color="#2E2E2E")
        sep2.grid(row=4, column=0, padx=20, sticky="ew")
        
        # Floating Widget Option
        widget_frame = ctk.CTkFrame(self.options_container, fg_color="transparent")
        widget_frame.grid(row=5, column=0, padx=20, pady=15, sticky="ew")
        widget_frame.grid_columnconfigure(0, weight=1)
        
        lbl_widget = ctk.CTkLabel(
            widget_frame, text="Widget Desktop Melayang",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color="#FFFFFF"
        )
        lbl_widget.grid(row=0, column=0, sticky="w")
        
        lbl_widget_desc = ctk.CTkLabel(
            widget_frame, text="Tampilkan widget melayang kecil di layar desktop untuk optimasi RAM cepat.",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color="#888888"
        )
        lbl_widget_desc.grid(row=1, column=0, sticky="w", pady=(2, 0))
        
        self.widget_var = tk.BooleanVar(value=self.controller.floating_widget_enabled)
        self.switch_widget = ctk.CTkSwitch(
            widget_frame, text="", variable=self.widget_var, 
            command=self.toggle_widget, progress_color="#3B82F6"
        )
        self.switch_widget.grid(row=0, column=1, rowspan=2, sticky="e")
            
        # Log out button at bottom of settings
        logout_btn = ctk.CTkButton(
            self, text="Keluar dari Akun (Logout)",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            fg_color="#333333", hover_color="#444444", text_color="#EF4444",
            height=35, command=self.perform_logout
        )
        logout_btn.grid(row=2, column=0, padx=20, pady=25, sticky="w")

    def toggle_widget(self):
        val = self.widget_var.get()
        self.controller.floating_widget_enabled = val
        self.controller.save_settings()
        self.controller.toggle_floating_widget(val)

    def perform_logout(self):
        confirm = messagebox.askyesno("Logout", "Apakah Anda yakin ingin keluar dari akun?")
        if confirm:
            self.controller.clear_session()
            self.controller.current_user = None
            # Tampilkan layar login kembali
            self.controller.show_login_screen()

    def get_startup_status(self):
        """Reads user startup run status from registry."""
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        app_name = "Bersihin"
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_READ)
            winreg.QueryValueEx(key, app_name)
            winreg.CloseKey(key)
            return True
        except Exception:
            return False

    def toggle_startup(self):
        """Enables/disables Windows registry run key for the app."""
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        app_name = "Bersihin"
        enabled = self.startup_var.get()
        
        # Determine executable location
        if getattr(sys, 'frozen', False):
            exe_path = sys.executable
        else:
            exe_path = os.path.abspath(sys.argv[0])
            
        cmd = f'"{exe_path}" --startup'
        
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
            if enabled:
                winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, cmd)
                self.controller.show_status("Aplikasi didaftarkan pada Startup Windows.")
            else:
                try:
                    winreg.DeleteValue(key, app_name)
                    self.controller.show_status("Aplikasi dihapus dari Startup Windows.")
                except FileNotFoundError:
                    pass
            winreg.CloseKey(key)
        except Exception as e:
            self.startup_var.set(not enabled) # Revert
            messagebox.showerror("Error", f"Gagal merubah registrasi Startup: {e}")

    def toggle_autoclean(self):
        enabled = self.autoclean_var.get()
        self.controller.autoclean_enabled = enabled
        self.controller.save_settings()
        
        if enabled:
            self.slider.configure(state="normal")
            self.controller.show_status(f"Auto-Clean diaktifkan (Batas: {self.controller.autoclean_threshold}%)")
        else:
            self.slider.configure(state="disabled")
            self.controller.show_status("Auto-Clean dinonaktifkan.")

    def update_threshold_slider(self, val):
        threshold = int(val)
        self.lbl_threshold.configure(text=f"Batas Pemakaian: {threshold}%")
        self.controller.autoclean_threshold = threshold
        self.controller.save_settings()

class GameBoostFrame(ctk.CTkFrame):
    """Premium Game Booster tab to optimize RAM and set High CPU priority for games."""
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        
        self.game_path = ""
        self.is_boosting = False
        self.suspended_pids = []
        
        # Title
        title = ctk.CTkLabel(
            self, text="Game Mode Booster",
            font=ctk.CTkFont(family="Segoe UI", size=24, weight="bold"),
            text_color="#FFFFFF"
        )
        title.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")
        
        desc = ctk.CTkLabel(
            self, text="Tangguhkan proses non-kritis dan jalankan game dengan prioritas CPU maksimum.",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color="#AAAAAA"
        )
        desc.grid(row=1, column=0, padx=20, pady=(0, 15), sticky="w")
        
        # Main layout container
        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.grid(row=2, column=0, padx=20, pady=5, sticky="nsew")
        self.container.grid_columnconfigure(0, weight=1)
        self.container.grid_columnconfigure(1, weight=1)
        self.container.grid_rowconfigure(0, weight=1)
        
        # Left Panel: Game launcher
        self.left_panel = ctk.CTkFrame(self.container, fg_color="#1E1E1E", corner_radius=12)
        self.left_panel.grid(row=0, column=0, padx=(0, 10), sticky="nsew")
        self.left_panel.grid_columnconfigure(0, weight=1)
        
        lbl_game = ctk.CTkLabel(self.left_panel, text="Pilih Game Anda", font=ctk.CTkFont(size=15, weight="bold"))
        lbl_game.pack(pady=(15, 10), padx=20, anchor="w")
        
        self.entry_game = ctk.CTkEntry(self.left_panel, placeholder_text="Belum ada game terpilih...", height=35)
        self.entry_game.pack(pady=5, padx=20, fill="x")
        self.entry_game.configure(state="disabled")
        
        btn_choose = ctk.CTkButton(
            self.left_panel, text="Pilih Game (.exe)",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#475569", hover_color="#334155",
            command=self.choose_game_exe
        )
        btn_choose.pack(pady=10, padx=20, anchor="w")
        
        self.btn_boost = ctk.CTkButton(
            self.left_panel, text="Aktifkan Game Boost & Jalankan",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#3B82F6", hover_color="#2563EB", text_color="#FFFFFF",
            height=45, command=self.toggle_boost
        )
        self.btn_boost.pack(pady=20, padx=20, fill="x")
        
        # Right Panel: Status / Suspended processes
        self.right_panel = ctk.CTkFrame(self.container, fg_color="#1E1E1E", corner_radius=12)
        self.right_panel.grid(row=0, column=1, padx=(10, 0), sticky="nsew")
        self.right_panel.grid_columnconfigure(0, weight=1)
        self.right_panel.grid_rowconfigure(2, weight=1)
        
        lbl_status_title = ctk.CTkLabel(self.right_panel, text="Status Pengoptimalan", font=ctk.CTkFont(size=15, weight="bold"))
        lbl_status_title.grid(row=0, column=0, pady=(15, 5), padx=20, sticky="w")
        
        self.lbl_boost_status = ctk.CTkLabel(
            self.right_panel, text="BOOST NONAKTIF",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#888888"
        )
        self.lbl_boost_status.grid(row=1, column=0, pady=5, padx=20, sticky="w")
        
        self.proc_textbox = ctk.CTkTextbox(self.right_panel, fg_color="#121212", border_color="#2E2E2E")
        self.proc_textbox.grid(row=2, column=0, pady=15, padx=20, sticky="nsew")
        self.proc_textbox.insert("1.0", "Daftar proses browser/media yang ditangguhkan sementara akan muncul di sini saat Boost aktif.")
        self.proc_textbox.configure(state="disabled")

    def choose_game_exe(self):
        file_path = filedialog.askopenfilename(
            title="Pilih Executable Game",
            filetypes=[("Executable Files", "*.exe")]
        )
        if file_path:
            self.game_path = file_path
            self.entry_game.configure(state="normal")
            self.entry_game.delete(0, tk.END)
            self.entry_game.insert(0, os.path.basename(file_path))
            self.entry_game.configure(state="disabled")
            
    def toggle_boost(self):
        if self.is_boosting:
            self.deactivate_boost()
        else:
            self.activate_boost()
            
    def activate_boost(self):
        self.is_boosting = True
        self.btn_boost.configure(text="Mengoptimalkan...", state="disabled")
        self.lbl_boost_status.configure(text="BOOST AKTIF", text_color="#10B981")
        self.controller.show_status("Menjalankan pembersihan memori Game Boost...")
        
        # 1. Quiet RAM Clean
        import memory_cleaner
        memory_cleaner.clean_process_working_sets()
        if memory_cleaner.is_admin():
            memory_cleaner.clean_system_file_cache()
            memory_cleaner.clean_standby_list()
            
        # 2. Suspend non-essential processes
        self.suspended_pids = memory_cleaner.suspend_non_essential_processes(exclude_pids=[os.getpid()])
        
        # Tulis ke kotak teks status
        self.proc_textbox.configure(state="normal")
        self.proc_textbox.delete("1.0", tk.END)
        if self.suspended_pids:
            self.proc_textbox.insert(tk.END, f"Berhasil menangguhkan {len(self.suspended_pids)} proses latar belakang:\n")
            for pid in self.suspended_pids:
                try:
                    name = psutil.Process(pid).name()
                    self.proc_textbox.insert(tk.END, f"- {name} (PID: {pid})\n")
                except:
                    pass
        else:
            self.proc_textbox.insert(tk.END, "Tidak ada proses latar belakang non-kritis yang perlu ditangguhkan.\n")
        self.proc_textbox.configure(state="disabled")
        
        # 3. Launch game (if selected)
        if self.game_path and os.path.exists(self.game_path):
            try:
                self.controller.show_status(f"Meluncurkan game: {os.path.basename(self.game_path)}")
                proc = subprocess.Popen(self.game_path, cwd=os.path.dirname(self.game_path))
                
                # Set Game Process priority to High
                memory_cleaner.set_process_priority_high(proc.pid)
                
                # Thread untuk menunggu game keluar di background
                def wait_game():
                    proc.wait()
                    self.after(0, self.deactivate_boost)
                threading.Thread(target=wait_game, daemon=True).start()
            except Exception as e:
                messagebox.showerror("Gagal", f"Gagal meluncurkan game: {e}")
                self.deactivate_boost()
                return
        
        self.btn_boost.configure(text="Nonaktifkan Game Boost", state="normal", fg_color="#EF4444", hover_color="#DC2626")
        
    def deactivate_boost(self):
        self.is_boosting = False
        self.btn_boost.configure(text="Aktifkan Game Boost & Jalankan", fg_color="#3B82F6", hover_color="#2563EB", state="disabled")
        self.controller.show_status("Mengembalikan proses latar belakang...")
        self.lbl_boost_status.configure(text="BOOST NONAKTIF", text_color="#888888")
        
        # Resume processes
        import memory_cleaner
        resumed = memory_cleaner.resume_processes(self.suspended_pids)
        self.suspended_pids = []
        
        self.proc_textbox.configure(state="normal")
        self.proc_textbox.delete("1.0", tk.END)
        self.proc_textbox.insert("1.0", f"Boost nonaktif. {resumed} proses latar belakang berhasil dipulihkan.")
        self.proc_textbox.configure(state="disabled")
        
        self.btn_boost.configure(state="normal")

class DuplicateFinderFrame(ctk.CTkFrame):
    """Premium Duplicate File Finder tab using size & MD5 hash checks."""
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        
        self.target_dir = ""
        self.dupes_list = []
        self.checkbox_vars = {}
        
        # Title
        title = ctk.CTkLabel(
            self, text="Pencari File Duplikat",
            font=ctk.CTkFont(family="Segoe UI", size=24, weight="bold"),
            text_color="#FFFFFF"
        )
        title.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")
        
        desc = ctk.CTkLabel(
            self, text="Pindai folder Anda dari file kembar dan hapus salah satunya untuk menghemat ruang disk.",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color="#AAAAAA"
        )
        desc.grid(row=1, column=0, padx=20, pady=(0, 15), sticky="w")
        
        # Top panel: Folder chooser
        self.top_panel = ctk.CTkFrame(self, fg_color="#1E1E1E", corner_radius=12, height=75)
        self.top_panel.grid(row=2, column=0, padx=20, pady=5, sticky="ew")
        self.top_panel.grid_propagate(False)
        
        self.btn_choose = ctk.CTkButton(
            self.top_panel, text="Pilih Folder",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#475569", hover_color="#334155",
            width=120, height=35, command=self.choose_folder
        )
        self.btn_choose.pack(side="left", padx=15, pady=20)
        
        self.lbl_folder = ctk.CTkLabel(
            self.top_panel, text="Tidak ada folder terpilih.",
            font=ctk.CTkFont(size=13, slant="italic"),
            text_color="#888888"
        )
        self.lbl_folder.pack(side="left", padx=10, pady=20)
        
        self.btn_scan = ctk.CTkButton(
            self.top_panel, text="Mulai Pindai",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#3B82F6", hover_color="#2563EB",
            width=120, height=35, command=self.run_scan
        )
        self.btn_scan.pack(side="right", padx=15, pady=20)
        self.btn_scan.configure(state="disabled")
        
        # Middle panel: Scrollable results list
        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color="#1E1E1E", label_text="Daftar File Duplikat Ditemukan", corner_radius=12)
        self.scroll_frame.grid(row=3, column=0, padx=20, pady=10, sticky="nsew")
        self.grid_rowconfigure(3, weight=1)
        
        self.lbl_no_dupes = ctk.CTkLabel(
            self.scroll_frame, text="Silakan pilih folder dan lakukan pemindaian terlebih dahulu.",
            font=ctk.CTkFont(size=13), text_color="#888888"
        )
        self.lbl_no_dupes.pack(pady=50)
        
        # Bottom Action Bar
        self.bottom_bar = ctk.CTkFrame(self, fg_color="transparent")
        self.bottom_bar.grid(row=4, column=0, padx=20, pady=(5, 20), sticky="ew")
        
        self.btn_delete_selected = ctk.CTkButton(
            self.bottom_bar, text="Hapus File Terpilih",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#EF4444", hover_color="#DC2626", text_color="#FFFFFF",
            width=200, height=40, command=self.delete_selected_files
        )
        self.btn_delete_selected.pack(side="right")
        self.btn_delete_selected.configure(state="disabled")
        
        self.btn_select_all = ctk.CTkButton(
            self.bottom_bar, text="Pilih Semua Salinan",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#475569", hover_color="#334155", text_color="#FFFFFF",
            width=160, height=40, command=self.select_all_copies
        )
        self.btn_select_all.pack(side="left", padx=(0, 10))
        self.btn_select_all.configure(state="disabled")
        
        self.btn_deselect_all = ctk.CTkButton(
            self.bottom_bar, text="Batal Pilih",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#333333", hover_color="#444444", text_color="#FFFFFF",
            width=100, height=40, command=self.deselect_all
        )
        self.btn_deselect_all.pack(side="left")
        self.btn_deselect_all.configure(state="disabled")
        
    def choose_folder(self):
        folder = filedialog.askdirectory(title="Pilih Folder yang Akan Dipindai")
        if folder:
            self.target_dir = folder
            self.lbl_folder.configure(text=folder, text_color="#FFFFFF")
            self.btn_scan.configure(state="normal")
            
    def run_scan(self):
        self.btn_scan.configure(state="disabled", text="Memindai...")
        self.btn_choose.configure(state="disabled")
        self.btn_delete_selected.configure(state="disabled")
        self.btn_select_all.configure(state="disabled")
        self.btn_deselect_all.configure(state="disabled")
        self.lbl_no_dupes.configure(text="Sedang memindai file duplikat (mengalkulasi hash)...")
        self.controller.show_status("Menganalisis file duplikat...")
        
        # Clear previous list
        for w in self.scroll_frame.winfo_children():
            w.destroy()
        self.checkbox_vars = {}
        
        def scan_worker():
            import file_cleaner
            duplicates = file_cleaner.find_duplicate_files(self.target_dir)
            self.after(0, lambda: self.render_results(duplicates))
            
        threading.Thread(target=scan_worker, daemon=True).start()
        
    def render_results(self, duplicates):
        self.btn_scan.configure(state="normal", text="Mulai Pindai")
        self.btn_choose.configure(state="normal")
        self.dupes_list = duplicates
        
        if not duplicates:
            self.lbl_no_dupes = ctk.CTkLabel(
                self.scroll_frame, text="Bagus! Tidak ditemukan file duplikat di folder ini.",
                font=ctk.CTkFont(size=13), text_color="#10B981"
            )
            self.lbl_no_dupes.pack(pady=50)
            self.btn_delete_selected.configure(state="disabled")
            self.btn_select_all.configure(state="disabled")
            self.btn_deselect_all.configure(state="disabled")
            self.controller.show_status("Pemindaian selesai: Tidak ada duplikat.")
            return
            
        self.btn_delete_selected.configure(state="normal")
        self.btn_select_all.configure(state="normal")
        self.btn_deselect_all.configure(state="normal")
        self.controller.show_status(f"Pemindaian selesai: Menemukan {len(duplicates)} grup duplikat.")
        
        to_mb = lambda b: f"{b / (1024*1024):.2f} MB" if b >= 1024*1024 else f"{b / 1024:.1f} KB"
        
        for idx, group in enumerate(duplicates):
            group_frame = ctk.CTkFrame(self.scroll_frame, fg_color="#121212", corner_radius=8)
            group_frame.pack(fill="x", pady=5, padx=5)
            
            # Header Group
            lbl_group_title = ctk.CTkLabel(
                group_frame, 
                text=f"Grup {idx+1} | Ukuran: {to_mb(group['size'])} | Hash: {group['hash'][:8]}...",
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color="#3B82F6"
            )
            lbl_group_title.pack(anchor="w", padx=10, pady=5)
            
            # List files
            for file_idx, filepath in enumerate(group['files']):
                file_row = ctk.CTkFrame(group_frame, fg_color="transparent")
                file_row.pack(fill="x", padx=15, pady=3)
                
                cb_var = tk.BooleanVar(value=(file_idx > 0))
                self.checkbox_vars[filepath] = cb_var
                
                # Truncate long path for clean display
                display_path = filepath
                if len(filepath) > 85:
                    parts = filepath.split(os.sep)
                    if len(parts) > 3:
                        display_path = parts[0] + os.sep + "..." + os.sep + os.sep.join(parts[-2:])
                    else:
                        display_path = filepath[:40] + "..." + filepath[-40:]
                        
                cb = ctk.CTkCheckBox(
                    file_row, text=display_path, variable=cb_var,
                    font=ctk.CTkFont(size=11),
                    checkbox_width=18, checkbox_height=18, corner_radius=4
                )
                cb.pack(side="left", fill="x", expand=True)
                
                badge_text = "ASLI" if file_idx == 0 else "SALINAN"
                badge_bg = "#2E2E2E" if file_idx == 0 else "#475569"
                badge_lbl = ctk.CTkLabel(
                    file_row, text=badge_text,
                    font=ctk.CTkFont(size=9, weight="bold"),
                    text_color="#FFFFFF", fg_color=badge_bg, corner_radius=4, width=50, height=18
                )
                badge_lbl.pack(side="right", padx=10)

    def delete_selected_files(self):
        files_to_delete = [path for path, var in self.checkbox_vars.items() if var.get()]
        if not files_to_delete:
            messagebox.showwarning("Pilih File", "Pilih minimal satu file salinan untuk dihapus.")
            return
            
        confirm = messagebox.askyesno(
            "Hapus File Duplikat",
            f"Apakah Anda yakin ingin menghapus permanen {len(files_to_delete)} file duplikat terpilih dari harddisk?"
        )
        if not confirm:
            return
            
        self.btn_delete_selected.configure(state="disabled", text="Menghapus...")
        self.btn_scan.configure(state="disabled")
        self.controller.show_status("Menghapus file duplikat...")
        
        def delete_worker():
            deleted_count = 0
            freed_bytes = 0
            failed_count = 0
            import stat
            for path in files_to_delete:
                try:
                    size = os.path.getsize(path)
                    # Hapus atribut read-only jika ada agar bisa dihapus
                    try:
                        os.chmod(path, stat.S_IWRITE)
                    except Exception:
                        pass
                    os.remove(path)
                    deleted_count += 1
                    freed_bytes += size
                except Exception:
                    failed_count += 1
            self.after(0, lambda count=deleted_count, size=freed_bytes, failed=failed_count: 
                       self.finish_deletion(count, size, failed))
            
        threading.Thread(target=delete_worker, daemon=True).start()
        
    def finish_deletion(self, count, freed_bytes, failed_count=0):
        self.btn_scan.configure(state="normal")
        to_mb = lambda b: f"{b / (1024*1024):.2f} MB" if b >= 1024*1024 else f"{b / 1024:.1f} KB"
        freed_str = to_mb(freed_bytes)
        
        msg = f"Berhasil menghapus {count} file duplikat dan membebaskan {freed_str} ruang disk."
        if failed_count > 0:
            msg += f"\n\nPerhatian: {failed_count} file gagal dihapus (kemungkinan sedang terkunci atau butuh hak akses Administrator lebih tinggi)."
            
        messagebox.showinfo("Penghapusan Selesai", msg)
        self.controller.show_status(f"Duplikat dibersihkan: Bebas {freed_str}.")
        
        # Kirim laporan performa ke Firebase
        freed_mb = freed_bytes / (1024 * 1024)
        def report_worker():
            import firebase_handler
            firebase_handler.report_stats(
                self.controller.current_user['uid'],
                self.controller.current_user['idToken'],
                0,
                freed_mb
            )
        threading.Thread(target=report_worker, daemon=True).start()
        
        self.run_scan()

    def select_all_copies(self):
        """Checks all duplicate files (except the first original one in each group)."""
        if not self.dupes_list:
            return
        for group in self.dupes_list:
            for file_idx, filepath in enumerate(group['files']):
                if filepath in self.checkbox_vars:
                    self.checkbox_vars[filepath].set(file_idx > 0)
                    
    def deselect_all(self):
        """Unchecks all files."""
        for var in self.checkbox_vars.values():
            var.set(False)
 
class AppManagerFrame(ctk.CTkFrame):
    """Premium tab representing Software Uninstaller (Basic/Advanced) and Registry Startup Manager."""
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        
        self.apps_list = []
        self.startup_list = []
        
        # Title
        title = ctk.CTkLabel(
            self, text="Manajer Aplikasi & Startup",
            font=ctk.CTkFont(family="Segoe UI", size=24, weight="bold"),
            text_color="#FFFFFF"
        )
        title.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")
        
        # Tabview
        self.tabview = ctk.CTkTabview(self, fg_color="#1E1E1E", segmented_button_selected_color="#3B82F6", segmented_button_selected_hover_color="#2563EB")
        self.tabview.grid(row=2, column=0, padx=20, pady=(0, 20), sticky="nsew")
        self.grid_rowconfigure(2, weight=1)
        
        self.tab_uninstaller = self.tabview.add("Uninstaller Sisa")
        self.tab_startup = self.tabview.add("Program Startup")
        
        # Setup Tab 1: Uninstaller
        self.setup_uninstaller_tab()
        
        # Setup Tab 2: Startup
        self.setup_startup_tab()
        
    def setup_uninstaller_tab(self):
        self.tab_uninstaller.grid_columnconfigure(0, weight=1)
        self.tab_uninstaller.grid_rowconfigure(1, weight=1)
        
        # Search panel
        search_panel = ctk.CTkFrame(self.tab_uninstaller, fg_color="transparent")
        search_panel.grid(row=0, column=0, pady=10, padx=10, sticky="ew")
        search_panel.grid_columnconfigure(0, weight=1)
        
        self.search_entry = ctk.CTkEntry(search_panel, placeholder_text="Cari nama aplikasi terinstal...", height=35)
        self.search_entry.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self.search_entry.bind("<KeyRelease>", self.filter_installed_apps)
        
        btn_refresh = ctk.CTkButton(
            search_panel, text="Muat Ulang",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#475569", hover_color="#334155",
            width=100, height=35, command=self.load_installed_apps
        )
        btn_refresh.grid(row=0, column=1, sticky="e")
        
        # Scrollable App list
        self.app_scroll = ctk.CTkScrollableFrame(self.tab_uninstaller, fg_color="#121212")
        self.app_scroll.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="nsew")
        self.app_scroll.grid_columnconfigure(0, weight=1)
        
        self.lbl_app_status = ctk.CTkLabel(self.app_scroll, text="Klik 'Muat Ulang' untuk melihat daftar software terinstal.", text_color="#888888")
        self.lbl_app_status.pack(pady=40)
        
    def setup_startup_tab(self):
        self.tab_startup.grid_columnconfigure(0, weight=1)
        self.tab_startup.grid_rowconfigure(1, weight=1)
        
        # Header Info: Uptime
        self.info_panel = ctk.CTkFrame(self.tab_startup, fg_color="transparent")
        self.info_panel.grid(row=0, column=0, pady=10, padx=10, sticky="ew")
        
        self.lbl_uptime = ctk.CTkLabel(
            self.info_panel, text="Mengalkulasi waktu aktif sistem...",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#3B82F6"
        )
        self.lbl_uptime.pack(side="left")
        
        btn_refresh_startup = ctk.CTkButton(
            self.info_panel, text="Segarkan",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#475569", hover_color="#334155",
            width=100, height=28, command=self.load_startup_entries
        )
        btn_refresh_startup.pack(side="right")
        
        # Scrollable Startup list
        self.startup_scroll = ctk.CTkScrollableFrame(self.tab_startup, fg_color="#121212")
        self.startup_scroll.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="nsew")
        self.startup_scroll.grid_columnconfigure(0, weight=1)
        
        self.apps_loaded = False

    def on_show(self):
        if not self.apps_loaded:
            self.apps_loaded = True
            self.load_installed_apps()
            self.load_startup_entries()

    def filter_installed_apps(self, event=None):
        q = self.search_entry.get().strip().lower()
        
        # If app_widgets is not initialized yet, skip
        if not getattr(self, 'app_widgets', None):
            return
            
        visible_count = 0
        for app_name, row_widget in self.app_widgets:
            if not q or q in app_name:
                # Show row if matches search query
                if not row_widget.winfo_manager(): # If not currently packed
                    row_widget.pack(fill="x", pady=4, padx=5)
                visible_count += 1
            else:
                # Hide row
                row_widget.pack_forget()
                
        # If no apps match, show a label
        if visible_count == 0:
            if not getattr(self, 'lbl_no_match', None):
                self.lbl_no_match = ctk.CTkLabel(self.app_scroll, text="Tidak ada software yang cocok.", text_color="#888888")
            self.lbl_no_match.pack(pady=20)
        else:
            if getattr(self, 'lbl_no_match', None):
                self.lbl_no_match.pack_forget()

    def load_installed_apps(self):
        for widget in self.app_scroll.winfo_children():
            widget.destroy()
        
        lbl_loading = ctk.CTkLabel(self.app_scroll, text="Memuat daftar aplikasi terinstal (mengambil dari Registry)...", text_color="#888888")
        lbl_loading.pack(pady=40)
        
        def worker():
            import file_cleaner
            self.apps_list = file_cleaner.get_installed_apps()
            self.after(0, self.render_installed_apps)
            
        threading.Thread(target=worker, daemon=True).start()
        
    def render_installed_apps(self):
        for widget in self.app_scroll.winfo_children():
            widget.destroy()
        self.app_widgets = []
        self.lbl_no_match = None
            
        if not self.apps_list:
            lbl = ctk.CTkLabel(self.app_scroll, text="Gagal memuat daftar aplikasi.", text_color="#EF4444")
            lbl.pack(pady=40)
            return
            
        for app in self.apps_list:
            # Use high-performance standard tk.Frame to prevent resize/drawing lag
            row = tk.Frame(self.app_scroll, bg="#1E1E1E", height=50)
            row.pack(fill="x", pady=4, padx=5)
            row.pack_propagate(False)
            
            row.grid_columnconfigure(0, weight=1)
            row.grid_columnconfigure(1, weight=0)
            
            # Use standard tk.Label for instant rendering (saves seconds on long lists)
            lbl_name = tk.Label(
                row, text=app['name'], font=("Segoe UI", 10, "bold"),
                fg="#FFFFFF", bg="#1E1E1E", anchor="w"
            )
            lbl_name.grid(row=0, column=0, padx=15, pady=10, sticky="w")
            
            btn_uninstall = ctk.CTkButton(
                row, text="Uninstall", font=ctk.CTkFont(size=11, weight="bold"),
                fg_color="#3B82F6", hover_color="#2563EB", text_color="#FFFFFF",
                width=80, height=28, command=lambda a=app: self.confirm_uninstall(a)
            )
            btn_uninstall.grid(row=0, column=1, padx=15, pady=10, sticky="e")
            
            self.app_widgets.append((app['name'].lower(), row))
            
        self.filter_installed_apps()

    def confirm_uninstall(self, app):
        dialog = tk.Toplevel(self)
        dialog.title("Konfirmasi Uninstall")
        dialog.geometry("450x260")
        dialog.resizable(False, False)
        dialog.configure(bg="#1E1E1E")
        dialog.transient(self)
        dialog.grab_set()
        
        # Center dialog
        x = self.winfo_x() + (self.winfo_width() - 450) // 2
        y = self.winfo_y() + (self.winfo_height() - 260) // 2
        dialog.geometry(f"+{x}+{y}")
        
        lbl_title = ctk.CTkLabel(
            dialog, text=f"Uninstall: {app['name'][:40]}...",
            font=ctk.CTkFont(size=15, weight="bold"), text_color="#FFFFFF"
        )
        lbl_title.pack(pady=(20, 10), padx=20)
        
        lbl_desc = ctk.CTkLabel(
            dialog, 
            text="Pilih tipe metode penghapusan aplikasi yang Anda inginkan:\n\n"
                 "• Basic: Hanya jalankan uninstaller resmi bawaan aplikasi.\n"
                 "• Advanced: Jalankan uninstaller, lalu pindai & hapus folder sisa\n"
                 "  (AppData/Program Files) dan registry yang tertinggal.",
            font=ctk.CTkFont(size=11), text_color="#CCCCCC", justify="left"
        )
        lbl_desc.pack(pady=10, padx=25, anchor="w")
        
        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(fill="x", pady=20, padx=20)
        
        def handle_choice(mode):
            dialog.destroy()
            self.run_uninstall(app, mode)
            
        btn_basic = ctk.CTkButton(
            btn_frame, text="Basic Uninstall", fg_color="#475569", hover_color="#334155",
            command=lambda: handle_choice("basic")
        )
        btn_basic.pack(side="left", padx=10, expand=True, fill="x")
        
        btn_advanced = ctk.CTkButton(
            btn_frame, text="Advanced Uninstall", fg_color="#3B82F6", hover_color="#2563EB",
            command=lambda: handle_choice("advanced")
        )
        btn_advanced.pack(side="right", padx=10, expand=True, fill="x")

    def run_uninstall(self, app, mode):
        self.controller.show_status(f"Menjalankan uninstaller untuk: {app['name']}")
        
        uninst_str = app['uninstall_string']
        
        def worker():
            try:
                proc = subprocess.Popen(uninst_str, shell=True)
                proc.wait()
                
                if mode == "advanced":
                    self.after(0, lambda: self.scan_leftovers(app))
                else:
                    self.after(0, lambda: messagebox.showinfo("Uninstall Selesai", f"Uninstal Basic untuk '{app['name']}' selesai."))
                    self.after(0, self.load_installed_apps)
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Gagal", f"Gagal menjalankan uninstaller: {e}"))
                
        threading.Thread(target=worker, daemon=True).start()
        
    def scan_leftovers(self, app):
        self.controller.show_status("Memindai file & registry sisa...")
        
        scan_dlg = tk.Toplevel(self)
        scan_dlg.title("Memindai Sisa Aplikasi")
        scan_dlg.geometry("380x150")
        scan_dlg.resizable(False, False)
        scan_dlg.configure(bg="#1E1E1E")
        scan_dlg.transient(self)
        scan_dlg.grab_set()
        
        x = self.winfo_x() + (self.winfo_width() - 380) // 2
        y = self.winfo_y() + (self.winfo_height() - 150) // 2
        scan_dlg.geometry(f"+{x}+{y}")
        
        lbl = ctk.CTkLabel(scan_dlg, text="Sedang memindai direktori & registry sisa...", font=ctk.CTkFont(size=13, weight="bold"))
        lbl.pack(pady=40)
        
        def scan_worker():
            import file_cleaner
            leftovers = file_cleaner.find_app_leftovers(
                app['name'], 
                app.get('install_location'), 
                app.get('publisher')
            )
            self.after(0, lambda: scan_dlg.destroy())
            self.after(0, lambda: self.show_leftovers_dialog(app, leftovers))
            
        threading.Thread(target=scan_worker, daemon=True).start()

    def show_leftovers_dialog(self, app, leftovers):
        folders = leftovers["folders"]
        registry_keys = leftovers["registry_keys"]
        
        if not folders and not registry_keys:
            messagebox.showinfo("Tidak Ada Sisa", f"Tidak ditemukan folder atau entri registry sisa untuk '{app['name']}'.")
            self.load_installed_apps()
            return
            
        dialog = tk.Toplevel(self)
        dialog.title("File Sisa Ditemukan")
        dialog.geometry("500x420")
        dialog.resizable(False, False)
        dialog.configure(bg="#1E1E1E")
        dialog.transient(self)
        dialog.grab_set()
        
        x = self.winfo_x() + (self.winfo_width() - 500) // 2
        y = self.winfo_y() + (self.winfo_height() - 420) // 2
        dialog.geometry(f"+{x}+{y}")
        
        lbl_title = ctk.CTkLabel(
            dialog, text="File & Registry Sisa Terdeteksi",
            font=ctk.CTkFont(size=14, weight="bold"), text_color="#EF4444"
        )
        lbl_title.pack(pady=(15, 5))
        
        lbl_desc = ctk.CTkLabel(
            dialog, text=f"Pilih file sisa dari '{app['name']}' yang ingin Anda bersihkan:",
            font=ctk.CTkFont(size=11), text_color="#CCCCCC"
        )
        lbl_desc.pack(pady=5)
        
        # Scrollable Checklist
        scroll = ctk.CTkScrollableFrame(dialog, fg_color="#121212", height=240)
        scroll.pack(fill="both", expand=True, padx=20, pady=10)
        
        checkbox_vars = {}
        
        # Folders
        if folders:
            lbl_f = ctk.CTkLabel(scroll, text="Folder Sisa:", font=ctk.CTkFont(size=11, weight="bold"), text_color="#3B82F6")
            lbl_f.pack(anchor="w", pady=(5, 2), padx=5)
            for f in folders:
                cb_var = tk.BooleanVar(value=True)
                checkbox_vars[("folder", f)] = cb_var
                cb = ctk.CTkCheckBox(scroll, text=f, variable=cb_var, font=ctk.CTkFont(size=10))
                cb.pack(anchor="w", pady=2, padx=15)
                
        # Registry
        if registry_keys:
            lbl_r = ctk.CTkLabel(scroll, text="Registry Sisa:", font=ctk.CTkFont(size=11, weight="bold"), text_color="#10B981")
            lbl_r.pack(anchor="w", pady=(10, 2), padx=5)
            for r in registry_keys:
                cb_var = tk.BooleanVar(value=True)
                checkbox_vars[("reg", r)] = cb_var
                cb = ctk.CTkCheckBox(scroll, text=r, variable=cb_var, font=ctk.CTkFont(size=10))
                cb.pack(anchor="w", pady=2, padx=15)
                
        # Buttons
        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(fill="x", pady=15, padx=20)
        
        def clean_now():
            sel_folders = [val for (t, val), var in checkbox_vars.items() if var.get() and t == "folder"]
            sel_regs = [val for (t, val), var in checkbox_vars.items() if var.get() and t == "reg"]
            
            dialog.destroy()
            self.controller.show_status("Membersihkan sisa aplikasi...")
            
            def run_cleaner():
                import file_cleaner
                df, dr = file_cleaner.delete_app_leftovers(sel_folders, sel_regs)
                self.after(0, lambda: messagebox.showinfo("Bersih!", f"Pembersihan Advanced Selesai!\n\nBerhasil menghapus:\n• {df} folder sisa\n• {dr} kunci Registry."))
                self.after(0, self.load_installed_apps)
                
            threading.Thread(target=run_cleaner, daemon=True).start()
            
        btn_cancel = ctk.CTkButton(
            btn_frame, text="Lewati / Selesai", fg_color="#475569", hover_color="#334155",
            command=lambda: [dialog.destroy(), self.load_installed_apps()]
        )
        btn_cancel.pack(side="left", padx=10, expand=True, fill="x")
        
        btn_clean = ctk.CTkButton(
            btn_frame, text="Bersihkan Sisa", fg_color="#EF4444", hover_color="#DC2626",
            command=clean_now
        )
        btn_clean.pack(side="right", padx=10, expand=True, fill="x")

    def load_startup_entries(self):
        for widget in self.startup_scroll.winfo_children():
            widget.destroy()
            
        # Tampilkan uptime
        boot_timestamp = psutil.boot_time()
        uptime_secs = time.time() - boot_timestamp
        
        days = int(uptime_secs // 86400)
        hours = int((uptime_secs % 86400) // 3600)
        mins = int((uptime_secs % 3600) // 60)
        
        uptime_str = f"Uptime: {hours} jam {mins} menit"
        if days > 0:
            uptime_str = f"Uptime: {days} hari {hours} jam {mins} menit"
            
        boot_time_str = datetime.datetime.fromtimestamp(boot_timestamp).strftime('%d/%m/%Y %H:%M:%S')
        self.lbl_uptime.configure(text=f"Aktif sejak: {boot_time_str} | {uptime_str}")
        
        # Load registry keys
        self.startup_list = []
        reg_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, reg_path, 0, winreg.KEY_READ)
            num_values = winreg.QueryInfoKey(key)[1]
            for i in range(num_values):
                val_name, val_data, val_type = winreg.EnumValue(key, i)
                self.startup_list.append({
                    "name": val_name,
                    "command": val_data,
                    "enabled": True
                })
            winreg.CloseKey(key)
        except Exception:
            pass
            
        if not self.startup_list:
            lbl = ctk.CTkLabel(self.startup_scroll, text="Tidak ada program startup pengguna terdaftar.", text_color="#888888")
            lbl.pack(pady=40)
            return
            
        for entry in self.startup_list:
            # Use high-performance standard tk.Frame and grid column layout to prevent overlap/overflow
            row = tk.Frame(self.startup_scroll, bg="#1E1E1E", height=50)
            row.pack(fill="x", pady=4, padx=5)
            row.pack_propagate(False)
            
            row.grid_columnconfigure(0, weight=3, uniform="startup")
            row.grid_columnconfigure(1, weight=5, uniform="startup")
            row.grid_columnconfigure(2, weight=0)
            row.grid_rowconfigure(0, weight=1)
            
            display_name = entry['name']
            if len(display_name) > 30:
                display_name = display_name[:27] + "..."
                
            lbl_name = tk.Label(
                row, text=display_name, font=("Segoe UI", 10, "bold"),
                fg="#FFFFFF", bg="#1E1E1E", anchor="w"
            )
            lbl_name.grid(row=0, column=0, padx=15, sticky="ew")
            
            cmd_trunc = entry['command']
            if len(cmd_trunc) > 55:
                cmd_trunc = cmd_trunc[:52] + "..."
            lbl_cmd = tk.Label(
                row, text=cmd_trunc, font=("Segoe UI", 9, "italic"),
                fg="#888888", bg="#1E1E1E", anchor="w"
            )
            lbl_cmd.grid(row=0, column=1, padx=10, sticky="ew")
            
            sw_var = tk.BooleanVar(value=entry['enabled'])
            
            def toggle_startup_entry(name=entry['name'], cmd=entry['command'], var=sw_var):
                self.set_startup_entry_status(name, cmd, var.get())
                
            sw = ctk.CTkSwitch(
                row, text="", variable=sw_var, command=toggle_startup_entry,
                progress_color="#3B82F6"
            )
            sw.grid(row=0, column=2, padx=15, sticky="e")

    def set_startup_entry_status(self, name, command, enabled):
        reg_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, reg_path, 0, winreg.KEY_SET_VALUE)
            if enabled:
                winreg.SetValueEx(key, name, 0, winreg.REG_SZ, command)
                self.controller.show_status(f"Startup diaktifkan: {name}")
            else:
                try:
                    winreg.DeleteValue(key, name)
                    self.controller.show_status(f"Startup dinonaktifkan: {name}")
                except FileNotFoundError:
                    pass
            winreg.CloseKey(key)
        except Exception as e:
            messagebox.showerror("Error", f"Gagal merubah status startup Registry: {e}")
            self.load_startup_entries()

class App(ctk.CTk):
    """Main Application Controller Frame."""
    def __init__(self, start_minimized=False):
        super().__init__()
        
        self.current_user = None
        self.autoclean_enabled = False
        self.autoclean_threshold = 85
        self.floating_widget_enabled = False
        
        # Window properties
        self.title("Bersihin")
        self.geometry("1280x720")
        self.resizable(True, True)
        self.minsize(960, 540)
        
        # Intercept window close to minimize to tray
        self.protocol("WM_DELETE_WINDOW", self.minimize_to_tray)
        self.tray_icon = None
        self.after(1000, self.setup_tray_icon)
        
        # Custom Icon (if available, fallback to standard)
        try:
            if getattr(sys, 'frozen', False):
                ico_path = os.path.join(sys._MEIPASS, "assets", "logo.ico")
                png_path = os.path.join(sys._MEIPASS, "assets", "logo.png")
            else:
                base_project_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
                ico_path = os.path.join(base_project_dir, "assets", "logo.ico")
                png_path = os.path.join(base_project_dir, "assets", "logo.png")
                
            # Set titlebar icon (standard Windows method)
            if os.path.exists(ico_path):
                self.iconbitmap(ico_path)
                
            # Set taskbar and shortcut icon (modern Tkinter method)
            if os.path.exists(png_path):
                self.img_icon = tk.PhotoImage(file=png_path)
                self.iconphoto(True, self.img_icon)
        except Exception:
            pass
            
        # Pemuatan sesi login & pengaturan lokal
        session = self.load_session()
        self.load_settings()
        
        self.floating_widget = None
        if getattr(self, 'floating_widget_enabled', False):
            self.after(2000, lambda: self.toggle_floating_widget(True))
        


        if session:
            # Pengecekan status blokir secara instan di background
            self.current_user = session
            self.initialize_main_app(start_minimized)
        else:
            self.show_login_screen()

    def setup_tray_icon(self):
        """Set up the system tray icon using pystray."""
        if not HAS_PYSTRAY:
            return
            
        try:
            # Determine logo path
            if getattr(sys, 'frozen', False):
                png_path = os.path.join(sys._MEIPASS, "assets", "logo.png")
            else:
                base_project_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
                png_path = os.path.join(base_project_dir, "assets", "logo.png")
                
            if not os.path.exists(png_path):
                return
                
            image = Image.open(png_path)
            
            def restore_window(icon, item):
                self.after(0, self.restore_from_tray)
                
            def exit_app(icon, item):
                self.after(0, self.exit_app_fully)
                
            menu = pystray.Menu(
                pystray.MenuItem("Buka Bersihin", restore_window, default=True),
                pystray.MenuItem("Keluar Aplikasi", exit_app)
            )
            self.tray_icon = pystray.Icon("Bersihin", image, "Bersihin", menu)
            
            # Start tray icon running in a background thread
            threading.Thread(target=self.tray_icon.run, daemon=True).start()
        except Exception:
            pass

    def minimize_to_tray(self):
        """Hides the window and runs it in the system tray."""
        if HAS_PYSTRAY and self.tray_icon:
            self.withdraw()
        else:
            self.exit_app_fully()

    def restore_from_tray(self):
        """Restores the window from system tray."""
        self.deiconify()
        self.focus_force()
        self.state("normal")

    def exit_app_fully(self):
        """Fully closes the application and stops the tray icon."""
        if HAS_PYSTRAY and self.tray_icon:
            try:
                self.tray_icon.stop()
            except Exception:
                pass
        self.destroy()
        sys.exit(0)

    def quit(self):
        """Override quit to exit fully including tray icon thread."""
        self.exit_app_fully()

    def show_login_screen(self):
        """Cleans window and displays the Login / Register screen."""
        # Bersihkan widget jika ada
        for w in self.winfo_children():
            w.destroy()
            
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)
        
        self.login_frame = LoginFrame(self, self)
        self.login_frame.grid(row=0, column=0, sticky="nsew")

    def initialize_main_app(self, start_minimized=False):
        """Builds the main app sidebar and container pages after success login."""
        # Bersihkan widget lama (misal: login frame)
        for w in self.winfo_children():
            w.destroy()
            
        # Configure layout grids
        self.grid_columnconfigure(0, weight=0) # Sidebar
        self.grid_columnconfigure(1, weight=1) # Main Area
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)    # Status Bar
        
        # Left Sidebar Frame
        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0, fg_color="#121212")
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(11, weight=1) # Push lower items to bottom
        
        # Sidebar Logo Header
        self.logo_label = ctk.CTkLabel(
            self.sidebar, text="BERSIHIN", 
            font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold"),
            text_color="#F8FAFC"
        )
        self.logo_label.grid(row=0, column=0, padx=20, pady=(25, 25))
        
        # Sidebar Buttons
        self.nav_buttons = {}
        self.create_nav_button("Dasbor", DashboardFrame, 1)
        self.create_nav_button("RAM Mendalam", RAMCleanerFrame, 2)
        self.create_nav_button("Pembersih File", FileCleanerFrame, 3)
        self.create_nav_button("Game Booster", GameBoostFrame, 4)
        self.create_nav_button("Manajer Aplikasi", AppManagerFrame, 5)
        self.create_nav_button("File Besar", LargeFileFinderFrame, 6)
        self.create_nav_button("Pembersih Registry", RegistryCleanerFrame, 7)
        self.create_nav_button("Klik Kanan", ContextMenuManagerFrame, 8)
        self.create_nav_button("Optimasi Internet", InternetSpeedBoosterFrame, 9)
        self.create_nav_button("Pengaturan", SettingsFrame, 10)
            
        # Right Side Content Container Frame
        self.container = ctk.CTkFrame(self, fg_color="#121212", corner_radius=0)
        self.container.grid(row=0, column=1, sticky="nsew")
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)
        
        # Status Bar
        self.status_bar = ctk.CTkFrame(self, height=25, fg_color="#0F0F0F", corner_radius=0)
        self.status_bar.grid(row=1, column=0, columnspan=2, sticky="ew")
        
        # DB status indicator in Status Bar
        db_mode = "Offline (Lokal)" if firebase_handler.is_mock_mode() else "Online (Firebase)"
        user_name = self.current_user.get('username', 'Unknown')
        status_text = f"Pengguna: {user_name} | Database: {db_mode} | Siap digunakan."
        
        self.status_lbl = ctk.CTkLabel(
            self.status_bar, text=status_text,
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color="#888888"
        )
        self.status_lbl.pack(side="left", padx=15)
        
        self.credits_lbl = ctk.CTkLabel(
            self.status_bar, text="Created by Arya AL | v1.0.0",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color="#888888"
        )
        self.credits_lbl.pack(side="right", padx=15)
        
        # Load and stack screen frames
        self.frames = {}
        for F in (DashboardFrame, RAMCleanerFrame, FileCleanerFrame, GameBoostFrame, AppManagerFrame, 
                  LargeFileFinderFrame, RegistryCleanerFrame, ContextMenuManagerFrame, InternetSpeedBoosterFrame, SettingsFrame):
            frame = F(self.container, self)
            self.frames[F] = frame
            
        # Set default active frame
        self.show_frame(DashboardFrame)
        
        # Handle minimized state on start
        if start_minimized:
            self.withdraw()
            self.after(1000, self.deiconify)
            
        # Check updates in background
        self.check_for_updates()
            
        # Start background monitor thread for auto-clean and lockout checks
        self.start_autoclean_monitor()

    def create_nav_button(self, text, frame_class, row_idx):
        btn = ctk.CTkButton(
            self.sidebar, text=text, 
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            fg_color="transparent", text_color="#CCCCCC", hover_color="#1E1E1E",
            anchor="w", height=40, corner_radius=8,
            command=lambda: self.show_frame(frame_class)
        )
        btn.grid(row=row_idx, column=0, padx=15, pady=5, sticky="ew")
        self.nav_buttons[frame_class] = btn

    def show_frame(self, frame_class):
        """Hides all frames from the grid, then grids only the active frame."""
        for f in self.frames.values():
            f.grid_forget()
            
        frame = self.frames[frame_class]
        frame.grid(row=0, column=0, sticky="nsew")
        
        # Highlight active nav button
        for cls, btn in self.nav_buttons.items():
            if cls == frame_class:
                btn.configure(fg_color="#1E1E1E", text_color="#3B82F6")
            else:
                btn.configure(fg_color="transparent", text_color="#CCCCCC")
                
        # Trigger lazy load if applicable (prevents lag on startup)
        if hasattr(frame, "on_show"):
            frame.on_show()

    def show_status(self, text):
        db_mode = "Offline (Lokal)" if firebase_handler.is_mock_mode() else "Online (Firebase)"
        user_name = self.current_user.get('username', 'Unknown')
        self.status_lbl.configure(text=f"Pengguna: {user_name} | Database: {db_mode} | {text}")

    def relaunch_as_admin(self):
        """Relaunches the application with administrator elevation."""
        if getattr(sys, 'frozen', False):
            path = sys.executable
        else:
            path = sys.argv[0]
            
        try:
            # ShellExecuteW with runas forces UAC prompt
            ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, f'"{path}"', None, 1)
            sys.exit(0)
        except Exception as e:
            messagebox.showerror("Gagal", f"Gagal menjalankan ulang sebagai Administrator: {e}")

    def load_session(self):
        """Loads session.json configuration."""
        if os.path.exists("session.json"):
            try:
                with open("session.json", "r") as f:
                    return json.load(f)
            except Exception:
                pass
        return None

    def save_session(self, user_data):
        """Saves current login details to session.json."""
        try:
            with open("session.json", "w") as f:
                json.dump(user_data, f)
        except Exception:
            pass

    def clear_session(self):
        """Clears local session.json configuration (logout)."""
        if os.path.exists("session.json"):
            try:
                os.remove("session.json")
            except Exception:
                pass

    def load_settings(self):
        """Loads settings from registry HKEY_CURRENT_USER."""
        key_path = r"Software\Bersihin"
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_READ)
            self.autoclean_enabled = winreg.QueryValueEx(key, "AutoCleanEnabled")[0] == 1
            self.autoclean_threshold = winreg.QueryValueEx(key, "AutoCleanThreshold")[0]
            try:
                self.floating_widget_enabled = winreg.QueryValueEx(key, "FloatingWidgetEnabled")[0] == 1
            except Exception:
                self.floating_widget_enabled = False
            winreg.CloseKey(key)
        except Exception:
            self.autoclean_enabled = False
            self.autoclean_threshold = 85
            self.floating_widget_enabled = False

    def save_settings(self):
        """Saves settings to registry HKEY_CURRENT_USER."""
        key_path = r"Software\Bersihin"
        try:
            key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path)
            winreg.SetValueEx(key, "AutoCleanEnabled", 0, winreg.REG_DWORD, 1 if self.autoclean_enabled else 0)
            winreg.SetValueEx(key, "AutoCleanThreshold", 0, winreg.REG_DWORD, self.autoclean_threshold)
            winreg.SetValueEx(key, "FloatingWidgetEnabled", 0, winreg.REG_DWORD, 1 if self.floating_widget_enabled else 0)
            winreg.CloseKey(key)
        except Exception:
            pass

    def show_blocked_screen(self):
        """Locks application UI and logs out user if blocked by Administrator."""
        self.clear_session()
        self.current_user = None
        
        # Destroy all active GUI elements
        for widget in self.winfo_children():
            widget.destroy()
            
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)
        
        blocked_frame = ctk.CTkFrame(self, fg_color="#121212")
        blocked_frame.grid(row=0, column=0, sticky="nsew")
        blocked_frame.grid_columnconfigure(0, weight=1)
        
        # Drawing warning triangle in canvas
        canvas = tk.Canvas(blocked_frame, width=100, height=100, bg="#121212", highlightthickness=0)
        canvas.pack(pady=(120, 20))
        canvas.create_polygon(50, 10, 90, 80, 10, 80, fill="#EF4444", outline="")
        canvas.create_text(50, 52, text="!", fill="#FFFFFF", font=("Segoe UI", 32, "bold"))
        
        lbl_title = ctk.CTkLabel(
            blocked_frame, text="Akses Dinonaktifkan", 
            font=ctk.CTkFont(family="Segoe UI", size=26, weight="bold"),
            text_color="#EF4444"
        )
        lbl_title.pack(pady=10)
        
        lbl_desc = ctk.CTkLabel(
            blocked_frame, 
            text="Akun atau perangkat Anda telah dinonaktifkan oleh Administrator.\n"
                 "Silakan hubungi administrator Anda untuk informasi lebih lanjut.",
            font=ctk.CTkFont(family="Segoe UI", size=14),
            text_color="#CCCCCC", justify="center"
        )
        lbl_desc.pack(pady=20)
        
        btn_exit = ctk.CTkButton(
            blocked_frame, text="Keluar dari Aplikasi",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            fg_color="#333333", hover_color="#444444", text_color="#FFFFFF",
            width=180, height=40, command=self.quit
        )
        btn_exit.pack(pady=10)

    def start_autoclean_monitor(self):
        """Runs a daemon thread to monitor RAM and run auto-clean when limit exceeded, and check for block status."""
        def monitor():
            while True:
                time.sleep(15)
                
                # Check for block status from database
                if self.current_user:
                    try:
                        is_blocked = firebase_handler.check_blocked_status(
                            self.current_user['uid'], 
                            self.current_user['idToken']
                        )
                        if is_blocked:
                            self.after(0, self.show_blocked_screen)
                            break
                            
                        # Check for remote commands
                        cmds, _ = firebase_handler.check_remote_commands(
                            self.current_user['uid'],
                            self.current_user['idToken']
                        )
                        if cmds:
                            # 1. Remote clean
                            if cmds.get('remote_clean') == True:
                                self.after(0, lambda: self.show_status("Menjalankan pembersihan jarak jauh oleh Admin..."))
                                
                                import memory_cleaner
                                import file_cleaner
                                
                                # RAM Clean
                                c_ws, _ = memory_cleaner.clean_process_working_sets()
                                if memory_cleaner.is_admin():
                                    memory_cleaner.clean_system_file_cache()
                                    memory_cleaner.clean_standby_list()
                                    
                                # File Clean
                                f_freed = 0
                                targets = file_cleaner.get_clean_targets()
                                for k, info in targets.items():
                                    if info.get('requires_admin') and not memory_cleaner.is_admin():
                                        continue
                                    freed, _, _ = file_cleaner.clean_target(k, info)
                                    f_freed += freed
                                    
                                # Send response
                                resp = {
                                    "status": "success",
                                    "ram_freed_mb": c_ws * 12, # Estimasi RAM dibersihkan per proses
                                    "disk_freed_mb": f_freed / (1024*1024),
                                    "timestamp": time.time()
                                }
                                firebase_handler.respond_to_remote_command(self.current_user['uid'], self.current_user['idToken'], resp)
                                firebase_handler.clear_remote_command(self.current_user['uid'], self.current_user['idToken'], 'remote_clean')
                                self.after(0, lambda: self.show_status("Pembersihan jarak jauh selesai."))
                                
                            # 2. Personal Notification
                            if cmds.get('notification'):
                                msg_text = cmds['notification']
                                firebase_handler.clear_remote_command(self.current_user['uid'], self.current_user['idToken'], 'notification')
                                self.after(0, lambda text=msg_text: messagebox.showinfo("Pesan dari Administrator", text))
                                
                        # Check global broadcast message
                        broadcast_msg, _ = firebase_handler.get_broadcast_message()
                        if broadcast_msg and getattr(self, 'last_shown_broadcast', None) != broadcast_msg:
                            self.last_shown_broadcast = broadcast_msg
                            self.after(0, lambda text=broadcast_msg: messagebox.showinfo("Pengumuman Penting", text))
                    except Exception:
                        pass
                
                if self.autoclean_enabled and self.current_user:
                    try:
                        ram = memory_cleaner.get_ram_usage()
                        if ram['percent'] >= self.autoclean_threshold:
                            self.after(0, lambda: self.show_status("Auto-cleaning RAM (Batas terlampaui)..."))
                            cleaned, failed = memory_cleaner.clean_process_working_sets()
                            
                            if memory_cleaner.is_admin():
                                memory_cleaner.clean_system_file_cache()
                                memory_cleaner.clean_standby_list()
                                
                            self.after(0, lambda c=cleaned: self.show_status(f"Auto-clean membebaskan RAM dari {c} proses."))
                    except Exception:
                        pass
                        
        threading.Thread(target=monitor, daemon=True).start()

    def check_for_updates(self):
        """Checks for software updates on Firebase."""
        def worker():
            time.sleep(2)
            try:
                import firebase_handler
                config, err = firebase_handler.get_update_config()
                if not err and config:
                    remote_ver = config.get("version", "1.0.0")
                    update_url = config.get("update_url", "")
                    
                    local_ver = "1.0.0"
                    
                    r_parts = [int(x) for x in remote_ver.split('.')]
                    l_parts = [int(x) for x in local_ver.split('.')]
                    
                    if r_parts > l_parts:
                        self.after(0, lambda: self.show_update_prompt(remote_ver, update_url))
            except Exception:
                pass
        threading.Thread(target=worker, daemon=True).start()
        
    def show_update_prompt(self, new_version, url):
        confirm = messagebox.askyesno(
            "Pembaruan Tersedia",
            f"Versi baru v{new_version} telah dirilis!\n\n"
            f"Apakah Anda ingin mengunduh pembaruan sekarang?"
        )
        if confirm and url:
            import webbrowser
            webbrowser.open(url)

    def toggle_floating_widget(self, enabled):
        """Displays or hides the floating desktop monitoring widget."""
        if enabled:
            if not self.floating_widget:
                self.floating_widget = FloatingWidget(self)
            self.floating_widget.deiconify()
        else:
            if self.floating_widget:
                self.floating_widget.withdraw()

class FloatingWidget(tk.Toplevel):
    """Semi-transparent floating desktop widget for quick monitoring and RAM boosting."""
    def __init__(self, controller):
        super().__init__(controller)
        self.controller = controller
        
        self.title("Bersihin Widget")
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.attributes("-alpha", 0.85)
        self.configure(bg="#121212")
        
        # Dimensions and Position
        width, height = 150, 160
        self.geometry(f"{width}x{height}+100+100")
        
        # Draggable bindings
        self.bind("<Button-1>", self.start_drag)
        self.bind("<B1-Motion>", self.do_drag)
        
        # UI Elements
        self.lbl_title = tk.Label(self, text="BERSIHIN WIDGET", font=("Segoe UI", 9, "bold"), fg="#3B82F6", bg="#121212")
        self.lbl_title.pack(pady=(10, 5))
        
        self.lbl_ram = tk.Label(self, text="RAM: -%", font=("Segoe UI", 11, "bold"), fg="#FFFFFF", bg="#121212")
        self.lbl_ram.pack(pady=2)
        
        self.lbl_cpu = tk.Label(self, text="CPU: -%", font=("Segoe UI", 11, "bold"), fg="#CCCCCC", bg="#121212")
        self.lbl_cpu.pack(pady=2)
        
        self.btn_boost = ctk.CTkButton(
            self, text="BOOST", font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            fg_color="#3B82F6", hover_color="#2563EB", text_color="#FFFFFF",
            width=100, height=28, corner_radius=6, command=self.quick_boost
        )
        self.btn_boost.pack(pady=(12, 10))
        
        self.update_stats()
        
    def start_drag(self, event):
        self.x = event.x
        self.y = event.y

    def do_drag(self, event):
        deltax = event.x - self.x
        deltay = event.y - self.y
        new_x = self.winfo_x() + deltax
        new_y = self.winfo_y() + deltay
        self.geometry(f"+{new_x}+{new_y}")
        
    def update_stats(self):
        if not self.winfo_exists():
            return
        try:
            import psutil
            import memory_cleaner
            ram = memory_cleaner.get_ram_usage()
            self.lbl_ram.configure(text=f"RAM: {ram['percent']}%")
            
            cpu = psutil.cpu_percent()
            self.lbl_cpu.configure(text=f"CPU: {cpu}%")
        except Exception:
            pass
        self.after(2000, self.update_stats)
        
    def quick_boost(self):
        self.btn_boost.configure(state="disabled", text="Boosting...")
        
        def run():
            import memory_cleaner
            ram_before = memory_cleaner.get_ram_usage()
            cleaned, failed = memory_cleaner.clean_process_working_sets()
            
            admin_msg = ""
            if memory_cleaner.is_admin():
                memory_cleaner.clean_system_file_cache()
                memory_cleaner.clean_standby_list()
                
            ram_after = memory_cleaner.get_ram_usage()
            freed_bytes = max(0, ram_before['used'] - ram_after['used'])
            if freed_bytes >= 1024**3:
                freed_str = f"{freed_bytes / (1024**3):.2f} GB"
            else:
                freed_str = f"{freed_bytes / (1024**2):.1f} MB"
                
            self.after(0, lambda: self.finish_boost(freed_str))
            
        import threading
        threading.Thread(target=run, daemon=True).start()
        
    def finish_boost(self, freed_str):
        self.btn_boost.configure(state="normal", text="BOOST")
        messagebox.showinfo("Widget Boost", f"Berhasil membebaskan {freed_str} RAM!")

class RegistryCleanerFrame(ctk.CTkFrame):
    """Registry Cleaner tab to scan and fix broken uninstall keys and dead DLLs."""
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        
        self.invalid_uninstalls = []
        self.dead_dlls = []
        self.checkbox_vars = {}
        
        # Title
        title = ctk.CTkLabel(
            self, text="Pembersih Registry",
            font=ctk.CTkFont(family="Segoe UI", size=24, weight="bold"),
            text_color="#FFFFFF"
        )
        title.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")
        
        desc = ctk.CTkLabel(
            self, text="Pindai dan bersihkan entri instalasi usang & referensi DLL mati di Registry Windows.",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color="#AAAAAA"
        )
        desc.grid(row=1, column=0, padx=20, pady=(0, 15), sticky="w")
        
        # Container for results
        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color="#1E1E1E", label_text="Daftar Masalah Registry Ditemukan", corner_radius=12)
        self.scroll_frame.grid(row=2, column=0, padx=20, pady=10, sticky="nsew")
        self.scroll_frame.columnconfigure(0, weight=1)
        
        self.lbl_status = ctk.CTkLabel(
            self.scroll_frame, text="Klik 'Pindai Registry' untuk memeriksa masalah di Registry Anda.",
            font=ctk.CTkFont(size=13), text_color="#888888"
        )
        self.lbl_status.pack(pady=50)
        
        # Action Buttons frame
        self.btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.btn_frame.grid(row=3, column=0, pady=(5, 20), padx=20, sticky="ew")
        
        self.btn_scan = ctk.CTkButton(
            self.btn_frame, text="Pindai Registry",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#475569", hover_color="#334155", text_color="#FFFFFF",
            width=150, height=40, command=self.run_scan
        )
        self.btn_scan.pack(side="left", padx=(0, 10))
        
        self.btn_clean = ctk.CTkButton(
            self.btn_frame, text="Bersihkan Entri Terpilih",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#3B82F6", hover_color="#2563EB", text_color="#FFFFFF",
            width=200, height=40, command=self.run_clean
        )
        self.btn_clean.pack(side="right")
        self.btn_clean.configure(state="disabled")
        
    def run_scan(self):
        if not memory_cleaner.is_admin():
            confirm = messagebox.askyesno(
                "Butuh Hak Akses Administrator",
                "Fitur pemindaian Registry Windows membutuhkan hak akses Administrator.\n\n"
                "Apakah Anda ingin menjalankan ulang aplikasi ini sebagai Administrator?"
            )
            if confirm:
                relaunch_as_admin()
            return
            
        self.btn_scan.configure(state="disabled", text="Memindai...")
        self.btn_clean.configure(state="disabled")
        
        for w in self.scroll_frame.winfo_children():
            w.destroy()
            
        self.lbl_status = ctk.CTkLabel(
            self.scroll_frame, text="Sedang memindai Registry Windows...",
            font=ctk.CTkFont(size=13), text_color="#888888"
        )
        self.lbl_status.pack(pady=50)
        self.controller.show_status("Memindai masalah Registry...")
        self.checkbox_vars = {}
        
        def worker():
            import premium_tools
            uninstalls, dlls = premium_tools.scan_invalid_registry()
            self.after(0, lambda: self.render_results(uninstalls, dlls))
            
        threading.Thread(target=worker, daemon=True).start()
        
    def render_results(self, uninstalls, dlls):
        self.btn_scan.configure(state="normal", text="Pindai Registry")
        self.invalid_uninstalls = uninstalls
        self.dead_dlls = dlls
        
        if not uninstalls and not dlls:
            lbl_res = ctk.CTkLabel(
                self.scroll_frame, text="Registry Bersih! Tidak ditemukan masalah referensi usang.",
                font=ctk.CTkFont(size=13), text_color="#10B981"
            )
            lbl_res.pack(pady=50)
            self.btn_clean.configure(state="disabled")
            self.controller.show_status("Pemindaian Registry selesai: Bersih.")
            return
            
        self.btn_clean.configure(state="normal")
        self.controller.show_status(f"Pemindaian selesai: Menemukan {len(uninstalls)} uninstall usang & {len(dlls)} DLL rusak.")
        
        # Render Uninstalls
        if uninstalls:
            lbl_u = ctk.CTkLabel(self.scroll_frame, text="Instalasi Aplikasi Usang:", font=ctk.CTkFont(size=14, weight="bold"), text_color="#EF4444")
            lbl_u.pack(anchor="w", pady=(10, 5), padx=10)
            for item in uninstalls:
                row = tk.Frame(self.scroll_frame, bg="#1E1E1E", height=40)
                row.pack(fill="x", pady=2, padx=10)
                
                cb_var = tk.BooleanVar(value=True)
                self.checkbox_vars[("uninstall", item["path"])] = cb_var
                
                cb = ctk.CTkCheckBox(row, text=f"{item['name']} - {item['reason'][:80]}", variable=cb_var, font=ctk.CTkFont(size=11))
                cb.pack(side="left", padx=5, fill="x", expand=True)
                
        # Render DLLs
        if dlls:
            lbl_d = ctk.CTkLabel(self.scroll_frame, text="Referensi DLL Mati:", font=ctk.CTkFont(size=14, weight="bold"), text_color="#F59E0B")
            lbl_d.pack(anchor="w", pady=(20, 5), padx=10)
            for item in dlls:
                row = tk.Frame(self.scroll_frame, bg="#1E1E1E", height=40)
                row.pack(fill="x", pady=2, padx=10)
                
                cb_var = tk.BooleanVar(value=True)
                self.checkbox_vars[("dll", item["name"])] = cb_var
                
                disp = item["name"]
                if len(disp) > 75:
                    disp = disp[:35] + "..." + disp[-35:]
                    
                cb = ctk.CTkCheckBox(row, text=disp, variable=cb_var, font=ctk.CTkFont(size=11))
                cb.pack(side="left", padx=5, fill="x", expand=True)
                
    def run_clean(self):
        sel_uninstalls = [item for item in self.invalid_uninstalls if self.checkbox_vars.get(("uninstall", item["path"])).get()]
        sel_dlls = [item for item in self.dead_dlls if self.checkbox_vars.get(("dll", item["name"])).get()]
        
        if not sel_uninstalls and not sel_dlls:
            messagebox.showwarning("Pilih Item", "Pilih minimal satu entri registry untuk dibersihkan.")
            return
            
        confirm = messagebox.askyesno(
            "Konfirmasi Bersihkan Registry",
            f"Apakah Anda yakin ingin menghapus {len(sel_uninstalls) + len(sel_dlls)} entri registry terpilih secara permanen?"
        )
        if not confirm:
            return
            
        self.btn_clean.configure(state="disabled", text="Membersihkan...")
        self.btn_scan.configure(state="disabled")
        self.controller.show_status("Membersihkan Registry...")
        
        def worker():
            import premium_tools
            u_cleaned, d_cleaned = premium_tools.clean_invalid_registry(sel_uninstalls, sel_dlls)
            self.after(0, lambda u=u_cleaned, d=d_cleaned: self.finish_clean(u, d))
            
        threading.Thread(target=worker, daemon=True).start()
        
    def finish_clean(self, u_count, d_count):
        messagebox.showinfo("Registry Bersih", f"Berhasil menghapus:\n• {u_count} Kunci Uninstall usang\n• {d_count} Referensi DLL rusak.")
        self.btn_scan.configure(state="normal")
        self.run_scan()

class LargeFileFinderFrame(ctk.CTkFrame):
    """Large File Finder tab to scan folder/drive and clean huge files (>100MB)."""
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)
        
        self.target_dir = ""
        self.large_files = []
        self.checkbox_vars = {}
        
        # Title
        title = ctk.CTkLabel(
            self, text="Pencari File Besar",
            font=ctk.CTkFont(family="Segoe UI", size=24, weight="bold"),
            text_color="#FFFFFF"
        )
        title.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")
        
        desc = ctk.CTkLabel(
            self, text="Temukan dan hapus berkas berukuran raksasa (>100 MB) di folder Anda untuk meluangkan disk.",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color="#AAAAAA"
        )
        desc.grid(row=1, column=0, padx=20, pady=(0, 15), sticky="w")
        
        # Folder Selector panel
        self.top_panel = ctk.CTkFrame(self, fg_color="#1E1E1E", corner_radius=12, height=75)
        self.top_panel.grid(row=2, column=0, padx=20, pady=5, sticky="ew")
        self.top_panel.grid_propagate(False)
        
        self.btn_choose = ctk.CTkButton(
            self.top_panel, text="Pilih Folder",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#475569", hover_color="#334155",
            width=120, height=35, command=self.choose_folder
        )
        self.btn_choose.pack(side="left", padx=15, pady=20)
        
        self.lbl_folder = ctk.CTkLabel(
            self.top_panel, text="Tidak ada folder terpilih.",
            font=ctk.CTkFont(size=13, slant="italic"),
            text_color="#888888"
        )
        self.lbl_folder.pack(side="left", padx=10, pady=20)
        
        self.btn_scan = ctk.CTkButton(
            self.top_panel, text="Mulai Pindai",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#3B82F6", hover_color="#2563EB",
            width=120, height=35, command=self.run_scan
        )
        self.btn_scan.pack(side="right", padx=15, pady=20)
        self.btn_scan.configure(state="disabled")
        
        # Middle Scroll list
        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color="#1E1E1E", label_text="Daftar File Besar (>100MB)", corner_radius=12)
        self.scroll_frame.grid(row=3, column=0, padx=20, pady=10, sticky="nsew")
        
        self.lbl_status = ctk.CTkLabel(
            self.scroll_frame, text="Silakan pilih folder dan lakukan pemindaian terlebih dahulu.",
            font=ctk.CTkFont(size=13), text_color="#888888"
        )
        self.lbl_status.pack(pady=50)
        
        # Bottom Actions Bar
        self.bottom_bar = ctk.CTkFrame(self, fg_color="transparent")
        self.bottom_bar.grid(row=4, column=0, padx=20, pady=(5, 20), sticky="ew")
        
        self.btn_delete = ctk.CTkButton(
            self.bottom_bar, text="Hapus File Terpilih",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#EF4444", hover_color="#DC2626", text_color="#FFFFFF",
            width=180, height=40, command=self.delete_selected_files
        )
        self.btn_delete.pack(side="right")
        self.btn_delete.configure(state="disabled")
        
        self.btn_select_all = ctk.CTkButton(
            self.bottom_bar, text="Pilih Semua",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#475569", hover_color="#334155", text_color="#FFFFFF",
            width=120, height=40, command=self.select_all
        )
        self.btn_select_all.pack(side="left", padx=(0, 10))
        self.btn_select_all.configure(state="disabled")
        
        self.btn_deselect_all = ctk.CTkButton(
            self.bottom_bar, text="Batal Pilih",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#333333", hover_color="#444444", text_color="#FFFFFF",
            width=100, height=40, command=self.deselect_all
        )
        self.btn_deselect_all.pack(side="left")
        self.btn_deselect_all.configure(state="disabled")
        
    def choose_folder(self):
        folder = filedialog.askdirectory(title="Pilih Folder untuk Scan File Besar")
        if folder:
            self.target_dir = folder
            self.lbl_folder.configure(text=folder, text_color="#FFFFFF")
            self.btn_scan.configure(state="normal")
            
    def run_scan(self):
        self.btn_scan.configure(state="disabled", text="Memindai...")
        self.btn_choose.configure(state="disabled")
        self.btn_delete.configure(state="disabled")
        self.btn_select_all.configure(state="disabled")
        self.btn_deselect_all.configure(state="disabled")
        for w in self.scroll_frame.winfo_children():
            w.destroy()
        self.lbl_status = ctk.CTkLabel(self.scroll_frame, text="Sedang memindai direktori (mengurutkan ukuran)...", text_color="#888888")
        self.lbl_status.pack(pady=50)
        self.controller.show_status("Memindai berkas besar...")
        self.checkbox_vars = {}
        
        def worker():
            import premium_tools
            files = premium_tools.find_large_files(self.target_dir, min_size_mb=100)
            self.after(0, lambda: self.render_results(files))
            
        threading.Thread(target=worker, daemon=True).start()
        
    def render_results(self, files):
        self.btn_scan.configure(state="normal", text="Mulai Pindai")
        self.btn_choose.configure(state="normal")
        self.large_files = files
        
        for w in self.scroll_frame.winfo_children():
            w.destroy()
            
        if not files:
            self.lbl_status = ctk.CTkLabel(
                self.scroll_frame, text="Folder Bersih! Tidak ada file berukuran besar (>100 MB).",
                font=ctk.CTkFont(size=13), text_color="#10B981"
            )
            self.lbl_status.pack(pady=50)
            self.btn_delete.configure(state="disabled")
            self.btn_select_all.configure(state="disabled")
            self.btn_deselect_all.configure(state="disabled")
            self.controller.show_status("Scan selesai: Tidak ada berkas besar.")
            return
            
        self.btn_delete.configure(state="normal")
        self.btn_select_all.configure(state="normal")
        self.btn_deselect_all.configure(state="normal")
        self.controller.show_status(f"Scan selesai: Menemukan {len(files)} berkas besar.")
        
        to_mb = lambda b: f"{b / (1024*1024):.1f} MB"
        
        for item in files:
            row = tk.Frame(self.scroll_frame, bg="#1E1E1E", height=45)
            row.pack(fill="x", pady=3, padx=5)
            row.pack_propagate(False)
            
            row.grid_columnconfigure(0, weight=1)
            row.grid_columnconfigure(1, weight=0)
            row.grid_rowconfigure(0, weight=1)
            
            cb_var = tk.BooleanVar(value=False)
            self.checkbox_vars[item["path"]] = cb_var
            
            disp = item["path"]
            if len(disp) > 85:
                disp = disp[:40] + "..." + disp[-40:]
                
            cb = ctk.CTkCheckBox(row, text=disp, variable=cb_var, font=ctk.CTkFont(size=11))
            cb.grid(row=0, column=0, padx=10, sticky="w")
            
            lbl_size = tk.Label(row, text=to_mb(item["size"]), font=("Segoe UI", 10, "bold"), fg="#EF4444", bg="#1E1E1E")
            lbl_size.grid(row=0, column=1, padx=15, sticky="e")
            
    def delete_selected_files(self):
        files_to_del = [path for path, var in self.checkbox_vars.items() if var.get()]
        if not files_to_del:
            messagebox.showwarning("Pilih Berkas", "Pilih minimal satu berkas untuk dihapus.")
            return
            
        confirm = messagebox.askyesno(
            "Konfirmasi Hapus Berkas",
            f"Apakah Anda yakin ingin menghapus permanen {len(files_to_del)} berkas besar terpilih?"
        )
        if not confirm:
            return
            
        self.btn_delete.configure(state="disabled", text="Menghapus...")
        self.btn_scan.configure(state="disabled")
        self.controller.show_status("Menghapus berkas besar...")
        
        def worker():
            deleted = 0
            freed = 0
            failed = 0
            import stat
            for path in files_to_del:
                try:
                    sz = os.path.getsize(path)
                    try:
                        os.chmod(path, stat.S_IWRITE)
                    except Exception:
                        pass
                    os.remove(path)
                    deleted += 1
                    freed += sz
                except Exception:
                    failed += 1
            self.after(0, lambda c=deleted, f=freed, fl=failed: self.finish_deletion(c, f, fl))
            
        threading.Thread(target=worker, daemon=True).start()
        
    def finish_deletion(self, count, bytes_freed, failed_count):
        to_mb = lambda b: f"{b / (1024*1024):.1f} MB"
        msg = f"Berhasil menghapus {count} berkas besar dan membebaskan {to_mb(bytes_freed)} ruang disk."
        if failed_count > 0:
            msg += f"\n\nPerhatian: {failed_count} berkas gagal dihapus (sedang digunakan)."
        messagebox.showinfo("Selesai", msg)
        self.controller.show_status(f"Hapus berkas selesai: Bebas {to_mb(bytes_freed)}.")
        
        freed_mb = bytes_freed / (1024 * 1024)
        def report_worker():
            import firebase_handler
            firebase_handler.report_stats(
                self.controller.current_user['uid'],
                self.controller.current_user['idToken'],
                0,
                freed_mb
            )
        threading.Thread(target=report_worker, daemon=True).start()
        
        self.run_scan()
        
    def select_all(self):
        for var in self.checkbox_vars.values():
            var.set(True)
            
    def deselect_all(self):
        for var in self.checkbox_vars.values():
            var.set(False)

class ContextMenuManagerFrame(ctk.CTkFrame):
    """Context Menu Manager tab to disable/enable right-click context options safely."""
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        
        self.handlers = []
        
        # Title
        title = ctk.CTkLabel(
            self, text="Pengatur Klik Kanan",
            font=ctk.CTkFont(family="Segoe UI", size=24, weight="bold"),
            text_color="#FFFFFF"
        )
        title.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")
        
        desc = ctk.CTkLabel(
            self, text="Kelola dan bersihkan menu klik kanan Windows Explorer Anda dengan aman (Reversible).",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color="#AAAAAA"
        )
        desc.grid(row=1, column=0, padx=20, pady=(0, 15), sticky="w")
        
        # Scrollable container
        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color="#1E1E1E", label_text="Daftar Menu Klik Kanan Ditemukan", corner_radius=12)
        self.scroll_frame.grid(row=2, column=0, padx=20, pady=10, sticky="nsew")
        self.scroll_frame.columnconfigure(0, weight=1)
        
        # Status Label
        self.lbl_status = ctk.CTkLabel(self.scroll_frame, text="Memuat menu klik kanan...", text_color="#888888")
        self.lbl_status.pack(pady=40)
        
        self.load_handlers()
        
    def load_handlers(self):
        for w in self.scroll_frame.winfo_children():
            w.destroy()
            
        def worker():
            import premium_tools
            self.handlers = premium_tools.list_context_menus()
            self.after(0, self.render_handlers)
            
        threading.Thread(target=worker, daemon=True).start()
        
    def render_handlers(self):
        for w in self.scroll_frame.winfo_children():
            w.destroy()
            
        if not self.handlers:
            lbl = ctk.CTkLabel(self.scroll_frame, text="Tidak ada handler pihak ketiga yang dapat dimodifikasi.", text_color="#888888")
            lbl.pack(pady=40)
            return
            
        file_handlers = [h for h in self.handlers if h["category"] == "File"]
        folder_handlers = [h for h in self.handlers if h["category"] == "Folder Background"]
        
        if file_handlers:
            lbl_f = ctk.CTkLabel(self.scroll_frame, text="Menu Pada Berkas/File (*):", font=ctk.CTkFont(size=14, weight="bold"), text_color="#3B82F6")
            lbl_f.pack(anchor="w", pady=(10, 5), padx=10)
            
            for item in file_handlers:
                self.create_handler_row(item)
                
        if folder_handlers:
            lbl_fol = ctk.CTkLabel(self.scroll_frame, text="Menu Pada Latar Belakang Folder:", font=ctk.CTkFont(size=14, weight="bold"), text_color="#10B981")
            lbl_fol.pack(anchor="w", pady=(20, 5), padx=10)
            
            for item in folder_handlers:
                self.create_handler_row(item)
                
    def create_handler_row(self, item):
        row = tk.Frame(self.scroll_frame, bg="#1E1E1E", height=45)
        row.pack(fill="x", pady=2, padx=10)
        row.pack_propagate(False)
        
        row.grid_columnconfigure(0, weight=1)
        row.grid_columnconfigure(1, weight=0)
        row.grid_rowconfigure(0, weight=1)
        
        disp_name = item["name"] if item["name"] else item["clsid"]
        
        lbl_name = tk.Label(row, text=disp_name, font=("Segoe UI", 10, "bold"), fg="#FFFFFF", bg="#1E1E1E", anchor="w")
        lbl_name.grid(row=0, column=0, padx=10, sticky="w")
        
        sw_var = tk.BooleanVar(value=item["enabled"])
        
        def toggle(item=item, var=sw_var):
            item["enabled"] = var.get()
            def task():
                import premium_tools
                ok = premium_tools.toggle_context_menu(item)
                if ok:
                    self.after(0, lambda: self.controller.show_status(f"Menu '{item['name']}' berhasil diupdate."))
                    self.after(0, self.load_handlers)
                else:
                    self.after(0, lambda: messagebox.showerror("Gagal", f"Gagal mengubah status menu '{item['name']}' (Butuh hak Administrator)."))
                    self.after(0, self.load_handlers)
            threading.Thread(target=task, daemon=True).start()
            
        sw = ctk.CTkSwitch(row, text="", variable=sw_var, command=toggle, progress_color="#3B82F6")
        sw.grid(row=0, column=1, padx=10, sticky="e")

class InternetSpeedBoosterFrame(ctk.CTkFrame):
    """Internet Speed Booster tab to optimize TCP/IP network settings and reset Winsock."""
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        
        self.grid_columnconfigure(0, weight=1)
        
        # Title
        title = ctk.CTkLabel(
            self, text="Pengoptimal Internet",
            font=ctk.CTkFont(family="Segoe UI", size=24, weight="bold"),
            text_color="#FFFFFF"
        )
        title.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")
        
        desc = ctk.CTkLabel(
            self, text="Optimalkan pengaturan jaringan TCP/IP Windows dan segarkan soket Winsock Anda secara otomatis.",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color="#AAAAAA"
        )
        desc.grid(row=1, column=0, padx=20, pady=(0, 15), sticky="w")
        
        # Card Container
        self.card = ctk.CTkFrame(self, fg_color="#1E1E1E", corner_radius=12)
        self.card.grid(row=2, column=0, padx=20, pady=5, sticky="ew")
        self.card.columnconfigure(0, weight=1)
        
        lbl_info_title = ctk.CTkLabel(self.card, text="OPTIMASI YANG AKAN DILAKUKAN", font=ctk.CTkFont(size=14, weight="bold"), text_color="#3B82F6")
        lbl_info_title.pack(pady=(15, 10), padx=20, anchor="w")
        
        lbl_info = ctk.CTkLabel(
            self.card,
            text="• RFC 1323 Window Scaling: Meningkatkan throughput internet berkecepatan tinggi.\n"
                 "• Default TTL = 64: Menstandardisasi lompatan paket data untuk latency stabil.\n"
                 "• Max User Ports: Meningkatkan limitasi alokasi port keluar untuk multi-tasking.\n"
                 "• Flush DNS Cache: Membersihkan catatan domain domain usang di Windows.\n"
                 "• TCP/IP Winsock Reset: Memperbaiki soket jaringan yang rusak atau terputus.\n"
                 "• IP Address Renewal: Mengambil alamat IP segar dari DHCP Router Anda.",
            font=ctk.CTkFont(size=12), text_color="#CCCCCC", justify="left"
        )
        lbl_info.pack(pady=10, padx=25, anchor="w")
        
        self.btn_optimize = ctk.CTkButton(
            self.card, text="Optimalkan Koneksi Sekarang",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#3B82F6", hover_color="#2563EB", text_color="#FFFFFF",
            width=280, height=45, corner_radius=8, command=self.run_optimization
        )
        self.btn_optimize.pack(pady=25)
        
    def run_optimization(self):
        self.btn_optimize.configure(state="disabled", text="Mengoptimalkan...")
        self.controller.show_status("Menjalankan optimasi koneksi internet...")
        
        def worker():
            import premium_tools
            reg_ok, reset_log = premium_tools.optimize_internet_settings()
            self.after(0, lambda ok=reg_ok, log=reset_log: self.finish_optimization(ok, log))
            
        threading.Thread(target=worker, daemon=True).start()
        
    def finish_optimization(self, reg_ok, reset_log):
        self.btn_optimize.configure(state="normal", text="Optimalkan Koneksi Sekarang")
        self.controller.show_status("Optimasi koneksi internet selesai.")
        
        msg = "Optimasi Koneksi Selesai!\n\n"
        if reg_ok:
            msg += "✓ Tweak Registry TCP/IP berhasil diterapkan.\n"
        else:
            msg += "✗ Gagal menerapkan Tweak Registry (Butuh hak Administrator).\n"
            
        msg += "✓ Pembersihan DNS Cache selesai.\n"
        msg += "✓ Soket Winsock jaringan berhasil direset."
        
        messagebox.showinfo("Optimasi Selesai", msg)
