import logging
import os
import queue
import threading
import tkinter as tk
from tkinter import messagebox
from dataclasses import replace
from datetime import datetime
from pathlib import Path
from . import config, startup
from .capture import capture, cursor_position
from .clipboard import copy_image
from .crop import crop_box, select
from .detector import Detector
from .fallback import open_snipping_tool
from .hotkeys import Hotkeys
from .overlay import Overlay
from .paths import DATA
from .settings import Settings
from .tray import Tray
from .camera_box_detector import detect_camera_boxes, camera_crop_box, contains
from .camera_workflow import decide_camera
from .window_bounds import foreground_bounds, camera_search_rect

class Application:
    def __init__(self,show_settings=False):
        self.root=tk.Tk(); self.root.title('LiLiFaceSnixp Controller'); self.root.withdraw()
        self.root.protocol('WM_DELETE_WINDOW',self.close)
        self.root.report_callback_exception=self.tk_error
        self.config=config.load()
        self.config.start_with_windows=startup.enabled()
        self.events=queue.SimpleQueue()
        self.busy=False; self.closing=False; self.overlay=None; self.settings=None
        self.detector=None; self.detector_error=None
        self.jobs=queue.Queue(maxsize=1)
        self.worker=threading.Thread(target=self.work,name='CaptureWorker',daemon=True); self.worker.start()
        self.tray=Tray(self)
        self.hotkeys=Hotkeys(lambda:self.config.auto_face_snip,self.dispatch_capture)
        try: self.hotkeys.start()
        except Exception:
            logging.exception('Hotkey registration failed; original Windows keys remain available')
            messagebox.showwarning('LiLiFaceSnixp','Không đăng ký được phím PrtSc. Hãy đóng ứng dụng chụp màn hình khác rồi mở lại LiLiFaceSnixp.')
        self.root.after(20,self.poll)
        if show_settings: self.root.after(250,self.show_settings)
        logging.info('App started; tray initialized')

    def enqueue(self,kind,payload=None): self.events.put((kind,payload))

    def dispatch_capture(self,action,cursor):
        bounds=foreground_bounds() if self.config.crop_mode=='camera_box' else None
        self.enqueue('capture',(action,cursor,bounds))

    def poll(self):
        try:
            for _ in range(30):
                try: kind,payload=self.events.get_nowait()
                except queue.Empty: break
                try:
                    if kind=='capture': self.request(*payload)
                    elif kind=='setting': self.update_config(replace(self.config,**{payload[0]:payload[1]}))
                    elif kind=='settings': self.show_settings()
                    elif kind=='exit': self.close(); return
                    elif kind=='result': self.result(*payload)
                    elif kind=='overlay_key':
                        if self.overlay:
                            if payload=='cancel': self.overlay.cancel()
                            elif 0<=payload<len(self.overlay.faces): self.overlay.finish(payload)
                    elif kind=='done': self.busy=False
                    elif kind=='error': self.busy=False; open_snipping_tool()
                except Exception:
                    logging.exception('Event handling failed: %s',kind)
                    self.busy=False; open_snipping_tool()
        finally:
            if not self.closing: self.root.after(20,self.poll)

    def request(self,action,cursor=None,bounds=None):
        logging.info('Shortcut/request: %s',action)
        if action=='manual':
            if self.overlay: self.overlay.cancel(); self.overlay=None
            open_snipping_tool(); return
        if self.busy:
            logging.info('Capture already in progress; duplicate ignored'); return
        self.busy=True
        if self.config.crop_mode=='camera_box' and bounds is None: bounds=foreground_bounds()
        self.jobs.put_nowait(('capture',action,cursor or cursor_position(),replace(self.config),bounds))

    def work(self):
        try: self.detector=Detector()
        except Exception:
            self.detector_error=True; logging.exception('Detector load failed; manual fallback remains available')
        while True:
            job=self.jobs.get()
            if job is None: return
            try:
                if job[0]=='copy':
                    _,shot,faces,cfg=job
                    self.finish_capture(shot,faces,cfg)
                    self.enqueue('done'); continue
                _,action,cursor,cfg,*context=job
                shot=capture(cfg.capture_mode,cursor)
                if action=='full':
                    self.output(shot.image,cfg); self.enqueue('done'); continue
                if self.detector is None: raise RuntimeError('Detector unavailable')
                faces=self.detector.detect(shot.image,cfg.confidence)
                if cfg.crop_mode=='camera_box':
                    self.camera_result(shot,faces,cfg,cursor,context[0] if context else None,action=='test')
                    continue
                if action=='test': self.enqueue('result',(shot,faces,cfg,True)); continue
                if not faces: self.enqueue('error'); continue
                chosen=select(faces,cfg.multiple_faces,shot.local_cursor(cursor))
                logging.info('Selected strategy=%s crop_mode=%s padding=%s faces=%s',cfg.multiple_faces,cfg.crop_mode,cfg.padding,chosen)
                if chosen is None: self.enqueue('result',(shot,faces,cfg,False))
                else:
                    self.finish_capture(shot,chosen,cfg); self.enqueue('done')
            except Exception:
                logging.exception('Capture workflow failed'); self.enqueue('error')

    def camera_result(self,shot,faces,cfg,cursor,bounds,preview):
        logging.info('Camera mode enabled: search=%s confidence=%.2f padding=%spx',cfg.camera_box_search_area,cfg.camera_box_confidence,cfg.camera_box_padding)
        rect=camera_search_rect(cfg.camera_box_search_area,bounds,shot,cursor)
        faces=[f for f in faces if contains(rect,f)]
        if not faces and not preview: self.enqueue('error'); return
        local_cursor=shot.local_cursor(cursor)
        try:
            detection=detect_camera_boxes(shot.image,faces,local_cursor,cfg.camera_box_confidence,rect)
        except Exception:
            logging.exception('Camera detector failed; applying configured fallback')
            from .camera_box_detector import CameraDetection
            detection=CameraDetection([],[],tuple(range(len(faces))))
        if preview:
            targets=detection.boxes or detection.candidates[:9]
            label='camera boxes' if detection.boxes else 'candidate camera boxes (uncertain)'
            self.enqueue('result',(shot,targets,cfg,True,label)); return
        decision=decide_camera(detection,faces,cfg,local_cursor)
        chosen_cfg=replace(cfg,crop_mode=decision.crop_mode)
        if decision.crop_mode!='camera_box' or decision.manual or decision.uncertain:
            logging.info('Camera fallback=%s unresolved=%s',cfg.camera_box_fallback,detection.unresolved_faces)
        if decision.manual: self.enqueue('error')
        elif decision.ask:
            label='candidate camera boxes — confirm boundaries' if decision.uncertain else ('camera boxes' if decision.crop_mode=='camera_box' else 'faces (Head fallback)')
            self.enqueue('result',(shot,decision.targets,chosen_cfg,False,label))
        else:
            self.finish_capture(shot,decision.targets,chosen_cfg); self.enqueue('done')

    def result(self,shot,faces,cfg,preview,label='faces'):
        def selected(index):
            self.hotkeys.overlay_dispatch=None
            self.overlay=None
            if index is None or preview:
                self.busy=False
                if preview and self.settings and self.settings.window.winfo_exists(): self.settings.window.deiconify()
                return
            self.jobs.put_nowait(('copy',shot,[faces[index]],cfg))
        try:
            self.overlay=Overlay(self.root,shot,faces,selected,preview,label)
            self.hotkeys.overlay_preview=preview
            self.hotkeys.overlay_dispatch=lambda selection:self.enqueue('overlay_key',selection)
        except Exception:
            # A partially constructed transparent window must not block the desktop.
            for child in self.root.winfo_children():
                if isinstance(child,tk.Toplevel) and (not self.settings or child is not self.settings.window): child.destroy()
            raise

    def finish_capture(self,shot,faces,cfg):
        box=(camera_crop_box(faces,shot.image.size,cfg.camera_box_padding) if cfg.crop_mode=='camera_box'
             else crop_box(faces,shot.image.size,cfg.crop_mode,cfg.padding))
        logging.info('Selected crop bounding box=%s',box)
        self.output(shot.image.crop(box),cfg)

    def output(self,image,cfg):
        copy_image(image)
        if cfg.save_copy:
            try:
                from win32com.shell import shell, shellcon
                folder=Path(shell.SHGetFolderPath(0,shellcon.CSIDL_MYPICTURES,0,0))/'LiLiFaceSnixp'
                folder.mkdir(parents=True,exist_ok=True)
                image.save(folder/(datetime.now().strftime('%Y%m%d_%H%M%S_%f')+'.png'))
                logging.info('Optional image copy saved')
            except Exception: logging.exception('Save a copy failed; clipboard is still available')

    def update_config(self,cfg):
        try:
            if cfg.start_with_windows!=startup.enabled(): startup.set_enabled(cfg.start_with_windows)
            config.save(cfg)
            self.config=cfg
            self.tray.refresh()
        except Exception:
            logging.exception('Settings could not be saved')
            messagebox.showerror('LiLiFaceSnixp','Không lưu được cài đặt. Xem Open logs để biết chi tiết.')

    def show_settings(self):
        if self.settings and self.settings.window.winfo_exists():
            self.settings.window.destroy()
        self.settings=Settings(self)

    def open_logs(self): os.startfile(str(DATA/'logs'))

    def tk_error(self,kind,error,tb):
        logging.error('GUI error',exc_info=(kind,error,tb))
        self.busy=False
        if self.overlay:
            try: self.overlay.cancel()
            except Exception: pass
        open_snipping_tool()

    def close(self):
        self.closing=True
        self.hotkeys.stop(); self.tray.stop()
        if self.overlay: self.overlay.cancel()
        self.root.destroy()
        logging.info('App stopped')

    def run(self): self.root.mainloop()
