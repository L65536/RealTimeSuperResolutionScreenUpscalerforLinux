import Xlib 
import Xlib.display
from Xlib import X

def get_window_handle(default = 0):    
    disp = Xlib.display.Display()
    windows = []
    try:
        disp_root = disp.screen().root
        windowIDs = disp_root.get_full_property(disp.intern_atom('_NET_CLIENT_LIST'), X.AnyPropertyType).value
        for windowID in windowIDs:
            window = disp.create_resource_object('window', windowID)
            wproperty = window.get_full_property(disp.intern_atom('_NET_WM_NAME'), 0)
            geometry = window.get_geometry()
            title = wproperty.value.decode('utf-8') #.lower()
             
            windows.append({"id":windowID, "width":geometry.width, "height":geometry.height, "title":title})
            print(f"{len(windows)} {windowID} ({geometry.width:<4} x {geometry.height:<4}) {title}")
    finally:
        disp.close()
                
    while True:
        try:
            if default: selection = default                
            else: selection = input("\nSelect a window to capture: ")
            selected_item = windows[int(selection) - 1]['id']
            clientW = windows[int(selection) - 1]['width']
            clientH = windows[int(selection) - 1]['height']                        
            windowW = windows[int(selection) - 1]['width']
            windowH = windows[int(selection) - 1]['height']             
            return selected_item, clientW, clientH, windowW, windowH    
        except:
            pass
            
if __name__ == "__main__":
    print(get_window_handle())