cbuffer __CB1 : register(b0) {
	uint2 __inputSize;
	uint2 __outputSize;
	float2 __inputPt;
	float2 __outputPt;
	float2 __scale;
};


Texture2D<MF4> INPUT : register(t0);
RWTexture2D<unorm MF4> T0 : register(u0);
RWTexture2D<unorm MF4> T1 : register(u1);
RWTexture2D<unorm MF4> T2 : register(u2);
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

#define L0(x, y) MF(dot(MF3(0.299, 0.587, 0.114), O(INPUT, x, y).rgb))

void Pass1(uint2 blockStart, uint3 tid) {
	float2 pt = float2(GetInputPt());
	uint2 gxy = Rmp8x8(tid.x) + blockStart;
	uint2 sz = GetInputSize();
	if (gxy.x >= sz.x || gxy.y >= sz.y)
		return;
	float2 pos = (gxy + 0.5) * pt;
	MF s0_0_0, s0_0_1, s0_0_2, s0_1_0, s0_1_1, s0_1_2, s0_2_0, s0_2_1, s0_2_2;
	V4 r0 = 0.0, r1 = 0.0, r2 = 0.0;
	r0 = V4(-7.280e-05, 1.400e-04, -1.296e-04, 4.014e-04);
	r1 = V4(-1.023e-03, 2.540e-04, 1.793e-03, -4.770e-03);
	r2 = V4(-5.813e-04, 2.326e-02, 2.179e-02, 3.161e-03);
	s0_0_0 = L0(-1.0, -1.0); s0_0_1 = L0(0.0, -1.0); s0_0_2 = L0(1.0, -1.0);
	s0_1_0 = L0(-1.0, 0.0); s0_1_1 = L0(0.0, 0.0); s0_1_2 = L0(1.0, 0.0);
	s0_2_0 = L0(-1.0, 1.0); s0_2_1 = L0(0.0, 1.0); s0_2_2 = L0(1.0, 1.0);
	r0 = mad(s0_0_0, V4(3.974e-03, -4.994e-02, -1.106e-01, 7.984e-02), r0);
	r1 = mad(s0_0_0, V4(-1.146e-02, 2.714e-02, -1.208e-01, -5.811e-03), r1);
	r2 = mad(s0_0_0, V4(2.306e-02, -1.984e-02, -1.205e-02, -5.797e-03), r2);
	r0 = mad(s0_0_1, V4(8.621e-01, 4.326e-01, 5.918e-01, -1.650e-01), r0);
	r1 = mad(s0_0_1, V4(5.566e-03, -1.528e-01, 1.548e-01, -3.752e-01), r1);
	r2 = mad(s0_0_1, V4(-2.113e-02, -2.094e-04, 6.522e-02, -5.227e-02), r2);
	r0 = mad(s0_0_2, V4(1.085e-02, -1.058e-01, -7.681e-03, -8.618e-02), r0);
	r1 = mad(s0_0_2, V4(2.526e-03, -1.193e-01, 1.655e-01, 2.262e-02), r1);
	r2 = mad(s0_0_2, V4(4.877e-03, 8.765e-03, 9.976e-03, 3.630e-02), r2);
	r0 = mad(s0_1_0, V4(-6.514e-03, -1.627e-02, 9.897e-02, 3.289e-02), r0);
	r1 = mad(s0_1_0, V4(7.988e-01, 3.223e-02, 3.274e-02, -2.993e-01), r1);
	r2 = mad(s0_1_0, V4(2.822e-03, -4.395e-03, 3.037e-01, -2.012e-01), r2);
	r0 = mad(s0_1_1, V4(-8.652e-01, -1.159e-02, 8.169e-02, 4.252e-01), r0);
	r1 = mad(s0_1_1, V4(-7.781e-01, 4.338e-01, 2.879e-01, 7.549e-01), r1);
	r2 = mad(s0_1_1, V4(6.310e-01, -1.011e-01, -2.446e-01, 5.293e-01), r2);
	r0 = mad(s0_1_2, V4(-5.410e-03, -9.159e-02, -6.371e-01, -6.387e-01), r0);
	r1 = mad(s0_1_2, V4(-1.319e-02, -1.619e-01, 2.345e-01, -8.862e-02), r1);
	r2 = mad(s0_1_2, V4(-1.833e-02, 3.118e-02, 2.168e-02, -4.513e-02), r2);
	r0 = mad(s0_2_0, V4(5.906e-05, -6.218e-03, 2.289e-02, -1.228e-01), r0);
	r1 = mad(s0_2_0, V4(-1.375e-02, 1.999e-02, 9.690e-02, 1.443e-02), r1);
	r2 = mad(s0_2_0, V4(2.581e-02, -1.284e-01, 3.156e-02, -6.670e-02), r2);
	r0 = mad(s0_2_1, V4(2.334e-03, -4.197e-03, -1.160e-01, 3.487e-01), r0);
	r1 = mad(s0_2_1, V4(2.869e-03, -2.522e-02, -4.490e-01, 8.423e-02), r1);
	r2 = mad(s0_2_1, V4(-5.647e-03, 3.777e-01, -1.097e-01, -1.901e-01), r2);
	r0 = mad(s0_2_2, V4(-4.110e-03, 1.439e-03, 7.400e-02, 1.250e-01), r0);
	r1 = mad(s0_2_2, V4(6.177e-03, 1.872e-02, -4.033e-01, -1.047e-01), r1);
	r2 = mad(s0_2_2, V4(1.412e-02, 1.066e-02, -2.194e-02, 2.292e-02), r2);
	r0 = max(r0, 0.0);
	T0[gxy] = r0;
	r1 = max(r1, 0.0);
	T1[gxy] = r1;
	r2 = max(r2, 0.0);
	T2[gxy] = r2;
}

[numthreads(64, 1, 1)]
void __M(uint3 tid : SV_GroupThreadID, uint3 gid : SV_GroupID) {
	Pass1((gid.xy << 3), tid);
}
