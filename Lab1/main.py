import math
import glfw
from OpenGL.GL import *


# Each panel uses an 800 x 600 coordinate system
COORD_W = 800
COORD_H = 600


def dda_line(x1, y1, x2, y2):

    dx = x2 - x1
    dy = y2 - y1

    steps = max(abs(dx), abs(dy))

    if steps == 0:
        glVertex2i(x1, y1)
        return

    x_inc = dx / steps
    y_inc = dy / steps

    x = x1
    y = y1

    for _ in range(steps + 1):

        # Round half up to the nearest pixel
        glVertex2i(math.floor(x + 0.5), math.floor(y + 0.5))

        x += x_inc
        y += y_inc


def bresenham_line(x1, y1, x2, y2):

    dx = abs(x2 - x1)
    dy = abs(y2 - y1)

    sx = 1 if x2 > x1 else -1
    sy = 1 if y2 > y1 else -1

    err = dx - dy

    while True:

        glVertex2i(x1, y1)

        if x1 == x2 and y1 == y2:
            break

        e2 = 2 * err

        if e2 > -dy:
            err -= dy
            x1 += sx

        if e2 < dx:
            err += dx
            y1 += sy


def read_int(prompt, default):

    value = input(f"{prompt} [{default}]: ").strip()

    return int(value) if value else default


def draw_border():

    glColor3f(0.4, 0.4, 0.4)
    glLineWidth(1.0)

    glBegin(GL_LINE_LOOP)
    glVertex2f(1, 1)
    glVertex2f(COORD_W - 1, 1)
    glVertex2f(COORD_W - 1, COORD_H - 1)
    glVertex2f(1, COORD_H - 1)
    glEnd()


def main():

    print("Enter the line endpoints (0-800 for x, 0-600 for y)")
    print("Press Enter to keep the default value")

    x1 = read_int("x1", 100)
    y1 = read_int("y1", 100)
    x2 = read_int("x2", 700)
    y2 = read_int("y2", 400)

    print("\nLeft panel : DDA (green)")
    print("Right panel: Bresenham (red)")

    if not glfw.init():
        return

    window = glfw.create_window(
        1200,
        450,
        "DDA (left) vs Bresenham (right) Line Drawing",
        None,
        None
    )

    if not window:
        glfw.terminate()
        return

    glfw.make_context_current(window)

    # Set coordinate system (shared by both panels)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    glOrtho(0, COORD_W, 0, COORD_H, -1, 1)

    glMatrixMode(GL_MODELVIEW)

    panels = [
        (dda_line, (0.0, 1.0, 0.0)),
        (bresenham_line, (1.0, 0.0, 0.0)),
    ]

    while not glfw.window_should_close(window):

        glClear(GL_COLOR_BUFFER_BIT)

        # Framebuffer size is in pixels (differs from window size on Retina displays)
        fb_w, fb_h = glfw.get_framebuffer_size(window)
        half = fb_w // 2

        for i, (draw_line, color) in enumerate(panels):

            glViewport(i * half, 0, half, fb_h)

            draw_border()

            glColor3f(*color)

            glPointSize(3)

            glBegin(GL_POINTS)

            draw_line(x1, y1, x2, y2)

            glEnd()

        glfw.swap_buffers(window)
        glfw.poll_events()

    glfw.terminate()


if __name__ == "__main__":
    main()
