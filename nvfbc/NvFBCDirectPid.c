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

#include <dlfcn.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>
#include <getopt.h>

#include <NvFBC.h>

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
    printf("  --frames|-f <n>   Number of frames to capture (default: %u)\n",
           N_FRAMES);
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

    /*
     * Parse the command line.
     */
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

    /*
     * Dynamically load the NvFBC library.
     */
    libNVFBC = dlopen(LIB_NVFBC_NAME, RTLD_NOW);
    if (libNVFBC == NULL) {
        fprintf(stderr, "Unable to open '%s'\n", LIB_NVFBC_NAME);
        return EXIT_FAILURE;
    }

    /*
     * Resolve the 'NvFBCCreateInstance' symbol that will allow us to get
     * the API function pointers.
     */
    NvFBCCreateInstance_ptr = (PNVFBCCREATEINSTANCE)dlsym(libNVFBC, "NvFBCCreateInstance");
    if (NvFBCCreateInstance_ptr == NULL) {
        fprintf(stderr, "Unable to resolve symbol 'NvFBCCreateInstance'\n");
        return EXIT_FAILURE;
    }

    /*
     * Create an NvFBC instance.
     *
     * API function pointers are accessible through pFn.
     */
    memset(&pFn, 0, sizeof(pFn));

    pFn.dwVersion = NVFBC_VERSION;

    fbcStatus = NvFBCCreateInstance_ptr(&pFn);
    if (fbcStatus != NVFBC_SUCCESS) {
        fprintf(stderr, "Unable to create NvFBC instance (status: %d)\n", fbcStatus);
        return EXIT_FAILURE;
    }

    /*
     * Create a session handle that is used to identify the client.
     */
    memset(&createHandleParams, 0, sizeof(createHandleParams));

    createHandleParams.dwVersion = NVFBC_CREATE_HANDLE_PARAMS_VER;
    createHandleParams.eBackend = NVFBC_BACKEND_DIRECT;
    createHandleParams.bUseEGL = NVFBC_TRUE;

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
        goto destroy_handle;
    }

    /*
     * Create a capture session.
     *
     */
    memset(&createCaptureParams, 0, sizeof(createCaptureParams));

    createCaptureParams.dwVersion = NVFBC_CREATE_CAPTURE_SESSION_PARAMS_VER;
    createCaptureParams.eCaptureType = NVFBC_CAPTURE_TO_SYS;
    createCaptureParams.bDisableAutoModesetRecovery = NVFBC_TRUE;
    createCaptureParams.bPushModel = NVFBC_TRUE;
    createCaptureParams.dwPid = capturePid;
    createCaptureParams.dwDbusTimeoutMs = captureTarget;

    fbcStatus = pFn.nvFBCCreateCaptureSession(fbcHandle, &createCaptureParams);
    if (fbcStatus != NVFBC_SUCCESS) {
        fprintf(stderr, "%s\n", pFn.nvFBCGetLastErrorStr(fbcHandle));
        goto destroy_resources;
    }

    /*
     * Set up the capture session.
     */
    memset(&setupParams, 0, sizeof(setupParams));

    setupParams.dwVersion = NVFBC_TOSYS_SETUP_PARAMS_VER;
    setupParams.eBufferFormat = NVFBC_BUFFER_FORMAT_BGRA;
    setupParams.ppBuffer = (void**)&frame;

    fbcStatus = pFn.nvFBCToSysSetUp(fbcHandle, &setupParams);
    if (fbcStatus != NVFBC_SUCCESS) {
        fprintf(stderr, "%s\n", pFn.nvFBCGetLastErrorStr(fbcHandle));
        goto destroy_resources;
    }

    printf("Capturing frames...\n");
    for (frameCount = 0; frameCount < nFrames; frameCount++) {
        /*
         * Start capturing frames.
         */
        memset(&grabParams, 0, sizeof(grabParams));
        memset(&frameInfo, 0, sizeof(frameInfo));

        grabParams.dwVersion = NVFBC_TOSYS_GRAB_FRAME_PARAMS_VER;

        /*
         * Use blocking calls.
         *
         * The application will wait for new frames. New frames are
         * generated when the mouse cursor moves or when the screen if
         * refreshed.
         */
        grabParams.dwFlags = NVFBC_TOSYS_GRAB_FLAGS_NOFLAGS;

        /*
         * This structure will contain information about the captured
         * frame.
         */
        grabParams.pFrameGrabInfo = &frameInfo;

        /*
         * Capture a new frame.
         */
        fbcStatus = pFn.nvFBCToSysGrabFrame(fbcHandle, &grabParams);
        if (fbcStatus != NVFBC_SUCCESS) {
            fprintf(stderr, "%s\n", pFn.nvFBCGetLastErrorStr(fbcHandle));
            goto destroy_resources;
        }

        /*
         * Convert BGRA frame to BMP and save it on the disk.
         *
         * This operation can be quite slow.
         */
        snprintf(filename, FILENAME_LEN, "frame%d.bmp", frameCount);
        res = NvFBCUtilsSaveFrame(NVFBC_BUFFER_FORMAT_BGRA,
                                  filename,
                                  frame,
                                  frameInfo.dwWidth,
                                  frameInfo.dwHeight);
        if (res > 0) {
            fprintf(stderr, "Unable to save frame\n");
            goto destroy_resources;
        }
            printf("The captured frame is saved as %s\n", filename);
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
