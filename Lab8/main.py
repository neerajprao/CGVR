import sys
import math
import ctypes
import glfw
from OpenGL.GL import *


# ---------------------------------------------------------
# Window size
# ---------------------------------------------------------
WIDTH = 800
HEIGHT = 600


# ---------------------------------------------------------
# Vertex shader: runs once per vertex
# Transforms the vertex to clip space and passes its
# color, normal and world position to the fragment shader
# ---------------------------------------------------------
VERTEX_SHADER = """
#version 330 core

layout (location = 0) in vec3 aPosition;
layout (location = 1) in vec3 aColor;
layout (location = 2) in vec3 aNormal;

uniform mat4 uModel;
uniform mat4 uView;
uniform mat4 uProjection;

out vec3 vColor;
out vec3 vNormal;
out vec3 vWorldPos;

void main()
{
    vec4 world = uModel * vec4(aPosition, 1.0);

    vWorldPos = world.xyz;

    // The model matrix only rotates, so it can transform normals directly
    vNormal = mat3(uModel) * aNormal;

    vColor = aColor;

    gl_Position = uProjection * uView * world;
}
"""


# ---------------------------------------------------------
# Fragment shader: runs once per pixel (fragment)
# Receives the values interpolated across the triangle
# ---------------------------------------------------------
FRAGMENT_SHADER = """
#version 330 core

in vec3 vColor;
in vec3 vNormal;
in vec3 vWorldPos;

uniform int uMode;
uniform vec3 uLightPos;
uniform vec3 uViewPos;

out vec4 FragColor;

void main()
{
    // Mode 0: color interpolated from the vertices
    if (uMode == 0)
    {
        FragColor = vec4(vColor, 1.0);
        return;
    }

    vec3 N = normalize(vNormal);

    // Mode 2: normal vector shown as a color
    if (uMode == 2)
    {
        FragColor = vec4(N * 0.5 + 0.5, 1.0);
        return;
    }

    // Mode 1: per-fragment Phong lighting
    vec3 L = normalize(uLightPos - vWorldPos);
    vec3 V = normalize(uViewPos - vWorldPos);
    vec3 R = reflect(-L, N);

    float n_dot_l = max(dot(N, L), 0.0);

    float ambient = 0.15;
    float diffuse = 0.7 * n_dot_l;
    float specular = n_dot_l > 0.0 ? 0.5 * pow(max(dot(R, V), 0.0), 32.0) : 0.0;

    FragColor = vec4((ambient + diffuse) * vColor + vec3(specular), 1.0);
}
"""


MODE_NAMES = [
    "Vertex colors (interpolated)",
    "Per-fragment lighting (Phong)",
    "Normals as colors",
]


CAMERA_POS = (0.0, 0.0, 6.0)
LIGHT_POS = (3.0, 4.0, 5.0)


# ---------------------------------------------------------
# Cube geometry: 6 faces x 4 vertices
# Each face has its own vertices so it can have its own normal
# ---------------------------------------------------------
FACES = [
    ((0, 0, 1), [(-1, -1, 1), (1, -1, 1), (1, 1, 1), (-1, 1, 1)]),        # front
    ((0, 0, -1), [(1, -1, -1), (-1, -1, -1), (-1, 1, -1), (1, 1, -1)]),   # back
    ((1, 0, 0), [(1, -1, 1), (1, -1, -1), (1, 1, -1), (1, 1, 1)]),        # right
    ((-1, 0, 0), [(-1, -1, -1), (-1, -1, 1), (-1, 1, 1), (-1, 1, -1)]),   # left
    ((0, 1, 0), [(-1, 1, 1), (1, 1, 1), (1, 1, -1), (-1, 1, -1)]),        # top
    ((0, -1, 0), [(-1, -1, -1), (1, -1, -1), (1, -1, 1), (-1, -1, 1)]),   # bottom
]


def build_cube():

    vertices = []
    indices = []

    for face, (normal, corners) in enumerate(FACES):

        for x, y, z in corners:

            # Color comes from the corner position: RGB cube
            color = ((x + 1) / 2, (y + 1) / 2, (z + 1) / 2)

            vertices.extend((x, y, z) + color + normal)

        # Two triangles per face
        base = face * 4

        indices.extend((base, base + 1, base + 2, base, base + 2, base + 3))

    return vertices, indices


# ---------------------------------------------------------
# 4x4 matrix helpers (row-major, uploaded with transpose)
# ---------------------------------------------------------
def multiply(a, b):

    return [
        [sum(a[row][k] * b[k][col] for k in range(4)) for col in range(4)]
        for row in range(4)
    ]


def translation(tx, ty, tz):

    return [
        [1, 0, 0, tx],
        [0, 1, 0, ty],
        [0, 0, 1, tz],
        [0, 0, 0, 1],
    ]


def rotation_x(angle_in_degrees):

    c = math.cos(math.radians(angle_in_degrees))
    s = math.sin(math.radians(angle_in_degrees))

    return [
        [1, 0, 0, 0],
        [0, c, -s, 0],
        [0, s, c, 0],
        [0, 0, 0, 1],
    ]


def rotation_y(angle_in_degrees):

    c = math.cos(math.radians(angle_in_degrees))
    s = math.sin(math.radians(angle_in_degrees))

    return [
        [c, 0, s, 0],
        [0, 1, 0, 0],
        [-s, 0, c, 0],
        [0, 0, 0, 1],
    ]


def perspective(fov_in_degrees, aspect, near, far):

    f = 1 / math.tan(math.radians(fov_in_degrees) / 2)

    return [
        [f / aspect, 0, 0, 0],
        [0, f, 0, 0],
        [0, 0, (far + near) / (near - far), 2 * far * near / (near - far)],
        [0, 0, -1, 0],
    ]


def set_matrix(location, matrix):

    values = [value for row in matrix for value in row]

    glUniformMatrix4fv(location, 1, GL_TRUE, (ctypes.c_float * 16)(*values))


# ---------------------------------------------------------
# Shader compilation and linking
# ---------------------------------------------------------
def compile_shader(source, shader_type, name):

    shader = glCreateShader(shader_type)

    glShaderSource(shader, source)
    glCompileShader(shader)

    if not glGetShaderiv(shader, GL_COMPILE_STATUS):

        log = glGetShaderInfoLog(shader).decode()

        sys.exit(f"{name} shader failed to compile:\n{log}")

    print(f"{name} shader compiled: OK")

    return shader


def create_program():

    vertex_shader = compile_shader(VERTEX_SHADER, GL_VERTEX_SHADER, "Vertex")
    fragment_shader = compile_shader(FRAGMENT_SHADER, GL_FRAGMENT_SHADER, "Fragment")

    program = glCreateProgram()

    glAttachShader(program, vertex_shader)
    glAttachShader(program, fragment_shader)

    glLinkProgram(program)

    if not glGetProgramiv(program, GL_LINK_STATUS):

        log = glGetProgramInfoLog(program).decode()

        sys.exit(f"Shader program failed to link:\n{log}")

    print("Shader program linked: OK")

    # The linked program keeps the compiled code
    glDeleteShader(vertex_shader)
    glDeleteShader(fragment_shader)

    return program


# ---------------------------------------------------------
# Upload the cube to the GPU (VAO + VBO + EBO)
# ---------------------------------------------------------
def create_buffers(vertices, indices):

    vao = glGenVertexArrays(1)
    glBindVertexArray(vao)

    vertex_data = (ctypes.c_float * len(vertices))(*vertices)

    vbo = glGenBuffers(1)
    glBindBuffer(GL_ARRAY_BUFFER, vbo)
    glBufferData(GL_ARRAY_BUFFER, ctypes.sizeof(vertex_data), vertex_data, GL_STATIC_DRAW)

    index_data = (ctypes.c_uint * len(indices))(*indices)

    ebo = glGenBuffers(1)
    glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, ebo)
    glBufferData(GL_ELEMENT_ARRAY_BUFFER, ctypes.sizeof(index_data), index_data, GL_STATIC_DRAW)

    # Each vertex: position (3) + color (3) + normal (3) floats
    stride = 9 * ctypes.sizeof(ctypes.c_float)

    for location, offset in ((0, 0), (1, 3), (2, 6)):

        glVertexAttribPointer(
            location,
            3,
            GL_FLOAT,
            GL_FALSE,
            stride,
            ctypes.c_void_p(offset * ctypes.sizeof(ctypes.c_float))
        )

        glEnableVertexAttribArray(location)

    glBindVertexArray(0)

    return vao, vbo, ebo


# ---------------------------------------------------------
# Terminal input
# ---------------------------------------------------------
def read_float(prompt, default):

    value = input(f"{prompt} [{default:g}]: ").strip()

    return float(value) if value else default


def read_int(prompt, default):

    value = input(f"{prompt} [{default}]: ").strip()

    return int(value) if value else default


# ---------------------------------------------------------
# Main
# ---------------------------------------------------------
def main():

    print("==========================================")
    print("VERTEX AND FRAGMENT SHADERS")
    print("==========================================\n")

    print("Press Enter to keep the default value")

    speed = read_float("Rotation speed (degrees per second)", 45)

    print("\nFragment shader mode")

    for i, name in enumerate(MODE_NAMES, start=1):
        print(f"{i}. {name}")

    mode = read_int("Choice", 1) - 1

    if not 0 <= mode < len(MODE_NAMES):
        raise SystemExit("Invalid fragment shader mode")

    # -----------------------------------------------------
    # Initialization: request a modern (core profile) context
    # -----------------------------------------------------
    if not glfw.init():
        sys.exit("Failed to initialize GLFW")

    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
    glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
    glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, GL_TRUE)

    window = glfw.create_window(
        WIDTH,
        HEIGHT,
        f"Vertex and Fragment Shaders - {MODE_NAMES[mode]}",
        None,
        None
    )

    if not window:
        glfw.terminate()
        sys.exit("Failed to create GLFW window (OpenGL 3.3 required)")

    glfw.make_context_current(window)

    print("\n==========================================")
    print("OPENGL")
    print("==========================================")

    print(f"OpenGL version: {glGetString(GL_VERSION).decode()}")
    print(f"GLSL version  : {glGetString(GL_SHADING_LANGUAGE_VERSION).decode()}")
    print(f"Renderer      : {glGetString(GL_RENDERER).decode()}")

    print("\n==========================================")
    print("SHADER PROGRAM")
    print("==========================================")

    program = create_program()

    vertices, indices = build_cube()

    vao, vbo, ebo = create_buffers(vertices, indices)

    print("\n==========================================")
    print("VERTEX DATA")
    print("==========================================")

    print(f"Vertices : {len(vertices) // 9} (9 floats = 36 bytes each)")
    print(f"Indices  : {len(indices)} ({len(indices) // 3} triangles)")
    print("Attribute location 0: aPosition (vec3, byte offset 0)")
    print("Attribute location 1: aColor    (vec3, byte offset 12)")
    print("Attribute location 2: aNormal   (vec3, byte offset 24)")
    print("Uniforms: uModel, uView, uProjection, uMode, uLightPos, uViewPos")

    print("\nM: switch fragment shader mode   Space: pause rotation")

    glUseProgram(program)

    model_loc = glGetUniformLocation(program, "uModel")
    view_loc = glGetUniformLocation(program, "uView")
    projection_loc = glGetUniformLocation(program, "uProjection")
    mode_loc = glGetUniformLocation(program, "uMode")

    glUniform3f(glGetUniformLocation(program, "uLightPos"), *LIGHT_POS)
    glUniform3f(glGetUniformLocation(program, "uViewPos"), *CAMERA_POS)

    set_matrix(view_loc, translation(-CAMERA_POS[0], -CAMERA_POS[1], -CAMERA_POS[2]))

    state = {"mode": mode, "paused": False}

    def key_callback(win, key, scancode, action, mods):

        if action != glfw.PRESS:
            return

        if key == glfw.KEY_M:

            state["mode"] = (state["mode"] + 1) % len(MODE_NAMES)

            name = MODE_NAMES[state["mode"]]

            glfw.set_window_title(win, f"Vertex and Fragment Shaders - {name}")

            print(f"Fragment shader mode: {name}")

        elif key == glfw.KEY_SPACE:

            state["paused"] = not state["paused"]

    glfw.set_key_callback(window, key_callback)

    # Hidden surface removal by the GPU's depth buffer (see Lab 6)
    glEnable(GL_DEPTH_TEST)

    glClearColor(0.05, 0.05, 0.05, 1.0)

    angle = 0.0
    last_time = glfw.get_time()

    while not glfw.window_should_close(window):

        current_time = glfw.get_time()

        if not state["paused"]:
            angle += speed * (current_time - last_time)

        last_time = current_time

        # Framebuffer size is in pixels (differs from window size on Retina displays)
        fb_w, fb_h = glfw.get_framebuffer_size(window)

        glViewport(0, 0, fb_w, fb_h)

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        # Uniforms: per-frame values shared by every vertex / fragment
        set_matrix(projection_loc, perspective(45, fb_w / max(1, fb_h), 0.1, 100))
        set_matrix(model_loc, multiply(rotation_x(25), rotation_y(angle)))

        glUniform1i(mode_loc, state["mode"])

        glBindVertexArray(vao)
        glDrawElements(GL_TRIANGLES, len(indices), GL_UNSIGNED_INT, None)

        glfw.swap_buffers(window)
        glfw.poll_events()

    # Free GPU resources
    glDeleteVertexArrays(1, [vao])
    glDeleteBuffers(2, [vbo, ebo])
    glDeleteProgram(program)

    glfw.terminate()


if __name__ == "__main__":
    main()
