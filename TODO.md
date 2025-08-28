# TODO PLANS
- [Shader/Windows] use shader to crop image for client area
- [Shader/Linux] use shader to convert XPixMap
- [Capture/Windows] load/copy captured texture within VRAM
- [Capture/Windows] improve cropping speed by modify Compushady/upload2D
- [Capture] try NVFBC

# WIP
- [Linux] display_id_int = glfw.get_x11_display() # How to get this number with XLIB or PYQT5 ????? changes every run
- [Linux] Compushady/Swapchain not as fast as expected when compared to Windows
- [Linux] xshm testing, no speed improvement observed.
- [Windows] capture/crop client area without costly numpy operations.
- [Shader] Improve cascade shaders speed by elimiting unnecessary intermediate buffer I/O
- [Testing] Gracefully exit/clean up for compushady and capture.
  
# Implemented or Solved Issues
- [Windows] Implement Graphics Capture using PyWinRT https://github.com/pywinrt/pywinrt
- [SHADER] Row pitch now correctly implemented for output buffer sizes and texture upload 2d function() => now support all input resolutions.
- [GUI] Implement cascade shader for shrinking fit to screen. This should solve most undefined oversize behavior.(for v0.3 only)
- [Windows] Flickering when capturing, both original and captured.  => fixed with new capture method.
- [Linux] Improve capture with ctypes. => 2x~3x faster
- Optimize threads/queues/callbacks to reduce frame latency.
- Use display swapchain and copy output texture within VRAM.
- [Windows/LInux] Keyboard/mouse input pass through by transparent overlay window.
- [Windows/Linux] Fullscreen support for swapchain display.
- 
