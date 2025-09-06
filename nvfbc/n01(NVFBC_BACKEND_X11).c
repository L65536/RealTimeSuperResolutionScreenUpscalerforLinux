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
 
// gcc -o n00 n00.c NvFBCUtils.c

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

#define FILENAME_LEN 64
#define N_FRAMES 10

static void usage(const char *pname)
{
    printf("Usage: %s [options]\n", pname);
    printf("\n");
    printf("Options:\n");
    printf("  --help|-h         This message\n");
    printf("  --get-status|-g   Print status of the application and exit\n");
    printf("  --pid|-p <pid>    PID of the Vulkan application to capture\n");
    printf("  --target|-t <n>   Index of the capture target to capture\n");
    printf("                    as returned by --get-status (default: 0)\n");
    printf("  --frames|-f <n>   Number of frames to capture (default: %u)\n", N_FRAMES);
}

int main(int argc, char* argv[])
{
    static struct option longopts[] = {
        { "frames", required_argument, NULL, 'f' },
        { "get-status", no_argument, NULL, 'g' },
        { "pid", required_argument, NULL, 'p' },
        { "target", required_argument, NULL, 't' },
        { NULL, 0, NULL, 0 }
    };

    void* libNVFBC = NULL;
    PNVFBCCREATEINSTANCE NvFBCCreateInstance_ptr = NULL;
    NVFBC_API_FUNCTION_LIST pFn;

    char filename[FILENAME_LEN] = { '\0' };
    unsigned char* frame = NULL;
    int res, opt;

    NVFBC_BOOL printStatusOnly = NVFBC_FALSE;

    unsigned int nFrames = N_FRAMES;
    unsigned int frameCount;
    pid_t capturePid = 0;
    uint32_t captureTarget = 0;

    NVFBCSTATUS fbcStatus = NVFBC_SUCCESS;
    NVFBC_SESSION_HANDLE fbcHandle;
    NVFBC_CREATE_HANDLE_PARAMS createHandleParams;
    NVFBC_DESTROY_HANDLE_PARAMS destroyHandleParams;
    NVFBC_CREATE_CAPTURE_SESSION_PARAMS createCaptureParams;
    NVFBC_TOSYS_GRAB_FRAME_PARAMS grabParams;
    NVFBC_FRAME_GRAB_INFO frameInfo;
    NVFBC_DESTROY_CAPTURE_SESSION_PARAMS destroyCaptureParams;
    NVFBC_TOSYS_SETUP_PARAMS setupParams;

    NvFBCUtilsPrintVersions(APP_VERSION);

    // Parse the command line.     
    while ((opt = getopt_long(argc, argv, "hgf:p:t:", longopts, NULL)) != -1) {
        switch (opt) {
            case 'f':
                nFrames = (unsigned int) atoi(optarg);
                break;
            case 'g':
                printStatusOnly = NVFBC_TRUE;
                break;
            case 'p':
                capturePid = (pid_t) atoi(optarg);
                break;
            case 't':
                captureTarget = (uint32_t) atoi(optarg);
                break;
            case 'h':
            default:
                usage(argv[0]);
                return EXIT_SUCCESS;
        }
    }

    if (capturePid == 0) {
        fprintf(stderr, "No pid specified\n");
        return EXIT_FAILURE;
    }

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
        goto destroy_resources;
    }

    if (printStatusOnly) {
        NVFBC_GET_STATUS_PARAMS statusParams;

        memset(&statusParams, 0, sizeof(statusParams));

        statusParams.dwVersion = NVFBC_GET_STATUS_PARAMS_VER;
        statusParams.dwPid = capturePid;

        fbcStatus = pFn.nvFBCGetStatus(fbcHandle, &statusParams);
        if (fbcStatus != NVFBC_SUCCESS) {
            fprintf(stderr, "%s\n", pFn.nvFBCGetLastErrorStr(fbcHandle));
            goto destroy_handle;
        }

        NvFBCUtilsPrintStatus(&statusParams);
        printf("%u\n",statusParams.dwCaptureTargetCount);
        printf("%u\n",statusParams.captureTargetSizes->w);
        printf("%u\n",statusParams.captureTargetSizes->h);
        goto destroy_handle;
    }

    // Create a capture session.     
    memset(&createCaptureParams, 0, sizeof(createCaptureParams));

    createCaptureParams.dwVersion = NVFBC_CREATE_CAPTURE_SESSION_PARAMS_VER;
    createCaptureParams.eCaptureType = NVFBC_CAPTURE_TO_SYS; // or CUDA MODE: Captures a frame to a CUDA device in video memory. No CUDA lib needed.
    createCaptureParams.bDisableAutoModesetRecovery = NVFBC_TRUE;
    createCaptureParams.bPushModel = NVFBC_TRUE;
    createCaptureParams.bAllowDirectCapture = NVFBC_TRUE;
    //createCaptureParams.bAllowDirectCapture = NVFBC_FALSE;
    createCaptureParams.dwPid = capturePid; // only for direct mode, vulkan app
    createCaptureParams.dwDbusTimeoutMs = captureTarget;

    // Manully assign capture window coordinates and frame size for NVFBC_BACKEND_X11
    struct _NVFBC_BOX box;
    box.x=10;
    box.y=10;
    box.w=200;
    box.h=200;
    struct _NVFBC_SIZE fsize;
    fsize.w=200;
    fsize.h=200;
    createCaptureParams.captureBox = box; 
    createCaptureParams.frameSize = fsize;

    fbcStatus = pFn.nvFBCCreateCaptureSession(fbcHandle, &createCaptureParams);
    if (fbcStatus != NVFBC_SUCCESS) {
        fprintf(stderr, "%s\n", pFn.nvFBCGetLastErrorStr(fbcHandle));
        goto destroy_resources;
    }

    // Set up the capture session.     
    memset(&setupParams, 0, sizeof(setupParams));
    setupParams.dwVersion = NVFBC_TOSYS_SETUP_PARAMS_VER;
    setupParams.eBufferFormat = NVFBC_BUFFER_FORMAT_BGRA;
    setupParams.ppBuffer = (void**)&frame;
    fbcStatus = pFn.nvFBCToSysSetUp(fbcHandle, &setupParams);
    if (fbcStatus != NVFBC_SUCCESS) {
        fprintf(stderr, "%s\n", pFn.nvFBCGetLastErrorStr(fbcHandle));
        goto destroy_resources;
    }

	// Use blocking calls. The application will wait for new frames.
	// New frames are generated when the mouse cursor moves or when the screen refreshed.
	// &frameInfo This structure will contain information about the captured frame.         		
	memset(&grabParams, 0, sizeof(grabParams));
	memset(&frameInfo, 0, sizeof(frameInfo));       
	grabParams.dwVersion = NVFBC_TOSYS_GRAB_FRAME_PARAMS_VER;
	grabParams.dwFlags = NVFBC_TOSYS_GRAB_FLAGS_NOFLAGS;
	grabParams.pFrameGrabInfo = &frameInfo;
		
    printf("Capturing frames...\n");
    for (frameCount = 0; frameCount < nFrames; frameCount++) {		               
               
        // Capture a new frame.         
        fbcStatus = pFn.nvFBCToSysGrabFrame(fbcHandle, &grabParams);
        if (fbcStatus != NVFBC_SUCCESS) {
            fprintf(stderr, "%s\n", pFn.nvFBCGetLastErrorStr(fbcHandle));
            goto destroy_resources;
        }

		// DEUBG info
        printf("%u %u %u %u %u\n",frameInfo.dwWidth,frameInfo.dwHeight,
			frameInfo.dwCurrentFrame, // counter
			(unsigned int)frameInfo.bIsNewFrame,(unsigned int)frameInfo.bDirectCapture);
        }

destroy_resources:
    memset(&destroyCaptureParams, 0, sizeof(destroyCaptureParams));

    destroyCaptureParams.dwVersion = NVFBC_DESTROY_CAPTURE_SESSION_PARAMS_VER;
    fbcStatus = pFn.nvFBCDestroyCaptureSession(fbcHandle, &destroyCaptureParams);
    if (fbcStatus != NVFBC_SUCCESS) {
        fprintf(stderr, "%s\n", pFn.nvFBCGetLastErrorStr(fbcHandle));
    }

destroy_handle:
    memset(&destroyHandleParams, 0, sizeof(destroyHandleParams));

    destroyHandleParams.dwVersion = NVFBC_DESTROY_HANDLE_PARAMS_VER;
    pFn.nvFBCDestroyHandle(fbcHandle, &destroyHandleParams);

    return (fbcStatus == NVFBC_SUCCESS) ? EXIT_FAILURE : EXIT_SUCCESS;
}
