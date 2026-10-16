using System.Text;
using UnityEngine;
using UnityEngine.InputSystem;

// Lab 10's 3D viewing pipeline:
//   1. model (object -> world)   2. view (world -> eye, look-at camera)
//   3. projection (eye -> clip)   4. perspective division (clip -> NDC)
//   5. viewport mapping (NDC -> window pixels)   6. depth testing
// The view and projection matrices are built here exactly as in Lab10/main.py and handed
// to the two cameras, so the GPU draws with the same numbers the trace prints.
// Left/Right: orbit the camera   Space: pause   T: print the pipeline   Esc: stop
[ExecuteAlways]
public class ViewingPipeline : MonoBehaviour
{
    [Header("Scene")]
    public Transform cube;
    public Camera perspectiveCamera;  // left viewport
    public Camera orthographicCamera; // right viewport

    [Header("Camera and view volume")]
    public Vector3 cameraPosition = new Vector3(3f, 2f, 6f);
    public Vector3 target = Vector3.zero;
    public Vector3 up = Vector3.up;
    public float fov = 45f;
    public float near = 0.1f;
    public float far = 100f;
    public float orthoSize = 2.5f; // half-height of the orthographic view volume
    public float orbitStep = 10f;

    [Header("Animation")]
    public float speed = 45f; // degrees per second
    public bool paused;

    float angle;
    float orbit;
    bool trace = true; // print the pipeline for the first frame

    void Start()
    {
        if (!Application.isPlaying) return;

        Debug.Log("3D VIEWING PIPELINE\n" +
                  "1. Model transformation      (object -> world)\n" +
                  "2. View transformation       (world -> eye, look-at camera)\n" +
                  "3. Projection                (eye -> clip, perspective / orthographic)\n" +
                  "4. Perspective division      (clip -> NDC)\n" +
                  "5. Viewport mapping          (NDC -> window pixels)\n" +
                  "6. Depth testing             (hidden surface removal)");

        Debug.Log($"Graphics API: {SystemInfo.graphicsDeviceVersion}\nRenderer: {SystemInfo.graphicsDeviceName}");

        Mesh mesh = cube.GetComponent<MeshFilter>().sharedMesh;
        uint indexCount = mesh.GetIndexCount(0);
        Debug.Log($"Vertices: {mesh.vertexCount}\nIndices: {indexCount}\nTriangles: {indexCount / 3}");

        Debug.Log("Left viewport: perspective   Right viewport: orthographic\n" +
                  "Left/Right: orbit camera   Space: pause   T: print pipeline   Esc: stop");
    }

    void OnValidate()
    {
        if ((cameraPosition - target).sqrMagnitude < 1e-6f)
            Debug.LogWarning("Camera cannot be at the target point");
    }

    void OnDisable()
    {
        foreach (Camera cam in new[] { perspectiveCamera, orthographicCamera })
        {
            if (cam == null) continue;
            cam.ResetWorldToCameraMatrix();
            cam.ResetProjectionMatrix();
        }
    }

    void Update()
    {
        if (Application.isPlaying)
        {
            HandleInput();

            if (!paused)
                angle += speed * Time.deltaTime;
        }

        Apply();
    }

    void HandleInput()
    {
        var kb = Keyboard.current;
        if (kb == null) return;

        if (kb.leftArrowKey.wasPressedThisFrame) orbit -= orbitStep;
        if (kb.rightArrowKey.wasPressedThisFrame) orbit += orbitStep;
        if (kb.spaceKey.wasPressedThisFrame) paused = !paused;
        if (kb.tKey.wasPressedThisFrame) trace = true;

        if (kb.escapeKey.wasPressedThisFrame)
        {
#if UNITY_EDITOR
            UnityEditor.EditorApplication.isPlaying = false;
#else
            Application.Quit();
#endif
        }
    }

    // Runs every frame (also in Edit mode, so the Game view preview matches Play mode)
    public void Apply()
    {
        if (cube == null || perspectiveCamera == null || orthographicCamera == null) return;
        if ((cameraPosition - target).sqrMagnitude < 1e-6f) return;

        // 1. Model transformation: rotation_x(25) * rotation_y(angle)
        cube.rotation = Quaternion.Euler(25f, 0f, 0f) * Quaternion.Euler(0f, angle, 0f);
        Matrix4x4 model = cube.localToWorldMatrix;

        // 2. View transformation: orbit the camera around the Y-axis, then look at the target
        Vector3 eye = Quaternion.Euler(0f, orbit, 0f) * cameraPosition;
        Matrix4x4 view = LookAt(eye, target, up);

        bool print = trace && Application.isPlaying;

        if (print)
            Debug.Log($"Camera eye: {Fmt(eye)}   Model angle: {Mathf.Repeat(angle, 360f):F1} deg");

        SetUpCamera(perspectiveCamera, "Perspective", false, eye, model, view, print);
        SetUpCamera(orthographicCamera, "Orthographic", true, eye, model, view, print);

        if (print)
            trace = false;
    }

    void SetUpCamera(Camera cam, string name, bool orthographic, Vector3 eye,
                     Matrix4x4 model, Matrix4x4 view, bool print)
    {
        // 5. Viewport: this camera's rectangle of the window, in pixels
        Rect viewport = cam.pixelRect;
        float aspect = viewport.width / Mathf.Max(1f, viewport.height);

        // 3. Projection
        Matrix4x4 projection = orthographic
            ? Orthographic(-orthoSize * aspect, orthoSize * aspect, -orthoSize, orthoSize, near, far)
            : Perspective(fov, aspect, near, far);

        // Hand our matrices to the camera: the GPU now uses them instead of Unity's own
        cam.worldToCameraMatrix = view;
        cam.projectionMatrix = projection;

        // Keep the camera object at the eye, for the Scene view gizmo
        cam.transform.position = eye;
        cam.transform.LookAt(target, up);

        if (print)
            PrintPipeline(name, model, view, projection, viewport);
    }

    // ---------------------------------------------------------
    // The matrices, the same as in Lab10/main.py
    // ---------------------------------------------------------

    // Look-at: the camera's right, up and back axes become the rows, so the
    // camera ends up at the origin looking down -Z
    public static Matrix4x4 LookAt(Vector3 eye, Vector3 target, Vector3 up)
    {
        Vector3 forward = (target - eye).normalized;
        Vector3 right = Vector3.Cross(forward, up).normalized;
        Vector3 trueUp = Vector3.Cross(right, forward);

        var m = new Matrix4x4();
        m.SetRow(0, new Vector4(right.x, right.y, right.z, -Vector3.Dot(right, eye)));
        m.SetRow(1, new Vector4(trueUp.x, trueUp.y, trueUp.z, -Vector3.Dot(trueUp, eye)));
        m.SetRow(2, new Vector4(-forward.x, -forward.y, -forward.z, Vector3.Dot(forward, eye)));
        m.SetRow(3, new Vector4(0, 0, 0, 1));
        return m;
    }

    // Perspective: w = -z_eye, so distant points shrink after the division
    public static Matrix4x4 Perspective(float fov, float aspect, float near, float far)
    {
        float f = 1f / Mathf.Tan(fov * Mathf.Deg2Rad / 2f);

        var m = new Matrix4x4();
        m.SetRow(0, new Vector4(f / aspect, 0, 0, 0));
        m.SetRow(1, new Vector4(0, f, 0, 0));
        m.SetRow(2, new Vector4(0, 0, (far + near) / (near - far), 2 * far * near / (near - far)));
        m.SetRow(3, new Vector4(0, 0, -1, 0));
        return m;
    }

    // Orthographic: maps the box [l,r] x [b,t] x [-n,-f] to the NDC cube; w stays 1
    public static Matrix4x4 Orthographic(float left, float right, float bottom, float top, float near, float far)
    {
        var m = new Matrix4x4();
        m.SetRow(0, new Vector4(2 / (right - left), 0, 0, -(right + left) / (right - left)));
        m.SetRow(1, new Vector4(0, 2 / (top - bottom), 0, -(top + bottom) / (top - bottom)));
        m.SetRow(2, new Vector4(0, 0, -2 / (far - near), -(far + near) / (far - near)));
        m.SetRow(3, new Vector4(0, 0, 0, 1));
        return m;
    }

    // 4. Perspective division: clip -> NDC [-1, 1]
    static Vector3 PerspectiveDivide(Vector4 clip) => new Vector3(clip.x / clip.w, clip.y / clip.w, clip.z / clip.w);

    // 5. Viewport mapping: NDC -> window pixels, depth [-1, 1] -> [0, 1]
    static Vector3 ViewportMap(Vector3 ndc, Rect viewport) => new Vector3(
        viewport.x + (ndc.x + 1) * viewport.width / 2,
        viewport.y + (ndc.y + 1) * viewport.height / 2,
        (ndc.z + 1) / 2);

    // ---------------------------------------------------------
    // Print every stage of the pipeline on the CPU
    // ---------------------------------------------------------
    void PrintPipeline(string name, Matrix4x4 model, Matrix4x4 view, Matrix4x4 projection, Rect viewport)
    {
        var sb = new StringBuilder();
        sb.AppendLine($"--- {name} viewport ({viewport.x:0}, {viewport.y:0}, {viewport.width:0}, {viewport.height:0}) ---");

        Vector4 obj = PipelineCube.Corners[0];
        obj.w = 1;
        Vector4 world = model * obj;
        Vector4 eye = view * world;
        Vector4 clip = projection * eye;
        Vector3 ndc = PerspectiveDivide(clip);
        Vector3 window = ViewportMap(ndc, viewport);

        sb.AppendLine("Vertex 0 through the pipeline:");
        sb.AppendLine($"  1. Object                {Fmt(obj)}");
        sb.AppendLine($"  2. World  = Model * obj  {Fmt(world)}");
        sb.AppendLine($"  3. Eye    = View * world {Fmt(eye)}");
        sb.AppendLine($"  4. Clip   = Proj * eye   {Fmt(clip)}");
        sb.AppendLine($"  5. NDC    = clip / w     {Fmt(ndc)}");
        sb.AppendLine($"  6. Window = viewport     {Fmt(window)}");

        // The GPU's own depth convention: Unity converts the OpenGL-style projection
        // (GL.GetGPUProjectionMatrix); Metal, DirectX and Vulkan use reversed Z (near = 1, far = 0)
        Vector4 gpuClip = GL.GetGPUProjectionMatrix(projection, false) * eye;
        sb.AppendLine($"  GPU depth buffer value   {gpuClip.z / gpuClip.w,7:F2}   " +
                      $"({SystemInfo.graphicsDeviceType}, reversed Z: {SystemInfo.usesReversedZBuffer})");

        sb.AppendLine();
        sb.AppendLine(" #   NDC x   NDC y   NDC z   Win x   Win y   Depth");

        for (int i = 0; i < PipelineCube.Corners.Length; i++)
        {
            Vector4 p = PipelineCube.Corners[i];
            p.w = 1;
            Vector3 n = PerspectiveDivide(projection * (view * (model * p)));
            Vector3 w = ViewportMap(n, viewport);
            sb.AppendLine($" {i}  {n.x,7:F2} {n.y,7:F2} {n.z,7:F2} {w.x,7:F2} {w.y,7:F2} {w.z,7:F2}");
        }

        Debug.Log(sb.ToString());
    }

    static string Fmt(Vector4 v) => $"({v.x,7:F2}, {v.y,7:F2}, {v.z,7:F2}, {v.w,7:F2})";
    static string Fmt(Vector3 v) => $"({v.x,7:F2}, {v.y,7:F2}, {v.z,7:F2})";

    void OnGUI()
    {
        if (!Application.isPlaying) return;

        GUI.Label(new Rect(10, 10, 700, 40),
            $"Perspective (left) | Orthographic (right){(paused ? "  (paused)" : "")}\n" +
            "Left/Right: orbit camera   Space: pause   T: print pipeline   Esc: stop");
    }
}
