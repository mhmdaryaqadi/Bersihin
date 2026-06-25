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
            total_size += get_folder_size(path)
            # Count files
            try:
                for _, _, filenames in os.walk(path):
                    total_files += len(filenames)
            except Exception:
                pass
                
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
