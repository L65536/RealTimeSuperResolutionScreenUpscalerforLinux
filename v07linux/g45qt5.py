# Requirements: [Linux] pip install xlib pyqt5 glfw compushady
# Requirements: [Linux] libvulkan-dev and libx11-dev on Debian etc

#import platform
import sys
import queue
import time
import threading
import numpy
from compushady import Swapchain
from compushady.formats import R8G8B8A8_UNORM

display_queue = queue.Queue(maxsize=1)
capture_queue = queue.Queue(maxsize=1)
time_display = 0 # on_draw()
time_compute = 0 # compute_worker()  # use SRCNN.time_compute
# time_capture = 0 # capture_worker() # use CAP.time_capture
count = 0

# local library import
import LIBSHADER_SRCNN2 as SRCNN
import CAPTURE_LINUX as CAP
from Xlib import X, display
from PyQt5.QtCore import QPoint, Qt
from PyQt5.QtGui import QPainter, QPen, QPixmap, QCursor
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5 import QtCore, QtGui, QtWidgets
import signal
signal.signal(signal.SIGINT, signal.SIG_DFL)
# import keyboard requires sudo/root

if True: # starting CLI UI
    print("Real Time Window Super Resolution Upscaler")    
    print("Use ctrl-C in the terminal window to exit.")
    print("Move mouse to the upper-left corner to exit.")       
    print("Upscaling the next active window in 5 seconds...")
    time.sleep(5)
    
    disp = display.Display()
    root = disp.screen().root
    active_window_atom = disp.intern_atom('_NET_ACTIVE_WINDOW')    
    window_id_prop = root.get_full_property(active_window_atom, X.AnyPropertyType)        
    handle = window_id_prop.value[0]
   
    window = disp.create_resource_object('window', handle)
    geometry = window.get_geometry()    
    wproperty = window.get_full_property(disp.intern_atom('_NET_WM_NAME'), 0)         
    title = wproperty.value.decode('utf-8') #.lower()
    clientW = geometry.width
    clientH = geometry.height
    windowW = geometry.width
    windowH = geometry.height    
    print(f"[{handle}] ({geometry.width} x {geometry.height}) {title}")
            
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

import glfw
glfw.init()
display_id_int = glfw.get_x11_display() # print(d) # int # How to get this number with XLIB or PYQT5 ????? changes every run
# print("X11 display ID (int) =", display_id_int)

app = QApplication([])
overlay = OverlayWindow(clientW*2, clientH*2, opacity=50)
swapchain = Swapchain((display_id_int, overlay.xid), R8G8B8A8_UNORM, 3)

first_run = 1
running = 1
total_time_compute = 0        
def compute_worker():
    global running, first_run, count, total_time_compute

    while running:  
        position = geometry.root.translate_coords(window, 0, 0)
        mouse = QCursor.pos() # print(mouse.x(),mouse.y()) 
        x = mouse.x()
        y = mouse.y()
        if x==0 and y==0:
            print(f'Total frames = {count}, average compute time/frame = {(total_time_compute/count)*1000:.2f} (ms)\n')
            running = 0                                    
            overlay.close() #overlay.hide()
            app.quit() # for single run
            sys.exit()
            return # for multi run
                       
        # if True: # Compute    
        bitmap = capture_queue.get() # blocking        
        t = time.perf_counter()

        w = clientW
        h = clientH
        mv = memoryview(bitmap) # cbuffer = (ctypes.c_ubyte*clientW*clientH*4)()

        # Set opacity according to mouse location
        if x>position.x and x<position.x+clientW and y>position.y and y<position.y+clientH: 
            overlay.setWindowOpacity(100/100)
            # Draw cursor position
            arr = numpy.frombuffer(bitmap, dtype=numpy.uint32)
            arr.shape = (h,w)
            arr[:,x-position.x] = 0xFFFFFFFF
            arr[y-position.y,:] = 0xFFFFFFFF
        else: overlay.setWindowOpacity(20/100) 

        if first_run:
            first_run = 0
            SRCNN.init_buffer(w, h)
        
        SRCNN.upload(mv, w, h)
        # capture_queue.task_done() # start another capture
        # swapchain.present(SRCNN.INPUT) # mirror test

        SRCNN.compute(mv, w, h)
        total_time_compute += time.perf_counter() - t
        time_compute = (time.perf_counter() - t)*1000
             
        #if True: # Display
        t = time.perf_counter()                                     
        swapchain.present(SRCNN.OUTPUT)        
        time_display = (time.perf_counter() - t)*1000    
        #string = str(count)+" "+str(int(CAP.time_capture))+"/"+str(int(time_compute))+"/"+str(int(time_display))+" ms (CAP/GPU/DISP)"
        #print(string)
        count+=1    

capture_thread = threading.Thread(target=CAP.capture_worker, args=(capture_queue, handle, clientW, clientH, windowW, windowH))
capture_thread.start()
compute_thread = threading.Thread(target=compute_worker, args=())
compute_thread.start()
            
app.exec()    
        
running = 0 # signal terminating thread
CAP.running = 0 # signal terminating thread
swapchain = None
disp.close() # xlib
print('End')
