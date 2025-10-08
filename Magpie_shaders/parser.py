# Parse MagpieFX shader directives
# https://github.com/Blinue/Magpie/wiki/MagpieFX%20(EN)
shader = "CuNNy-veryfast-NVL.hlsl"

with open(shader, 'r') as fp: s = fp.read()
lines = s.splitlines()
total = len(lines)

for index, line in enumerate(lines):  
    
    T=[]
    if "Texture2D T" in line: 
        print(f"{index}/{total} {line}")
        line = line.replace("Texture2D T", "")
        line = line.replace(";", "")
        i = int(line)
        print(i)
           
    if "//!WIDTH" in line: 
        print(f"{index}/{total} {line}")
        line = line.replace("//!WIDTH INPUT_WIDTH", "")
        i = len(line)
        print(i,line)
        
    elif "//!HEIGHT" in line: 
        print(f"{index}/{total} {line}")
        line = line.replace("//!HEIGHT INPUT_HEIGHT", "")        
        i = len(line)
        print(i,line)                    
        
    elif "//!PASS" in line: 
        print(f"{index}/{total} {line}")
        line = line.replace("//!PASS", "")        
        i = int(line)
        print(i)
        
    elif "//!BLOCK_SIZE" in line: 
        print(f"{index}/{total} {line}")
        line = line.replace("//!BLOCK_SIZE", "")     
        i = int(line)
        print(i)    
            
    if "//!IN" in line: 
        print(f"{index}/{total} {line}")
        line = line.replace("//!IN", "").replace(" ", "").split(',')    
        print(line)    
        
    if "//!OUT" in line: 
        print(f"{index}/{total} {line}")
        line = line.replace("//!OUT", "").replace(" ", "").split(',')      
        print(line)    
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

#if "//!TEXTURE" in line: print(f"{index}/{total} {line}")
#if "//!FORMAT" in line: print(f"{index}/{total} {line}")
#if "//!NUM_THREADS" in line: print(f"{index}/{total} {line}")