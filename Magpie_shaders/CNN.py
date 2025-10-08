import struct
import compushady
import compushady.formats
import compushady.shaders.hlsl
#from compushady import (Compute, Buffer, Texture2D, HEAP_UPLOAD, HEAP_READBACK)

SP = compushady.Sampler(
        filter_min=compushady.SAMPLER_FILTER_POINT,
        filter_mag=compushady.SAMPLER_FILTER_POINT,
        #address_mode_u=compushady.SAMPLER_ADDRESS_MODE_WRAP,
        #address_mode_v=compushady.SAMPLER_ADDRESS_MODE_CLAMP,
        #address_mode_w=compushady.SAMPLER_ADDRESS_MODE_MIRROR,
)
SL = compushady.Sampler(
        filter_min=compushady.SAMPLER_FILTER_LINEAR,
        filter_mag=compushady.SAMPLER_FILTER_LINEAR,
        #address_mode_u=compushady.SAMPLER_ADDRESS_MODE_WRAP,
        #address_mode_v=compushady.SAMPLER_ADDRESS_MODE_CLAMP,
        #address_mode_w=compushady.SAMPLER_ADDRESS_MODE_MIRROR, 
)

shader = "CuNNy-veryfast-NVL"
with open("FP16.hlsl", 'r') as fp: fp16 = fp.read()
with open("FP32.hlsl", 'r') as fp: fp32 = fp.read()
with open(shader+"_Pass1.hlsl", 'r') as fp: shader1 = fp.read()
with open(shader+"_Pass2.hlsl", 'r') as fp: shader2 = fp.read()
with open(shader+"_Pass3.hlsl", 'r') as fp: shader3 = fp.read()
with open(shader+"_Pass4.hlsl", 'r') as fp: shader4 = fp.read()
s1 = compushady.shaders.hlsl.compile(fp32+shader1, entry_point="__M")
s2 = compushady.shaders.hlsl.compile(fp32+shader2, entry_point="__M")
s3 = compushady.shaders.hlsl.compile(fp32+shader3, entry_point="__M")
s4 = compushady.shaders.hlsl.compile(fp32+shader4, entry_point="__M")

def init_buffer(width, height):
    global staging_buffer, readback_buffer
    global INPUT, OUTPUT, T0, T1, T2, T3, CB1, CB2, CB3, CB4
    global w, h
    w = width
    h = height
    INPUT = compushady.Texture2D(w, h, compushady.formats.R8G8B8A8_UNORM)
    OUTPUT = compushady.Texture2D(w*2, h*2, compushady.formats.R8G8B8A8_UNORM)
    staging_buffer = compushady.Buffer(INPUT.size, compushady.HEAP_UPLOAD)    
    readback_buffer = compushady.Buffer((OUTPUT.size+OUTPUT.row_pitch-1)//OUTPUT.row_pitch*OUTPUT.row_pitch, compushady.HEAP_READBACK)
    # readback_buffer = Buffer(OUTPUT.size, HEAP_READBACK) # wrong size
    # Adjust buffer size to match the correct row_pitch, otherwise size of last line mismatch
    # print(f"{OUTPUT.width}/{OUTPUT.row_pitch//4}x{OUTPUT.height}={OUTPUT.row_pitch*OUTPUT.height}/{OUTPUT.size}")

    T0 = compushady.Texture2D(w, h, compushady.formats.R8G8B8A8_UNORM)
    T1 = compushady.Texture2D(w, h, compushady.formats.R8G8B8A8_UNORM)
    T2 = compushady.Texture2D(w, h, compushady.formats.R8G8B8A8_UNORM)
    T3 = compushady.Texture2D(w, h, compushady.formats.R8G8B8A8_UNORM)
    CB1 = compushady.Buffer(40, compushady.HEAP_UPLOAD)
    CB2 = compushady.Buffer(40, compushady.HEAP_UPLOAD)
    CB3 = compushady.Buffer(40, compushady.HEAP_UPLOAD)
    CB4 = compushady.Buffer(40, compushady.HEAP_UPLOAD)
    CB1.upload(struct.pack('iiiiffffff', w, h, w, h, 1.0/w, 1.0/h, 1.0/w, 1.0/h, 1.0, 1.0))
    CB2.upload(struct.pack('iiiiffffff', w, h, w, h, 1.0/w, 1.0/h, 1.0/w, 1.0/h, 1.0, 1.0))
    CB3.upload(struct.pack('iiiiffffff', w, h, w, h, 1.0/w, 1.0/h, 1.0/w, 1.0/h, 1.0, 1.0))
    CB4.upload(struct.pack('iiiiffffff', w, h, w*2, h*2, 1.0/w, 1.0/h, 1.0/w/2, 1.0/h/2, 2.0, 2.0))

def upload(buffer):    
    pixel_size = compushady.formats.get_pixel_size(compushady.formats.R8G8B8A8_UNORM)
    staging_buffer.upload2d(buffer, INPUT.row_pitch, INPUT.width, INPUT.height, pixel_size)
    staging_buffer.copy_to(INPUT)

def compute():
    compute1 = compushady.Compute(s1, cbv=[CB1], srv=[INPUT], uav=[T0,T1], samplers=[SP,SL])
    compute1.dispatch((w+7)//8, (h+7)//8, 1)
    compute2 = compushady.Compute(s2, cbv=[CB2], srv=[T0,T1], uav=[T2,T3], samplers=[SP,SL])
    compute2.dispatch((w+7)//8, (h+7)//8, 1)
    compute3 = compushady.Compute(s3, cbv=[CB3], srv=[T2,T3], uav=[T0], samplers=[SP,SL])
    compute3.dispatch((w+7)//8, (h+7)//8, 1)
    compute4 = compushady.Compute(s4, cbv=[CB4], srv=[INPUT,T0], uav=[OUTPUT], samplers=[SP,SL])
    compute4.dispatch((w*2+15)//16, (h*2+15)//16, 1) # (OUPUT_size+block_size-1)//block_size

def download():
    OUTPUT.copy_to(readback_buffer)

if __name__ == "__main__":
    from PIL import Image
    import time
    import numpy
    import compushady

    image = Image.open("test.jpg").convert("RGBA")
    h, w = image.height, image.width
    img_data = numpy.array(image)

    DISPLAY = 1
    if(DISPLAY):
        import pyglet
        window = pyglet.window.Window(w*2,h*2, caption='Display')

    init_buffer(w, h)

    t = time.perf_counter()
    upload(img_data)
    compute()
    print("Close all terminal windows fist for accurate results.")
    t=(time.perf_counter() - t)*1000
    print(f"{t:.2f} ms")

    if(DISPLAY):
        @window.event
        def on_draw():
            download()
            img = pyglet.image.ImageData(OUTPUT.row_pitch//4, OUTPUT.height, "RGBA", readback_buffer.readback(), pitch=-OUTPUT.row_pitch)
            img.blit(0, 0)

        pyglet.app.run()
