# Requirements: pip install compushady pillow numpy xlib
# Requirements: libvulkan-dev and libx11-dev on Debian Linux
import tkinter
import numpy as np
import struct
import time
import Xlib # capture and window location lib
import Xlib.display
from Xlib import X
from PIL import Image, ImageTk, ImageDraw
from compushady import (
    Compute, Buffer, Texture2D, HEAP_UPLOAD, HEAP_READBACK, 
    Sampler, SAMPLER_FILTER_POINT, SAMPLER_FILTER_LINEAR, SAMPLER_ADDRESS_MODE_CLAMP, SAMPLER_ADDRESS_MODE_WRAP, SAMPLER_ADDRESS_MODE_MIRROR,
    )
from compushady.formats import R8G8B8A8_UNORM
from compushady.shaders import hlsl

DEBUG = 1 # enable/disable DEBUG messages
OSD = 1 # OSD info panel enable/disable
OSD_FONT = 'Helvetica 36 bold'
FONT_SIZE = 70 # selector menu thumbnail font, dynamic 70*tile_size//600
winID = 0 # target window ID
winH = 0 # target window height
winW = 0 # target window width
tile_size = 600 # will dynamically calculated in code
tile=[] # menu selector thumbnail tiles (PIL image)
windows=[] # dict of window ID width height title

def start_menu():
    global canvas
    global tile_size
    # global root
    display = Xlib.display.Display()
    try: # get all available window ID width height title into (dict)windows=[]
        display_root = display.screen().root
        windowIDs = display_root.get_full_property(display.intern_atom('_NET_CLIENT_LIST'), X.AnyPropertyType).value           
        for windowID in windowIDs:
            window = display.create_resource_object('window', windowID)
            wproperty = window.get_full_property(display.intern_atom('_NET_WM_NAME'), 0)        
            geometry = window.get_geometry()
            title = wproperty.value.decode('utf-8') #.lower()
            title_words = title.split()
            if title_words: title = title_words[-1]
            # if DEBUG: print(f"{windowID} ({geometry.width:<4} x {geometry.height:<4}) {title}")
            windows.append({"id":windowID, "width":geometry.width, "height":geometry.height, "title":title})
    finally:
        display.close()
                
    # Display thumbnails and let user choose a window to upscale in GUI
    row = len(windows) # calculae thumbnail tile number and size
    tile_size = w // row
    for i in range(len(windows)):
        if DEBUG: print(f"[{i}] {windows[i]["id"]} {windows[i]["width"]:<4} x {windows[i]["height"]:<4} {windows[i]["title"]}")
        img = make_thumbnail_tile(i)        
        # if img is None: img = Image.new('RGBA', (tile_size, tile_size))
        tile.append(ImageTk.PhotoImage(img))
        canvas.create_image(i*tile_size,0,image=tile[-1],anchor=tkinter.NW)
        canvas.pack()                
        root.geometry("%dx%d+0+0" % (w, tile_size))
        root.update()

def frame_capture_upscale():
    #global canvas
    #global root
    global photoimage
    
    start_time = time.time() # process_time() is for CPU ONLY    
    display = Xlib.display.Display()
    try:			        
        window = display.create_resource_object('window', winID)
        height = winH
        width = winW
        # geometry = window.get_geometry() # geometry.width geometry.height # need to re-init shader if dimension changes
        pixmap = window.get_image(0, 0, width, height, X.ZPixmap, 0xffffffff)

        staging_buffer.upload(pixmap.data)
        staging_buffer.copy_to(INPUT)       
        compute1 = Compute(s1, cbv=[CB1], srv=[INPUT], uav=[T0,T1], samplers=[SP,SL])
        compute1.dispatch((width+7)//8, (height+7)//8, 1)
        compute2 = Compute(s2, cbv=[CB2], srv=[T0,T1], uav=[T2,T3], samplers=[SP,SL])
        compute2.dispatch((width+7)//8, (height+7)//8, 1)
        compute3 = Compute(s3, cbv=[CB3], srv=[T2,T3], uav=[T0], samplers=[SP,SL])
        compute3.dispatch((width+7)//8, (height+7)//8, 1)
        compute4 = Compute(s4, cbv=[CB4], srv=[INPUT,T0], uav=[OUTPUT2], samplers=[SP,SL])
        compute4.dispatch((width*2+15)//16, (height*2+15)//16, 1) # (OUPUT_size+block_size-1)//block_size
        OUTPUT2.copy_to(readback_buffer)
                
        image = Image.frombuffer('RGBX', (OUTPUT2.width, OUTPUT2.height), readback_buffer.readback(), "raw", "BGRX") 
        photoimage = ImageTk.PhotoImage(image)
        canvas.delete("all")
        canvas.create_image(0,0,image=photoimage,anchor=tkinter.NW)
        
        if OSD: # display OSD info panel
            ms=(time.time() - start_time)*1000
            string=" "+str(width)+"x"+str(height)+" "+str(int(ms))+" ms "
            osd_id=canvas.create_text(36, 36, text=string, fill="white", font=(OSD_FONT), anchor=tkinter.W)
            bbox = canvas.bbox(osd_id)
            box_id = canvas.create_rectangle(bbox, outline="red", fill="black")
            canvas.tag_raise(box_id)
            canvas.tag_raise(osd_id)
        canvas.pack()                                    
        root.geometry("%dx%d+0+0" % (OUTPUT2.width, OUTPUT2.height))
        root.update()
        #root.focus()
        #root.focus_set()
        
    except:
        if DEBUG: print("Error capture window frame. Error get_image(). Probably minimized.")

    finally:
        display.close()
        
    root.after(10, frame_capture_upscale)

def make_thumbnail_tile(i):
    image = None
    FONT_SIZE = 70*tile_size//600
    win_id = windows[i]["id"]
    display = Xlib.display.Display()

    window = display.create_resource_object('window', win_id)        
    geometry = window.get_geometry()
    width, height = geometry.width, geometry.height
    string1 = " "+windows[i]["title"]
    string2 = " "+str(width)+" x "+str(height)    
    try: # capture crop and pad to thumbnail tile size
        pixmap = window.get_image(0, 0, width, height, X.ZPixmap, 0xffffffff) # will fail if minimized
        image = Image.frombuffer('RGBX', (width, height), pixmap.data, "raw", "BGRX") # must use RGBX, RGBA not working in some cases ???
        crop_width = min(tile_size, width)
        crop_height = min(tile_size, width)    
        img = image.crop((0,0,crop_width-1,crop_height-1))
        image = Image.new(img.mode, (tile_size, tile_size), (0,0,0))
        image.paste(img, (0, 0))

    except: # create blank image tile if capture failed
        image = Image.new('RGBA', (tile_size, tile_size), (0,0,255)) 
        print("INFO: Blue thumbnail used for minimized windows.")
    display.close()
    draw = ImageDraw.Draw(image)  
    draw.rectangle((2,2,tile_size-2,tile_size-2), fill = None, outline = "white")
    draw.text((5, tile_size-200*tile_size//600), string2, fill ="red",font_size=FONT_SIZE)
    draw.text((5, tile_size-100*tile_size//600), string1, fill ="red",font_size=FONT_SIZE)    
    return image

menu_select_mode = 1 # run once flag
def menu_select(event):
    global winID
    global winH
    global winW
    global menu_select_mode
    
    if menu_select_mode: 
        i = event.x//tile_size
        winID = windows[i]["id"]
        winH = windows[i]["height"]
        winW = windows[i]["width"]
        menu_select_mode = 0
        
        shader_init()
        frame_capture_upscale()

def shader_init():
    global staging_buffer, readback_buffer
    global INPUT, OUTPUT, OUTPUT2, SP, SL
    global s1, s2, s3, s4, T0, T1, T2, T3, CB1, CB2, CB3, CB4
    
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

    height = winH
    width = winW
    INPUT = Texture2D(width, height, R8G8B8A8_UNORM)
    OUTPUT = Texture2D(width*2, height*2, R8G8B8A8_UNORM)
    OUTPUT2 = Texture2D(width*2, height*2, R8G8B8A8_UNORM)
    T0 = Texture2D(width, height, R8G8B8A8_UNORM)
    T1 = Texture2D(width, height, R8G8B8A8_UNORM)
    T2 = Texture2D(width, height, R8G8B8A8_UNORM)
    T3 = Texture2D(width, height, R8G8B8A8_UNORM)
    staging_buffer = Buffer(INPUT.size, HEAP_UPLOAD)
    readback_buffer = Buffer(OUTPUT2.size, HEAP_READBACK)

    with open("CuNNy-veryfast-NVL_Pass1.hlsl", 'r') as fp: shader1 = fp.read()
    with open("CuNNy-veryfast-NVL_Pass2.hlsl", 'r') as fp: shader2 = fp.read()
    with open("CuNNy-veryfast-NVL_Pass3.hlsl", 'r') as fp: shader3 = fp.read()
    with open("CuNNy-veryfast-NVL_Pass4.hlsl", 'r') as fp: shader4 = fp.read()
    s1=hlsl.compile(shader1)
    s2=hlsl.compile(shader2)
    s3=hlsl.compile(shader3)
    s4=hlsl.compile(shader4)

    CB1 = Buffer(40, HEAP_UPLOAD)
    CB2 = Buffer(40, HEAP_UPLOAD)
    CB3 = Buffer(40, HEAP_UPLOAD)
    CB4 = Buffer(40, HEAP_UPLOAD)
    CB1.upload(struct.pack('iiiiffffff', width, height, width, height, 1.0/width, 1.0/height, 1.0/width, 1.0/height, 1.0, 1.0))
    CB2.upload(struct.pack('iiiiffffff', width, height, width, height, 1.0/width, 1.0/height, 1.0/width, 1.0/height, 1.0, 1.0))
    CB3.upload(struct.pack('iiiiffffff', width, height, width, height, 1.0/width, 1.0/height, 1.0/width, 1.0/height, 1.0, 1.0))
    CB4.upload(struct.pack('iiiiffffff', width, height, width*2, height*2, 1.0/width, 1.0/height, 1.0/width/2, 1.0/height/2, 2.0, 2.0))
          
# Main GUI init
root = tkinter.Tk()
w, h = root.winfo_screenwidth(), root.winfo_screenheight()
canvas = tkinter.Canvas(root,width=w,height=h,highlightthickness=0)
canvas.configure(background='black')
# window_border_toggle=0 # use 0 for Linux testing
# root.overrideredirect(window_border_toggle)
root.geometry("%dx%d+0+0" % (w, h))
root.title("RTSR v0.1 alpha")
root.bind("<Button-1>", menu_select) # Click mouse
root.bind("<space>", lambda e: (e.widget.withdraw(), e.widget.quit()))
root.bind("<Escape>", lambda e: (e.widget.withdraw(), e.widget.quit()))

print("RTSR v0.1\nSelect an active window to upscale.\nAvoid blue thumbnails. (Minimized window, unable to capture contents.)\n[ESC][Space] key to exit.\n")
start_menu()
root.mainloop()