import struct
from compushady import (
    Compute, Buffer, Texture2D, HEAP_UPLOAD, HEAP_READBACK,
    Sampler, SAMPLER_FILTER_POINT, SAMPLER_FILTER_LINEAR, SAMPLER_ADDRESS_MODE_CLAMP, SAMPLER_ADDRESS_MODE_WRAP, SAMPLER_ADDRESS_MODE_MIRROR,)
from compushady.formats import R8G8B8A8_UNORM, get_pixel_size
from compushady.shaders import hlsl

SP = Sampler(
        filter_min=SAMPLER_FILTER_POINT,
        filter_mag=SAMPLER_FILTER_POINT,
        address_mode_u=SAMPLER_ADDRESS_MODE_WRAP,
        address_mode_v=SAMPLER_ADDRESS_MODE_CLAMP,
        address_mode_w=SAMPLER_ADDRESS_MODE_CLAMP,
)
SL = Sampler(
        filter_min=SAMPLER_FILTER_LINEAR,
        filter_mag=SAMPLER_FILTER_LINEAR,
        address_mode_u=SAMPLER_ADDRESS_MODE_WRAP,
        address_mode_v=SAMPLER_ADDRESS_MODE_CLAMP,
        address_mode_w=SAMPLER_ADDRESS_MODE_CLAMP,
)

with open("Bicubic.hlsl", 'r') as fp: shader = fp.read()
s1 = hlsl.compile(shader)

def compute(buffer, width, height, output_width=0, output_height=0):
    global staging_buffer, readback_buffer
    global INPUT, OUTPUT, CB0
    if output_width == 0: output_width = width*2
    if output_height == 0: output_height = height*2

    INPUT = Texture2D(width, height, R8G8B8A8_UNORM)
    OUTPUT = Texture2D(output_width , output_height, R8G8B8A8_UNORM)
    staging_buffer = Buffer(INPUT.size, HEAP_UPLOAD)

    # readback_buffer = Buffer(OUTPUT.size, HEAP_READBACK) # wrong size
    readback_buffer = Buffer((OUTPUT.size+OUTPUT.row_pitch-1)//OUTPUT.row_pitch*OUTPUT.row_pitch, HEAP_READBACK)   
    # print(f"{OUTPUT.width}/{OUTPUT.row_pitch//4}x{OUTPUT.height}={OUTPUT.row_pitch*OUTPUT.height}/{OUTPUT.size}")

    ratio = float(output_width/width)
    CB0 = Buffer(40, HEAP_UPLOAD)
    CB0.upload(struct.pack('iiiiffffff', width, height, output_width, output_height, 1.0/width, 1.0/height, 1.0/output_width, 1.0/output_height, 2.0, 2.0))

    # def shadercompute(buffer, width, height):
    #staging_buffer.upload(buffer) # incorrect row_pitch
    staging_buffer.upload2d(buffer, INPUT.row_pitch, INPUT.width, INPUT.height, get_pixel_size(R8G8B8A8_UNORM))    
    staging_buffer.copy_to(INPUT)

    compute = Compute(s1, cbv=[CB0], srv=[INPUT], uav=[OUTPUT], samplers=[SP])

    compute.dispatch((width+7)//8, (height+7)//8, 1) # (OUPUT_size+block_size-1)//block_size
    OUTPUT.copy_to(readback_buffer)