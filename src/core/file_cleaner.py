import os
import shutil
import ctypes
from ctypes import wintypes
import subprocess
import glob
from pathlib import Path

# Win32 Recycle Bin structures and functions
class SHQUERYRBINFO(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("i64Size", ctypes.c_int64),
        ("i64NumItems", ctypes.c_int64)
    ]

def get_recycle_bin_info():
    """Returns the size (bytes) and number of items in the Recycle Bin."""
    try:
        info = SHQUERYRBINFO()
        info.cbSize = ctypes.sizeof(SHQUERYRBINFO)
        # Pass None to query all drives
        res = ctypes.windll.shell32.SHQueryRecycleBinW(None, ctypes.byref(info))
        if res == 0:
            return info.i64Size, info.i64NumItems
    except Exception:
        pass
    return 0, 0

def empty_recycle_bin():
    """Empties the Recycle Bin on all drives without showing UI or playing sound."""
    try:
        # SHERB_NOCONFIRMATION = 0x00000001
        # SHERB_NOPROGRESSUI = 0x00000002
        # SHERB_NOSOUND = 0x00000004
        # Combined = 7
        res = ctypes.windll.shell32.SHEmptyRecycleBinW(None, None, 7)
        return res == 0 or res == 0x80004005 # E_FAIL (already empty)
    except Exception:
        return False

def get_folder_size(folder_path):
    """Calculates the total size of a folder in bytes, skipping inaccessible files."""
    total_size = 0
    if not os.path.exists(folder_path):
        return 0
        
    try:
        for dirpath, dirnames, filenames in os.walk(folder_path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                # Skip symbolic links and inaccessible files
                if not os.path.islink(fp):
                    try:
                        total_size += os.path.getsize(fp)
                    except (OSError, PermissionError):
                        pass
    except Exception:
        pass
    return total_size

def clean_folder_contents(folder_path):
    """Deletes all files and subfolders inside a folder, skipping locked or protected files."""
    deleted_size = 0
    failed_files = 0
    deleted_files = 0
    
    if not os.path.exists(folder_path):
        return 0, 0, 0
        
    for item in os.listdir(folder_path):
        item_path = os.path.join(folder_path, item)
        if os.path.isdir(item_path):
            # Try to delete subfolder
            try:
                # Calculate size before deletion to track freed space
                folder_size = get_folder_size(item_path)
                shutil.rmtree(item_path)
                deleted_size += folder_size
                deleted_files += 1
            except Exception:
                # If rmtree fails, clean inside it recursively
                d_size, d_files, f_files = clean_folder_contents(item_path)
                deleted_size += d_size
                deleted_files += d_files
                failed_files += f_files
                # Try to remove the empty dir again
                try:
                    os.rmdir(item_path)
                except Exception:
                    pass
        else:
            # Try to delete file
            try:
                file_size = os.path.getsize(item_path)
                os.remove(item_path)
                deleted_size += file_size
                deleted_files += 1
            except Exception:
                failed_files += 1
                
    return deleted_size, deleted_files, failed_files

# Cache paths setup
def get_browser_cache_paths(browser_name):
    """Returns a list of cache directories for specified browsers (Chrome, Edge)."""
    paths = []
    local_appdata = os.environ.get('LOCALAPPDATA', '')
    if not local_appdata:
        return paths
        
    if browser_name.lower() == 'chrome':
        base_dir = os.path.join(local_appdata, 'Google', 'Chrome', 'User Data')
    elif browser_name.lower() == 'edge':
        base_dir = os.path.join(local_appdata, 'Microsoft', 'Edge', 'User Data')
    else:
        return paths
        
    if os.path.exists(base_dir):
        # Search all Profile directories (Default, Profile 1, Profile 2, etc.)
        for profile_dir in glob.glob(os.path.join(base_dir, 'Default')) + glob.glob(os.path.join(base_dir, 'Profile *')):
            cache_path = os.path.join(profile_dir, 'Cache')
            code_cache = os.path.join(profile_dir, 'Code Cache')
            if os.path.exists(cache_path):
                paths.append(cache_path)
            if os.path.exists(code_cache):
                paths.append(code_cache)
                
    return paths

def get_clean_targets():
    """Defines and returns dictionary of cleaner targets with their descriptions and scan logic."""
    local_temp = os.environ.get('TEMP', '')
    windir = os.environ.get('WINDIR', 'C:\\Windows')
    local_appdata = os.environ.get('LOCALAPPDATA', '')
    
    targets = {
        'user_temp': {
            'name': 'File Temp Pengguna',
            'desc': 'File sementara yang dibuat oleh aplikasi yang Anda jalankan.',
            'paths': [local_temp] if local_temp else [],
            'requires_admin': False
        },
        'system_temp': {
            'name': 'File Temp Sistem',
            'desc': 'File sementara yang dibuat oleh sistem operasi Windows.',
            'paths': [os.path.join(windir, 'Temp')],
            'requires_admin': True
        },
        'prefetch': {
            'name': 'Data Prefetch Windows',
            'desc': 'Data start-up aplikasi untuk mempercepat loading (aman dibersihkan).',
            'paths': [os.path.join(windir, 'Prefetch')],
            'requires_admin': True
        },
        'update_cache': {
            'name': 'Cache Windows Update',
            'desc': 'File sisa unduhan pembaruan Windows Update yang sudah terinstal.',
            'paths': [os.path.join(windir, 'SoftwareDistribution', 'Download')],
            'requires_admin': True
        },
        'crash_dumps': {
            'name': 'Laporan Crash & Memory Dumps',
            'desc': 'File dump memori yang dibuat saat Windows atau aplikasi mengalami error.',
            'paths': [
                os.path.join(windir, 'Minidump'),
                os.path.join(local_appdata, 'CrashDumps') if local_appdata else ''
            ],
            'requires_admin': False # Local crashdumps doesn't require admin, minidump does
        },
        'chrome_cache': {
            'name': 'Cache Google Chrome',
            'desc': 'Cache browser Google Chrome (gambar, skrip halaman web yang disimpan).',
            'paths': get_browser_cache_paths('chrome'),
            'requires_admin': False
        },
        'edge_cache': {
            'name': 'Cache Microsoft Edge',
            'desc': 'Cache browser Microsoft Edge.',
            'paths': get_browser_cache_paths('edge'),
            'requires_admin': False
        },
        'recycle_bin': {
            'name': 'Recycle Bin (Keranjang Sampah)',
            'desc': 'File-file yang telah Anda hapus dan berada di keranjang sampah.',
            'paths': [], # Handled by special API
            'requires_admin': False,
            'special': 'recycle_bin'
        },
        'dns_cache': {
            'name': 'DNS Cache Resolver',
            'desc': 'Cache alamat IP domain internet yang disimpan oleh Windows.',
            'paths': [], # Handled by command
            'requires_admin': False,
            'special': 'dns_cache'
        }
    }
    
    # Filter empty paths
    for key in targets:
        if 'paths' in targets[key]:
            targets[key]['paths'] = [p for p in targets[key]['paths'] if p]
            
    return targets

def scan_folder(folder_path):
    """Calculates the total size in bytes and count of files in a single pass."""
    total_size = 0
    total_files = 0
    if not os.path.exists(folder_path):
        return 0, 0
        
    try:
        for dirpath, _, filenames in os.walk(folder_path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                if not os.path.islink(fp):
                    try:
                        total_size += os.path.getsize(fp)
                        total_files += 1
                    except (OSError, PermissionError):
                        pass
    except Exception:
        pass
    return total_size, total_files

def scan_target(key, target_info):
    """Scans a single target and returns its total size in bytes and file count."""
    if 'special' in target_info:
        if target_info['special'] == 'recycle_bin':
            size, count = get_recycle_bin_info()
            return size, count
        elif target_info['special'] == 'dns_cache':
            # DNS Cache does not take disk space but can be flushed. 
            # We return 1 item if we can access it (symbolic).
            return 0, 1
            
    total_size = 0
    total_files = 0
    
    for path in target_info['paths']:
        if os.path.exists(path):
            size, count = scan_folder(path)
            total_size += size
            total_files += count
                
    return total_size, total_files

def clean_target(key, target_info):
    """Cleans a single target, returns (bytes_freed, files_deleted, files_failed)."""
    if 'special' in target_info:
        if target_info['special'] == 'recycle_bin':
            size_before, count_before = get_recycle_bin_info()
            success = empty_recycle_bin()
            if success:
                return size_before, count_before, 0
            else:
                return 0, 0, count_before
        elif target_info['special'] == 'dns_cache':
            try:
                # Run ipconfig /flushdns
                subprocess.run(['ipconfig', '/flushdns'], capture_output=True, check=True, creationflags=subprocess.CREATE_NO_WINDOW)
                return 0, 1, 0
            except Exception:
                return 0, 0, 1
                
    total_freed = 0
    total_deleted = 0
    total_failed = 0
    
    for path in target_info['paths']:
        if os.path.exists(path):
            freed, deleted, failed = clean_folder_contents(path)
            total_freed += freed
            total_deleted += deleted
            total_failed += failed
            
    return total_freed, total_deleted, total_failed


# ================= FITUR PREMIUM: CARI DUPLIKAT & UNINSTALLER SISA =================

import hashlib
import winreg

def find_duplicate_files(directory, progress_callback=None):
    """Memindai direktori untuk mencari file duplikat berdasarkan ukuran & hash MD5."""
    size_map = {}
    duplicates = []
    
    if not os.path.exists(directory):
        return []
        
    try:
        # Walk directory
        for dirpath, _, filenames in os.walk(directory):
            for filename in filenames:
                file_path = os.path.join(dirpath, filename)
                if os.path.islink(file_path):
                    continue
                try:
                    size = os.path.getsize(file_path)
                    if size > 0:
                        size_map.setdefault(size, []).append(file_path)
                except (OSError, PermissionError):
                    pass
    except Exception:
        pass
        
    # Filter ukuran yang memiliki lebih dari 1 file
    potential_dupes = {size: paths for size, paths in size_map.items() if len(paths) > 1}
    
    # Hash cepat MD5 (1024 byte pertama) untuk efisiensi
    quick_hash_map = {}
    for size, paths in potential_dupes.items():
        for path in paths:
            try:
                with open(path, 'rb') as f:
                    chunk = f.read(1024)
                    h = hashlib.md5(chunk).hexdigest()
                    quick_hash_map.setdefault((size, h), []).append(path)
            except Exception:
                pass
                
    # Filter lagi hasil hash cepat
    potential_dupes_2 = {sh: paths for sh, paths in quick_hash_map.items() if len(paths) > 1}
    
    # Hash penuh MD5 untuk memastikan file benar-benar kembar
    full_hash_map = {}
    for (size, qh), paths in potential_dupes_2.items():
        for path in paths:
            try:
                h = hashlib.md5()
                with open(path, 'rb') as f:
                    for chunk in iter(lambda: f.read(4096), b""):
                        h.update(chunk)
                full_hash_map.setdefault(h.hexdigest(), []).append(path)
            except Exception:
                pass
                
    # Format hasil pengembalian
    for file_hash, paths in full_hash_map.items():
        if len(paths) > 1:
            duplicates.append({
                "hash": file_hash,
                "size": os.path.getsize(paths[0]),
                "files": sorted(paths)
            })
            
    return sorted(duplicates, key=lambda x: x['size'] * len(x['files']), reverse=True)

def get_installed_apps():
    """Mengambil daftar perangkat lunak yang terinstal dari Registry Windows."""
    apps = []
    reg_paths = [
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall")
    ]
    
    seen_names = set()
    
    for hive, path in reg_paths:
        try:
            key = winreg.OpenKey(hive, path, 0, winreg.KEY_READ | winreg.KEY_WOW64_64KEY)
            num_subkeys = winreg.QueryInfoKey(key)[0]
            
            for i in range(num_subkeys):
                try:
                    subkey_name = winreg.EnumKey(key, i)
                    subkey = winreg.OpenKey(key, subkey_name, 0, winreg.KEY_READ | winreg.KEY_WOW64_64KEY)
                    
                    try:
                        display_name = winreg.QueryValueEx(subkey, "DisplayName")[0]
                        uninstall_string = winreg.QueryValueEx(subkey, "UninstallString")[0]
                    except FileNotFoundError:
                        continue
                        
                    if not display_name or display_name in seen_names or "KB" in subkey_name:
                        continue
                        
                    publisher = ""
                    try:
                        publisher = winreg.QueryValueEx(subkey, "Publisher")[0]
                    except FileNotFoundError:
                        pass
                        
                    install_loc = ""
                    try:
                        install_loc = winreg.QueryValueEx(subkey, "InstallLocation")[0]
                    except FileNotFoundError:
                        pass
                        
                    seen_names.add(display_name)
                    apps.append({
                        "name": display_name,
                        "uninstall_string": uninstall_string,
                        "install_location": install_loc,
                        "publisher": publisher,
                        "key_name": subkey_name,
                        "hive": "HKLM" if hive == winreg.HKEY_LOCAL_MACHINE else "HKCU",
                        "registry_path": f"{path}\\{subkey_name}"
                    })
                    winreg.CloseKey(subkey)
                except Exception:
                    pass
            winreg.CloseKey(key)
        except Exception:
            pass
            
    return sorted(apps, key=lambda x: x['name'].lower())

def find_app_leftovers(app_name, install_location=None, publisher=None):
    """Memindai direktori sistem dan Registry untuk mencari jejak sisa aplikasi."""
    leftovers = {
        "folders": [],
        "registry_keys": []
    }
    
    keywords = [app_name.lower()]
    short_name = app_name.split()[0].lower()
    if len(short_name) > 2 and short_name not in keywords:
        keywords.append(short_name)
        
    if publisher:
        pub_short = publisher.split()[0].lower()
        if len(pub_short) > 2 and pub_short not in keywords:
            keywords.append(pub_short)
            
    # 1. Pemindaian Direktori
    scan_roots = []
    localappdata = os.environ.get('LOCALAPPDATA', '')
    appdata = os.environ.get('APPDATA', '')
    programfiles = os.environ.get('ProgramFiles', 'C:\\Program Files')
    programfiles_x86 = os.environ.get('ProgramFiles(x86)', 'C:\\Program Files (x86)')
    
    if localappdata: scan_roots.append(localappdata)
    if appdata: scan_roots.append(appdata)
    if programfiles: scan_roots.append(programfiles)
    if programfiles_x86: scan_roots.append(programfiles_x86)
    
    if install_location and os.path.exists(install_location):
        leftovers["folders"].append(install_location)
        
    for root in scan_roots:
        if not os.path.exists(root):
            continue
        try:
            for item in os.listdir(root):
                full_path = os.path.join(root, item)
                if not os.path.isdir(full_path):
                    continue
                item_lower = item.lower()
                for kw in keywords:
                    if kw in item_lower:
                        if full_path not in leftovers["folders"] and full_path not in scan_roots:
                            leftovers["folders"].append(full_path)
                            break
        except Exception:
            pass
            
    # 2. Pemindaian Registry
    reg_roots = [
        (winreg.HKEY_CURRENT_USER, r"Software"),
        (winreg.HKEY_LOCAL_MACHINE, r"Software")
    ]
    
    for hive, path in reg_roots:
        try:
            key = winreg.OpenKey(hive, path, 0, winreg.KEY_READ | winreg.KEY_WOW64_64KEY)
            num_subkeys = winreg.QueryInfoKey(key)[0]
            
            for i in range(num_subkeys):
                try:
                    subkey_name = winreg.EnumKey(key, i)
                    subkey_lower = subkey_name.lower()
                    
                    for kw in keywords:
                        if kw in subkey_lower:
                            hive_name = "HKCU" if hive == winreg.HKEY_CURRENT_USER else "HKLM"
                            full_reg_path = f"{hive_name}\\{path}\\{subkey_name}"
                            if full_reg_path not in leftovers["registry_keys"]:
                                leftovers["registry_keys"].append(full_reg_path)
                            break
                except Exception:
                    pass
            winreg.CloseKey(key)
        except Exception:
            pass
            
    return leftovers

def delete_app_leftovers(folders, registry_keys):
    """Menghapus folder dan subkey registry sisa uninstall."""
    deleted_folders = 0
    deleted_registry = 0
    
    # Hapus Folder
    for f in folders:
        if os.path.exists(f) and os.path.isdir(f):
            try:
                shutil.rmtree(f)
                deleted_folders += 1
            except Exception:
                pass
                
    # Hapus Registry Keys
    for rkey in registry_keys:
        try:
            parts = rkey.split('\\')
            hive_name = parts[0]
            path = "\\".join(parts[1:-1])
            subkey_name = parts[-1]
            
            hive = winreg.HKEY_CURRENT_USER if hive_name == "HKCU" else winreg.HKEY_LOCAL_MACHINE
            
            def delete_key_recursive(parent_hive, parent_path, key_to_delete):
                try:
                    h_key = winreg.OpenKey(parent_hive, f"{parent_path}\\{key_to_delete}", 0, winreg.KEY_ALL_ACCESS | winreg.KEY_WOW64_64KEY)
                except Exception:
                    return False
                    
                while True:
                    try:
                        sub = winreg.EnumKey(h_key, 0)
                        delete_key_recursive(parent_hive, f"{parent_path}\\{key_to_delete}", sub)
                    except OSError:
                        break
                winreg.CloseKey(h_key)
                
                try:
                    winreg.DeleteKey(parent_hive, f"{parent_path}\\{key_to_delete}")
                    return True
                except Exception:
                    return False
                    
            if delete_key_recursive(hive, path, subkey_name):
                deleted_registry += 1
        except Exception:
            pass
            
    return deleted_folders, deleted_registry

