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


class AdminDashboardFrame(ctk.CTkFrame):
    """Main Administrator Dashboard Frame."""
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="#121212")
        self.controller = controller
        
        self.selected_uid = None
        self.selected_user_data = None
        self.selected_row_widget = None
        self.row_widgets = {}
        
        # Grid Configuration
        self.grid_columnconfigure(0, weight=3) # User Scroll Frame
        self.grid_columnconfigure(1, weight=1) # Action & Detail Frame
        self.grid_rowconfigure(1, weight=1)
        
        # Header Area
        header = ctk.CTkFrame(self, fg_color="#1E1E1E", height=60, corner_radius=0)
        header.grid(row=0, column=0, columnspan=2, sticky="ew")
        header.pack_propagate(False)
        
        lbl_header_title = ctk.CTkLabel(
            header, text="DASHBOARD KELOLA PENGGUNA (BERSIHIN)",
            font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"),
            text_color="#F8FAFC"
        )
        lbl_header_title.pack(side="left", padx=20, pady=15)
        
        # Sign Out Button
        btn_signout = ctk.CTkButton(
            header, text="Keluar Akun",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            fg_color="#333333", hover_color="#EF4444", text_color="#FFFFFF",
            width=100, height=28, command=self.perform_signout
        )
        btn_signout.pack(side="right", padx=20, pady=15)
        
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
        self.detail_frame = ctk.CTkFrame(self.right_panel, fg_color="transparent")
        
        # Detail Title
        self.lbl_detail_title = ctk.CTkLabel(
            self.detail_frame, text="Rincian Pengguna",
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
            text_color="#FFFFFF"
        )
        self.lbl_detail_title.pack(anchor="w", pady=(15, 15))
        
        # Detail items container
        self.details_container = ctk.CTkFrame(self.detail_frame, fg_color="#121212", corner_radius=8)
        self.details_container.pack(fill="x", pady=(0, 20))
        
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
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            fg_color="#EF4444", hover_color="#DC2626", text_color="#FFFFFF",
            height=35, command=self.perform_toggle_block
        )
        self.btn_toggle_block.pack(fill="x", pady=5)
        
        self.btn_toggle_role = ctk.CTkButton(
            self.detail_frame, text="Jadikan Admin",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            fg_color="#3B82F6", hover_color="#2563EB", text_color="#FFFFFF",
            height=35, command=self.perform_toggle_role
        )
        self.btn_toggle_role.pack(fill="x", pady=5)
        
        self.btn_delete_user = ctk.CTkButton(
            self.detail_frame, text="Hapus User dari DB",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            fg_color="#333333", hover_color="#444444", text_color="#EF4444",
            height=35, command=self.perform_delete_user
        )
        self.btn_delete_user.pack(fill="x", pady=(5, 15))

    def create_detail_row(self, label_text, default_val):
        row = ctk.CTkFrame(self.details_container, fg_color="transparent")
        row.pack(fill="x", pady=4, padx=10)
        
        lbl = ctk.CTkLabel(row, text=label_text, font=ctk.CTkFont(size=11), text_color="#888888", width=100, anchor="w")
        lbl.pack(side="left")
        
        val = ctk.CTkLabel(row, text=default_val, font=ctk.CTkFont(size=11, weight="bold"), text_color="#FFFFFF", anchor="w")
        val.pack(side="left", fill="x", expand=True)
        return val

    def load_users(self):
        """Loads and lists all users in the system."""
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
                
            self.after(0, lambda: self.render_users(users))
            
        threading.Thread(target=run, daemon=True).start()

    def render_users(self, users):
        if not users:
            self.lbl_no_selection.configure(text="Tidak ada data pengguna.")
            return
            
        self.lbl_no_selection.configure(text="Pilih pengguna dari daftar\nuntuk melihat rincian & aksi.")
        
        # Filter and render
        search_query = self.search_entry.get().strip().lower()
        
        idx = 0
        for uid, udata in users.items():
            # Skip if username or email does not match search
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
        # Debounce/reload simple
        self.load_users()

    def on_user_selected(self, uid, user_data, widget):
        # Unhighlight previous
        if self.selected_row_widget:
            self.selected_row_widget.unhighlight()
            
        self.selected_uid = uid
        self.selected_user_data = user_data
        self.selected_row_widget = widget
        widget.highlight()
        
        # Hide selection placeholder
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
            
        # Don't allow self-demotion or self-blocking
        is_self = (uid == self.controller.admin_user.get('uid'))
        if is_self:
            self.btn_toggle_block.configure(state="disabled")
            self.btn_toggle_role.configure(state="disabled")
            self.btn_delete_user.configure(state="disabled")
        else:
            self.btn_toggle_block.configure(state="normal")
            self.btn_toggle_role.configure(state="normal")
            self.btn_delete_user.configure(state="normal")
            
        # Show detail frame
        self.detail_frame.pack(fill="both", expand=True, padx=15)

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

    def on_action_success(self):
        messagebox.showinfo("Sukses", "Tindakan berhasil diterapkan!")
        self.load_users()

    def on_delete_success(self):
        messagebox.showinfo("Sukses", "Pengguna berhasil dihapus secara permanen dari database.")
        self.load_users()

    def perform_signout(self):
        self.controller.clear_admin_session()
        self.controller.admin_user = None
        self.controller.show_login()


class AdminApp(ctk.CTk):
    """Main Admin Window Controller."""
    def __init__(self):
        super().__init__()
        
        self.admin_user = None
        
        # Window settings
        self.title("Bersihin - Dashboard Administrator")
        self.geometry("980x600")
        self.resizable(False, False)
        
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
            
        self.dashboard_frame = AdminDashboardFrame(self, self)
        self.dashboard_frame.pack(fill="both", expand=True)
        # Load data on start
        self.dashboard_frame.load_users()

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
