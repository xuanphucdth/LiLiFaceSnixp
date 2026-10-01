import logging
import time
import cv2
import numpy as np
from .crop import Face
from .paths import MODEL

class Detector:
    def __init__(self, path=MODEL):
        if not path.is_file(): raise FileNotFoundError(f'Model missing: {path}')
        cv2.setNumThreads(2)
        self.model = cv2.FaceDetectorYN.create(str(path), '', (320,320), .6, .3, 5000)
        self.model.detect(np.zeros((320,320,3), dtype=np.uint8))
        logging.info('Detector loaded: %s', path)

    def detect(self, image, confidence=.60):
        start = time.perf_counter()
        # Bound CPU work on large virtual desktops, retain original pixel coordinates.
        scale = min(1., 1920/max(image.size))
        data = cv2.cvtColor(np.asarray(image), cv2.COLOR_RGB2BGR)
        if scale < 1: data = cv2.resize(data, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
        sx, sy = image.width/data.shape[1], image.height/data.shape[0]
        self.model.setScoreThreshold(confidence)
        self.model.setInputSize((data.shape[1],data.shape[0]))
        _, rows = self.model.detect(data)
        faces = []
        if rows is not None:
            for r in rows:
                x,y = max(0.,float(r[0])*sx),max(0.,float(r[1])*sy)
                right,bottom = min(image.width,float(r[0]+r[2])*sx),min(image.height,float(r[1]+r[3])*sy)
                if right>x and bottom>y: faces.append(Face(x,y,right-x,bottom-y,float(r[14])))
        faces.sort(key=lambda f:(f.x,f.y))
        logging.info('Faces detected=%s elapsed=%.3fs confidence_threshold=%.2f boxes=%s', len(faces),time.perf_counter()-start,confidence,faces)
        return faces
