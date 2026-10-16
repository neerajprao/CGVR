using System.Collections.Generic;
using UnityEngine;

// Builds the Lab 8 cube in code: 24 vertices (position, color, normal) and 36 indices.
// The Mesh is Unity's version of the VBO (vertex data), EBO (indices) and VAO (attribute layout).
[ExecuteAlways]
[RequireComponent(typeof(MeshFilter), typeof(MeshRenderer))]
public class CubeMesh : MonoBehaviour
{
    // Same faces as Lab8/main.py, in OpenGL's right-handed axes.
    // Each face has its own 4 vertices so it can have its own normal.
    static readonly Vector3[] FaceNormals =
    {
        new Vector3(0, 0, 1),   // front
        new Vector3(0, 0, -1),  // back
        new Vector3(1, 0, 0),   // right
        new Vector3(-1, 0, 0),  // left
        new Vector3(0, 1, 0),   // top
        new Vector3(0, -1, 0),  // bottom
    };

    static readonly Vector3[,] FaceCorners =
    {
        { new Vector3(-1, -1, 1), new Vector3(1, -1, 1), new Vector3(1, 1, 1), new Vector3(-1, 1, 1) },
        { new Vector3(1, -1, -1), new Vector3(-1, -1, -1), new Vector3(-1, 1, -1), new Vector3(1, 1, -1) },
        { new Vector3(1, -1, 1), new Vector3(1, -1, -1), new Vector3(1, 1, -1), new Vector3(1, 1, 1) },
        { new Vector3(-1, -1, -1), new Vector3(-1, -1, 1), new Vector3(-1, 1, 1), new Vector3(-1, 1, -1) },
        { new Vector3(-1, 1, 1), new Vector3(1, 1, 1), new Vector3(1, 1, -1), new Vector3(-1, 1, -1) },
        { new Vector3(-1, -1, -1), new Vector3(1, -1, -1), new Vector3(1, -1, 1), new Vector3(-1, -1, 1) },
    };

    Mesh mesh;

    void OnEnable()
    {
        mesh = Build();
        GetComponent<MeshFilter>().sharedMesh = mesh;
    }

    void OnDisable()
    {
        if (mesh == null) return;

        if (Application.isPlaying) Destroy(mesh);
        else DestroyImmediate(mesh);
    }

    // Unity is left-handed (+Z points into the screen), OpenGL is right-handed.
    // Flipping z converts between them, so the cube looks the same on screen as in Lab 8.
    static Vector3 ToUnity(Vector3 v) => new Vector3(v.x, v.y, -v.z);

    static Mesh Build()
    {
        var positions = new List<Vector3>();
        var colors = new List<Color>();
        var normals = new List<Vector3>();
        var indices = new List<int>();

        for (int face = 0; face < FaceNormals.Length; face++)
        {
            for (int corner = 0; corner < 4; corner++)
            {
                Vector3 p = FaceCorners[face, corner];

                positions.Add(ToUnity(p));
                normals.Add(ToUnity(FaceNormals[face]));

                // Color comes from the corner position: RGB cube
                colors.Add(new Color((p.x + 1) / 2, (p.y + 1) / 2, (p.z + 1) / 2));
            }

            // Two triangles per face. OpenGL's front faces are counter-clockwise on
            // screen, Unity's are clockwise, so each triangle's order is reversed
            int b = face * 4;
            indices.AddRange(new[] { b, b + 2, b + 1, b, b + 3, b + 2 });
        }

        var mesh = new Mesh { name = "Lab8 Cube", hideFlags = HideFlags.DontSave };
        mesh.SetVertices(positions);
        mesh.SetColors(colors);
        mesh.SetNormals(normals);
        mesh.SetTriangles(indices, 0);

        return mesh;
    }
}
