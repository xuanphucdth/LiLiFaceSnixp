import threading
import pystray
from PIL import Image, ImageDraw
from .settings import OPTIONS, CAMERA_MULTIPLE

def icon_image(on=True):
    im=Image.new('RGBA',(64,64),(0,0,0,0)); d=ImageDraw.Draw(im)
    d.rounded_rectangle((3,3,61,61),radius=15,fill='#124038' if on else '#555b67')
    d.ellipse((19,12,45,40),outline='#6effc8' if on else '#c3c5cb',width=4)
    d.arc((13,32,51,65),185,355,fill='white',width=4)
    for points in [[(8,21),(8,8),(21,8)],[(43,8),(56,8),(56,21)],[(8,43),(8,56),(21,56)],[(43,56),(56,56),(56,43)]]: d.line(points,fill='white',width=3)
    return im

class Tray:
    def __init__(self,app):
        self.app=app
        self.ready=threading.Event()
        item=pystray.MenuItem
        def toggle(key): return lambda *_:app.enqueue('setting',(key,not getattr(app.config,key)))
        def checked(key,value): return lambda _:getattr(app.config,key)==value
        def choose(key,value):
            return lambda icon,menu_item:app.enqueue('setting',(key,value))
        def option_label(key,label,value):
            return lambda _:next(name for name,v in CAMERA_MULTIPLE if v==value) if key=='multiple_faces' and app.config.crop_mode=='camera_box' else label
        def options(key,entries):
            return pystray.Menu(*(item(option_label(key,label,value),choose(key,value),checked=checked(key,value),radio=True) for label,value in entries))
        self.icon=pystray.Icon('LiLiFaceSnixp',icon_image(app.config.auto_face_snip),'LiLiFaceSnixp',pystray.Menu(
            item('LiLiFaceSnixp — Settings',lambda *_:app.enqueue('settings'),default=True),
            item('Auto Face Snip',toggle('auto_face_snip'),checked=lambda _:app.config.auto_face_snip),
            item('Snip Target',options('crop_mode',OPTIONS['crop_mode'])),
            item('Padding',options('padding',[(f'{n}%',n/100) for n in (10,15,20,25,30,40,50)])),
            item('Camera Box Padding',options('camera_box_padding',OPTIONS['camera_box_padding'])),
            item(lambda _:'Multiple Camera Boxes' if app.config.crop_mode=='camera_box' else 'Multiple Faces',options('multiple_faces',OPTIONS['multiple_faces'])),
            item('Capture Monitor',options('capture_mode',OPTIONS['capture_mode'])),
            item('Settings',lambda *_:app.enqueue('settings')),
            item('Start with Windows',toggle('start_with_windows'),checked=lambda _:app.config.start_with_windows),
            pystray.Menu.SEPARATOR,item('Exit',lambda *_:app.enqueue('exit'))))
        def setup(icon):
            icon.visible=True; self.ready.set()
        self.thread=threading.Thread(target=lambda:self.icon.run(setup),name='Tray',daemon=True)
        self.thread.start()

    def refresh(self):
        self.icon.icon=icon_image(self.app.config.auto_face_snip)
        self.icon.title='LiLiFaceSnixp — '+('ON' if self.app.config.auto_face_snip else 'OFF')
        self.icon.update_menu()

    def stop(self): self.icon.stop()
