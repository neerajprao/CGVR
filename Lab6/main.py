import sys
import math
import glfw
from OpenGL.GL import *


# ---------------------------------------------------------
# Frame buffer / depth buffer resolution (one panel)
# ---------------------------------------------------------
BUF_W = 600
BUF_H = 450

# Initial depth of every pixel: farther than any surface
FAR = float("inf")

BACKGROUND = (0, 0, 0)


# Polygon colors, assigned in input order
PALETTE = [
    ("Yellow", (255, 215, 0)),
    ("Red", (230, 40, 40)),
    ("Green", (40, 200, 70)),
    ("Blue", (50, 110, 240)),
    ("Magenta", (210, 60, 210)),
    ("Cyan", (40, 210, 210)),
    ("Orange", (255, 140, 0)),
    ("White", (235, 235, 235)),
]


# ---------------------------------------------------------
# Default scene: vertices are (x, y, z)
# z = distance from the viewer (smaller z = closer)
# ---------------------------------------------------------
DEFAULT_SCENE = [
    # Yellow triangle, nearest to the viewer
    [(380, 200, 10), (560, 330, 10), (420, 420, 10)],
    # Red band, tilted in depth (z = 20 on the left, 80 on the right)
    [(100, 150, 20), (500, 150, 80), (500, 250, 80), (100, 250, 20)],
    # Green band at z = 50, passes through the red band at x = 300
    [(250, 30, 50), (350, 30, 50), (350, 420, 50), (250, 420, 50)],
    # Blue wall, farthest from the viewer
    [(40, 40, 90), (330, 40, 90), (330, 300, 90), (40, 300, 90)],
]


# ---------------------------------------------------------
# Plane equation Ax + By + Cz + D = 0 (Newell's method)
# ---------------------------------------------------------
def plane_equation(vertices):

    a = b = c = 0.0

    n = len(vertices)

    for i in range(n):

        x1, y1, z1 = vertices[i]
        x2, y2, z2 = vertices[(i + 1) % n]

        a += (y1 - y2) * (z1 + z2)
        b += (z1 - z2) * (x1 + x2)
        c += (x1 - x2) * (y1 + y2)

    length = math.sqrt(a * a + b * b + c * c)

    if length < 1e-9:
        return None

    # Unit normal, oriented so that C >= 0
    sign = -1 if c < 0 else 1

    a = sign * a / length
    b = sign * b / length
    c = sign * c / length

    x0, y0, z0 = vertices[0]
    d = -(a * x0 + b * y0 + c * z0)

    return a, b, c, d


# ---------------------------------------------------------
# Scan-line polygon fill: yields (y, x_start, x_end)
# for every horizontal run of pixels inside the polygon
# ---------------------------------------------------------
def polygon_spans(vertices):

    ys = [y for x, y, z in vertices]

    y_first = max(0, math.ceil(min(ys) - 0.5))
    y_last = min(BUF_H - 1, math.ceil(max(ys) - 0.5) - 1)

    n = len(vertices)

    for y in range(y_first, y_last + 1):

        # Sample at the pixel center
        yc = y + 0.5

        # Intersections of the scan line with the polygon edges
        xs = []

        for i in range(n):

            x1, y1, _ = vertices[i]
            x2, y2, _ = vertices[(i + 1) % n]

            if (y1 <= yc < y2) or (y2 <= yc < y1):
                xs.append(x1 + (yc - y1) * (x2 - x1) / (y2 - y1))

        xs.sort()

        # Fill between pairs of intersections
        for k in range(0, len(xs) - 1, 2):

            x_start = max(0, math.ceil(xs[k] - 0.5))
            x_end = min(BUF_W, math.ceil(xs[k + 1] - 0.5))

            if x_start < x_end:
                yield y, x_start, x_end


# ---------------------------------------------------------
# Z-buffer algorithm
# ---------------------------------------------------------
def render(polygons, use_z_buffer):

    # Step 1: initialize the frame buffer to the background
    # color and the depth buffer to the farthest depth
    frame = bytearray(bytes(BACKGROUND) * (BUF_W * BUF_H))
    depth = [FAR] * (BUF_W * BUF_H)
    owner = [-1] * (BUF_W * BUF_H)

    stats = []

    # Step 2: scan convert each polygon
    for pid, (vertices, plane, color) in enumerate(polygons):

        # Polygon seen edge-on: it covers no pixels
        if plane is None or abs(plane[2]) < 1e-9:
            stats.append(None)
            continue

        a, b, c, d = plane

        # Depth change for one pixel step along a scan line
        dz = -a / c

        passed = 0
        failed = 0

        for y, x_start, x_end in polygon_spans(vertices):

            # Depth at the first pixel of the run: z = -(Ax + By + D) / C
            z = -(a * (x_start + 0.5) + b * (y + 0.5) + d) / c

            index = y * BUF_W + x_start

            for x in range(x_start, x_end):

                # Step 3: depth test, keep the surface closest to the viewer
                if not use_z_buffer or z < depth[index]:

                    depth[index] = z
                    owner[index] = pid
                    frame[3 * index:3 * index + 3] = color
                    passed += 1

                else:
                    failed += 1

                # Incremental depth calculation
                z += dz
                index += 1

        stats.append((passed, failed))

    return bytes(frame), depth, owner, stats


# ---------------------------------------------------------
# Depth buffer as a grayscale image (near = white, far = dark)
# ---------------------------------------------------------
def depth_image(depth, z_near, z_far):

    image = bytearray(bytes(BACKGROUND) * len(depth))

    z_range = max(1e-9, z_far - z_near)

    for i, z in enumerate(depth):

        if z != FAR:

            shade = int(255 - 205 * (z - z_near) / z_range)
            shade = max(50, min(255, shade))

            image[3 * i:3 * i + 3] = bytes((shade, shade, shade))

    return bytes(image)


# ---------------------------------------------------------
# Terminal input
# ---------------------------------------------------------
def read_scene():

    choice = input("Use the default scene? (y/n) [y]: ").strip().lower()

    if choice in ("", "y", "yes"):
        return DEFAULT_SCENE

    print(f"\nx: 0-{BUF_W}, y: 0-{BUF_H}, z: depth (smaller = closer)")

    count = int(input("Number of polygons: "))

    if count < 1:
        raise SystemExit("At least one polygon is required")

    scene = []

    for p in range(count):

        name = PALETTE[p % len(PALETTE)][0]

        print(f"\n--- Polygon {p + 1} ({name}) ---")

        n = int(input("Number of vertices: "))

        if n < 3:
            raise SystemExit("A polygon needs at least 3 vertices")

        vertices = []

        for i in range(n):

            x = float(input(f"x{i + 1}: "))
            y = float(input(f"y{i + 1}: "))
            z = float(input(f"z{i + 1}: "))

            vertices.append((x, y, z))

        scene.append(vertices)

    return scene


# ---------------------------------------------------------
# Drawing helpers
# ---------------------------------------------------------
def draw_border():

    glColor3f(0.4, 0.4, 0.4)
    glLineWidth(1.0)

    glBegin(GL_LINE_LOOP)
    glVertex2f(1, 1)
    glVertex2f(BUF_W - 1, 1)
    glVertex2f(BUF_W - 1, BUF_H - 1)
    glVertex2f(1, BUF_H - 1)
    glEnd()


def window_title(show_depth):

    right = "Depth Buffer" if show_depth else "With Z-Buffer"

    return f"Without Z-Buffer (left) vs {right} (right)"


# ---------------------------------------------------------
# Main
# ---------------------------------------------------------
def main():

    print("==========================================")
    print("Z-BUFFER HIDDEN SURFACE REMOVAL")
    print("==========================================\n")

    scene = read_scene()

    polygons = []

    for p, vertices in enumerate(scene):

        color = bytes(PALETTE[p % len(PALETTE)][1])

        polygons.append((vertices, plane_equation(vertices), color))

    # Render twice: in input order only, and with the depth test
    no_z_frame, _, _, _ = render(polygons, use_z_buffer=False)
    z_frame, depth, owner, stats = render(polygons, use_z_buffer=True)

    z_values = [z for vertices in scene for x, y, z in vertices]
    z_buffer_view = depth_image(depth, min(z_values), max(z_values))

    # -----------------------------------------------------
    # Display results
    # -----------------------------------------------------
    print("\n==========================================")
    print("POLYGONS (in drawing order)")
    print("==========================================")

    for p, (vertices, plane, color) in enumerate(polygons):

        name = PALETTE[p % len(PALETTE)][0]

        print(f"\nPolygon {p + 1} ({name}):")
        print("  Vertices: " + ", ".join(f"({x:g}, {y:g}, {z:g})" for x, y, z in vertices))

        if stats[p] is None:
            print("  Seen edge-on by the viewer: covers no pixels, skipped")
            continue

        a, b, c, d = plane
        passed, failed = stats[p]

        print(f"  Plane: {a:.3f}x + {b:.3f}y + {c:.3f}z + ({d:.3f}) = 0")
        print(f"  Pixels covered: {passed + failed}")
        print(f"  Depth test passed: {passed}, failed: {failed}")

    print("\n==========================================")
    print("VISIBLE PIXELS IN THE FINAL IMAGE")
    print("==========================================")

    for p in range(len(polygons)):

        name = PALETTE[p % len(PALETTE)][0]

        print(f"Polygon {p + 1} ({name}): {owner.count(p)}")

    print(f"Background: {owner.count(-1)}")

    print("\nLeft panel : without Z-buffer (drawn in input order)")
    print("Right panel: with Z-buffer")
    print("Press D to switch the right panel between the frame buffer and the depth buffer")

    # -----------------------------------------------------
    # Initialization
    # -----------------------------------------------------
    if not glfw.init():
        sys.exit("Failed to initialize GLFW")

    window = glfw.create_window(
        1200,
        450,
        window_title(False),
        None,
        None
    )

    if not window:
        glfw.terminate()
        sys.exit("Failed to create GLFW window")

    glfw.make_context_current(window)

    state = {"show_depth": False}

    def key_callback(win, key, scancode, action, mods):

        if key == glfw.KEY_D and action == glfw.PRESS:

            state["show_depth"] = not state["show_depth"]

            glfw.set_window_title(win, window_title(state["show_depth"]))

    glfw.set_key_callback(window, key_callback)

    glClearColor(0.0, 0.0, 0.0, 1.0)

    # Same coordinate system for both panels
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()

    glOrtho(0, BUF_W, 0, BUF_H, -1, 1)

    glMatrixMode(GL_MODELVIEW)

    glPixelStorei(GL_UNPACK_ALIGNMENT, 1)

    while not glfw.window_should_close(window):

        glClear(GL_COLOR_BUFFER_BIT)

        # Framebuffer size is in pixels (differs from window size on Retina displays)
        fb_w, fb_h = glfw.get_framebuffer_size(window)
        half = fb_w // 2

        # Stretch each buffer to fill its panel
        glPixelZoom(half / BUF_W, fb_h / BUF_H)

        right_image = z_buffer_view if state["show_depth"] else z_frame

        for i, image in enumerate([no_z_frame, right_image]):

            glViewport(i * half, 0, half, fb_h)

            glRasterPos2f(0, 0)
            glDrawPixels(BUF_W, BUF_H, GL_RGB, GL_UNSIGNED_BYTE, image)

            draw_border()

        glfw.swap_buffers(window)
        glfw.poll_events()

    glfw.terminate()


if __name__ == "__main__":
    main()
