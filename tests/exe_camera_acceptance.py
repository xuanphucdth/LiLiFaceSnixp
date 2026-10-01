"""Packaged Camera Box acceptance with real keyboard/clipboard, isolated config."""
import os,sys,json,time,threading,subprocess
from pathlib import Path
sys.path[:0]=[str(Path(__file__).resolve().parent.parent),str(Path(__file__).resolve().parent)]
import tkinter as tk
from PIL import Image,ImageTk,ImageGrab,ImageChops
import win32api,win32clipboard,win32gui,win32process
from app.capture import enable_dpi_awareness
from app.window_bounds import foreground_bounds
from app.config import Config,save
from camera_fixtures import layout,CASES
enable_dpi_awareness()
root=tk.Tk(); root.overrideredirect(True); root.geometry('1100x800+100+80'); root.attributes('-topmost',True)
canvas=tk.Canvas(root,highlightthickness=0); canvas.pack(fill='both',expand=True)
data=Path('test-results/exe-camera-data').resolve(); log=data/'logs'/'LiLiFaceSnixp.log'
exe=Path('dist/LiLiFaceSnixp/LiLiFaceSnixp.exe').resolve()
env={k:v for k,v in os.environ.items() if not k.upper().startswith(('PYTHON','VIRTUAL_ENV'))}
env['PATH']=str(Path(os.environ['SystemRoot'])/'System32')+';'+os.environ['SystemRoot']; env['LILIFACE_DATA_DIR']=str(data)
photo=None; process=None; report={}
def pump(seconds=.1):
    end=time.monotonic()+seconds
    while time.monotonic()<end: root.update(); time.sleep(.01)
def wait(fn):
    end=time.monotonic()+15
    while time.monotonic()<end:
        pump(.05)
        if fn():return
    raise AssertionError('EXE camera timeout')
def text():return log.read_text(encoding='utf-8') if log.exists() else ''
def stop(proc):
    windows=[]
    def visit(hwnd,_):
        if win32process.GetWindowThreadProcessId(hwnd)[1]==proc.pid and win32gui.GetWindowText(hwnd)=='LiLiFaceSnixp Controller': windows.append(hwnd)
    win32gui.EnumWindows(visit,None)
    for hwnd in windows:win32gui.PostMessage(hwnd,0x10,0,0)
    proc.wait(timeout=6); assert proc.returncode==0
try:
    for name,strategy,index in [('single','ask',0),('grid','ask',1),('self_view','nearest',1),('grid','all',None)]:
        if sys.argv[1:] and f'{name}_{strategy}' not in sys.argv[1:]: continue
        image,faces=layout(*[CASES[name][0]],**CASES[name][1]); boxes=CASES[name][0]
        photo=ImageTk.PhotoImage(image); canvas.delete('all'); canvas.create_image(0,0,image=photo,anchor='nw')
        cfg=Config(crop_mode='camera_box',capture_mode='primary',multiple_faces=strategy)
        save(cfg,data/'config'/'settings.json')
        before=text().count('App started'); process=subprocess.Popen([str(exe)],cwd=str(exe.parent),env=env)
        wait(lambda:text().count('App started')>before)
        root.lift(); root.focus_force(); pump(.25)
        # Windows may deny foreground activation after launching another process.
        # Activate this known topmost fixture with a real click before the shortcut.
        win32api.SetCursorPos((150,130)); win32api.mouse_event(0x0002,0,0,0,0); win32api.mouse_event(0x0004,0,0,0,0)
        pump(.1)
        assert foreground_bounds()==(100,80,1200,880),foreground_bounds()
        win32api.SetCursorPos((100+boxes[-1][0]+20,80+boxes[-1][1]+20))
        seq=win32clipboard.GetClipboardSequenceNumber(); overlays=text().count('Overlay opened')
        def press():
            win32api.keybd_event(0x2C,0,0,0); time.sleep(.04); win32api.keybd_event(0x2C,0,2,0)
        threading.Thread(target=press).start()
        if strategy=='ask' and len(boxes)>1:
            wait(lambda:text().count('Overlay opened')>overlays)
            print('Overlay keyboard target:',win32gui.GetWindowText(win32gui.GetForegroundWindow()),flush=True)
            win32api.keybd_event(ord('2'),0,0,0); win32api.keybd_event(ord('2'),0,2,0)
        wait(lambda:win32clipboard.GetClipboardSequenceNumber()!=seq)
        if index is None:
            bbox=(min(b[0] for b in boxes),min(b[1] for b in boxes),max(b[2] for b in boxes),max(b[3] for b in boxes))
        else:bbox=boxes[index]
        expected=image.crop(bbox); actual=ImageGrab.grabclipboard().convert('RGB')
        assert actual.size==expected.size,(actual.size,expected.size)
        assert ImageChops.difference(actual,expected).getbbox() is None
        report[f'{name}_{strategy}']={'passed':True,'size':actual.size,'real_hotkey':True,'exact_pixels':True}
        stop(process); process=None
finally:
    if process and process.poll() is None:stop(process)
    root.destroy(); Path('test-results/exe-camera.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report,indent=2))
