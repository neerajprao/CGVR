using UnityEngine;

// Builds the Lab 10 cube in code: 8 corners, each with its own color, and 36 indices.
// Faces share corners, so the colors blend across each face (there are no normals: no lighting).
[ExecuteAlways]
[RequireComponent(typeof(MeshFilter), typeof(MeshRenderer))]
public class PipelineCube : MonoBehaviour
{
    // Same data as build_cube() in Lab10/main.py
    public static readonly Vector3[] Corners =
    {
        new Vector3(-1, -1, 1), new Vector3(1, -1, 1), new Vector3(1, 1, 1), new Vector3(-1, 1, 1),
        new Vector3(-1, -1, -1), new Vector3(1, -1, -1), new Vector3(1, 1, -1), new Vector3(-1, 1, -1),
    };

    static readonly Color[] CornerColors =
    {
        new Color(1, 0, 0), new Color(0, 1, 0), new Color(0, 0, 1), new Color(1, 1, 0),
        new Color(1, 0, 1), new Color(0, 1, 1), new Color(1, 1, 1), new Color(1, 0.5f, 0),
    };

    static readonly int[] Indices =
    {
        0, 1, 2, 0, 2, 3,
        5, 4, 7, 5, 7, 6,
        4, 0, 3, 4, 3, 7,
        1, 5, 6, 1, 6, 2,
        3, 2, 6, 3, 6, 7,
        4, 5, 1, 4, 1, 0,
    };

    Mesh mesh;

    void OnEnable()
    {
        mesh = new Mesh { name = "Lab10 Cube", hideFlags = HideFlags.DontSave };
        mesh.SetVertices(Corners);
        mesh.SetColors(CornerColors);
        mesh.SetTriangles(Indices, 0);

        GetComponent<MeshFilter>().sharedMesh = mesh;
    }

    void OnDisable()
    {
        if (mesh == null) return;

        if (Application.isPlaying) Destroy(mesh);
        else DestroyImmediate(mesh);
    }
}
