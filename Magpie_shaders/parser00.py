# Class for loading Magpie HLSL shaders

# Parse MagpieFX shader directives
# https://github.com/Blinue/Magpie/wiki/MagpieFX%20(EN)

# Only tested on three CuNNy2 shaders
# [Assumptions] Output ratio is 2x2, NUM_THREADS handled in HLSL, FORMAT is R8G8B8A8_UNORM
# Still rely on Magpie's EffectCompiler.cpp to generate HLSL codes for individual passes externally.

import struct
import compushady
import compushady.formats
import compushady.shaders.hlsl

class magpie_shader:
    def __init__(self, shader_file):
        self.parse(shader_file)

    def parse(self, shader_file, verbose=1):
        print('Parsing shader file =', shader_file)
        with open(shader_file, 'r') as fp: file = fp.read()
        lines = file.splitlines()
        # total = len(lines)
        # print(f"{index}/{total} {line}")

        self.parsed_T_ratio = [] # intermediate textures T ratio (w, h)
        self.parsed_BLOCK_SIZE = []
        self.parsed_IN = []
        self.parsed_OUT = []
        wr = 0  # texture width ratio, redundant for error checks
        hr = 0  # texture width ratio, redundant for error checks
        format = 'None'

        for index, line in enumerate(lines):

            if "Texture2D T" in line:
                line = line.replace("Texture2D T", "").replace(";", "")
                i = int(line)
                if verbose: print(f"T{i} ratio = {wr}x{hr} {format}")
                self.parsed_T_ratio.append((wr,hr))
                wr = 0
                hr = 0
                format = 'None'

            elif "//!WIDTH" in line:
                line = line.replace("//!WIDTH INPUT_WIDTH", "").replace("*", "")
                i = len(line)
                if i>0: wr=int(line)
                else: wr=1 # print(wr, line)

            elif "//!HEIGHT" in line:
                line = line.replace("//!HEIGHT INPUT_HEIGHT", "").replace("*", "")
                i = len(line)
                if i>0: hr=int(line)
                else: hr=1 # print(hr, line)

            elif "//!FORMAT" in line:
                format = line.replace("//!FORMAT ", "")

            elif "//!PASS" in line:
                line = line.replace("//!PASS", "")
                pass_max = int(line)

            elif "//!BLOCK_SIZE" in line:
                line = line.replace("//!BLOCK_SIZE", "")
                i = int(line)
                if verbose: print('PASS', pass_max, 'BLOCK_SIZE', i)
                self.parsed_BLOCK_SIZE.append(i)

            elif "//!IN" in line:
                line = line.replace("//!IN", "").replace(" ", "").split(',')
                if verbose: print('PASS', pass_max, 'IN', line)
                self.parsed_IN.append(line)

            elif "//!OUT" in line:
                line = line.replace("//!OUT", "").replace(" ", "").split(',')
                if verbose: print('PASS', pass_max, 'OUT', line)
                self.parsed_OUT.append(line)

        if verbose: 
            print(self.parsed_T_ratio)
            print(self.parsed_BLOCK_SIZE)
            print(self.parsed_IN)
            print(self.parsed_OUT)
            print('Total passes =', pass_max, '\n')

if __name__ == "__main__":
    s1 = magpie_shader("CuNNy-veryfast-NVL.hlsl")
    s2 = magpie_shader("CuNNy-faster-NVL.hlsl")
    s3 = magpie_shader("CuNNy-fast-NVL.hlsl")
