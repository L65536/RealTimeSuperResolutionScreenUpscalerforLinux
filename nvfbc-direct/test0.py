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

count = 0
for p in psutil.process_iter():
    if 'vkcube' in p.name():
        print(p) 

        cap.init(p.pid)        
        while count < 20:
            count += 1                                                                                                                            
            addr = cap.capture(1)
            dimension = (ctypes.c_ubyte*4).from_address(addr)            
            clientW = dimension[0]+dimension[1]*256 # extra width height from the first pixel
            clientH = dimension[2]+dimension[3]*256 # extra width height from the first pixel        
            buffer = (ctypes.c_ubyte*4*clientW*clientH).from_address(addr)                    
            bitmap = numpy.frombuffer(buffer, dtype=numpy.uint32)
            print(clientW, clientH)
        cap.destroy()
if not count: print("vkcube not running.")           