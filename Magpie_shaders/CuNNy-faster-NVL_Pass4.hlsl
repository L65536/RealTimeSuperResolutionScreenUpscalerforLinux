cbuffer __CB1 : register(b0) {
	uint2 __inputSize;
	uint2 __outputSize;
	float2 __inputPt;
	float2 __outputPt;
	float2 __scale;
};


Texture2D<MF4> INPUT : register(t0);
Texture2D<MF4> T0 : register(t1);
Texture2D<MF4> T1 : register(t2);
RWTexture2D<unorm MF4> OUTPUT : register(u0);
SamplerState SP : register(s0);
SamplerState SL : register(s1);

uint __Bfe(uint src, uint off, uint bits) { uint mask = (1u << bits) - 1; return (src >> off) & mask; }
uint __BfiM(uint src, uint ins, uint bits) { uint mask = (1u << bits) - 1; return (ins & mask) | (src & (~mask)); }
uint2 Rmp8x8(uint a) { return uint2(__Bfe(a, 1u, 3u), __BfiM(__Bfe(a, 3u, 3u), a, 1u)); }
uint2 GetInputSize() { return __inputSize; }
float2 GetInputPt() { return __inputPt; }
uint2 GetOutputSize() { return __outputSize; }
float2 GetOutputPt() { return __outputPt; }
float2 GetScale() { return __scale; }
MF2 MulAdd(MF2 x, MF2x2 y, MF2 a) {
	MF2 result = a;
	result = mad(x.x, y._m00_m01, result);
	result = mad(x.y, y._m10_m11, result);
	return result;
}
MF3 MulAdd(MF2 x, MF2x3 y, MF3 a) {
	MF3 result = a;
	result = mad(x.x, y._m00_m01_m02, result);
	result = mad(x.y, y._m10_m11_m12, result);
	return result;
}
MF4 MulAdd(MF2 x, MF2x4 y, MF4 a) {
	MF4 result = a;
	result = mad(x.x, y._m00_m01_m02_m03, result);
	result = mad(x.y, y._m10_m11_m12_m13, result);
	return result;
}
MF2 MulAdd(MF3 x, MF3x2 y, MF2 a) {
	MF2 result = a;
	result = mad(x.x, y._m00_m01, result);
	result = mad(x.y, y._m10_m11, result);
	result = mad(x.z, y._m20_m21, result);
	return result;
}
MF3 MulAdd(MF3 x, MF3x3 y, MF3 a) {
	MF3 result = a;
	result = mad(x.x, y._m00_m01_m02, result);
	result = mad(x.y, y._m10_m11_m12, result);
	result = mad(x.z, y._m20_m21_m22, result);
	return result;
}
MF4 MulAdd(MF3 x, MF3x4 y, MF4 a) {
	MF4 result = a;
	result = mad(x.x, y._m00_m01_m02_m03, result);
	result = mad(x.y, y._m10_m11_m12_m13, result);
	result = mad(x.z, y._m20_m21_m22_m23, result);
	return result;
}
MF2 MulAdd(MF4 x, MF4x2 y, MF2 a) {
	MF2 result = a;
	result = mad(x.x, y._m00_m01, result);
	result = mad(x.y, y._m10_m11, result);
	result = mad(x.z, y._m20_m21, result);
	result = mad(x.w, y._m30_m31, result);
	return result;
}
MF3 MulAdd(MF4 x, MF4x3 y, MF3 a) {
	MF3 result = a;
	result = mad(x.x, y._m00_m01_m02, result);
	result = mad(x.y, y._m10_m11_m12, result);
	result = mad(x.z, y._m20_m21_m22, result);
	result = mad(x.w, y._m30_m31_m32, result);
	return result;
}
MF4 MulAdd(MF4 x, MF4x4 y, MF4 a) {
	MF4 result = a;
	result = mad(x.x, y._m00_m01_m02_m03, result);
	result = mad(x.y, y._m10_m11_m12_m13, result);
	result = mad(x.z, y._m20_m21_m22_m23, result);
	result = mad(x.w, y._m30_m31_m32_m33, result);
	return result;
}

#define O(t, x, y) t.SampleLevel(SP, pos + float2(x, y) * pt, 0)
#define V4 MF4
#define M4 MF4x4

#define L0(x, y) V4(O(T0, x, y))
#define L1(x, y) V4(O(T1, x, y))

void Pass4(uint2 blockStart, uint3 tid) {
	float2 pt = float2(GetInputPt());
	uint2 gxy = (Rmp8x8(tid.x) << 1) + blockStart;
	uint2 sz = GetOutputSize();
	if (gxy.x >= sz.x || gxy.y >= sz.y)
		return;
	float2 pos = ((gxy >> 1) + 0.5) * pt;
	V4 s0_0_0, s0_0_1, s0_0_2, s0_1_0, s0_1_1, s0_1_2, s0_2_0, s0_2_1, s0_2_2, s1_0_0, s1_0_1, s1_0_2, s1_1_0, s1_1_1, s1_1_2, s1_2_0, s1_2_1, s1_2_2;
	V4 r0 = 0.0;
	r0 = V4(1.178e-04, -5.913e-05, -9.275e-09, -1.228e-04);
	s0_0_0 = L0(-1.0, -1.0); s0_0_1 = L0(0.0, -1.0); s0_0_2 = L0(1.0, -1.0);
	s0_1_0 = L0(-1.0, 0.0); s0_1_1 = L0(0.0, 0.0); s0_1_2 = L0(1.0, 0.0);
	s0_2_0 = L0(-1.0, 1.0); s0_2_1 = L0(0.0, 1.0); s0_2_2 = L0(1.0, 1.0);
	s1_0_0 = L1(-1.0, -1.0); s1_0_1 = L1(0.0, -1.0); s1_0_2 = L1(1.0, -1.0);
	s1_1_0 = L1(-1.0, 0.0); s1_1_1 = L1(0.0, 0.0); s1_1_2 = L1(1.0, 0.0);
	s1_2_0 = L1(-1.0, 1.0); s1_2_1 = L1(0.0, 1.0); s1_2_2 = L1(1.0, 1.0);
	r0 = MulAdd(s0_0_0, M4(-1.244e-02, -8.758e-03, -8.863e-03, 2.117e-02, -9.270e-04, 5.927e-04, 1.009e-03, -1.716e-03, -9.253e-04, -1.111e-03, 1.800e-03, 1.738e-03, -1.496e-02, -1.273e-02, -1.486e-02, 7.423e-03), r0);
	r0 = MulAdd(s0_0_1, M4(3.739e-03, -9.298e-06, 1.274e-03, 3.710e-03, 3.239e-03, 1.140e-03, -1.923e-02, -4.003e-03, 3.644e-02, -8.557e-03, 9.162e-04, -2.231e-03, -5.309e-01, 1.193e-02, -4.997e-02, -2.020e-02), r0);
	r0 = MulAdd(s0_0_2, M4(6.792e-03, -1.583e-03, -1.545e-04, 2.123e-03, -1.343e-01, 1.223e-01, 2.373e-03, -8.276e-02, -4.049e-03, 1.254e-01, -1.080e-02, 1.894e-02, 9.075e-03, 1.250e-02, -3.510e-02, -1.125e-01), r0);
	r0 = MulAdd(s0_1_0, M4(1.235e-01, -3.503e-02, -3.821e-02, -3.128e-02, -5.355e-03, 4.795e-04, -7.349e-03, -4.585e-04, 5.054e-03, 8.673e-04, 1.080e-03, -6.774e-04, -1.712e-03, 1.244e-02, -5.717e-03, 4.947e-03), r0);
	r0 = MulAdd(s0_1_1, M4(-2.232e-02, 3.194e-01, -4.260e-02, 9.687e-03, 5.554e-02, -3.243e-02, 4.311e-02, -3.627e-02, 1.753e-01, 1.504e-02, 1.343e-01, 8.075e-03, 2.201e-02, 3.087e-04, 3.701e-01, 2.575e-01), r0);
	r0 = MulAdd(s0_1_2, M4(5.742e-03, -5.625e-02, 2.008e-02, -8.259e-03, -3.426e-01, 4.014e-01, -5.684e-01, 5.084e-01, -4.118e-01, 2.838e-02, -1.102e-01, 2.417e-01, -1.824e-03, -1.022e-02, -9.827e-03, 1.753e-01), r0);
	r0 = MulAdd(s0_2_0, M4(-2.962e-02, 3.611e-02, -2.826e-02, 7.162e-02, 3.191e-03, -2.836e-03, 3.641e-03, 4.525e-04, -3.387e-03, 1.218e-03, -2.024e-03, 1.153e-03, 3.745e-03, -9.613e-04, 1.151e-02, 4.385e-04), r0);
	r0 = MulAdd(s0_2_1, M4(-4.404e-01, 4.677e-02, -2.510e-01, 4.287e-01, -1.260e-02, 9.716e-04, 1.849e-02, 2.118e-03, 2.679e-02, -4.549e-03, 8.995e-02, -8.610e-03, -4.725e-03, -2.950e-03, -1.471e-02, -1.283e-02), r0);
	r0 = MulAdd(s0_2_2, M4(1.786e-02, -3.493e-02, 2.228e-02, -1.174e-01, 5.050e-02, -1.421e-02, 2.838e-02, 4.065e-02, -1.205e-02, -3.918e-02, -1.469e-01, -9.351e-02, 1.648e-03, -1.034e-03, 4.440e-03, 6.707e-03), r0);
	r0 = MulAdd(s1_0_0, M4(-2.142e-02, 6.180e-03, -4.312e-04, -1.255e-03, 1.440e-01, -3.725e-03, -9.258e-03, -2.704e-02, 5.318e-02, 2.435e-02, 3.821e-02, 2.240e-02, 3.649e-02, -1.872e-02, -5.139e-03, -2.301e-03), r0);
	r0 = MulAdd(s1_0_1, M4(1.169e-02, -4.560e-02, 3.319e-03, -1.149e-02, 1.058e-02, 1.033e-01, -8.919e-03, -3.206e-03, 1.938e-02, 4.199e-02, 1.024e-02, 2.606e-02, -6.607e-04, 9.595e-02, -1.618e-02, -9.020e-03), r0);
	r0 = MulAdd(s1_0_2, M4(-2.192e-04, -1.368e-03, 2.637e-04, 2.084e-03, 3.796e-04, 4.478e-03, 4.530e-03, 3.802e-03, 1.389e-03, 8.964e-03, -7.443e-03, -9.200e-03, -4.164e-03, -4.553e-02, 8.826e-03, 5.783e-03), r0);
	r0 = MulAdd(s1_1_0, M4(-3.189e-02, 1.554e-02, -2.356e-02, 6.188e-03, -3.738e-01, -1.353e-01, 3.467e-01, -7.778e-02, 3.385e-01, 1.687e-01, -1.031e+00, -5.774e-02, 8.364e-03, 6.707e-03, 4.895e-02, 3.747e-02), r0);
	r0 = MulAdd(s1_1_1, M4(2.261e-01, -5.996e-01, 1.353e-01, 2.720e-02, -1.738e-02, 6.702e-02, 2.513e-02, 2.757e-01, -2.204e-03, 8.863e-02, 4.658e-02, -1.606e-01, 3.429e-01, 3.604e-01, -4.408e-02, -8.637e-01), r0);
	r0 = MulAdd(s1_1_2, M4(-5.780e-03, 3.479e-02, -1.777e-03, -6.527e-04, -3.946e-03, -2.386e-02, 3.971e-03, 7.918e-04, -8.640e-05, 3.242e-02, -1.883e-03, 1.259e-02, 1.303e-02, -1.050e-02, -2.165e-02, -2.813e-02), r0);
	r0 = MulAdd(s1_2_0, M4(-4.737e-03, 4.114e-03, -5.121e-03, -5.830e-04, 1.718e-03, -3.928e-04, -1.548e-01, -5.817e-02, -2.471e-02, 2.727e-03, 1.538e-01, 9.399e-02, -3.287e-03, -2.909e-03, -2.165e-02, 1.371e-03), r0);
	r0 = MulAdd(s1_2_1, M4(1.177e-03, 3.208e-02, 9.937e-02, 2.223e-02, 7.648e-03, 1.837e-02, -2.497e-02, -2.802e-02, -1.218e-02, -2.563e-03, -3.208e-03, 3.593e-02, 2.020e-02, -9.020e-03, 1.183e-01, 9.113e-02), r0);
	r0 = MulAdd(s1_2_2, M4(-1.707e-03, -3.909e-03, 6.098e-03, 2.484e-03, 5.783e-04, 9.003e-03, -6.119e-03, -1.253e-02, -6.749e-04, -8.294e-03, 1.991e-03, 1.878e-02, 9.696e-04, -1.977e-03, 4.883e-03, 1.341e-02), r0);
	static const MF3x3 RY = {0.299, 0.587, 0.114, -0.169, -0.331, 0.5, 0.5, -0.419, -0.081}, YR = {1, -0.00093, 1.401687, 1, -0.3437, -0.71417, 1, 1.77216, 0.00099};
	float2 opt = float2(GetOutputPt()), fpos = (float2(gxy) + 0.5) * opt;
	MF3 yuv;
	yuv = mul(RY, INPUT.SampleLevel(SL, fpos + float2(0.0, 0.0) * opt, 0).rgb);
	OUTPUT[gxy + int2(0, 0)] = MF4(mul(YR, MF3(saturate(yuv.r + r0.x), yuv.yz)), 1.0);
	yuv = mul(RY, INPUT.SampleLevel(SL, fpos + float2(1.0, 0.0) * opt, 0).rgb);
	OUTPUT[gxy + int2(1, 0)] = MF4(mul(YR, MF3(saturate(yuv.r + r0.y), yuv.yz)), 1.0);
	yuv = mul(RY, INPUT.SampleLevel(SL, fpos + float2(0.0, 1.0) * opt, 0).rgb);
	OUTPUT[gxy + int2(0, 1)] = MF4(mul(YR, MF3(saturate(yuv.r + r0.z), yuv.yz)), 1.0);
	yuv = mul(RY, INPUT.SampleLevel(SL, fpos + float2(1.0, 1.0) * opt, 0).rgb);
	OUTPUT[gxy + int2(1, 1)] = MF4(mul(YR, MF3(saturate(yuv.r + r0.w), yuv.yz)), 1.0);
}

[numthreads(64, 1, 1)]
void __M(uint3 tid : SV_GroupThreadID, uint3 gid : SV_GroupID) {
	Pass4((gid.xy << 4), tid);
}
