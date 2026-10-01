"""Deterministic local call-layout fixtures using the existing NASA test photograph.
These are synthetic UI layouts, not screenshots of real video calls.
"""
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageEnhance,ImageFilter
from app.crop import Face

def layout(boxes,rounded=False,brightness=1.,toolbar=False,border=False,size=(1100,800)):
    image=Image.new('RGB',size,'#25272b'); draw=ImageDraw.Draw(image)
    draw.rectangle((0,0,69,size[1]-1),fill='#18191c')
    draw.rectangle((0,0,size[0]-1,39),fill='#141518')
    sample=Image.open(Path(__file__).parent/'fixtures'/'astronaut.png').convert('RGB')
    faces=[]
    for index,(l,t,r,b) in enumerate(boxes):
        w,h=r-l,b-t
        feed=ImageEnhance.Brightness(sample.resize((w,h))).enhance(brightness)
        inside=ImageDraw.Draw(feed); inside.rounded_rectangle((8,h-27,90,h-7),radius=5,fill='#15171b')
        inside.text((13,h-24),f'Person {index+1}',fill='white')
        if rounded:
            mask=Image.new('L',(w,h)); ImageDraw.Draw(mask).rounded_rectangle((0,0,w-1,h-1),radius=18,fill=255)
            image.paste(feed,(l,t),mask)
        else: image.paste(feed,(l,t))
        if border: draw.rectangle((l,t,r-1,b-1),outline='#535760',width=1)
        if toolbar:
            draw.rectangle((l,b,r-1,b+43),fill='#383b40')
            for x in (l+30,l+70,l+110): draw.ellipse((x,b+12,x+16,b+28),fill='#777b82')
        faces.append(Face(l+178/512*w,t+63/512*h,90/512*w,113/512*h,.93))
    return image,faces

CASES={
 'single': ([(220,130,940,610)],{}),
 'grid': ([(100,80,540,375),(558,80,998,375),(100,393,540,688),(558,393,998,688)],{'rounded':True}),
 'pip': ([(795,480,1035,660)],{}),
 'self_view': ([(100,100,760,600),(820,470,1060,650)],{}),
 'dark': ([(210,150,930,620)],{'brightness':.17,'rounded':True}),
 'bright': ([(210,150,930,620)],{'brightness':1.6}),
 'portrait': ([(390,80,690,710)],{'rounded':True}),
 'square': ([(300,120,850,670)],{}),
 'toolbar': ([(200,100,920,570)],{'toolbar':True}),
 'faint_border': ([(200,100,920,570)],{'border':True}),
}

def ambiguous():
    # A gradual textured scene has no rectangular camera boundary.
    y,x=np.mgrid[:700,:1000]
    scene=np.stack((70+x/30+np.sin(y/19)*5,85+y/23+np.sin(x/15)*5,100+x/35+y/40),axis=-1)
    return Image.fromarray(np.uint8(scene)),[Face(430,230,90,113)]
