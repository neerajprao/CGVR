// Lab 10 in Unity: the same vertex and fragment shaders as Lab10/main.py, written in HLSL.
// UNITY_MATRIX_V and UNITY_MATRIX_P are the look-at and projection matrices that
// ViewingPipeline.cs builds by hand and hands to each camera.
Shader "Lab10/VertexColor"
{
    SubShader
    {
        Tags { "RenderType" = "Opaque" "RenderPipeline" = "UniversalPipeline" "Queue" = "Geometry" }

        Pass
        {
            Name "Lab10"

            // 6. Depth testing: hidden surface removal by the GPU's depth buffer (see Lab 6).
            // Like Lab 10 there is no face culling, the depth test alone hides the back faces
            ZWrite On
            ZTest LEqual
            Cull Off

            HLSLPROGRAM
            #pragma vertex vert
            #pragma fragment frag

            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
            #include "Packages/com.unity.render-pipelines.core/ShaderLibrary/Color.hlsl"

            // Vertex attributes, read from the mesh (Lab 10: aPosition, aColor)
            struct Attributes
            {
                float3 positionOS : POSITION;
                float4 color      : COLOR;
            };

            struct Varyings
            {
                float4 positionCS : SV_POSITION;
                float3 color      : COLOR;
            };

            // Vertex shader: Model -> View -> Projection.
            // The GPU then does the perspective division and the viewport mapping
            Varyings vert(Attributes input)
            {
                Varyings output;

                // worldPosition = uModel * position
                float3 worldPosition = TransformObjectToWorld(input.positionOS);

                // viewPosition = uView * worldPosition
                float3 viewPosition = TransformWorldToView(worldPosition);

                // gl_Position = uProjection * viewPosition
                output.positionCS = TransformWViewToHClip(viewPosition);
                output.color = input.color.rgb;

                return output;
            }

            // Fragment shader: the color interpolated from the vertices.
            // Lab 10 writes its colors straight to the screen; Unity works in linear
            // color space, so convert to linear to make the colors look the same
            half4 frag(Varyings input) : SV_Target
            {
            #if defined(UNITY_COLORSPACE_GAMMA)
                return half4(input.color, 1.0);
            #else
                return half4(SRGBToLinear(saturate(input.color)), 1.0);
            #endif
            }
            ENDHLSL
        }
    }
}
