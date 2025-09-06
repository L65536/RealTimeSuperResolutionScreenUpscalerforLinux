/*!
 * \brief
 * Demonstrates how to use the NvFBC direct backend to capture a Vulkan
 * application from its pid.
 *
 * \file
 * This sample demonstrates the following features:
 * - Use the EGL path to have no dependencies on X. Can capture Vulkan
 *   applications running on X, Wayland, XWayland, and direct-to-display.
 * - Capture to system memory.
 *
 * \copyright
 * Copyright (c) 2025, NVIDIA CORPORATION. All rights reserved.
 *
 * Permission is hereby granted, free of charge, to any person obtaining a
 * copy of this software and associated documentation files (the "Software"),
 * to deal in the Software without restriction, including without limitation
 * the rights to use, copy, modify, merge, publish, distribute, sublicense,
 * and/or sell copies of the Software, and to permit persons to whom the
 * Software is furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in
 * all copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.  IN NO EVENT SHALL
 * THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
 * FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
 * DEALINGS IN THE SOFTWARE.
 */

// gcc -shared -O3 -fPIC -o nvfbc.so n03.c NvFBCUtils.c
// -03 = SIMD support
// -fPIC = position-independent code for shared library 

// createHandleParams.eBackend = NVFBC_BACKEND_X11;

// createHandleParams.eBackend = NVFBC_BACKEND_DIRECT; 
	// NVFBC_v9.0.0 PDF (JUL 2025) Driver >= 580.x.x
	// NvFBC Linux API version 1.9 Added support for the direct capture backend, which allows NvFBC direct capture of a Vulkan graphics application by its pid
    // The direct capture backend can capture occluded applications, provided that they are still presenting frames.

	// The direct capture backend lets an NvFBC client contact a Vulkan application through its pid via DBus without involving a display server.	
	// NvFBC uses the system bus and requires the below DBus configuration snippet in /etc/dbus-1/system.d/nvidia-dbus.conf:
	
	// sudo cp nvidia-dbus.conf /etc/dbus-1/system.d/
	// => (app) Unable to send DBus message
	// busctl 
	// sudo dbus-monitor --system
    // => Name "nvidia.nvfbc.pid_1505" does not exist"

#include <dlfcn.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>
#include <getopt.h>

#include "NvFBC.h"
#include "NvFBCUtils.h"
#define APP_VERSION 1
#define LIB_NVFBC_NAME "libnvidia-fbc.so.1"

    // Global
    void* libNVFBC = NULL;
    PNVFBCCREATEINSTANCE NvFBCCreateInstance_ptr = NULL;
    NVFBC_API_FUNCTION_LIST pFn;
    
    unsigned char* frame = NULL;
    int res, opt;
    pid_t capturePid = 0; // int
    // uint32_t captureTarget = 0;

    NVFBCSTATUS fbcStatus = NVFBC_SUCCESS;
    NVFBC_SESSION_HANDLE fbcHandle;
    NVFBC_CREATE_HANDLE_PARAMS createHandleParams;
    NVFBC_DESTROY_HANDLE_PARAMS destroyHandleParams;
    NVFBC_CREATE_CAPTURE_SESSION_PARAMS createCaptureParams;
    NVFBC_TOSYS_GRAB_FRAME_PARAMS grabParams;
    NVFBC_FRAME_GRAB_INFO frameInfo;
    NVFBC_DESTROY_CAPTURE_SESSION_PARAMS destroyCaptureParams;
    NVFBC_TOSYS_SETUP_PARAMS setupParams;
    // NvFBCUtilsPrintVersions(APP_VERSION);

int init(const int xx,const int yy,const int ww, const int hh, const int pid)
{
    capturePid = pid;

    // Dynamically load the NvFBC library.     
    libNVFBC = dlopen(LIB_NVFBC_NAME, RTLD_NOW);
    if (libNVFBC == NULL) {
        fprintf(stderr, "Unable to open '%s'\n", LIB_NVFBC_NAME);
        return EXIT_FAILURE;
    }

    // Resolve the 'NvFBCCreateInstance' symbol that will allow us to get the API function pointers.     
    NvFBCCreateInstance_ptr = (PNVFBCCREATEINSTANCE)dlsym(libNVFBC, "NvFBCCreateInstance");
    if (NvFBCCreateInstance_ptr == NULL) {
        fprintf(stderr, "Unable to resolve symbol 'NvFBCCreateInstance'\n");
        return EXIT_FAILURE;
    }

    // Create an NvFBC instance. API function pointers are accessible through pFn.     
    memset(&pFn, 0, sizeof(pFn));

    pFn.dwVersion = NVFBC_VERSION;

    fbcStatus = NvFBCCreateInstance_ptr(&pFn);
    if (fbcStatus != NVFBC_SUCCESS) {
        fprintf(stderr, "Unable to create NvFBC instance (status: %d)\n", fbcStatus);
        return EXIT_FAILURE;
    }

    // Create a session handle that is used to identify the client.     
    memset(&createHandleParams, 0, sizeof(createHandleParams));

    createHandleParams.dwVersion = NVFBC_CREATE_HANDLE_PARAMS_VER;
    // createHandleParams.eBackend = NVFBC_BACKEND_DIRECT; // Unable to send DBus message // The direct capture backend can capture occluded applications, provided that they are still presenting frames.   
    createHandleParams.eBackend = NVFBC_BACKEND_X11; // X11 full screen only, can set rect box, frame size, conflict with transparent overlay display
    createHandleParams.bUseEGL = NVFBC_TRUE;
        
    // Set privateData to allow NvFBC on consumer NVIDIA GPUs.
    // Based on https://github.com/keylase/nvidia-patch/blob/3193b4b1cea91527bf09ea9b8db5aade6a3f3c0a/win/nvfbcwrp/nvfbcwrp_main.cpp#L23-L25 .
    // Reference source https://github.com/LizardByte/Sunshine/blob/master/src/platform/linux/cuda.cpp
    const unsigned int MAGIC_PRIVATE_DATA[4] = {0xAEF57AC5, 0x401D1A39, 0x1B856BBE, 0x9ED0CEBA};
    createHandleParams.privateData = MAGIC_PRIVATE_DATA;
    createHandleParams.privateDataSize = sizeof(MAGIC_PRIVATE_DATA);
        
    fbcStatus = pFn.nvFBCCreateHandle(&fbcHandle, &createHandleParams);
    if (fbcStatus != NVFBC_SUCCESS) {
        fprintf(stderr, "%s\n", pFn.nvFBCGetLastErrorStr(fbcHandle));
        return EXIT_FAILURE; // goto destroy_resources;
    }

    // Create a capture session.     
    memset(&createCaptureParams, 0, sizeof(createCaptureParams));

    createCaptureParams.dwVersion = NVFBC_CREATE_CAPTURE_SESSION_PARAMS_VER;
    createCaptureParams.eCaptureType = NVFBC_CAPTURE_TO_SYS; // or CUDA MODE: Captures a frame to a CUDA device in video memory. No CUDA lib needed.
    createCaptureParams.bDisableAutoModesetRecovery = NVFBC_TRUE;
    createCaptureParams.bPushModel = NVFBC_TRUE;
    createCaptureParams.bAllowDirectCapture = NVFBC_TRUE; // NVFBC_FALSE;
    createCaptureParams.dwPid = capturePid; // only valid for direct mode
    createCaptureParams.dwDbusTimeoutMs = 0; // captureTarget; ???
    
    // Manually assign capture window coordinates and frame size for NVFBC_BACKEND_X11, not needed for NVFBC_BACKEND_DIRECT
    struct _NVFBC_BOX box;
    box.x=xx;
    box.y=yy;
    box.w=ww;
    box.h=hh;
    struct _NVFBC_SIZE fsize;
    fsize.w=ww;
    fsize.h=hh;
    createCaptureParams.captureBox = box; 
    createCaptureParams.frameSize = fsize;
    // DEBUG printf("%d %d %d %d\n", xx, yy, ww, hh);

    fbcStatus = pFn.nvFBCCreateCaptureSession(fbcHandle, &createCaptureParams);
    if (fbcStatus != NVFBC_SUCCESS) {
        fprintf(stderr, "%s\n", pFn.nvFBCGetLastErrorStr(fbcHandle));
        return EXIT_FAILURE; // goto destroy_resources;
    }

    // Set up the capture session.     
    memset(&setupParams, 0, sizeof(setupParams));
    setupParams.dwVersion = NVFBC_TOSYS_SETUP_PARAMS_VER;
    setupParams.eBufferFormat = NVFBC_BUFFER_FORMAT_BGRA;
    setupParams.ppBuffer = (void**)&frame;
    fbcStatus = pFn.nvFBCToSysSetUp(fbcHandle, &setupParams);
    if (fbcStatus != NVFBC_SUCCESS) {
        fprintf(stderr, "%s\n", pFn.nvFBCGetLastErrorStr(fbcHandle));
        return EXIT_FAILURE; // goto destroy_resources;
    }

	// Use blocking calls. The application will wait for new frames.
	// New frames are generated when the mouse cursor moves or when the screen refreshed.
	// &frameInfo This structure will contain information about the captured frame.         		
	memset(&grabParams, 0, sizeof(grabParams));
	memset(&frameInfo, 0, sizeof(frameInfo));       
	grabParams.dwVersion = NVFBC_TOSYS_GRAB_FRAME_PARAMS_VER;
	grabParams.dwFlags = NVFBC_TOSYS_GRAB_FLAGS_NOFLAGS;
	grabParams.pFrameGrabInfo = &frameInfo;
} // end of init

unsigned char* capture(int debug)
//void** capture(void)
{		        		                              
        // Capture a new frame.         
        fbcStatus = pFn.nvFBCToSysGrabFrame(fbcHandle, &grabParams);
        if (fbcStatus != NVFBC_SUCCESS) {
            fprintf(stderr, "%s\n", pFn.nvFBCGetLastErrorStr(fbcHandle));
            return 0; // EXIT_FAILURE; // goto destroy_resources;
        }

		// DEUBG info       
        if(debug) printf("%u %u %u %u %u\n",frameInfo.dwWidth,frameInfo.dwHeight,
			frameInfo.dwCurrentFrame, // counter
			(unsigned int)frameInfo.bIsNewFrame,(unsigned int)frameInfo.bDirectCapture);

       // printf("frame %p %d\n", frame, frame);
       return frame;
       //return (void**)&frame;
}
        
int destroy(void)
{
    // destroy_resources:
    memset(&destroyCaptureParams, 0, sizeof(destroyCaptureParams));

    destroyCaptureParams.dwVersion = NVFBC_DESTROY_CAPTURE_SESSION_PARAMS_VER;
    fbcStatus = pFn.nvFBCDestroyCaptureSession(fbcHandle, &destroyCaptureParams);
    if (fbcStatus != NVFBC_SUCCESS) {
        fprintf(stderr, "%s\n", pFn.nvFBCGetLastErrorStr(fbcHandle));
    }

    // destroy_handle:
    memset(&destroyHandleParams, 0, sizeof(destroyHandleParams));

    destroyHandleParams.dwVersion = NVFBC_DESTROY_HANDLE_PARAMS_VER;
    pFn.nvFBCDestroyHandle(fbcHandle, &destroyHandleParams);

    return (fbcStatus == NVFBC_SUCCESS) ? EXIT_FAILURE : EXIT_SUCCESS;
}

/*
// self test executable
// gcc -o a n03.c NvFBCUtils.c
int main(void)
{
	int pid = 1111; // use nvidia-smi for pid // NVFBC_BACKEND_DIRECT not working yet

    init(10, 10, 640, 480, pid);

    printf("Testing NVFBC capture, move mouse to trigger screen updates...\n");
    printf("%x\n", capture());
    printf("%x\n", capture());
    printf("%x\n", capture());
    printf("%x\n", capture());
    printf("%x\n", capture());

    destroy();
}
*/