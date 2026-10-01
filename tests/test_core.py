import json
import struct
from PIL import Image
import pytest
from app.crop import Face, crop_box, select
from app.config import Config, load, save
from app.capture import choose_monitor, Capture
from app.clipboard import dib_bytes
from app.hotkeys import route

FACES = [Face(100,100,100,100),Face(400,150,150,180),Face(800,60,80,90)]

def test_face_padding(): assert crop_box([FACES[0]],(1000,1000),'face',.25)==(75,75,225,225)

@pytest.mark.parametrize('mode',['face','head','portrait'])
def test_clamp_and_all(mode):
    for faces in (FACES,[Face(0,0,100,100)],[Face(990,990,10,10)]):
        l,t,r,b = crop_box(faces,(1000,1000),mode,.5)
        assert 0<=l<r<=1000 and 0<=t<b<=1000
        assert all(l<=f.x and t<=f.y and r>=f.x+f.w and b>=f.y+f.h for f in faces)

def test_head_portrait():
    face = crop_box([FACES[0]],(1000,1000),'face')
    head = crop_box([FACES[0]],(1000,1000),'head')
    portrait = crop_box([FACES[0]],(1000,1000),'portrait')
    assert head[1]<face[1] and portrait[3]>head[3]>face[3]

def test_selection():
    assert select(FACES,'largest',(0,0))==[FACES[1]]
    assert select(FACES,'nearest',(840,105))==[FACES[2]]
    assert select(FACES,'all',(0,0))==FACES
    assert select(FACES,'ask',(0,0)) is None
    assert select(FACES[:1],'ask',(0,0))==FACES[:1]
    assert select([],'ask',(0,0))==[]

def test_config(tmp_path):
    p = tmp_path/'settings.json'
    c = Config(crop_mode='portrait',confidence=.81,multiple_faces='all')
    save(c,p); assert load(p)==c
    p.write_text('{broken'); assert load(p)==Config()
    p.write_text(json.dumps({'confidence':2,'padding':-1,'crop_mode':'bad','auto_face_snip':'false'}))
    c=load(p); assert c.confidence==.9 and c.padding==.1 and c.crop_mode=='head' and c.auto_face_snip is True

def test_negative_monitor():
    ms=[dict(left=-1920,top=-1080,width=3840,height=2160),dict(left=0,top=0,width=1920,height=1080),dict(left=-1920,top=-1080,width=1920,height=1080)]
    assert choose_monitor(ms,'monitor_under_cursor',(-10,-10))==ms[2]
    assert choose_monitor(ms,'primary',(-10,-10))==ms[1]
    assert choose_monitor(ms,'all',(-10,-10))==ms[0]
    assert Capture(None,-1920,-1080).local_cursor((-10,-10))==(1910,1070)

def test_dib():
    data=dib_bytes(Image.new('RGB',(13,17),'red'))
    assert struct.unpack_from('<IiiHH',data)==(40,13,17,1,24)

def test_hotkey_routes():
    assert route(False)=='manual' and route(True)=='face'
    assert route(True,shift=True)=='manual' and route(False,shift=True)=='manual'
    assert route(False,ctrl=True)=='full' and route(True,ctrl=True)=='full'
    assert route(True,shift=True,ctrl=True)=='manual'
    assert route(True,alt=True) is None and route(True,win=True) is None
