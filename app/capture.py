import ctypes
from ctypes import wintypes
from dataclasses import dataclass
import logging
import mss
from PIL import Image

def enable_dpi_awareness():
    try: ctypes.windll.user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
    except (AttributeError, OSError): ctypes.windll.shcore.SetProcessDpiAwareness(2)

def cursor_position():
    p = wintypes.POINT()
    if not ctypes.windll.user32.GetCursorPos(ctypes.byref(p)): raise ctypes.WinError()
    return p.x, p.y

def choose_monitor(monitors, mode, cursor):
    if mode == 'all': return monitors[0]
    if mode == 'primary':
        return next((m for m in monitors[1:] if m['left'] == 0 and m['top'] == 0), monitors[1])
    x, y = cursor
    for m in monitors[1:]:
        if m['left'] <= x < m['left']+m['width'] and m['top'] <= y < m['top']+m['height']: return m
    raise ValueError('Cursor is not on a connected monitor')

@dataclass
class Capture:
    image: Image.Image
    left: int
    top: int

    def local_cursor(self, cursor): return cursor[0]-self.left, cursor[1]-self.top

def capture(mode, cursor):
    with mss.mss() as sct:
        monitor = choose_monitor(sct.monitors, mode, cursor)
        shot = sct.grab(monitor)
        image = Image.frombytes('RGB', shot.size, shot.bgra, 'raw', 'BGRX')
    logging.info('Screenshot captured: dimensions=%s origin=(%s,%s) mode=%s', image.size, monitor['left'], monitor['top'], mode)
    return Capture(image, monitor['left'], monitor['top'])
