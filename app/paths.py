import os
import sys
from pathlib import Path

ROOT = Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parent.parent))
DATA = Path(os.environ.get('LILIFACE_DATA_DIR', str(Path(os.environ['LOCALAPPDATA']) / 'LiLiFaceSnixp')))
MODEL = ROOT / 'models' / 'face_detection_yunet_2023mar.onnx'
