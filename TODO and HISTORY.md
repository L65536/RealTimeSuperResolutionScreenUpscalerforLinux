# Todo
- [Linux] Use pygame for Linux branch as well. WIP testing...
- [Windows/Linux] look into alternative capture and display methods for speed up tips.
- [Models] implement/integrate other AI models.

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
- Use pygame(SDL) for GUI and display, instead of tkinter.
