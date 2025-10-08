# Parse MagpieFX shader directives
# https://github.com/Blinue/Magpie/wiki/MagpieFX%20(EN)
shader = "CuNNy-veryfast-NVL.hlsl"

with open(shader, 'r') as fp: s = fp.read()
lines = s.splitlines()
total = len(lines)

for index, item in enumerate(lines):    
    if "Texture2D" in item: print(f"{index}/{total} {item}")
    if "//!FORMAT" in item: print(f"{index}/{total} {item}")
    if "//!HEIGHT" in item: print(f"{index}/{total} {item}")
    if "//!WIDTH" in item: print(f"{index}/{total} {item}")
    if "//!TEXTURE" in item: print(f"{index}/{total} {item}")
    
    if "//!PASS" in item: print(f"{index}/{total} {item}")
    if "//!BLOCK_SIZE" in item: print(f"{index}/{total} {item}")
    if "//!NUM_THREADS" in item: print(f"{index}/{total} {item}")
    if "//!IN" in item: print(f"{index}/{total} {item}")
    if "//!OUT" in item: print(f"{index}/{total} {item}")
    
"""        
//!TEXTURE
//!WIDTH INPUT_WIDTH
//!HEIGHT INPUT_HEIGHT
//!FORMAT R8G8B8A8_UNORM
Texture2D T3;

//!PASS 1
//!DESC in (1x8)
//!BLOCK_SIZE 8
//!NUM_THREADS 64
//!IN INPUT
//!OUT T0, T1
"""