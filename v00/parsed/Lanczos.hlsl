cbuffer __CB1 : register(b0) {
	uint2 __inputSize;
	uint2 __outputSize;
	float2 __inputPt;
	float2 __outputPt;
	float2 __scale;
};

static const float ARStrength = 0.500000f;

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

#define FIX(c) max(abs(c), 1e-5)
#define PI 3.14159265359
#define min4(a, b, c, d) min(min(a, b), min(c, d))
#define max4(a, b, c, d) max(max(a, b), max(c, d))

float3 weight3(float x) {
	const float rcpRadius = 1.0f / 3.0f;
	float3 s = FIX(2.0 * PI * float3(x - 1.5, x - 0.5, x + 0.5));
	
	return  sin(s) * sin(s * rcpRadius) * rcp(s * s);
}

float4 Pass1(float2 pos) {
	pos *= GetInputSize();
	float2 inputPt = GetInputPt();

	uint i, j;

	float2 f = frac(pos.xy + 0.5f);
	float3 linetaps1 = weight3(0.5f - f.x * 0.5f);
	float3 linetaps2 = weight3(1.0f - f.x * 0.5f);
	float3 columntaps1 = weight3(0.5f - f.y * 0.5f);
	float3 columntaps2 = weight3(1.0f - f.y * 0.5f);

	
	
	float suml = dot(linetaps1, float3(1, 1, 1)) + dot(linetaps2, float3(1, 1, 1));
	float sumc = dot(columntaps1, float3(1, 1, 1)) + dot(columntaps2, float3(1, 1, 1));
	linetaps1 /= suml;
	linetaps2 /= suml;
	columntaps1 /= sumc;
	columntaps2 /= sumc;

	pos -= f + 1.5f;

	float3 src[6][6];

	[unroll]
	for (i = 0; i <= 4; i += 2) {
		[unroll]
		for (j = 0; j <= 4; j += 2) {
			float2 tpos = (pos + uint2(i, j)) * inputPt;
			const float4 sr = INPUT.GatherRed(sam, tpos);
			const float4 sg = INPUT.GatherGreen(sam, tpos);
			const float4 sb = INPUT.GatherBlue(sam, tpos);

			
			
			src[i][j] = float3(sr.w, sg.w, sb.w);
			src[i][j + 1] = float3(sr.x, sg.x, sb.x);
			src[i + 1][j] = float3(sr.z, sg.z, sb.z);
			src[i + 1][j + 1] = float3(sr.y, sg.y, sb.y);
		}
	}

	

	float3 color = float3(0, 0, 0);
	[unroll]
	for (i = 0; i <= 4; i += 2) {
		color += (mul(linetaps1, float3x3(src[0][i], src[2][i], src[4][i])) + mul(linetaps2, float3x3(src[1][i], src[3][i], src[5][i]))) * columntaps1[i / 2] + (mul(linetaps1, float3x3(src[0][i + 1], src[2][i + 1], src[4][i + 1])) + mul(linetaps2, float3x3(src[1][i + 1], src[3][i + 1], src[5][i + 1]))) * columntaps2[i / 2];
	}

	
	float3 min_sample = min4(src[2][2], src[3][2], src[2][3], src[3][3]);
	float3 max_sample = max4(src[2][2], src[3][2], src[2][3], src[3][3]);
	color = lerp(color, clamp(color, min_sample, max_sample), ARStrength);

	return float4(color, 1);
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
