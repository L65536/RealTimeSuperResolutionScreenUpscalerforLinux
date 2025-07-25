#  WIP 0.3 Improved full frame and cascade shaders supports (Windows and Linux)
In order to get consistant output layouts:
- For source window < 1/2 of screen width/height,
2x upscaling and cascade Lanczos for final output.
- For source window == 1/2 of screen width/height,
2x upscaling only.
- For source window between 1/2 and 4/4 of screen width/height,
2x upscaling and cascade Lanczos for final output.
- For source window = 4/4 of screen width/height,
cropping applied and single 2x upscaling to produce full frame of upper left portion.

# Known Issues and Investigations
- [Windows] Flickering when capturing, both original and captured. Try different parameter or new capture method.
- [Linux] Menu icon sometimes(50%) appears to be blank(BGRA mode) or color inverted(RGBX mode).
  - BGRA mode capturing seems always working when upscaling.
  - ***Check individual images and alpha values. => check pixel width and pygame...convert()***
  - Try other pixmap format arguments 0xFFFFFFFF or 0xFFFFFF00 
  - BGRX not available in pygame, but avaible in PIL.
- [Linux] Buggy switching fullscreen modes.
  - Changes implemented. Works mostly for source windows size smaller than 1/2 of screen size.
  - ***Need to implement cascade shader for shrinking fit to screen. This should solve most undefined oversize behavior.***

# Solved
- [GUI] Frame freezing and pacing problems in v0.2 rev g9+
- [SHADER] Row pitch now correctly implemented for output buffer sizes and texture upload 2d function() => now support all input resolutions.
