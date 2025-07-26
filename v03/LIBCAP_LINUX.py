import Xlib # capture and window location
import Xlib.display
from Xlib import X

def enumerate_window_property(): # enum window ID width height title into windows=[{dict}]
    global windows
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
            title_words = title.split()
            if title_words: title = title_words[-1]
            if 'RTSR' in title: continue # skip self
            if 'Desktop' in title: continue # skip
            if 'panel' in title: continue # skip
            # if DEBUG: 
            print(f"{windowID} ({geometry.width:<4} x {geometry.height:<4}) {title}")
            windows.append({"id":windowID, "width":geometry.width, "height":geometry.height, "title":title, "accessible": 0})
    finally:
        disp.close()
        
    return windows    

def init(hwnd): # create capture handles only once
    # global WIN_HANDLES
    # WIN_HANDLES = (hwnd, hwnd_dc, mfc_dc, save_dc, bitmap)
    
    disp = Xlib.display.Display() # MOVE INIT OUTSIDE LOOP
    window = disp.create_resource_object('window', hwnd)
    geometry = window.get_geometry() # geometry.width geometry.height # need to re-init shader if dimension changes
    width, height = geometry.width, geometry.height
    # height = winH
    # width = winW       
    return (disp, window, width, height)
                
def get(WIN_HANDLES):
    # global WIN_HANDLES    
    global pixmap
    (disp, window, width, height) = WIN_HANDLES
    
    pixmap = window.get_image(0, 0, width, height, X.ZPixmap, 0xffffffff) # will fail if minimized # DEBUG print(len(pixmap.data))
    # image = Image.frombuffer('RGBX', (width, height), pixmap.data, "raw", "BGRX") # must use RGBX, RGBA not working in some cases ??? PIL LINUX
    # surface = pygame.image.frombuffer(pixmap.data, (width,height), "BGRX") # Windows pygame
    # buffer = pixmap.data                       
    return pixmap.data, width, height
    # return bmpstr, bmpinfo["bmWidth"], bmpinfo["bmHeight"] # Windows

def release(WIN_HANDLES):
    # global WIN_HANDLES       
    try:   
        (disp, window, width, height) = WIN_HANDLES
        disp.close()    
    except:
        pass
    