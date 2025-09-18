# Test NVFBC_BACKEND_DIRECT backend
# run ./vkcube

import numpy
import os
import psutil # pip install psutil

import pyglet
display = pyglet.display.get_display()
screen = display.get_default_screen()
screen_width = screen.width
screen_height = screen.height
print(f"Monitor Resolution: {screen_width}x{screen_height}")

import ctypes
LibName = '../nvfbc/nvfbc-direct.so'
LibName = 'nvfbc/nvfbc-direct.so'
AbsLibPath = os.path.dirname(os.path.abspath(__file__)) + os.path.sep + LibName
cap = ctypes.CDLL(AbsLibPath)

cap.init.argtypes = (ctypes.c_int,)
cap.init.restype = ctypes.c_int
cap.capture.argtypes = (ctypes.c_int,)
cap.capture.restype = ctypes.c_void_p # without this, 64 bit address got truncated to 32 bit (ctypes default action) => segmentation fault 
cap.destroy.argtypes = None
cap.destroy.restype = ctypes.c_int

pid = 0
count = 0
running = 0
for p in psutil.process_iter():
    if 'vkcube' in p.name():
        print(p)
        pid = p.pid
        break

window = pyglet.window.Window(500, 500, resizable=False, caption='Display', vsync=True)
# => Unable to bind EGL context

"""
@window.event
def on_draw():
    global count
    if running:                                                                                                                                    
        addr = cap.capture(1)
        print(addr)
        dimension = (ctypes.c_ubyte*4).from_address(addr)            
        w = dimension[0]+dimension[1]*256 # extra width height from the first pixel
        h = dimension[2]+dimension[3]*256 # extra width height from the first pixel               
        buffer = (ctypes.c_ubyte*4*clientW*clientH).from_address(addr)                    
        bitmap = numpy.frombuffer(buffer, dtype=numpy.uint32)
        print(clientW, clientH)
        img = pyglet.image.ImageData(w, h, 'RGBA', bitmap, pitch=-w*4) #'RGBX''BGRX''RGBA''BGRA' // mv may not working without pitch, mv.tobytes() slower
        img.blit(0, 0)
        count += 1
"""
if not pid: 
    print("vkcube not running.")
else: 
    print(pid)
    cap.init(pid)
    while count < 20:                                                                                                                               
            addr = cap.capture(1)
            dimension = (ctypes.c_ubyte*4).from_address(addr)            
            clientW = dimension[0]+dimension[1]*256 # extra width height from the first pixel
            clientH = dimension[2]+dimension[3]*256 # extra width height from the first pixel        
            buffer = (ctypes.c_ubyte*4*clientW*clientH).from_address(addr)                    
            bitmap = numpy.frombuffer(buffer, dtype=numpy.uint32)
            print(clientW, clientH)

    running = 1 
    #pyglet.app.run()
    cap.destroy()
    
