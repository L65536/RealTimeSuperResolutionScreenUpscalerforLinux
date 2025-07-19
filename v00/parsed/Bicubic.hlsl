cbuffer __CB1 : register(b0) {
	uint2 __inputSize;
	uint2 __outputSize;
	float2 __inputPt;
	float2 __outputPt;
	float2 __scale;
};

static const float paramB = 0.000000f;
static const float paramC = 0.500000f;
static const float paramBx = 0.330000f;
static const float paramCx = 0.330000f;

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

float weight(float x) {
	const float B = paramB;
	const float C = paramC;

	float ax = abs(x);

	if (ax < 1.0) {
		return (x * x * ((12.0 - 9.0 * B - 6.0 * C) * ax + (-18.0 + 12.0 * B + 6.0 * C)) + (6.0 - 2.0 * B)) / 6.0;
	} else if (ax >= 1.0 && ax < 2.0) {
		return (x * x * ((-B - 6.0 * C) * ax + (6.0 * B + 30.0 * C)) + (-12.0 * B - 48.0 * C) * ax + (8.0 * B + 24.0 * C)) / 6.0;
	} else {
		return 0.0;
	}
}

float4 weight4(float x) {
	return float4(
		weight(x - 2.0),
		weight(x - 1.0),
		weight(x),
		weight(x + 1.0)
	);
}


float4 Pass1(float2 pos) {
	const float2 inputPt = GetInputPt();
	const float2 inputSize = GetInputSize();

	pos *= inputSize;
	float2 pos1 = floor(pos - 0.5) + 0.5;
	float2 f = pos - pos1;

	float4 rowtaps = weight4(1 - f.x);
	float4 coltaps = weight4(1 - f.y);

	
	rowtaps /= rowtaps.r + rowtaps.g + rowtaps.b + rowtaps.a;
	coltaps /= coltaps.r + coltaps.g + coltaps.b + coltaps.a;

	float2 uv1 = pos1 * inputPt;
	float2 uv0 = uv1 - inputPt;
	float2 uv2 = uv1 + inputPt;
	float2 uv3 = uv2 + inputPt;

	float u_weight_sum = rowtaps.y + rowtaps.z;
	float u_middle_offset = rowtaps.z * inputPt.x / u_weight_sum;
	float u_middle = uv1.x + u_middle_offset;

	float v_weight_sum = coltaps.y + coltaps.z;
	float v_middle_offset = coltaps.z * inputPt.y / v_weight_sum;
	float v_middle = uv1.y + v_middle_offset;

	int2 coord_top_left = int2(max(uv0 * inputSize, 0.5));
	int2 coord_bottom_right = int2(min(uv3 * inputSize, inputSize - 0.5));

	float3 top = INPUT.Load(int3(coord_top_left, 0)).rgb * rowtaps.x;
	top += INPUT.SampleLevel(sam, float2(u_middle, uv0.y), 0).rgb * u_weight_sum;
	top += INPUT.Load(int3(coord_bottom_right.x, coord_top_left.y, 0)).rgb * rowtaps.w;
	float3 total = top * coltaps.x;

	float3 middle = INPUT.SampleLevel(sam, float2(uv0.x, v_middle), 0).rgb * rowtaps.x;
	middle += INPUT.SampleLevel(sam, float2(u_middle, v_middle), 0).rgb * u_weight_sum;
	middle += INPUT.SampleLevel(sam, float2(uv3.x, v_middle), 0).rgb * rowtaps.w;
	total += middle * v_weight_sum;

	float3 bottom = INPUT.Load(int3(coord_top_left.x, coord_bottom_right.y, 0)).rgb * rowtaps.x;
	bottom += INPUT.SampleLevel(sam, float2(u_middle, uv3.y), 0).rgb * u_weight_sum;
	bottom += INPUT.Load(int3(coord_bottom_right, 0)).rgb * rowtaps.w;
	total += bottom * coltaps.w;

	return float4(total, 1);
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
