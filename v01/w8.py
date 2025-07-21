# Requirements: pip install compushady pillow numpy xlib
# Requirements: libvulkan-dev and libx11-dev on Debian Linux
from PIL import Image, ImageTk, ImageDraw
import tkinter
import numpy as np
import struct
import time

import Xlib # capture and window location
import Xlib.display
from Xlib import X

from compushady import (
    Compute, Buffer, Texture2D, HEAP_UPLOAD, HEAP_READBACK,
    Sampler, SAMPLER_FILTER_POINT, SAMPLER_FILTER_LINEAR, SAMPLER_ADDRESS_MODE_CLAMP, SAMPLER_ADDRESS_MODE_WRAP, SAMPLER_ADDRESS_MODE_MIRROR,
    )
from compushady.formats import R8G8B8A8_UNORM
from compushady.shaders import hlsl

DEBUG = 1 # enable/disable DEBUG messages
OSD = 1 # OSD info panel enable/disable
OSD_FONT = 'Helvetica 36 bold'

windows = [] # dict of window properties, {"id":windowID, "width":geometry.width, "height":geometry.height, "title":title, "accessible", 0}
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

menu_tile = [] # menu selector thumbnail tiles (PIL image)
def start_menu(): # Display thumbnails and let user choose a window to upscale
    global canvas
    global tile_size
    enumerate_windows_property_linux()
    canvas.delete("all")
    
    row = len(windows) # number of active windows
    tile_size = w // row # dynamic adjust tile size to fit all windows in one row
    for i in range(row):
        if DEBUG: print(f"[{i}] {windows[i]["id"]} {windows[i]["width"]:<4} x {windows[i]["height"]:<4} {windows[i]["title"]}")        
        menu_tile.append(ImageTk.PhotoImage(make_thumbnail_tile(i, tile_size)))
        canvas.create_image(i*tile_size,0,image=menu_tile[-1],anchor=tkinter.NW)
        canvas.pack()
        root.geometry("%dx%d+0+0" % (w, tile_size))
        root.update()

def make_thumbnail_tile(i, tile_size):
    image = None
    FONT_SIZE = 70*tile_size//600
    win_id = windows[i]["id"]

    # Linux
    display = Xlib.display.Display()
    window = display.create_resource_object('window', win_id)
    geometry = window.get_geometry()
    width, height = geometry.width, geometry.height

    try: # capture crop and pad to thumbnail tile size
        pixmap = window.get_image(0, 0, width, height, X.ZPixmap, 0xffffffff) # will fail if minimized
        image = Image.frombuffer('RGBX', (width, height), pixmap.data, "raw", "BGRX") # must use RGBX, RGBA not working in some cases ???
        crop_width = min(tile_size, width)
        crop_height = min(tile_size, width)
        cropped = image.crop((0,0,crop_width-1,crop_height-1))
        image = Image.new(image.mode, (tile_size, tile_size), (0,0,0))
        image.paste(cropped, (0, 0))
        windows[i]["accessible"] = 1
    except: # create blank image (plain blue) tile if capture failed
        image = Image.new('RGBA', (tile_size, tile_size), (0,0,255))
        if DEBUG: print("INFO: Blue thumbnail used for minimized windows.")
    display.close()

    # Decorate thumbnail tiles with rect and info
    string1 = " "+windows[i]["title"]
    string2 = " "+str(width)+" x "+str(height)
    string3 = " Minimized? " # Inaccessible
    draw = ImageDraw.Draw(image)
    draw.rectangle((2,2,tile_size-2,tile_size-2), fill = None, outline = "white")
    draw.text((5, tile_size-100*tile_size//600), string1, fill ="red",font_size=FONT_SIZE)
    draw.text((5, tile_size-200*tile_size//600), string2, fill ="red",font_size=FONT_SIZE)
    if not windows[i]["accessible"]: draw.text((5, tile_size-300*tile_size//600), string3, fill ="red",font_size=FONT_SIZE)
    return image

winID = 0 # target window ID
winH = 0 # target window height
winW = 0 # target window width
menu_select_mode = 1 # run once flag
def menu_select(event):
    global winID
    global winH
    global winW
    global menu_select_mode

    if menu_select_mode:
        i = event.x//tile_size
        if windows[i]["accessible"]:
            winID = windows[i]["id"]
            winH = windows[i]["height"]
            winW = windows[i]["width"]
            menu_select_mode = 0

            init_shader()
            init_buffer()
            capture_upscale_display_linux() # self loop
        else:
            if DEBUG: print("Unable to capture this window, probably minimized?")

def return_to_menu_select(event):
    global menu_select_mode
    global windows    
    menu_select_mode = 1
    windows = [] # reset
    start_menu() # refresh start menu

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

    height = winH
    width = winW
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

def capture_upscale_display_linux():
    global photoimage
    if menu_select_mode: return
    
    if True: #try:
        ###############################################################################################################
        start_time_capture = time.perf_counter()        
        display = Xlib.display.Display()
        window = display.create_resource_object('window', winID)        
        # geometry = window.get_geometry() # geometry.width geometry.height # need to re-init shader if dimension changes        
        height = winH
        width = winW
        pixmap = window.get_image(0, 0, width, height, X.ZPixmap, 0xffffffff) # DEBUG print(len(pixmap.data))
        display.close()
        ###############################################################################################################                
        start_time_shader = time.perf_counter() # process_time() is for CPU ONLY
        staging_buffer.upload(pixmap.data)
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
        start_time_postp = time.perf_counter() # process_time() is for CPU ONLY
        image = Image.frombuffer('RGBX', (OUTPUT.width, OUTPUT.height), readback_buffer.readback(), "raw", "BGRX")
        photoimage = ImageTk.PhotoImage(image)
        canvas.delete("all")
        canvas.create_image(0,0,image=photoimage,anchor=tkinter.NW)       
        if OSD: # display OSD info panel            
            postp_time = (time.perf_counter() - start_time_postp)*1000
            shader_time = (start_time_postp - start_time_shader)*1000
            capture_time = (start_time_shader - start_time_capture)*1000
            string = " "+str(width)+"x"+str(height)+" "+str(int(capture_time))+"/"+str(int(shader_time))+"/"+str(int(postp_time))+" ms (CAP/GPU/POST)"
            osd_id = canvas.create_text(36, 36, text=string, fill="white", font=(OSD_FONT), anchor=tkinter.W)
            bbox = canvas.bbox(osd_id)
            box_id = canvas.create_rectangle(bbox, outline="red", fill="black")
            canvas.tag_raise(box_id)
            canvas.tag_raise(osd_id)
        canvas.pack()
        root.geometry("%dx%d+0+0" % (OUTPUT.width, OUTPUT.height))
        root.update()
        #root.focus()
        #root.focus_set()
    #except: 
        # if DEBUG: print("Error capture window frame. Minimized???")
    #finally: 
        # display.close()
    
    root.after(10, capture_upscale_display_linux) # self loop
    
# Main GUI init
root = tkinter.Tk()
w, h = root.winfo_screenwidth(), root.winfo_screenheight()
canvas = tkinter.Canvas(root,width=w,height=h,highlightthickness=0)
canvas.configure(background='black')
# window_border_toggle=0 # use 0 for Linux testing
# root.overrideredirect(window_border_toggle)
root.geometry("%dx%d+0+0" % (w, h))
root.title("RTSR")
root.bind("<Button-1>", menu_select) # mouse, left-click
root.bind("<space>", return_to_menu_select)
root.bind("<Escape>", lambda e: (e.widget.withdraw(), e.widget.quit()))

print("<RTSR> Select an active window to upscale.\n[ESC] to exit.\n[Space] Refresh/Return to start menu.\n")
start_menu()
root.mainloop()