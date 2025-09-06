import os
import threading
import time
import queue
import numpy
from Xlib import X, display

import ctypes
LibName = '../nvfbc/nvfbc.so'
AbsLibPath = os.path.dirname(os.path.abspath(__file__)) + os.path.sep + LibName
cap = ctypes.CDLL(AbsLibPath)

cap.init.argtypes = (ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_int)
cap.init.restype = ctypes.c_int
cap.capture.argtypes = (ctypes.c_int,)
cap.capture.restype = ctypes.c_void_p # without this, 64 bit address got truncated to 32 bit (ctypes default action) => segmentation fault 
cap.destroy.argtypes = None
cap.destroy.restype = ctypes.c_int

time_capture = 0 # loop time in ms
copy_queue = queue.Queue(maxsize=1) # flag for capture thread control

running = 1 # thread shutdown signal
bitmap = None
buffer = None
def capture_worker(capture_queue, x ,y , clientW, clientH, handle):
    global time_capture, bitmap, buffer
    # cbuffer = (ctypes.c_ubyte*clientW*clientH*4)()
    cap.init(x, y, clientW, clientH, handle)

    count = 0 # loop count
    while running:                                            
        if(capture_queue.qsize() == 1):
            time.sleep(1.0/60) 
            continue
        t = time.perf_counter()                                                                        
        addr = cap.capture(1)        
        buffer = (ctypes.c_ubyte*4*clientW*clientH).from_address(addr)                    
        bitmap = numpy.frombuffer(buffer, dtype=numpy.uint32)
        # bitmap = numpy.ctypeslib.as_array(buffer)
                        
        time_capture = (time.perf_counter() - t)*1000
        if not running: break
        capture_queue.put(1) # blocking
        count+=1 # print(count)
    print("capture_worker() ended.")
        
if __name__ == "__main__":
    # import CLI_MENU # local file
    # handle, clientW, clientH, windowW, windowH = CLI_MENU.get_window_handle(2)

    disp = display.Display()
    root = disp.screen().root
    active_window_atom = disp.intern_atom('_NET_ACTIVE_WINDOW') # use current active window as capture source, i.e. terminal   
    window_id_prop = root.get_full_property(active_window_atom, X.AnyPropertyType)        
    handle = window_id_prop.value[0]
   
    window = disp.create_resource_object('window', handle)
    geometry = window.get_geometry()    
    clientW = geometry.width
    clientH = geometry.height
    position = geometry.root.translate_coords(window, 0, 0)
    print(handle, position.x, position.y, clientW, clientH)

    capture_queue = queue.Queue(maxsize=1)
    capture_thread = threading.Thread(target=capture_worker, args=(capture_queue, position.x, position.y, clientW, clientH, handle))

    print("Source window needs to have screen changes to trigger incoming capture frames.")
    capture_thread.start()
            
    for i in range(3):
        capture_queue.get()
        #capture_queue.task_done()    
        time.sleep(1)

    cap.destroy()    
    running = 0 # trigger exit signal
    capture_thread.join()
    print('END')
