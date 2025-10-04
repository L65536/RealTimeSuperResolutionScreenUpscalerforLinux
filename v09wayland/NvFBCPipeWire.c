/*!
 * \brief
 * Demonstrates how to use the PipeWire backend of NvFBC to grab frames to
 * system memory and save them to the disk.
 *
 * \file
 * This sample demonstrates the following features:
 * - Creating capture sessions with the PipeWire backend of NvFBC.
 * - Capture to system memory.
 *
 *
 * \copyright
 * Copyright (c) 2024, NVIDIA CORPORATION. All rights reserved.
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

#include <NvFBC.h>

#include "NvFBCUtils.h"

#define APP_VERSION 1

#define LIB_NVFBC_NAME "libnvidia-fbc.so.1"

#define FILENAME_LEN 64
#define FRAMES_PER_SESSION 2

int main(int argc, char* argv[])
{
    void* libNVFBC = NULL;
    PNVFBCCREATEINSTANCE NvFBCCreateInstance_ptr = NULL;
    NVFBC_API_FUNCTION_LIST pFn;

    NVFBCSTATUS fbcStatus;
    NVFBC_SESSION_HANDLE fbcHandle;
    NVFBC_CREATE_HANDLE_PARAMS createHandleParams;
    NVFBC_DESTROY_HANDLE_PARAMS destroyHandleParams;
    NVFBC_BOOL err = NVFBC_FALSE;

    int it;
    char portalRestoreToken[NVFBC_PORTAL_RESTORE_TOKEN_LEN] = { '\0' };

    NvFBCUtilsPrintVersions(APP_VERSION);

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
     * The loop below demonstrates the ways to create a capture session that
     * uses the PipeWire backend.
     */
    for (it = 0; it < 2; it++) {
        NVFBC_GET_STATUS_PARAMS statusParams;
        NVFBC_CREATE_CAPTURE_SESSION_PARAMS createCaptureParams;
        NVFBC_TOSYS_GRAB_FRAME_PARAMS grabParams;
        NVFBC_FRAME_GRAB_INFO frameInfo;
        NVFBC_DESTROY_CAPTURE_SESSION_PARAMS destroyCaptureParams;
        NVFBC_TOSYS_SETUP_PARAMS setupParams;

        char filename[FILENAME_LEN] = { '\0' };
        unsigned char* frame = NULL;
        int frameCount;
        int res;

        /*
         * Create a session handle that is used to identify the client.
         */
        memset(&createHandleParams, 0, sizeof(createHandleParams));

        createHandleParams.dwVersion = NVFBC_CREATE_HANDLE_PARAMS_VER;

        // Set privateData to allow NvFBC on consumer NVIDIA GPUs.
        // Based on https://github.com/keylase/nvidia-patch/blob/3193b4b1cea91527bf09ea9b8db5aade6a3f3c0a/win/nvfbcwrp/nvfbcwrp_main.cpp#L23-L25 .
        // Reference source https://github.com/LizardByte/Sunshine/blob/master/src/platform/linux/cuda.cpp
        const unsigned int MAGIC_PRIVATE_DATA[4] = {0xAEF57AC5, 0x401D1A39, 0x1B856BBE, 0x9ED0CEBA};
        createHandleParams.privateData = MAGIC_PRIVATE_DATA;
        createHandleParams.privateDataSize = sizeof(MAGIC_PRIVATE_DATA);

        if (it == 0) {
            printf("Creating a capture session without a restore token...\n");

            /*
             * This explicitly requests the PipeWire backend to be used for
             * recording. NvFBC uses XDG Desktop Portal to request a PipeWire
             * connection from the compositor. Please see the explanation of
             * NVFBC_BACKEND in NvFBC.h for the known limitations of this
             * backend.
             */
            createHandleParams.eBackend = NVFBC_BACKEND_PIPEWIRE;
        } else {
            printf("Creating a capture session with a restore token...\n");

            /*
             * It is also possible to use NVFBC_BACKEND_AUTO here. In that
             * case, NvFBC tries to find the best backend itself by using the
             * information available. (e.g. environment variables such as
             * XDG_SESSION_TYPE)
             */
            createHandleParams.eBackend = NVFBC_BACKEND_AUTO;

            /*
             * If we have a session restore token we received from a capture
             * session we used earlier, we can specify it here to restore the
             * previous session. Since the session we received the restore
             * token from was given permission to record user's screen,
             * creating a capture session below won't cause the compositor to
             * seek permission again.
             */
            snprintf(createHandleParams.portalRestoreToken,
                     NVFBC_PORTAL_RESTORE_TOKEN_LEN,
                     "%s",
                     portalRestoreToken);
        }

        fbcStatus = pFn.nvFBCCreateHandle(&fbcHandle, &createHandleParams);
        if (fbcStatus != NVFBC_SUCCESS) {
            fprintf(stderr, "%s\n", pFn.nvFBCGetLastErrorStr(fbcHandle));
            err = NVFBC_TRUE;
            goto destroy_resources;
        }

        /*
         * If succeeds, NvFBCCreateHandle() updates the eBackend field of the
         * given parameter struct to specify the chosen backend. This can be
         * useful when eBackend is set to NVFBC_BACKEND_AUTO.
         */
        assert(createHandleParams.eBackend == NVFBC_BACKEND_PIPEWIRE);

        /*
         * Create a capture session.
         *
         * If the PipeWire backend is in use, this call may cause the
         * compositor to show a dialog asking the user to grant NvFBC
         * permission to record the screen. Users can also choose the screen
         * they want to record using this dialog.
         *
         * Even though NVFBC_CAPTURE_TO_SYS is chosen here, all the available
         * capture types can be used.
         */
        memset(&createCaptureParams, 0, sizeof(createCaptureParams));

        createCaptureParams.dwVersion = NVFBC_CREATE_CAPTURE_SESSION_PARAMS_VER;
        createCaptureParams.eCaptureType = NVFBC_CAPTURE_TO_SYS;
        createCaptureParams.bWithCursor = NVFBC_TRUE;
        createCaptureParams.eTrackingType = NVFBC_TRACKING_DEFAULT;

        fbcStatus = pFn.nvFBCCreateCaptureSession(fbcHandle, &createCaptureParams);
        if (fbcStatus != NVFBC_SUCCESS) {
            fprintf(stderr, "%s\n", pFn.nvFBCGetLastErrorStr(fbcHandle));
            err = NVFBC_TRUE;
            goto destroy_resources;
        }

        /*
         * Save the XDG Desktop Portal restore token. It will be used in the
         * next iteration.
         *
         * Restore token is a null-terminated string.
         */
        memset(&statusParams, 0, sizeof(statusParams));

        statusParams.dwVersion = NVFBC_GET_STATUS_PARAMS_VER;

        fbcStatus = pFn.nvFBCGetStatus(fbcHandle, &statusParams);
        if (fbcStatus != NVFBC_SUCCESS) {
            fprintf(stderr, "%s\n", pFn.nvFBCGetLastErrorStr(fbcHandle));
            err = NVFBC_TRUE;
            goto destroy_resources;
        }

        strncpy(portalRestoreToken,
                statusParams.portalRestoreToken,
                NVFBC_PORTAL_RESTORE_TOKEN_LEN);

        assert(strlen(portalRestoreToken) != 0);

        /*
         * Set up the capture session.
         */
        memset(&setupParams, 0, sizeof(setupParams));

        setupParams.dwVersion = NVFBC_TOSYS_SETUP_PARAMS_VER;
        setupParams.eBufferFormat = NVFBC_BUFFER_FORMAT_RGB;
        setupParams.ppBuffer = (void**)&frame;

        fbcStatus = pFn.nvFBCToSysSetUp(fbcHandle, &setupParams);
        if (fbcStatus != NVFBC_SUCCESS) {
            fprintf(stderr, "%s\n", pFn.nvFBCGetLastErrorStr(fbcHandle));
            err = NVFBC_TRUE;
            goto destroy_resources;
        }

        for (frameCount = 0; frameCount < FRAMES_PER_SESSION; frameCount++) {
            /*
             * Start capturing frames.
             */
            printf("Capturing a frame...\n");

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
            if (fbcStatus == NVFBC_ERR_MUST_RECREATE) {
                printf("Capture session must be recreated!\n");
                it--;
                continue;
            } else if (fbcStatus != NVFBC_SUCCESS) {
                fprintf(stderr, "%s\n", pFn.nvFBCGetLastErrorStr(fbcHandle));
                err = NVFBC_TRUE;
                goto destroy_resources;
            }

            /*
             * Convert RGB frame to BMP and save it on the disk.
             *
             * This operation can be quite slow.
             */
            snprintf(filename, FILENAME_LEN, "frame%d-%d.bmp", it, frameCount);

            res = NvFBCUtilsSaveFrame(NVFBC_BUFFER_FORMAT_RGB,
                                      filename,
                                      frame,
                                      frameInfo.dwWidth,
                                      frameInfo.dwHeight);
            if (res > 0) {
                fprintf(stderr, "Unable to save frame\n");
                err = NVFBC_TRUE;
                goto destroy_resources;
            }

            printf("The captured frame is saved as %s\n", filename);
        }

    destroy_resources:
        printf("Destroying the capture session...\n");

        /*
         * Destroy capture session, tear down resources.
         */
        memset(&destroyCaptureParams, 0, sizeof(destroyCaptureParams));

        destroyCaptureParams.dwVersion = NVFBC_DESTROY_CAPTURE_SESSION_PARAMS_VER;

        fbcStatus = pFn.nvFBCDestroyCaptureSession(fbcHandle, &destroyCaptureParams);
        if (fbcStatus != NVFBC_SUCCESS) {
            fprintf(stderr, "%s\n", pFn.nvFBCGetLastErrorStr(fbcHandle));
            err = NVFBC_TRUE;
        }

        /*
         * Destroy session handle, tear down more resources.
         */
        memset(&destroyHandleParams, 0, sizeof(destroyHandleParams));

        destroyHandleParams.dwVersion = NVFBC_DESTROY_HANDLE_PARAMS_VER;

        fbcStatus = pFn.nvFBCDestroyHandle(fbcHandle, &destroyHandleParams);
        if (fbcStatus != NVFBC_SUCCESS) {
            fprintf(stderr, "%s\n", pFn.nvFBCGetLastErrorStr(fbcHandle));
            err = NVFBC_TRUE;
        }

        if (err) {
            break;
        }
    }

    return err ? EXIT_FAILURE : EXIT_SUCCESS;
}
