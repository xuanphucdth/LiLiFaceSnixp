"""Resolve detection, explicit uncertainty and selection without changing face modes."""
from dataclasses import dataclass
from .camera_box_detector import select_camera_boxes
from .crop import select

@dataclass
class CameraDecision:
    targets: list
    crop_mode: str
    ask: bool = False
    manual: bool = False
    uncertain: bool = False

def decide_camera(result,faces,config,cursor):
    if result.boxes and not result.unresolved_faces:
        chosen=select_camera_boxes(result.boxes,config.multiple_faces,cursor)
        return CameraDecision(result.boxes if chosen is None else chosen,'camera_box',chosen is None)
    if config.camera_box_fallback=='snipping': return CameraDecision([],'camera_box',manual=True)
    if config.camera_box_fallback=='ask':
        # Never silently auto-crop an uncertain proposal, even if there is only one.
        candidates=[b for b in result.candidates if b.confidence>=.20][:9]
        if candidates: return CameraDecision(candidates,'camera_box',ask=True,uncertain=True)
        return CameraDecision([],'camera_box',manual=True)
    chosen=select(faces,config.multiple_faces,cursor)
    return CameraDecision(faces if chosen is None else chosen,'head',chosen is None)
