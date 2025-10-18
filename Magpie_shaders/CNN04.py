# Class for loading Magpie HLSL shaders

# Parse MagpieFX shader directives
# https://github.com/Blinue/Magpie/wiki/MagpieFX%20(EN)

# Only tested on three CuNNy2 shaders
# [Assumptions] Output ratio is 2x2, NUM_THREADS handled in HLSL, FORMAT is R8G8B8A8_UNORM(FP32)/...(FP16)

import struct
import compushady
import compushady.formats
import compushady.shaders.hlsl

class magpie_shader:
    def __init__(self, shader_file):
        self.shader_file = shader_file
        self.parse(shader_file, verbose=0)
        self.generate(shader_file, verbose=0)

    def parse(self, shader_file, verbose=0):
        print('Parsing shader file =', shader_file)
        with open(shader_file, 'r') as fp: file = fp.read()
        lines = file.splitlines()

        self.parsed_T_ratio = [] # Intermediate textures T ratio (w, h). Assume always 1x1
        self.parsed_BLOCK_SIZE = [] # Assume always [8 ... 8, 16]
        self.parsed_NUM_THREADS = [] # Assume always 64
        self.parsed_IN = []
        self.parsed_OUT = []
        self.start_point = []
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
                self.start_point.append(index)

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
            print(self.parsed_IN)
            print(self.parsed_OUT)
            print('Total passes =', self.pass_max, '\n')

    def generate(self, shader_file, verbose=0):
        print('Generating individual shader passes.')
        with open(shader_file, 'r') as fp: file = fp.read()
        lines = file.splitlines()

        # Extract individual HLSL passes
        pass_body = []
        body = ""
        current_pass = 0
        self.start_point.append(len(lines))
        for index, line in enumerate(lines):
            # print (index, len(lines), start_point[current_pass+1]-1, current_pass)
            if self.start_point[current_pass] <= index < self.start_point[current_pass+1]:
                body = body + line + "\n"
            if index == self.start_point[current_pass+1]-1:
                pass_body.append(body)
                body = ""
                if current_pass < self.pass_max: current_pass+=1

        # Read macros from file
        with open("macros.hlsl", 'r') as fp: macros = fp.read() #print(macros)

        # Generate individual HLSL textures definitions
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

        # Generate entry functions definitions
        footer_main = []
        f1 = "[numthreads(64, 1, 1)]\n"
        f2 = "void __M(uint3 tid : SV_GroupThreadID, uint3 gid : SV_GroupID) {Pass"
        f3 = "((gid.xy << 3), tid);}\n"
        for i in range(self.pass_max): footer_main.append(f1+f2+str(i+1)+f3) #print(footer_main)

        # Combine all elements
        self.shader_passes_hlsl = []
        for i in range(self.pass_max):
            self.shader_passes_hlsl.append(header_textures[i]+macros+pass_body[i]+footer_main[i])

        if (verbose):
            for i in range(self.pass_max):
                print("=======================")
                print(self.shader_passes_hlsl[i])

    def init(self, w, h, verbose=0):
        self.w = w
        self.h = h

        self.SP = compushady.Sampler(
            filter_min=compushady.SAMPLER_FILTER_POINT,
            filter_mag=compushady.SAMPLER_FILTER_POINT,
            #address_mode_u=compushady.SAMPLER_ADDRESS_MODE_WRAP,
            #address_mode_v=compushady.SAMPLER_ADDRESS_MODE_CLAMP,
            #address_mode_w=compushady.SAMPLER_ADDRESS_MODE_MIRROR,
            )

        self.SL = compushady.Sampler(
            filter_min=compushady.SAMPLER_FILTER_LINEAR,
            filter_mag=compushady.SAMPLER_FILTER_LINEAR,
            #address_mode_u=compushady.SAMPLER_ADDRESS_MODE_WRAP,
            #address_mode_v=compushady.SAMPLER_ADDRESS_MODE_CLAMP,
            #address_mode_w=compushady.SAMPLER_ADDRESS_MODE_MIRROR,
            )

        #with open("FP16.hlsl", 'r') as fp: fp1632 = fp.read() # use this for FP16
        with open("FP32.hlsl", 'r') as fp: fp1632 = fp.read() # use this for FP32

        self.shader = []
        for i in range(self.pass_max):
            # Use this for separate shader_passN.hlsl files.
            #s = self.shader_file.replace(".hlsl", "")
            #pass_filename = f"{s}_Pass{i+1}.hlsl"
            #with open(pass_filename, 'r') as fp: pass_file = fp.read()
            pass_file = self.shader_passes_hlsl[i]

            s = compushady.shaders.hlsl.compile(fp1632+pass_file, entry_point="__M")
            self.shader.append(s)

        self.INPUT = compushady.Texture2D(w, h, compushady.formats.R8G8B8A8_UNORM)
        self.OUTPUT = compushady.Texture2D(w*2, h*2, compushady.formats.R8G8B8A8_UNORM)
        self.staging_buffer = compushady.Buffer(self.INPUT.size, compushady.HEAP_UPLOAD)
        self.readback_buffer = compushady.Buffer((self.OUTPUT.size+self.OUTPUT.row_pitch-1)//self.OUTPUT.row_pitch*self.OUTPUT.row_pitch, compushady.HEAP_READBACK)
        # readback_buffer = Buffer(OUTPUT.size, HEAP_READBACK) # wrong size
        # Adjust buffer size to match the correct row_pitch, otherwise size of last line mismatch
        # print(f"{OUTPUT.width}/{OUTPUT.row_pitch//4}x{OUTPUT.height}={OUTPUT.row_pitch*OUTPUT.height}/{OUTPUT.size}")

        self.T = []
        for i in self.parsed_T_ratio: #range(self.parsed_T_ratio):
            (wr,hr) = i # self.parsed_T_ratio[i] # always 1x1
            t = compushady.Texture2D(w*wr, h*hr, compushady.formats.R8G8B8A8_UNORM)
            self.T.append(t)

        self.CB = []
        for i in range(self.pass_max):
            cb = compushady.Buffer(40, compushady.HEAP_UPLOAD)
            if i == self.pass_max-1:
                cb.upload(struct.pack('iiiiffffff', w, h, w*2, h*2, 1.0/w, 1.0/h, 1.0/w/2, 1.0/h/2, 2.0, 2.0))
            else:
                cb.upload(struct.pack('iiiiffffff', w, h, w, h, 1.0/w, 1.0/h, 1.0/w, 1.0/h, 1.0, 1.0))
            self.CB.append(cb)

        self.SRV = [] # need to group each pass first then append
        for i in range(self.pass_max):
            p = []
            for s in self.parsed_IN[i]:
                if s == 'INPUT': p.append(self.INPUT)
                else: p.append(self.T[int(s.replace("T", ""))])
            self.SRV.append(p)

        self.UAV = [] # need to group each pass first then append
        for i in range(self.pass_max):
            p = []
            for s in self.parsed_OUT[i]:
                if s == 'OUTPUT': p.append(self.OUTPUT)
                else: p.append(self.T[int(s.replace("T", ""))])
            self.UAV.append(p)

    def upload(self, buffer):
        pixel_size = compushady.formats.get_pixel_size(compushady.formats.R8G8B8A8_UNORM)
        self.staging_buffer.upload2d(buffer, self.INPUT.row_pitch, self.INPUT.width, self.INPUT.height, pixel_size)
        self.staging_buffer.copy_to(self.INPUT)

    def compute(self):
        for i in range(self.pass_max):

            ####### move this to init section?
            compute = compushady.Compute(self.shader[i], cbv=[self.CB[i]], srv=self.SRV[i], uav=self.UAV[i], samplers=[self.SP,self.SL])

            ### ??? BUG
            n = self.parsed_BLOCK_SIZE[i]
            # print(n)
            n = 8 # temp fix

            if i == self.pass_max-1:
                compute.dispatch((self.w*2+n-1)//n, (self.h*2+n-1)//n, 1) # (OUPUT_size+block_size-1)//block_size
            else:
                compute.dispatch((self.w+n-1)//n, (self.h+n-1)//n, 1) # (OUPUT_size+block_size-1)//block_size

    def download(self):
        self.OUTPUT.copy_to(self.readback_buffer)

if __name__ == "__main__":
    print("Comparing shaders results: load multiple shaders and click to loop title/images within single window.")
    print("Close all existing terminal windows first for accurate results.")
    print("Reference time on an entry level GPU (Pascal) = 16 16 22 45 52 89 205 474 788 ms for 720p FP32")
    print("Reference time on an entry level GPU (Pascal) = 22 25 34 69 80 141 341 639 1249 ms for 1080p FP32")
    print("Require a 'test.jpg' in the same folder.\n")
    file = "test.jpg"
    file = "test720.jpg"
    file = "test1080.jpg"

    from PIL import Image
    import time
    import numpy

    image = Image.open(file).convert("RGBA")
    h, w = image.height, image.width
    img_data = numpy.array(image)

    DISPLAY = 1
    if(DISPLAY):
        import pyglet

    shader = []
    shader.append(magpie_shader("CuNNy-veryfast-NVL.hlsl"))
    shader.append(magpie_shader("CuNNy-faster-NVL.hlsl"))
    shader.append(magpie_shader("CuNNy-fast-NVL.hlsl"))
    shader.append(magpie_shader("CuNNy-3x12-NVL.hlsl"))
    shader.append(magpie_shader("CuNNy-4x12-NVL.hlsl"))
    shader.append(magpie_shader("CuNNy-4x16-NVL.hlsl"))
    shader.append(magpie_shader("CuNNy-4x24-NVL.hlsl"))
    shader.append(magpie_shader("CuNNy-4x32-NVL.hlsl"))
    shader.append(magpie_shader("CuNNy-8x32-NVL.hlsl"))
    print()

    img = []
    title = []
    for s in shader:
        s.init(w, h)
        s.upload(img_data)

        t = time.perf_counter()
        s.compute()
        t=(time.perf_counter() - t)*1000
        print(f"{t:.2f} ms")

        if(DISPLAY):
            s.download()
            i = pyglet.image.ImageData(s.OUTPUT.row_pitch//4, s.OUTPUT.height, "RGBA", s.readback_buffer.readback(), pitch=-s.OUTPUT.row_pitch)
            img.append(i)
            title.append(s.shader_file)

    if(DISPLAY):
        print("\nClick on the window to cycle through all different images.\n")
        window = pyglet.window.Window(w*2,h*2, caption='Display')
        i = 0

        @window.event
        def on_draw():
            img[i].blit(0, 0)
            window.set_caption(title[i])

        @window.event
        def on_mouse_press(x, y, button, modifiers):
            global i
            i = i + 1
            if i == len(img): i = 0

        pyglet.app.run(1/30)