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
	V4 r0 = 0.0, r1 = 0.0;
	r0 = V4(-1.467e-03, -2.492e-04, -6.573e-04, -6.401e-04);
	r1 = V4(-4.736e-03, 7.443e-03, 2.352e-03, -8.863e-04);
	s0_0_0 = L0(-1.0, -1.0); s0_0_1 = L0(0.0, -1.0); s0_0_2 = L0(1.0, -1.0);
	s0_1_0 = L0(-1.0, 0.0); s0_1_1 = L0(0.0, 0.0); s0_1_2 = L0(1.0, 0.0);
	s0_2_0 = L0(-1.0, 1.0); s0_2_1 = L0(0.0, 1.0); s0_2_2 = L0(1.0, 1.0);
	r0 = mad(s0_0_0, V4(-3.649e-02, 6.494e-03, 6.929e-03, -1.320e-02), r0);
	r1 = mad(s0_0_0, V4(-2.453e-01, 2.722e-02, -7.841e-02, -8.301e-01), r1);
	r0 = mad(s0_0_1, V4(-5.663e-02, 2.213e-03, -9.981e-03, 7.036e-03), r0);
	r1 = mad(s0_0_1, V4(-2.193e-01, 5.934e-04, -3.767e-02, -6.469e-02), r1);
	r0 = mad(s0_0_2, V4(-5.772e-02, -7.180e-03, 4.832e-03, -4.077e-03), r0);
	r1 = mad(s0_0_2, V4(3.104e-02, 3.213e-03, 8.831e-02, -1.925e-02), r1);
	r0 = mad(s0_1_0, V4(-1.444e-01, 2.094e-03, -8.605e-01, -3.923e-02), r0);
	r1 = mad(s0_1_0, V4(1.032e-01, 4.432e-02, 3.857e-01, 8.655e-01), r1);
	r0 = mad(s0_1_1, V4(7.103e-01, 8.262e-01, 8.574e-01, 6.191e-01), r0);
	r1 = mad(s0_1_1, V4(8.105e-01, -8.463e-02, -5.097e-01, 4.015e-02), r1);
	r0 = mad(s0_1_2, V4(-8.078e-02, -1.313e-01, -2.669e-04, 3.881e-02), r0);
	r1 = mad(s0_1_2, V4(-1.696e-01, -3.874e-02, 1.460e-01, 1.208e-02), r1);
	r0 = mad(s0_2_0, V4(-5.270e-02, -9.660e-03, 3.139e-03, 5.236e-02), r0);
	r1 = mad(s0_2_0, V4(8.130e-02, 2.059e-01, 1.882e-01, -3.923e-02), r1);
	r0 = mad(s0_2_1, V4(-1.171e-01, -7.569e-01, 9.770e-04, -6.428e-02), r0);
	r1 = mad(s0_2_1, V4(-2.483e-01, 3.656e-02, -2.046e-01, 3.488e-02), r1);
	r0 = mad(s0_2_2, V4(1.227e-02, 6.710e-02, -5.071e-03, 3.497e-02), r0);
	r1 = mad(s0_2_2, V4(-1.450e-01, 6.362e-02, 2.222e-02, -1.415e-03), r1);
	r0 = max(r0, 0.0);
	T0[gxy] = r0;
	r1 = max(r1, 0.0);
	T1[gxy] = r1;
}

[numthreads(64, 1, 1)]
void __M(uint3 tid : SV_GroupThreadID, uint3 gid : SV_GroupID) {
	Pass1((gid.xy << 3), tid);
}
