using UnityEngine;
using UnityEngine.InputSystem;

// Moves the player with WASD / arrow keys and keeps it on the ground plane.
public class PlayerController : MonoBehaviour
{
    public float moveSpeed = 5f;
    public float turnSpeed = 720f;
    public float boundary = 14f; // Ground is a 30x30 plane (scale 3)

    void Update()
    {
        var kb = Keyboard.current;
        if (kb == null) return;

        Vector3 input = Vector3.zero;
        if (kb.wKey.isPressed || kb.upArrowKey.isPressed) input.z += 1;
        if (kb.sKey.isPressed || kb.downArrowKey.isPressed) input.z -= 1;
        if (kb.dKey.isPressed || kb.rightArrowKey.isPressed) input.x += 1;
        if (kb.aKey.isPressed || kb.leftArrowKey.isPressed) input.x -= 1;

        if (input.sqrMagnitude > 0f)
        {
            input.Normalize();
            Vector3 pos = transform.position + input * moveSpeed * Time.deltaTime;
            pos.x = Mathf.Clamp(pos.x, -boundary, boundary);
            pos.z = Mathf.Clamp(pos.z, -boundary, boundary);
            transform.position = pos;

            Quaternion target = Quaternion.LookRotation(input, Vector3.up);
            transform.rotation = Quaternion.RotateTowards(transform.rotation, target, turnSpeed * Time.deltaTime);
        }
    }
}
