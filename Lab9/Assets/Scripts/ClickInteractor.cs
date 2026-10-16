using UnityEngine;
using UnityEngine.InputSystem;

// Attach to the camera: left-click casts a ray and notifies any Spinner it hits.
[RequireComponent(typeof(Camera))]
public class ClickInteractor : MonoBehaviour
{
    Camera cam;

    void Awake()
    {
        cam = GetComponent<Camera>();
    }

    void Update()
    {
        var mouse = Mouse.current;
        if (mouse == null || !mouse.leftButton.wasPressedThisFrame) return;

        Ray ray = cam.ScreenPointToRay(mouse.position.ReadValue());
        if (Physics.Raycast(ray, out RaycastHit hit, 100f))
        {
            var spinner = hit.collider.GetComponent<Spinner>();
            if (spinner != null)
                spinner.OnClicked();
        }
    }
}
