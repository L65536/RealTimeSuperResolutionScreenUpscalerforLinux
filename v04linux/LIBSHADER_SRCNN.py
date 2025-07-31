import struct
from compushady import (
    Compute, Buffer, Texture2D, HEAP_UPLOAD, HEAP_READBACK,
    Sampler, SAMPLER_FILTER_POINT, SAMPLER_FILTER_LINEAR, SAMPLER_ADDRESS_MODE_CLAMP, SAMPLER_ADDRESS_MODE_WRAP, SAMPLER_ADDRESS_MODE_MIRROR,
    )
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

with open("CuNNy-veryfast-NVL_Pass1.hlsl", 'r') as fp: shader1 = fp.read()
with open("CuNNy-veryfast-NVL_Pass2.hlsl", 'r') as fp: shader2 = fp.read()
with open("CuNNy-veryfast-NVL_Pass3.hlsl", 'r') as fp: shader3 = fp.read()
with open("CuNNy-veryfast-NVL_Pass4.hlsl", 'r') as fp: shader4 = fp.read()
s1 = hlsl.compile(shader1)
s2 = hlsl.compile(shader2)
s3 = hlsl.compile(shader3)
s4 = hlsl.compile(shader4)

def init_buffer(width, height):
    global staging_buffer, readback_buffer
    global INPUT, OUTPUT, T0, T1, T2, T3, CB1, CB2, CB3, CB4    
        
    INPUT = Texture2D(width, height, R8G8B8A8_UNORM)
    OUTPUT = Texture2D(width*2, height*2, R8G8B8A8_UNORM)
    staging_buffer = Buffer(INPUT.size, HEAP_UPLOAD)
    # readback_buffer = Buffer(OUTPUT.size, HEAP_READBACK) # wrong size
    readback_buffer = Buffer((OUTPUT.size+OUTPUT.row_pitch-1)//OUTPUT.row_pitch*OUTPUT.row_pitch, HEAP_READBACK) 
    # Adjust buffer size to match the correct row_pitch, otherwise size of last line mismatch
    # print(f"{OUTPUT.width}/{OUTPUT.row_pitch//4}x{OUTPUT.height}={OUTPUT.row_pitch*OUTPUT.height}/{OUTPUT.size}")

    T0 = Texture2D(width, height, R8G8B8A8_UNORM)
    T1 = Texture2D(width, height, R8G8B8A8_UNORM)
    T2 = Texture2D(width, height, R8G8B8A8_UNORM)
    T3 = Texture2D(width, height, R8G8B8A8_UNORM)
    CB1 = Buffer(40, HEAP_UPLOAD)
    CB2 = Buffer(40, HEAP_UPLOAD)
    CB3 = Buffer(40, HEAP_UPLOAD)
    CB4 = Buffer(40, HEAP_UPLOAD)
    CB1.upload(struct.pack('iiiiffffff', width, height, width, height, 1.0/width, 1.0/height, 1.0/width, 1.0/height, 1.0, 1.0))
    CB2.upload(struct.pack('iiiiffffff', width, height, width, height, 1.0/width, 1.0/height, 1.0/width, 1.0/height, 1.0, 1.0))
    CB3.upload(struct.pack('iiiiffffff', width, height, width, height, 1.0/width, 1.0/height, 1.0/width, 1.0/height, 1.0, 1.0))
    CB4.upload(struct.pack('iiiiffffff', width, height, width*2, height*2, 1.0/width, 1.0/height, 1.0/width/2, 1.0/height/2, 2.0, 2.0))

def compute(buffer, width, height):
    #staging_buffer.upload(buffer) # incorrect row_pitch
    staging_buffer.upload2d(buffer, INPUT.row_pitch, INPUT.width, INPUT.height, get_pixel_size(R8G8B8A8_UNORM))
    staging_buffer.copy_to(INPUT)
    compute1 = Compute(s1, cbv=[CB1], srv=[INPUT], uav=[T0,T1], samplers=[SP,SL])
    compute1.dispatch((width+7)//8, (height+7)//8, 1)
    compute2 = Compute(s2, cbv=[CB2], srv=[T0,T1], uav=[T2,T3], samplers=[SP,SL])
    compute2.dispatch((width+7)//8, (height+7)//8, 1)
    compute3 = Compute(s3, cbv=[CB3], srv=[T2,T3], uav=[T0], samplers=[SP,SL])
    compute3.dispatch((width+7)//8, (height+7)//8, 1)
    compute4 = Compute(s4, cbv=[CB4], srv=[INPUT,T0], uav=[OUTPUT], samplers=[SP,SL])
    compute4.dispatch((width*2+15)//16, (height*2+15)//16, 1) # (OUPUT_size+block_size-1)//block_size
    OUTPUT.copy_to(readback_buffer)