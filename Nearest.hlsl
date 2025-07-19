cbuffer __CB1 : register(b0) {
	uint2 __inputSize;
	uint2 __outputSize;
	float2 __inputPt;
	float2 __outputPt;
	float2 __scale;
};

#define MF4 float4
Texture2D<MF4> INPUT : register(t0);
RWTexture2D<unorm MF4> OUTPUT : register(u0);
SamplerState sam : register(s0);

uint __Bfe(uint src, uint off, uint bits) { uint mask = (1u << bits) - 1; return (src >> off) & mask; }
uint __BfiM(uint src, uint ins, uint bits) { uint mask = (1u << bits) - 1; return (ins & mask) | (src & (~mask)); }
uint2 Rmp8x8(uint a) { return uint2(__Bfe(a, 1u, 3u), __BfiM(__Bfe(a, 3u, 3u), a, 1u)); }
uint2 GetInputSize() { return __inputSize; }
float2 GetInputPt() { return __inputPt; }
uint2 GetOutputSize() { return __outputSize; }
float2 GetOutputPt() { return __outputPt; }
float2 GetScale() { return __scale; }

float4 Pass1(float2 pos) {
	return INPUT.SampleLevel(sam, pos, 0);
}

[numthreads(64, 1, 1)]
void main(uint3 tid : SV_GroupThreadID, uint3 gid : SV_GroupID) {
	uint2 gxy = (gid.xy << 4u) + Rmp8x8(tid.x);
	if (gxy.x >= __outputSize.x || gxy.y >= __outputSize.y) {
		return;
	}
	float2 pos = (gxy + 0.5f) * __outputPt;
	float2 step = 8 * __outputPt;

	OUTPUT[gxy] = Pass1(pos);

	gxy.x += 8u;
	pos.x += step.x;
	if (gxy.x < __outputSize.x && gxy.y < __outputSize.y) {
		OUTPUT[gxy] = Pass1(pos);
	}
	
	gxy.y += 8u;
	pos.y += step.y;
	if (gxy.x < __outputSize.x && gxy.y < __outputSize.y) {
		OUTPUT[gxy] = Pass1(pos);
	}
	
	gxy.x -= 8u;
	pos.x -= step.x;
	if (gxy.x < __outputSize.x && gxy.y < __outputSize.y) {
		OUTPUT[gxy] = Pass1(pos);
	}
}
