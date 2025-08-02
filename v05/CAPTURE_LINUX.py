import os
import threading
import time
import queue

import Xlib 
import Xlib.display
from Xlib import X
import ctypes
LibName = 'captureRGBX.so'
AbsLibPath = os.path.dirname(os.path.abspath(__file__)) + os.path.sep + LibName
cap = ctypes.CDLL(AbsLibPath)

time_capture = 0 # loop time in ms
copy_queue = queue.Queue(maxsize=1) # bitmap copy from GPU to CPU callback data queue

running = 1 # thread shutdown signal
def capture_worker(capture_queue, handle, clientW, clientH, windowW, windowH):
    global time_capture
    cbuffer = (ctypes.c_ubyte*clientW*clientH*4)()
    
    count = 0 # loop count
    while running:                                    
        t = time.perf_counter()                                                                
        cap.captureRGBX(0, 0, clientW, clientH, handle, cbuffer) # window must NOT be minimized, uncatchable err            
        if running: capture_queue.put(cbuffer)        
        time_capture = (time.perf_counter() - t)*1000
        count+=1
        # print(count)
        
if __name__ == "__main__":
    import CLI_MENU # local file
    handle, clientW, clientH, windowW, windowH = CLI_MENU.get_window_handle(2)

    capture_queue = queue.Queue(maxsize=1)
    capture_thread = threading.Thread(target=capture_worker, args=(capture_queue, handle, clientW, clientH, windowW, windowH))

    print("Source window needs to have screen changes to trigger incoming capture frames.")
    capture_thread.start()
            
    for i in range(3):
        capture_queue.get()
        capture_queue.task_done()    
        time.sleep(1)
    
    running = 0 # trigger exit signal
    capture_thread.join()
    
    print('END')
