"""Verify the built app in a separate process with a minimal PATH and no Python env."""
import sys,os,json,time,subprocess,threading
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from PIL import Image,ImageTk,ImageGrab,ImageChops
import tkinter as tk
import win32api,win32gui,win32process,win32clipboard
from app.capture import enable_dpi_awareness,capture
from app.config import Config,save
from app.detector import Detector
from app.crop import crop_box
enable_dpi_awareness()
root=tk.Tk(); root.overrideredirect(True); root.geometry('1920x1080+0+0'); root.attributes('-topmost',True)
canvas=tk.Canvas(root,highlightthickness=0,bg='#243040'); canvas.pack(fill='both',expand=True)
sample=Image.open('tests/fixtures/astronaut.png').resize((450,450))
photo=ImageTk.PhotoImage(sample); canvas.create_image(300,200,image=photo,anchor='nw')
data=Path('test-results/exe-live-data').resolve(); data.mkdir(parents=True,exist_ok=True)
cfg=Config(crop_mode='portrait',padding=.4,confidence=.72,capture_mode='primary',multiple_faces='largest')
save(cfg,data/'config'/'settings.json')
env={k:v for k,v in os.environ.items() if not k.upper().startswith(('PYTHON','VIRTUAL_ENV'))}
env['PATH']=str(Path(os.environ['SystemRoot'])/'System32')+';'+os.environ['SystemRoot']
env['LILIFACE_DATA_DIR']=str(data)
exe=Path('dist/LiLiFaceSnixp/LiLiFaceSnixp.exe').resolve()
log=data/'logs'/'LiLiFaceSnixp.log'
def pump(seconds=.1):
    end=time.monotonic()+seconds
    while time.monotonic()<end: root.update(); time.sleep(.01)
def wait(fn,timeout=12):
    end=time.monotonic()+timeout
    while time.monotonic()<end:
        pump(.05)
        if fn():return
    raise AssertionError('Timed out')
def logtext(): return log.read_text(encoding='utf-8') if log.exists() else ''
def stop(process):
    windows=[]
    def find(hwnd,_):
        if win32process.GetWindowThreadProcessId(hwnd)[1]==process.pid and win32gui.GetWindowText(hwnd)=='LiLiFaceSnixp Controller': windows.append(hwnd)
    win32gui.EnumWindows(find,None)
    for hwnd in windows: win32gui.PostMessage(hwnd,0x10,0,0)
    try: process.wait(timeout=5)
    except subprocess.TimeoutExpired: process.terminate(); process.wait(timeout=5); raise AssertionError('App did not exit cleanly')
report={}; process=None
try:
    for run in (1,2):
        before=logtext().count('App started')
        process=subprocess.Popen([str(exe)],env=env,cwd=str(exe.parent))
        wait(lambda:logtext().count('App started')>before)
        assert process.poll() is None
        root.lift(); root.focus_force(); pump(.3)
        shot=capture('primary',(800,700)); faces=Detector().detect(shot.image,cfg.confidence); assert len(faces)==1
        expected=shot.image.crop(crop_box(faces,shot.image.size,cfg.crop_mode,cfg.padding))
        seq=win32clipboard.GetClipboardSequenceNumber()
        def press():
            win32api.keybd_event(0x2C,0,0,0); time.sleep(.04); win32api.keybd_event(0x2C,0,2,0)
        threading.Thread(target=press).start()
        wait(lambda:win32clipboard.GetClipboardSequenceNumber()!=seq)
        actual=ImageGrab.grabclipboard().convert('RGB')
        assert actual.size==expected.size and ImageChops.difference(actual,expected).getbbox() is None
        stop(process); assert process.returncode==0; process=None
        report[f'run_{run}']={'passed':True,'clipboard_size':actual.size,'saved_settings':cfg.__dict__}
    report['J_restart']={'passed':True,'detail':'Two separate EXE processes used persisted nondefault settings'}
    report['K_standalone']={'passed':True,'detail':'EXE started with no Python PATH/venv variables; actual hotkey, YuNet, clipboard and graceful exit verified'}
finally:
    if process and process.poll() is None: stop(process)
    root.destroy()
    Path('test-results/exe-acceptance.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report,indent=2))
