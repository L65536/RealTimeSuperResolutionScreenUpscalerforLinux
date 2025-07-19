INPUT_FOLDER=r"c:\source_folder"
OUTPUT_FOLDER=r"c:\destination_folder"

# Requirements: pip install compushady pillow numpy
# Requirements: libvulkan-dev and libx11-dev on Debian Linux
from compushady import (
    Compute, Buffer, Texture2D, HEAP_UPLOAD, HEAP_READBACK,
    Sampler, SAMPLER_FILTER_POINT, SAMPLER_FILTER_LINEAR, SAMPLER_ADDRESS_MODE_CLAMP, SAMPLER_ADDRESS_MODE_WRAP, SAMPLER_ADDRESS_MODE_MIRROR,
    )
from compushady.formats import R8G8B8A8_UNORM
from compushady.shaders import hlsl
from PIL import Image
import numpy as np
import struct
import time
import os

BLOCK_SIZE=64
def pad_margin_to_block_size(pil_img, color=(0,0,0)):
    width, height = pil_img.size
    new_width = (width+BLOCK_SIZE-1)//BLOCK_SIZE*BLOCK_SIZE
    new_height = (height+BLOCK_SIZE-1)//BLOCK_SIZE*BLOCK_SIZE
    result = Image.new(pil_img.mode, (new_width, new_height), color)
    result.paste(pil_img, (0, 0))
    return result

def upsacle_a_file(filename):
    # DEBUG print(INPUT_FOLDER+"\\"+filename)
    # DEBUG print(OUTPUT_FOLDER+"\\"+filename)
    input=INPUT_FOLDER+"\\"+filename
    
    image = Image.open(input).convert("RGBA")
    height0, width0 = image.height, image.width
    print (f"{filename} {width0}x{height0}") # works with 1920x1080 1280x720 640x480 but not 800x600? pad/trim to block size 8x8 16x16?
    
    image=pad_margin_to_block_size(image)
    height, width = image.height, image.width
    # DEBUG print (f"{filename} {width}x{height} padded") 
    
    img_data = np.array(image)

    # Shader definitions
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

    INPUT = Texture2D(width, height, R8G8B8A8_UNORM)
    OUTPUT = Texture2D(width*2, height*2, R8G8B8A8_UNORM)
    OUTPUT2 = Texture2D(width*2, height*2, R8G8B8A8_UNORM)
    T0 = Texture2D(width, height, R8G8B8A8_UNORM)
    T1 = Texture2D(width, height, R8G8B8A8_UNORM)
    T2 = Texture2D(width, height, R8G8B8A8_UNORM)
    T3 = Texture2D(width, height, R8G8B8A8_UNORM)

    staging_buffer = Buffer(INPUT.size, HEAP_UPLOAD)
    staging_buffer.upload(img_data)
    staging_buffer.copy_to(INPUT)

    # Multi pass shaders
    with open("parsed/CuNNy-veryfast-NVL_Pass1.hlsl", 'r') as fp: shader1 = fp.read()
    with open("parsed/CuNNy-veryfast-NVL_Pass2.hlsl", 'r') as fp: shader2 = fp.read()
    with open("parsed/CuNNy-veryfast-NVL_Pass3.hlsl", 'r') as fp: shader3 = fp.read()
    with open("parsed/CuNNy-veryfast-NVL_Pass4.hlsl", 'r') as fp: shader4 = fp.read()
    s1=hlsl.compile(shader1)
    s2=hlsl.compile(shader2)
    s3=hlsl.compile(shader3)
    s4=hlsl.compile(shader4)

    CB1 = Buffer(40, HEAP_UPLOAD)
    CB2 = Buffer(40, HEAP_UPLOAD)
    CB3 = Buffer(40, HEAP_UPLOAD)
    CB4 = Buffer(40, HEAP_UPLOAD)
    CB1.upload(struct.pack('iiiiffffff', width, height, width, height, 1.0/width, 1.0/height, 1.0/width, 1.0/height, 1.0, 1.0))
    CB2.upload(struct.pack('iiiiffffff', width, height, width, height, 1.0/width, 1.0/height, 1.0/width, 1.0/height, 1.0, 1.0))
    CB3.upload(struct.pack('iiiiffffff', width, height, width, height, 1.0/width, 1.0/height, 1.0/width, 1.0/height, 1.0, 1.0))
    CB4.upload(struct.pack('iiiiffffff', width, height, width*2, height*2, 1.0/width, 1.0/height, 1.0/width/2, 1.0/height/2, 2.0, 2.0))

    start_time = time.time() # process_time() is for CPU ONLY
    compute1 = Compute(s1, cbv=[CB1], srv=[INPUT], uav=[T0,T1], samplers=[SP,SL])
    compute1.dispatch((width+7)//8, (height+7)//8, 1)
    compute2 = Compute(s2, cbv=[CB2], srv=[T0,T1], uav=[T2,T3], samplers=[SP,SL])
    compute2.dispatch((width+7)//8, (height+7)//8, 1)
    compute3 = Compute(s3, cbv=[CB3], srv=[T2,T3], uav=[T0], samplers=[SP,SL])
    compute3.dispatch((width+7)//8, (height+7)//8, 1)
    compute4 = Compute(s4, cbv=[CB4], srv=[INPUT,T0], uav=[OUTPUT2], samplers=[SP,SL])
    compute4.dispatch((width*2+15)//16, (height*2+15)//16, 1) # (OUPUT_size+block_size-1)//block_size
    ms=(time.time() - start_time)*1000
    # DEBUG print(f"Shader compute time: {int(ms)} ms") # ~20ms for 1080p

    # Save output file
    readback_buffer = Buffer(OUTPUT2.size, HEAP_READBACK)
    OUTPUT2.copy_to(readback_buffer)
    image = Image.frombuffer('RGBA', (OUTPUT2.width, OUTPUT2.height), readback_buffer.readback())
    image=image.crop((0,0,width0*2, height0*2))
    # DEBUG image.show()
  
    output=OUTPUT_FOLDER+"\\"+filename    
    image_rgb = image.convert('RGB')
    image_rgb.save(output, quality=98)

# Load images from folder, upscale and save to target
filelist = []
extsion = [".jpeg",".jpg",".png"]
for f in os.listdir(INPUT_FOLDER):
    ext = os.path.splitext(f)[1]
    if ext.lower() in extsion: filelist.append(f)
# DEBUG print(filelist)

print(f"Upscaling {len(filelist)} files from {INPUT_FOLDER} and save to {OUTPUT_FOLDER} ...")
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
for f in filelist:
    upsacle_a_file(f)
