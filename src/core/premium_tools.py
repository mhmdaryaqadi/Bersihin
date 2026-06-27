import os
import winreg
import stat
import subprocess

def scan_invalid_registry():
    """Scans for invalid uninstall references and dead shared DLLs.
    Returns:
        tuple: (list of invalid_uninstall_items, list of dead_shared_dll_items)
    """
    invalid_uninstalls = []
    dead_dlls = []
    
    # 1. Scan HKLM & HKCU Uninstall keys
    uninstall_paths = [
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Uninstall")
    ]
    
    for hkey, path in uninstall_paths:
        try:
            key = winreg.OpenKey(hkey, path, 0, winreg.KEY_READ)
            num_subkeys = winreg.QueryInfoKey(key)[0]
            for i in range(num_subkeys):
                subkey_name = winreg.EnumKey(key, i)
                try:
                    sub_path = f"{path}\\{subkey_name}"
                    subkey = winreg.OpenKey(hkey, sub_path, 0, winreg.KEY_READ)
                    
                    display_name = ""
                    try:
                        display_name = winreg.QueryValueEx(subkey, "DisplayName")[0]
                    except Exception:
                        pass
                        
                    if not display_name:
                        display_name = subkey_name
                        
                    install_loc = ""
                    try:
                        install_loc = winreg.QueryValueEx(subkey, "InstallLocation")[0].strip()
                    except Exception:
                        pass
                        
                    display_icon = ""
                    try:
                        display_icon = winreg.QueryValueEx(subkey, "DisplayIcon")[0].strip()
                        # Remove quotes and comma index
                        if display_icon.startswith('"') and display_icon.endswith('"'):
                            display_icon = display_icon[1:-1]
                        if ',' in display_icon:
                            display_icon = display_icon.split(',')[0].strip()
                    except Exception:
                        pass
                        
                    winreg.CloseKey(subkey)
                    
                    # Validate paths
                    is_invalid = False
                    reason = ""
                    if install_loc and not os.path.exists(install_loc):
                        is_invalid = True
                        reason = f"Folder instalasi tidak ditemukan: {install_loc}"
                    elif display_icon and not os.path.exists(display_icon) and not install_loc:
                        is_invalid = True
                        reason = f"Ikon aplikasi tidak ditemukan: {display_icon}"
                        
                    if is_invalid:
                        invalid_uninstalls.append({
                            "hkey": int(hkey),
                            "path": sub_path,
                            "name": display_name,
                            "reason": reason
                        })
                except Exception:
                    pass
            winreg.CloseKey(key)
        except Exception:
            pass
            
    # 2. Scan Shared DLLs
    shared_dll_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\SharedDlls"
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, shared_dll_path, 0, winreg.KEY_READ)
        num_values = winreg.QueryInfoKey(key)[1]
        for i in range(num_values):
            val_name, val_data, val_type = winreg.EnumValue(key, i)
            if val_name and not os.path.exists(val_name):
                dead_dlls.append({
                    "name": val_name,
                    "count": val_data,
                    "path": shared_dll_path
                })
        winreg.CloseKey(key)
    except Exception:
        pass
        
    return invalid_uninstalls, dead_dlls

def clean_invalid_registry(uninstalls, dlls):
    """Cleans selected invalid registry entries.
    Returns:
        tuple: (count of uninstalls cleaned, count of dlls cleaned)
    """
    uninstalls_cleaned = 0
    dlls_cleaned = 0
    
    # 1. Clean uninstalls
    for item in uninstalls:
        try:
            hkey = int(item["hkey"])
            path = item["path"]
            parent_path, key_name = path.rsplit('\\', 1)
            parent_key = winreg.OpenKey(hkey, parent_path, 0, winreg.KEY_ALL_ACCESS)
            winreg.DeleteKey(parent_key, key_name)
            winreg.CloseKey(parent_key)
            uninstalls_cleaned += 1
        except Exception:
            pass
            
    # 2. Clean dlls
    if dlls:
        try:
            shared_dll_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\SharedDlls"
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, shared_dll_path, 0, winreg.KEY_ALL_ACCESS)
            for item in dlls:
                try:
                    winreg.DeleteValue(key, item["name"])
                    dlls_cleaned += 1
                except Exception:
                    pass
            winreg.CloseKey(key)
        except Exception:
            pass
            
    return uninstalls_cleaned, dlls_cleaned

def find_large_files(target_dir, min_size_mb=100):
    """Finds files larger than min_size_mb in target_dir.
    Returns:
        list: list of dicts with name, path, size (bytes)
    """
    large_files = []
    min_bytes = min_size_mb * 1024 * 1024
    
    for root, dirs, files in os.walk(target_dir):
        if any(p in root for p in ["System Volume Information", "$RECYCLE.BIN", "Windows\\CSC"]):
            continue
        for file in files:
            filepath = os.path.join(root, file)
            try:
                size = os.path.getsize(filepath)
                if size >= min_bytes:
                    large_files.append({
                        "name": file,
                        "path": filepath,
                        "size": size
                    })
            except Exception:
                pass
    large_files.sort(key=lambda x: x["size"], reverse=True)
    return large_files

def list_context_menus():
    """Lists Context Menu Handlers for file (*) and directory background.
    Returns:
        list: list of dicts containing name, key_path, enabled, registry_key, clsid
    """
    handlers = []
    
    paths = [
        (winreg.HKEY_CLASSES_ROOT, r"*\shellex\ContextMenuHandlers", "File"),
        (winreg.HKEY_CLASSES_ROOT, r"Directory\Background\shellex\ContextMenuHandlers", "Folder Background")
    ]
    
    for hkey, parent_path, category in paths:
        try:
            key = winreg.OpenKey(hkey, parent_path, 0, winreg.KEY_READ)
            num_subkeys = winreg.QueryInfoKey(key)[0]
            for i in range(num_subkeys):
                name = winreg.EnumKey(key, i)
                if name.lower() in ["property sheet shell extension", "workfolders"]:
                    continue
                    
                enabled = True
                display_name = name
                actual_name = name
                
                if name.startswith("-"):
                    enabled = False
                    display_name = name[1:]
                
                try:
                    subkey = winreg.OpenKey(key, name, 0, winreg.KEY_READ)
                    clsid = ""
                    try:
                        clsid = winreg.QueryValue(subkey, None)
                    except Exception:
                        pass
                    winreg.CloseKey(subkey)
                except Exception:
                    clsid = ""
                    
                handlers.append({
                    "name": display_name,
                    "actual_name": actual_name,
                    "category": category,
                    "hkey": int(hkey),
                    "parent_path": parent_path,
                    "enabled": enabled,
                    "clsid": clsid
                })
            winreg.CloseKey(key)
        except Exception:
            pass
            
    return handlers

def toggle_context_menu(handler_item):
    """Enables or disables context menu item by renaming its registry key.
    Returns:
        bool: True if success, else False
    """
    hkey = int(handler_item["hkey"])
    parent_path = handler_item["parent_path"]
    actual_name = handler_item["actual_name"]
    enabled = handler_item["enabled"]
    
    old_path = f"{parent_path}\\{actual_name}"
    
    if enabled:
        if actual_name.startswith("-"):
            new_name = actual_name[1:]
        else:
            return True
    else:
        if not actual_name.startswith("-"):
            new_name = f"-{actual_name}"
        else:
            return True
            
    new_path = f"{parent_path}\\{new_name}"
    
    try:
        def copy_key(src_hkey, src_path, dst_hkey, dst_path):
            src_key = winreg.OpenKey(src_hkey, src_path, 0, winreg.KEY_READ)
            dst_key = winreg.CreateKey(dst_hkey, dst_path)
            
            try:
                default_val = winreg.QueryValue(src_key, None)
                if default_val is not None:
                    winreg.SetValue(dst_key, None, winreg.REG_SZ, default_val)
            except Exception:
                pass
                
            num_vals = winreg.QueryInfoKey(src_key)[1]
            for i in range(num_vals):
                val_name, val_data, val_type = winreg.EnumValue(src_key, i)
                winreg.SetValueEx(dst_key, val_name, 0, val_type, val_data)
                
            num_subkeys = winreg.QueryInfoKey(src_key)[0]
            for i in range(num_subkeys):
                sub_name = winreg.EnumKey(src_key, i)
                copy_key(src_hkey, f"{src_path}\\{sub_name}", dst_hkey, f"{dst_path}\\{sub_name}")
                
            winreg.CloseKey(src_key)
            winreg.CloseKey(dst_key)
            
        def delete_key_recursively(target_hkey, target_path):
            try:
                key = winreg.OpenKey(target_hkey, target_path, 0, winreg.KEY_ALL_ACCESS)
            except WindowsError:
                return
            subkeys = []
            try:
                num_subkeys = winreg.QueryInfoKey(key)[0]
                for i in range(num_subkeys):
                    subkeys.append(winreg.EnumKey(key, i))
            except Exception:
                pass
            winreg.CloseKey(key)
            
            for sub in subkeys:
                delete_key_recursively(target_hkey, f"{target_path}\\{sub}")
                
            parent_p, key_n = target_path.rsplit('\\', 1)
            p_key = winreg.OpenKey(target_hkey, parent_p, 0, winreg.KEY_ALL_ACCESS)
            winreg.DeleteKey(p_key, key_n)
            winreg.CloseKey(p_key)
            
        copy_key(hkey, old_path, hkey, new_path)
        delete_key_recursively(hkey, old_path)
        return True
    except Exception:
        return False

def check_browser_running(process_names=["chrome.exe", "msedge.exe"]):
    """Checks if any process in process_names is currently running.
    Returns:
        list: list of running process names
    """
    import psutil
    running = []
    for proc in psutil.process_iter(['name']):
        try:
            name = proc.info['name'].lower()
            if name in process_names and name not in running:
                running.append(name)
        except Exception:
            pass
    return running

def force_close_browsers(process_names=["chrome.exe", "msedge.exe"]):
    """Force terminates specified browser processes.
    """
    import psutil
    for proc in psutil.process_iter(['name']):
        try:
            name = proc.info['name'].lower()
            if name in process_names:
                proc.terminate()
        except Exception:
            pass

def clear_browser_privacy(chrome_history=True, chrome_cookies=True, edge_history=True, edge_cookies=True):
    """Clears SQLite history/cookies databases for Chrome and Edge.
    Returns:
        dict: success status and list of files deleted
    """
    user_profile = os.environ.get("USERPROFILE", "")
    targets = []
    
    if chrome_history:
        targets.append(os.path.join(user_profile, r"AppData\Local\Google\Chrome\User Data\Default\History"))
    if chrome_cookies:
        targets.append(os.path.join(user_profile, r"AppData\Local\Google\Chrome\User Data\Default\Network\Cookies"))
        
    if edge_history:
        targets.append(os.path.join(user_profile, r"AppData\Local\Microsoft\Edge\User Data\Default\History"))
    if edge_cookies:
        targets.append(os.path.join(user_profile, r"AppData\Local\Microsoft\Edge\User Data\Default\Network\Cookies"))
        
    deleted_files = []
    failed_files = []
    
    for path in targets:
        if os.path.exists(path):
            try:
                try:
                    os.chmod(path, stat.S_IWRITE)
                except Exception:
                    pass
                os.remove(path)
                deleted_files.append(path)
            except Exception:
                failed_files.append(path)
                
    return {
        "success": len(failed_files) == 0,
        "deleted": deleted_files,
        "failed": failed_files
    }

def optimize_internet_settings():
    """Applies network performance tweaks in Registry and resets TCP/IP.
    Returns:
        tuple: (bool registry_success, str network_reset_output)
    """
    reg_success = True
    
    tcpip_path = r"SYSTEM\CurrentControlSet\Services\Tcpip\Parameters"
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, tcpip_path, 0, winreg.KEY_ALL_ACCESS)
        winreg.SetValueEx(key, "DefaultTTL", 0, winreg.REG_DWORD, 64)
        winreg.SetValueEx(key, "Tcp1323Opts", 0, winreg.REG_DWORD, 1)
        winreg.SetValueEx(key, "MaxUserPort", 0, winreg.REG_DWORD, 65534)
        winreg.SetValueEx(key, "TcpTimedWaitDelay", 0, winreg.REG_DWORD, 30)
        winreg.CloseKey(key)
    except Exception:
        reg_success = False
        
    output = []
    commands = [
        "netsh winsock reset",
        "netsh int ip reset",
        "ipconfig /flushdns"
    ]
    for cmd in commands:
        try:
            res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            output.append(f"> {cmd}\n{res.stdout}")
        except Exception as e:
            output.append(f"> {cmd}\nFailed: {e}")
            
    return reg_success, "\n".join(output)
