# Known issues: duplicate cursor[], cursor out of bound[], slow cropping[fixed]
# Known issues: Capture/D3D11CreateDevice clean up, out of memory if restarts repeatedly

# pip install compushady pywin32 keyboard
# pip install -r requirements.txt # for winrt

# import platform
import numpy
import queue
import time
import threading
from compushady import Swapchain
from compushady.formats import R8G8B8A8_UNORM

#if platform.system() == 'Windows':
import win32api, win32con, win32gui # pip install pywin32
import keyboard
import ctypes
ctypes.windll.user32.SetProcessDPIAware() # HiDPI support
from winrt.windows.ui import WindowId
from winrt.windows.ui.windowmanagement import WindowServices
from winrt.windows.graphics.capture import GraphicsCaptureItem
from winrt.windows.graphics.imaging import SoftwareBitmap, BitmapBufferAccessMode
import LIBSHADER_SRCNN3 as SR # local library
import CAPTURE_WINDOWS as CAP # local library

class MyWindow:
    def __init__(self):
        global wc_registered
        win32gui.InitCommonControls()
        self.hinst = win32api.GetModuleHandle(None)
        message_map = {win32con.WM_DESTROY: self.OnDestroy,}
        className = 'MyWndClass'
        wc = win32gui.WNDCLASS()
        wc.style = win32con.CS_HREDRAW | win32con.CS_VREDRAW
        wc.lpfnWndProc = message_map
        wc.lpszClassName = className
        self.class_atom = win32gui.RegisterClass(wc)

        # CreateWindowEx(dwExStyle, className , windowTitle , style , x , y , width , height , parent , menu , hinstance , reserved )
        ex_style = win32con.WS_EX_TOPMOST | win32con.WS_EX_TRANSPARENT | win32con.WS_EX_LAYERED | win32con.WS_EX_TOOLWINDOW | win32con.WS_EX_NOACTIVATE
        style = win32con.WS_POPUP | win32con.WS_MAXIMIZE
        self.hwnd = win32gui.CreateWindowEx(
            ex_style, className, 'RTSR', style,
            win32con.CW_USEDEFAULT, win32con.CW_USEDEFAULT,
            1280*2, 800*2, # size does not matter for full screen overlay
            0, 0, self.hinst, None)
        win32gui.UpdateWindow(self.hwnd)
        win32gui.ShowWindow(self.hwnd, win32con.SW_SHOW)

    def OnDestroy(self, hwnd, message, wparam, lparam):
        win32gui.PostQuitMessage(0)
        return True

def hotkey(): # when "TAB" key is pressed: #1 get current window handle for upscale #2 Exit loop
    global handle, running
    if not first_run:
        running = 0
        return
    handle = win32gui.GetForegroundWindow()

def calculate_client_offset(w, h):
    boarder=(w-clientW)//2
    top=h-clientH-boarder
    return boarder, top

# Main worker loop
def compute_worker():
    global first_run, offsetX, offsetY
    global count, total_time_compute

    while running:
        bitmap = capture_queue.get() # blocking
        
        if first_run:
            first_run = 0
            offsetX, offsetY = calculate_client_offset(bitmap.pixel_width, bitmap.pixel_height)
            SR.init_buffer(windowW, windowH-offsetY) # crop title bar only
            #if cropping: SR.init_buffer(clientW, clientH)
            #else: SR.init_buffer(windowW, windowH)

        #if platform.system() == 'Windows':
        buffer = bitmap.lock_buffer(BitmapBufferAccessMode.READ)
        if cropping: 
            mv = memoryview(buffer.create_reference())[offsetY*windowW*4:] # crop title bar only # slack/lazy cropping             
            #np_window = numpy.frombuffer(buffer.create_reference(), dtype=numpy.uint32) # CPU time expensive cropping with numpy
            #np_client = np_window.reshape(bitmap.pixel_height, bitmap.pixel_width)[offsetY:offsetY+clientH, offsetX:offsetX+clientW]
            #mv = np_client.tobytes()
        else:
            mv = memoryview(buffer.create_reference())

        t = time.perf_counter()
        SR.upload(mv)
        SR.compute()
        total_time_compute += time.perf_counter() - t
        count += 1
        swapchain.present(SR.OUTPUT) # Display
    win32gui.PostMessage(w.hwnd, win32con.WM_CLOSE, 0, 0)

# Main menu loop
cropping = 1 # crop client window area with numpy for windows, CPU time expensive
width = win32api.GetSystemMetrics(0)
height = win32api.GetSystemMetrics(1)
print("Real Time Super Resolution Upscaler")
print(f"Screen resolution: {width}x{height}")
print("[TAB] key to Start/Stop upscaling current active window.\n")

while True:
    capture_queue = queue.Queue(maxsize=1)
    total_time_compute = 0
    count = 0 # Total frame count
    first_run = 1 # first run flag
    running = 1 # main loop exit flag
    handle = None # window and capture handle

    keyboard.add_hotkey('tab', hotkey)
    while handle is None: time.sleep(1)

    _, _, clientW, clientH = win32gui.GetClientRect(handle)
    handle = GraphicsCaptureItem.try_create_from_window_id(WindowId(handle)) # convert window handle to GraphicsCaptureItem handle
    title = handle.display_name
    windowW, windowH = handle.size.width, handle.size.height
    print(f"Source = [{clientW}x{clientH}][{windowW}x{windowH}] {title}")

    w = MyWindow()
    swapchain = Swapchain(w.hwnd, R8G8B8A8_UNORM, 3)

    CAP.running = 1
    capture_thread = threading.Thread(target=CAP.capture_worker, args=(capture_queue, handle, clientW, clientH, windowW, windowH))
    capture_thread.start()
    compute_thread = threading.Thread(target=compute_worker, args=())
    compute_thread.start()

    win32gui.PumpMessages() # Message Loop
    win32gui.UnregisterClass(w.class_atom, None)
    SR.clear_buffer()
    del w
    CAP.running = 0 # terminating worker thread loop
    swapchain = None
    print(f'Total frames = {count}, average compute time/frame = {(total_time_compute/count)*1000:.2f} (ms)\n')    
    # average time including CPU/GPU upload, excluding cropping

"""
TODO: try pyside6 and transparence
TODO: duplicate cursor, cursor out of bound
TODO: avoid repeat new capture/D3D11CreateDevice, use frame_pool/Recreates for source resolution change
[] Recreate(IDirect3DDevice, DirectXPixelFormat, Int32, SizeInt32) https://learn.microsoft.com/en-us/uwp/api/windows.graphics.capture.direct3d11captureframepool?view=winrt-26100

TODO: Upload/Cropping speed up
[v] slack/lazy cropping => crop title bar only, since windows11 boarders are very thin
[x] modify compushady/upload2d to copy from ID3D11Texture2D/3D directly
[x] modify compushady/upload2d to implement offset/stride for cropping
[x] use CopySubresourceRegion((ID3D11Texture2D)) then download/upload
"""