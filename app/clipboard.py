from io import BytesIO
import logging
import time
import win32clipboard
import win32con

def dib_bytes(image):
    stream = BytesIO()
    image.convert('RGB').save(stream, 'BMP')
    return stream.getvalue()[14:]

def copy_image(image):
    dib = dib_bytes(image)
    png = BytesIO(); image.save(png, 'PNG')
    for attempt in range(12):
        try:
            win32clipboard.OpenClipboard()
            break
        except Exception:
            if attempt == 11: raise
            time.sleep(.025)
    try:
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardData(win32con.CF_DIB, dib)
        win32clipboard.SetClipboardData(win32clipboard.RegisterClipboardFormat('PNG'), png.getvalue())
    finally:
        win32clipboard.CloseClipboard()
    logging.info('Image copied to clipboard: %s CF_DIB + PNG', image.size)
