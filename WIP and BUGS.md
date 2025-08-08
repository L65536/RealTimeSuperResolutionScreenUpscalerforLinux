# Ver 0.6 WIP
- [Linux] crash
- [Linux] xshm testing
- [Windows] capture/cropping client area without costly operations
  
# Future plans
- [Windows/LInux] Keyboard/mouse input pass through by window messenging etc.
- [Shader] Improve cascade shaders speed by elimiting unnecessary intermediate buffer I/O

# Past Issues
- [Windows] ver 0.5 Flickering at start, when no screen update => break down compute() to smaller functions and wait for display queue finish before download/overwrite buffer
- Add more checks for queues for gracefully exit.
  
# Implemented or Solved Issues
- [Windows] Implement Graphics Capture using PyWinRT https://github.com/pywinrt/pywinrt
- [SHADER] Row pitch now correctly implemented for output buffer sizes and texture upload 2d function() => now support all input resolutions.
- [GUI] Implement cascade shader for shrinking fit to screen. This should solve most undefined oversize behavior.(for v0.3 only)
- [Windows] Flickering when capturing, both original and captured.  => fixed with new capture method.
- [Linux] Improve capture with ctypes. => 2x~3x faster
- Optimize threads/queues/callbacks to reduce frame latency.
- Use display swapchain and copy output texture within VRAM.
