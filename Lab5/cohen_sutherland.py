from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import sys


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
def display():

    glClear(GL_COLOR_BUFFER_BIT)

    # -----------------------------------------------------
    # Original line
    # -----------------------------------------------------
    x1, y1 = -8, -6
    x2, y2 = 8, 6

    # Draw clipping window
    glColor3f(1.0, 1.0, 1.0)

    glBegin(GL_LINE_LOOP)

    glVertex2f(XMIN, YMIN)
    glVertex2f(XMAX, YMIN)
    glVertex2f(XMAX, YMAX)
    glVertex2f(XMIN, YMAX)

    glEnd()

    # -----------------------------------------------------
    # Draw original line
    # -----------------------------------------------------
    glColor3f(1.0, 0.0, 0.0)

    glBegin(GL_LINES)

    glVertex2f(x1, y1)
    glVertex2f(x2, y2)

    glEnd()

    # -----------------------------------------------------
    # Cohen-Sutherland clipping
    # -----------------------------------------------------
    clipped = cohen_sutherland(
        x1, y1, x2, y2
    )

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

    glutSwapBuffers()


# ---------------------------------------------------------
# Initialization
# ---------------------------------------------------------
def init():

    glClearColor(0.0, 0.0, 0.0, 1.0)

    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()

    gluOrtho2D(-10, 10, -8, 8)

    glMatrixMode(GL_MODELVIEW)


# ---------------------------------------------------------
# Main
# ---------------------------------------------------------
def main():

    glutInit(sys.argv)

    glutInitDisplayMode(
        GLUT_DOUBLE | GLUT_RGB
    )

    glutInitWindowSize(800, 600)

    glutInitWindowPosition(100, 100)

    glutCreateWindow(
        b"Experiment 5 - Cohen Sutherland Line Clipping"
    )

    init()

    glutDisplayFunc(display)

    glutMainLoop()


if __name__ == "__main__":
    main()
