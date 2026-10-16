using UnityEngine;

// Smoothly follows the target from a fixed offset and keeps it in view.
public class CameraFollow : MonoBehaviour
{
    public Transform target;
    public Vector3 offset = new Vector3(0f, 6f, -10f);
    public float smoothTime = 0.2f;

    Vector3 velocity;

    void LateUpdate()
    {
        if (target == null) return;

        Vector3 desired = target.position + offset;
        transform.position = Vector3.SmoothDamp(transform.position, desired, ref velocity, smoothTime);
        transform.LookAt(target.position + Vector3.up * 0.5f);
    }
}
