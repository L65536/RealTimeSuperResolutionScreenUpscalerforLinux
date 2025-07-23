# Known Issues and Investigations
- [Windows] Flickering when capturing, both original and captured. Try different parameter or new capture method.
- [Linux] Menu icon appears to be blank(BGRA mode) or color inversed(RGBX mode).
  - BGRA mode capturing seems working. Check individual images and alpha values.
  - Try other pixmap format arguments 0xFFFFFFFF or 0xFFFFFF00 
  - BGRX not available in pygame, but avaible in PIL.
- [Linux] slow and buggy switching fullscreen modes.

# Solved
- [GUI] Frame freezing and pacing problems in v0.2 rev g9+
- [SHADER] Row pitch now correctly implemented for buffer sizes and image upload 2d => fix support of all input resolutions.
