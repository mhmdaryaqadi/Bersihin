import ctypes
from ctypes import wintypes
import psutil
import sys

# Windows API Constants
TOKEN_ADJUST_PRIVILEGES = 0x0020
TOKEN_QUERY = 0x0008
SE_PRIVILEGE_ENABLED = 0x00000002

PROCESS_QUERY_INFORMATION = 0x0400
PROCESS_SET_QUOTA = 0x0100

# Structures for adjusting token privileges
class LUID(ctypes.Structure):
    _fields_ = [("LowPart", wintypes.DWORD), ("HighPart", wintypes.LONG)]

class LUID_AND_ATTRIBUTES(ctypes.Structure):
    _fields_ = [("Luid", LUID), ("Attributes", wintypes.DWORD)]

class TOKEN_PRIVILEGES(ctypes.Structure):
    _fields_ = [("PrivilegeCount", wintypes.DWORD), ("Privileges", LUID_AND_ATTRIBUTES * 1)]

def is_admin():
    """Checks if the script is running with administrator privileges."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except:
        return False

def enable_privilege(privilege_name):
    """Enables a specific privilege in the current process access token."""
    token = wintypes.HANDLE()
    if not ctypes.windll.advapi32.OpenProcessToken(
        ctypes.windll.kernel32.GetCurrentProcess(),
        TOKEN_ADJUST_PRIVILEGES | TOKEN_QUERY,
        ctypes.byref(token)
    ):
        return False

    luid = LUID()
    if not ctypes.windll.advapi32.LookupPrivilegeValueW(None, privilege_name, ctypes.byref(luid)):
        ctypes.windll.kernel32.CloseHandle(token)
        return False

    tp = TOKEN_PRIVILEGES()
    tp.PrivilegeCount = 1
    tp.Privileges[0].Luid = luid
    tp.Privileges[0].Attributes = SE_PRIVILEGE_ENABLED

    res = ctypes.windll.advapi32.AdjustTokenPrivileges(
        token, False, ctypes.byref(tp), 0, None, None
    )
    
    ctypes.windll.kernel32.CloseHandle(token)
    return res != 0

def clean_process_working_sets():
    """Iterates through all running processes and empties their working sets."""
    cleaned_count = 0
    failed_count = 0
    
    # Enable SeIncreaseQuotaPrivilege to clean system/other processes (if admin)
    enable_privilege("SeIncreaseQuotaPrivilege")
    
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            pid = proc.info['pid']
            # Open process with PROCESS_QUERY_INFORMATION | PROCESS_SET_QUOTA
            h_process = ctypes.windll.kernel32.OpenProcess(
                PROCESS_QUERY_INFORMATION | PROCESS_SET_QUOTA, 
                False, 
                pid
            )
            if h_process:
                success = ctypes.windll.psapi.EmptyWorkingSet(h_process)
                ctypes.windll.kernel32.CloseHandle(h_process)
                if success:
                    cleaned_count += 1
                else:
                    failed_count += 1
            else:
                failed_count += 1
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            failed_count += 1
        except Exception:
            failed_count += 1
            
    return cleaned_count, failed_count

def clean_system_file_cache():
    """Flushes the Windows System File Cache."""
    if not is_admin():
        return False, "Diperlukan hak akses Administrator untuk membersihkan System Cache."
        
    if not enable_privilege("SeIncreaseQuotaPrivilege"):
        return False, "Gagal mengaktifkan hak istimewa SeIncreaseQuotaPrivilege."
        
    SIZE_T = ctypes.c_size_t
    DWORD = wintypes.DWORD
    
    # Configure argument and result types for SetSystemFileCacheSize
    ctypes.windll.kernel32.SetSystemFileCacheSize.argtypes = [SIZE_T, SIZE_T, DWORD]
    ctypes.windll.kernel32.SetSystemFileCacheSize.restype = wintypes.BOOL
    
    # Cast -1 to SIZE_T to signal flush cache
    success = ctypes.windll.kernel32.SetSystemFileCacheSize(SIZE_T(-1), SIZE_T(-1), DWORD(0))
    if not success:
        err = ctypes.GetLastError()
        return False, f"Gagal mengosongkan cache file sistem (Error code: {err})."
        
    return True, "System File Cache berhasil dikosongkan."

def clean_standby_list():
    """Purges the Windows Standby Memory List."""
    if not is_admin():
        return False, "Diperlukan hak akses Administrator untuk membersihkan Standby List."
        
    if not enable_privilege("SeProfileSingleProcessPrivilege"):
        return False, "Gagal mengaktifkan hak istimewa SeProfileSingleProcessPrivilege."
        
    SystemMemoryListInformation = 80
    MemoryPurgeStandbyList = 4
    
    command = ctypes.c_int(MemoryPurgeStandbyList)
    status = ctypes.windll.ntdll.NtSetSystemInformation(
        SystemMemoryListInformation,
        ctypes.byref(command),
        ctypes.sizeof(command)
    )
    
    if status != 0:
        return False, f"Gagal mengosongkan Standby List (NTSTATUS: {hex(status & 0xffffffff)})."
        
    return True, "Standby List berhasil dibersihkan."

def get_ram_usage():
    """Returns real-time RAM usage statistics."""
    mem = psutil.virtual_memory()
    # Cache and standby are included in psutil's cached attribute on some platforms,
    # but on Windows we can approximate cached from performance counters if needed.
    # We will use standard psutil parameters which are reliable.
    return {
        'total': mem.total,
        'available': mem.available,
        'percent': mem.percent,
        'used': mem.used,
        'free': mem.free
    }

def get_top_processes(limit=10):
    """Returns top memory consuming processes."""
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'memory_info']):
        try:
            mem = proc.info['memory_info'].rss
            processes.append({
                'pid': proc.info['pid'],
                'name': proc.info['name'],
                'memory': mem
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
            
    # Sort by memory descending
    processes.sort(key=lambda x: x['memory'], reverse=True)
    return processes[:limit]
