from ctypes import windll
windll.user32.SetProcessDPIAware() # HiDPI support for GetClientRect()

from win32gui import GetClientRect
from winrt.windows.ui.windowmanagement import WindowServices
from winrt.windows.graphics.capture import GraphicsCaptureItem

def get_window_handle(default = 0):
    windows: list[GraphicsCaptureItem] = []
    client = []
    for win_id in WindowServices.find_all_top_level_window_ids():
        item = GraphicsCaptureItem.try_create_from_window_id(win_id)
        left, top, right, bottom = GetClientRect(win_id.value)
        if item is None: continue
        windows.append(item)
        client.append((right, bottom))
        print(f"{len(windows)} [{item.size.width}x{item.size.height}] {item.display_name}")
        
    while True:
        try:
            if default: selection = default                
            else: selection = input("\nSelect a window to capture: ")
            selected_item = windows[int(selection) - 1]
            clientW, clientH = client[int(selection) - 1]            
            windowW = selected_item.size.width
            windowH = selected_item.size.height            
            return selected_item, clientW, clientH, windowW, windowH    
        except:
            pass
            
if __name__ == "__main__":
    print(get_window_handle())
    