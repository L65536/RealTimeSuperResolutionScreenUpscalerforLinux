# pip install pyglet compushady pillow
# Requirements: [windows] pip install -r requirements.txt

# import os
# import numpy as np
import queue
import time
import threading

display_queue = 0 # int flag # queue.Queue(maxsize=3)
capture_queue = queue.Queue(maxsize=1)
time_display = 0 # on_draw()
time_compute = 0 # compute_worker()  # use SRCNN.time_compute
# time_capture = 0 # capture_worker() # use CAP.time_capture
count = 0

from winrt.windows.graphics.imaging import SoftwareBitmap, BitmapBufferAccessMode
from win32gui import GetClientRect
from ctypes import windll
windll.user32.SetProcessDPIAware() # HiDPI support

import pyglet
display = pyglet.display.get_display()
screen = display.get_default_screen()
screen_width = screen.width
screen_height = screen.height
print(f"Monitor Resolution: {screen_width}x{screen_height}")

# local library import
import LIBSHADER_SRCNN as SRCNN
import CAPTURE_WINDOWS as CAP
import CLI_MENU
handle, clientW, clientH, windowW, windowH = CLI_MENU.get_window_handle()
print(handle, clientW, clientH)

window = pyglet.window.Window(clientW*2, clientH*2, resizable=False, caption='Display', vsync=True)

@window.event
def on_key_press(symbol, modifiers):
    if symbol == pyglet.window.key.F11:
        window.set_fullscreen(not window.fullscreen)
    if symbol == pyglet.window.key.ESCAPE:
        window.close()
        pyglet.app.exit()
    if symbol == pyglet.window.key.SPACE:
        window.close()
        pyglet.app.exit()

@window.event
def on_mouse_press(x, y, button, modifiers):
    if button == pyglet.window.mouse.MIDDLE:
        window.set_fullscreen(not window.fullscreen)
    if button == pyglet.window.mouse.LEFT: pass
    if button == pyglet.window.mouse.RIGHT: pass

@window.event
def on_draw():
    global count, time_display, display_queue

    if False: # mirroring mode, for testing
        bitmap = capture_queue.get()
        capture_queue.task_done() # still keeps reference # release resource ???
        w = bitmap.pixel_width
        h = bitmap.pixel_height
        buffer = bitmap.lock_buffer(BitmapBufferAccessMode.READ)
        mv = memoryview(buffer.create_reference())
        img = pyglet.image.ImageData(w, h, 'RGBA', mv, pitch=-w*4) #'RGBX''BGRX''RGBA''BGRA' // mv may not working without pitch, mv.tobytes() slower
        #img = pyglet.image.ImageData(w, h, 'RGBA', mv.tobytes(), pitch=-w*4) #'RGBX''BGRX''RGBA''BGRA'
        img.blit(0, 0)
        count+=1

    if display_queue:
        t = time.perf_counter()
        window.clear()
        img = pyglet.image.ImageData(SRCNN.OUTPUT.row_pitch//4, SRCNN.OUTPUT.height, "RGBA", SRCNN.readback_buffer.readback(), pitch=-SRCNN.OUTPUT.row_pitch)
        #img = pyglet.image.ImageData(SRCNN.OUTPUT.row_pitch//4, SRCNN.OUTPUT.height, "RGBA", SRCNN.readback_buffer.readback())
        img.blit(0, 0)
        display_queue = 0
        count+=1

        # string = f"{window.width}x{window.height} {count}"
        # label = pyglet.text.Label(string, font_size=72, x=window.width // 2, y=window.height // 2, anchor_x='center', anchor_y='center')

        w = clientW
        h = clientH
        string = str(count)+" "+str(w)+"x"+str(h)+" "+str(int(CAP.time_capture))+"/"+str(int(time_compute))+"/"+str(int(time_display))+" ms (CAP/GPU/DISP)"
        window.set_caption(string)
        # label = pyglet.text.Label(string, font_size=72, x=window.width//32, y=window.height*15//16, color = (255,0,0))
        # label.draw()
        time_display = (time.perf_counter() - t)*1000
        display_queue = 0

def calculate_client_offset(w, h):
    boarder=(w-clientW)//2
    top=h-clientH-boarder
    # print(boarder, top)
    return boarder, top

first_run = 1
running = 1
def compute_worker():
    global first_run, offsetX, offsetY
    global time_compute
    global display_queue

    while running:        
        bitmap = capture_queue.get()
        capture_queue.task_done() # still keeps reference # release resource ???
        
        t = time.perf_counter()
        w = bitmap.pixel_width
        h = bitmap.pixel_height
        buffer = bitmap.lock_buffer(BitmapBufferAccessMode.READ)
        mv = memoryview(buffer.create_reference())

        if first_run:
            first_run = 0
            SRCNN.init_buffer(w, h)
            # offsetX, offsetY = (0, 0) #calculate_client_offset(w, h)
        SRCNN.compute(mv, w, h)
        time_compute = (time.perf_counter() - t)*1000

        display_queue = 1 # trigger on_draw(vsync) from compute_worker

capture_thread = threading.Thread(target=CAP.capture_worker, args=(capture_queue, handle, clientW, clientH, windowW, windowH))
capture_thread.start()
compute_thread = threading.Thread(target=compute_worker, args=())
compute_thread.start()
pyglet.app.run() # default 1/60, 0=continuously, None=manual
running = 0 # signal terminating thread
CAP.running = 0 # signal terminating thread
print('End')
