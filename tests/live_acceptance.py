"""Run from project root. Exercises real desktop capture, hook, tray, overlay and DIB.
Only NASA fixture images and optional own-window QA images may be written to disk.
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
import os
os.environ['LILIFACE_DATA_DIR']=str(Path('test-results/live-data').resolve())
import json,time,traceback,threading
from dataclasses import replace
from PIL import Image,ImageTk,ImageGrab,ImageChops
import tkinter as tk
import win32api,win32con,win32gui,win32process
from app.capture import enable_dpi_awareness,capture,cursor_position
enable_dpi_awareness()
from app.logger import setup
setup()
from app.application import Application
from app.crop import crop_box,select
from app.config import save,load
import app.application as module

only=set(sys.argv[1:])
results=json.loads(Path('test-results/live-acceptance.json').read_text()) if only and Path('test-results/live-acceptance.json').exists() else {}
app=Application()
fixture=tk.Toplevel(app.root); fixture.overrideredirect(True); fixture.attributes('-topmost',True)
fixture.geometry('1920x1080+0+0')
canvas=tk.Canvas(fixture,width=1920,height=1080,highlightthickness=0); canvas.pack(fill='both',expand=True)
astronaut=Image.open('tests/fixtures/astronaut.png').convert('RGB')
refs=[]
def pump(seconds=.1):
    deadline=time.monotonic()+seconds
    while time.monotonic()<deadline:
        app.root.update(); time.sleep(.01)
def wait(predicate,timeout=8):
    deadline=time.monotonic()+timeout
    while time.monotonic()<deadline:
        pump(.03)
        if predicate(): return
    raise AssertionError('Timed out waiting for expected state')
def stage(count):
    canvas.delete('all'); refs.clear()
    canvas.create_rectangle(0,0,1920,1080,fill='#243040',outline='')
    canvas.create_text(960,50,text='LiLiFaceSnixp — automated acceptance fixture',fill='white',font=('Segoe UI',22))
    sizes=[380] if count==1 else [300,460,350]
    for i,size in enumerate(sizes[:count]):
        photo=ImageTk.PhotoImage(astronaut.resize((size,size)),master=fixture); refs.append(photo)
        canvas.create_image(130+i*570,220,image=photo,anchor='nw')
    fixture.lift(); fixture.focus_force(); pump(.3)
def press(shift=False,ctrl=False):
    def inject():
        mods=([win32con.VK_LSHIFT] if shift else [])+([win32con.VK_LCONTROL] if ctrl else [])
        for k in mods: win32api.keybd_event(k,0,0,0)
        time.sleep(.05)
        win32api.keybd_event(0x2C,0,0,0); time.sleep(.03); win32api.keybd_event(0x2C,0,2,0)
        for k in reversed(mods): win32api.keybd_event(k,0,2,0)
    threading.Thread(target=inject,daemon=True).start()
    pump(.2)
def clip():
    value=ImageGrab.grabclipboard()
    assert isinstance(value,Image.Image),'Clipboard does not contain bitmap'
    return value.convert('RGB')
def compare(expected):
    actual=clip(); assert actual.size==expected.size,(actual.size,expected.size)
    assert ImageChops.difference(actual,expected).getbbox() is None,'Clipboard pixels differ'
def check(name,fn):
    if only and name not in only: return
    try:
        detail=fn(); results[name]={'passed':True,'detail':str(detail)}; print('PASS',name,detail,flush=True)
    except Exception:
        results[name]={'passed':False,'detail':traceback.format_exc()}; print('FAIL',name,traceback.format_exc(),flush=True)

fallback_calls=[]
original_fallback=module.open_snipping_tool
def fallback_spy():
    fallback_calls.append(time.monotonic())
    original_fallback()
module.open_snipping_tool=fallback_spy
def snipping_windows():
    found=[]
    def visit(hwnd,_):
        if win32gui.IsWindowVisible(hwnd):
            title=win32gui.GetWindowText(hwnd); cls=win32gui.GetClassName(hwnd)
            if any(s in (title+' '+cls).lower() for s in ['snip','screenclipping','screen clipping']): found.append((title,cls))
    win32gui.EnumWindows(visit,None)
    return found
def dismiss():
    win32api.keybd_event(0x1B,0,0,0); win32api.keybd_event(0x1B,0,2,0); pump(.5)
    fixture.lift(); fixture.focus_force(); pump(.15)
def manual_case(auto,shift=False,blank=False):
    app.config.auto_face_snip=auto
    stage(0 if blank else 1)
    before=len(fallback_calls)
    press(shift=shift)
    wait(lambda:len(fallback_calls)>before)
    wait(lambda:bool(snipping_windows()),10)
    found=snipping_windows(); dismiss(); return found
def one_face():
    app.config.auto_face_snip=True; stage(1)
    shot=capture('primary',(800,700)); faces=app.detector.detect(shot.image,.6); assert len(faces)==1,faces
    press(); wait(lambda:not app.busy)
    compare(shot.image.crop(crop_box(faces,shot.image.size)))
    assert app.overlay is None
    return 'Real PrtSc hook → YuNet → Head +25% → clipboard pixel match'
def many(strategy):
    app.config.multiple_faces=strategy; stage(3)
    win32api.SetCursorPos((1350,320)); pump(.1)
    shot=capture('primary',(1350,320)); faces=app.detector.detect(shot.image,.6); assert len(faces)==3,faces
    press()
    if strategy=='ask':
        wait(lambda:app.overlay is not None)
        # Only this own-fixture overlay is saved for the explicit visual QA checkpoint.
        ImageGrab.grab(bbox=(0,0,1920,1080)).save('test-results/overlay-qa.png')
        app.overlay.window.event_generate('<KeyPress-2>'); chosen=[faces[1]]
    else: chosen=select(faces,strategy,(1350,320))
    wait(lambda:not app.busy)
    compare(shot.image.crop(crop_box(chosen,shot.image.size)))
    return f'{len(faces)} detected; strategy={strategy}; exact clipboard pixels'
def full():
    stage(1); shot=capture('primary',(800,700))
    press(ctrl=True); wait(lambda:not app.busy); compare(shot.image); return shot.image.size
def overlay_click_escape():
    app.config.multiple_faces='ask'; stage(3); previous=clip()
    press(); wait(lambda:app.overlay is not None)
    app.overlay.window.event_generate('<KeyPress-Escape>'); wait(lambda:not app.busy); compare(previous)
    press(); wait(lambda:app.overlay is not None)
    face=app.overlay.faces[2]; expected=app.overlay.capture.image.crop(crop_box([face],app.overlay.capture.image.size))
    app.overlay.canvas.event_generate('<Button-1>',x=int(face.x+face.w/2),y=int(face.y+face.h/2))
    wait(lambda:not app.busy); compare(expected)
    return 'Esc preserves clipboard; click selects face 3'
def settings_preview():
    stage(3); fixture.attributes('-topmost',False)
    app.show_settings(); pump(.3)
    w=app.settings.window
    assert w.winfo_width()>300 and w.winfo_height()>300,(w.winfo_width(),w.winfo_height())
    ImageGrab.grab(bbox=(w.winfo_rootx(),w.winfo_rooty(),w.winfo_rootx()+w.winfo_width(),w.winfo_rooty()+w.winfo_height())).save('test-results/settings-qa.png')
    previous=clip(); app.settings.test(); wait(lambda:app.overlay is not None)
    assert app.overlay.preview and len(app.overlay.faces)==3
    app.overlay.cancel(); wait(lambda:not app.busy); compare(previous)
    app.settings.window.destroy(); fixture.attributes('-topmost',True)
    return 'Settings + preview, clipboard unchanged'
def restart_config():
    wanted=replace(app.config,crop_mode='portrait',padding=.4,confidence=.72,multiple_faces='all')
    app.update_config(wanted); assert load()==wanted
    return 'Settings persisted to disk and reloaded'
try:
    app.config.capture_mode='primary'
    app.config.crop_mode='head'; app.config.padding=.25; app.config.confidence=.6
    wait(lambda:app.detector is not None)
    check('Tray',lambda:app.tray.ready.wait(5) or (_ for _ in ()).throw(AssertionError('Tray not ready')))
    check('A_OFF',lambda:manual_case(False))
    check('B_one_face',one_face)
    check('C_ask_keyboard',lambda:many('ask'))
    check('D_largest',lambda:many('largest'))
    check('E_nearest',lambda:many('nearest'))
    check('F_all',lambda:many('all'))
    check('G_no_faces',lambda:manual_case(True,blank=True))
    check('H_manual_override',lambda:manual_case(True,shift=True))
    check('I_full_screenshot',full)
    check('Overlay_click_Esc',overlay_click_escape)
    check('Settings_TestDetection',settings_preview)
    check('J_config_reload',restart_config)
finally:
    fixture.destroy(); app.close()
    Path('test-results/live-acceptance.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
sys.exit(0 if all(r['passed'] for r in results.values()) else 1)
