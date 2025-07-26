# Known issues:
# [Windows] Flickering when capturing, both original and captured. Try different parameter or new capture method.
# [Linux] Menu icon appears to be blank(BGRA mode) or color inversed(RGBX).

# Requirements: pip install compushady pillow numpy pygame
# Requirements: [Linux] pip install xlib
# Requirements: [Linux] libvulkan-dev and libx11-dev on Debian

import numpy as np
import time
import os

import LIBSHADER_SRCNN as SRCNN # local lib
import LIBSHADER_Lanczos as Lanczos # local lib
if os.name == 'nt':
    import LIBCAP_WINDOWS as CAP  # local lib
else:
    import LIBCAP_LINUX as CAP  # local lib

caption = 'RTSR'
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
import pygame
pygame.init()
clock = pygame.time.Clock()

DEBUG = 1 # enable/disable DEBUG messages
OSD = 1 # OSD info panel enable/disable
OSD_FONT = 'Helvetica 36 bold'

windows = [] # dict of window properties, {"id":windowID, "width":geometry.width, "height":geometry.height, "title":title, "accessible", 0}
sourceID = 0 # target window ID
sourceH = 0 # target window height
sourceW = 0 # target window width
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
    global sourceH, sourceW
    image = None
    FONT_SIZE = 70*tile_size//600
    id = windows[i]["id"]
    sourceH = windows[i]["height"]
    sourceW = windows[i]["width"]

    try: # capture crop and pad to thumbnail tile size
        cap = CAP.init(id)
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
        height = sourceH
        width = sourceW
        print(f"[ERROR] Capture or conversion failed on [{win_id}:{sourceW}x{sourceH}]. Minimized? Blue thumbnail used as substitute.")

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
    try: # TODO reduce if complexity
        time_capture = time.perf_counter()
        buffer,width,height = CAP.get(cap) # DEBUG print("Captured",width,height)

        time_shader = time.perf_counter() # process_time() is for CPU ONLY
        SRCNN.compute(buffer,sourceW,sourceH)
        if cascade: Lanczos.compute(SRCNN.readback_buffer.readback(), SRCNN.OUTPUT.row_pitch//4, sourceH*2, (Lanczos.OUTPUT.row_pitch//4, Lanczos.OUTPUT.height))
        
        time_postp = time.perf_counter()
        if cascade:
            surface = pygame.image.frombuffer(Lanczos.readback_buffer.readback(), (Lanczos.OUTPUT.row_pitch//4, Lanczos.OUTPUT.height), "BGRA") # Windows and Linux
        else:
            surface = pygame.image.frombuffer(SRCNN.readback_buffer.readback(), (SRCNN.OUTPUT.row_pitch//4, SRCNN.OUTPUT.height), "BGRA") # Windows and Linux        
        
    except:
        print(f"[ERROR] Capture or conversion failed on [{sourceID}]:{sourceW}x{sourceH} to {sourceW*2}x{sourceH*2}. Row pitch = {SRCNN.OUTPUT.row_pitch//4}x4")
        print(f"[ERROR] Buffer conversion expect {SRCNN.OUTPUT.row_pitch//4}x{SRCNN.OUTPUT.height}x4={SRCNN.OUTPUT.row_pitch*SRCNN.OUTPUT.height} {SRCNN.OUTPUT.size}. Got {len(SRCNN.readback_buffer.readback())}")
        CAP.release(cap)
        start_menu() # go back to menu
        return
    
    display.blit(surface, (0, 0))
    if OSD: # display resolution and timing info panel
        postp_time = (time.perf_counter() - time_postp)*1000
        shader_time = (time_postp - time_shader)*1000
        capture_time = (time_shader - time_capture)*1000
        string = " "+str(width)+"x"+str(height)+" "+str(int(capture_time))+"/"+str(int(shader_time))+"/"+str(int(postp_time))+" ms (CAP/GPU/POST)"
        if cropping: string = "Cropped"+string
        if cascade: string = "Cascaded"+string
        text = font.render(string, False, (255, 255, 255),(0,0,0))
        display.blit(text, (36, 36))

def set_window_size(fullscreen):
    global display
    if fullscreen:
        display = pygame.display.set_mode((sysW, sysH))
    else:
        w = sourceW*2
        h = sourceH*2
        if sysW/sysH <= 4096/1080: # only for non-wide screen
            if sourceW >= sysW//2: # cropped or oversize
                   w = sourceW
                   h = sourceH

        display = pygame.display.set_mode((w, h)) # pygame.SHOWN default
        # display = pygame.display.set_mode((sourceW*2, sourceH*2))

def init(i):
    global sourceID, sourceH, sourceW
    global cascade, cropping
    global cap, display, fullscreen
    sourceID = windows[i]["id"]
    sourceH = windows[i]["height"]
    sourceW = windows[i]["width"]

    # define handling of source frame size
    cascade = 0
    cropping = 0
    if sysW/sysH <= 4096/1080: # only for non-wide screen        
        if sourceW >= sysW: cropping = 1# crop full screen source image
        if sourceW == sysW//2 or sourceW == sysW: cascade = 0
        else: cascade = 1 # use additional Lanczos to fit screen size
    # print (sourceW,sysW,cropping,cascade)
    if cropping:
        cap = CAP.initQ(sourceID)
        sourceH = sourceH//2
        sourceW = sourceW//2
    else:
        cap = CAP.init(sourceID) # create capture handles only once

    SRCNN.init_buffer(sourceW,sourceH) # trimming/padding adjusted w h
    if cascade: 
        w = SRCNN.OUTPUT.row_pitch//4
        h = sourceH*2
        ratio = min(sysW/w, sysH/h) # keep aspect ratio        
        Lanczos.init_buffer(SRCNN.OUTPUT.row_pitch//4, sourceH*2, int(w*ratio), int(h*ratio))                    

    fullscreen = 0
    set_window_size(fullscreen)
    capture_upscale_display(cap)

# Main
info = pygame.display.Info()
print(info)

print("\n<RTSR> Select an active window to upscale.\n[ESC] to exit.\n[Space Bar] Refresh/Return to menu. \n[Mouse] Mid/Right = Fullscreen/Return to Menu.\n")
pygame.display.set_caption(caption)
pygame.font.init() # print(pygame.font.get_fonts())
font = pygame.font.SysFont('arialblack', 30)
[(sysW,sysH)] = pygame.display.get_desktop_sizes()
fullscreen = 0

start_menu()
running = True
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
                        init(i)
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
                        #display = pygame.display.set_mode((3840,2160), pygame.FULLSCREEN|pygame.DOUBLEBUF)
                        pygame.display.quit()
                        pygame.display.init()
                        pygame.display.set_caption(caption)
                        fullscreen = 1
                        set_window_size(fullscreen)
                    else:
                        #display = pygame.display.set_mode((sourceW*2, sourceH*2), pygame.DOUBLEBUF) # toggle to normal windowed mode
                        pygame.display.quit()
                        pygame.display.init()
                        pygame.display.set_caption(caption)
                        fullscreen = 0
                        set_window_size(fullscreen)
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
    clock.tick(120)  # limits FPS to 30/60
pygame.quit()
