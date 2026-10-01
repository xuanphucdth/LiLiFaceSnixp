import json
import logging
import math
from dataclasses import dataclass, asdict, fields
from .paths import DATA

@dataclass
class Config:
    auto_face_snip: bool = True
    crop_mode: str = 'head'
    padding: float = .25
    multiple_faces: str = 'ask'
    capture_mode: str = 'monitor_under_cursor'
    confidence: float = .60
    save_copy: bool = False
    start_with_windows: bool = False
    camera_box_padding: int = 0
    camera_box_confidence: float = .55
    camera_box_fallback: str = 'head'
    camera_box_search_area: str = 'foreground'
    debug_camera_detection: bool = False

    @classmethod
    def validated(cls, values):
        result = cls()
        if not isinstance(values, dict):
            return result
        enums = {'crop_mode': ('face','head','portrait','camera_box'), 'multiple_faces': ('ask','largest','nearest','all'), 'capture_mode': ('monitor_under_cursor','primary','all'), 'camera_box_fallback': ('head','ask','snipping'), 'camera_box_search_area': ('monitor','foreground')}
        for f in fields(cls):
            value = values.get(f.name, getattr(result, f.name))
            if f.name in enums:
                if value in enums[f.name]: setattr(result, f.name, value)
            elif f.type is bool:
                if type(value) is bool: setattr(result, f.name, value)
            elif f.name=='camera_box_padding':
                if type(value) in (float,int) and math.isfinite(value): setattr(result,f.name,max(0,min(16,int(value))))
            elif type(value) in (float, int) and math.isfinite(value):
                low, high = (.30, .90) if f.name in ('confidence','camera_box_confidence') else (.10, .50)
                setattr(result, f.name, max(low, min(high, float(value))))
        return result

def save(config, path=None):
    path = path or DATA / 'config' / 'settings.json'
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix('.tmp')
    temp.write_text(json.dumps(asdict(config), indent=2), encoding='utf-8')
    temp.replace(path)

def load(path=None):
    path = path or DATA / 'config' / 'settings.json'
    try:
        config = Config.validated(json.loads(path.read_text(encoding='utf-8')))
    except (OSError, ValueError, TypeError):
        logging.info('Configuration missing/invalid; using defaults')
        config = Config()
    save(config, path)
    logging.info('Configuration loaded: %s', asdict(config))
    return config
