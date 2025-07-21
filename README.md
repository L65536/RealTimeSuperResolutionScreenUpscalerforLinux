# Introduction
This project contains simple Python scripts that magnify/upscale the screens of apps/games in realtime. 
Using current Super Resolution AI models for improved perceived upscaling quality.
GPUs and compute shaders are used to speed up the computation.
This process is similar to Nvidia's DLSS-SR and AMD's FSR series.
Other similar software projects include Magpie and Lossless Scaling.

# Ver 0.1 Summary
This project uses the HLSL shader files taken straight from the Magpie/CuNNy project.
A fast CNN model called CuNNy-veryfast-NVL is used (It's Similar to Anime4k).
This model provides good balance of text and graphic upscaling quality and speed.
Core of this project contains around 200 lines of Python codes plus external HLSL shader files.

# Ver 0.1 Functionalities
- X2 upscaling of any runing window to a seperate window in Linux.
- [GUI] Thumbnailed target window selector at start up. 

# Ver 0.1 Limitations
- No input passthrough support (need to run the original window side by side or with multi monitor setup).
- Fixed X2 magnification. No full screen support yet.
- Does not handle minimized windows. (Plain blue thumbnail is shown)
- Slow FPS for large target window sizes. 
Current background screen capture and display function overhead are magnitude slower than the core shader computations by GPUs.
Alternative screen capture and display acceleration approaches are required.
- [BUG] Wrong display coordinates if the target window is too large (eg. desktop or taskbar at full screen width)

# Acknowledgement and special thanks
This project contains codes based on the following projects/libraries:
- https://github.com/Blinue/Magpie
- https://github.com/funnyplanter/CuNNy
- https://github.com/rdeioris/compushady
- https://github.com/UR4N0-235/XWindowSystem_Screenshoter
