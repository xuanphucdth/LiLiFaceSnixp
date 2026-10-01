from dataclasses import replace
import pytest
from app.camera_box_detector import detect_camera_boxes,CameraBox,CameraDetection,camera_crop_box,select_camera_boxes,iou
from app.camera_workflow import decide_camera
from app.config import Config,load,save
from app.capture import Capture
from app.window_bounds import local_search_rect
from camera_fixtures import layout,CASES,ambiguous

@pytest.mark.parametrize('name',list(CASES))
def test_static_boundaries(name):
    expected,options=CASES[name]; image,faces=layout(expected,**options)
    result=detect_camera_boxes(image,faces)
    assert len(result.boxes)==len(expected),[(b.box,round(b.confidence,3)) for b in result.candidates[:8]]
    for truth in expected:
        matched=max(result.boxes,key=lambda b:iou(b.box,truth))
        assert iou(matched.box,truth)>.94,(name,matched,truth)
        assert max(abs(a-b) for a,b in zip(matched.box,truth))<=4,(name,matched.box,truth)

def test_ambiguous_abstains():
    image,faces=ambiguous(); result=detect_camera_boxes(image,faces)
    assert not result.boxes and result.unresolved_faces==(0,)

def test_window_perimeter_with_tiny_face_is_not_camera():
    from PIL import Image,ImageDraw
    from app.crop import Face
    image=Image.new('RGB',(1100,800),'#151515')
    ImageDraw.Draw(image).rectangle((80,60,1039,739),fill='#999999')
    result=detect_camera_boxes(image,[Face(500,250,30,40)],confidence=.30)
    assert not result.boxes and result.unresolved_faces==(0,)

def test_nearest_inside_priority_and_union():
    # Cursor in wide tile 0 but closer to the small tile 1's center.
    boxes=[CameraBox(0,0,900,200,.8),CameraBox(905,0,100,200,.8),CameraBox(0,300,100,100,.8)]
    assert select_camera_boxes(boxes,'nearest',(890,100))==[boxes[0]]
    assert select_camera_boxes(boxes,'nearest',(50,350))==[boxes[2]]
    assert select_camera_boxes(boxes,'largest',(0,0))==[boxes[0]]
    assert select_camera_boxes(boxes,'ask',(0,0)) is None
    assert camera_crop_box(select_camera_boxes(boxes,'all',(0,0)),(1100,500),8)==(0,0,1013,408)

def test_shared_tile_dedup():
    image,faces=layout([(200,100,900,600)])
    faces.append(replace(faces[0],x=faces[0].x+180))
    result=detect_camera_boxes(image,faces)
    assert len(result.boxes)==1 and not result.unresolved_faces
    assert result.boxes[0].face_indices==(0,1)

def test_overlapping_pip_and_remote_camera():
    expected=[(100,100,900,700),(760,500,1030,710)]
    image,faces=layout(expected)
    result=detect_camera_boxes(image,faces)
    assert len(result.boxes)==2 and not result.unresolved_faces
    assert all(max(iou(b.box,truth) for b in result.boxes)>.94 for truth in expected)

def test_search_offset():
    image,faces=layout([(200,100,900,600)])
    rect=local_search_rect((-900,-300,100,400),Capture(image,-1000,-400))
    assert rect==(100,100,1100,800)
    result=detect_camera_boxes(image,faces,search_rect=(80,40,1050,760))
    assert iou(result.boxes[0].box,(200,100,900,600))>.96

def test_camera_settings_migrate(tmp_path):
    path=tmp_path/'settings.json'; path.write_text('{"crop_mode":"portrait","padding":0.4}')
    cfg=load(path)
    assert cfg.crop_mode=='portrait' and cfg.padding==.4
    assert cfg.camera_box_padding==0 and cfg.camera_box_confidence==.55
    cfg=replace(cfg,crop_mode='camera_box',camera_box_padding=8,camera_box_confidence=.73,camera_box_fallback='ask')
    save(cfg,path); assert load(path)==cfg
    bad=Config.validated({'camera_box_padding':900,'camera_box_confidence':-4,'camera_box_search_area':'bad'})
    assert bad.camera_box_padding==16 and bad.camera_box_confidence==.3 and bad.camera_box_search_area=='foreground'

def test_fallbacks_and_partial_detection():
    image,faces=ambiguous(); cfg=Config(crop_mode='camera_box')
    uncertain=CameraDetection([],[],(0,))
    decision=decide_camera(uncertain,faces,cfg,(0,0))
    assert decision.crop_mode=='head' and decision.targets==faces
    assert decide_camera(uncertain,faces,replace(cfg,camera_box_fallback='snipping'),(0,0)).manual
    assert decide_camera(uncertain,faces,replace(cfg,camera_box_fallback='ask'),(0,0)).manual
    candidate=CameraBox(100,100,700,500,.35,(0,))
    uncertain.candidates=[candidate]
    ask=decide_camera(uncertain,faces,replace(cfg,camera_box_fallback='ask'),(0,0))
    assert ask.ask and ask.uncertain and ask.targets==[candidate]
    partial=CameraDetection([replace(candidate,confidence=.9)],[candidate],(1,))
    assert decide_camera(partial,faces,cfg,(0,0)).crop_mode=='head'

def test_no_faces():
    image,_=ambiguous(); result=detect_camera_boxes(image,[])
    assert not result.boxes and not result.candidates

def test_large_desktop_preserves_pixel_coordinates():
    image,faces=layout([(200,100,900,600)])
    image=image.resize((2200,1600))
    faces=[replace(f,x=f.x*2,y=f.y*2,w=f.w*2,h=f.h*2) for f in faces]
    result=detect_camera_boxes(image,faces)
    assert iou(result.boxes[0].box,(400,200,1800,1200))>.96

def test_threshold_controls_acceptance():
    boxes,opts=CASES['dark']; image,faces=layout(boxes,**opts)
    assert detect_camera_boxes(image,faces,confidence=.55).boxes
    strict=detect_camera_boxes(image,faces,confidence=.90)
    assert not strict.boxes and strict.unresolved_faces==(0,)

@pytest.mark.parametrize('name',['single','grid','pip'])
def test_actual_yunet_then_camera(name):
    from app.detector import Detector
    boxes,opts=CASES[name]; image,_=layout(boxes,**opts)
    faces=Detector().detect(image)
    assert len(faces)==len(boxes)
    result=detect_camera_boxes(image,faces)
    assert len(result.boxes)==len(boxes)
    assert all(max(iou(b.box,truth) for b in result.boxes)>.94 for truth in boxes)
