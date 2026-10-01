import subprocess
import sys
import winreg
from pathlib import Path

KEY = r'Software\Microsoft\Windows\CurrentVersion\Run'
NAME = 'LiLiFaceSnixp'

def command():
    if getattr(sys,'frozen',False): return subprocess.list2cmdline([sys.executable])
    pythonw = Path(sys.executable).with_name('pythonw.exe')
    return subprocess.list2cmdline([str(pythonw), str(Path(__file__).resolve().parent.parent/'main.py')])

def enabled():
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER,KEY) as key: return bool(winreg.QueryValueEx(key,NAME)[0])
    except FileNotFoundError: return False

def set_enabled(value):
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER,KEY) as key:
        if value: winreg.SetValueEx(key,NAME,0,winreg.REG_SZ,command())
        else:
            try: winreg.DeleteValue(key,NAME)
            except FileNotFoundError: pass
