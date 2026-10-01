import argparse
import ctypes
import logging
import sys
from pathlib import Path

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--settings',action='store_true')
    parser.add_argument('--self-test',metavar='REPORT_JSON')
    args=parser.parse_args()
    from app.capture import enable_dpi_awareness
    enable_dpi_awareness()
    from app.logger import setup
    setup()
    if args.self_test:
        from app.diagnostics import run
        return run(Path(args.self_test))
    import win32event,win32api,winerror
    mutex=win32event.CreateMutex(None,False,r'Local\LiLiFaceSnixp.Application')
    if win32api.GetLastError()==winerror.ERROR_ALREADY_EXISTS:
        ctypes.windll.user32.MessageBoxW(0,'LiLiFaceSnixp đang chạy. Mở biểu tượng trong khay hệ thống để đổi cài đặt.','LiLiFaceSnixp',0x40)
        return 0
    try:
        from app.application import Application
        from app.paths import DATA
        first_run=not (DATA/'config'/'settings.json').exists()
        Application(args.settings or first_run).run()
        return 0
    except Exception:
        logging.exception('App startup failed')
        ctypes.windll.user32.MessageBoxW(0,'Không khởi động được LiLiFaceSnixp. Xem log trong %LOCALAPPDATA%\\LiLiFaceSnixp\\logs.','LiLiFaceSnixp',0x10)
        return 1
    finally: win32api.CloseHandle(mutex)

if __name__=='__main__': sys.exit(main())
