# pip install compushady pyglet
# Requirements: [windows] pip install -r requirements.txt
# Requirements: [Linux] pip install xlib compushady pyglet
# Requirements: [Linux] libvulkan-dev and libx11-dev on Debian etc

import numpy
import platform
import queue
import time
import threading
from compushady import Swapchain
from compushady.formats import R8G8B8A8_UNORM

cropping = 0 # crop client window area with numpy for windows, CPU time expensive
display_queue = queue.Queue(maxsize=1)
capture_queue = queue.Queue(maxsize=1)
time_display = 0 # on_draw()
time_compute = 0 # compute_worker()  # use SRCNN.time_compute
time_capture = 0 # capture_worker() # use CAP.time_capture
count = 0

if platform.system() == 'Windows':
    from winrt.windows.graphics.imaging import SoftwareBitmap, BitmapBufferAccessMode
    from ctypes import windll
    windll.user32.SetProcessDPIAware() # HiDPI support

# local library import
import LIBSHADER_SRCNN3 as SRCNN

if platform.system() == 'Windows':
    import CAPTURE_WINDOWS as CAP
    import CLI_MENU as MENU
else:
    import CAPTURE_LINUX as CAP
    import CLI_MENU_LINUX as MENU

handle, clientW, clientH, windowW, windowH = MENU.get_window_handle() # run CLI menu
print(handle, clientW, clientH, windowW, windowH)

import pyglet
display = pyglet.display.get_display()
screen = display.get_default_screen()
screen_width = screen.width
screen_height = screen.height
print(f"Monitor Resolution: {screen_width}x{screen_height}\n")
if cropping: window = pyglet.window.Window(clientW*2, clientH*2, resizable=True, caption='Display', vsync=True)
else: window = pyglet.window.Window(windowW*2, windowH*2, resizable=True, caption='Display', vsync=True)

if platform.system() == 'Windows':
    swapchain = Swapchain(window._hwnd, R8G8B8A8_UNORM, 3) # window._hwnd for windows only
else:
    swapchain = Swapchain((glfw.get_x11_display(), glfw.get_x11_window(window)), R8G8B8A8_UNORM, 3)

def calculate_client_offset(w, h):
    boarder=(w-clientW)//2
    top=h-clientH-boarder
    return boarder, top

first_run = 1
running = 1
def compute_worker():
    global first_run, offsetX, offsetY
    global time_compute
    global display_queue

    while running:
        bitmap = capture_queue.get() # blocking
        t = time.perf_counter()

        if first_run:
            first_run = 0
            offsetX, offsetY = calculate_client_offset(bitmap.pixel_width, bitmap.pixel_height)
            if cropping: SRCNN.init_buffer(clientW, clientH)
            else: SRCNN.init_buffer(windowW, windowH)

        if platform.system() == 'Windows':
            buffer = bitmap.lock_buffer(BitmapBufferAccessMode.READ)
            if cropping: # CPU time expensive cropping with numpy
                np_window = numpy.frombuffer(buffer.create_reference(), dtype=numpy.uint32)
                np_client = np_window.reshape(bitmap.pixel_height, bitmap.pixel_width)[offsetY:offsetY+clientH, offsetX:offsetX+clientW]
                mv = np_client.tobytes()
            else:
                mv = memoryview(buffer.create_reference())
        else:
            mv = memoryview(bitmap) # cbuffer = (ctypes.c_ubyte*clientW*clientH*4)()

        SRCNN.upload(mv)
        SRCNN.compute()
        time_compute = (time.perf_counter() - t)*1000
        display_queue.put(1)

capture_thread = threading.Thread(target=CAP.capture_worker, args=(capture_queue, handle, clientW, clientH, windowW, windowH))
capture_thread.start()
compute_thread = threading.Thread(target=compute_worker, args=())
compute_thread.start()

@window.event
def on_draw():
    global count
    if(display_queue.qsize() == 1):
        t = time.perf_counter()
        display_queue.get()
        swapchain.present(SRCNN.OUTPUT)
        time_display = (time.perf_counter() - t)*1000

        string = f"#{count} {int(CAP.time_capture)}/{int(time_compute)}/{int(time_display)} ms (CAP/GPU/DISP)"
        window.set_caption(string)
        count+=1

pyglet.app.run()

running = 0 # terminating worker thread loop
CAP.running = 0 # terminating worker thread loop
swapchain = None
print('End')

"""
compushady swapchain.present() x,y offsets can only be positive, not suitable for lazy cropping
[glfw] CPU 100%
[pyglet] less CPU, limited frame rate with vsync?
[pyglet] flickering if skipping on_draw() updates, due to framebuffer flipping, expired old frame will be shown.
[pyglet] swapchain no display at fullscreen mode
[] cropping with CopySubresourceRegion((ID3D11Texture2D))
"""