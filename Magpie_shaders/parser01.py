# Class for loading Magpie HLSL shaders

# Parse MagpieFX shader directives
# https://github.com/Blinue/Magpie/wiki/MagpieFX%20(EN)

# Generate compilable HLSL codes for individual passes locally without relying on Magpie's EffectCompiler.cpp

# Only tested on three CuNNy2 shaders
# [Assumptions] Output ratio is 2x2, intermediate texture ratio is 1x1, NUM_THREADS handled in HLSL, FORMAT is R8G8B8A8_UNORM(FP32)/...(FP16)

import struct
import compushady
import compushady.formats
import compushady.shaders.hlsl

class magpie_shader:
    def __init__(self, shader_file):
        self.parse(shader_file)

    def parse(self, shader_file, verbose=1, vv=1):
        print('Parsing shader file =', shader_file)
        with open(shader_file, 'r') as fp: file = fp.read()
        lines = file.splitlines()
        # total = len(lines)
        # print(f"{index}/{total} {line}")

        self.parsed_T_ratio = [] # intermediate textures T ratio (w, h), always 1x1
        self.parsed_BLOCK_SIZE = [] # always [8 ... 8, 16]
        self.parsed_NUM_THREADS = [] # always 64
        self.parsed_IN = []
        self.parsed_OUT = []
        self.pass_max = 0
        start_point = []
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
                self.pass_max = int(line)
                start_point.append(index)

            elif "//!BLOCK_SIZE" in line:
                line = line.replace("//!BLOCK_SIZE", "")
                i = int(line)
                if verbose: print('PASS', self.pass_max, 'BLOCK_SIZE', i)
                self.parsed_BLOCK_SIZE.append(i)

            elif "//!NUM_THREADS" in line:
                line = line.replace("//!NUM_THREADS", "")
                i = int(line)
                if verbose: print('PASS', self.pass_max, 'NUM_THREADS', i)
                self.parsed_NUM_THREADS.append(i)

            elif "//!IN" in line:
                line = line.replace("//!IN", "").replace(" ", "").split(',')
                if verbose: print('PASS', self.pass_max, 'IN', line)
                self.parsed_IN.append(line)

            elif "//!OUT" in line:
                line = line.replace("//!OUT", "").replace(" ", "").split(',')
                if verbose: print('PASS', self.pass_max, 'OUT', line)
                self.parsed_OUT.append(line)

        if verbose:
            print(self.parsed_T_ratio)
            print(self.parsed_BLOCK_SIZE)
            print(self.parsed_NUM_THREADS)
            print(self.parsed_IN)
            print(self.parsed_OUT)
            print(start_point, '/', len(lines))
            print('Total passes =', self.pass_max, '\n')

        # Extract individual HLSL passes
        pass_body = []
        body = ""
        current_pass = 0
        start_point.append(len(lines))
        for index, line in enumerate(lines):
            # print (index, len(lines), start_point[current_pass+1]-1, current_pass)
            if start_point[current_pass] <= index < start_point[current_pass+1]:
                body = body + line + "\n"
            if index == start_point[current_pass+1]-1:
                pass_body.append(body)
                body = ""
                if current_pass < self.pass_max: current_pass+=1

        # macros.hlsl read from file
        with open("macros.hlsl", 'r') as fp: macros = fp.read() #print(macros)

        # Generate individual HLSL texture and entry function definition
        header_textures = []
        for i in range(self.pass_max):
            n = 0
            tt = ""
            for s in self.parsed_IN[i]:
                if s == 'INPUT':
                    tt += f"Texture2D<MF4> INPUT : register(t{n});\n"
                else:
                    t = int(s.replace("T", ""))
                    tt += f"Texture2D<MF4> T{t} : register(t{n});\n"
                n+=1

            n = 0
            for s in self.parsed_OUT[i]:
                if s == 'OUTPUT':
                    tt += f"RWTexture2D<unorm MF4> OUTPUT : register(u{n});\n"
                else:
                    t = int(s.replace("T", ""))
                    tt += f"RWTexture2D<unorm MF4> T{t} : register(u{n});\n"
                n+=1
            header_textures.append(tt)

        footer_main = []
        f1 = "[numthreads(64, 1, 1)]\n"
        f2 = "void __M(uint3 tid : SV_GroupThreadID, uint3 gid : SV_GroupID) {Pass"
        f3 = "((gid.xy << 3), tid);}\n"
        for i in range(self.pass_max): footer_main.append(f1+f2+str(i+1)+f3) #print(footer_main)

        self.shader_passes_hlsl = []
        for i in range(self.pass_max):
            self.shader_passes_hlsl.append(header_textures[i]+macros+pass_body[i]+footer_main[i])

        if (vv):
            for i in range(self.pass_max):
                print("=======================")
                print(self.shader_passes_hlsl[i])

if __name__ == "__main__":
    s1 = magpie_shader("CuNNy-veryfast-NVL.hlsl")
    s2 = magpie_shader("CuNNy-faster-NVL.hlsl")
    s3 = magpie_shader("CuNNy-fast-NVL.hlsl")
    s4 = magpie_shader("CuNNy-3x12-NVL.hlsl")
    s5 = magpie_shader("CuNNy-4x12-NVL.hlsl")
    s6 = magpie_shader("CuNNy-4x16-NVL.hlsl")
    s7 = magpie_shader("CuNNy-4x24-NVL.hlsl")
    s8 = magpie_shader("CuNNy-4x32-NVL.hlsl")
    s9 = magpie_shader("CuNNy-8x32-NVL.hlsl")
