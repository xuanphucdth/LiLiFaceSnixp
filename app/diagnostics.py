"""Explicit opt-in packaged smoke test. Never saves captured screen pixels."""
import json
import traceback
from pathlib import Path
from PIL import Image

def run(report_path):
    result={}
    def check(name,fn):
        try: result[name]={'passed':True,'detail':str(fn())}
        except Exception: result[name]={'passed':False,'detail':traceback.format_exc()}
    from .capture import capture,cursor_position
    from .detector import Detector
    from .clipboard import dib_bytes
    from .paths import MODEL,ROOT
    from .crop import crop_box,Face
    from .config import Config
    import tkinter as tk
    import win32clipboard
    import pystray
    check('model_bundle',lambda: (MODEL.exists(),MODEL.stat().st_size))
    check('detector_load_inference',lambda:Detector().detect(Image.new('RGB',(320,320)),.6))
    check('capture',lambda:capture('monitor_under_cursor',cursor_position()).image.size)
    check('clipboard_conversion',lambda:len(dib_bytes(Image.new('RGB',(8,8)))))
    check('crop',lambda:crop_box([Face(20,20,40,40)],(100,100)))
    check('icon_bundle',lambda:(ROOT/'assets'/'LiLiFaceSnixp.ico').stat().st_size)
    def gui():
        root=tk.Tk(); root.withdraw(); root.update(); root.destroy(); return 'Tk initialized'
    check('gui_dependencies',gui)
    check('default_config',lambda:Config())
    def camera_smoke():
        from .camera_box_detector import detect_camera_boxes
        result=detect_camera_boxes(Image.new('RGB',(320,240),'#343434'),[Face(100,60,40,50)])
        assert not result.boxes, 'Flat scene must not yield a confident tile'
        return 'Camera module loaded; ambiguous image rejected'
    check('camera_module',camera_smoke)
    report_path.parent.mkdir(parents=True,exist_ok=True)
    report_path.write_text(json.dumps(result,indent=2),encoding='utf-8')
    return 0 if all(r['passed'] for r in result.values()) else 1
