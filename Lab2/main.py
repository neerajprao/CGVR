import glfw
from OpenGL.GL import *


def plot_circle_points(xc, yc, x, y):

    glVertex2i(xc + x, yc + y)
    glVertex2i(xc - x, yc + y)
    glVertex2i(xc + x, yc - y)
    glVertex2i(xc - x, yc - y)

    glVertex2i(xc + y, yc + x)
    glVertex2i(xc - y, yc + x)
    glVertex2i(xc + y, yc - x)
    glVertex2i(xc - y, yc - x)


def midpoint_circle(xc, yc, r):

    x = 0
    y = r

    # Initial decision parameter
    p = 1 - r

    while x <= y:

        plot_circle_points(xc, yc, x, y)

        x += 1

        if p < 0:
            p = p + 2 * x + 1

        else:
            y -= 1
            p = p + 2 * x - 2 * y + 1


def read_int(prompt, default):

    value = input(f"{prompt} [{default}]: ").strip()

    return int(value) if value else default


def main():

    print("Enter the circle parameters (window is 800 x 600)")
    print("Press Enter to keep the default value")

    xc = read_int("Center x", 400)
    yc = read_int("Center y", 300)
    r = read_int("Radius", 150)

    if r <= 0:
        raise SystemExit("Radius must be positive")

    if not glfw.init():
        return

    window = glfw.create_window(
        800,
        600,
        "Midpoint Circle Drawing",
        None,
        None
    )

    if not window:
        glfw.terminate()
        return

    glfw.make_context_current(window)

    # Coordinate system
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()

    glOrtho(
        0, 800,
        0, 600,
        -1, 1
    )

    glMatrixMode(GL_MODELVIEW)

    # Background
    glClearColor(
        0.05, 0.05, 0.05, 1.0
    )

    while not glfw.window_should_close(window):

        glClear(GL_COLOR_BUFFER_BIT)

        # Circle color
        glColor3f(
            0.0, 1.0, 0.0
        )

        # Pixel size
        glPointSize(4)

        glBegin(GL_POINTS)

        midpoint_circle(
            xc,
            yc,
            r
        )

        glEnd()

        glfw.swap_buffers(window)
        glfw.poll_events()

    glfw.terminate()


if __name__ == "__main__":
    main()