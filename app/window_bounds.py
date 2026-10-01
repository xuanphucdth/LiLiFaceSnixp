"""Snapshot foreground bounds before capture, translated to screenshot coordinates."""
import logging
import win32gui
import mss
from .capture import choose_monitor

def foreground_bounds():
    try:
        hwnd=win32gui.GetForegroundWindow()
        if not hwnd or win32gui.IsIconic(hwnd): return None
        l,t,r,b=win32gui.GetClientRect(hwnd)
        l,t=win32gui.ClientToScreen(hwnd,(l,t)); r,b=win32gui.ClientToScreen(hwnd,(r,b))
        return (l,t,r,b) if r>l and b>t else None
    except Exception:
        logging.exception('Foreground bounds unavailable; using current monitor')
        return None

def local_search_rect(bounds,capture):
    if bounds is None: return None
    l,t,r,b=bounds
    l=max(0,l-capture.left); t=max(0,t-capture.top)
    r=min(capture.image.width,r-capture.left); b=min(capture.image.height,b-capture.top)
    return (l,t,r,b) if r>l and b>t else None

def camera_search_rect(area,bounds,shot,cursor):
    if area=='foreground':
        rect=local_search_rect(bounds,shot)
        if rect is not None: return rect
    try:
        with mss.mss() as sct: monitor=choose_monitor(sct.monitors,'monitor_under_cursor',cursor)
        rect=local_search_rect((monitor['left'],monitor['top'],monitor['left']+monitor['width'],monitor['top']+monitor['height']),shot)
        if rect is not None: return rect
    except Exception: logging.exception('Camera monitor search bounds unavailable; using captured area')
    return (0,0,shot.image.width,shot.image.height)
