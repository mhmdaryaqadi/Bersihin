import os
import sys
import json
import time
import threading
import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk

# Import firebase handler
import firebase_handler

# Set appearance
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class AdminLoginFrame(ctk.CTkFrame):
    """Admin Login GUI Frame using Google Sign-In."""
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="#121212")
        self.controller = controller
        
        # Center container card
        self.card = ctk.CTkFrame(self, width=400, height=310, fg_color="#1E1E1E", corner_radius=15)
        self.card.place(relx=0.5, rely=0.5, anchor="center")
        self.card.pack_propagate(False)
        
        # Title
        logo_lbl = ctk.CTkLabel(
            self.card, text="BERSIHIN ADMIN", 
            font=ctk.CTkFont(family="Segoe UI", size=26, weight="bold"),
            text_color="#3B82F6"
        )
        logo_lbl.pack(pady=(25, 5))
        
        # Subtitle
        mode_text = "Mode: Simulasi Lokal" if firebase_handler.is_mock_mode() else "Mode: Online (Firebase)"
        mode_color = "#888888" if firebase_handler.is_mock_mode() else "#4E9F3D"
        
        self.mode_lbl = ctk.CTkLabel(
            self.card, text=mode_text,
            font=ctk.CTkFont(family="Segoe UI", size=11, slant="italic"),
            text_color=mode_color
        )
        self.mode_lbl.pack(pady=(0, 20))
        
        # Status Label
        self.lbl_status = ctk.CTkLabel(
            self.card, text="Silakan masuk menggunakan Akun Google Administrator Anda.",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color="#CCCCCC",
            wraplength=320,
            justify="center"
        )
        self.lbl_status.pack(pady=(0, 20), padx=20)
        
        # Google Sign-In Button (Purple admin style)
        self.btn_google = ctk.CTkButton(
            self.card, text="Masuk Admin dengan Google",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            fg_color="#3B82F6", hover_color="#2563EB", text_color="#FFFFFF",
            width=320, height=45, corner_radius=8, command=self.perform_google_login
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
        self.lbl_status.configure(text="", text_color="#FFFFFF")
        
        if firebase_handler.is_mock_mode():
            dialog = ctk.CTkInputDialog(
                title="Google Login Admin (Simulasi)",
                text="Masukkan Email Google Admin Simulasi Anda:\n(Contoh: admin@bersihin.com)"
            )
            email = dialog.get_input()
            if not email:
                return
            email = email.strip()
            if '@' not in email:
                self.lbl_status.configure(text="Format email tidak valid.", text_color="#FF9F1C")
                return
                
            self.btn_google.configure(state="disabled", text="Menghubungkan...")
            self.lbl_status.configure(text="Memproses login simulasi...", text_color="#FFFFFF")
            
            def run_mock():
                user, err = firebase_handler.login_mock_google(email, is_admin_requested=True)
                if err:
                    self.after(0, lambda: self.on_login_fail(err))
                else:
                    if user.get('role') != 'admin':
                        self.after(0, lambda: self.on_login_fail("Akses Ditolak: Anda bukan Administrator (Lokal)."))
                    else:
                        self.after(0, lambda: self.on_login_success(user))
            threading.Thread(target=run_mock, daemon=True).start()
        else:
            self.btn_google.configure(state="disabled", text="Membuka Browser...")
            
            def update_status(status_msg):
                self.after(0, lambda: self.lbl_status.configure(text=status_msg, text_color="#3B82F6"))
                
            def run_online():
                user, err = firebase_handler.login_user_with_google(on_status_update=update_status)
                if err:
                    self.after(0, lambda: self.on_login_fail(err))
                else:
                    if user.get('role') != 'admin':
                        self.after(0, lambda: self.on_login_fail("Akses Ditolak: Anda bukan Administrator."))
                    else:
                        self.after(0, lambda: self.on_login_success(user))
            threading.Thread(target=run_online, daemon=True).start()

    def on_login_fail(self, err_msg):
        self.btn_google.configure(state="normal", text="Masuk Admin dengan Google")
        self.lbl_status.configure(text=err_msg, text_color="#EF4444")

    def on_login_success(self, user_data):
        self.btn_google.configure(state="normal", text="Masuk Admin dengan Google")
        if self.remember_var.get() == 1:
            self.controller.save_admin_session(user_data)
        else:
            self.controller.clear_admin_session()
        self.controller.admin_user = user_data
        self.controller.show_dashboard()


class UserRowWidget(ctk.CTkFrame):
    """Custom Widget representing a single row in the user scroll list."""
    def __init__(self, parent, uid, user_data, on_click_callback):
        super().__init__(parent, fg_color="#1E1E1E", height=70, corner_radius=8, cursor="hand2")
        self.uid = uid
        self.user_data = user_data
        self.on_click_callback = on_click_callback
        
        self.pack_propagate(False)
        
        # Bind click events for all components
        self.bind("<Button-1>", self.on_click)
        
        # Grid layout for sub-elements
        self.grid_columnconfigure(0, weight=2) # Email & Username
        self.grid_columnconfigure(1, weight=1) # Computer Info
        self.grid_columnconfigure(2, weight=1) # Stats (RAM/Disk)
        self.grid_columnconfigure(3, weight=0) # Badges & Last active
        
        # 1. Email & Username
        user_lbl_frame = ctk.CTkFrame(self, fg_color="transparent")
        user_lbl_frame.grid(row=0, column=0, padx=15, pady=10, sticky="w")
        
        lbl_username = ctk.CTkLabel(
            user_lbl_frame, text=user_data.get('username', 'Unknown'),
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color="#FFFFFF"
        )
        lbl_username.pack(anchor="w")
        lbl_username.bind("<Button-1>", self.on_click)
        
        lbl_email = ctk.CTkLabel(
            user_lbl_frame, text=user_data.get('email', '-'),
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color="#888888"
        )
        lbl_email.pack(anchor="w")
        lbl_email.bind("<Button-1>", self.on_click)
        
        # 2. Computer Info
        pc_lbl_frame = ctk.CTkFrame(self, fg_color="transparent")
        pc_lbl_frame.grid(row=0, column=1, padx=10, pady=10, sticky="w")
        
        lbl_pc = ctk.CTkLabel(
            pc_lbl_frame, text=user_data.get('computer_name', '-'),
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color="#CCCCCC"
        )
        lbl_pc.pack(anchor="w")
        lbl_pc.bind("<Button-1>", self.on_click)
        
        lbl_os = ctk.CTkLabel(
            pc_lbl_frame, text=user_data.get('os', '-'),
            font=ctk.CTkFont(family="Segoe UI", size=10),
            text_color="#888888"
        )
        lbl_os.pack(anchor="w")
        lbl_os.bind("<Button-1>", self.on_click)
        
        # 3. Stats (RAM & Disk cleaned)
        stats_lbl_frame = ctk.CTkFrame(self, fg_color="transparent")
        stats_lbl_frame.grid(row=0, column=2, padx=10, pady=10, sticky="w")
        
        ram_mb = user_data.get('ram_cleaned_mb', 0)
        disk_mb = user_data.get('disk_cleaned_mb', 0)
        
        ram_str = f"{ram_mb / 1024:.2f} GB" if ram_mb >= 1024 else f"{ram_mb:.0f} MB"
        disk_str = f"{disk_mb / 1024:.2f} GB" if disk_mb >= 1024 else f"{disk_mb:.0f} MB"
        
        lbl_ram = ctk.CTkLabel(
            stats_lbl_frame, text=f"RAM: {ram_str}",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color="#CCCCCC"
        )
        lbl_ram.pack(anchor="w")
        lbl_ram.bind("<Button-1>", self.on_click)
        
        lbl_disk = ctk.CTkLabel(
            stats_lbl_frame, text=f"Disk: {disk_str}",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color="#CCCCCC"
        )
        lbl_disk.pack(anchor="w")
        lbl_disk.bind("<Button-1>", self.on_click)
        
        # 4. Status Badges & Last active
        badge_lbl_frame = ctk.CTkFrame(self, fg_color="transparent")
        badge_lbl_frame.grid(row=0, column=3, padx=15, pady=10, sticky="e")
        
        badges_container = ctk.CTkFrame(badge_lbl_frame, fg_color="transparent")
        badges_container.pack(anchor="e")
        
        # Status Badge
        status = user_data.get('status', 'active')
        status_bg = "#10B981" if status == "active" else "#EF4444"
        status_txt = "AKTIF" if status == "active" else "BLOKIR"
        
        lbl_status_badge = ctk.CTkLabel(
            badges_container, text=status_txt,
            font=ctk.CTkFont(family="Segoe UI", size=9, weight="bold"),
            text_color="#FFFFFF", fg_color=status_bg, corner_radius=4, width=55, height=18
        )
        lbl_status_badge.pack(side="right", padx=2)
        lbl_status_badge.bind("<Button-1>", self.on_click)
        
        # Role Badge
        role = user_data.get('role', 'user')
        role_bg = "#3B82F6" if role == "admin" else "#2E2E2E"
        role_txt = "ADMIN" if role == "admin" else "USER"
        
        lbl_role_badge = ctk.CTkLabel(
            badges_container, text=role_txt,
            font=ctk.CTkFont(family="Segoe UI", size=9, weight="bold"),
            text_color="#FFFFFF", fg_color=role_bg, corner_radius=4, width=50, height=18
        )
        lbl_role_badge.pack(side="right", padx=2)
        lbl_role_badge.bind("<Button-1>", self.on_click)
        
        # Last active timestamp
        last_act = user_data.get('last_active', 0)
        if last_act > 0:
            last_act_str = time.strftime('%d/%m/%y %H:%M', time.localtime(last_act))
        else:
            last_act_str = "Belum Aktif"
            
        lbl_last_active = ctk.CTkLabel(
            badge_lbl_frame, text=f"Aktif: {last_act_str}",
            font=ctk.CTkFont(family="Segoe UI", size=9),
            text_color="#666666"
        )
        lbl_last_active.pack(anchor="e", pady=(2, 0))
        lbl_last_active.bind("<Button-1>", self.on_click)

    def on_click(self, event):
        self.on_click_callback(self.uid, self.user_data, self)

    def highlight(self):
        self.configure(fg_color="#2A2A2A")
    def unhighlight(self):
        self.configure(fg_color="#1E1E1E")


class AdminUsersFrame(ctk.CTkFrame):
    """Main Administrator Users Management Frame."""
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        
        self.selected_uid = None
        self.selected_user_data = None
        self.selected_row_widget = None
        self.row_widgets = {}
        
        # Grid Configuration
        self.grid_columnconfigure(0, weight=3) # User Scroll Frame
        self.grid_columnconfigure(1, weight=1) # Action & Detail Frame
        self.grid_rowconfigure(1, weight=1)
        
        # Header / Title
        title = ctk.CTkLabel(
            self, text="Manajemen Akun Pengguna",
            font=ctk.CTkFont(family="Segoe UI", size=24, weight="bold"),
            text_color="#FFFFFF"
        )
        title.grid(row=0, column=0, columnspan=2, padx=20, pady=(20, 10), sticky="w")
        
        # Left Side: User Scroll Frame
        left_container = ctk.CTkFrame(self, fg_color="transparent")
        left_container.grid(row=1, column=0, padx=(15, 10), pady=15, sticky="nsew")
        left_container.grid_rowconfigure(1, weight=1)
        left_container.grid_columnconfigure(0, weight=1)
        
        # Search & Reload Panel
        search_panel = ctk.CTkFrame(left_container, fg_color="transparent")
        search_panel.grid(row=0, column=0, pady=(0, 10), sticky="ew")
        search_panel.grid_columnconfigure(0, weight=1)
        
        self.search_entry = ctk.CTkEntry(
            search_panel, placeholder_text="Cari nama pengguna atau email...",
            height=35
        )
        self.search_entry.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self.search_entry.bind("<KeyRelease>", self.on_search_change)
        
        btn_refresh = ctk.CTkButton(
            search_panel, text="Refresh Data",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            fg_color="#475569", hover_color="#334155", text_color="#FFFFFF",
            width=110, height=35, command=self.load_users
        )
        btn_refresh.grid(row=0, column=1, sticky="e")
        
        # Scrollable Frame for Users
        self.scroll_frame = ctk.CTkScrollableFrame(
            left_container, fg_color="transparent", label_text="Daftar Pengguna Terdaftar"
        )
        self.scroll_frame.grid(row=1, column=0, sticky="nsew")
        
        # Right Side: Action & Detail Panel
        self.right_panel = ctk.CTkFrame(self, fg_color="#1E1E1E", corner_radius=10)
        self.right_panel.grid(row=1, column=1, padx=(10, 15), pady=15, sticky="nsew")
        self.right_panel.pack_propagate(False)
        
        # Placeholder for no user selected
        self.lbl_no_selection = ctk.CTkLabel(
            self.right_panel, text="Pilih pengguna dari daftar\nuntuk melihat rincian & aksi.",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color="#888888", justify="center"
        )
        self.lbl_no_selection.pack(expand=True)
        
        # Setup Detail UI (hidden initially)
        self.setup_detail_ui()
 
    def setup_detail_ui(self):
        self.detail_frame = ctk.CTkScrollableFrame(self.right_panel, fg_color="transparent")
        
        # Detail Title
        self.lbl_detail_title = ctk.CTkLabel(
            self.detail_frame, text="Rincian Pengguna",
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
            text_color="#FFFFFF"
        )
        self.lbl_detail_title.pack(anchor="w", pady=(15, 10))
        
        # Detail items container
        self.details_container = ctk.CTkFrame(self.detail_frame, fg_color="#121212", corner_radius=8)
        self.details_container.pack(fill="x", pady=(0, 10))
        
        # Details Fields
        self.val_username = self.create_detail_row("Username:", "")
        self.val_email = self.create_detail_row("Email:", "")
        self.val_computer = self.create_detail_row("Perangkat:", "")
        self.val_os = self.create_detail_row("Sistem Operasi:", "")
        self.val_ram_total = self.create_detail_row("RAM Total:", "")
        self.val_ram_cleaned = self.create_detail_row("RAM Dibersihkan:", "")
        self.val_disk_cleaned = self.create_detail_row("Disk Dibersihkan:", "")
        self.val_role = self.create_detail_row("Peran:", "")
        self.val_status = self.create_detail_row("Status:", "")
        self.val_last_active = self.create_detail_row("Aktif Terakhir:", "")
        
        # Action Buttons
        self.btn_toggle_block = ctk.CTkButton(
            self.detail_frame, text="Blokir Pengguna",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            fg_color="#EF4444", hover_color="#DC2626", text_color="#FFFFFF",
            height=30, command=self.perform_toggle_block
        )
        self.btn_toggle_block.pack(fill="x", pady=3)
        
        self.btn_toggle_role = ctk.CTkButton(
            self.detail_frame, text="Jadikan Admin",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            fg_color="#3B82F6", hover_color="#2563EB", text_color="#FFFFFF",
            height=30, command=self.perform_toggle_role
        )
        self.btn_toggle_role.pack(fill="x", pady=3)
        
        self.btn_delete_user = ctk.CTkButton(
            self.detail_frame, text="Hapus User dari DB",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            fg_color="#333333", hover_color="#444444", text_color="#EF4444",
            height=30, command=self.perform_delete_user
        )
        self.btn_delete_user.pack(fill="x", pady=3)
        
        # Remote section
        lbl_remote = ctk.CTkLabel(self.detail_frame, text="KENDALI JARAK JAUH", font=ctk.CTkFont(size=10, weight="bold"), text_color="#888888")
        lbl_remote.pack(pady=(10, 5), anchor="w")
        
        self.btn_remote_clean = ctk.CTkButton(
            self.detail_frame, text="Remote Clean (Senyap)",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            fg_color="#475569", hover_color="#334155", text_color="#FFFFFF",
            height=30, command=self.perform_remote_clean
        )
        self.btn_remote_clean.pack(fill="x", pady=3)
        
        self.btn_remote_msg = ctk.CTkButton(
            self.detail_frame, text="Kirim Pesan Pribadi",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            fg_color="#475569", hover_color="#334155", text_color="#FFFFFF",
            height=30, command=self.perform_remote_msg
        )
        self.btn_remote_msg.pack(fill="x", pady=(3, 10))
 
    def create_detail_row(self, label_text, default_val):
        row = ctk.CTkFrame(self.details_container, fg_color="transparent")
        row.pack(fill="x", pady=2, padx=5)
        
        lbl = ctk.CTkLabel(row, text=label_text, font=ctk.CTkFont(size=11), text_color="#888888", width=110, anchor="w")
        lbl.pack(side="left")
        
        val = ctk.CTkLabel(row, text=default_val, font=ctk.CTkFont(size=11, weight="bold"), text_color="#FFFFFF", anchor="w")
        val.pack(side="left", fill="x", expand=True)
        return val
 
    def load_users(self):
        """Loads and lists all users in the system."""
        # Biarkan panel no_selection memuat
        self.lbl_no_selection.configure(text="Memuat daftar pengguna...")
        self.lbl_no_selection.pack(expand=True)
        self.detail_frame.pack_forget()
        
        # Clear current list
        for w in self.scroll_frame.winfo_children():
            w.destroy()
        self.row_widgets = {}
        self.selected_uid = None
        self.selected_user_data = None
        self.selected_row_widget = None
        
        def run():
            users, err = firebase_handler.get_all_users_data(self.controller.admin_user['idToken'])
            if err:
                self.after(0, lambda: messagebox.showerror("Error", f"Gagal memuat pengguna: {err}"))
                self.after(0, lambda: self.lbl_no_selection.configure(text="Gagal memuat data."))
                return
            
            self.all_users = users
            self.after(0, self.render_users)
            
        threading.Thread(target=run, daemon=True).start()
 
    def render_users(self):
        # Clear current list
        for w in self.scroll_frame.winfo_children():
            w.destroy()
        self.row_widgets = {}
        
        users = getattr(self, 'all_users', None)
        if not users:
            self.lbl_no_selection.configure(text="Tidak ada data pengguna.")
            self.lbl_no_selection.pack(expand=True)
            return
            
        self.lbl_no_selection.configure(text="Pilih pengguna dari daftar\nuntuk melihat rincian & aksi.")
        
        # Filter and render
        search_query = self.search_entry.get().strip().lower()
        
        idx = 0
        for uid, udata in users.items():
            username = udata.get('username', '').lower()
            email = udata.get('email', '').lower()
            
            if search_query and (search_query not in username and search_query not in email):
                continue
                
            row = UserRowWidget(self.scroll_frame, uid, udata, self.on_user_selected)
            row.pack(fill="x", pady=4, padx=5)
            self.row_widgets[uid] = row
            idx += 1
            
        if idx == 0:
            self.lbl_no_selection.configure(text="Hasil pencarian kosong.")
            self.lbl_no_selection.pack(expand=True)
 
    def on_search_change(self, event):
        # Filter in-memory only, no database load!
        self.render_users()
 
    def on_user_selected(self, uid, user_data, widget):
        if self.selected_row_widget:
            self.selected_row_widget.unhighlight()
            
        self.selected_uid = uid
        self.selected_user_data = user_data
        self.selected_row_widget = widget
        widget.highlight()
        
        self.lbl_no_selection.pack_forget()
        
        # Update detail fields
        self.val_username.configure(text=user_data.get('username', '-'))
        self.val_email.configure(text=user_data.get('email', '-'))
        self.val_computer.configure(text=user_data.get('computer_name', '-'))
        self.val_os.configure(text=user_data.get('os', '-'))
        
        ram_total = user_data.get('ram_total', 0)
        ram_total_str = f"{ram_total / (1024**3):.2f} GB" if ram_total > 0 else "-"
        self.val_ram_total.configure(text=ram_total_str)
        
        ram_cleaned = user_data.get('ram_cleaned_mb', 0)
        self.val_ram_cleaned.configure(text=f"{ram_cleaned:.0f} MB")
        
        disk_cleaned = user_data.get('disk_cleaned_mb', 0)
        self.val_disk_cleaned.configure(text=f"{disk_cleaned:.0f} MB")
        
        role = user_data.get('role', 'user')
        self.val_role.configure(text=role.upper(), text_color="#3B82F6" if role == "admin" else "#FFFFFF")
        
        status = user_data.get('status', 'active')
        status_txt = "AKTIF" if status == "active" else "BLOKIR"
        status_color = "#10B981" if status == "active" else "#EF4444"
        self.val_status.configure(text=status_txt, text_color=status_color)
        
        last_act = user_data.get('last_active', 0)
        if last_act > 0:
            last_act_str = time.strftime('%d/%m/%Y %H:%M:%S', time.localtime(last_act))
        else:
            last_act_str = "Belum Aktif"
        self.val_last_active.configure(text=last_act_str)
        
        # Update action buttons states/texts
        if status == "active":
            self.btn_toggle_block.configure(text="Blokir Akses Akun", fg_color="#EF4444", hover_color="#DC2626")
        else:
            self.btn_toggle_block.configure(text="Aktifkan Akses Akun", fg_color="#10B981", hover_color="#059669")
            
        if role == "admin":
            self.btn_toggle_role.configure(text="Turunkan ke User", fg_color="#333333", hover_color="#444444", text_color="#FFFFFF")
        else:
            self.btn_toggle_role.configure(text="Jadikan Administrator", fg_color="#3B82F6", hover_color="#2563EB", text_color="#FFFFFF")
            
        # Don't allow self-demotion, self-blocking, or self-remote
        is_self = (uid == self.controller.admin_user.get('uid'))
        if is_self:
            self.btn_toggle_block.configure(state="disabled")
            self.btn_toggle_role.configure(state="disabled")
            self.btn_delete_user.configure(state="disabled")
            self.btn_remote_clean.configure(state="disabled")
            self.btn_remote_msg.configure(state="disabled")
        else:
            self.btn_toggle_block.configure(state="normal")
            self.btn_toggle_role.configure(state="normal")
            self.btn_delete_user.configure(state="normal")
            self.btn_remote_clean.configure(state="normal")
            self.btn_remote_msg.configure(state="normal")
            
        self.detail_frame.pack(fill="both", expand=True, padx=10)
 
    def perform_toggle_block(self):
        if not self.selected_uid:
            return
            
        status = self.selected_user_data.get('status', 'active')
        new_status = "blocked" if status == "active" else "active"
        
        act_str = "memblokir" if new_status == "blocked" else "mengaktifkan kembali"
        confirm = messagebox.askyesno(
            "Konfirmasi Tindakan",
            f"Apakah Anda yakin ingin {act_str} user '{self.selected_user_data.get('username')}'?"
        )
        if not confirm:
            return
            
        self.btn_toggle_block.configure(state="disabled", text="Memproses...")
        
        def run():
            ok = firebase_handler.update_user_status_by_admin(
                self.controller.admin_user['idToken'],
                self.selected_uid,
                new_status
            )
            if ok:
                self.after(0, self.on_action_success)
            else:
                self.after(0, lambda: messagebox.showerror("Gagal", "Gagal memperbarui status pengguna."))
                self.after(0, lambda: self.btn_toggle_block.configure(state="normal"))
                
        threading.Thread(target=run, daemon=True).start()
 
    def perform_toggle_role(self):
        if not self.selected_uid:
            return
            
        role = self.selected_user_data.get('role', 'user')
        new_role = "user" if role == "admin" else "admin"
        
        act_str = "menurunkan peran ke User" if new_role == "user" else "mempromosikan ke Administrator"
        confirm = messagebox.askyesno(
            "Konfirmasi Tindakan",
            f"Apakah Anda yakin ingin {act_str} user '{self.selected_user_data.get('username')}'?"
        )
        if not confirm:
            return
            
        self.btn_toggle_role.configure(state="disabled", text="Memproses...")
        
        def run():
            ok = firebase_handler.update_user_role_by_admin(
                self.controller.admin_user['idToken'],
                self.selected_uid,
                new_role
            )
            if ok:
                self.after(0, self.on_action_success)
            else:
                self.after(0, lambda: messagebox.showerror("Gagal", "Gagal memperbarui peran pengguna."))
                self.after(0, lambda: self.btn_toggle_role.configure(state="normal"))
                
        threading.Thread(target=run, daemon=True).start()
 
    def perform_delete_user(self):
        if not self.selected_uid:
            return
            
        confirm = messagebox.askyesno(
            "Hapus Pengguna Permanent",
            f"PERHATIAN!\n\nApakah Anda yakin ingin menghapus data user '{self.selected_user_data.get('username')}' secara permanen dari database?\nTindakan ini tidak dapat dibatalkan."
        )
        if not confirm:
            return
            
        self.btn_delete_user.configure(state="disabled", text="Menghapus...")
        
        def run():
            ok = firebase_handler.delete_user_by_admin(
                self.controller.admin_user['idToken'],
                self.selected_uid
            )
            if ok:
                self.after(0, self.on_delete_success)
            else:
                self.after(0, lambda: messagebox.showerror("Gagal", "Gagal menghapus pengguna dari database."))
                self.after(0, lambda: self.btn_delete_user.configure(state="normal"))
                
        threading.Thread(target=run, daemon=True).start()
 
    def perform_remote_clean(self):
        if not self.selected_uid:
            return
            
        confirm = messagebox.askyesno(
            "Konfirmasi Remote Clean",
            f"Apakah Anda yakin ingin memicu pembersihan RAM & Disk jarak jauh secara senyap pada PC '{self.selected_user_data.get('username')}'?"
        )
        if not confirm:
            return
            
        self.btn_remote_clean.configure(state="disabled", text="Mengirim...")
        
        def run():
            import firebase_handler
            ok = firebase_handler.write_remote_command(
                self.controller.admin_user['idToken'],
                self.selected_uid,
                'remote_clean',
                True
            )
            if not ok:
                self.after(0, lambda: messagebox.showerror("Gagal", "Gagal mengirimkan perintah ke database."))
                self.after(0, lambda: self.btn_remote_clean.configure(state="normal", text="Remote Clean (Senyap)"))
                return
                
            # Polling response
            start_time = time.time()
            max_wait = 30
            success = False
            
            while time.time() - start_time < max_wait:
                time.sleep(2)
                cmds, _ = firebase_handler.check_remote_commands(self.selected_uid, self.controller.admin_user['idToken'])
                if cmds and cmds.get('response'):
                    resp = cmds['response']
                    self.after(0, lambda r=resp: self.show_remote_response(r))
                    success = True
                    break
                    
            if not success:
                self.after(0, lambda: messagebox.showinfo("Habis Waktu", "Perintah terkirim, namun tidak ada respon dari Klien (Klien mungkin offline)."))
                self.after(0, lambda: self.btn_remote_clean.configure(state="normal", text="Remote Clean (Senyap)"))
                
        threading.Thread(target=run, daemon=True).start()
        
    def show_remote_response(self, resp):
        self.btn_remote_clean.configure(state="normal", text="Remote Clean (Senyap)")
        ram_freed = resp.get('ram_freed_mb', 0)
        disk_freed = resp.get('disk_freed_mb', 0)
        
        messagebox.showinfo(
            "Respon Remote Clean",
            f"Pembersihan jarak jauh berhasil dilakukan!\n\n"
            f"• RAM Dibebaskan: {ram_freed:.1f} MB\n"
            f"• Disk Dibebaskan: {disk_freed:.2f} MB"
        )
        self.load_users()
        
    def perform_remote_msg(self):
        if not self.selected_uid:
            return
            
        dialog = ctk.CTkInputDialog(
            title="Kirim Pesan Pribadi",
            text=f"Masukkan pesan yang ingin dikirim langsung ke PC '{self.selected_user_data.get('username')}':"
        )
        msg_text = dialog.get_input()
        if not msg_text:
            return
            
        msg_text = msg_text.strip()
        self.btn_remote_msg.configure(state="disabled", text="Mengirim...")
        
        def run():
            import firebase_handler
            ok = firebase_handler.write_remote_command(
                self.controller.admin_user['idToken'],
                self.selected_uid,
                'notification',
                msg_text
            )
            if ok:
                self.after(0, lambda: messagebox.showinfo("Sukses", "Pesan notifikasi pribadi berhasil dikirim."))
            else:
                self.after(0, lambda: messagebox.showerror("Gagal", "Gagal mengirimkan notifikasi."))
            self.after(0, lambda: self.btn_remote_msg.configure(state="normal", text="Kirim Pesan Pribadi"))
            
        threading.Thread(target=run, daemon=True).start()
 
    def on_action_success(self):
        messagebox.showinfo("Sukses", "Tindakan berhasil diterapkan!")
        self.load_users()
 
    def on_delete_success(self):
        messagebox.showinfo("Sukses", "Pengguna berhasil dihapus secara permanen dari database.")
        self.load_users()

class AdminAnalyticsFrame(ctk.CTkFrame):
    """Premium tab visualizing aggregate system health and stats of all users using clean canvas charts."""
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        
        # Title
        title = ctk.CTkLabel(
            self, text="Analitik & Performa Global",
            font=ctk.CTkFont(family="Segoe UI", size=24, weight="bold"),
            text_color="#FFFFFF"
        )
        title.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")
        
        desc = ctk.CTkLabel(
            self, text="Statistik kumulatif kebersihan, aktivitas, dan perangkat keras seluruh pengguna terdaftar.",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color="#AAAAAA"
        )
        desc.grid(row=1, column=0, padx=20, pady=(0, 15), sticky="w")
        
        # Main Scrollable Area
        self.scroll = ctk.CTkScrollableFrame(self, fg_color="#1E1E1E", corner_radius=12)
        self.scroll.grid(row=2, column=0, padx=20, pady=(0, 20), sticky="nsew")
        self.scroll.grid_columnconfigure(0, weight=1)
        
        # 1. Cards Panel
        self.cards_frame = ctk.CTkFrame(self.scroll, fg_color="transparent")
        self.cards_frame.pack(fill="x", pady=10, padx=10)
        self.cards_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)
        
        self.card_total_users = self.create_stat_card(self.cards_frame, "TOTAL PENGGUNA", "0", 0)
        self.card_active_users = self.create_stat_card(self.cards_frame, "USER AKTIF (10M)", "0", 1)
        self.card_total_ram = self.create_stat_card(self.cards_frame, "TOTAL RAM BEBAS", "0 GB", 2)
        self.card_total_disk = self.create_stat_card(self.cards_frame, "TOTAL DISK BEBAS", "0 GB", 3)
        
        # 2. Charts Container
        self.charts_frame = ctk.CTkFrame(self.scroll, fg_color="transparent")
        self.charts_frame.pack(fill="both", expand=True, pady=20, padx=10)
        self.charts_frame.grid_columnconfigure(0, weight=1)
        self.charts_frame.grid_columnconfigure(1, weight=1)
        
        # OS Distribution Chart Box
        self.box_os = ctk.CTkFrame(self.charts_frame, fg_color="#121212", corner_radius=10, height=260)
        self.box_os.grid(row=0, column=0, padx=10, sticky="nsew")
        self.box_os.pack_propagate(False)
        
        lbl_os_title = ctk.CTkLabel(self.box_os, text="Distribusi Sistem Operasi (OS)", font=ctk.CTkFont(size=13, weight="bold"))
        lbl_os_title.pack(pady=10, padx=15, anchor="w")
        
        self.canvas_os = tk.Canvas(self.box_os, bg="#121212", highlightthickness=0, height=180)
        self.canvas_os.pack(fill="both", expand=True, padx=15, pady=5)
        
        # Performance Comparison Chart Box
        self.box_perf = ctk.CTkFrame(self.charts_frame, fg_color="#121212", corner_radius=10, height=260)
        self.box_perf.grid(row=0, column=1, padx=10, sticky="nsew")
        self.box_perf.pack_propagate(False)
        
        lbl_perf_title = ctk.CTkLabel(self.box_perf, text="Statistik Pembersihan Kumulatif (GB)", font=ctk.CTkFont(size=13, weight="bold"))
        lbl_perf_title.pack(pady=10, padx=15, anchor="w")
        
        self.canvas_perf = tk.Canvas(self.box_perf, bg="#121212", highlightthickness=0, height=180)
        self.canvas_perf.pack(fill="both", expand=True, padx=15, pady=5)
        
    def create_stat_card(self, parent, title_text, val_text, col_idx):
        card = ctk.CTkFrame(parent, fg_color="#121212", height=80, corner_radius=8)
        card.grid(row=0, column=col_idx, padx=5, sticky="nsew")
        card.pack_propagate(False)
        
        lbl = ctk.CTkLabel(card, text=title_text, font=ctk.CTkFont(size=9, weight="bold"), text_color="#888888")
        lbl.pack(pady=(15, 2), padx=10, anchor="w")
        
        val = ctk.CTkLabel(card, text=val_text, font=ctk.CTkFont(size=18, weight="bold"), text_color="#3B82F6")
        val.pack(pady=(2, 10), padx=10, anchor="w")
        return val

    def load_analytics_data(self):
        def worker():
            import firebase_handler
            data, err = firebase_handler.get_global_analytics(self.controller.admin_user['idToken'])
            if not err and data:
                self.after(0, lambda d=data: self.update_charts(d))
                
        threading.Thread(target=worker, daemon=True).start()
        
    def update_charts(self, data):
        # Update Cards
        self.card_total_users.configure(text=str(data["total_users"]))
        self.card_active_users.configure(text=str(data["active_users"]))
        self.card_total_ram.configure(text=f"{data['total_ram_cleaned_gb']:.1f} GB")
        self.card_total_disk.configure(text=f"{data['total_disk_cleaned_gb']:.1f} GB")
        
        # Ensure widget dimensions are updated
        self.canvas_os.update_idletasks()
        self.canvas_perf.update_idletasks()
        
        # 1. Draw OS Distribution Chart
        self.canvas_os.delete("all")
        os_data = data.get("os_distribution", {})
        if os_data:
            canvas_width = max(self.canvas_os.winfo_width(), 300)
            bar_max_width = max(canvas_width - 180, 100)
            
            max_val = max(os_data.values()) if os_data.values() else 1
            y_offset = 20
            bar_height = 20
            
            for os_name, count in os_data.items():
                ratio = count / max_val
                bar_width = int(ratio * bar_max_width)
                
                self.canvas_os.create_text(10, y_offset + 10, text=f"{os_name}: {count}", fill="#FFFFFF", anchor="w", font=("Segoe UI", 10, "bold"))
                self.canvas_os.create_rectangle(140, y_offset, 140 + bar_width, y_offset + bar_height, fill="#3B82F6", outline="")
                
                y_offset += 35
                
        # 2. Draw Performance Comparison Chart (RAM vs Disk)
        self.canvas_perf.delete("all")
        ram_gb = data["total_ram_cleaned_gb"]
        disk_gb = data["total_disk_cleaned_gb"]
        
        max_gb = max(ram_gb, disk_gb, 1)
        
        canvas_width = max(self.canvas_perf.winfo_width(), 300)
        canvas_height = max(self.canvas_perf.winfo_height(), 180)
        
        bar_width = 50
        spacing = 60
        total_width = (bar_width * 2) + spacing
        start_x = (canvas_width - total_width) // 2
        
        ram_x = start_x
        disk_x = start_x + bar_width + spacing
        
        max_bar_height = canvas_height - 60
        ram_height = int((ram_gb / max_gb) * max_bar_height)
        disk_height = int((disk_gb / max_gb) * max_bar_height)
        
        # RAM Bar
        self.canvas_perf.create_rectangle(ram_x, canvas_height - 40 - ram_height, ram_x + bar_width, canvas_height - 40, fill="#3B82F6", outline="")
        self.canvas_perf.create_text(ram_x + bar_width/2, canvas_height - 25, text="RAM", fill="#FFFFFF", font=("Segoe UI", 10, "bold"))
        self.canvas_perf.create_text(ram_x + bar_width/2, canvas_height - 52 - ram_height, text=f"{ram_gb:.1f} GB", fill="#3B82F6", font=("Segoe UI", 10, "bold"))
        
        # Disk Bar
        self.canvas_perf.create_rectangle(disk_x, canvas_height - 40 - disk_height, disk_x + bar_width, canvas_height - 40, fill="#475569", outline="")
        self.canvas_perf.create_text(disk_x + bar_width/2, canvas_height - 25, text="Disk", fill="#FFFFFF", font=("Segoe UI", 10, "bold"))
        self.canvas_perf.create_text(disk_x + bar_width/2, canvas_height - 52 - disk_height, text=f"{disk_gb:.1f} GB", fill="#CCCCCC", font=("Segoe UI", 10, "bold"))

class AdminGlobalSettingsFrame(ctk.CTkFrame):
    """Premium tab managing global application update versions and broadcast messaging."""
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        
        # Title
        title = ctk.CTkLabel(
            self, text="Pesan Siaran & Manajemen Update",
            font=ctk.CTkFont(family="Segoe UI", size=24, weight="bold"),
            text_color="#FFFFFF"
        )
        title.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")
        
        desc = ctk.CTkLabel(
            self, text="Kirim pesan massal real-time ke semua klien atau atur versi aplikasi yang aktif.",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color="#AAAAAA"
        )
        desc.grid(row=1, column=0, padx=20, pady=(0, 15), sticky="w")
        
        # Content Container
        self.container = ctk.CTkScrollableFrame(self, fg_color="#1E1E1E", corner_radius=12)
        self.container.grid(row=2, column=0, padx=20, pady=5, sticky="nsew")
        self.grid_rowconfigure(2, weight=1)
        self.container.grid_columnconfigure(0, weight=1)
        
        # 1. Broadcast Section
        self.box_broadcast = ctk.CTkFrame(self.container, fg_color="#121212", corner_radius=8)
        self.box_broadcast.pack(fill="x", pady=10, padx=10)
        self.box_broadcast.grid_columnconfigure(0, weight=1)
        
        lbl_b_title = ctk.CTkLabel(self.box_broadcast, text="KIRIM PESAN SIARAN (BROADCAST)", font=ctk.CTkFont(size=14, weight="bold"), text_color="#3B82F6")
        lbl_b_title.pack(pady=(15, 5), padx=20, anchor="w")
        
        lbl_b_desc = ctk.CTkLabel(self.box_broadcast, text="Pesan siaran akan langsung pop-up di layar komputer seluruh pengguna aktif saat ini.", font=ctk.CTkFont(size=11), text_color="#888888")
        lbl_b_desc.pack(pady=(0, 15), padx=20, anchor="w")
        
        self.entry_broadcast = ctk.CTkEntry(self.box_broadcast, placeholder_text="Tulis pesan pengumuman massal di sini...", height=40)
        self.entry_broadcast.pack(fill="x", padx=20, pady=5)
        
        # Row for button commands
        btn_row_b = ctk.CTkFrame(self.box_broadcast, fg_color="transparent")
        btn_row_b.pack(fill="x", padx=20, pady=(10, 20))
        
        self.btn_send_b = ctk.CTkButton(
            btn_row_b, text="Kirim Siaran Sekarang",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#3B82F6", hover_color="#2563EB", text_color="#FFFFFF",
            width=180, height=35, command=self.send_broadcast
        )
        self.btn_send_b.pack(side="left", padx=(0, 10))
        
        self.btn_clear_b = ctk.CTkButton(
            btn_row_b, text="Hapus Siaran Aktif",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#333333", hover_color="#444444", text_color="#EF4444",
            width=150, height=35, command=self.clear_broadcast
        )
        self.btn_clear_b.pack(side="left")
        
        # 2. Update Checker Section
        self.box_update = ctk.CTkFrame(self.container, fg_color="#121212", corner_radius=8)
        self.box_update.pack(fill="x", pady=10, padx=10)
        
        lbl_u_title = ctk.CTkLabel(self.box_update, text="PENGATURAN VERSI APLIKASI (AUTO-UPDATER)", font=ctk.CTkFont(size=14, weight="bold"), text_color="#10B981")
        lbl_u_title.pack(pady=(15, 5), padx=20, anchor="w")
        
        lbl_u_desc = ctk.CTkLabel(self.box_update, text="Tentukan versi aktif teratas. Jika client mendeteksi versi mereka lebih lama, mereka akan dipaksa update.", font=ctk.CTkFont(size=11), text_color="#888888")
        lbl_u_desc.pack(pady=(0, 15), padx=20, anchor="w")
        
        row_v = ctk.CTkFrame(self.box_update, fg_color="transparent")
        row_v.pack(fill="x", padx=20, pady=5)
        lbl_v = ctk.CTkLabel(row_v, text="Versi Aplikasi Klien Terbaru:", font=ctk.CTkFont(size=12), width=180, anchor="w")
        lbl_v.pack(side="left")
        self.entry_version = ctk.CTkEntry(row_v, placeholder_text="Contoh: 1.1.0", height=32, width=150)
        self.entry_version.pack(side="left")
        
        row_url = ctk.CTkFrame(self.box_update, fg_color="transparent")
        row_url.pack(fill="x", padx=20, pady=5)
        lbl_url = ctk.CTkLabel(row_url, text="Tautan Unduhan (URL):", font=ctk.CTkFont(size=12), width=180, anchor="w")
        lbl_url.pack(side="left")
        self.entry_url = ctk.CTkEntry(row_url, placeholder_text="https://github.com/...", height=32)
        self.entry_url.pack(side="left", fill="x", expand=True)
        
        self.btn_save_u = ctk.CTkButton(
            self.box_update, text="Simpan & Terapkan Pembaruan",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#10B981", hover_color="#059669", text_color="#FFFFFF",
            width=220, height=35, command=self.save_update_settings
        )
        self.btn_save_u.pack(padx=20, pady=20, anchor="w")
        
        # Load values initially
        self.load_settings_data()
        
    def load_settings_data(self):
        def worker():
            import firebase_handler
            config, _ = firebase_handler.get_update_config()
            if config:
                self.after(0, lambda: self.render_settings_data(config))
        threading.Thread(target=worker, daemon=True).start()
        
    def render_settings_data(self, config):
        self.entry_version.delete(0, tk.END)
        self.entry_version.insert(0, config.get("version", "1.0.0"))
        
        self.entry_url.delete(0, tk.END)
        self.entry_url.insert(0, config.get("update_url", ""))
        
        self.entry_broadcast.delete(0, tk.END)
        self.entry_broadcast.insert(0, config.get("broadcast_message", ""))
        
    def send_broadcast(self):
        msg = self.entry_broadcast.get().strip()
        if not msg:
            messagebox.showwarning("Pesan Kosong", "Masukkan teks pengumuman siaran terlebih dahulu.")
            return
            
        self.btn_send_b.configure(state="disabled", text="Mengirim...")
        
        def worker():
            import firebase_handler
            ok = firebase_handler.set_broadcast_message(self.controller.admin_user['idToken'], msg)
            if ok:
                self.after(0, lambda: messagebox.showinfo("Sukses", "Pesan siaran global berhasil dikirim ke database!"))
            else:
                self.after(0, lambda: messagebox.showerror("Gagal", "Gagal mengirim pesan siaran."))
            self.after(0, lambda: self.btn_send_b.configure(state="normal", text="Kirim Siaran Sekarang"))
            
        threading.Thread(target=worker, daemon=True).start()
        
    def clear_broadcast(self):
        self.btn_clear_b.configure(state="disabled", text="Menghapus...")
        
        def worker():
            import firebase_handler
            ok = firebase_handler.set_broadcast_message(self.controller.admin_user['idToken'], "")
            if ok:
                self.after(0, lambda: self.entry_broadcast.delete(0, tk.END))
                self.after(0, lambda: messagebox.showinfo("Sukses", "Pesan siaran global berhasil dihapus dari database."))
            else:
                self.after(0, lambda: messagebox.showerror("Gagal", "Gagal menghapus pesan siaran."))
            self.after(0, lambda: self.btn_clear_b.configure(state="normal", text="Hapus Siaran Aktif"))
            
        threading.Thread(target=worker, daemon=True).start()
        
    def save_update_settings(self):
        ver = self.entry_version.get().strip()
        url = self.entry_url.get().strip()
        
        if not ver or not url:
            messagebox.showwarning("Form Kosong", "Isi nomor versi dan tautan unduhan update.")
            return
            
        self.btn_save_u.configure(state="disabled", text="Menyimpan...")
        
        def worker():
            import firebase_handler
            ok = firebase_handler.set_update_config(self.controller.admin_user['idToken'], ver, url)
            if ok:
                self.after(0, lambda: messagebox.showinfo("Sukses", "Pengaturan pembaruan aplikasi berhasil disimpan!"))
            else:
                self.after(0, lambda: messagebox.showerror("Gagal", "Gagal menyimpan konfigurasi pembaruan."))
            self.after(0, lambda: self.btn_save_u.configure(state="normal", text="Simpan & Terapkan Pembaruan"))
            
        threading.Thread(target=worker, daemon=True).start()

class AdminApp(ctk.CTk):
    """Main Admin Window Controller with modern sidebar navigation."""
    def __init__(self):
        super().__init__()
        
        self.admin_user = None
        
        # Window settings
        self.title("Bersihin - Dashboard Administrator")
        self.geometry("1280x720")
        self.resizable(True, True)
        self.minsize(960, 540)
        
        # Icon loading
        try:
            base_project_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
            ico_path = os.path.join(base_project_dir, "assets", "logo.ico")
            png_path = os.path.join(base_project_dir, "assets", "logo.png")
            if os.path.exists(ico_path):
                self.iconbitmap(ico_path)
            if os.path.exists(png_path):
                self.img_icon = tk.PhotoImage(file=png_path)
                self.iconphoto(True, self.img_icon)
        except Exception:
            pass
            
        # Try explicit Windows grouping
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("antigravity.bersihin.admin.v1")
        except Exception:
            pass
            
        # Load local session
        session = self.load_admin_session()
        if session:
            self.admin_user = session
            self.show_dashboard()
        else:
            self.show_login()
 
    def show_login(self):
        for w in self.winfo_children():
            w.destroy()
            
        self.login_frame = AdminLoginFrame(self, self)
        self.login_frame.pack(fill="both", expand=True)
 
    def show_dashboard(self):
        for w in self.winfo_children():
            w.destroy()
            
        # Layout Grids
        self.grid_columnconfigure(0, weight=0) # Sidebar
        self.grid_columnconfigure(1, weight=1) # Main Content
        self.grid_rowconfigure(0, weight=1)
        
        # Sidebar Frame
        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0, fg_color="#121212")
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(5, weight=1) # Push lower items to bottom
        
        # Sidebar Header Logo
        lbl_logo = ctk.CTkLabel(
            self.sidebar, text="BERSIHIN ADMIN",
            font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"),
            text_color="#3B82F6"
        )
        lbl_logo.grid(row=0, column=0, padx=20, pady=(25, 25))
        
        # Sidebar Nav Buttons
        self.nav_buttons = {}
        self.create_nav_button("Kelola User", AdminUsersFrame, 1)
        self.create_nav_button("Analitik Global", AdminAnalyticsFrame, 2)
        self.create_nav_button("Pesan & Update", AdminGlobalSettingsFrame, 3)
        
        # Sign Out Button at bottom of sidebar
        btn_signout = ctk.CTkButton(
            self.sidebar, text="Keluar Akun",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            fg_color="#333333", hover_color="#EF4444", text_color="#FFFFFF",
            height=30, command=self.perform_signout
        )
        btn_signout.grid(row=6, column=0, padx=20, pady=(10, 25), sticky="ew")
        
        # Main Content Container
        self.container = ctk.CTkFrame(self, fg_color="#121212", corner_radius=0)
        self.container.grid(row=0, column=1, sticky="nsew")
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)
        
        # Load and stack frames
        self.frames = {}
        for F in (AdminUsersFrame, AdminAnalyticsFrame, AdminGlobalSettingsFrame):
            frame = F(self.container, self)
            self.frames[F] = frame
            
        # Show default frame
        self.show_frame(AdminUsersFrame)
 
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
        for f in self.frames.values():
            f.grid_forget()
            
        frame = self.frames[frame_class]
        frame.grid(row=0, column=0, sticky="nsew")
        
        # Highlight active button
        for cls, btn in self.nav_buttons.items():
            if cls == frame_class:
                btn.configure(fg_color="#1E1E1E", text_color="#3B82F6")
            else:
                btn.configure(fg_color="transparent", text_color="#CCCCCC")
                
        # If showing analytics, trigger reload
        if frame_class == AdminAnalyticsFrame:
            frame.load_analytics_data()
            
        # If showing settings, trigger reload
        if frame_class == AdminGlobalSettingsFrame:
            frame.load_settings_data()
            
        # If showing users list, trigger load users
        if frame_class == AdminUsersFrame:
            frame.load_users()
            
    def perform_signout(self):
        self.clear_admin_session()
        self.admin_user = None
        self.show_login()
        
    def load_admin_session(self):
        if os.path.exists("admin_session.json"):
            try:
                with open("admin_session.json", "r") as f:
                    return json.load(f)
            except Exception:
                pass
        return None
 
    def save_admin_session(self, user_data):
        try:
            with open("admin_session.json", "w") as f:
                json.dump(user_data, f)
        except Exception:
            pass
 
    def clear_admin_session(self):
        if os.path.exists("admin_session.json"):
            try:
                os.remove("admin_session.json")
            except Exception:
                pass
