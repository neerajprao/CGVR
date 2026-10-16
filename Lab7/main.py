import sys
import math
import glfw
from OpenGL.GL import *


# ---------------------------------------------------------
# Panel resolution (each panel is a square image buffer)
# ---------------------------------------------------------
PANEL = 300

# Sphere radius in pixels (the sphere is a unit sphere in object space)
SPHERE_RADIUS_PX = 120

BACKGROUND = (0, 0, 0)

# Intensity of the ambient light and of the point light source
AMBIENT_LIGHT = 1.0
LIGHT_INTENSITY = 1.0

# Orthographic viewer looking down the -z axis
VIEW = (0.0, 0.0, 1.0)

PANEL_NAMES = ["Ambient", "Diffuse", "Specular", "Phong (sum)"]


# ---------------------------------------------------------
# Vector helpers
# ---------------------------------------------------------
def dot(a, b):

    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def normalize(v):

    length = math.sqrt(dot(v, v))

    return (v[0] / length, v[1] / length, v[2] / length)


# ---------------------------------------------------------
# Phong illumination model at one surface point
# Returns L, R, (N.L) and (R.V) clamped at 0
# ---------------------------------------------------------
def phong_vectors(point, normal, light_pos):

    # Unit vector from the surface point to the light
    L = normalize((
        light_pos[0] - point[0],
        light_pos[1] - point[1],
        light_pos[2] - point[2],
    ))

    n_dot_l = dot(normal, L)

    # Reflection of L about the normal: R = 2(N.L)N - L
    R = (
        2 * n_dot_l * normal[0] - L[0],
        2 * n_dot_l * normal[1] - L[1],
        2 * n_dot_l * normal[2] - L[2],
    )

    # Surface facing away from the light gets no diffuse or specular light
    if n_dot_l <= 0:
        return L, R, 0.0, 0.0

    return L, R, n_dot_l, max(0.0, dot(R, VIEW))


def phong_terms(params, n_dot_l, r_dot_v):

    ambient = params["ka"] * AMBIENT_LIGHT
    diffuse = params["kd"] * LIGHT_INTENSITY * n_dot_l
    specular = params["ks"] * LIGHT_INTENSITY * r_dot_v ** params["n"]

    return ambient, diffuse, specular


# ---------------------------------------------------------
# Shade the sphere: one image per term plus the total
# ---------------------------------------------------------
def render(params):

    images = [bytearray(bytes(BACKGROUND) * (PANEL * PANEL)) for _ in range(4)]

    color = params["color"]

    brightest = None

    for py in range(PANEL):

        for px in range(PANEL):

            # Pixel center in object space
            x = (px + 0.5 - PANEL / 2) / SPHERE_RADIUS_PX
            y = (py + 0.5 - PANEL / 2) / SPHERE_RADIUS_PX

            d = x * x + y * y

            if d > 1:
                continue

            # Visible point on the unit sphere; its normal is the point itself
            z = math.sqrt(1 - d)

            point = (x, y, z)
            normal = point

            _, _, n_dot_l, r_dot_v = phong_vectors(point, normal, params["light"])

            ambient, diffuse, specular = phong_terms(params, n_dot_l, r_dot_v)

            total = ambient + diffuse + specular

            if brightest is None or total > brightest[0]:
                brightest = (total, point)

            # Ambient and diffuse take the object color, specular takes the light color (white)
            pixel_colors = [
                [ambient * c for c in color],
                [diffuse * c for c in color],
                [specular] * 3,
                [(ambient + diffuse) * c + specular for c in color],
            ]

            index = 3 * (py * PANEL + px)

            for image, rgb in zip(images, pixel_colors):

                image[index:index + 3] = bytes(
                    int(255 * min(1.0, value) + 0.5) for value in rgb
                )

    return [bytes(image) for image in images], brightest[1]


# ---------------------------------------------------------
# Terminal output
# ---------------------------------------------------------
def format_vector(v):

    return "(" + ", ".join(f"{value:.3f}" for value in v) + ")"


def print_worked_example(params, point):

    normal = point

    L, R, n_dot_l, r_dot_v = phong_vectors(point, normal, params["light"])

    ambient, diffuse, specular = phong_terms(params, n_dot_l, r_dot_v)

    print("\n==========================================")
    print("WORKED EXAMPLE AT THE BRIGHTEST POINT")
    print("==========================================")

    print(f"Point P          = {format_vector(point)}")
    print(f"Normal N         = {format_vector(normal)}   (unit sphere: N = P)")
    print(f"Light vector L   = {format_vector(L)}")
    print(f"View vector V    = {format_vector(VIEW)}")
    print(f"Reflection R     = 2(N.L)N - L = {format_vector(R)}")

    print(f"\nN.L = {n_dot_l:.4f}")
    print(f"R.V = {r_dot_v:.4f}")

    print(f"\nAmbient  = ka * Ia           = {params['ka']:g} * {AMBIENT_LIGHT:g} = {ambient:.4f}")
    print(f"Diffuse  = kd * Il * (N.L)   = {params['kd']:g} * {LIGHT_INTENSITY:g} * {n_dot_l:.4f} = {diffuse:.4f}")
    print(f"Specular = ks * Il * (R.V)^n = {params['ks']:g} * {LIGHT_INTENSITY:g} * {r_dot_v:.4f}^{params['n']:g} = {specular:.4f}")

    color = params["color"]

    rgb = [min(1.0, (ambient + diffuse) * c + specular) for c in color]

    print(f"\nI = Ambient + Diffuse + Specular = {ambient + diffuse + specular:.4f}")
    print(f"Pixel color (object color applied to ambient and diffuse) = {format_vector(rgb)}")


def print_state(params):

    light = params["light"]

    print(f"Light at ({light[0]:g}, {light[1]:g}, {light[2]:g}), shininess n = {params['n']:g}")


# ---------------------------------------------------------
# Terminal input
# ---------------------------------------------------------
def read_float(prompt, default):

    value = input(f"{prompt} [{default:g}]: ").strip()

    return float(value) if value else default


def read_params():

    print("Enter the Phong model parameters (press Enter to keep the default)")

    ka = read_float("Ambient reflection coefficient ka (0-1)", 0.15)
    kd = read_float("Diffuse reflection coefficient kd (0-1)", 0.7)
    ks = read_float("Specular reflection coefficient ks (0-1)", 0.6)
    n = read_float("Shininess exponent n", 32)

    for name, value in (("ka", ka), ("kd", kd), ("ks", ks)):

        if not 0 <= value <= 1:
            raise SystemExit(f"{name} must be between 0 and 1")

    if n <= 0:
        raise SystemExit("Shininess must be positive")

    print("\nLight position (the sphere has radius 1 and is centered at the origin)")

    lx = read_float("Light x", -2)
    ly = read_float("Light y", 2)
    lz = read_float("Light z", 3)

    if lx * lx + ly * ly + lz * lz <= 1:
        raise SystemExit("The light must be outside the sphere")

    print("\nObject color (RGB, 0-1)")

    r = read_float("Red", 0.9)
    g = read_float("Green", 0.3)
    b = read_float("Blue", 0.2)

    return {
        "ka": ka,
        "kd": kd,
        "ks": ks,
        "n": n,
        "light": (lx, ly, lz),
        "color": (r, g, b),
    }


# ---------------------------------------------------------
# Drawing helpers
# ---------------------------------------------------------
def draw_border():

    glColor3f(0.4, 0.4, 0.4)
    glLineWidth(1.0)

    glBegin(GL_LINE_LOOP)
    glVertex2f(1, 1)
    glVertex2f(PANEL - 1, 1)
    glVertex2f(PANEL - 1, PANEL - 1)
    glVertex2f(1, PANEL - 1)
    glEnd()


# ---------------------------------------------------------
# Main
# ---------------------------------------------------------
def main():

    print("==========================================")
    print("PHONG ILLUMINATION MODEL")
    print("I = ka*Ia + kd*Il*(N.L) + ks*Il*(R.V)^n")
    print("==========================================\n")

    initial = read_params()

    params = dict(initial)

    images, brightest = render(params)

    print_worked_example(params, brightest)

    print("\nPanels (left to right): " + " | ".join(PANEL_NAMES))
    print("Arrow keys: move the light   +/-: change shininess   R: reset")

    # -----------------------------------------------------
    # Initialization
    # -----------------------------------------------------
    if not glfw.init():
        sys.exit("Failed to initialize GLFW")

    window = glfw.create_window(
        1200,
        300,
        "Phong Illumination: Ambient + Diffuse + Specular = Phong",
        None,
        None
    )

    if not window:
        glfw.terminate()
        sys.exit("Failed to create GLFW window")

    glfw.make_context_current(window)

    state = {"changed": False}

    def key_callback(win, key, scancode, action, mods):

        if action not in (glfw.PRESS, glfw.REPEAT):
            return

        lx, ly, lz = params["light"]

        if key == glfw.KEY_LEFT:
            params["light"] = (lx - 0.5, ly, lz)

        elif key == glfw.KEY_RIGHT:
            params["light"] = (lx + 0.5, ly, lz)

        elif key == glfw.KEY_UP:
            params["light"] = (lx, ly + 0.5, lz)

        elif key == glfw.KEY_DOWN:
            params["light"] = (lx, ly - 0.5, lz)

        elif key in (glfw.KEY_EQUAL, glfw.KEY_KP_ADD):
            params["n"] = min(512, params["n"] * 2)

        elif key in (glfw.KEY_MINUS, glfw.KEY_KP_SUBTRACT):
            params["n"] = max(1, params["n"] / 2)

        elif key == glfw.KEY_R:
            params.update(initial)

        else:
            return

        state["changed"] = True

    glfw.set_key_callback(window, key_callback)

    glClearColor(0.0, 0.0, 0.0, 1.0)

    # Same coordinate system for every panel
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()

    glOrtho(0, PANEL, 0, PANEL, -1, 1)

    glMatrixMode(GL_MODELVIEW)

    glPixelStorei(GL_UNPACK_ALIGNMENT, 1)

    while not glfw.window_should_close(window):

        # Re-shade the sphere after a key press
        if state["changed"]:

            images, brightest = render(params)

            print_state(params)

            state["changed"] = False

        glClear(GL_COLOR_BUFFER_BIT)

        # Framebuffer size is in pixels (differs from window size on Retina displays)
        fb_w, fb_h = glfw.get_framebuffer_size(window)
        quarter = fb_w // 4

        # Stretch each buffer to fill its panel
        glPixelZoom(quarter / PANEL, fb_h / PANEL)

        for i, image in enumerate(images):

            glViewport(i * quarter, 0, quarter, fb_h)

            glRasterPos2f(0, 0)
            glDrawPixels(PANEL, PANEL, GL_RGB, GL_UNSIGNED_BYTE, image)

            draw_border()

        glfw.swap_buffers(window)
        glfw.poll_events()

    glfw.terminate()


if __name__ == "__main__":
    main()
