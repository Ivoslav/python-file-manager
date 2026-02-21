import os
import re

# --- КОНСТАНТИ ---
MAX_UI_FILES = 1000
SYSTEM_PATHS = ['/bin', '/boot', '/etc', '/lib', '/opt', '/sbin', '/sys', '/usr', '/var', 'c:\\windows', 'c:\\program files']
SYSTEM_EXTS = ['.sys', '.dll', '.so', '.exe', '.sh', '.bin']

# --- СТРУКТУРИ ОТ ДАННИ ---
class TreeNode:
    def __init__(self, name):
        self.name = name
        self.files = []      
        self.children = {}   

# --- АЛГОРИТМИ ---
def natural_sort_key(s):
    # Разделя текст и числа за правилно сортиране (file2 преди file10)
    return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', s)]

def format_size(size_in_bytes):
    # Превръща байтовете в четим формат
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_in_bytes < 1024.0:
            return f"{size_in_bytes:.2f} {unit}"
        size_in_bytes /= 1024.0