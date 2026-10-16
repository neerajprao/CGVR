// Lab 8 in Unity: the same vertex and fragment shaders as Lab8/main.py, written in HLSL.
// Unity supplies uModel, uView and uProjection as built-in matrices (unity_ObjectToWorld,
// UNITY_MATRIX_V, UNITY_MATRIX_P); _Mode and _LightPos are set from ShaderController.cs.
Shader "Lab8/CubeShader"
{
    Properties
    {
        // 0 = vertex colors, 1 = per-fragment lighting, 2 = normals as colors
        _Mode ("Fragment Shader Mode", Integer) = 0
        _LightPos ("Light Position (world)", Vector) = (3, 4, -5, 0)
    }

    SubShader
    {
        Tags { "RenderType" = "Opaque" "RenderPipeline" = "UniversalPipeline" "Queue" = "Geometry" }

        Pass
        {
            Name "Lab8"

            // Hidden surface removal by the GPU's depth buffer (see Lab 6)
            ZWrite On
            ZTest LEqual
            Cull Back

            HLSLPROGRAM
            #pragma vertex vert
            #pragma fragment frag

            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
            #include "Packages/com.unity.render-pipelines.core/ShaderLibrary/Color.hlsl"

            // Vertex attributes, read from the mesh (Lab 8: aPosition, aColor, aNormal)
            struct Attributes
            {
                float3 positionOS : POSITION;
                float4 color      : COLOR;
                float3 normalOS   : NORMAL;
            };

            // Passed from the vertex shader to the fragment shader, interpolated across each triangle
            struct Varyings
            {
                float4 positionCS : SV_POSITION;
                float3 color      : COLOR;
                float3 normalWS   : TEXCOORD0;
                float3 positionWS : TEXCOORD1;
            };

            CBUFFER_START(UnityPerMaterial)
                int _Mode;
                float4 _LightPos;
            CBUFFER_END

            // Vertex shader: runs once per vertex
            Varyings vert(Attributes input)
            {
                Varyings output;

                // world = uModel * position
                float3 world = TransformObjectToWorld(input.positionOS);

                output.positionWS = world;
                output.normalWS = TransformObjectToWorldNormal(input.normalOS);
                output.color = input.color.rgb;

                // gl_Position = uProjection * uView * world
                output.positionCS = TransformWorldToHClip(world);

                return output;
            }

            // Lab 8 writes its colors straight to the screen; Unity works in linear
            // color space, so convert to linear to make the colors look the same
            half4 ToScreen(float3 color)
            {
            #if defined(UNITY_COLORSPACE_GAMMA)
                return half4(color, 1.0);
            #else
                return half4(SRGBToLinear(saturate(color)), 1.0);
            #endif
            }

            // Fragment shader: runs once per pixel (fragment)
            half4 frag(Varyings input) : SV_Target
            {
                // Mode 0: color interpolated from the vertices
                if (_Mode == 0)
                    return ToScreen(input.color);

                float3 N = normalize(input.normalWS);

                // Mode 2: normal vector shown as a color. Z is flipped back to
                // OpenGL's right-handed axes so the colors match Lab 8
                if (_Mode == 2)
                    return ToScreen(N * float3(1.0, 1.0, -1.0) * 0.5 + 0.5);

                // Mode 1: per-fragment Phong lighting
                float3 L = normalize(_LightPos.xyz - input.positionWS);
                float3 V = normalize(_WorldSpaceCameraPos - input.positionWS);
                float3 R = reflect(-L, N);

                float n_dot_l = max(dot(N, L), 0.0);

                float ambient = 0.15;
                float diffuse = 0.7 * n_dot_l;
                float specular = n_dot_l > 0.0 ? 0.5 * pow(max(dot(R, V), 0.0), 32.0) : 0.0;

                return ToScreen((ambient + diffuse) * input.color + specular);
            }
            ENDHLSL
        }
    }
}
