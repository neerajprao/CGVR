import sys
import math
import ctypes
import glfw
from OpenGL.GL import *


# ---------------------------------------------------------
# Window size
# The window is split into two viewports side by side
# ---------------------------------------------------------
WIDTH = 1000
HEIGHT = 500


# ---------------------------------------------------------
# Vertex shader: Model -> View -> Projection
# The GPU then does the perspective division and the
# viewport mapping (the same steps print_pipeline shows)
# ---------------------------------------------------------
VERTEX_SHADER = """
#version 330 core

layout (location = 0) in vec3 aPosition;
layout (location = 1) in vec3 aColor;

uniform mat4 uModel;
uniform mat4 uView;
uniform mat4 uProjection;

out vec3 vColor;

void main()
{
    vec4 worldPosition = uModel * vec4(aPosition, 1.0);
    vec4 viewPosition = uView * worldPosition;

    gl_Position = uProjection * viewPosition;
    vColor = aColor;
}
"""


# ---------------------------------------------------------
# Fragment shader
# ---------------------------------------------------------
FRAGMENT_SHADER = """
#version 330 core

in vec3 vColor;
out vec4 FragColor;

void main()
{
    FragColor = vec4(vColor, 1.0);
}
"""


# ---------------------------------------------------------
# Camera and view volume
# ---------------------------------------------------------
CAMERA_POS = (3.0, 2.0, 6.0)
CAMERA_TARGET = (0.0, 0.0, 0.0)
CAMERA_UP = (0.0, 1.0, 0.0)

FOV = 45.0
NEAR = 0.1
FAR = 100.0

# Half-height of the orthographic view volume
ORTHO_SIZE = 2.5

ORBIT_STEP = 10.0

PROJECTION_NAMES = ["Perspective", "Orthographic"]

BACKGROUNDS = [
    (0.05, 0.05, 0.05),
    (0.09, 0.09, 0.12),
]


# ---------------------------------------------------------
# Cube geometry
# Each vertex: position (3) + color (3)
# ---------------------------------------------------------
def build_cube():

    vertices = [
        -1, -1,  1,  1, 0, 0,
         1, -1,  1,  0, 1, 0,
         1,  1,  1,  0, 0, 1,
        -1,  1,  1,  1, 1, 0,

        -1, -1, -1,  1, 0, 1,
         1, -1, -1,  0, 1, 1,
         1,  1, -1,  1, 1, 1,
        -1,  1, -1,  1, 0.5, 0,
    ]

    indices = [
        0, 1, 2, 0, 2, 3,
        5, 4, 7, 5, 7, 6,
        4, 0, 3, 4, 3, 7,
        1, 5, 6, 1, 6, 2,
        3, 2, 6, 3, 6, 7,
        4, 5, 1, 4, 1, 0,
    ]

    return vertices, indices


# ---------------------------------------------------------
# Vector helpers
# ---------------------------------------------------------
def subtract(a, b):

    return [a[i] - b[i] for i in range(3)]


def dot(a, b):

    return sum(a[i] * b[i] for i in range(3))


def cross(a, b):

    return [
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    ]


def normalize(v):

    length = math.sqrt(dot(v, v))

    return [x / length for x in v]


# ---------------------------------------------------------
# Matrix multiplication
# ---------------------------------------------------------
def multiply(a, b):

    return [
        [
            sum(a[row][k] * b[k][col] for k in range(4))
            for col in range(4)
        ]
        for row in range(4)
    ]


# ---------------------------------------------------------
# Matrix * homogeneous point
# ---------------------------------------------------------
def transform(matrix, point):

    return [
        sum(matrix[row][k] * point[k] for k in range(4))
        for row in range(4)
    ]


# ---------------------------------------------------------
# Translation matrix
# ---------------------------------------------------------
def translation(tx, ty, tz):

    return [
        [1, 0, 0, tx],
        [0, 1, 0, ty],
        [0, 0, 1, tz],
        [0, 0, 0, 1],
    ]


# ---------------------------------------------------------
# Rotation around X-axis
# ---------------------------------------------------------
def rotation_x(angle):

    c = math.cos(math.radians(angle))
    s = math.sin(math.radians(angle))

    return [
        [1, 0, 0, 0],
        [0, c, -s, 0],
        [0, s, c, 0],
        [0, 0, 0, 1],
    ]


# ---------------------------------------------------------
# Rotation around Y-axis
# ---------------------------------------------------------
def rotation_y(angle):

    c = math.cos(math.radians(angle))
    s = math.sin(math.radians(angle))

    return [
        [c, 0, s, 0],
        [0, 1, 0, 0],
        [-s, 0, c, 0],
        [0, 0, 0, 1],
    ]


# ---------------------------------------------------------
# View transformation (look-at)
# Builds the camera axes u, v, n and changes world
# coordinates into eye coordinates, where the camera
# sits at the origin looking down -Z
# ---------------------------------------------------------
def look_at(eye, target, up):

    forward = normalize(subtract(target, eye))
    right = normalize(cross(forward, up))
    true_up = cross(right, forward)

    return [
        [right[0], right[1], right[2], -dot(right, eye)],
        [true_up[0], true_up[1], true_up[2], -dot(true_up, eye)],
        [-forward[0], -forward[1], -forward[2], dot(forward, eye)],
        [0, 0, 0, 1],
    ]


# ---------------------------------------------------------
# Perspective projection matrix
# Converts the view frustum into clip coordinates;
# w = -z_eye, so distant points shrink after the division
# ---------------------------------------------------------
def perspective(fov, aspect, near, far):

    f = 1.0 / math.tan(math.radians(fov) / 2.0)

    return [
        [f / aspect, 0, 0, 0],
        [0, f, 0, 0],
        [
            0, 0,
            (far + near) / (near - far),
            (2 * far * near) / (near - far)
        ],
        [0, 0, -1, 0],
    ]


# ---------------------------------------------------------
# Orthographic (parallel) projection matrix
# Maps the box [l,r] x [b,t] x [-n,-f] to the NDC cube;
# w stays 1, so size does not depend on distance
# ---------------------------------------------------------
def orthographic(left, right, bottom, top, near, far):

    return [
        [2 / (right - left), 0, 0, -(right + left) / (right - left)],
        [0, 2 / (top - bottom), 0, -(top + bottom) / (top - bottom)],
        [0, 0, -2 / (far - near), -(far + near) / (far - near)],
        [0, 0, 0, 1],
    ]


def create_projection(kind, aspect):

    if kind == 0:
        return perspective(FOV, aspect, NEAR, FAR)

    return orthographic(
        -ORTHO_SIZE * aspect, ORTHO_SIZE * aspect,
        -ORTHO_SIZE, ORTHO_SIZE,
        NEAR, FAR
    )


# ---------------------------------------------------------
# Perspective division
# Clip coordinates -> normalized device coordinates [-1, 1]
# ---------------------------------------------------------
def perspective_divide(clip):

    w = clip[3]

    return [clip[0] / w, clip[1] / w, clip[2] / w]


# ---------------------------------------------------------
# Viewport mapping
# NDC [-1, 1] -> window pixels inside the viewport (x, y, w, h)
# and depth [-1, 1] -> [0, 1] for the depth buffer
# ---------------------------------------------------------
def viewport_map(ndc, x, y, width, height):

    return [
        x + (ndc[0] + 1) * width / 2,
        y + (ndc[1] + 1) * height / 2,
        (ndc[2] + 1) / 2,
    ]


# ---------------------------------------------------------
# Print every stage of the pipeline on the CPU
# ---------------------------------------------------------
def fmt(values):

    return "(" + ", ".join(f"{v:7.2f}" for v in values) + ")"


def print_pipeline(name, vertices, model, view, projection, viewport):

    count = len(vertices) // 6

    print(f"\n--- {name} viewport {viewport} ---")

    obj = vertices[0:3] + [1]
    world = transform(model, obj)
    eye = transform(view, world)
    clip = transform(projection, eye)
    ndc = perspective_divide(clip)
    window = viewport_map(ndc, *viewport)

    print("Vertex 0 through the pipeline:")
    print(f"  1. Object                {fmt(obj)}")
    print(f"  2. World  = Model * obj  {fmt(world)}")
    print(f"  3. Eye    = View * world {fmt(eye)}")
    print(f"  4. Clip   = Proj * eye   {fmt(clip)}")
    print(f"  5. NDC    = clip / w     {fmt(ndc)}")
    print(f"  6. Window = viewport     {fmt(window)}")

    print("\n #   NDC x   NDC y   NDC z   Win x   Win y   Depth")

    for i in range(count):

        obj = vertices[i * 6:i * 6 + 3] + [1]
        clip = transform(projection, transform(view, transform(model, obj)))
        ndc = perspective_divide(clip)
        window = viewport_map(ndc, *viewport)

        print(
            f" {i}  "
            + " ".join(f"{v:7.2f}" for v in ndc)
            + " "
            + " ".join(f"{v:7.2f}" for v in window)
        )


# ---------------------------------------------------------
# Upload matrix to OpenGL
# ---------------------------------------------------------
def set_matrix(location, matrix):

    values = [
        value
        for row in matrix
        for value in row
    ]

    glUniformMatrix4fv(
        location,
        1,
        GL_TRUE,
        (ctypes.c_float * 16)(*values)
    )


# ---------------------------------------------------------
# Compile shader
# ---------------------------------------------------------
def compile_shader(source, shader_type, name):

    shader = glCreateShader(shader_type)

    glShaderSource(shader, source)
    glCompileShader(shader)

    if not glGetShaderiv(shader, GL_COMPILE_STATUS):

        log = glGetShaderInfoLog(shader).decode()
        sys.exit(f"{name} shader failed:\n{log}")

    print(f"{name} shader compiled: OK")

    return shader


# ---------------------------------------------------------
# Create shader program
# ---------------------------------------------------------
def create_program():

    vertex_shader = compile_shader(
        VERTEX_SHADER, GL_VERTEX_SHADER, "Vertex"
    )

    fragment_shader = compile_shader(
        FRAGMENT_SHADER, GL_FRAGMENT_SHADER, "Fragment"
    )

    program = glCreateProgram()

    glAttachShader(program, vertex_shader)
    glAttachShader(program, fragment_shader)

    glLinkProgram(program)

    if not glGetProgramiv(program, GL_LINK_STATUS):

        log = glGetProgramInfoLog(program).decode()
        sys.exit(f"Shader linking failed:\n{log}")

    print("Shader program linked: OK")

    glDeleteShader(vertex_shader)
    glDeleteShader(fragment_shader)

    return program


# ---------------------------------------------------------
# Upload geometry to GPU
# VAO + VBO + EBO
# ---------------------------------------------------------
def create_buffers(vertices, indices):

    vao = glGenVertexArrays(1)
    glBindVertexArray(vao)

    vertex_data = (ctypes.c_float * len(vertices))(*vertices)

    vbo = glGenBuffers(1)
    glBindBuffer(GL_ARRAY_BUFFER, vbo)

    glBufferData(
        GL_ARRAY_BUFFER,
        ctypes.sizeof(vertex_data),
        vertex_data,
        GL_STATIC_DRAW
    )

    index_data = (ctypes.c_uint * len(indices))(*indices)

    ebo = glGenBuffers(1)
    glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, ebo)

    glBufferData(
        GL_ELEMENT_ARRAY_BUFFER,
        ctypes.sizeof(index_data),
        index_data,
        GL_STATIC_DRAW
    )

    stride = 6 * ctypes.sizeof(ctypes.c_float)

    # Position attribute
    glVertexAttribPointer(
        0, 3, GL_FLOAT, GL_FALSE,
        stride, ctypes.c_void_p(0)
    )
    glEnableVertexAttribArray(0)

    # Color attribute
    glVertexAttribPointer(
        1, 3, GL_FLOAT, GL_FALSE,
        stride,
        ctypes.c_void_p(3 * ctypes.sizeof(ctypes.c_float))
    )
    glEnableVertexAttribArray(1)

    glBindVertexArray(0)

    return vao, vbo, ebo


# ---------------------------------------------------------
# Terminal input
# ---------------------------------------------------------
def read_float(prompt, default):

    value = input(f"{prompt} [{default:g}]: ").strip()

    return float(value) if value else default


# ---------------------------------------------------------
# Main
# ---------------------------------------------------------
def main():

    print("==========================================")
    print("3D VIEWING PIPELINE")
    print("==========================================")

    print("1. Model transformation      (object -> world)")
    print("2. View transformation       (world -> eye, look-at camera)")
    print("3. Projection                (eye -> clip, perspective / orthographic)")
    print("4. Perspective division      (clip -> NDC)")
    print("5. Viewport mapping          (NDC -> window pixels)")
    print("6. Depth testing             (hidden surface removal)")

    print("\nPress Enter to keep the default value")

    camera = [
        read_float("Camera x", CAMERA_POS[0]),
        read_float("Camera y", CAMERA_POS[1]),
        read_float("Camera z", CAMERA_POS[2]),
    ]

    if camera == list(CAMERA_TARGET):
        sys.exit("Camera cannot be at the target point (0, 0, 0)")

    speed = read_float("Rotation speed (degrees per second)", 45)

    if not glfw.init():
        sys.exit("Failed to initialize GLFW")

    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
    glfw.window_hint(
        glfw.OPENGL_PROFILE,
        glfw.OPENGL_CORE_PROFILE
    )
    glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, GL_TRUE)

    window = glfw.create_window(
        WIDTH, HEIGHT,
        "3D Viewing Pipeline - Perspective (left) | Orthographic (right)",
        None, None
    )

    if not window:
        glfw.terminate()
        sys.exit("Failed to create GLFW window")

    glfw.make_context_current(window)

    print("\nOpenGL:", glGetString(GL_VERSION).decode())
    print("Renderer:", glGetString(GL_RENDERER).decode())

    program = create_program()

    vertices, indices = build_cube()
    vao, vbo, ebo = create_buffers(vertices, indices)

    print("\nVertices:", len(vertices) // 6)
    print("Indices:", len(indices))
    print("Triangles:", len(indices) // 3)

    print("\nLeft viewport: perspective   Right viewport: orthographic")
    print("Left/Right: orbit camera   Space: pause   T: print pipeline   Esc: quit")

    glUseProgram(program)

    model_loc = glGetUniformLocation(program, "uModel")
    view_loc = glGetUniformLocation(program, "uView")
    projection_loc = glGetUniformLocation(
        program, "uProjection"
    )

    # Print the pipeline for the first frame
    state = {"paused": False, "orbit": 0.0, "trace": True}

    def key_callback(win, key, scancode, action, mods):

        if action not in (glfw.PRESS, glfw.REPEAT):
            return

        if key == glfw.KEY_ESCAPE:
            glfw.set_window_should_close(win, True)

        elif key == glfw.KEY_SPACE:
            state["paused"] = not state["paused"]

        elif key == glfw.KEY_LEFT:
            state["orbit"] -= ORBIT_STEP

        elif key == glfw.KEY_RIGHT:
            state["orbit"] += ORBIT_STEP

        elif key == glfw.KEY_T:
            state["trace"] = True

    glfw.set_key_callback(window, key_callback)

    # Hidden surface removal by the GPU's depth buffer (see Lab 6)
    glEnable(GL_DEPTH_TEST)

    # Keep each glClear inside its own viewport
    glEnable(GL_SCISSOR_TEST)

    angle = 0.0
    last_time = glfw.get_time()

    while not glfw.window_should_close(window):

        current_time = glfw.get_time()
        delta_time = current_time - last_time
        last_time = current_time

        if not state["paused"]:
            angle += speed * delta_time

        # ---------------------------------------------
        # View transformation
        # Orbit the camera around the Y-axis
        # ---------------------------------------------
        eye = transform(rotation_y(state["orbit"]), camera + [1])[:3]

        view = look_at(eye, CAMERA_TARGET, CAMERA_UP)

        set_matrix(view_loc, view)

        # ---------------------------------------------
        # Model transformation
        # ---------------------------------------------
        model = multiply(
            rotation_x(25.0),
            rotation_y(angle)
        )

        set_matrix(model_loc, model)

        # ---------------------------------------------
        # Viewport mapping
        # Split the framebuffer into two viewports
        # ---------------------------------------------
        fb_w, fb_h = glfw.get_framebuffer_size(window)

        fb_w = max(2, fb_w)
        fb_h = max(1, fb_h)

        half = fb_w // 2

        viewports = [
            (0, 0, half, fb_h),
            (half, 0, fb_w - half, fb_h),
        ]

        if state["trace"]:
            print(f"\nCamera eye: {fmt(eye)}   Model angle: {angle % 360:.1f} deg")

        for kind, viewport in enumerate(viewports):

            x, y, w, h = viewport

            glViewport(x, y, w, h)
            glScissor(x, y, w, h)

            glClearColor(*BACKGROUNDS[kind], 1.0)
            glClear(
                GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT
            )

            # -----------------------------------------
            # Projection
            # -----------------------------------------
            projection = create_projection(kind, w / h)

            set_matrix(projection_loc, projection)

            if state["trace"]:
                print_pipeline(
                    PROJECTION_NAMES[kind], vertices,
                    model, view, projection, viewport
                )

            # -----------------------------------------
            # Render the 3D object on the 2D screen
            # -----------------------------------------
            glBindVertexArray(vao)

            glDrawElements(
                GL_TRIANGLES,
                len(indices),
                GL_UNSIGNED_INT,
                None
            )

        state["trace"] = False

        glfw.swap_buffers(window)
        glfw.poll_events()

    # Release GPU resources
    glDeleteVertexArrays(1, [vao])
    glDeleteBuffers(2, [vbo, ebo])
    glDeleteProgram(program)

    glfw.terminate()


if __name__ == "__main__":
    main()
