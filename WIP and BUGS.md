# Ver 0.7 WIP
- [Linux] unstable frame rate/latency.
- [Linux] xshm testing.
- [LInux] Keyboard/mouse input pass through by transparent window or messenging etc.
- [Linux] Fullscreen support for swapchain display.
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
