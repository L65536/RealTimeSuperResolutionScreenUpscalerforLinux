# Known issues:
# [] Works with certain window resolution only. eg. 3840x 1920x 1280x but errors with random resolution => trim or pad to block size (too heavy to implement in python)
# [Windows] Capturing causes the original window and captured images flickering??? try different parameter or new capture method

# [] return to menu from continous mode failed without error => check command log
# [Windows] very slow frame updates? [fixed]
# [Linux] freezed frames?  [fixed]test[]

# Requirements: pip install compushady pillow numpy pygame
# Requirements: [Linux] pip install xlib
# Requirements: [Linux] libvulkan-dev and libx11-dev on Debian 

import numpy as np
import time
import os

import LIBSHADER as SHADER # local lib
if os.name == 'nt':
    import LIBCAP_WINDOWS as CAP  # local lib
else:
    import LIBCAP_LINUX as CAP  # local lib

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
menu_select_mode = 1 # menu mode, run once flag

def start_menu():
    global menu_select_mode
    global tile_size   
    global windows
    menu_select_mode = 1
    windows = CAP.enumerate_window_property()
        
    row = len(windows) # number of active windows
    tile_size = 3840 // row # dynamic adjust tile size to fit all windows in one row    
    display = pygame.display.set_mode((3840, tile_size),pygame.DOUBLEBUF)
    display.fill((0,0,0))

    for i in range(row): display.blit(make_thumbnail_tile(i, tile_size), (i*tile_size, 0))
    # if DEBUG: print(f"[{i}] {windows[i]["id"]} {windows[i]["width"]:<4} x {windows[i]["height"]:<4} {windows[i]["title"]}")

def make_thumbnail_tile(i, tile_size):
    global winH, winW
    image = None
    FONT_SIZE = 70*tile_size//600
    win_id = windows[i]["id"]
    winH = windows[i]["height"]
    winW = windows[i]["width"]

    try: # capture crop and pad to thumbnail tile size            
        cap = CAP.init(win_id)        
        buffer, width, height = CAP.get(cap) # DEBUG
        # print("DEBUG captured", win_id,width,height,len(buffer),width*height*4)
        if os.name == 'nt':        
            surface = pygame.image.frombuffer(buffer, (width,height), "BGRA") # Windows. [BUG] black icons in Linux ??? but capture OK?
        else:
            surface = pygame.image.frombuffer(buffer, (width,height), "RGBX") # Shows all icons in Linux but incorrect color, BGRX not available in pygame.         
        
        # image = surface.subsurface((0,0,tile_size,tile_size))
        image = pygame.transform.scale(surface, (tile_size,tile_size))
        windows[i]["accessible"] = 1
        CAP.release(cap)    
    except: # create blank image (plain blue) tile if capture failed
        image = pygame.Surface((tile_size, tile_size))
        image.fill((0,0,255))
        height = winH
        width = winW
        print(f"[ERROR] Capture or conversion failed on [{win_id}:{winW}x{winH}]. Minimized? Blue thumbnail used as substitute.")

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

def capture_upscale_display(cap):
    try:            
        time_capture = time.perf_counter()
        buffer,width,height = CAP.get(cap) # DEBUG print("Captured",width,height)            
        time_shader = time.perf_counter() # process_time() is for CPU ONLY
        SHADER.shadercompute(buffer,winW,winH)        
        time_postp = time.perf_counter()                
        surface = pygame.image.frombuffer(SHADER.readback_buffer.readback(), (SHADER.OUTPUT.width, SHADER.OUTPUT.height), "BGRA") # Windows and Linux               
    except:
        print(f"[ERROR] Capture or conversion failed on [{winID}]:{winW}x{winH} to {winW*2}x{winH*2}.")                    
        #print(f"[ERROR] Buffer conversion expect {SHADER.OUTPUT.width}x{SHADER.OUTPUT.height}x4={SHADER.OUTPUT.width*SHADER.OUTPUT.height*4} {SHADER.OUTPUT.size}. Got {len(SHADER.readback_buffer.readback())}")
        print("[ERROR] Currently limited support on target window size. Need to fit into block size of 8/16/64 ???\n")            
        # TODO: try adjust receiving buffer WxH, then surface = surface.subsurface((0,0,tile_size,tile_size)) or need to pad/trim input frame
        CAP.release(cap)                    
        start_menu() # go back to menu
        return
        
    display.blit(surface, (0, 0))
    if OSD: # display resolution and timing info panel
        postp_time = (time.perf_counter() - time_postp)*1000
        shader_time = (time_postp - time_shader)*1000
        capture_time = (time_shader - time_capture)*1000
        string = " "+str(width)+"x"+str(height)+" "+str(int(capture_time))+"/"+str(int(shader_time))+"/"+str(int(postp_time))+" ms (CAP/GPU/POST)"
        text = font.render(string, False, (255, 255, 255),(0,0,0))
        display.blit(text, (36, 36))
            
# Main
info = pygame.display.Info()
print(info)

print("\n<RTSR> Select an active window to upscale.\n[ESC] to exit.\n[Space Bar] Refresh/Return to menu. \n[Mouse] Mid/Right = Fullscreen/Return to Menu.\n")
pygame.display.set_caption('RTSR')
pygame.font.init() # print(pygame.font.get_fonts())
font = pygame.font.SysFont('arialblack', 30)
fullscreen = 0

start_menu()
while running:
    events = pygame.event.get()
    if menu_select_mode:
        for event in events:
            if event.type == pygame.QUIT: running = False # user clicked X to close window        
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE: running = False # ESC to exit
                elif event.key == pygame.K_SPACE: start_menu() # Refresh

            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1: # 1/2/3 left/mid/right
                    x, y = pygame.mouse.get_pos()
                    i = x//tile_size
                    if windows[i]["accessible"]:
                        winID = windows[i]["id"]
                        winH = windows[i]["height"]
                        winW = windows[i]["width"]
                        # print("Assigned",winW,winH,windows[i]["title"])
                        SHADER.init_buffer(winW,winH) # trimming/padding adjusted w h
                        cap = CAP.init(winID) # create capture handles only once                       
                        display = pygame.display.set_mode((winW*2, winH*2))
                        menu_select_mode = 0
                elif event.button == 3: # 1/2/3 left/mid/right
                    start_menu() # Refresh

    if not menu_select_mode:
        capture_upscale_display(cap)
        for event in events:
            if event.type == pygame.QUIT: running = False # user clicked X to close window        
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 2: # 1/2/3 left/mid/right                    
                    if(not fullscreen):
                        #display = pygame.display.set_mode((3840,2160),pygame.FULLSCREEN|pygame.HWSURFACE|pygame.DOUBLEBUF) # toggle full screen
                        display = pygame.display.set_mode((3840,2160), pygame.FULLSCREEN|pygame.DOUBLEBUF)
                        fullscreen = 1
                    else:
                        display = pygame.display.set_mode((winW*2, winH*2), pygame.DOUBLEBUF) # toggle to normal windowed mode
                        fullscreen = 0
                elif event.button == 3: # 1/2/3 left/mid/right                    
                    CAP.release(cap)   
                    start_menu() # go back to menu
                    continue

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE: running = False # ESC to exit
                elif event.key == pygame.K_SPACE:                    
                    CAP.release(cap)                    
                    start_menu() # go back to menu
                    continue
                    
    pygame.display.flip()
    clock.tick(60)  # limits FPS to 30/60
pygame.quit()

"""
        # print(readback_buffer.readback())
        # print(type(readback_buffer.readback()))
        # w=((OUTPUT.width+15)//16)*16
        # h=((OUTPUT.height+15)//16)*16
        # print(len(readback_buffer.readback()),h*w*4,w,h)

    start_time = time.perf_counter()
    buffer,width,height = capture_windows(786802,0)
    surface = pygame.image.frombuffer(buffer, (width,height), "BGRA")
    end_time = time.perf_counter()
    elapsed_time = end_time - start_time
    print(elapsed_time)

    # display.blit(surface, (0, 0))
    # display.blit(text, (0,0))
    # text = font.render('Test', False, (255, 0, 0),(0, 0, 0))
"""