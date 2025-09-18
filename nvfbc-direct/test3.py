# Test NVFBC_BACKEND_DIRECT backend
# run ./vkcube first

import numpy
import os
import psutil # pip install psutil
import threading
import time
from compushady import Swapchain, Buffer, Texture2D, HEAP_UPLOAD
from compushady.formats import R8G8B8A8_UNORM, get_pixel_size

from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QPainter, QPen, QPixmap, QCursor
from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6 import QtCore, QtGui, QtWidgets
import signal
signal.signal(signal.SIGINT, signal.SIG_DFL) # enables ctrl-c in qt, or ctrl-z does not destroy overlay window

class OverlayWindow(QMainWindow):
    def __init__(self, width, height, opacity):
        super().__init__()                        
        self.opacity = opacity/100
        self.setWindowOpacity(self.opacity)        
        self.setGeometry(0, 0, width, height)               
        self.setWindowFlags(self.windowFlags()| Qt.WindowTransparentForInput|Qt.X11BypassWindowManagerHint)
        self.show()        
        self.xid = int(self.winId())
        # print("Overlay window xid =", self.xid)

app = QApplication([])
overlay = OverlayWindow(100, 100, opacity=60)

import ctypes
nvfbc = '../nvfbc/nvfbc-direct.so'
nvfbc = 'nvfbc/nvfbc-direct.so'
cap = ctypes.CDLL(nvfbc)

xlib = ctypes.cdll.LoadLibrary("libX11.so")
display_id_int = xlib.XOpenDisplay( ctypes.c_int(0) ) 

cap.init.argtypes = (ctypes.c_int,)
cap.init.restype = ctypes.c_int
cap.capture.argtypes = (ctypes.c_int,)
cap.capture.restype = ctypes.c_void_p # without this, 64 bit address got truncated to 32 bit (ctypes default action) => segmentation fault 
cap.destroy.argtypes = None
cap.destroy.restype = ctypes.c_int

pid = 0
count = 0
running = 1
for p in psutil.process_iter():
    if 'vkcube' in p.name():
        print(p)
        pid = p.pid
        break

def worker():
    global count     
    cap.init(pid)
    while running:                                                                                                                                           
        addr = cap.capture(0)
        dimension = (ctypes.c_ubyte*4).from_address(addr)            
        w = dimension[0]+dimension[1]*256 # extra width height from the first pixel
        h = dimension[2]+dimension[3]*256 # extra width height from the first pixel

        if count == 0:
            INPUT = Texture2D(w, h, R8G8B8A8_UNORM)
            staging_buffer = Buffer(INPUT.size, HEAP_UPLOAD)
            overlay.setGeometry(0, 0, w, h)
            swapchain = Swapchain((display_id_int, overlay.xid), R8G8B8A8_UNORM, 3)       
       
        buffer = (ctypes.c_ubyte*4*w*h).from_address(addr)                    
        # bitmap = numpy.frombuffer(buffer, dtype=numpy.uint32)

        staging_buffer.upload2d(buffer, INPUT.row_pitch, INPUT.width, INPUT.height, get_pixel_size(R8G8B8A8_UNORM))
        staging_buffer.copy_to(INPUT)
        swapchain.present(INPUT)
        
        count += 1        
    cap.destroy()

if not pid: 
    print("vkcube not running.")
else:        
    compute_thread = threading.Thread(target=worker, args=())
    compute_thread.start()              
    app.exec()
    running = 0
    print("END")
        
# => Unable to bind EGL context
# => The context is bound to a different thread
# [] release context