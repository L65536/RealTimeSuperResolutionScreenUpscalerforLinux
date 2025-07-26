import win32gui # pip install pywin32
import win32ui
from win32.win32gui import FindWindow, GetWindowRect, GetForegroundWindow, GetWindowText
from ctypes import windll
windll.user32.SetProcessDPIAware()

def enumerate_window_property(): # Retrieves a list of all visible top-level window handles.
    # global windows
    windows = []
    handles = []
    def enum_windows_callback(hwnd, lParam): # Callback function for EnumWindows. Appends visible window handles to the list.
        if win32gui.IsWindowVisible(hwnd): handles.append(hwnd)
        return True  # Continue enumeration
    win32gui.EnumWindows(enum_windows_callback, None)

    for handle in handles:
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
    return windows
    
def init(hwnd): # create capture handles only once
    # global WIN_HANDLES
    windll.user32.SetProcessDPIAware()
    left, top, right, bottom = win32gui.GetClientRect(hwnd)
    w = right - left
    h = bottom - top
    #w = winW # w = right - left # use trimmed/padded sizes for shaders
    #h = winH # h = bottom - top  # use trimmed/padded sizes for shaders
    hwnd_dc = win32gui.GetWindowDC(hwnd)
    mfc_dc = win32ui.CreateDCFromHandle(hwnd_dc)
    save_dc = mfc_dc.CreateCompatibleDC()
    bitmap = win32ui.CreateBitmap()
    bitmap.CreateCompatibleBitmap(mfc_dc, w, h)
    return (hwnd, hwnd_dc, mfc_dc, save_dc, bitmap)
    # WIN_HANDLES = (hwnd, hwnd_dc, mfc_dc, save_dc, bitmap)
    
def initQ(hwnd): # capture quarter only h=1/2 w=1/2
    # global WIN_HANDLES
    windll.user32.SetProcessDPIAware()
    left, top, right, bottom = win32gui.GetClientRect(hwnd)
    w = (right - left)//2
    h = (bottom - top)//2
    #w = winW # w = right - left # use trimmed/padded sizes for shaders
    #h = winH # h = bottom - top  # use trimmed/padded sizes for shaders
    hwnd_dc = win32gui.GetWindowDC(hwnd)
    mfc_dc = win32ui.CreateDCFromHandle(hwnd_dc)
    save_dc = mfc_dc.CreateCompatibleDC()
    bitmap = win32ui.CreateBitmap()
    bitmap.CreateCompatibleBitmap(mfc_dc, w, h)
    return (hwnd, hwnd_dc, mfc_dc, save_dc, bitmap)
    # WIN_HANDLES = (hwnd, hwnd_dc, mfc_dc, save_dc, bitmap)
    
def get(WIN_HANDLES):
    # global WIN_HANDLES
    (hwnd, hwnd_dc, mfc_dc, save_dc, bitmap) = WIN_HANDLES
    save_dc.SelectObject(bitmap)
    result = windll.user32.PrintWindow(hwnd, save_dc.GetSafeHdc(), 3)
    if result != 1: raise RuntimeError(f"Unable to acquire screenshot! Result: {result}")

    bmpinfo = bitmap.GetInfo()
    bmpstr = bitmap.GetBitmapBits(True)
    return bmpstr, bmpinfo["bmWidth"], bmpinfo["bmHeight"]
    
def release(WIN_HANDLES):
    # global WIN_HANDLES
    try: 
        (hwnd, hwnd_dc, mfc_dc, save_dc, bitmap) = WIN_HANDLES    
        win32gui.DeleteObject(bitmap.GetHandle())
        save_dc.DeleteDC()
        mfc_dc.DeleteDC()
        win32gui.ReleaseDC(hwnd, hwnd_dc)
        WIN_HANDLES = None    
    except:
        pass    