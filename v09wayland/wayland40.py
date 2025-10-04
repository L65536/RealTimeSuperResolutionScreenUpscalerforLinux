# examples/30-main-window.py
# Copyright (c) 2024-2025 Graham R King
# Licensed under the MIT License. See LICENSE file for details.

import sys
import sys
import os
import numpy

import wayland
from wayland.client import wayland_class
from wayland.client.memory_pool import SharedMemoryPool

import ctypes
LibName = '../nvfbc/nvfbc-pipewire.so'
LibName = 'nvfbc-pipewire.so'
AbsLibPath = os.path.dirname(os.path.abspath(__file__)) + os.path.sep + LibName
cap = ctypes.CDLL(AbsLibPath)

cap.init.argtypes = None
cap.init.restype = ctypes.c_int
cap.capture.argtypes = (ctypes.c_int,)
cap.capture.restype = ctypes.c_void_p # without this, 64 bit address got truncated to 32 bit (ctypes default action) => segmentation fault
cap.destroy.argtypes = None
cap.destroy.restype = ctypes.c_int

cap.init()


@wayland_class("xdg_wm_base")
class WmBase(wayland.xdg_wm_base):

   # Respond to compositor pings.
   def on_ping(self, serial):
       self.pong(serial)


@wayland_class("xdg_surface")
class Surface(wayland.xdg_surface):

   def __init__(self, app):
       super().__init__(app=app)
       self.app = app

   def on_configure(self, serial):
       self.ack_configure(serial)
       self.app.redraw()


@wayland_class("wl_shm")
class Shm(wayland.wl_shm):

   def __init__(self, app):
       super().__init__(app=app)
       self.pool = SharedMemoryPool(self)


@wayland_class("wl_registry")
class Registry(wayland.wl_registry):

   def __init__(self, app):
       super().__init__(app=app)
       self.wl_shm = None
       self.xdg_wm_base = None
       self.wl_compositor = None

   def on_global(self, name, interface, version):
       # Bind any interfaces that match our properties
       if hasattr(self, interface):
           setattr(self, interface, self.bind(name, interface, version))


@wayland_class("wl_display")
class Display(wayland.wl_display):

   def on_error(self, object_id, code, message):
       # Handle fatal errors
       print(f"Error: {object_id} {code} {message}")
       sys.exit(1)


class MainWindow:

   def __init__(self):
        self.running = True
        self.surface = None

        # Load image and set initial window size
        self.width, self.height = 1920, 1080
        # Initialize Wayland connection
        self.display = Display(app=self)
        self.registry = self.display.get_registry()

   def on_configure(self, width, height, states):
       """Handle window resize events."""
       if width and height:
           self.width, self.height = width, height
           self.redraw()

   def assert_initialised(self):
       """Initialize Wayland interfaces when available."""
       if self.surface:
           return True

       # Check if all required interfaces are available
       if all([self.registry.wl_compositor, self.registry.wl_shm, self.registry.xdg_wm_base]):
           # Create surface and configure window
           self.surface = self.registry.wl_compositor.create_surface()
           xdg_surface = self.registry.xdg_wm_base.get_xdg_surface(self.surface)
           toplevel = xdg_surface.get_toplevel()

           # Set up event handlers
           toplevel.events.configure += self.on_configure
           toplevel.events.close += lambda: setattr(self, 'running', False)

           # Commit initial surface
           self.surface.commit()
       return False

   def redraw(self):
       # Create buffer for current surface size
       buffer, ptr = self.registry.wl_shm.pool.create_buffer(self.width, self.height)

       # Copy image to buffer
       addr = cap.capture(1)
       dimension = (ctypes.c_ubyte*4).from_address(addr)
       clientW = dimension[0]+dimension[1]*256 # extra width height from the first pixel
       clientH = dimension[2]+dimension[3]*256 # extra width height from the first pixel
       buf = (ctypes.c_ubyte*4*clientW*clientH).from_address(addr)
       #bitmap = numpy.frombuffer(buf, dtype=numpy.uint32)
       #print(clientW, clientH)

       #self.image.copy_to_buffer(ptr, self.width, self.height)
       pixels = ctypes.cast(ptr, ctypes.POINTER(ctypes.c_uint32))
       b = ctypes.cast(addr, ctypes.POINTER(ctypes.c_uint32))
       ctypes.memmove(pixels, b, clientW * clientH * 4)

       # Commit buffer to surface/
       self.surface.attach(buffer, 0, 0)
       self.surface.damage_buffer(0, 0, self.width, self.height)
       self.surface.commit()

   def run(self):
       # Main event loop
       while self.running:
           self.assert_initialised()
           self.display.dispatch_timeout(1/25)  # 25 FPS

if __name__ == "__main__":
   MainWindow().run()
