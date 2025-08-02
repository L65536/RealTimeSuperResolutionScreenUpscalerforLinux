# Ver 0.6 WIP
- [Windows/LInux] Keyboard/mouse input pass through by window messenging etc.
- [Shader] Improve cascade shaders speed by elimiting unnecessary intermediate buffer I/O

# Known Issues and Investigations
- [Windows] ver 0.5 Flickering => break down compute() to smaller functions and wait for display queue finish before download/overwrite buffer
  
# Implemented or Solved Issues
- [Windows] Implement Graphics Capture using PyWinRT https://github.com/pywinrt/pywinrt
- [SHADER] Row pitch now correctly implemented for output buffer sizes and texture upload 2d function() => now support all input resolutions.
- [GUI] Implement cascade shader for shrinking fit to screen. This should solve most undefined oversize behavior.
- [Windows] Flickering when capturing, both original and captured.  => new capture method.
- [Linux] Improve capture with ctypes. => 2x~3x faster
- Optimize threads/queues/callbacks to reduce frame latency.
