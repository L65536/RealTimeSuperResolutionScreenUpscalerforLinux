# Test KDE/Plasma(wayland) and NVFBC_BACKEND_PIPEWIRE capture backend with virtual monitor
# Run this program, KDE/Plasma will display a "Screen sharing" dialog for all possible capture targets, choose "New virtual outout"
# By default(assumption), the virtual monitor has resolution of 1920x1080 and located to the right of current monitor.
# Virtual monitor details can be checked/changed at KDE monitor configuration page.
# You can move any target program to the monitor:
    #1 by dragging to the right or
    #2 right click menu on titlebar, choose "Move to screen" ...

# tested on CachyOS Linux (Arch Linux based)
# DE: KDE Plasma 6.4.5
# WM: KWin (Wayland)
# NVIDIA driver 580.95.05

# sudo pacman -S vulkan-devel
# pip install compushady

import threading
import time
import queue
import numpy
import os
import pprint
from compushady import Swapchain
from compushady.formats import R8G8B8A8_UNORM

import SRCNN3 as SR

import ctypes
LibName = '../nvfbc/nvfbc-pipewire.so'
LibName = 'nvfbc-pipewire.so'
AbsLibPath = os.path.dirname(os.path.abspath(__file__)) + os.path.sep + LibName
cap = ctypes.CDLL(AbsLibPath)
cap.init.argtypes = None
cap.init.restype = ctypes.c_int
cap.capture.argtypes = (ctypes.c_int,)
cap.capture.restype = ctypes.c_void_p # without this, 64 bit address got truncated to 32 bit (ctypes default action) => segmentation fault 
cap.destroy.argtypes = None
cap.destroy.restype = ctypes.c_int

def capture_worker():
    global count, buffer, w, h, running
    cap.init()
    while running:
        addr = cap.capture(0)
        if addr is None:
            print("Capture failed.")
            cap.destroy()
            running = False
            return

        dimension = (ctypes.c_ubyte*4).from_address(addr)
        w = dimension[0]+dimension[1]*256 # extra width height from the first pixel
        h = dimension[2]+dimension[3]*256 # extra width height from the first pixel
        buffer = (ctypes.c_ubyte*4*w*h).from_address(addr)
        # bitmap = numpy.frombuffer(buffer, dtype=numpy.uint32)
        # print(w, h)

        capture_queue.put(1) # blocking, signal captured frame is ready
    cap.destroy()

def compute_worker():
    global first_run, count, total_time_compute
    global screen

    while running:
        if(capture_queue.qsize() == 0):
            time.sleep(1.0/60)
            continue

        if first_run:
            first_run = 0
            SR.init_buffer(w, h)
            #window.set_size(1920*2, 1080*2)

        t = time.perf_counter()
        SR.upload(buffer) # DEBUG print(w,h, mv.shape, mv.nbytes, mv.strides)
        capture_queue.get() # effectively non-blocking, signal ready to get another frame
        # swapchain.present(SRCNN.INPUT) # DEBUG mirror test
        SR.compute()
        total_time_compute += time.perf_counter() - t
        count+=1
        #swapchain.present(SR.OUTPUT)

        #SR.download()
        #surface = pygame.image.frombuffer(SR.readback_buffer.readback(), (SR.OUTPUT.row_pitch//4, SR.OUTPUT.height), 'BGRA')
        #surface = pygame.image.frombuffer(SR.readback_buffer.readback(), (SR.OUTPUT.row_pitch//4, SR.OUTPUT.height), 'BGRA')
        #screen.blit(surface, (0, 0))
        #pygame.display.flip()

running = True # common thread execution control flag
first_run = 1 # init flag
count = 0 # total frame count
total_time_compute = 0 # compute time
capture_queue = queue.Queue(maxsize=1) # [capture worker] capture control

capture_thread = threading.Thread(target=capture_worker, args=())
capture_thread.start()
compute_thread = threading.Thread(target=compute_worker, args=())
compute_thread.start()
# Unable to bind EGL context => put capture and display on different threads, init capture first, pygame latter

print('KDE/Plasma will display a "Screen sharing" dialog.\nChoose "New virtual outout".\nThe new virtual screen is located to the right.\nAny target window can be dragged or send there.\n')
import pyglet
window = pyglet.window.Window(width=1920, height=1080, caption='Display')

import ctypes
xlib = ctypes.cdll.LoadLibrary("libX11.so")
display_id_int = xlib.XOpenDisplay( ctypes.c_int(0) )
print(display_id_int)
print(window._window)
swapchain = Swapchain((display_id_int, window._window), R8G8B8A8_UNORM, 3)
print(xxx) # crash at swapchain init

@window.event
def on_draw():
    pass

pyglet.app.run()
swapchain = None
