import tkinter as tk
from tkinter import ttk
from dataclasses import asdict
from .config import Config

OPTIONS = {
 'crop_mode': [('Face','face'),('Head','head'),('Portrait','portrait'),('Camera Box','camera_box')],
 'multiple_faces': [('Ask me','ask'),('Largest face','largest'),('Face nearest cursor','nearest'),('Crop all faces together','all')],
 'capture_mode': [('Monitor under cursor','monitor_under_cursor'),('Primary monitor','primary'),('All monitors','all')],
 'camera_box_padding': [(f'{n} px',n) for n in (0,2,4,8,12,16)],
 'camera_box_fallback': [('Crop Head','head'),('Ask me with candidates','ask'),('Open Snipping Tool','snipping')],
 'camera_box_search_area': [('Current monitor','monitor'),('Foreground window','foreground')],
}
CAMERA_MULTIPLE=[('Ask me','ask'),('Largest camera box','largest'),('Camera box nearest cursor','nearest'),('Crop all camera boxes together','all')]

class Settings:
    def __init__(self,app):
        self.app=app
        self.window=tk.Toplevel(app.root)
        self.window.title('LiLiFaceSnixp Settings')
        self.window.resizable(False,False)
        frame=ttk.Frame(self.window,padding=24); frame.pack(fill='both',expand=True)
        ttk.Label(frame,text='LiLiFaceSnixp',font=('Segoe UI',20,'bold')).grid(row=0,column=0,columnspan=2,sticky='w')
        ttk.Label(frame,text='Local face snipping • Your screenshots stay on this PC').grid(row=1,column=0,columnspan=2,sticky='w',pady=(0,18))
        self.values={}
        self.combos={}; self.labels={}
        row=2
        for key,label in [('auto_face_snip','Auto Face Snip'),('crop_mode','Snip Target'),('padding','Face / Head / Portrait Padding'),('multiple_faces','When multiple faces are detected'),('capture_mode','Capture'),('confidence','Face Detection Confidence'),('save_copy','Save a copy to Pictures/LiLiFaceSnixp'),('start_with_windows','Start LiLiFaceSnixp with Windows')]:
            value=getattr(app.config,key)
            if type(value) is bool:
                var=tk.BooleanVar(value=value)
                ttk.Checkbutton(frame,text=label,variable=var,command=self.apply).grid(row=row,column=0,columnspan=2,sticky='w',pady=9)
            else:
                self.labels[key]=ttk.Label(frame,text=label,wraplength=210)
                self.labels[key].grid(row=row,column=0,sticky='w',padx=(0,24),pady=9)
                if key=='confidence':
                    var=tk.DoubleVar(value=value)
                    cell=ttk.Frame(frame); cell.grid(row=row,column=1,sticky='ew')
                    slider=ttk.Scale(cell,from_=.3,to=.9,variable=var,command=self.confidence_changed); slider.pack(side='left',fill='x',expand=True)
                    self.confidence_label=ttk.Label(cell,text=f'{value:.2f}',width=5); self.confidence_label.pack(side='right')
                    slider.bind('<ButtonRelease-1>',lambda _:self.apply())
                    slider.bind('<KeyRelease>',lambda _:self.apply())
                else:
                    options=OPTIONS.get(key,[(f'{n}% ',n/100) for n in (10,15,20,25,30,40,50)])
                    var=tk.StringVar(value=next((name for name,v in options if v==value),f'{round(value*100)}% ' if key=='padding' else options[0][0]))
                    combo=ttk.Combobox(frame,textvariable=var,values=[name for name,_ in options],state='readonly',width=29)
                    combo.grid(row=row,column=1,sticky='ew'); combo.bind('<<ComboboxSelected>>',lambda _:self.apply())
                    self.combos[key]=combo
            self.values[key]=var; row+=1
        self.camera_frame=ttk.LabelFrame(frame,text='Camera Box',padding=10)
        self.camera_frame.grid(row=row,column=0,columnspan=2,sticky='ew',pady=6); row+=1
        for camera_row,(key,label) in enumerate([('camera_box_padding','Camera Box Padding'),('camera_box_fallback','Camera Box Fallback'),('camera_box_search_area','Camera Box Search Area')]):
            ttk.Label(self.camera_frame,text=label).grid(row=camera_row,column=0,sticky='w',padx=(0,12),pady=5)
            options=OPTIONS[key]; value=getattr(app.config,key)
            var=tk.StringVar(value=next((name for name,v in options if v==value),options[0][0]))
            self.values[key]=var
            combo=ttk.Combobox(self.camera_frame,textvariable=var,values=[name for name,_ in options],state='readonly',width=27)
            combo.grid(row=camera_row,column=1,sticky='ew'); combo.bind('<<ComboboxSelected>>',lambda _:self.apply())
        ttk.Label(self.camera_frame,text='Camera Box Confidence').grid(row=3,column=0,sticky='w',pady=5)
        var=tk.DoubleVar(value=app.config.camera_box_confidence); self.values['camera_box_confidence']=var
        cell=ttk.Frame(self.camera_frame); cell.grid(row=3,column=1,sticky='ew')
        self.camera_confidence_label=ttk.Label(cell,text=f'{var.get():.2f}',width=5); self.camera_confidence_label.pack(side='right')
        slider=ttk.Scale(cell,from_=.3,to=.9,variable=var,command=lambda value:self.camera_confidence_label.configure(text=f'{float(value):.2f}'))
        slider.pack(side='left',fill='x',expand=True)
        slider.bind('<ButtonRelease-1>',lambda _:self.apply()); slider.bind('<KeyRelease>',lambda _:self.apply())
        self.multiple_options=OPTIONS['multiple_faces']
        self.refresh_target()
        ttk.Separator(frame).grid(row=row,column=0,columnspan=2,sticky='ew',pady=12); row+=1
        ttk.Label(frame,text='PrtSc: snip   •   Shift+PrtSc: manual   •   Ctrl+PrtSc: full screen').grid(row=row,column=0,columnspan=2,pady=5); row+=1
        buttons=ttk.Frame(frame); buttons.grid(row=row,column=0,columnspan=2,sticky='ew',pady=(12,0))
        ttk.Button(buttons,text='Test Detection',command=self.test).pack(side='left')
        ttk.Button(buttons,text='Open logs',command=app.open_logs).pack(side='left',padx=8)
        ttk.Button(buttons,text='Close',command=self.window.destroy).pack(side='right')
        self.window.protocol('WM_DELETE_WINDOW',self.window.destroy)

    def confidence_changed(self,value):
        if hasattr(self,'confidence_label'): self.confidence_label.configure(text=f'{float(value):.2f}')
        if 'confidence' in self.values:
            self.app.config.confidence=round(float(value),2)

    def apply(self):
        data=asdict(self.app.config)
        for key,var in self.values.items():
            value=var.get()
            if key=='multiple_faces': value=dict(self.multiple_options)[value]
            elif key in OPTIONS: value=dict(OPTIONS[key])[value]
            elif key=='padding': value=float(value.strip().strip('%'))/100
            elif key in ('confidence','camera_box_confidence'): value=round(value,2)
            data[key]=value
        self.app.update_config(Config.validated(data))
        self.refresh_target()

    def refresh_target(self):
        camera=self.app.config.crop_mode=='camera_box'
        self.multiple_options=CAMERA_MULTIPLE if camera else OPTIONS['multiple_faces']
        self.combos['multiple_faces'].configure(values=[name for name,_ in self.multiple_options],width=32)
        self.values['multiple_faces'].set(next(name for name,value in self.multiple_options if value==self.app.config.multiple_faces))
        self.labels['multiple_faces'].configure(text='When multiple camera boxes are detected' if camera else 'When multiple faces are detected')
        if camera: self.camera_frame.grid()
        else: self.camera_frame.grid_remove()

    def test(self):
        self.apply(); self.window.withdraw()
        from .capture import cursor_position
        cursor=cursor_position()
        self.app.root.after(250,lambda:self.app.request('test',cursor))
