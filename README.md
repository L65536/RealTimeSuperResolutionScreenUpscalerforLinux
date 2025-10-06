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

Screen captures are performed natively using DirectX's Graphics Capture (for Windows) and NVFBC direct backend (for Linux) for the best latency performance.
The shaders are loaded using Compushady library and computed on GPU. Display via Swapchain.

Core of this project contains around 300 lines of Python and C codes plus external HLSL shader files.

# Latest stable versions
## For Linux (X11 only) with Nvidia GPUs
https://github.com/L65536/RealTimeSuperResolutionScreenUpscalerforLinux/blob/main/v08linux_nvfbc/g62nvfbc-direct.py
## For Windows 
https://github.com/L65536/RealTimeSuperResolutionScreenUpscalerforLinux/blob/main/v07win/g43.py

# Development and test system configurations
- Windows 11 LTSC
- Python 3.12.xx
- (Linux) PorteuX 2.3 (Slackware current based)
- (Linux) Xfce 4.2 with X11
- (Linux) NVIDIA Driver 580.82.09
- (Linux) wine-10.15 (from PorteuX store)
- (Linux) dxvk-2.7.1 for wine (from Github download), required for NVFBC direct capture.

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

## Ver 0.2 for Windows and Linux [pygame]
- [Windows] New Windows support. The main python GUI script is now cross-platform.
- [Windows] Capture support using win32gui.
- [Windows/Linux] Use pygame(SDL) for faster GUI and display, instead of tkinter.
- [Windows/Linux] Full screen support with mid mouse button. [ESC] or [Space] key to exit.
- [Shader backend] Fixed row pitch. Now shaders should support all input window dimensions.

##  Ver 0.3 for Windows and Linux
- [SHADER] Cascade shaders support.
- [GUI] Improved full screen support with more consistant output layouts.

##  Ver 0.4win Streamlined version for Windows [D3D11 Graphic Capture]
- [Windows] Caputure function now uses native Windows Graphic Capture Direct3D11CaptureFramePool calls implemented using pywinrt. This provides theoretically fastest capture speed and customizability on Windows 10+.
  
##  Ver 0.4linux Streamlined version for Linux 
- [Linux] Improved capture processing speed (2x~3x) with xlib/ctypes.
- [Linux] xshm Implementation/benchmark. (Work in Progress)

##  Ver 0.5 Windows and Linux [pyglet]
- [GUI] Switched to Pyglet for GUI and display, instead of Pygame. This should provide more consistant full screen switching and faster display, especially on Linux.
- Improved frame latency with concurrent thread/queue management for capture, compute and display.

##  Ver 0.6 Windows and Linux [Swapchain]
- [Display] Implemented compushady's Swapchain display function. This eliminates display overhead and should increase FPS significantly.

##  Ver 0.7 Windows and Linux [Transparent window overlay]
- [Display/UI] Implemented transparent window overlay mode and enabled keyboard/mouse passthrough.
- [Windows/UI] Use [TAB] key to start/stop upscaling current active window.

##  Ver 0.8 Linux only [NVFBC DIRECT capture for X11]
- [Capture] Implemented NVFBC with X11 backend (NVFBC_BACKEND_X11) via ctypes. Much faster capture performance.
  - [Limitation] Requires a Nvidia GPU.
  - [Limitation] This particular backend only works with non-occluded windows. Only suitable for ultrawide screens.
  - [Limitation] NVFBC_BACKEND_X11 is for X11 only.
- [Capture] Implemented NVFBC capture with DIRECT backend (NVFBC_BACKEND_DIRECT). This backend can capture occluded applications on both X11 and Wayland. This new capture backend API was just released in H2 2025.
  - [Limitation] Current capture API v1.9 only works with Vulkan programs, but not OpenGL programs. MangoHud could show which display library a program uses.
  - [Limitation] This repo's implementation has only been tested on x11.
  - [Requirement] Requires a Nvidia GPU with the latest driver. (tested on 580.xx)
  - [Requirement] nvidia-dbus.conf needs to be placed at /etc/dbus-1/system.d/, then reboot. (requires dbus only, not related to systemd)
##  Ver 0.9 Linux only [Wayland support] Work in progress...
- [Capture] Implemented NVFBC with PipeWire backend (NVFBC_BACKEND_PIPEWIRE). This works well in conjunction with Virtual Screen of KDE Plasma Desktop, eliminating the need to handle most window/overlay/mouse/cursor/UI elements, resulting much shorter codes.
- [Display/wayland/pygame-ce] Works but very slow downloading from GPU.
- [Display/wayland/swapchain/glfw] Works quite well with good latency.
- [GUI finalization] Work in progress...

# Future plans
- [Models] Implement/integrate other AI models with pytorch.

# Acknowledgement and Special Thanks
This project contains codes based on the following projectsa and libraries:
- https://github.com/Blinue/Magpie
- https://github.com/funnyplanter/CuNNy
- https://github.com/rdeioris/compushady
- https://developer.nvidia.com/capture-sdk
- https://github.com/LizardByte/Sunshine
- https://github.com/pywinrt/pywinrt
- https://pypi.org/project/PySide6/
- https://shallowsky.com/blog/programming/click-thru-translucent-update.html
  
- For old versions:
- https://github.com/UR4N0-235/XWindowSystem_Screenshoter
- https://stackoverflow.com/questions/69645/take-a-screenshot-via-a-python-script-on-linux/16141058#16141058
- https://pyglet.org/
- https://www.pygame.org/
- https://www.glfw.org/
- https://github.com/BoboTiG/python-mss/issues/180

