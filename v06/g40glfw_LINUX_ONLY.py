# Requirements: [Linux] pip install xlib glfw compushady
# Requirements: [Linux] libvulkan-dev and libx11-dev on Debian etc

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

# local library import
import LIBSHADER_SRCNN2 as SRCNN
import CAPTURE_LINUX as CAP
import CLI_MENU_LINUX as MENU

handle, clientW, clientH, windowW, windowH = MENU.get_window_handle() # run CLI menu
print(handle, clientW, clientH)

import glfw
glfw.init()
glfw.window_hint(glfw.RESIZABLE, glfw.FALSE)
glfw.window_hint(glfw.CLIENT_API, glfw.NO_API)
window = glfw.create_window(windowW*2, windowH*2, 'Display', None, None)
swapchain = Swapchain((glfw.get_x11_display(), glfw.get_x11_window(window)), R8G8B8A8_UNORM, 3)

capture_thread = threading.Thread(target=CAP.capture_worker, args=(capture_queue, handle, clientW, clientH, windowW, windowH))
capture_thread.start()

first_run = 1
running = 1        
while not glfw.window_should_close(window):
    glfw.poll_events() # non-blocking     

    if True: # Compute    
        bitmap = capture_queue.get() # blocking        
        t = time.perf_counter()

        w = clientW
        h = clientH
        mv = memoryview(bitmap) # cbuffer = (ctypes.c_ubyte*clientW*clientH*4)()

        if first_run:
            first_run = 0
            SRCNN.init_buffer(w, h)
        
        SRCNN.upload(mv, w, h)
        if running: capture_queue.task_done() # start another capture
        # swapchain.present(SRCNN.INPUT) # mirror test

        if running: SRCNN.compute(mv, w, h)
        time_compute = (time.perf_counter() - t)*1000
             
    if True: # Display
        t = time.perf_counter()                                     
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
