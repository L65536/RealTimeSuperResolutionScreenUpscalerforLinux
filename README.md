# Introduction
This project contains simple Python scripts that magnify/upscale the screens of apps/games in realtime. 
Using current Super Resolution AI models for improved perceived upscaling quality.
GPUs and compute shaders are used to speed up the computation.
This process is similar to Nvidia's DLSS-SR and AMD's FSR series.
Other similar software projects include Magpie and Lossless Scaling.

# Implementation Overview
This project uses the HLSL shader files taken straight from the Magpie/CuNNy project.
A fast CNN model called CuNNy-veryfast-NVL is used (It's Similar to Anime4k).
This model provides good balance of text and graphic upscaling quality and speed.
Core of this project contains around 300 lines of Python codes plus external HLSL shader files.

# Version History
## Ver 0.0 for Windows and Linux
- Read single image from file, upscale with SRCNN(Magpie HLSL), display.
- Batch image converter.

## Ver 0.1 for Linux only
- Real-time Linux window capture using xlib.
- X2 upscaling of any runing window to a seperate window in Linux.
- [GUI] Thumbnailed source window selector at start up.
- [GUI] OSD displays seperate times for capture/compute/display

## Ver 0.1 Limitations
- No input passthrough support (need to run the original window side by side or with multi monitor setup).
- Fixed X2 magnification. No full screen support yet.
- Does not handle minimized windows. (Plain blue thumbnail is shown)
- Slow FPS for large source window sizes. 
Current background screen capture and display function overhead are magnitude slower than the core shader computations by GPUs.
Alternative screen capture and display acceleration approaches are required.
- [BUG] Undefined display/coordinates if the source window is too large (eg. desktop or taskbar at full screen width)

## Ver 0.2 for Windows and Linux
- [Windows] New Windows support. The main python GUI script is now cross-platform.
- [Windows] Capture support using win32gui.
- [Windows/Linux] Use pygame(SDL) for faster GUI and display, instead of tkinter.
- [Windows/Linux] Full screen support with mid mouse button. [ESC] or [Space] key to exit.
- [Shader backend] Fixed row pitch. Now shaders should support all input window dimensions.

##  Ver 0.3 for Windows and Linux
- [SHADER] Cascade shaders support.
- [GUI] Improved full screen support with more consistant output layouts.

# Future plans
- [Models] Implement/integrate other AI models with pytorch.
- [Windows/Linux] Look into alternative capture and display methods for speed up tips.
- [SHADER] Cascade with other resizing shaders for support of random zoom ratio.
- [GUI] Input passthrough to source app window.

# Acknowledgement and Special Thanks
This project contains codes based on the following projects/libraries:
- https://github.com/Blinue/Magpie
- https://github.com/funnyplanter/CuNNy
- https://github.com/rdeioris/compushady
- https://github.com/UR4N0-235/XWindowSystem_Screenshoter
- https://github.com/BoboTiG/python-mss/issues/180
- https://www.pygame.org/
