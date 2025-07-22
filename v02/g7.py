# Known issues:
# Works with certain window resolution only. eg. 3840x 1920x 1280x but errors with random resolution => trim or pad to block size (too heavy to implement in python)
# [Windows] Capturing causes the original window and captured images flickering??? try different parameter or new capture method

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
    global tile_size   
    global windows
    windows = CAP.enumerate_window_property()
        
    row = len(windows) # number of active windows
    tile_size = 3840 // row # dynamic adjust tile size to fit all windows in one row
    display = pygame.display.set_mode((3840, tile_size))
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
        buffer, width, height = CAP.get(cap) # print(win_id,width,height)
        surface = pygame.image.frombuffer(buffer, (width,height), "BGRA")
        CAP.release(cap)        
        image = surface.subsurface((0,0,tile_size,tile_size))
        windows[i]["accessible"] = 1    
    except: # create blank image (plain blue) tile if capture failed
        image = pygame.Surface((tile_size, tile_size))
        image.fill((0,0,255))
        height = winH
        width = winW
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

def capture_upscale_display(cap):
    if True: #try:        
        time_capture = time.perf_counter()
        buffer,width,height = CAP.get(cap) # DEBUG print("Captured",width,height)
                
        time_shader = time.perf_counter() # process_time() is for CPU ONLY
        SHADER.shadercompute(buffer,winW,winH)
        
        time_postp = time.perf_counter()
        # DEBUG print(len(readback_buffer.readback()),"read,",OUTPUT.width*OUTPUT.height*4,"=",OUTPUT.width,"x",OUTPUT.height)
        # surface = pygame.image.frombuffer(buffer, (width,height), "BGRA")
        surface = pygame.image.frombuffer(SHADER.readback_buffer.readback(), (SHADER.OUTPUT.width, SHADER.OUTPUT.height), "BGRA")
        display.blit(surface, (0, 0))

        if OSD: # display resolution and timing info panel
            postp_time = (time.perf_counter() - time_postp)*1000
            shader_time = (time_postp - time_shader)*1000
            capture_time = (time_shader - time_capture)*1000
            string = " "+str(width)+"x"+str(height)+" "+str(int(capture_time))+"/"+str(int(shader_time))+"/"+str(int(postp_time))+" ms (CAP/GPU/POST)"
            text = font.render(string, False, (255, 255, 255),(0,0,0))
            display.blit(text, (36, 36))
            
# Main
print("<RTSR> Select an active window to upscale.\n[ESC] to exit.\n[Space Bar] Refresh/Return to menu. [Mouse] Left/Right = Fullscreen/Return to Menu.\n")
pygame.display.set_caption('RTSR')
pygame.font.init() # print(pygame.font.get_fonts())
font = pygame.font.SysFont('arialblack', 30)
start_menu()

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT: running = False # user clicked X to close window

        if menu_select_mode:
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
                        # print("assigned",winW,winH,windows[i]["title"])
                        SHADER.init_buffer(winW,winH) # trimming/padding adjusted w h
                        cap = CAP.init(winID) # create capture handles only once                       
                        display = pygame.display.set_mode((winW*2, winH*2))
                        menu_select_mode = 0
                elif event.button == 3: # 1/2/3 left/mid/right
                    start_menu() # Refresh

        if not menu_select_mode:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1: # 1/2/3 left/mid/right
                    display = pygame.display.set_mode((3840,2160),pygame.FULLSCREEN|pygame.HWSURFACE|pygame.DOUBLEBUF) # toggle full screen
                elif event.button == 3: # 1/2/3 left/mid/right
                    menu_select_mode = 1
                    CAP.release(cap)   
                    start_menu() # Refresh
                    continue

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE: running = False # ESC to exit
                elif event.key == pygame.K_SPACE:
                    menu_select_mode = 1
                    CAP.release(cap)                    
                    start_menu() # Refresh
                    continue
            capture_upscale_display(cap) # Cross platform

    pygame.display.flip()
    clock.tick(120)  # limits FPS to 30/60
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