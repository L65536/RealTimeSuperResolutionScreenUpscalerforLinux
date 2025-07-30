# pip install -r requirements.txt
import time
import threading
lock = threading.Lock()    
from ctypes import windll
windll.user32.SetProcessDPIAware() # HiDPI support
import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
import pygame
pygame.init()
pygame.font.init()
font = pygame.font.SysFont('arialblack', 36)
clock = pygame.time.Clock()
running = True
count = 0
    
from winrt.windows.ui.windowmanagement import WindowServices
from winrt.windows.graphics.capture import (GraphicsCaptureItem, Direct3D11CaptureFramePool,)
from winrt.windows.graphics.directx import DirectXPixelFormat
from winrt.windows.graphics.directx.direct3d11.interop import (create_direct3d11_device_from_dxgi_device,)
from winrt.windows.graphics.imaging import BitmapEncoder, SoftwareBitmap, BitmapBufferAccessMode
from d3d11 import D3D_DRIVER_TYPE, D3D11_CREATE_DEVICE_FLAG, D3D11CreateDevice # local file

import LIBSHADER_SRCNN as SRCNN # local lib
from win32gui import GetClientRect            
            
capture_items: list[GraphicsCaptureItem] = []
client_area = []
for win_id in WindowServices.find_all_top_level_window_ids():
    item = GraphicsCaptureItem.try_create_from_window_id(win_id)    
    left, top, right, bottom = GetClientRect(win_id.value)
    if item is None: continue
    capture_items.append(item)
    client_area.append((right, bottom))
    print(f"{len(capture_items)} [{item.size.width}x{item.size.height}] {item.display_name}")

while True:
    try:
        selection = input("\nSelect a window to capture: ")        
        selected_item = capture_items[int(selection) - 1]
        clientW, clientH = client_area[int(selection) - 1]
        break
    except:
        pass
display = pygame.display.set_mode((clientW*2, clientH*2))
print(selected_item.size.width, selected_item.size.height, clientW, clientH)

def calculate_client_offset(w, h):
    boarder=(w-clientW)//2
    top=h-clientH-boarder
    # print(boarder,top)
    return boarder, top
    
first_run = 1
postp_time = 0
shader_time = 0
def show(op, status):
    global first_run, offsetX, offsetY
    global shader_time, postp_time
    lock.acquire()
    
    bitmap = op.get_results()
    w = bitmap.pixel_width
    h = bitmap.pixel_height
    buffer = bitmap.lock_buffer(BitmapBufferAccessMode.READ)
    mv = memoryview(buffer.create_reference())
    
    time_shader = time.perf_counter()
    if first_run: 
        first_run = 0
        SRCNN.init_buffer(w, h)
        offsetX, offsetY = calculate_client_offset(w, h)        
    SRCNN.compute(mv, w, h)
    if not running: return
    
    time_postp = time.perf_counter()
    surface = pygame.image.frombuffer(SRCNN.readback_buffer.readback(), (SRCNN.OUTPUT.row_pitch//4, SRCNN.OUTPUT.height), "BGRA")                
    string1 = " [ESC][SPACE] Exit "
    string2 = " " +str(count)+" "+str(clientW)+"x"+str(clientH)+" "+str(int(shader_time))+"+"+str(int(postp_time))+" ms (GPU+POSTP) "
    osd1 = font.render(string1, False, (255, 255, 255),(0,0,0))    
    osd2 = font.render(string2, False, (255, 255, 255),(0,0,0))    
    
    display.blit(surface, (-offsetX*2, -offsetY*2))    
    display.blit(osd2, (36, 36))
    display.blit(osd1, (36, 108))
    postp_time = (time.perf_counter() - time_postp)*1000
    shader_time = (time_postp - time_shader)*1000
    
    op.close()
    lock.release()
    
if True:
    dxgi, _, context = D3D11CreateDevice(DriverType=D3D_DRIVER_TYPE.HARDWARE, Flags=D3D11_CREATE_DEVICE_FLAG.BGRA_SUPPORT,)
    device = create_direct3d11_device_from_dxgi_device(dxgi.value)
    frame_pool = Direct3D11CaptureFramePool.create_free_threaded(device, DirectXPixelFormat.B8_G8_R8_A8_UINT_NORMALIZED, 1, selected_item.size,)
    session = frame_pool.create_capture_session(selected_item)
    session.include_secondary_windows = True
    session.is_border_required = True
    session.is_cursor_capture_enabled = True
    session.start_capture()

    while running:
        event = pygame.event.poll()
        if event.type == pygame.QUIT: running = False
        if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE: running = False
                elif event.key == pygame.K_SPACE: running = False
                
        frame = frame_pool.try_get_next_frame()
        if frame is not None:
            if not lock.locked(): # check if worker thread is busy
                op = SoftwareBitmap.create_copy_from_surface_async(frame.surface)
                op.completed = show
                count+=1
                
        pygame.display.flip()
        clock.tick(30)
        
    session.close() 
    frame_pool.close()
    device.close()
    pygame.display.quit()    
pygame.quit()
print('End')