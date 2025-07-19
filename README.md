# RealTimeSuperResolutionScreenUpscalerforLinux
Real Time Super Resolution Screen Upscaler for Linux written in Python

# Abstract
This project contains simple Python scripts that magnify/upscale the screens of apps/games in realtime. 
Using current Super Resolution AI models for improved perceived upscaling quality.
GPUs and compute shaders are used to speed up the computation.
This process is similar to Nvidia's DLSS-SR and AMD's FSR series.
Other similar software projects include Magpie and Lossless Scaling.

# Ver 0.1 Summary
This project uses the HLSL shader files taken straight from the Magpie project.
A specialised CNN model called CuNNy-veryfast-NVL is used. (Similar to Anime4k)
This model provides good text and grpachic upscaling quality and speed.
V1 of this project contains around 200 lines of Python codes.

# Ver 0.1 Functionalities
- X2 upscaling of a runing window to a seperate window in Linux.
- [GUI] Thumbnailed target window selector at start up. 

# Ver 0.1 Limitations
- No input passthrough support (need to run the original window side by side or with multi monitor setup).
- No full screen support yet.
- Does not handle minimized windows. (plain blue thumbnail)
- Slow FPS for large target window sizes. 
Current background screen capture speed is >10x slower than the core shader computation by GPUs.
An alternative screen capture approach is required.
- [BUG] wrong display coordinate if the target window is too large (eg desktop or taskbar)

# Acknowledgement and special thanks
V1 of this project contains codes based on the following projects/libraries:
- https://github.com/Blinue/Magpie
- https://github.com/funnyplanter/CuNNy
- https://github.com/rdeioris/compushady
- https://github.com/UR4N0-235/XWindowSystem_Screenshoter
