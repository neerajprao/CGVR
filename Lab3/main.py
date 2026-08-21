import math
import sys
import glfw
from OpenGL.GL import *

# Canvas dimensions
WIDTH = 900
HEIGHT = 650
MARGIN = 70


# ==========================================
# 2D Homogeneous Matrix Operations
# ==========================================


def identity_matrix():
    return [
        [1, 0, 0],
        [0, 1, 0],
        [0, 0, 1],
    ]


def translation_matrix(tx, ty):
    return [
        [1, 0, tx],
        [0, 1, ty],
        [0, 0, 1],
    ]


def rotation_matrix(angle_in_degrees):
    angle = math.radians(angle_in_degrees)
    cos_val = math.cos(angle)
    sin_val = math.sin(angle)

    return [
        [cos_val, -sin_val, 0],
        [sin_val, cos_val, 0],
        [0, 0, 1],
    ]


def scaling_matrix(sx, sy):
    return [
        [sx, 0, 0],
        [0, sy, 0],
        [0, 0, 1],
    ]


def reflection_matrix(axis):
    if axis == "x":
        return scaling_matrix(1, -1)
    if axis == "y":
        return scaling_matrix(-1, 1)
    if axis == "origin":
        return scaling_matrix(-1, -1)
    if axis == "y=x":
        return [
            [0, 1, 0],
            [1, 0, 0],
            [0, 0, 1],
        ]
    if axis == "y=-x":
        return [
            [0, -1, 0],
            [-1, 0, 0],
            [0, 0, 1],
        ]

    return identity_matrix()


def multiply_matrices(a, b):
    result = [[0, 0, 0], [0, 0, 0], [0, 0, 0]]
    for row in range(3):
        for col in range(3):
            total = 0
            for k in range(3):
                total += a[row][k] * b[k][col]
            result[row][col] = total
    return result


def about_point(matrix, px, py):
    shifted = multiply_matrices(translation_matrix(px, py), matrix)
    return multiply_matrices(shifted, translation_matrix(-px, -py))


def transform_points(matrix, points):
    transformed = []
    for x, y in points:
        new_x = matrix[0][0] * x + matrix[0][1] * y + matrix[0][2]
        new_y = matrix[1][0] * x + matrix[1][1] * y + matrix[1][2]
        w = matrix[2][0] * x + matrix[2][1] * y + matrix[2][2]

        if abs(w) < 1e-9:
            w = 1.0

        transformed.append((clean(new_x / w), clean(new_y / w)))

    return transformed


def clean(value):
    if abs(value) < 1e-9:
        return 0.0
    return round(value, 6)


def print_matrix(matrix):
    for row in matrix:
        print("  ".join(f"{clean(val):7.2f}" for val in row))


def get_graph_bounds(points):
    x_vals = [x for x, y in points]
    y_vals = [y for x, y in points]

    min_x = math.floor(min(x_vals))
    max_x = math.ceil(max(x_vals))
    min_y = math.floor(min(y_vals))
    max_y = math.ceil(max(y_vals))

    x_padding = max(1, (max_x - min_x) // 5)
    y_padding = max(1, (max_y - min_y) // 5)

    return min_x - x_padding, max_x + x_padding, min_y - y_padding, max_y + y_padding


def choose_grid_step(min_val, max_val):
    graph_range = max_val - min_val
    if graph_range <= 20:
        return 1
    if graph_range <= 50:
        return 5
    if graph_range <= 100:
        return 10
    return 20


# ==========================================
# Coordinate Mapping Functions
# ==========================================


def make_mapper(min_x, max_x, min_y, max_y):
    graph_w = WIDTH - 2 * MARGIN
    graph_h = HEIGHT - 2 * MARGIN
    x_range = max(1e-6, max_x - min_x)
    y_range = max(1e-6, max_y - min_y)

    scale = min(graph_w / x_range, graph_h / y_range)
    used_w = x_range * scale
    used_h = y_range * scale
    left = MARGIN + (graph_w - used_w) / 2
    top = MARGIN + (graph_h - used_h) / 2

    def screen_x(x):
        return left + (x - min_x) * scale

    def screen_y(y):
        return top + (max_y - y) * scale

    return screen_x, screen_y


# ==========================================
# OpenGL Rendering Helpers
# ==========================================


def draw_grid(min_x, max_x, min_y, max_y, screen_x, screen_y):
    x_step = choose_grid_step(min_x, max_x)
    y_step = choose_grid_step(min_y, max_y)

    # Grid lines (Light Gray)
    glColor3f(0.86, 0.86, 0.86)
    glLineWidth(1.0)

    glBegin(GL_LINES)
    for x in range(min_x, max_x + 1, x_step):
        sx = screen_x(x)
        glVertex2f(sx, screen_y(min_y))
        glVertex2f(sx, screen_y(max_y))

    for y in range(min_y, max_y + 1, y_step):
        sy = screen_y(y)
        glVertex2f(screen_x(min_x), sy)
        glVertex2f(screen_x(max_x), sy)
    glEnd()

    # Bounding border (Black)
    glColor3f(0.0, 0.0, 0.0)
    glBegin(GL_LINE_LOOP)
    glVertex2f(screen_x(min_x), screen_y(min_y))
    glVertex2f(screen_x(max_x), screen_y(min_y))
    glVertex2f(screen_x(max_x), screen_y(max_y))
    glVertex2f(screen_x(min_x), screen_y(max_y))
    glEnd()

    # X and Y Axes (Black, Thick)
    glLineWidth(2.0)
    glBegin(GL_LINES)
    if min_y <= 0 <= max_y:
        glVertex2f(screen_x(min_x), screen_y(0))
        glVertex2f(screen_x(max_x), screen_y(0))

    if min_x <= 0 <= max_x:
        glVertex2f(screen_x(0), screen_y(min_y))
        glVertex2f(screen_x(0), screen_y(max_y))
    glEnd()


def draw_shape(points, screen_x, screen_y, color, dashed):
    glColor3f(*color)
    glLineWidth(2.0)

    if dashed:
        glEnable(GL_LINE_STIPPLE)
        glLineStipple(1, 0x00FF)
    else:
        glDisable(GL_LINE_STIPPLE)

    mode = GL_LINE_LOOP if len(points) > 2 else GL_LINES
    glBegin(mode)
    for x, y in points:
        glVertex2f(screen_x(x), screen_y(y))
    glEnd()

    glDisable(GL_LINE_STIPPLE)


def plot_points(points, screen_x, screen_y, color):
    glColor3f(*color)
    glPointSize(8.0)

    glBegin(GL_POINTS)
    for x, y in points:
        glVertex2f(screen_x(x), screen_y(y))
    glEnd()


# ==========================================
# Terminal Input Handling
# ==========================================


def read_shape():
    count = int(input("Number of vertices: "))
    if count < 2:
        raise SystemExit("A shape needs at least 2 vertices")

    points = []
    for i in range(count):
        x = float(input(f"x{i + 1}: "))
        y = float(input(f"y{i + 1}: "))
        points.append((x, y))

    return points


def read_reflection():
    print("\nReflect about")
    print("1. X axis")
    print("2. Y axis")
    print("3. Origin")
    print("4. Line y = x")
    print("5. Line y = -x")
    choice = input("Choice: ").strip()

    axes = {"1": "x", "2": "y", "3": "origin", "4": "y=x", "5": "y=-x"}
    labels = {
        "x": "X axis",
        "y": "Y axis",
        "origin": "origin",
        "y=x": "line y = x",
        "y=-x": "line y = -x",
    }

    if choice not in axes:
        raise SystemExit("Invalid reflection choice")

    axis = axes[choice]
    return reflection_matrix(axis), f"Reflection about the {labels[axis]}"


def read_transformation():
    print("\nChoose a transformation")
    print("1. Translation")
    print("2. Rotation")
    print("3. Scaling")
    print("4. Reflection")
    choice = input("Choice: ").strip()

    if choice == "1":
        tx = float(input("tx: "))
        ty = float(input("ty: "))
        return translation_matrix(tx, ty), f"Translation by ({tx:g}, {ty:g})"

    if choice == "2":
        angle = float(input("Angle in degrees (anticlockwise): "))
        px = float(input("Pivot x: "))
        py = float(input("Pivot y: "))
        return about_point(
            rotation_matrix(angle), px, py
        ), f"Rotation of {angle:g}° about ({px:g}, {py:g})"

    if choice == "3":
        sx = float(input("sx: "))
        sy = float(input("sy: "))
        px = float(input("Fixed point x: "))
        py = float(input("Fixed point y: "))
        return about_point(
            scaling_matrix(sx, sy), px, py
        ), f"Scaling by ({sx:g}, {sy:g}) about ({px:g}, {py:g})"

    if choice == "4":
        return read_reflection()

    raise SystemExit("Invalid transformation choice")


# ==========================================
# Main Execution Pipeline
# ==========================================


def main():
    print("Enter the shape vertices")
    original = read_shape()

    matrix, name = read_transformation()
    transformed = transform_points(matrix, original)

    print(f"\n{name}")
    print("\nHomogeneous transformation matrix:")
    print_matrix(matrix)

    print("\nOriginal -> Transformed:")
    for (x, y), (new_x, new_y) in zip(original, transformed):
        print(f"({x:g}, {y:g}) -> ({new_x:g}, {new_y:g})")

    min_x, max_x, min_y, max_y = get_graph_bounds(original + transformed)
    screen_x, screen_y = make_mapper(min_x, max_x, min_y, max_y)

    # Initialize GLFW Window
    if not glfw.init():
        sys.exit("Failed to initialize GLFW")

    window = glfw.create_window(
        WIDTH,
        HEIGHT,
        "2D Transformations using Homogeneous Coordinates (OpenGL)",
        None,
        None,
    )
    if not window:
        glfw.terminate()
        sys.exit("Failed to create GLFW window")

    glfw.make_context_current(window)

    # Configure 2D Orthographic Projection (0 to WIDTH, HEIGHT to 0 for screen coordinates)
    glViewport(0, 0, WIDTH, HEIGHT)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    glOrtho(0, WIDTH, HEIGHT, 0, -1, 1)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

    # Clear color (White)
    glClearColor(1.0, 1.0, 1.0, 1.0)

    # Render Loop
    while not glfw.window_should_close(window):
        glClear(GL_COLOR_BUFFER_BIT)

        # Draw Elements
        draw_grid(min_x, max_x, min_y, max_y, screen_x, screen_y)
        draw_shape(original, screen_x, screen_y, (0.0, 0.0, 1.0), True)  # Blue Dashed
        draw_shape(
            transformed, screen_x, screen_y, (1.0, 0.0, 0.0), False
        )  # Red Solid
        plot_points(original, screen_x, screen_y, (0.0, 0.0, 1.0))
        plot_points(transformed, screen_x, screen_y, (1.0, 0.0, 0.0))

        glfw.swap_buffers(window)
        glfw.poll_events()

    glfw.terminate()


if __name__ == "__main__":
    main()