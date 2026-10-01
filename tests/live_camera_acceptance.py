"""Actual PrtSc/clipboard/overlay against a local synthetic call window (no calls).
Only our own GUI fixture is saved for the optional visual QA checkpoint.
"""
import os,sys,json,time,threading,traceback
from pathlib import Path
sys.path[:0]=[str(Path(__file__).resolve().parent.parent),str(Path(__file__).resolve().parent)]
sys.stdout.reconfigure(encoding='utf-8')
os.environ['LILIFACE_DATA_DIR']=str(Path('test-results/camera-live-data').resolve())
from PIL import Image,ImageTk,ImageGrab,ImageChops
import tkinter as tk
import win32api,win32clipboard,win32gui
from app.capture import enable_dpi_awareness,capture
enable_dpi_awareness()
from app.logger import setup
setup()
from app.application import Application
from app.crop import crop_box
from app.camera_box_detector import camera_crop_box,iou
from app.window_bounds import foreground_bounds
from camera_fixtures import layout,CASES

only=set(sys.argv[1:]); path=Path('test-results/camera-live.json')
report=json.loads(path.read_text()) if only and path.exists() else {}
app=Application(); window=tk.Toplevel(app.root); window.overrideredirect(True); window.attributes('-topmost',True)
window.title('Camera Box acceptance fixture'); window.geometry('1100x800+100+80')
canvas=tk.Canvas(window,highlightthickness=0); canvas.pack(fill='both',expand=True)
photo=None
def pump(seconds=.1):
    until=time.monotonic()+seconds
    while time.monotonic()<until: app.root.update(); time.sleep(.01)
def wait(condition,timeout=12):
    until=time.monotonic()+timeout
    while time.monotonic()<until:
        pump(.03)
        if condition(): return
    raise AssertionError('Timeout waiting for camera workflow')
def stage(name):
    global photo
    if name=='ambiguous': image=Image.open('tests/fixtures/astronaut.png').convert('RGB').resize((1100,800)); boxes=[]
    else:
        boxes,options=CASES[name]; image,_=layout(boxes,**options)
    photo=ImageTk.PhotoImage(image,master=window); canvas.delete('all'); canvas.create_image(0,0,image=photo,anchor='nw')
    window.deiconify(); window.lift(); window.focus_force(); win32api.SetCursorPos((700,700)); pump(.3)
    return image,boxes
def press():
    def inject():
        win32api.keybd_event(0x2C,0,0,0); time.sleep(.04); win32api.keybd_event(0x2C,0,2,0)
    threading.Thread(target=inject,daemon=True).start()
    pump(.12)
def clip():
    result=ImageGrab.grabclipboard(); assert isinstance(result,Image.Image)
    return result.convert('RGB')
def compare(expected):
    actual=clip()
    assert actual.size==expected.size,(actual.size,expected.size)
    assert ImageChops.difference(actual,expected).getbbox() is None
def copied(fn):
    seq=win32clipboard.GetClipboardSequenceNumber(); fn()
    wait(lambda:not app.busy and win32clipboard.GetClipboardSequenceNumber()!=seq)
def check(name,fn):
    if only and name not in only:return
    try: report[name]={'passed':True,'detail':fn()}; print('PASS',name,report[name]['detail'],flush=True)
    except Exception: report[name]={'passed':False,'detail':traceback.format_exc()}; print('FAIL',name,report[name]['detail'],flush=True)

def single():
    image,boxes=stage('single'); copied(press); compare(image.crop(boxes[0])); return 'PrtSc, exact 720x480 camera pixels, zero padding'
def grid():
    app.config.multiple_faces='ask'; image,boxes=stage('grid')
    press(); wait(lambda:app.overlay is not None)
    assert len(app.overlay.faces)==4
    # Screenshot restricted to the fixture area, not any unrelated user window.
    ImageGrab.grab(bbox=(100,80,1200,880)).save('test-results/camera-overlay-qa.png')
    app.overlay.window.event_generate('<KeyPress-2>'); wait(lambda:not app.busy)
    compare(image.crop(boxes[1])); return 'Four camera rectangles; key 2 selects the second tile'
def nearest():
    app.config.multiple_faces='nearest'; image,boxes=stage('self_view')
    win32api.SetCursorPos((100+boxes[1][0]+12,80+boxes[1][1]+12))
    copied(press); compare(image.crop(boxes[1])); return 'Cursor inside self-view selects self-view'
def pip():
    image,boxes=stage('pip'); copied(press); compare(image.crop(boxes[0])); return 'Small PiP boundary, not background window'
def all_boxes():
    app.config.multiple_faces='all'; image,boxes=stage('grid'); copied(press)
    compare(image.crop((100,80,998,688))); return 'Single image contains all four tiles'
def fallback():
    app.config.multiple_faces='largest'; app.config.camera_box_fallback='head'
    image,_=stage('ambiguous'); shot=capture('primary',(700,700)); faces=app.detector.detect(shot.image)
    assert len(faces)==1
    copied(press); compare(shot.image.crop(crop_box(faces,shot.image.size))); return 'Uncertain boundary automatically crops Head'
def candidates():
    app.config.camera_box_fallback='ask'; stage('ambiguous'); previous=clip()
    press(); wait(lambda:app.overlay is not None)
    assert len(app.overlay.faces)>0 and app.overlay.faces[0].confidence<.55
    app.overlay.window.event_generate('<KeyPress-Escape>'); wait(lambda:not app.busy); compare(previous)
    press(); wait(lambda:app.overlay is not None)
    expected=app.overlay.capture.image.crop(camera_crop_box([app.overlay.faces[0]],app.overlay.capture.image.size))
    app.overlay.window.event_generate('<KeyPress-1>'); wait(lambda:not app.busy); compare(expected)
    app.config.camera_box_fallback='head'; return 'Uncertain candidate requires explicit confirmation; Esc preserves clipboard'
def old_head():
    app.config.crop_mode='head'; app.config.multiple_faces='largest'
    stage('single'); shot=capture('primary',(700,700)); faces=app.detector.detect(shot.image)
    copied(press); compare(shot.image.crop(crop_box(faces,shot.image.size)))
    app.config.crop_mode='camera_box'; return 'Switching back to Head preserves previous pixel crop'
def settings():
    stage('single'); window.attributes('-topmost',False); app.show_settings(); pump(.3)
    s=app.settings
    assert s.camera_frame.winfo_ismapped() and s.values['crop_mode'].get()=='Camera Box'
    s.values['camera_box_padding'].set('8 px'); s.apply(); assert app.config.camera_box_padding==8
    s.values['camera_box_padding'].set('0 px'); s.apply()
    w=s.window; w.lift(); w.focus_force(); pump(.15)
    ImageGrab.grab(bbox=(w.winfo_rootx(),w.winfo_rooty(),w.winfo_rootx()+w.winfo_width(),w.winfo_rooty()+w.winfo_height())).save('test-results/camera-settings-qa.png')
    previous=clip(); s.test(); wait(lambda:app.overlay is not None)
    assert app.overlay.preview and len(app.overlay.faces)==1
    app.overlay.cancel(); wait(lambda:not app.busy); compare(previous)
    s.window.destroy(); window.attributes('-topmost',True)
    return 'Camera settings persist; Test Detection previews tiles without copying'
try:
    app.config.crop_mode='camera_box'; app.config.camera_box_search_area='foreground'; app.config.camera_box_padding=0
    app.config.camera_box_fallback='head'; app.config.camera_box_confidence=.55; app.config.multiple_faces='ask'
    app.config.capture_mode='primary'; app.config.auto_face_snip=True
    wait(lambda:app.detector is not None)
    check('A_single_fixture',single); check('B_grid_overlay_fixture',grid)
    check('C_nearest_fixture',nearest); check('D_PiP_fixture',pip); check('All_boxes_fixture',all_boxes)
    check('E_Head_fallback_fixture',fallback); check('Ask_candidates',candidates); check('F_Head_regression',old_head)
    check('Settings_preview',settings)
finally:
    window.destroy(); app.close(); path.write_text(json.dumps(report,indent=2),encoding='utf-8')
sys.exit(0 if all(item['passed'] for item in report.values()) else 1)
