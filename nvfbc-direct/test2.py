# Test NVFBC_BACKEND_DIRECT backend
# run ./vkcube

import numpy
import os
import psutil # pip install psutil
import threading
import time

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
overlay = OverlayWindow(600, 600, opacity=50)

import ctypes
LibName = '../nvfbc/nvfbc-direct.so'
LibName = 'nvfbc/nvfbc-direct.so'
AbsLibPath = os.path.dirname(os.path.abspath(__file__)) + os.path.sep + LibName
cap = ctypes.CDLL(AbsLibPath)

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
        addr = cap.capture(1)
        dimension = (ctypes.c_ubyte*4).from_address(addr)            
        w = dimension[0]+dimension[1]*256 # extra width height from the first pixel
        h = dimension[2]+dimension[3]*256 # extra width height from the first pixel               
        buffer = (ctypes.c_ubyte*4*w*h).from_address(addr)                    
        bitmap = numpy.frombuffer(buffer, dtype=numpy.uint32)
        
        #img = pyglet.image.ImageData(w, h, 'RGBA', bitmap, pitch=-w*4) #'RGBX''BGRX''RGBA''BGRA' // mv may not working without pitch, mv.tobytes() slower
        #img.blit(0, 0)
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