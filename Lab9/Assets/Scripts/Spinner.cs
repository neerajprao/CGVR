using UnityEngine;

// Continuously rotates an object; can be toggled and recoloured by clicking.
public class Spinner : MonoBehaviour
{
    public Vector3 axis = Vector3.up;
    public float speed = 90f; // degrees per second
    public bool spinning = true;

    Renderer rend;

    void Awake()
    {
        rend = GetComponent<Renderer>();
    }

    void Update()
    {
        if (spinning)
            transform.Rotate(axis, speed * Time.deltaTime, Space.World);
    }

    public void OnClicked()
    {
        spinning = !spinning;
        if (rend != null)
            rend.material.color = Random.ColorHSV(0f, 1f, 0.6f, 1f, 0.7f, 1f);
        Debug.Log($"{name} clicked: spinning = {spinning}");
    }
}
