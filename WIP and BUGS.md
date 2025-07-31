# Ver 0.4 WIP
- Optimize thread and callbacks to reduce frame latency.
- [Shader] Improve cascade shaders speed by elimiting unnecessary intermediate buffer I/O
- [Windows/LInux] Test keyboard/mouse input pass through by window messenging etc.

# Known Issues and Investigations
- [Linux] ver 0.3 Buggy switching fullscreen modes. Changes implemented. Testing...
  
# Implemented or Solved Issues
- [Windows] Implement Graphics Capture using PyWinRT https://github.com/pywinrt/pywinrt
- [SHADER] Row pitch now correctly implemented for output buffer sizes and texture upload 2d function() => now support all input resolutions.
- [GUI] Implement cascade shader for shrinking fit to screen. This should solve most undefined oversize behavior.
- [Windows] Flickering when capturing, both original and captured.  => new capture method.
- [Linux] Improve capture with ctypes. => 2x~3x faster
