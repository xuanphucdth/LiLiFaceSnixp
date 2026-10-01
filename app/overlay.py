import ctypes
import logging
import tkinter as tk
from ctypes import wintypes
from PIL import ImageTk, ImageEnhance

user32=ctypes.windll.user32
user32.GetParent.argtypes=[wintypes.HWND]
user32.GetParent.restype=wintypes.HWND
user32.SetWindowPos.argtypes=[wintypes.HWND,wintypes.HWND,ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_int,wintypes.UINT]

class Overlay:
    """Near-transparent-looking frozen desktop. Original pixels stay untouched in RAM."""
    def __init__(self, root, capture, faces, on_select, preview=False, label='faces'):
        self.capture,self.faces,self.on_select,self.preview = capture,faces,on_select,preview
        self.closed = False
        self.window = tk.Toplevel(root)
        self.window.title('LiLiFaceSnixp Selection')
        self.window.withdraw()
        self.window.overrideredirect(True)
        self.window.attributes('-topmost',True)
        self.window.configure(bg='#010203')
        w,h = capture.image.size
        self.window.geometry(f'{w}x{h}+0+0')
        self.canvas = tk.Canvas(self.window,bg='#010203',highlightthickness=0)
        self.canvas.pack(fill='both',expand=True)
        self.background=ImageTk.PhotoImage(ImageEnhance.Brightness(capture.image).enhance(.94),master=self.window)
        self.canvas.create_image(0,0,image=self.background,anchor='nw')
        for index,face in enumerate(faces):
            x,y,r,b=face.box
            self.canvas.create_rectangle(x,y,r,b,outline='#20f0bb',width=3)
            self.canvas.create_rectangle(x,max(36,y-27),x+58,max(36,y-27)+25,fill='#083c35',outline='')
            self.canvas.create_text(x+7,max(36,y-27)+12,text=f'{index+1}',fill='white',anchor='w',font=('Segoe UI',12,'bold'))
        text = (f'Test Detection: {len(faces)} {label} | Esc / Close' if preview else f'Choose {label}: click a box or press 1–9 | Esc: cancel')
        self.canvas.create_rectangle(0,0,min(w-110,1000),34,fill='#13253a',outline='')
        self.canvas.create_text(12,17,text=text,anchor='w',fill='white',font=('Segoe UI',11))
        button=tk.Button(self.window,text='Close' if preview else 'Cancel',command=self.cancel)
        self.canvas.create_window(w-55,18,window=button)
        self.canvas.bind('<Button-1>',self.click)
        self.window.bind('<Key>',self.key)
        self.window.protocol('WM_DELETE_WINDOW',self.cancel)
        self.window.update_idletasks()
        self.window.deiconify()
        self.window.update_idletasks()
        # Tk geometry interprets negative offsets relative to the right/bottom edge.
        # SetWindowPos uses actual virtual-desktop coordinates, including negatives.
        hwnd=user32.GetParent(self.window.winfo_id())
        user32.SetWindowPos(hwnd,-1,capture.left,capture.top,w,h,0x40)
        self.window.lift(); self.window.focus_force()
        self.timer=self.window.after(60000,self.cancel)
        logging.info('Overlay opened: preview=%s faces=%s origin=(%s,%s)',preview,len(faces),capture.left,capture.top)

    def click(self,event):
        if self.preview: return
        candidates=[(i,f) for i,f in enumerate(self.faces) if f.x<=event.x<=f.x+f.w and f.y<=event.y<=f.y+f.h]
        if candidates: self.finish(min(candidates,key=lambda item:item[1].w*item[1].h)[0])

    def key(self,event):
        if event.keysym=='Escape': self.cancel()
        elif not self.preview and event.char in '123456789' and event.char:
            index=int(event.char)-1
            if index<len(self.faces): self.finish(index)

    def cancel(self): self.finish(None)

    def finish(self,index):
        if self.closed: return
        self.closed=True
        self.window.after_cancel(self.timer)
        self.window.destroy()
        logging.info('Overlay selection: %s',index)
        self.on_select(index)
