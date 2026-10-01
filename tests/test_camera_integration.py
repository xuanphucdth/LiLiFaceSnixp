import queue
from unittest.mock import Mock
from dataclasses import replace
import pytest
from app.application import Application
from app.capture import Capture
from app.config import Config
from app.camera_box_detector import CameraBox,CameraDetection
from app.crop import crop_box
from camera_fixtures import layout,ambiguous
import app.application as module

def app_stub(monkeypatch):
    app=Application.__new__(Application); app.events=queue.SimpleQueue(); app.jobs=queue.Queue()
    app.output=Mock()
    monkeypatch.setattr(module,'camera_search_rect',lambda area,bounds,shot,cursor:(0,0,*shot.image.size))
    return app

@pytest.mark.parametrize('strategy',['ask','largest','nearest','all'])
def test_camera_flow(monkeypatch,strategy):
    app=app_stub(monkeypatch)
    image,faces=layout([(100,80,500,380),(550,80,950,380)])
    shot=Capture(image,-1920,-200)
    cfg=Config(crop_mode='camera_box',multiple_faces=strategy)
    app.camera_result(shot,faces,cfg,(-1200,10),None,False)
    kind,payload=app.events.get_nowait()
    if strategy=='ask':
        assert kind=='result' and payload[2].crop_mode=='camera_box'
        assert len(payload[1])==2 and payload[1][0].w>faces[0].w*2
        app.output.assert_not_called()
    else:
        assert kind=='done'
        result_image=app.output.call_args.args[0]
        assert result_image.size==((850,300) if strategy=='all' else (400,300))

@pytest.mark.parametrize('fallback',['head','ask','snipping'])
def test_camera_detector_error_fallback(monkeypatch,fallback):
    app=app_stub(monkeypatch); image,faces=ambiguous(); shot=Capture(image,0,0)
    monkeypatch.setattr(module,'detect_camera_boxes',Mock(side_effect=RuntimeError('CV unavailable')))
    cfg=Config(crop_mode='camera_box',camera_box_fallback=fallback)
    app.camera_result(shot,faces,cfg,(450,300),None,False)
    event,payload=app.events.get_nowait()
    if fallback=='head':
        assert event=='done'
        assert app.output.call_args.args[0].size==image.crop(crop_box(faces,image.size)).size
    else:
        assert event=='error'; app.output.assert_not_called()

def test_camera_preview_never_copies_or_falls_back(monkeypatch):
    app=app_stub(monkeypatch); image,faces=ambiguous()
    app.camera_result(Capture(image,0,0),faces,Config(crop_mode='camera_box'),(500,300),None,True)
    kind,payload=app.events.get_nowait()
    assert kind=='result' and payload[3] is True
    app.output.assert_not_called()

def test_camera_zero_faces_opens_manual(monkeypatch):
    app=app_stub(monkeypatch); image,_=ambiguous()
    app.camera_result(Capture(image,0,0),[],Config(crop_mode='camera_box'),(500,300),None,False)
    assert app.events.get_nowait()[0]=='error'

def test_foreground_filters_unrelated_faces(monkeypatch):
    app=app_stub(monkeypatch); image,faces=layout([(100,80,500,380),(550,80,950,380)])
    monkeypatch.setattr(module,'camera_search_rect',lambda *args:(50,40,520,500))
    app.camera_result(Capture(image,0,0),faces,Config(crop_mode='camera_box'),(500,300),None,False)
    assert app.events.get_nowait()[0]=='done'
    assert app.output.call_args.args[0].size==(400,300)

def test_ctrl_prtsc_bypasses_camera_and_face(monkeypatch):
    app=app_stub(monkeypatch); image,_=ambiguous()
    detector=Mock(); monkeypatch.setattr(module,'Detector',Mock(return_value=detector))
    monkeypatch.setattr(module,'capture',Mock(return_value=Capture(image,0,0)))
    camera=Mock(); monkeypatch.setattr(module,'detect_camera_boxes',camera)
    app.jobs.put(('capture','full',(0,0),Config(crop_mode='camera_box'))); app.jobs.put(None)
    app.work(); detector.detect.assert_not_called(); camera.assert_not_called()
    assert app.output.call_args.args[0] is image

def test_overlay_key_scope():
    from app.hotkeys import overlay_key
    assert overlay_key(ord('2'))==1 and overlay_key(0x69)==8
    assert overlay_key(0x1B)=='cancel'
    assert overlay_key(ord('2'),preview=True) is None
    assert overlay_key(ord('0')) is None and overlay_key(ord('V')) is None
