# KDE/Plasma(wayland) and NVFBC_BACKEND_PIPEWIRE capture backend with virtual monitor

# Basic usage concepts summary:
# 1. A new virtual screen will be created and magnified on primary monitor
# 2. Send your app to the virtual screen by using right click menu on the taskbar.
# 3. Move mouse cursor beyond the right side monitor boundary to access your target app in the virtual screen.
# 4. Close this app by by using right click menu on the taskbar.

# Run this script, KDE/Plasma will display a "Screen sharing" dialog for all possible capture targets, choose "New virtual output"
# By default, the virtual monitor should have resolution of 1920x1080 and located to the right of current monitor.
# Virtual monitor details can be checked/changed at KDE monitor configuration page.
# You can move any target program to the monitor:
    #1 by dragging them to the right or
    #2 right click menu on title bar or taskbar, choose "Move to screen" ...
# Use middle click or [window] key to return to desktop.
# Use right click menu on the taskbar to close this app.

# sudo pacman -S vulkan-devel
# pip install compushady glfw

import threading
import time
import queue
import numpy
import os
import compushady
import compushady.formats
import glfw # not pyglfw
from PIL import Image, ImageDraw, ImageFont, ImageOps  

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

def mouse_button_callback(window, button, action, mods):
    if button == glfw.MOUSE_BUTTON_MIDDLE and action == glfw.PRESS: glfw.iconify_window(window)

def custom_cursor():
    image = Image.open("cursor6250.png").convert("RGBA")
    image = image.resize((128, 128), Image.LANCZOS)
    image = ImageOps.pad(image, (1280,128) , centering=(0,0), color='red')

    text = "      Move cursor beyond the boundary to access your target app >>>>>>"
    font = ImageFont.truetype("arial.ttf", 64)
    draw = ImageDraw.Draw(image)
    draw.text((0,0), text, fill=(255, 255, 255), font=font)

    return glfw.create_cursor(image, 0, 0) # hotspot at top-left corner

running = True # common thread execution control flag
first_run = 1 # initialization flag
count = 0 # total frame count
total_time_capture = 0
total_time_compute = 0
total_time_display = 0

print('\nKDE/Plasma will display a "Screen sharing" dialog.\nChoose "New virtual output".\n')
print('The new virtual screen is located to the right by default.\nAny target app can be dragged or send there.\n')
print('Move mouse cursor beyond the right side monitor boundary to access your target app in the virtual screen.\n')
capture_queue = queue.Queue(maxsize=1) # [capture worker] capture control
capture_thread = threading.Thread(target=capture_worker, args=())
capture_thread.start()

glfw.init()
monitor = glfw.get_primary_monitor()
mode = glfw.get_video_mode(monitor)
width, height = mode.size.width, mode.size.height
glfw.window_hint(glfw.CLIENT_API, glfw.NO_API)
glfw.window_hint(glfw.DECORATED, glfw.FALSE)
glfw.window_hint(glfw.RED_BITS, mode.bits.red)
glfw.window_hint(glfw.GREEN_BITS, mode.bits.green)
glfw.window_hint(glfw.BLUE_BITS, mode.bits.blue)
glfw.window_hint(glfw.REFRESH_RATE, mode.refresh_rate)
window = glfw.create_window(width, height, "Borderless Fullscreen", monitor, None)
cursor = custom_cursor()
glfw.set_cursor(window, cursor)
glfw.set_mouse_button_callback(window, mouse_button_callback)

assert os.environ.get("XDG_SESSION_TYPE") == "wayland", "This script only supports wayland."
swapchain = compushady.Swapchain((glfw.get_wayland_display(), glfw.get_wayland_window(window)),
            compushady.formats.B8G8R8A8_UNORM, 3, None, width*2, height*2)

print('\nThe magnified window, "Borderless Fullscreen", should be available minimized on the taskbar.\n')
print('Use middle click or [window] key to return to desktop.\n')
print('Use right click menu on the taskbar to close this app.\n')
glfw.iconify_window(window)
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
glfw.destroy_cursor(cursor)
glfw.terminate()
print(f'\nTotal frames processed = {count}')
print(f'Average capture time/frame = {(total_time_capture/count)*1000:.2f} (ms)') # 17 ms for 60hz (including waiting for screen updates)
print(f'Average compute time/frame = {(total_time_compute/count)*1000:.2f} (ms)') # 6-7 ms for 1080p source
print(f'Average display time/frame = {(total_time_display/count)*1000:.2f} (ms)') # 0.2 ms for 4k output
print('End')
# Virtual screen locked to 1080p ?
# try krfb-virtualmonitor to create virtual monitor of desired resolution 720p 1080p