# Test KDE/Plasma(wayland) and NVFBC_BACKEND_PIPEWIRE capture backend with virtual monitor
# Run this program, KDE/Plasma will display a "Screen sharing" dialog for all possible capture targets, choose "New virtual outout"
# By default(assumption), the virtual monitor has resolution of 1920x1080 and located to the right of current monitor.
# Virtual monitor details can be checked/changed at KDE monitor configuration page.
# You can move any target program to the monitor:
    #1 by dragging to the right or
    #2 right click menu on title bar, choose "Move to screen" ...

# sudo pacman -S vulkan-devel
# pip install compushady

import threading
import time
import queue
import numpy
import os
import compushady 
import compushady.formats 
import glfw

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
    global count, buffer, w, h, running, total_time_capture
    cap.init()
    while running:
        t = time.perf_counter()
        addr = cap.capture(0)
        total_time_capture += time.perf_counter() - t
        if addr is None:
            print("Capture failed.")
            cap.destroy()
            running = False
            return

        dimension = (ctypes.c_ubyte*4).from_address(addr)
        w = dimension[0]+dimension[1]*256 # extra width height from the first pixel
        h = dimension[2]+dimension[3]*256 # extra width height from the first pixel
        buffer = (ctypes.c_ubyte*4*w*h).from_address(addr)
        capture_queue.put(1) # blocking, signal captured frame is ready
    cap.destroy()

running = True # common thread execution control flag
first_run = 1 # initialization flag
count = 0 # total frame count
total_time_capture = 0
total_time_compute = 0
total_time_display = 0

capture_queue = queue.Queue(maxsize=1) # [capture worker] capture control
capture_thread = threading.Thread(target=capture_worker, args=())
capture_thread.start()

width = 1920
height = 1080

glfw.init()
glfw.window_hint(glfw.CLIENT_API, glfw.NO_API)
window = glfw.create_window(width, height, "XXX", None, None) # free window size
assert os.environ.get("XDG_SESSION_TYPE") == "wayland", "This script only supports wayland."
swapchain = compushady.Swapchain((glfw.get_wayland_display(), glfw.get_wayland_window(window)),
            compushady.formats.B8G8R8A8_UNORM, 3, None, width*2, height*2)

print('\nKDE/Plasma will display a "Screen sharing" dialog.\nChoose "New virtual output".\nThe new virtual screen is located to the right.\nAny target window can be dragged or send there.\n')
# virtual screen fixed at 1080p ?
# try krfb-virtualmonitor to create virtual monitor of desired resolution 720p 1080p

while not glfw.window_should_close(window):
    glfw.poll_events()
    if glfw.get_key(window, glfw.KEY_1): pass

    if(capture_queue.qsize() == 0):
        time.sleep(1.0/120)
        continue

    if first_run:
        first_run = 0
        SR.init_buffer(w, h)

    t = time.perf_counter()
    SR.upload(buffer)
    capture_queue.get() # effectively non-blocking, signal ready to get another frame        
    SR.compute()
    total_time_compute += time.perf_counter() - t
    
    t = time.perf_counter()
    swapchain.present(SR.OUTPUT)
    total_time_display += time.perf_counter() - t
        
    count+=1

running = False
swapchain = None
glfw.terminate()
print(f'\nTotal frames processed = {count}')
print(f'Average capture time/frame = {(total_time_capture/count)*1000:.2f} (ms)') # 17 ms for 60hz (including waiting for screen updates)
print(f'Average compute time/frame = {(total_time_compute/count)*1000:.2f} (ms)') # 6-7 ms for 1080p source
print(f'Average display time/frame = {(total_time_display/count)*1000:.2f} (ms)') # 0.2 ms for 4k output

# tested on CachyOS Linux (Arch Linux based)
# DE: KDE Plasma 6.4.5
# WM: KWin (Wayland)
# NVIDIA driver 580.95.05

# kscreen-doctor output.<OUTPUT_NAME>.scale.<SCALE_FACTOR>
# kscreen-doctor output.1.scale.1
# kscreen-doctor output.1.scale.2

