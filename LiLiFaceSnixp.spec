# PyInstaller one-folder distribution: runtime, model, icon, DLLs, no test screenshots.
from PyInstaller.utils.hooks import collect_data_files
datas = [('models/face_detection_yunet_2023mar.onnx','models'),('models/LICENSE-YuNet.txt','models'),('assets/LiLiFaceSnixp.ico','assets'),('config/defaults.json','config')]
a = Analysis(['main.py'], pathex=[], binaries=[], datas=datas,
    hiddenimports=['pystray._win32','win32timezone','win32com.shell.shell','win32com.shell.shellcon'],
    hookspath=[], hooksconfig={}, runtime_hooks=[], excludes=['pytest','IPython','matplotlib'], noarchive=False)
pyz = PYZ(a.pure)
exe = EXE(pyz,a.scripts,[],exclude_binaries=True,name='LiLiFaceSnixp',debug=False,
    bootloader_ignore_signals=False,strip=False,upx=False,console=False,
    icon='assets/LiLiFaceSnixp.ico',version='assets/version.txt')
coll = COLLECT(exe,a.binaries,a.datas,strip=False,upx=False,name='LiLiFaceSnixp')
