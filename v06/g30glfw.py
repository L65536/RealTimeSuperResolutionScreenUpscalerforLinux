# pip install glfw compushady pillow
# Requirements: [windows] pip install -r requirements.txt
# Requirements: [Linux] pip install xlib
# Requirements: [Linux] libvulkan-dev and libx11-dev on Debian etc

# import numpy as np
import platform
import queue
import time
import threading
from compushady import Swapchain
from compushady.formats import R8G8B8A8_UNORM

display_queue = queue.Queue(maxsize=1)
capture_queue = queue.Queue(maxsize=1)
time_display = 0 # on_draw()
time_compute = 0 # compute_worker()  # use SRCNN.time_compute
# time_capture = 0 # capture_worker() # use CAP.time_capture
count = 0

if platform.system() == 'Windows':
    from winrt.windows.graphics.imaging import SoftwareBitmap, BitmapBufferAccessMode
    from win32gui import GetClientRect
    from ctypes import windll
    windll.user32.SetProcessDPIAware() # HiDPI support

# local library import
import LIBSHADER_SRCNN2 as SRCNN

if platform.system() == 'Windows':
    import CAPTURE_WINDOWS as CAP
    import CLI_MENU as MENU
else:
    import CAPTURE_LINUX as CAP
    import CLI_MENU_LINUX as MENU

handle, clientW, clientH, windowW, windowH = MENU.get_window_handle() # run CLI menu
print(handle, clientW, clientH)

import glfw
glfw.init()
glfw.window_hint(glfw.CLIENT_API, glfw.NO_API)
window = glfw.create_window(windowW*2, windowH*2, 'Display', None, None)

if platform.system() == 'Windows':
    swapchain = Swapchain(glfw.get_win32_window(window), R8G8B8A8_UNORM, 3)
else:
    swapchain = Swapchain((glfw.get_x11_display(), glfw.get_x11_window(window)), R8G8B8A8_UNORM, 3)

first_run = 1
running = 1
def compute_worker():
    global first_run, offsetX, offsetY
    global time_compute
    global display_queue
    
    while running:
        bitmap = capture_queue.get() # blocking        
        t = time.perf_counter()

        if platform.system() == 'Windows':
            w = bitmap.pixel_width
            h = bitmap.pixel_height
            buffer = bitmap.lock_buffer(BitmapBufferAccessMode.READ)
            mv = memoryview(buffer.create_reference())
        else:
            w = clientW
            h = clientH
            mv = memoryview(bitmap) # cbuffer = (ctypes.c_ubyte*clientW*clientH*4)()

        if first_run:
            first_run = 0
            SRCNN.init_buffer(w, h)
            # offsetX, offsetY = (0, 0) #calculate_client_offset(w, h)

        SRCNN.upload(mv, w, h)
        if running: capture_queue.task_done() # start another capture
        # swapchain.present(SRCNN.INPUT) # mirror test

        if running: SRCNN.compute(mv, w, h)
        time_compute = (time.perf_counter() - t)*1000
        display_queue.put(1)

capture_thread = threading.Thread(target=CAP.capture_worker, args=(capture_queue, handle, clientW, clientH, windowW, windowH))
capture_thread.start()
compute_thread = threading.Thread(target=compute_worker, args=())
compute_thread.start()
        
while not glfw.window_should_close(window):
    glfw.poll_events()

    if(display_queue.qsize() == 1):
        t = time.perf_counter()
        d = display_queue.get()             
        display_queue.task_done()
        if d is None: break
        
        swapchain.present(SRCNN.OUTPUT)
        time_display = (time.perf_counter() - t)*1000
    
        string = str(count)+" "+str(int(CAP.time_capture))+"/"+str(int(time_compute))+"/"+str(int(time_display))+" ms (CAP/GPU/DISP)"
        glfw.set_window_title(window, string)
        count+=1
        
running = 0 # signal terminating thread
CAP.running = 0 # signal terminating thread
swapchain = None
glfw.terminate()
print('End')

"""
swapchain.present() offsets can only be positive, not suitable for cropping

if(capture_queue.qsize() == 1): 
    capture_queue.task_done()
    capture_queue.put(None)
if(display_queue.qsize() == 1): 
    display_queue.task_done()
    display_queue.put(None)

display_queue.join()
capture_queue.join()

def calculate_client_offset(w, h):
    boarder=(w-clientW)//2
    top=h-clientH-boarder
    # print(boarder, top)
    return boarder, top
"""    
