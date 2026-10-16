# Computer Graphics Lab

This repository contains implementations of computer graphics algorithms using **Python and PyOpenGL**.

## Lab Programs

### 1. DDA and Bresenham Line Drawing Algorithms

**Description:**
The Digital Differential Analyzer (DDA) algorithm samples the line at unit intervals along its longer axis and rounds the floating-point coordinates to the nearest pixel. The Bresenham Line Drawing Algorithm is an incremental line rasterization algorithm that uses only integer arithmetic to decide which pixels best approximate the line.

The program reads the line endpoints (press Enter to use the default line from `(100, 100)` to `(700, 400)`) and draws the line with DDA in the left panel (green) and with Bresenham in the right panel (red) so the two can be compared.

**Implementation:**

[`Lab1/main.py`](Lab1/main.py)

**Output:**

![DDA and Bresenham Line Drawing](Lab1/Output/Line.png)

---

### 2. Midpoint Circle Drawing Algorithm

**Description:**
The Midpoint Circle Drawing Algorithm uses a decision parameter to determine the closest pixels to the circumference of a circle. It calculates one octant of the circle and uses 8-way symmetry to generate the remaining points.

The program reads the center and radius (press Enter to use the default center `(400, 300)` and radius `150`).

**Implementation:**

[`Lab2/main.py`](Lab2/main.py)

**Output:**

![Midpoint Circle Drawing](Lab2/Output/Circle.png)

---

### 3. 2D Transformations Using Homogeneous Coordinates

**Description:**
Lab 3 demonstrates 2D geometric transformations using **3x3 homogeneous transformation matrices**. The program supports translation, rotation, scaling, reflection, and shearing. It displays the original shape with a dashed blue outline and the transformed shape with a solid red outline.

The sample shape uses three vertices:

* `(-1, 0)`
* `(1, 0)`
* `(0, 2)`

The number of vertices, vertex coordinates, transformation type, transformation values, rotation pivot, scaling fixed point, reflection axis, and shearing reference point are all customizable through the program prompts.

**Implementation:**

[`Lab3/main.py`](Lab3/main.py)

**Outputs:**

#### Translation

![Translation](Lab3/Output/Translation.png)

#### Rotation

![Rotation](Lab3/Output/Rotation.png)

#### Scaling

![Scaling](Lab3/Output/Scaling.png)

#### Reflection

![Reflection](Lab3/Output/Reflection.png)

#### Shearing

![Shearing](Lab3/Output/Shearing.png)

---

### 4. Composite 2D Transformations Using Matrix Representation

**Description:**
Lab 4 extends Lab 3 by chaining multiple 2D transformations (translation, rotation, scaling, reflection, and shearing) into a single **composite transformation matrix**. The program reads a custom shape, lets the user build a sequence of transformations, and applies them one after another, printing the intermediate coordinates at every stage. Each stage of the transformation is animated on the graph so the full sequence from the original shape to the final result can be visualized. Press `R` to replay the animation.

**Implementation:**

[`Lab4/main.py`](Lab4/main.py)

**Output:**

<video src="https://raw.githubusercontent.com/neerajprao/CGVR/main/Lab4/Output/Lab4_Demo.mp4" controls width="600"></video>

> If the video above does not render, watch/download it directly: [`Lab4/Output/Lab4_Demo.mp4`](Lab4/Output/Lab4_Demo.mp4)

---

### 5. Cohen-Sutherland Line Clipping Algorithm

**Description:**
Lab 5 implements the **Cohen-Sutherland Line Clipping Algorithm**, which clips a line segment against a rectangular clipping window. Each endpoint is assigned a 4-bit region code (top, bottom, right, left) relative to the window, and the algorithm iteratively computes intersections with the window boundaries until the line is trivially accepted (fully inside) or trivially rejected (fully outside). The original line is drawn in red and the clipped portion inside the window is highlighted in green.

The clipping window is `x = [-4, 4]`, `y = [-3, 3]`. The program reads the line endpoints (press Enter to use the default line from `(-8, -6)` to `(8, 6)`) and prints the region codes and the clipped line.

**Implementation:**

[`Lab5/main.py`](Lab5/main.py)

**Output:**

![Cohen-Sutherland Line Clipping](Lab5/Output/LineClipping.png)

---

### 6. Z-Buffer Algorithm for Hidden Surface Removal

**Description:**
Lab 6 implements the **Z-buffer (depth buffer) algorithm** in software. Every pixel stores a color in the frame buffer and a depth in the depth buffer, initialized to the background color and the farthest depth. Each polygon is scan converted, its depth at every pixel is computed from its plane equation `Ax + By + Cz + D = 0` (incrementally, `z' = z - A/C` along a scan line), and the pixel is overwritten only if the new surface is closer to the viewer. Because the test is done per pixel, it correctly handles polygons that pass through each other.

The default scene has four polygons, including a red band tilted in depth that passes through a green band. The left panel draws the polygons in input order without a Z-buffer (the far blue wall wrongly covers everything), and the right panel shows the correct result with the Z-buffer. Press `D` to switch the right panel to a grayscale view of the depth buffer (nearer = brighter). The program prints each polygon's plane equation, depth-test results, and visible pixel count. Custom polygons can be entered instead of the default scene.

**Implementation:**

[`Lab6/main.py`](Lab6/main.py)

**Outputs:**

#### Without vs With Z-Buffer

![Z-Buffer](Lab6/Output/ZBuffer.png)

#### Depth Buffer

![Depth Buffer](Lab6/Output/DepthBuffer.png)

---

### 7. Phong Illumination Model

**Description:**
Lab 7 implements the **Phong illumination model** on a 3D sphere, evaluated in software at every pixel:

```
I = ka·Ia + kd·Il·(N·L) + ks·Il·(R·V)^n
```

where `N` is the surface normal, `L` the unit vector to the point light, `R = 2(N·L)N − L` the reflection of `L`, and `V` the view vector. The window shows the three terms separately and then their sum: **Ambient | Diffuse | Specular | Phong**. Ambient and diffuse light take the object's color, while the specular highlight takes the light's color (white).

The program reads the coefficients `ka`, `kd`, `ks`, the shininess exponent `n`, the light position, and the object color (press Enter to keep the defaults), then prints a worked example of every vector and term at the brightest point on the sphere. In the window, the arrow keys move the light, `+`/`-` double or halve the shininess, and `R` resets.

**Implementation:**

[`Lab7/main.py`](Lab7/main.py)

**Outputs:**

#### Default (shininess n = 32)

![Phong Illumination](Lab7/Output/Phong.png)

#### Low shininess (n = 4): wider, softer highlight

![Phong Illumination, low shininess](Lab7/Output/Phong_LowShininess.png)

---

### 8. Basic OpenGL Program Using Vertex and Fragment Shaders

**Description:**
Lab 8 uses the **programmable pipeline** (OpenGL 3.3 core profile) to draw a rotating 3D cube with GLSL shaders. The cube's vertices (position, color, and normal for each of 24 vertices) are uploaded once to GPU memory in a **VBO**, the 36 triangle indices in an **EBO**, and the attribute layout is recorded in a **VAO**.

* The **vertex shader** runs once per vertex: it transforms the vertex with the model, view, and projection matrices (passed as uniforms) and passes its color, normal, and world position on to the next stage.
* The **fragment shader** runs once per pixel on the values interpolated across each triangle. It has three modes: interpolated vertex colors, per-fragment Phong lighting (Lab 7's model on the GPU), and the surface normal shown as a color.

The program reads the rotation speed and the starting fragment shader mode (press Enter to keep the defaults), and prints the OpenGL/GLSL versions, the shader compile and link status, and the vertex layout. In the window, `M` switches the fragment shader mode and `Space` pauses the rotation. The GPU's depth buffer is enabled for hidden surface removal (see Lab 6).

**Implementation:**

[`Lab8/main.py`](Lab8/main.py)

**Outputs:**

#### Vertex colors (interpolated)

![Vertex colors](Lab8/Output/VertexColors.png)

#### Per-fragment lighting

![Per-fragment lighting](Lab8/Output/Lighting.png)

#### Normals as colors

![Normals](Lab8/Output/Normals.png)

---

## Technologies Used

* Python
* PyOpenGL
* GLFW
* OpenGL


## How to Run

Install the required packages:

```bash
pip install -r requirements.txt
```

Then navigate to the required lab folder and run:

```bash
cd Lab1
python main.py
```
