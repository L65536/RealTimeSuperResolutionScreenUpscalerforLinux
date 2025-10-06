import glfw # pip install glfw # not pyglfw
import compushady
import compushady.formats
import platform
import random
import time
from PIL import Image, ImageDraw, ImageFont  
    
target = compushady.Texture2D(256, 256, compushady.formats.B8G8R8A8_UNORM)
random_buffer = compushady.Buffer(target.size, compushady.HEAP_UPLOAD)

def mouse_button_callback(window, button, action, mods): # up/down double event trigger
    if button == glfw.MOUSE_BUTTON_MIDDLE and action == glfw.PRESS:
        print("Middle mouse button pressed!")
    if button == glfw.MOUSE_BUTTON_LEFT and action == glfw.PRESS:
        print("Left mouse button pressed!")
    if button == glfw.MOUSE_BUTTON_RIGHT and action == glfw.RELEASE:
        print("Right mouse button released!")
    xpos, ypos = glfw.get_cursor_pos(window)
    print(f"Cursor Position: X={xpos}, Y={ypos}")
    
def cursor_position_callback(window, xpos, ypos):
    print(f"Mouse position: X={xpos}, Y={ypos}")

def custom_cursor():
    # image = Image.open("cursor64.png").convert("RGBA")
    image = Image.open("cursor6250.png").convert("RGBA")
    image = image.resize((128, 128), Image.LANCZOS)

    text = "xxxxx"
    font = ImageFont.truetype("arial.ttf", 64)
    draw = ImageDraw.Draw(image)
    draw.text((0,0), text, fill=(255, 0, 0), font=font)

    return glfw.create_cursor(image, 0, 0) # hotspot at top-left corner

glfw.init()
glfw.window_hint(glfw.CLIENT_API, glfw.NO_API)
glfw.window_hint(glfw.DECORATED, glfw.FALSE)  

monitor = glfw.get_primary_monitor()
mode = glfw.get_video_mode(monitor)
width, height = mode.size.width, mode.size.height

glfw.window_hint(glfw.RED_BITS, mode.bits.red);
glfw.window_hint(glfw.GREEN_BITS, mode.bits.green);
glfw.window_hint(glfw.BLUE_BITS, mode.bits.blue);
glfw.window_hint(glfw.REFRESH_RATE, mode.refresh_rate);
window = glfw.create_window(width, height, "Borderless Fullscreen", monitor, None)
# window = glfw.create_window(target.width, target.height, 'Random', None, None)

#cursor = glfw.create_standard_cursor(glfw.ARROW_CURSOR)
#cursor = glfw.create_standard_cursor(glfw.IBEAM_CURSOR)
#cursor = glfw.create_standard_cursor(glfw.HAND_CURSOR)
#cursor = glfw.create_standard_cursor(glfw.CROSSHAIR_CURSOR)
#cursor = glfw.create_standard_cursor(glfw.HRESIZE_CURSOR)
#cursor = glfw.create_standard_cursor(glfw.VRESIZE_CURSOR)
cursor = custom_cursor()
glfw.set_cursor(window, cursor)
# glfw.set_cursor(window, None)
glfw.set_mouse_button_callback(window, mouse_button_callback)
# glfw.set_cursor_pos_callback(window, cursor_position_callback)

if platform.system() == "Windows":
    swapchain = compushady.Swapchain(glfw.get_win32_window(window), compushady.formats.B8G8R8A8_UNORM, 3)
# swapchain = Swapchain((glfw.get_x11_display(), glfw.get_x11_window(window)), B8G8R8A8_UNORM, 3)

while not glfw.window_should_close(window):
    glfw.poll_events()
    if glfw.get_key(window, glfw.KEY_1): pass

    random_buffer.upload(bytes([random.randint(0, 255), random.randint(
        0, 255), random.randint(0, 255), 255]) * (target.size // 4))
    random_buffer.copy_to(target)
    swapchain.present(target)

    # xpos, ypos = glfw.get_cursor_pos(window)
    # print(f"Cursor Position: X={xpos}, Y={ypos}")

    time.sleep(0.2)

swapchain = None  # this ensures the swapchain is destroyed before the window
glfw.destroy_cursor(cursor)
glfw.terminate()

# [v] glfw change mouse cursor
# [v] glfw mouse events
# [][windows:tested ok] glfw boardless window full screen toggle
