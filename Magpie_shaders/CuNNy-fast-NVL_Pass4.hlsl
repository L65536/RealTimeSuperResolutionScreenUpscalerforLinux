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
	s0_0_0 = L0(-1.0, -1.0); s0_0_1 = L0(0.0, -1.0); s0_0_2 = L0(1.0, -1.0);
	s0_1_0 = L0(-1.0, 0.0); s0_1_1 = L0(0.0, 0.0); s0_1_2 = L0(1.0, 0.0);
	s0_2_0 = L0(-1.0, 1.0); s0_2_1 = L0(0.0, 1.0); s0_2_2 = L0(1.0, 1.0);
	s1_0_0 = L1(-1.0, -1.0); s1_0_1 = L1(0.0, -1.0); s1_0_2 = L1(1.0, -1.0);
	s1_1_0 = L1(-1.0, 0.0); s1_1_1 = L1(0.0, 0.0); s1_1_2 = L1(1.0, 0.0);
	s1_2_0 = L1(-1.0, 1.0); s1_2_1 = L1(0.0, 1.0); s1_2_2 = L1(1.0, 1.0);
	r0 = MulAdd(s0_0_0, M4(2.292e-02, 1.001e-02, -8.934e-03, 1.739e-03, -1.075e-02, 1.342e-03, 7.415e-03, 4.035e-03, 6.036e-02, -7.155e-03, -1.980e-03, -2.166e-03, -2.081e-02, 7.952e-03, -1.267e-02, 1.142e-02), r0);
	r0 = MulAdd(s0_0_1, M4(7.132e-02, 2.416e-02, -2.227e-03, -4.860e-04, 5.798e-03, -1.587e-02, 2.928e-02, -4.944e-02, 4.748e-02, 1.255e-01, -1.654e-02, 7.912e-03, -7.690e-02, -8.911e-02, -5.182e-04, 1.592e-02), r0);
	r0 = MulAdd(s0_0_2, M4(1.837e-02, 1.590e-02, -5.851e-04, -1.591e-02, 2.044e-03, -3.361e-02, 1.057e-02, 1.349e-02, 1.272e-02, -6.750e-03, 7.907e-03, -1.285e-02, -1.592e-02, 9.610e-04, -9.432e-03, 8.813e-03), r0);
	r0 = MulAdd(s0_1_0, M4(8.667e-02, -9.242e-03, 3.318e-02, 1.916e-02, 6.151e-02, 2.082e-02, 3.235e-02, -2.143e-02, 5.009e-02, -1.719e-02, 1.851e-01, -1.685e-02, 2.506e-02, -3.894e-03, 1.690e-03, 2.377e-02), r0);
	r0 = MulAdd(s0_1_1, M4(-8.387e-01, -1.761e-01, 3.328e-01, 5.308e-02, 2.998e-01, 4.975e-02, -7.793e-01, -1.165e-01, -5.922e-02, 1.125e-01, 9.888e-02, 4.112e-01, 2.311e-01, 3.285e-01, 1.176e-02, -2.353e-01), r0);
	r0 = MulAdd(s0_1_2, M4(-3.505e-02, -1.204e-01, -3.650e-02, 3.279e-02, 2.166e-02, 1.921e-02, 4.179e-02, -1.014e-01, 1.004e-02, -3.576e-02, 1.460e-02, -1.919e-02, -8.401e-03, 5.749e-02, -1.101e-02, 4.334e-02), r0);
	r0 = MulAdd(s0_2_0, M4(1.645e-02, 5.136e-04, 1.847e-02, 1.850e-02, -5.264e-03, 1.014e-03, 1.631e-02, 7.070e-03, -1.447e-03, -3.175e-03, -3.604e-02, -1.518e-02, 1.477e-05, -1.200e-03, 5.377e-02, -3.313e-03), r0);
	r0 = MulAdd(s0_2_1, M4(3.565e-02, 5.328e-03, 4.944e-02, -7.376e-03, -2.322e-03, 6.952e-04, 2.526e-02, -4.164e-03, -5.473e-03, 3.168e-03, -8.765e-02, -6.798e-02, -4.066e-03, -7.083e-03, 1.200e-01, 1.899e-01), r0);
	r0 = MulAdd(s0_2_2, M4(1.376e-02, 5.270e-03, 2.451e-02, -3.066e-02, -1.031e-03, -8.212e-04, -1.497e-02, 1.617e-04, -6.968e-03, 2.039e-04, -6.910e-03, -1.776e-02, 2.744e-03, 5.319e-04, 8.148e-03, 1.788e-02), r0);
	r0 = MulAdd(s1_0_0, M4(-1.572e-02, 8.821e-03, -1.483e-02, 2.154e-02, -9.811e-03, -2.851e-03, 2.289e-03, -3.321e-03, -4.134e-02, -7.724e-03, 4.346e-03, -9.430e-04, -4.933e-03, 3.370e-03, -5.796e-03, 8.162e-03), r0);
	r0 = MulAdd(s1_0_1, M4(5.311e-02, -1.421e-01, 1.289e-02, 3.699e-02, 2.606e-02, -7.378e-03, 5.391e-03, -6.596e-03, -3.749e-02, -7.154e-02, -1.086e-03, 6.008e-03, 2.401e-02, -1.457e-02, -2.020e-02, 6.355e-03), r0);
	r0 = MulAdd(s1_0_2, M4(-2.142e-02, 4.039e-02, -1.041e-02, 9.822e-03, 3.846e-02, 1.240e-01, 3.890e-03, -1.742e-03, -2.683e-03, 7.338e-03, -4.240e-04, 4.985e-03, -6.563e-03, 2.869e-03, 4.070e-03, 4.858e-03), r0);
	r0 = MulAdd(s1_1_0, M4(9.836e-02, 2.372e-03, 1.294e-01, -3.218e-03, -6.737e-02, -7.906e-03, -1.745e-02, -6.910e-03, 1.958e-01, 3.296e-02, -1.284e-01, -3.370e-02, -1.589e-02, -3.011e-02, -3.112e-03, -1.329e-02), r0);
	r0 = MulAdd(s1_1_1, M4(3.337e-01, -3.467e-01, 3.918e-01, -5.527e-01, -1.231e-01, 6.421e-02, 1.877e-02, 4.993e-02, 1.997e-01, 3.447e-01, -8.720e-02, -1.753e-01, -5.701e-01, 4.404e-01, -9.540e-02, 1.248e-01), r0);
	r0 = MulAdd(s1_1_2, M4(-1.848e-02, 7.104e-02, -3.674e-02, 7.264e-02, 3.116e-02, -8.314e-01, 1.517e-01, 3.116e-01, 2.196e-03, 3.479e-02, 3.625e-03, -7.317e-03, -4.041e-02, 9.449e-02, -3.724e-02, 1.484e-02), r0);
	r0 = MulAdd(s1_2_0, M4(-2.451e-02, 4.403e-03, -5.063e-03, 4.535e-03, -1.594e-02, -2.546e-03, -3.374e-02, -1.276e-02, -5.974e-02, -8.156e-03, -8.276e-02, 6.096e-02, -9.513e-03, 9.127e-04, -8.361e-03, -2.912e-02), r0);
	r0 = MulAdd(s1_2_1, M4(-7.426e-03, 4.917e-03, 1.844e-02, -1.523e-02, -2.838e-02, -5.470e-03, 2.448e-02, -2.177e-02, -4.583e-02, -2.253e-02, 7.540e-02, -3.926e-01, -1.423e-02, 2.884e-02, -4.344e-01, 3.271e-01), r0);
	r0 = MulAdd(s1_2_2, M4(3.116e-03, -2.670e-03, 2.760e-03, 2.948e-02, -3.235e-02, 1.630e-02, -2.941e-02, 1.160e-01, -1.131e-02, -9.327e-03, -2.012e-02, 4.236e-02, -5.858e-03, -1.082e-02, -2.096e-02, 9.844e-02), r0);
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
