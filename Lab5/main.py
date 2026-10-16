import sys
import glfw
from OpenGL.GL import *


# ---------------------------------------------------------
# Window size
# ---------------------------------------------------------
WIDTH = 800
HEIGHT = 600


# ---------------------------------------------------------
# Clipping window
# ---------------------------------------------------------
XMIN = -4
XMAX = 4
YMIN = -3
YMAX = 3


# Region codes
INSIDE = 0
LEFT = 1
RIGHT = 2
BOTTOM = 4
TOP = 8


# ---------------------------------------------------------
# Find region code
# ---------------------------------------------------------
def compute_code(x, y):

    code = INSIDE

    if x < XMIN:
        code |= LEFT

    elif x > XMAX:
        code |= RIGHT

    if y < YMIN:
        code |= BOTTOM

    elif y > YMAX:
        code |= TOP

    return code


# ---------------------------------------------------------
# Cohen-Sutherland algorithm
# ---------------------------------------------------------
def cohen_sutherland(x1, y1, x2, y2):

    code1 = compute_code(x1, y1)
    code2 = compute_code(x2, y2)

    accept = False

    while True:

        # Both points inside
        if code1 == 0 and code2 == 0:
            accept = True
            break

        # Line completely outside
        elif (code1 & code2) != 0:
            break

        # At least one point outside
        else:

            if code1 != 0:
                code_out = code1
            else:
                code_out = code2

            # Find intersection with TOP
            if code_out & TOP:

                x = x1 + (x2 - x1) * (YMAX - y1) / (y2 - y1)
                y = YMAX

            # Find intersection with BOTTOM
            elif code_out & BOTTOM:

                x = x1 + (x2 - x1) * (YMIN - y1) / (y2 - y1)
                y = YMIN

            # Find intersection with RIGHT
            elif code_out & RIGHT:

                y = y1 + (y2 - y1) * (XMAX - x1) / (x2 - x1)
                x = XMAX

            # Find intersection with LEFT
            elif code_out & LEFT:

                y = y1 + (y2 - y1) * (XMIN - x1) / (x2 - x1)
                x = XMIN

            # Replace outside point
            if code_out == code1:

                x1 = x
                y1 = y
                code1 = compute_code(x1, y1)

            else:

                x2 = x
                y2 = y
                code2 = compute_code(x2, y2)

    if accept:
        return x1, y1, x2, y2

    return None


# ---------------------------------------------------------
# View bounds: fit the clipping window and the line,
# keeping the window's aspect ratio so nothing is stretched
# ---------------------------------------------------------
def get_view_bounds(x1, y1, x2, y2):

    min_x = min(XMIN, x1, x2)
    max_x = max(XMAX, x1, x2)
    min_y = min(YMIN, y1, y2)
    max_y = max(YMAX, y1, y2)

    padding = 0.1 * max(max_x - min_x, max_y - min_y)

    width = max_x - min_x + 2 * padding
    height = max_y - min_y + 2 * padding

    aspect = WIDTH / HEIGHT

    if width / height < aspect:
        width = height * aspect
    else:
        height = width / aspect

    center_x = (min_x + max_x) / 2
    center_y = (min_y + max_y) / 2

    return (
        center_x - width / 2,
        center_x + width / 2,
        center_y - height / 2,
        center_y + height / 2,
    )


# ---------------------------------------------------------
# Draw clipping rectangle
# ---------------------------------------------------------
def draw_rectangle():

    glBegin(GL_LINE_LOOP)

    glVertex2f(XMIN, YMIN)
    glVertex2f(XMAX, YMIN)
    glVertex2f(XMAX, YMAX)
    glVertex2f(XMIN, YMAX)

    glEnd()


# ---------------------------------------------------------
# Display
# ---------------------------------------------------------
def display(x1, y1, x2, y2, clipped):

    glClear(GL_COLOR_BUFFER_BIT)

    # Draw clipping window
    glColor3f(1.0, 1.0, 1.0)

    draw_rectangle()

    # -----------------------------------------------------
    # Draw original line
    # -----------------------------------------------------
    glColor3f(1.0, 0.0, 0.0)

    glBegin(GL_LINES)

    glVertex2f(x1, y1)
    glVertex2f(x2, y2)

    glEnd()

    # Draw clipped line
    if clipped is not None:

        cx1, cy1, cx2, cy2 = clipped

        glColor3f(0.0, 1.0, 0.0)

        glLineWidth(5.0)

        glBegin(GL_LINES)

        glVertex2f(cx1, cy1)
        glVertex2f(cx2, cy2)

        glEnd()

        glLineWidth(1.0)


# ---------------------------------------------------------
# Terminal input
# ---------------------------------------------------------
def read_float(prompt, default):

    value = input(f"{prompt} [{default:g}]: ").strip()

    return float(value) if value else default


def format_code(code):

    # Bit order: TOP BOTTOM RIGHT LEFT
    return format(code, "04b")


# ---------------------------------------------------------
# Main
# ---------------------------------------------------------
def main():

    print(f"Clipping window: x = [{XMIN}, {XMAX}], y = [{YMIN}, {YMAX}]")
    print("Enter the line endpoints (press Enter to keep the default)")

    x1 = read_float("x1", -8)
    y1 = read_float("y1", -6)
    x2 = read_float("x2", 8)
    y2 = read_float("y2", 6)

    print(f"\nRegion code of P1 ({x1:g}, {y1:g}): {format_code(compute_code(x1, y1))}")
    print(f"Region code of P2 ({x2:g}, {y2:g}): {format_code(compute_code(x2, y2))}")
    print("(bit order: TOP BOTTOM RIGHT LEFT)")

    # -----------------------------------------------------
    # Cohen-Sutherland clipping
    # -----------------------------------------------------
    clipped = cohen_sutherland(
        x1, y1, x2, y2
    )

    if clipped is None:
        print("\nLine rejected: it lies completely outside the clipping window")

    else:
        cx1, cy1, cx2, cy2 = clipped
        print(f"\nClipped line: ({cx1:g}, {cy1:g}) -> ({cx2:g}, {cy2:g})")

    # -----------------------------------------------------
    # Initialization
    # -----------------------------------------------------
    if not glfw.init():
        sys.exit("Failed to initialize GLFW")

    window = glfw.create_window(
        WIDTH,
        HEIGHT,
        "Cohen-Sutherland Line Clipping",
        None,
        None
    )

    if not window:
        glfw.terminate()
        sys.exit("Failed to create GLFW window")

    glfw.make_context_current(window)

    glClearColor(0.0, 0.0, 0.0, 1.0)

    left, right, bottom, top = get_view_bounds(x1, y1, x2, y2)

    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()

    glOrtho(left, right, bottom, top, -1, 1)

    glMatrixMode(GL_MODELVIEW)

    while not glfw.window_should_close(window):

        display(x1, y1, x2, y2, clipped)

        glfw.swap_buffers(window)
        glfw.poll_events()

    glfw.terminate()


if __name__ == "__main__":
    main()
