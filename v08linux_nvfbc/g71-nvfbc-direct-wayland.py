"""
[] [wayland support] compushady/Swapchain
    VK_STRUCTURE_TYPE_WAYLAND_SURFACE_CREATE_INFO_KHR;
    (struct wl_display *)display;
    (struct wl_surface *)window;
[] [wayland support] kde mouse position => kwin
[] [wayland support] test QT6 transparency overlay
"""

pid = 0 # User definable pid (process id) of the target Vulkan program. Use nvidia-smi for a list.
target_process_name = "wine" # If pid = 0 (not defined by user), look for target instances by name instead

# Requirements: [Linux] pip install pyside6 compushady psutil
# Requirements: [Linux] libvulkan-dev package

import sys
import queue
import time
import threading
import numpy
import psutil

if pid == 0:
    for p in psutil.process_iter():
        if target_process_name in p.name():
            print(p)
            pid = p.pid
            break
        
from compushady import Swapchain
from compushady.formats import R8G8B8A8_UNORM

# Local library import
# import CAPTURE_LINUX_NVFBC as CAP
import LIBSHADER_SRCNN3 as SR

def inspect(x):
    print(">>> VALUE >>>",x)
    print(">>> TYPE >>>",type(x))
    print(">>> DIR >>>",dir(x))

import ctypes
nvfbc = '../nvfbc-direct/nvfbc-direct.so'
cap = ctypes.CDLL(nvfbc)
cap.init.argtypes = (ctypes.c_int,)
cap.init.restype = ctypes.c_int
cap.capture.argtypes = (ctypes.c_int,)
cap.capture.restype = ctypes.c_void_p # without this, 64 bit address got truncated to 32 bit (ctypes default action) => segmentation fault
cap.destroy.argtypes = None
cap.destroy.restype = ctypes.c_int

# from Xlib import X, display
from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QPainter, QPen, QPixmap, QCursor
from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6 import QtCore, QtGui, QtWidgets
import signal
signal.signal(signal.SIGINT, signal.SIG_DFL) # enables ctrl-c in qt, or ctrl-z does not destroy overlay window

if True: # starting CLI UI
    print("Real Time Window Super Resolution Upscaler")
    print("[To exit] Press Ctrl-C in the terminal window.")
    print("[To exit] Move mouse to the upper-left corner.")
    print(f"Upscaling (pid={pid}) or ({target_process_name}) window in 5 seconds...\n")    
    time.sleep(5)

    """
    clientW = geometry.width
    clientH = geometry.height
    position = geometry.root.translate_coords(window, 0, 0)
    print(f"[{handle}] ({geometry.width} x {geometry.height} at {position.x}x{position.y}) {title} PID={pid}")
    """

class OverlayWindow(QMainWindow):
    def __init__(self, width, height, opacity):
        super().__init__()
        self.opacity = opacity/100
        self.setWindowOpacity(self.opacity)
        self.setGeometry(0, 0, width, height)
        self.setWindowFlags(self.windowFlags()| Qt.WindowTransparentForInput|Qt.X11BypassWindowManagerHint)
        self.show()
        self.xid = int(self.winId())

#import ctypes
#xlib = ctypes.cdll.LoadLibrary("libX11.so")
#display_id_int = xlib.XOpenDisplay( ctypes.c_int(0) ) #glfw.get_x11_display()

app = QApplication([])
overlay = OverlayWindow(clientW*2, clientH*2, opacity=100)
swapchain = Swapchain((display_id_int, overlay.xid), R8G8B8A8_UNORM, 3) ### how to support this in wayland??? try glfw (no transparency)

count = 0 # total frame count
running = 1 # common thread execution control flag
first_run = 1 # init flag
time_compute = 0 # compute time
total_time_compute = 0 # compute time
capture_queue = queue.Queue(maxsize=1) # [capture worker] capture control

def compute_worker():
    global running, first_run, count, total_time_compute

    while running:
        """
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

        if not running: break
        """
        if(capture_queue.qsize() == 0):
            time.sleep(1.0/60)
            continue

        t = time.perf_counter()

        # wayland: get mouse position in KDE
        # Draw crusor and set opacity according to mouse location
        if False:
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
        # time_compute = (time.perf_counter() - t)*1000

        swapchain.present(SR.OUTPUT)
        count+=1
    print("compute_worker() ended.")

def capture_worker(pid):
    global count, buffer, w, h, running
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

        buffer = (ctypes.c_ubyte*4*w*h).from_address(addr)
        # bitmap = numpy.frombuffer(buffer, dtype=numpy.uint32)

        capture_queue.put(1) # blocking, signal captured frame is ready
    cap.destroy()

capture_thread = threading.Thread(target=capture_worker, args=[pid])
capture_thread.start()
compute_thread = threading.Thread(target=compute_worker, args=())
compute_thread.start()

app.exec()

print('Ending') # not ending gracefully???
print(f'Total frames processed = {count}, average compute time/frame = {(total_time_compute/count)*1000:.2f} (ms)\n')
running = 0 # signal terminating thread
swapchain = None
# disp.close() # xlib
print('End')