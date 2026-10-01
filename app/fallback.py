import logging
import os
import threading
import time
import win32api
import win32con

def open_snipping_tool():
    """Ask the Windows shell for its normal snip UI without changing any settings."""
    def launch():
        try:
            # Let the physical shortcut be released before injecting Win+Shift+S.
            deadline = time.monotonic()+2
            while any(win32api.GetAsyncKeyState(k)&0x8000 for k in (0x10,0x11,0x2C)) and time.monotonic()<deadline:
                time.sleep(.02)
            keys = (win32con.VK_LWIN,win32con.VK_LSHIFT,ord('S'))
            try:
                for key in keys: win32api.keybd_event(key,0,0,0)
            finally:
                for key in reversed(keys): win32api.keybd_event(key,0,win32con.KEYEVENTF_KEYUP,0)
            logging.info('Fallback opened: Windows Win+Shift+S')
        except Exception:
            logging.exception('Snipping shortcut failed')
            try: os.startfile('ms-screenclip:')
            except Exception: logging.exception('Snipping URI failed')
    threading.Thread(target=launch,name='SnippingFallback',daemon=True).start()
