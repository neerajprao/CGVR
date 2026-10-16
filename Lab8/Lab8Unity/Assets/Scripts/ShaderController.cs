using UnityEngine;
using UnityEngine.InputSystem;

// Spins the cube and sends the shader its uniforms (_Mode, _LightPos).
// M switches the fragment shader mode, Space pauses the rotation.
[RequireComponent(typeof(MeshFilter), typeof(MeshRenderer))]
public class ShaderController : MonoBehaviour
{
    public enum Mode { VertexColors, Lighting, Normals }

    static readonly string[] ModeNames =
    {
        "Vertex colors (interpolated)",
        "Per-fragment lighting (Phong)",
        "Normals as colors",
    };

    static readonly int ModeId = Shader.PropertyToID("_Mode");
    static readonly int LightPosId = Shader.PropertyToID("_LightPos");

    public float speed = 45f; // degrees per second
    public Mode mode = Mode.VertexColors;
    public Transform lightSource; // its position is the shader's light position
    public bool paused;

    MeshRenderer rend;
    MaterialPropertyBlock uniforms;
    float angle;

    void Start()
    {
        rend = GetComponent<MeshRenderer>();
        uniforms = new MaterialPropertyBlock();

        PrintInfo();
    }

    void Update()
    {
        var kb = Keyboard.current;
        if (kb != null)
        {
            if (kb.mKey.wasPressedThisFrame)
            {
                mode = (Mode)(((int)mode + 1) % ModeNames.Length);
                Debug.Log($"Fragment shader mode: {ModeNames[(int)mode]}");
            }

            if (kb.spaceKey.wasPressedThisFrame)
                paused = !paused;
        }

        if (!paused)
            angle += speed * Time.deltaTime;

        // Model matrix: Lab 8's rotation_x(25) * rotation_y(angle).
        // The angles are negated because Unity is left-handed (see CubeMesh.ToUnity).
        transform.rotation = Quaternion.Euler(-25f, 0f, 0f) * Quaternion.Euler(0f, -angle, 0f);

        // Uniforms: per-frame values shared by every vertex / fragment
        uniforms.SetInteger(ModeId, (int)mode);
        if (lightSource != null)
            uniforms.SetVector(LightPosId, lightSource.position);
        rend.SetPropertyBlock(uniforms);
    }

    void PrintInfo()
    {
        Debug.Log($"Graphics API: {SystemInfo.graphicsDeviceVersion}\n" +
                  $"Renderer    : {SystemInfo.graphicsDeviceName}\n" +
                  $"Shader model: {SystemInfo.graphicsShaderLevel / 10f:0.0}");

        Shader shader = rend.sharedMaterial.shader;
        Debug.Log($"Shader {shader.name}: {(shader.isSupported ? "compiled and supported: OK" : "NOT supported")}");

        Mesh mesh = GetComponent<MeshFilter>().sharedMesh;
        uint indexCount = mesh.GetIndexCount(0);

        string layout = $"Vertices : {mesh.vertexCount} ({mesh.GetVertexBufferStride(0)} bytes each)\n" +
                        $"Indices  : {indexCount} ({indexCount / 3} triangles)";

        foreach (var attribute in mesh.GetVertexAttributes())
            layout += $"\n{attribute.attribute,-8}: {attribute.format} x {attribute.dimension}, " +
                      $"byte offset {mesh.GetVertexAttributeOffset(attribute.attribute)}";

        Debug.Log(layout);
        Debug.Log("Uniforms: unity_ObjectToWorld (model), UNITY_MATRIX_V (view), UNITY_MATRIX_P (projection), _Mode, _LightPos, _WorldSpaceCameraPos");
        Debug.Log($"Fragment shader mode: {ModeNames[(int)mode]}\nM: switch fragment shader mode   Space: pause rotation");
    }

    void OnGUI()
    {
        GUI.Label(new Rect(10, 10, 600, 40),
            $"{ModeNames[(int)mode]}{(paused ? "  (paused)" : "")}\nM: switch mode   Space: pause");
    }
}
