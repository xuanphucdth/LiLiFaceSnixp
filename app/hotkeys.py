"""User-level keyboard hook on its own message-pump thread; callback only queues work."""
import ctypes
from ctypes import wintypes
import logging
import threading

user32 = ctypes.WinDLL('user32', use_last_error=True)
kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
HOOKPROC = ctypes.WINFUNCTYPE(ctypes.c_ssize_t, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM)
user32.SetWindowsHookExW.argtypes = [ctypes.c_int, HOOKPROC, wintypes.HINSTANCE, wintypes.DWORD]
user32.SetWindowsHookExW.restype = wintypes.HANDLE
user32.CallNextHookEx.argtypes = [wintypes.HANDLE, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM]
user32.CallNextHookEx.restype = ctypes.c_ssize_t
user32.UnhookWindowsHookEx.argtypes = [wintypes.HANDLE]
kernel32.GetModuleHandleW.argtypes = [wintypes.LPCWSTR]
kernel32.GetModuleHandleW.restype = wintypes.HMODULE

class KeyData(ctypes.Structure):
    _fields_ = [('vkCode',wintypes.DWORD),('scanCode',wintypes.DWORD),('flags',wintypes.DWORD),('time',wintypes.DWORD),('extra',ctypes.c_size_t)]

def route(auto, shift=False, ctrl=False, alt=False, win=False):
    if alt or win: return None
    if shift: return 'manual'
    if ctrl: return 'full'
    return 'face' if auto else 'manual'

def overlay_key(vk,preview=False):
    if vk==0x1B: return 'cancel'
    if not preview and (0x31<=vk<=0x39 or 0x61<=vk<=0x69): return (vk & 0x0F)-1
    return None

class Hotkeys:
    def __init__(self, get_auto, dispatch):
        self.get_auto, self.dispatch = get_auto, dispatch
        self.ready = threading.Event()
        self.error = None
        self.thread_id = None
        self.pressed = False
        self.consumed = False
        self.overlay_dispatch = None
        self.overlay_preview = False
        self.overlay_pressed = set()

    def start(self):
        self.thread = threading.Thread(target=self._run, name='Hotkeys', daemon=True)
        self.thread.start()
        if not self.ready.wait(5): raise RuntimeError('Hotkey setup timed out')
        if self.error: raise self.error

    def _run(self):
        self.thread_id = kernel32.GetCurrentThreadId()
        def callback(code, msg, address):
            try:
                if code >= 0:
                    key = ctypes.cast(address, ctypes.POINTER(KeyData)).contents
                    # A background tray process cannot always take foreground focus.
                    # While our full-screen selector is visible, route only its keys
                    # through the existing hook. No GUI work executes on this thread.
                    if key.vkCode in self.overlay_pressed:
                        if msg in (0x101,0x105): self.overlay_pressed.discard(key.vkCode)
                        return 1
                    handler=self.overlay_dispatch
                    if handler and msg in (0x100,0x104):
                        selection=overlay_key(key.vkCode,self.overlay_preview)
                        modified=any(user32.GetAsyncKeyState(vk)&0x8000 for vk in (0x10,0x11,0x12,0x5B,0x5C))
                        if selection is not None and not modified:
                            self.overlay_pressed.add(key.vkCode)
                            handler(selection)
                            return 1
                    if key.vkCode == 0x2C:
                        if msg in (0x100,0x104):
                            if not self.pressed:
                                down = lambda vk: bool(user32.GetAsyncKeyState(vk) & 0x8000)
                                action = route(self.get_auto(),down(0x10),down(0x11),down(0x12),down(0x5B) or down(0x5C))
                                self.pressed, self.consumed = True, action is not None
                                if action:
                                    from .capture import cursor_position
                                    self.dispatch(action,cursor_position())
                            if self.consumed: return 1
                        elif msg in (0x101,0x105):
                            consumed = self.consumed
                            self.pressed = self.consumed = False
                            if consumed: return 1
            except Exception:
                # Fail open: Windows receives the original key if our callback fails.
                self.pressed = self.consumed = False
            return user32.CallNextHookEx(None,code,msg,address)
        self.callback = HOOKPROC(callback)
        hook = user32.SetWindowsHookExW(13,self.callback,kernel32.GetModuleHandleW(None),0)
        if not hook:
            self.error = ctypes.WinError(ctypes.get_last_error()); self.ready.set(); return
        logging.info('Hotkey registered: PrtSc, Shift+PrtSc, Ctrl+PrtSc')
        self.ready.set()
        try:
            msg = wintypes.MSG()
            while user32.GetMessageW(ctypes.byref(msg),None,0,0) > 0:
                user32.TranslateMessage(ctypes.byref(msg)); user32.DispatchMessageW(ctypes.byref(msg))
        finally: user32.UnhookWindowsHookEx(hook)

    def stop(self):
        if self.thread_id: user32.PostThreadMessageW(self.thread_id,0x12,0,0)
