# Experimental version for Windows with pygame instead of tkinter to speed up display
# Known issues:
# Works with certain window resolution only. eg. 3840x 1920x 1280x but errors with random resolution => trim or pad to block size (too heavy to implement in python)
# Capturing causes the original window and captured images flickering??? try different parameter or new capture method

# Requirements: pip install compushady pillow numpy xlib
# Requirements: libvulkan-dev and libx11-dev on Debian Linux
from PIL import Image, ImageTk, ImageDraw
import numpy as np

import struct
import time
import os

if os.name == 'nt':
    import win32gui # pip install pywin32
    import win32ui
    from win32.win32gui import FindWindow, GetWindowRect, GetForegroundWindow, GetWindowText
    from ctypes import windll
    windll.user32.SetProcessDPIAware()
else:
    import Xlib # capture and window location
    import Xlib.display
    from Xlib import X

from compushady import (
    Compute, Buffer, Texture2D, HEAP_UPLOAD, HEAP_READBACK,
    Sampler, SAMPLER_FILTER_POINT, SAMPLER_FILTER_LINEAR, SAMPLER_ADDRESS_MODE_CLAMP, SAMPLER_ADDRESS_MODE_WRAP, SAMPLER_ADDRESS_MODE_MIRROR,
    )
from compushady.formats import R8G8B8A8_UNORM
from compushady.shaders import hlsl

import pygame
pygame.init()
clock = pygame.time.Clock()
running = True

DEBUG = 1 # enable/disable DEBUG messages
OSD = 1 # OSD info panel enable/disable
OSD_FONT = 'Helvetica 36 bold'

windows = [] # dict of window properties, {"id":windowID, "width":geometry.width, "height":geometry.height, "title":title, "accessible", 0}
winID = 0 # target window ID
winH = 0 # target window height
winW = 0 # target window width
menu_select_mode = 1 # run once flag

def enumerate_windows_property_linux(): # enum window ID width height title into windows=[{dict}]
    # global windows
    display = Xlib.display.Display()
    try:
        display_root = display.screen().root
        windowIDs = display_root.get_full_property(display.intern_atom('_NET_CLIENT_LIST'), X.AnyPropertyType).value
        for windowID in windowIDs:
            window = display.create_resource_object('window', windowID)
            wproperty = window.get_full_property(display.intern_atom('_NET_WM_NAME'), 0)
            geometry = window.get_geometry()
            title = wproperty.value.decode('utf-8') #.lower()
            title_words = title.split()
            if title_words: title = title_words[-1]
            if 'RTSR' in title: continue # skip self
            if 'Desktop' in title: continue # skip
            if 'panel' in title: continue # skip
            # if DEBUG: print(f"{windowID} ({geometry.width:<4} x {geometry.height:<4}) {title}")
            windows.append({"id":windowID, "width":geometry.width, "height":geometry.height, "title":title, "accessible": 0})
    finally:
        display.close()

def enumerate_windows_property_windows(): # Retrieves a list of all visible top-level window handles.
    global windows
    windows = []
    window_handles = []
    def enum_windows_callback(hwnd, lParam): # Callback function for EnumWindows. Appends visible window handles to the list.
        if win32gui.IsWindowVisible(hwnd): window_handles.append(hwnd)
        return True  # Continue enumeration
    win32gui.EnumWindows(enum_windows_callback, None)

    for handle in window_handles:
        try:
            title = win32gui.GetWindowText(handle)
            left, top, right, bottom = win32gui.GetClientRect(handle)
            w = right - left
            h = bottom - top
            if w<60 or h<60: # ignore minimized window 
                print(f"Skip minimized or inaccessible windows: [{handle:<8}]({w} x {h})'{title}'")
                continue            
            # if w==3840: continue # ignore full screen windows
            if title:  # Only print handles with a visible title
                title_words = title.split()
                if title_words: title = title_words[-1] # trim title string to the last word
                # print(f"[{handle:<8}]({w:<4} x {h:<4})'{title}'") # print(w, h, "=", left, top, right, bottom)
                windows.append({"id":handle, "width":w, "height":h, "title":title, "accessible": 0})            
        except Exception as e:
            print(f"Could not get title for handle {handle}: {e}")
    
    for i in range(len(windows)):
        print(f"[{windows[i]['id']:<8}]({windows[i]['width']:<4} x {windows[i]['height']:<4})'{windows[i]['title']}'") 
    print()

###############################################################################################################
menu_tile = [] # menu selector thumbnail tiles (PIL image)
def start_menu_windows():
    global tile_size
    enumerate_windows_property_windows()      
    
    row = len(windows) # number of active windows
    tile_size = 3840 // row # dynamic adjust tile size to fit all windows in one row
    display = pygame.display.set_mode((3840, tile_size))
    display.fill((0,0,0))
    
    for i in range(row): display.blit(make_thumbnail_tile_windows(i, tile_size), (i*tile_size, 0))
    # if DEBUG: print(f"[{i}] {windows[i]["id"]} {windows[i]["width"]:<4} x {windows[i]["height"]:<4} {windows[i]["title"]}")
        
def make_thumbnail_tile_windows(i, tile_size):
    global winH, winW
    image = None
    FONT_SIZE = 70*tile_size//600
    win_id = windows[i]["id"]
    winH = windows[i]["height"]
    winW = windows[i]["width"]

    try: # capture crop and pad to thumbnail tile size
    #if True:
        capture_windows_init(win_id)
        buffer, width, height = capture_windows()
        # print(win_id,width,height)
        surface = pygame.image.frombuffer(buffer, (width,height), "BGRA")
        image = surface.subsurface((0,0,tile_size,tile_size))
        windows[i]["accessible"] = 1
        capture_windows_release()
    #if False:
    except: # create blank image (plain blue) tile if capture failed
        image = pygame.Surface((tile_size, tile_size))
        image.fill((0,0,255))
        if DEBUG: print("[DEBUG] Blue thumbnail used for minimized windows.")

    # Decorate thumbnail tiles with rect and info
    pygame.draw.rect(image,(255,255,255),(5,5,tile_size-5,tile_size-5),1)
    string1 = " "+windows[i]["title"]
    string2 = " "+str(width)+" x "+str(height)
    string3 = " Minimized? " # Inaccessible
    text1 = font.render(string1, False, (255, 0, 0))
    text2 = font.render(string2, False, (255, 0, 0))
    text3 = font.render(string3, False, (255, 0, 0))
    image.blit(text1, (5,tile_size-100*tile_size//600))
    image.blit(text2, (5,tile_size-200*tile_size//600))
    if not windows[i]["accessible"]: image.blit(text3, (5,tile_size-300*tile_size//600))    
    return image

def init_shader():
    global SP, SL, s1, s2, s3, s4

    SP = Sampler(
            filter_min=SAMPLER_FILTER_POINT,
            filter_mag=SAMPLER_FILTER_POINT,
            address_mode_u=SAMPLER_ADDRESS_MODE_WRAP,
            address_mode_v=SAMPLER_ADDRESS_MODE_CLAMP,
            address_mode_w=SAMPLER_ADDRESS_MODE_CLAMP,
    )
    SL = Sampler(
            filter_min=SAMPLER_FILTER_LINEAR,
            filter_mag=SAMPLER_FILTER_LINEAR,
            address_mode_u=SAMPLER_ADDRESS_MODE_WRAP,
            address_mode_v=SAMPLER_ADDRESS_MODE_CLAMP,
            address_mode_w=SAMPLER_ADDRESS_MODE_CLAMP,
    )
    with open("CuNNy-veryfast-NVL_Pass1.hlsl", 'r') as fp: shader1 = fp.read()
    with open("CuNNy-veryfast-NVL_Pass2.hlsl", 'r') as fp: shader2 = fp.read()
    with open("CuNNy-veryfast-NVL_Pass3.hlsl", 'r') as fp: shader3 = fp.read()
    with open("CuNNy-veryfast-NVL_Pass4.hlsl", 'r') as fp: shader4 = fp.read()
    s1 = hlsl.compile(shader1)
    s2 = hlsl.compile(shader2)
    s3 = hlsl.compile(shader3)
    s4 = hlsl.compile(shader4)

def init_buffer():
    global staging_buffer, readback_buffer
    global INPUT, OUTPUT, T0, T1, T2, T3, CB1, CB2, CB3, CB4
    global winH, winW

    BLOCK_SIZE = 64 # trim to block size, capture in this solution too
    height = winH
    width = winW
    # winW = (width-BLOCK_SIZE+1)//BLOCK_SIZE*BLOCK_SIZE
    # winH = (height-BLOCK_SIZE+1)//BLOCK_SIZE*BLOCK_SIZE
    # print("Trimmed",width,height,"to", winW,winH)
    
    INPUT = Texture2D(width, height, R8G8B8A8_UNORM)
    OUTPUT = Texture2D(width*2, height*2, R8G8B8A8_UNORM)
    staging_buffer = Buffer(INPUT.size, HEAP_UPLOAD)
    readback_buffer = Buffer(OUTPUT.size, HEAP_READBACK)
    T0 = Texture2D(width, height, R8G8B8A8_UNORM)
    T1 = Texture2D(width, height, R8G8B8A8_UNORM)
    T2 = Texture2D(width, height, R8G8B8A8_UNORM)
    T3 = Texture2D(width, height, R8G8B8A8_UNORM)
    CB1 = Buffer(40, HEAP_UPLOAD)
    CB2 = Buffer(40, HEAP_UPLOAD)
    CB3 = Buffer(40, HEAP_UPLOAD)
    CB4 = Buffer(40, HEAP_UPLOAD)
    CB1.upload(struct.pack('iiiiffffff', width, height, width, height, 1.0/width, 1.0/height, 1.0/width, 1.0/height, 1.0, 1.0))
    CB2.upload(struct.pack('iiiiffffff', width, height, width, height, 1.0/width, 1.0/height, 1.0/width, 1.0/height, 1.0, 1.0))
    CB3.upload(struct.pack('iiiiffffff', width, height, width, height, 1.0/width, 1.0/height, 1.0/width, 1.0/height, 1.0, 1.0))
    CB4.upload(struct.pack('iiiiffffff', width, height, width*2, height*2, 1.0/width, 1.0/height, 1.0/width/2, 1.0/height/2, 2.0, 2.0))

def capture_windows():
    global WIN_HANDLES
    (hwnd, hwnd_dc, mfc_dc, save_dc, bitmap) = WIN_HANDLES
    save_dc.SelectObject(bitmap)
    result = windll.user32.PrintWindow(hwnd, save_dc.GetSafeHdc(), 3)
    if result != 1: raise RuntimeError(f"Unable to acquire screenshot! Result: {result}")

    bmpinfo = bitmap.GetInfo()
    bmpstr = bitmap.GetBitmapBits(True)
    return bmpstr, bmpinfo["bmWidth"], bmpinfo["bmHeight"]

def capture_windows_init(hwnd): # create capture handles only once
    global WIN_HANDLES
    windll.user32.SetProcessDPIAware()
    left, top, right, bottom = win32gui.GetClientRect(hwnd)
    w = winW # w = right - left # use trimmed/padded sizes for shaders
    h = winH # h = bottom - top  # use trimmed/padded sizes for shaders
    hwnd_dc = win32gui.GetWindowDC(hwnd)
    mfc_dc = win32ui.CreateDCFromHandle(hwnd_dc)
    save_dc = mfc_dc.CreateCompatibleDC()
    bitmap = win32ui.CreateBitmap()
    bitmap.CreateCompatibleBitmap(mfc_dc, w, h)
    WIN_HANDLES = (hwnd, hwnd_dc, mfc_dc, save_dc, bitmap)

def capture_windows_release():
    global WIN_HANDLES
    (hwnd, hwnd_dc, mfc_dc, save_dc, bitmap) = WIN_HANDLES
    win32gui.DeleteObject(bitmap.GetHandle())
    save_dc.DeleteDC()
    mfc_dc.DeleteDC()
    win32gui.ReleaseDC(hwnd, hwnd_dc)
    WIN_HANDLES = None

def capture_upscale_display_windows():
    if True: #try:
        ###############################################################################################################
        time_capture = time.perf_counter()
        capture_windows()
        buffer,width,height = capture_windows()
        # print("captured",width,height)
        # surface = pygame.image.frombuffer(buffer, (width,height), "BGRA")
        ###############################################################################################################
        time_shader = time.perf_counter() # process_time() is for CPU ONLY
        staging_buffer.upload(buffer)
        staging_buffer.copy_to(INPUT)
        compute1 = Compute(s1, cbv=[CB1], srv=[INPUT], uav=[T0,T1], samplers=[SP,SL])
        compute1.dispatch((width+7)//8, (height+7)//8, 1)
        compute2 = Compute(s2, cbv=[CB2], srv=[T0,T1], uav=[T2,T3], samplers=[SP,SL])
        compute2.dispatch((width+7)//8, (height+7)//8, 1)
        compute3 = Compute(s3, cbv=[CB3], srv=[T2,T3], uav=[T0], samplers=[SP,SL])
        compute3.dispatch((width+7)//8, (height+7)//8, 1)
        compute4 = Compute(s4, cbv=[CB4], srv=[INPUT,T0], uav=[OUTPUT], samplers=[SP,SL])
        compute4.dispatch((width*2+15)//16, (height*2+15)//16, 1) # (OUPUT_size+block_size-1)//block_size
        OUTPUT.copy_to(readback_buffer)
        ###############################################################################################################
        time_postp = time.perf_counter() # process_time() is for CPU ONLY        
        # print(len(readback_buffer.readback()),"read,",OUTPUT.width*OUTPUT.height*4,"=",OUTPUT.width,"x",OUTPUT.height)        
        surface = pygame.image.frombuffer(readback_buffer.readback(), (OUTPUT.width, OUTPUT.height), "BGRA")
        display.blit(surface, (0, 0))
        
        if OSD: # display OSD info panel
            postp_time = (time.perf_counter() - time_postp)*1000
            shader_time = (time_postp - time_shader)*1000
            capture_time = (time_shader - time_capture)*1000
            string = " "+str(width)+"x"+str(height)+" "+str(int(capture_time))+"/"+str(int(shader_time))+"/"+str(int(postp_time))+" ms (CAP/GPU/POST)"            
            text = font.render(string, False, (255, 255, 255),(0,0,0))
            display.blit(text, (36, 36))
            # osd_id = canvas.create_text(36, 36, text=string, fill="white", font=(OSD_FONT), anchor=tkinter.W)
            
# Main
print("<RTSR> Select an active window to upscale.\n[ESC] to exit.\n[Space Bar] Refresh/Return to start menu.\n")
pygame.display.set_caption('RTSR')
pygame.font.init() # print(pygame.font.get_fonts())
font = pygame.font.SysFont('arialblack', 30)
start_menu_windows()
init_shader()

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT: running = False # user clicked X to close window           
        
        if menu_select_mode:    
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE: running = False # ESC to exit
                elif event.key == pygame.K_SPACE: start_menu_windows() # Refresh
                
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1: # 1/2/3 left/mid/right
                    x, y = pygame.mouse.get_pos()
                    i = x//tile_size
                    if windows[i]["accessible"]:
                        winID = windows[i]["id"]
                        winH = windows[i]["height"]
                        winW = windows[i]["width"]
                        # print("assigned",winW,winH,windows[i]["title"])
                        init_buffer() # trimming/padding adjusted w h
                        capture_windows_init(winID) # create capture handles only once
                        display = pygame.display.set_mode((winW*2, winH*2))
                        menu_select_mode = 0
                elif event.button == 3: # 1/2/3 left/mid/right
                    start_menu_windows() # Refresh

        if not menu_select_mode:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 2: # 1/2/3 left/mid/right
                    display = pygame.display.set_mode((3840,2160),pygame.FULLSCREEN|pygame.HWSURFACE|pygame.DOUBLEBUF) # toggle full screen
                elif event.button == 3: # 1/2/3 left/mid/right
                    menu_select_mode = 1
                    capture_windows_release()
                    start_menu_windows() # Refresh
                    continue     
                    
            if event.type == pygame.KEYDOWN:            
                if event.key == pygame.K_ESCAPE: running = False # ESC to exit
                elif event.key == pygame.K_SPACE: 
                    menu_select_mode = 1
                    capture_windows_release()
                    start_menu_windows() # Refresh
                    continue
            capture_upscale_display_windows()        
            

    pygame.display.flip()
    clock.tick(60)  # limits FPS to 30/60
pygame.quit()
