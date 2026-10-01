"""Static-image-only development runner; never captures the user's screen.
Usage: python tools/test_camera_images.py [--image FILE] [--debug]
"""
import argparse,json,sys,time
from pathlib import Path
sys.path[:0]=[str(Path(__file__).resolve().parent.parent),str(Path(__file__).resolve().parent.parent/'tests')]
from PIL import Image,ImageDraw
from app.camera_box_detector import detect_camera_boxes,iou
from app.detector import Detector
from app.config import load
from camera_fixtures import CASES,layout,ambiguous

def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--image',type=Path); parser.add_argument('--debug',action='store_true')
    args=parser.parse_args(); report={}
    debug_enabled=args.debug or load().debug_camera_detection
    detector=Detector() if args.image else None
    cases={'local_image':(Image.open(args.image).convert('RGB'),None)} if args.image else {name:layout(boxes,**opts) for name,(boxes,opts) in CASES.items()}
    if not args.image: cases['ambiguous']=ambiguous()
    for name,(image,faces) in cases.items():
        faces=faces if faces is not None else detector.detect(image)
        start=time.perf_counter(); result=detect_camera_boxes(image,faces)
        report[name]={'milliseconds':round((time.perf_counter()-start)*1000),'boxes':[{'box':b.box,'score':round(b.confidence,3)} for b in result.boxes],'unresolved_faces':result.unresolved_faces,'candidates':len(result.candidates)}
        if debug_enabled:
            debug=image.copy(); draw=ImageDraw.Draw(debug)
            for f in faces: draw.rectangle(f.box,outline='#00bfff',width=2)
            for box in result.candidates[:12]:
                draw.rectangle(box.box,outline='#ffaa33',width=1); draw.text((box.x+3,box.y+3),f'{box.confidence:.2f}',fill='#ffaa33')
            for box in result.boxes: draw.rectangle(box.box,outline='#00ff88',width=3)
            folder=Path('debug/camera_detection'); folder.mkdir(parents=True,exist_ok=True); debug.save(folder/f'{name}.png')
    Path('test-results').mkdir(exist_ok=True)
    Path('test-results/camera-static.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2))
if __name__=='__main__':main()
