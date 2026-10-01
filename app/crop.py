from dataclasses import dataclass
from math import floor, ceil

@dataclass(frozen=True)
class Face:
    x: float
    y: float
    w: float
    h: float
    confidence: float = 1.0

    @property
    def box(self): return (self.x, self.y, self.x+self.w, self.y+self.h)

def select(faces, strategy, cursor):
    if not faces: return []
    if len(faces) == 1 or strategy == 'all': return faces
    if strategy == 'largest': return [max(faces, key=lambda f: f.w*f.h)]
    if strategy == 'nearest':
        return [min(faces, key=lambda f: (f.x+f.w/2-cursor[0])**2 + (f.y+f.h/2-cursor[1])**2)]
    if strategy == 'ask': return None
    raise ValueError('Unknown multiple-face strategy')

def crop_box(faces, size, mode='head', padding=.25):
    if not faces: raise ValueError('No faces to crop')
    left = min(f.x for f in faces); top = min(f.y for f in faces)
    right = max(f.x+f.w for f in faces); bottom = max(f.y+f.h for f in faces)
    width, height = right-left, bottom-top
    # Per-side margin relative to union width/height; head adds room above hair.
    side, above, below = {'face': (0,0,0), 'head': (.12,.40,.18), 'portrait': (.65,.50,1.55)}[mode]
    box = (max(0, floor(left-width*(side+padding))), max(0, floor(top-height*(above+padding))),
           min(size[0], ceil(right+width*(side+padding))), min(size[1], ceil(bottom+height*(below+padding))))
    if box[2] <= box[0] or box[3] <= box[1]: raise ValueError('Empty crop')
    return box
