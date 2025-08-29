# TODO PLANS
- [Capture/Linux] use shader to convert XPixMap
- [Capture/Windows] load/copy captured texture within VRAM
- [Capture] try NVFBC

# WIP
- [Linux] display_id_int = glfw.get_x11_display() # How to get this number with XLIB or PYQT5 ????? changes every run
- [Linux] Compushady/Swapchain not as fast as expected when compared to Windows
- [Linux] xshm testing, no speed improvement observed.
- [Shader] Improve cascade shaders speed by elimiting unnecessary intermediate buffer I/O
- [Testing] Gracefully exit/clean up for compushady and capture.
  
# HISTORY
- [Windows] Implement Graphics Capture using PyWinRT https://github.com/pywinrt/pywinrt
- [SHADER] Row pitch now correctly implemented for output buffer sizes and texture upload 2d function() => now support all input resolutions.
- [GUI] Implement cascade shader for shrinking fit to screen. This should solve most undefined oversize behavior.(for v0.3 only)
- [Windows] Flickering when capturing, both original and captured.  => fixed with new capture method.
- [Linux] Improve capture with ctypes. => 2x~3x faster
- Optimize threads/queues/callbacks to reduce frame latency.
- [v06 Windows/Linux] Display swapchain and copy output texture within VRAM.
- [v07 Windows/LInux] Keyboard/mouse input pass through by transparent overlay window.
- [v07 win/g40] [Capture/Windows] improve cropping speed with slack/lazy cropping (cut out title bar only)
- [v07 win/g43] improve out-of-bound mouse position => warp to the other side.





