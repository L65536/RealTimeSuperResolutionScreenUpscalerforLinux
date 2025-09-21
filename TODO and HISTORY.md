# WIP
- [Shader] FP16 support
- [Shader] Improve cascade shaders speed by elimiting unnecessary intermediate buffer I/O
- [Testing] Gracefully exit/clean up for compushady/capture/qt(pyside6).
- [Capture/Windows/Linux] load/copy captured texture within VRAM (interop, check stride issue)

# ON HOLD
- [Capture/Linux] use shader to convert XPixMap. => use NVFBC instead
- [Linux] xshm testing, no speed improvement observed yet.  => use NVFBC instead

# HISTORY
- [Windows] Implement Graphics Capture using PyWinRT https://github.com/pywinrt/pywinrt
- [SHADER] Row pitch now correctly implemented for output buffer sizes and texture upload 2d function() => now support all input resolutions.
- [GUI] Implement cascade shader for shrinking fit to screen. This should solve most undefined oversize behavior.(for v0.3 only)
- [Windows] Flickering when capturing, both original and captured.  => fixed with new capture method.
- [Linux] Improve capture with ctypes. => 2x~3x faster
- Optimize threads/queues/callbacks to reduce frame latency.
- [v06 Windows/Linux] Display swapchain and copy output texture within VRAM.
- [v07 Windows/LInux] Keyboard/mouse input pass through by transparent overlay window.
- [v07 win/g40] [Capture/Windows] improve cropping speed with slack/lazy cropping (cut out title bar only)
- [v07 win/g43] improve out-of-bound mouse position => warp to the other side.
- [v08 Linux] Compushady/Swapchain not as fast as expected when compared to Windows => NVFBC reduced overall CPU load significantly.
- [Capture/Linux] NVFBC with NVFBC_BACKEND_DIRECT => Unable to send DBus message => Only works with vulkan apps




