# Requirements: [Linux] pip install xlib pyside6 compushady
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
import LIBSHADER_SRCNN3 as SR
#import CAPTURE_LINUX_NVFBC as CAP
import ctypes
nvfbc = '../nvfbc-direct/nvfbc-direct.so'
cap = ctypes.CDLL(nvfbc)
cap.init.argtypes = (ctypes.c_int,)
cap.init.restype = ctypes.c_int
cap.capture.argtypes = (ctypes.c_int,)
cap.capture.restype = ctypes.c_void_p # without this, 64 bit address got truncated to 32 bit (ctypes default action) => segmentation fault 
cap.destroy.argtypes = None
cap.destroy.restype = ctypes.c_int

from Xlib import X, display
from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QPainter, QPen, QPixmap, QCursor
from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6 import QtCore, QtGui, QtWidgets
import signal
signal.signal(signal.SIGINT, signal.SIG_DFL) # enables ctrl-c in qt, or ctrl-z does not destroy overlay window
# import keyboard # hotkey requires sudo/root

if True: # starting CLI UI
    print("Real Time Window Super Resolution Upscaler")    
    print("[To exit] Press Ctrl-C in the terminal window.")
    print("[To exit] Move mouse to the upper-left corner.")       
    print("Upscaling the next active window in 5 seconds...\n")
    time.sleep(5)
    
    disp = display.Display()
    root = disp.screen().root
    active_window_atom = disp.intern_atom('_NET_ACTIVE_WINDOW')    
    window_id_prop = root.get_full_property(active_window_atom, X.AnyPropertyType)        
    handle = window_id_prop.value[0]
   
    window = disp.create_resource_object('window', handle)
    geometry = window.get_geometry()    
    wproperty = window.get_full_property(disp.intern_atom('_NET_WM_NAME'), 0)         
    if wproperty: title = wproperty.value.decode('utf-8') #.lower()
    else: title = None
    clientW = geometry.width
    clientH = geometry.height
    #windowW = geometry.width
    #windowH = geometry.height
    position = geometry.root.translate_coords(window, 0, 0)    
    print(f"[{handle}] ({geometry.width} x {geometry.height} at {position.x}x{position.y}) {title}")    
            
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

def inspect(x):
    print(">>> VALUE >>>",x)
    print(">>> TYPE >>>",type(x))
    print(">>> DIR >>>",dir(x))

import ctypes
xlib = ctypes.cdll.LoadLibrary("libX11.so")
display_id_int = xlib.XOpenDisplay( ctypes.c_int(0) ) #glfw.get_x11_display() # how to get this from Xlib/Display Lib ??? 

app = QApplication([])
overlay = OverlayWindow(clientW*2, clientH*2, opacity=100)
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
            print(f'Total frames processed = {count}, average compute time/frame = {(total_time_compute/count)*1000:.2f} (ms)\n')
            running = 0                                    
            overlay.close() #overlay.hide()
            app.quit() # for single run
            #sys.exit()
            return
            # break # for multi run
                       
        # if True: # Compute
        if not running: break
        if(capture_queue.qsize() == 0):
            time.sleep(1.0/60) 
            continue
            
        #bitmap = CAP.bitmap        
        t = time.perf_counter()
                
        #w = clientW
        #h = clientH
        #mv = memoryview(bitmap) # cbuffer = (ctypes.c_ubyte*clientW*clientH*4)()
        
        # Reset out-of-bound mouse position, warp to the other side        
        if False:
            if x<position.x: QCursor.setPos(position.x+clientW, y)
            if x>position.x+clientW: QCursor.setPos(position.x, y)
            if y<position.y: QCursor.setPos(x, position.y+clientH)
            if y>position.y+clientH: QCursor.setPos(x, position.y)
        
        # Draw crusor and set opacity according to mouse location
        if True:
            if x>position.x and x<position.x+clientW and y>position.y and y<position.y+clientH: 
                overlay.setWindowOpacity(100/100)
                # Draw cursor position
                arr = numpy.frombuffer(buffer, dtype=numpy.uint32)
                arr.shape = (h,w)                
                arr[:,x-position.x] = 0xFFFFFFFF
                arr[y-position.y,:] = 0xFFFFFFFF
            else: overlay.setWindowOpacity(20/100) 

        if first_run:
            first_run = 0
            SR.init_buffer(w, h)
        
        # DEBUG print(w,h, mv.shape, mv.nbytes, mv.strides)        
        SR.upload(buffer)
        if not running: break       
        capture_queue.get() # blocking, ready to get another frame              
        # swapchain.present(SRCNN.INPUT) # DEBUG mirror test

        SR.compute()
        total_time_compute += time.perf_counter() - t
        time_compute = (time.perf_counter() - t)*1000
             
        t = time.perf_counter()                                     
        swapchain.present(SR.OUTPUT)        
        time_display = (time.perf_counter() - t)*1000    
        #string = str(count)+" "+str(int(CAP.time_capture))+"/"+str(int(time_compute))+"/"+str(int(time_display))+" ms (CAP/GPU/DISP)"
        #print(string)
        # time_capture is locked to screen updates(refresh rate), not actual processor time taken         
        count+=1
    print("compute_worker() ended.")    

def capture_worker(pid):
    global count, buffer, w, h, running
    print(pid)
    cap.init(pid) # nvfbc-direct.so
    while running:                                                                                                                                           
        addr = cap.capture(0)
        if addr is None:
            print("Capture failed.")
            cap.destroy()
            running = 0
            overlay.close() #overlay.hide()
            app.quit() 
            return
        dimension = (ctypes.c_ubyte*4).from_address(addr)            
        w = dimension[0]+dimension[1]*256 # extra width height from the first pixel
        h = dimension[2]+dimension[3]*256 # extra width height from the first pixel

        if False: #if count == 0:
            INPUT = Texture2D(w, h, R8G8B8A8_UNORM)
            staging_buffer = Buffer(INPUT.size, HEAP_UPLOAD)
            overlay.setGeometry(0, 0, w, h)
            swapchain = Swapchain((display_id_int, overlay.xid), R8G8B8A8_UNORM, 3)       
               
        buffer = (ctypes.c_ubyte*4*w*h).from_address(addr)                    
        # bitmap = numpy.frombuffer(buffer, dtype=numpy.uint32)

        #staging_buffer.upload2d(buffer, INPUT.row_pitch, INPUT.width, INPUT.height, get_pixel_size(R8G8B8A8_UNORM))
        #staging_buffer.copy_to(INPUT)
        #swapchain.present(INPUT)
        
        capture_queue.put(1) # blocking, signal captured frame is ready
        #count += 1        
    cap.destroy()
    
capture_thread = threading.Thread(target=capture_worker, args=[1924])
capture_thread.start()
compute_thread = threading.Thread(target=compute_worker, args=())
compute_thread.start()
            
app.exec()

print('Ending') # not ending gracefully???
print(f'Total frames processed = {count}, average compute time/frame = {(total_time_compute/count)*1000:.2f} (ms)\n')
running = 0 # signal terminating thread
# CAP.running = 0 # signal terminating thread
#if capture_queue.size(): capture_queue.get() # blocking
swapchain = None
disp.close() # xlib
print('End')
