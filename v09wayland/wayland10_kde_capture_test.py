# Test KDE/Plasma(wayland) and NVFBC_BACKEND_PIPEWIRE capture backend with virtual monitor
# Run this program, KDE/Plasma will display a "Screen sharing" dialog for all possible capture targets, choose "New virtual outout"
# By default(assumption), the virtual monitor has resolution of 1920x1080 and located to the right of current monitor.
# Virtual monitor details can be checked/changed at KDE monitor configuration page.
# You can move any target program to the monitor:
    #1 by dragging to the right or
    #2 right click menu on titlebar, choose "Move to screen" ...

import threading
import time
import queue
import numpy
import os
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

running = True
capture_queue = queue.Queue(maxsize=1) # [capture worker] capture control
capture_thread = threading.Thread(target=capture_worker, args=[])
capture_thread.start()
# Unable to bind EGL context => put capture and display on different threads, init capture first, pygame latter

import pygame
pygame.init()
screen = pygame.display.set_mode((1920, 1080))
pygame.display.set_caption("KDE Plasma Virtual screen test with NVFBC_BACKEND_PIPEWIRE capture")
clock = pygame.time.Clock()

string = 'KDE/Plasma will display a "Screen sharing" dialog.\nChoose "New virtual outout".\nThe new virtual screen is located to the right.\nAny target window can be dragged or send there.'
pygame.font.init()
font = pygame.font.SysFont('Arial', 50)
text_surface = font.render(string, True, (255, 255, 255))
screen.blit(text_surface, (100,100))
pygame.display.flip()

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT: running = False

    if(capture_queue.qsize() == 1):
        surface = pygame.image.frombuffer(buffer, (w, h), 'BGRA')
        screen.blit(surface, (0, 0))
        pygame.display.flip()
        capture_queue.get() # [effecitively non-blocking] ready to get another frame

    clock.tick(30)
pygame.quit()


