import queue
import threading
from unittest.mock import Mock
from PIL import Image
import pytest
from app.application import Application
from app.capture import Capture
from app.config import Config
from app.crop import Face
import app.application as module

@pytest.mark.parametrize('failure',['model','capture','detect','clipboard','no_faces'])
def test_worker_survives_and_requests_fallback(monkeypatch,failure):
    app=Application.__new__(Application)
    app.events=queue.SimpleQueue(); app.jobs=queue.Queue()
    detector=Mock(); detector.detect.return_value=[Face(10,10,20,20)]
    monkeypatch.setattr(module,'Detector',Mock(return_value=detector))
    monkeypatch.setattr(module,'capture',Mock(return_value=Capture(Image.new('RGB',(100,100)),0,0)))
    monkeypatch.setattr(module,'copy_image',Mock())
    if failure=='model': module.Detector.side_effect=RuntimeError('model missing')
    elif failure=='capture': module.capture.side_effect=RuntimeError('capture unavailable')
    elif failure=='detect': detector.detect.side_effect=RuntimeError('detector failure')
    elif failure=='clipboard': module.copy_image.side_effect=RuntimeError('clipboard locked')
    elif failure=='no_faces': detector.detect.return_value=[]
    app.jobs.put(('capture','face',(0,0),Config())); app.jobs.put(None)
    thread=threading.Thread(target=app.work); thread.start(); thread.join(3)
    assert not thread.is_alive()
    assert app.events.get_nowait()[0]=='error'

def test_clipboard_retry_and_close(monkeypatch):
    import app.clipboard as cb
    open_clip=Mock(side_effect=[RuntimeError('busy'),None]); close=Mock()
    monkeypatch.setattr(cb.win32clipboard,'OpenClipboard',open_clip)
    monkeypatch.setattr(cb.win32clipboard,'CloseClipboard',close)
    monkeypatch.setattr(cb.win32clipboard,'EmptyClipboard',Mock())
    monkeypatch.setattr(cb.win32clipboard,'SetClipboardData',Mock(side_effect=RuntimeError('write failed')))
    with pytest.raises(RuntimeError): cb.copy_image(Image.new('RGB',(5,5)))
    assert open_clip.call_count==2
    close.assert_called_once()

def test_overlay_failure_cleans_up(monkeypatch):
    app=Application.__new__(Application)
    app.root=Mock(); app.root.winfo_children.return_value=[]; app.settings=None
    monkeypatch.setattr(module,'Overlay',Mock(side_effect=RuntimeError('GUI creation failed')))
    with pytest.raises(RuntimeError): app.result(None,[],Config(),False)
    app.root.winfo_children.assert_called_once()

def test_preview_never_copies(monkeypatch):
    app=Application.__new__(Application); app.events=queue.SimpleQueue(); app.jobs=queue.Queue()
    detector=Mock(); detector.detect.return_value=[]
    monkeypatch.setattr(module,'Detector',Mock(return_value=detector))
    monkeypatch.setattr(module,'capture',Mock(return_value=Capture(Image.new('RGB',(10,10)),0,0)))
    copy=Mock(); monkeypatch.setattr(module,'copy_image',copy)
    app.jobs.put(('capture','test',(0,0),Config())); app.jobs.put(None); app.work()
    event,payload=app.events.get_nowait()
    assert event=='result' and payload[-1] is True
    copy.assert_not_called()
