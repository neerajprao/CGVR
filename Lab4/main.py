import math
import sys
import glfw
from OpenGL.GL import *


# ==========================================
# Canvas Dimensions
# ==========================================

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


# ==========================================
# Matrix Multiplication
# ==========================================

def multiply_matrices(a, b):

    result = [
        [0, 0, 0],
        [0, 0, 0],
        [0, 0, 0],
    ]

    for row in range(3):

        for col in range(3):

            total = 0

            for k in range(3):
                total += a[row][k] * b[k][col]

            result[row][col] = total

    return result


# ==========================================
# Transformation About a Fixed Point
# ==========================================

def about_point(matrix, px, py):

    shifted = multiply_matrices(
        translation_matrix(px, py),
        matrix
    )

    return multiply_matrices(
        shifted,
        translation_matrix(-px, -py)
    )


# ==========================================
# Apply Matrix to Shape Points
# ==========================================

def transform_points(matrix, points):

    transformed = []

    for x, y in points:

        new_x = (
            matrix[0][0] * x
            + matrix[0][1] * y
            + matrix[0][2]
        )

        new_y = (
            matrix[1][0] * x
            + matrix[1][1] * y
            + matrix[1][2]
        )

        w = (
            matrix[2][0] * x
            + matrix[2][1] * y
            + matrix[2][2]
        )

        if abs(w) < 1e-9:
            w = 1.0

        transformed.append(
            (
                clean(new_x / w),
                clean(new_y / w),
            )
        )

    return transformed


# ==========================================
# Utility Functions
# ==========================================

def clean(value):

    if abs(value) < 1e-9:
        return 0.0

    return round(value, 6)


def print_matrix(matrix):

    for row in matrix:

        print(
            "  ".join(
                f"{clean(val):8.3f}"
                for val in row
            )
        )


# ==========================================
# Graph Boundary Calculation
# ==========================================

def get_graph_bounds(all_points):

    x_vals = [x for x, y in all_points]
    y_vals = [y for x, y in all_points]

    min_x = math.floor(min(x_vals))
    max_x = math.ceil(max(x_vals))

    min_y = math.floor(min(y_vals))
    max_y = math.ceil(max(y_vals))

    x_padding = max(1, (max_x - min_x) // 5)
    y_padding = max(1, (max_y - min_y) // 5)

    return (
        min_x - x_padding,
        max_x + x_padding,
        min_y - y_padding,
        max_y + y_padding,
    )


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

    scale = min(
        graph_w / x_range,
        graph_h / y_range
    )

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

    # Draw grid lines
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

    # Draw bounding border
    glColor3f(0.0, 0.0, 0.0)

    glBegin(GL_LINE_LOOP)

    glVertex2f(screen_x(min_x), screen_y(min_y))
    glVertex2f(screen_x(max_x), screen_y(min_y))
    glVertex2f(screen_x(max_x), screen_y(max_y))
    glVertex2f(screen_x(min_x), screen_y(max_y))

    glEnd()

    # Draw X and Y axes
    glLineWidth(2.0)

    glBegin(GL_LINES)

    if min_y <= 0 <= max_y:

        glVertex2f(screen_x(min_x), screen_y(0))
        glVertex2f(screen_x(max_x), screen_y(0))

    if min_x <= 0 <= max_x:

        glVertex2f(screen_x(0), screen_y(min_y))
        glVertex2f(screen_x(0), screen_y(max_y))

    glEnd()


def draw_shape(points, screen_x, screen_y, color, dashed=False):

    glColor3f(*color)
    glLineWidth(2.5)

    if dashed:
        glEnable(GL_LINE_STIPPLE)
        glLineStipple(1, 0x00FF)

    else:
        glDisable(GL_LINE_STIPPLE)

    mode = GL_LINE_LOOP if len(points) > 2 else GL_LINES

    glBegin(mode)

    for x, y in points:

        glVertex2f(
            screen_x(x),
            screen_y(y)
        )

    glEnd()

    glDisable(GL_LINE_STIPPLE)


def plot_points(points, screen_x, screen_y, color):

    glColor3f(*color)
    glPointSize(8.0)

    glBegin(GL_POINTS)

    for x, y in points:

        glVertex2f(
            screen_x(x),
            screen_y(y)
        )

    glEnd()


# ==========================================
# Terminal Input Functions
# ==========================================

def read_shape():

    count = int(input("Number of vertices: "))

    if count < 2:
        raise SystemExit(
            "A shape needs at least 2 vertices"
        )

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

    axes = {
        "1": "x",
        "2": "y",
        "3": "origin",
        "4": "y=x",
        "5": "y=-x",
    }

    labels = {
        "x": "X axis",
        "y": "Y axis",
        "origin": "origin",
        "y=x": "line y = x",
        "y=-x": "line y = -x",
    }

    if choice not in axes:
        raise SystemExit(
            "Invalid reflection choice"
        )

    axis = axes[choice]

    return (
        reflection_matrix(axis),
        f"Reflection about the {labels[axis]}"
    )


# ==========================================
# Read One Transformation
# ==========================================

def read_transformation():

    print("\nChoose a transformation")
    print("1. Translation")
    print("2. Rotation")
    print("3. Scaling")
    print("4. Reflection")

    choice = input("Choice: ").strip()

    # Translation
    if choice == "1":

        tx = float(input("tx: "))
        ty = float(input("ty: "))

        return (
            translation_matrix(tx, ty),
            f"Translation by ({tx:g}, {ty:g})"
        )

    # Rotation
    if choice == "2":

        angle = float(
            input("Angle in degrees (anticlockwise): ")
        )

        px = float(input("Pivot x: "))
        py = float(input("Pivot y: "))

        return (
            about_point(
                rotation_matrix(angle),
                px,
                py
            ),
            f"Rotation of {angle:g}° about ({px:g}, {py:g})"
        )

    # Scaling
    if choice == "3":

        sx = float(input("sx: "))
        sy = float(input("sy: "))

        px = float(input("Fixed point x: "))
        py = float(input("Fixed point y: "))

        return (
            about_point(
                scaling_matrix(sx, sy),
                px,
                py
            ),
            f"Scaling by ({sx:g}, {sy:g}) about ({px:g}, {py:g})"
        )

    # Reflection
    if choice == "4":
        return read_reflection()

    raise SystemExit(
        "Invalid transformation choice"
    )


# ==========================================
# Read Multiple Transformations
# ==========================================

def read_composite_transformation():

    count = int(
        input(
            "\nNumber of transformations to apply: "
        )
    )

    if count < 1:
        raise SystemExit(
            "At least one transformation is required"
        )

    # Final composite matrix
    composite_matrix = identity_matrix()

    # Store each individual transformation matrix
    transformation_matrices = []

    # Store transformation names
    transformation_names = []

    for i in range(count):

        print(f"\n--- Transformation {i + 1} ---")

        matrix, name = read_transformation()

        transformation_matrices.append(matrix)
        transformation_names.append(name)

        # Build composite matrix
        composite_matrix = multiply_matrices(
            matrix,
            composite_matrix
        )

    return (
        composite_matrix,
        transformation_matrices,
        transformation_names
    )


# ==========================================
# Main Program
# ==========================================

def main():

    print("==========================================")
    print("COMPOSITE TRANSFORMATIONS")
    print("USING MATRIX REPRESENTATION")
    print("==========================================")

    # Read original shape
    print("\nEnter the shape vertices")

    original = read_shape()

    # Read transformations
    (
        composite_matrix,
        transformation_matrices,
        transformation_names
    ) = read_composite_transformation()

    # ==========================================
    # Store Every Intermediate Transformation
    # ==========================================

    # Stage 0 = Original shape
    transformation_stages = [original]

    current_points = original

    # Apply transformations one by one
    for matrix in transformation_matrices:

        current_points = transform_points(
            matrix,
            current_points
        )

        transformation_stages.append(current_points)

    # Final transformed shape
    transformed = transformation_stages[-1]

    # ==========================================
    # Display Transformation Sequence
    # ==========================================

    print("\n==========================================")
    print("TRANSFORMATION SEQUENCE")
    print("==========================================")

    for i, name in enumerate(
        transformation_names,
        start=1
    ):
        print(f"{i}. {name}")

    # ==========================================
    # Display Intermediate Coordinates
    # ==========================================

    print("\n==========================================")
    print("INTERMEDIATE TRANSFORMATION RESULTS")
    print("==========================================")

    print("\nStage 0: Original Shape")

    for i, (x, y) in enumerate(original, start=1):
        print(f"P{i}: ({x:g}, {y:g})")

    for stage_number in range(
        1,
        len(transformation_stages)
    ):

        print(
            f"\nStage {stage_number}: "
            f"After {transformation_names[stage_number - 1]}"
        )

        for i, (x, y) in enumerate(
            transformation_stages[stage_number],
            start=1
        ):
            print(f"P{i}: ({x:g}, {y:g})")

    # ==========================================
    # Display Final Composite Matrix
    # ==========================================

    print("\n==========================================")
    print("FINAL COMPOSITE TRANSFORMATION MATRIX")
    print("==========================================")

    print_matrix(composite_matrix)

    # ==========================================
    # Calculate Graph Bounds
    # Include Every Intermediate Shape
    # ==========================================

    all_points = []

    for stage in transformation_stages:
        all_points.extend(stage)

    min_x, max_x, min_y, max_y = (
        get_graph_bounds(all_points)
    )

    # Create coordinate mapper
    screen_x, screen_y = make_mapper(
        min_x,
        max_x,
        min_y,
        max_y
    )

    # ==========================================
    # Initialize GLFW
    # ==========================================

    if not glfw.init():

        sys.exit(
            "Failed to initialize GLFW"
        )

    window = glfw.create_window(
        WIDTH,
        HEIGHT,
        "Composite Transformations Using Matrix Representation",
        None,
        None,
    )

    if not window:

        glfw.terminate()

        sys.exit(
            "Failed to create GLFW window"
        )

    glfw.make_context_current(window)

    # ==========================================
    # Configure OpenGL Projection
    # ==========================================

    glViewport(0, 0, WIDTH, HEIGHT)

    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()

    glOrtho(
        0,
        WIDTH,
        HEIGHT,
        0,
        -1,
        1
    )

    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

    # White background
    glClearColor(
        1.0,
        1.0,
        1.0,
        1.0
    )

    # ==========================================
    # Colors for Each Transformation Stage
    # ==========================================

    stage_colors = [
        (0.0, 0.0, 1.0),   # Blue - Original
        (0.0, 0.6, 0.0),   # Green - Stage 1
        (1.0, 0.5, 0.0),   # Orange - Stage 2
        (0.6, 0.0, 0.8),   # Purple - Stage 3
        (0.0, 0.7, 0.7),   # Cyan - Stage 4
        (0.8, 0.2, 0.5),   # Pink - Stage 5
        (0.5, 0.5, 0.0),   # Olive - Stage 6
        (1.0, 0.0, 0.0),   # Red - Additional stages
    ]

    # ==========================================
    # OpenGL Render Loop
    # ==========================================

    while not glfw.window_should_close(window):

        glClear(GL_COLOR_BUFFER_BIT)

        # Draw coordinate grid
        draw_grid(
            min_x,
            max_x,
            min_y,
            max_y,
            screen_x,
            screen_y
        )

        # ==========================================
        # Draw Every Transformation Stage
        # ==========================================

        for stage_number, stage_points in enumerate(
            transformation_stages
        ):

            color = stage_colors[
                stage_number % len(stage_colors)
            ]

            # Original shape is dashed
            dashed = (stage_number == 0)

            draw_shape(
                stage_points,
                screen_x,
                screen_y,
                color,
                dashed
            )

            plot_points(
                stage_points,
                screen_x,
                screen_y,
                color
            )

        glfw.swap_buffers(window)
        glfw.poll_events()

    glfw.terminate()


if __name__ == "__main__":
    main()