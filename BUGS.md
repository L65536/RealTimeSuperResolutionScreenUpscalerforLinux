# Known Issues and Investigations
- [Windows] Flickering when capturing, both original and captured. Try different parameter or new capture method.
- [Linux] Menu icon appears to be blank(BGRA mode) or color inverted(RGBX mode).
  - BGRA mode capturing seems working when upscaling.
  - ***Check individual images and alpha values. => check pixel width and pygame...convert()***
  - Try other pixmap format arguments 0xFFFFFFFF or 0xFFFFFF00 
  - BGRX not available in pygame, but avaible in PIL.
- [Linux] Buggy switching fullscreen modes.
  - Changes implemented. Works mostly for source windows size smaller than 1/2 of screen size.
  - ***Need to implement cascade shader for shrinking fit to screen. This should solve most undefined oversize behavior.***

# Solved
- [GUI] Frame freezing and pacing problems in v0.2 rev g9+
- [SHADER] Row pitch now correctly implemented for buffer sizes and image upload 2d => fix support of all input resolutions.
