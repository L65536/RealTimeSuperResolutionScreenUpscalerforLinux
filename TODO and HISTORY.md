# Todo
- [Windows/Linux] look into alternative capture and display methods for speed up tips.
- [Models] implement/integrate other AI models with pytorch.

# History
## v0.0 Windows/Linux
- Read single image from file, upscale with SRCNN(Magpie HLSL), display.
- Cross platform, tested on Windows and Linux.
- Batch image converter.

## v0.1 rev w5 (Linux only)
- Real-time Linux window capture using xlib.
- [GUI] menu selector with thumbnails.

## v0.1 rev w8 (Linux only)
- [Code/Clean up] Breakdown/organize codes into functions, preparing for future changes.
- [GUI/Usability] return to main menu, refresh.
- [GUI/Usability] main menu, check if capture success and skip minimized target window.
- [GUI] OSD displays seperate times for capture/compute/display

## v0.2 rev g2 (Windows only) (Linux WIP)
- [Windows] New Windows branch.
- [Windows] Capture support using win32gui.
- [Windows] Use pygame(SDL) for GUI and display, instead of tkinter.

## v0.2 rev g8 (Windows and Linux) WIP testing...
- [Linux] Use pygame for Linux branch as well. 
- [Linux] [BUG] black thumbnails when capturing in BGRA. While RGBX modeshows all icons in Linux but incorrect color, BGRX not available in pygame.
- <del>[Linux] [BUG] Severe frame freeze, causes under invetigation.</del>
- <del>[Windows] frame pacing very insistant, looks to be slower than measured frame times. Moving mouse seems to increase frame updates???</del>
  Fixing frame freezing and pacing problems in v0.2 rev g9.
