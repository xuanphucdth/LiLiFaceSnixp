"""Face-anchored, conservative camera tile proposals using local image evidence.

No app names, OCR, network or extra models. Scores are heuristic evidence scores,
not calibrated probabilities. Coordinates are exclusive right/bottom image pixels.
This module never writes an image; debug export is an explicit static-image tool.
"""
from dataclasses import dataclass, replace
from itertools import product
import logging
import math
import time
import cv2
import numpy as np
from .crop import Face


@dataclass(frozen=True)
class CameraBox:
    x: float
    y: float
    w: float
    h: float
    confidence: float
    face_indices: tuple = ()
    evidence: tuple = ()

    @property
    def box(self): return (self.x, self.y, self.x+self.w, self.y+self.h)


@dataclass
class CameraDetection:
    boxes: list
    candidates: list
    unresolved_faces: tuple


def contains(box, face):
    l,t,r,b=box
    return l<=face.x and t<=face.y and r>=face.x+face.w and b>=face.y+face.h


def iou(a,b):
    l,t,r,d=max(a[0],b[0]),max(a[1],b[1]),min(a[2],b[2]),min(a[3],b[3])
    overlap=max(0,r-l)*max(0,d-t)
    return overlap/max(1,(a[2]-a[0])*(a[3]-a[1])+(b[2]-b[0])*(b[3]-b[1])-overlap)


def select_camera_boxes(boxes,strategy,cursor):
    if not boxes: return []
    if len(boxes)==1 or strategy=='all': return boxes
    if strategy=='ask': return None
    if strategy=='largest': return [max(boxes,key=lambda b:b.w*b.h)]
    if strategy=='nearest':
        inside=[b for b in boxes if b.x<=cursor[0]<b.x+b.w and b.y<=cursor[1]<b.y+b.h]
        if inside: return [min(inside,key=lambda b:b.w*b.h)]
        return [min(boxes,key=lambda b:(b.x+b.w/2-cursor[0])**2+(b.y+b.h/2-cursor[1])**2)]
    raise ValueError('Unknown camera selection strategy')


def camera_crop_box(boxes,size,padding=0):
    if not boxes: raise ValueError('No camera boxes')
    p=max(0,int(padding))
    box=(max(0,math.floor(min(b.x for b in boxes))-p),max(0,math.floor(min(b.y for b in boxes))-p),
         min(size[0],math.ceil(max(b.x+b.w for b in boxes))+p),min(size[1],math.ceil(max(b.y+b.h for b in boxes))+p))
    if box[2]<=box[0] or box[3]<=box[1]: raise ValueError('Empty camera crop')
    return box


def _peaks(values,start,end,count=4):
    start=max(1,int(start)); end=min(len(values)-1,int(end))
    if end<=start: return []
    order=np.argsort(values[start:end])[::-1]+start
    found=[]
    for pos in order:
        if values[pos]<3: break
        if all(abs(pos-old)>5 for old in found): found.append(int(pos))
        if len(found)==count: break
    return found


def _proposals(rgb,faces):
    h,w=rgb.shape[:2]; proposals={}
    def add(box,source):
        l,t,r,b=map(int,box)
        if l<0 or t<0 or r>w or b>h or r-l<32 or b-t<32: return
        anchors=tuple(i for i,f in enumerate(faces) if contains((l,t,r,b),f) and r-l>=1.65*f.w and b-t>=1.6*f.h)
        if anchors: proposals.setdefault((l,t,r,b),set()).add(source)
    def contours(mask,source):
        cs,_=cv2.findContours(mask,cv2.RETR_LIST,cv2.CHAIN_APPROX_SIMPLE)
        for c in sorted(cs,key=cv2.contourArea,reverse=True)[:180]:
            x,y,cw,ch=cv2.boundingRect(c)
            if cw*ch>1000 and cv2.contourArea(c)>.60*cw*ch: add((x,y,x+cw,y+ch),source)
    gray=cv2.cvtColor(rgb,cv2.COLOR_RGB2GRAY)
    edges=cv2.Canny(gray,35,100)
    contours(cv2.morphologyEx(edges,cv2.MORPH_CLOSE,np.ones((3,3),np.uint8)),'contour')
    # Flat UI surrounds a textured feed even without a drawn border. Segment several
    # dominant appearance clusters, both their regions and their complements.
    small=rgb[::4,::4].astype(np.int32)
    codes=(small[:,:,0]//16)*256+(small[:,:,1]//16)*16+small[:,:,2]//16
    counts=np.bincount(codes.ravel(),minlength=4096)
    for code in np.argsort(counts)[-5:]:
        if counts[code]<codes.size*.025: continue
        color=np.median(small[codes==code],axis=0)
        mask=(np.max(np.abs(rgb.astype(np.int16)-color),axis=2)<=13).astype(np.uint8)*255
        for region in (mask,255-mask):
            contours(cv2.morphologyEx(region,cv2.MORPH_CLOSE,np.ones((3,3),np.uint8)),'appearance')
    # Face-anchored horizontal/vertical contrast profiles also find open contours,
    # rounded corners, and a feed/toolbar transition inside a larger outer panel.
    data=rgb.astype(np.float32)
    dx=np.zeros((h,w),np.float32); dy=np.zeros((h,w),np.float32)
    dx[:,1:]=np.max(np.abs(data[:,1:]-data[:,:-1]),axis=2)
    dy[1:]=np.max(np.abs(data[1:]-data[:-1]),axis=2)
    for f in faces[:48]:
        y1=max(0,int(f.y-.5*f.h)); y2=min(h,int(f.y+1.8*f.h))
        x1=max(0,int(f.x-.8*f.w)); x2=min(w,int(f.x+1.8*f.w))
        vx=dx[y1:y2].mean(axis=0); vy=dy[:,x1:x2].mean(axis=1)
        left=_peaks(vx,f.x-12*f.w,f.x-.3*f.w)
        right=_peaks(vx,f.x+1.3*f.w,f.x+13*f.w)
        top=_peaks(vy,f.y-9*f.h,f.y-.2*f.h)
        bottom=_peaks(vy,f.y+1.3*f.h,f.y+12*f.h)
        for l,r,t,b in product(left,right,top,bottom): add((l,t,r,b),'profile')
    return proposals,dx,dy


def _side_signal(samples):
    if not samples.size: return 0.
    # Ignore corner rounding and tolerate controls occluding part of a boundary.
    values=samples.ravel()
    contrast=float(np.percentile(values,60))
    continuity=float(np.mean(values>5))
    return min(1.,contrast/25)*continuity


def _boundary(box,dx,dy,cache):
    l,t,r,b=box; h,w=dx.shape
    insetx=max(2,int((r-l)*.09)); insety=max(2,int((b-t)*.09))
    ys=slice(t+insety,b-insety); xs=slice(l+insetx,r-insetx)
    sides=[]
    def signal(axis,pos,start,stop):
        key=(axis,pos,start,stop)
        if key not in cache:
            samples=dx[start:stop,pos] if axis==0 else dy[pos,start:stop]
            cache[key]=_side_signal(samples)
        return cache[key]
    for pos in (l,r):
        sides.append(max((signal(0,p,ys.start,ys.stop) for p in range(max(1,pos-1),min(w,pos+2))),default=0.))
    for pos in (t,b):
        sides.append(max((signal(1,p,xs.start,xs.stop) for p in range(max(1,pos-1),min(h,pos+2))),default=0.))
    return sides


def _grid_support(a,others):
    l,t,r,b=a; w,h=r-l,b-t; matches=0
    for other in others:
        if iou(a,other)>.05: continue
        ol,ot,orr,ob=other; ow,oh=orr-ol,ob-ot
        if abs(w-ow)>.12*max(w,ow) or abs(h-oh)>.12*max(h,oh): continue
        same_row=abs(t-ot)<.08*h and abs(b-ob)<.08*h
        same_col=abs(l-ol)<.08*w and abs(r-orr)<.08*w
        gap=(max(l,ol)-min(r,orr)) if same_row else (max(t,ot)-min(b,ob))
        if (same_row or same_col) and 0<=gap<.35*max(w,h): matches+=1
    return min(1.,matches/2)


def detect_camera_boxes(image,faces,cursor=None,confidence=.55,search_rect=None):
    """Return confident non-duplicate boxes plus uncertain proposals for Ask fallback.

    search_rect is in screenshot coordinates; outputs always retain that coordinate
    space. A face without a confident box is reported, never silently dropped.
    """
    started=time.perf_counter()
    if not faces: return CameraDetection([],[],())
    iw,ih=image.size
    l,t,r,b=search_rect or (0,0,iw,ih)
    l,t,r,b=max(0,int(l)),max(0,int(t)),min(iw,int(r)),min(ih,int(b))
    if r<=l or b<=t: l,t,r,b=0,0,iw,ih
    included=[(i,f) for i,f in enumerate(faces) if contains((l,t,r,b),f)]
    if not included: return CameraDetection([],[],())
    region=np.asarray(image.convert('RGB'))[t:b,l:r]
    scale=min(1.,1280/max(region.shape[:2]))
    if scale<1: region=cv2.resize(region,None,fx=scale,fy=scale,interpolation=cv2.INTER_AREA)
    sx,sy=(r-l)/region.shape[1],(b-t)/region.shape[0]
    local=[Face((f.x-l)/sx,(f.y-t)/sy,f.w/sx,f.h/sy,f.confidence) for _,f in included]
    proposals,dx,dy=_proposals(region,local)
    scored=[]; signal_cache={}
    area=region.shape[0]*region.shape[1]
    for box,sources in proposals.items():
        x,y,x2,y2=box; width,height=x2-x,y2-y
        anchors=tuple(i for i,f in enumerate(local) if contains(box,f))
        if not anchors: continue
        coverage=max(local[i].w*local[i].h/(width*height) for i in anchors)
        if coverage>.37: continue
        sides=_boundary(box,dx,dy,signal_cache)
        support=.65*np.mean(sides)+.35*min(sides)
        ratio=width/height
        aspect=math.exp(-.4*abs(math.log(ratio/(16/9))))
        # Similar score for common wide, square and portrait layouts; not a gate.
        aspect=max(aspect,math.exp(-.7*abs(math.log(ratio))),math.exp(-.6*abs(math.log(ratio/(9/16)))))
        face_scale=min(1.,coverage/.035)
        oversize=max(0.,width*height/area-.65)*.35
        huge_face_ratio=max(0.,.012-coverage)*14
        # Evidence dominates: shape alone cannot manufacture a camera boundary.
        score=.76*support+.07*aspect+.08*face_scale+.03*('appearance' in sources)-oversize-huge_face_ratio
        if min(sides)<.12: score=min(score,.44)
        # A clean app-window perimeter is not sufficient evidence for a tiny face.
        # Keep it available for explicit Ask confirmation, below every auto threshold.
        if coverage<.008 or (width*height/area>.65 and coverage<.018): score=min(score,.20)
        scored.append((box,float(score),anchors,tuple(sides),sources))
    # Alignments support a grid only when peer candidates have boundary evidence.
    peers=[box for box,score,_,_,_ in scored if score>=.48]
    candidates=[]
    for box,score,anchors,sides,sources in scored:
        score=min(.99,max(0.,score+.06*_grid_support(box,peers)))
        x,y,x2,y2=box
        candidates.append(CameraBox(round(x*sx+l),round(y*sy+t),round(x2*sx+l)-round(x*sx+l),round(y2*sy+t)-round(y*sy+t),score,tuple(included[i][0] for i in anchors),tuple(round(v,3) for v in sides)))
    candidates.sort(key=lambda c:(-c.confidence,c.w*c.h))
    dedup=[]
    for candidate in candidates:
        if not any(iou(candidate.box,old.box)>.90 for old in dedup): dedup.append(candidate)
        if len(dedup)>=120: break
    selected=[]; resolved=set()
    # Prefer the smaller strong proposal when scores are essentially equal (PiP,
    # tile within app panel). Larger proposals spanning already chosen tiles lose.
    ordered=sorted(dedup,key=lambda c:(-round(c.confidence/.07),c.w*c.h))
    for candidate in ordered:
        if candidate.confidence<confidence or set(candidate.face_indices)<=resolved: continue
        if any(iou(candidate.box,old.box)>.20 for old in selected): continue
        selected.append(candidate); resolved.update(candidate.face_indices)
    selected.sort(key=lambda c:(c.y,c.x))
    unresolved=tuple(i for i,_ in included if i not in resolved)
    logging.info('Camera candidates=%s selected=%s unresolved=%s elapsed=%.3fs',len(dedup),len(selected),unresolved,time.perf_counter()-started)
    for candidate in dedup[:24]: logging.info('Camera candidate box=%s score=%.3f boundary=%s',candidate.box,candidate.confidence,candidate.evidence)
    for candidate in selected: logging.info('Selected camera box=%s score=%.3f',candidate.box,candidate.confidence)
    return CameraDetection(selected,dedup,unresolved)
