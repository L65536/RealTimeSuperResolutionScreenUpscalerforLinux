# Requirements: pip install compushady pillow numpy pygame
# Requirements: [Linux] pip install xlib
# Requirements: [Linux] libvulkan-dev and libx11-dev on Debian etc
import time
import threading
lock = threading.Lock()    
import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
import pygame
pygame.init()
pygame.font.init()
font = pygame.font.SysFont('arial', 36)
clock = pygame.time.Clock()
running = True
capture_time = 0
count = 0
    
import LIBSHADER_SRCNN as SRCNN # local lib
import ctypes
import Xlib 
import Xlib.display
from Xlib import X
LibName = 'captureRGBX.so'
AbsLibPath = os.path.dirname(os.path.abspath(__file__)) + os.path.sep + LibName
cap = ctypes.CDLL(AbsLibPath)

if True:
    windows = []
    disp = Xlib.display.Display()
    try:
        disp_root = disp.screen().root
        windowIDs = disp_root.get_full_property(disp.intern_atom('_NET_CLIENT_LIST'), X.AnyPropertyType).value
        for windowID in windowIDs:
            window = disp.create_resource_object('window', windowID)
            wproperty = window.get_full_property(disp.intern_atom('_NET_WM_NAME'), 0)
            geometry = window.get_geometry()
            title = wproperty.value.decode('utf-8') #.lower()
             
            windows.append({"id":windowID, "width":geometry.width, "height":geometry.height, "title":title, "accessible": 0})
            print(f"{len(windows)} {windowID} ({geometry.width:<4} x {geometry.height:<4}) {title}")
    finally:
        disp.close()
        
while True:
    try:
        selection = input("\nSelect a window to capture: ")        
        selected_item = windows[int(selection) - 1]['id']
        clientW = windows[int(selection) - 1]['width']
        clientH = windows[int(selection) - 1]['height']
        break
    except:
        pass

w = clientW
h = clientH   
display = pygame.display.set_mode((clientW*2, clientH*2))
# print(selected_item.size.width, selected_item.size.height, clientW, clientH)
cap.captureRGBX.argtypes = []
cbuffer = (ctypes.c_ubyte*clientW*clientH*4)()
    
first_run = 1
postp_time = 0
shader_time = 0
def show():
    global first_run, offsetX, offsetY
    global shader_time, postp_time
    global lock
    lock.acquire()
    
    w = clientW
    h = clientH    
    time_shader = time.perf_counter()
    if first_run: 
        first_run = 0
        SRCNN.init_buffer(w, h)
        # offsetX, offsetY = calculate_client_offset(w, h)        
    SRCNN.compute(cbuffer, w, h)
    if not running: return
    
    time_postp = time.perf_counter()
    surface = pygame.image.frombuffer(SRCNN.readback_buffer.readback(), (SRCNN.OUTPUT.row_pitch//4, SRCNN.OUTPUT.height), "RGBX") # BGRX is 3x slower in linux???                
    string1 = " [ESC][SPACE] Exit "
    string2 = " " +str(count)+" "+str(clientW)+"x"+str(clientH)+" "+str(int(capture_time))+"/"+str(int(shader_time))+"+"+str(int(postp_time))+" ms (CAP/GPU+POSTP) "
    osd1 = font.render(string1, False, (255, 255, 255),(0,0,0))    
    osd2 = font.render(string2, False, (255, 255, 255),(0,0,0))    
    
    # display.blit(surface, (-offsetX*2, -offsetY*2))    
    display.blit(surface, (0, 0))    
    display.blit(osd2, (36, 36))
    display.blit(osd1, (36, 108))

    postp_time = (time.perf_counter() - time_postp)*1000
    shader_time = (time_postp - time_shader)*1000
       
    lock.release()
    
while running:
    events = pygame.event.get()
    for event in events:
        if event.type == pygame.QUIT: running = False
        if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE: running = False
                elif event.key == pygame.K_SPACE: running = False
                                
    if True:
        if not lock.locked(): # check if worker thread is busy
            pygame.display.flip()
            
            time_capture = time.perf_counter()            
            cap.captureRGBX(0, 0, w, h, selected_item, cbuffer) # window must not be minimized, uncatchable err            
            capture_time = (time.perf_counter() - time_capture)*1000
    
            ttt = threading.Thread(target=show) 
            ttt.start()                
            count+=1
                        
    clock.tick(120)        
pygame.display.quit()    
pygame.quit()
print('End')
