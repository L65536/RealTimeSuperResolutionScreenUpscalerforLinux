# Ver 0.4 WIP
- [Linux] Improve capture with ctypes https://stackoverflow.com/questions/69645/take-a-screenshot-via-a-python-script-on-linux/16141058#16141058
- [Shader] Improve cascade shaders speed by elimiting unnecessary intermediate buffer I/O
- [Windows/LInux] Test keyboard/mouse input pass through by window messenging etc.

# Known Issues and Investigations
- [Linux] Menu icon sometimes(50%) appears to be blank(BGRA mode) or color inverted(RGBX mode).
  - BGRA mode capturing seems always working when upscaling.
  - ***Check individual images and alpha values. => check pixel width and pygame...convert()***
  - Try other pixmap format arguments 0xFFFFFFFF or 0xFFFFFF00 
  - BGRX not available in pygame, but avaible in PIL.
- [Linux] Buggy switching fullscreen modes. Changes implemented. Testing...
  
# Implemented or Solved
- [Windows] Implement Graphics Capture using PyWinRT https://github.com/pywinrt/pywinrt
- [GUI] Frame freezing and pacing problems in v0.2 rev g9+
- [SHADER] Row pitch now correctly implemented for output buffer sizes and texture upload 2d function() => now support all input resolutions.
- [GUI] Implement cascade shader for shrinking fit to screen. This should solve most undefined oversize behavior.
- [Windows] Flickering when capturing, both original and captured. Try different parameter or new capture method.
