import threading
import time
import queue

from winrt.windows.graphics.capture import (GraphicsCaptureItem, Direct3D11CaptureFramePool,)
from winrt.windows.graphics.directx import DirectXPixelFormat
from winrt.windows.graphics.directx.direct3d11.interop import (create_direct3d11_device_from_dxgi_device,)
from winrt.windows.graphics.imaging import BitmapEncoder, SoftwareBitmap, BitmapBufferAccessMode

# local file
from d3d11 import D3D_DRIVER_TYPE, D3D11_CREATE_DEVICE_FLAG, D3D11CreateDevice

running = 1 # thread shutdown signal
time_capture = 0 # loop time in ms
copy_queue = queue.Queue(maxsize=1) # bitmap copy from GPU to CPU callback data queue

def copy_completed(op, status):
    copy_queue.put(op.get_results())
    op.close()

def capture_worker(capture_queue, handle, clientW, clientH, windowW, windowH):
    dxgi, _, context = D3D11CreateDevice(DriverType=D3D_DRIVER_TYPE.HARDWARE, Flags=D3D11_CREATE_DEVICE_FLAG.BGRA_SUPPORT,)
    device = create_direct3d11_device_from_dxgi_device(dxgi.value)
    frame_pool = Direct3D11CaptureFramePool.create_free_threaded(device, DirectXPixelFormat.R8_G8_B8_A8_UINT_NORMALIZED, 1, handle.size,)
    session = frame_pool.create_capture_session(handle)
    session.include_secondary_windows = True
    session.is_border_required = True    
    session.is_cursor_capture_enabled = True # False
    session.start_capture()
    global time_capture

    count = 0 # loop count
    while running:
        if capture_queue.qsize() == 0:
            frame = frame_pool.try_get_next_frame()
            if frame is not None:
                t = time.perf_counter()
                op = SoftwareBitmap.create_copy_from_surface_async(frame.surface)
                op.completed = copy_completed
                # Windows message loop conflict if using .get() or .get_results() here
                # Traceback: Cannot call blocking method from single-threaded apartment.                
                
                if running: bitmap = copy_queue.get() # blocking
                if running: capture_queue.put(bitmap) # blocking
                                
                count+=1
                time_capture = (time.perf_counter() - t)*1000
                
                if False: # DEBUG 
                    w = bitmap.pixel_width
                    h = bitmap.pixel_height
                    print(count, time_capture, w, h)
        else:
            time.sleep(1/60)
    session.close()
    frame_pool.close()
    device.close()
    del device
    del frame_pool
    del session
    del dxgi
    del context

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
