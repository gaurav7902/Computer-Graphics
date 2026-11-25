# Computer Graphics

Course lectures and interactive lab activities for Computer Graphics (NCSD302).
The repository includes 28 lecture PDFs and Python demonstrations that make raster
images, transformations, viewing, clipping, shading, colour, and related graphics
algorithms easier to explore.

Course and resource credit: [Prof. Saurabh Srivastava](https://people.iitism.ac.in/~ssrivastava/),
Assistant Professor, Department of Computer Science & Engineering, IIT (ISM) Dhanbad.

## Repository Structure

```text
Computer-Graphics/
├── Computer_Graphics_Numerical_Question_Bank_1.pdf
├── Lectures/                                      # Lecture slides arranged by unit and topic
│   ├── 0.0 Introduction to the Course.pdf
│   ├── 1.1 Introduction to Computer Graphics and Rendering.pdf
│   ├── 1.2 Raster Images and Graphics Devices.pdf
│   ├── 2.1 Object Representation Fundamentals.pdf
│   ├── 2.2 Representing Lines and Curves – Part 1.pdf
│   ├── 2.3 Representing Lines and Curves – Part 2.pdf
│   ├── 2.4 Representing Lines and Curves – Part 3.pdf
│   ├── 2.5 Representing Surfaces.pdf
│   ├── 3.1 Introduction To Transforms.pdf
│   ├── 3.2 Viewing and Projection.pdf
│   ├── 3.3 Clipping.pdf
│   ├── 3.4 Graphics Rendering.pdf
│   ├── 3.5 Scan Conversion.pdf
│   ├── 4.1 Colour Models and Display Considerations.pdf
│   ├── 5.1 Visibility Problem and Back-Face Culling.pdf
│   ├── 5.2 Painters Algorithm and Z-Buffers.pdf
│   ├── 5.3 Triangle Rasterisation and Barycentric Coordinates.pdf
│   ├── 5.4 Interpolating Depth and Surface Attributes.pdf
│   ├── 5.5 Extended Visibility and Transparency.pdf
│   ├── 5.6 Integrated Solid-Object Rasteriser.pdf
│   ├── 6.1 Computer Animation.pdf
│   ├── 6.2 Texture Mapping and Related Techniques.pdf
│   ├── 7.1 Hierarchical Modelling and Scene Graphs.pdf
│   ├── 7.2 Fractal Geometry and Procedural Generation.pdf
│   ├── 8.1 Event-Driven Interaction and Camera Control.pdf
│   ├── 8.2 Selection Picking and Object Manipulation.pdf
│   ├── 8.3 Graphics Software and GPU.pdf
│   ├── 9 Ray Tracing.pdf
├── Resources/
│   ├── Activity 1.3/                            # Introductory raster and display demonstrations
│   │   ├── 01_framebuffer.py                    # Create and display an RGB pixel framebuffer
│   │   ├── 02_primitives.py                     # Render basic geometric drawing primitives
│   │   ├── 03_aliasing.py                       # Compare aliased and supersampled rendering
│   │   ├── README.md                            # Setup, controls, and activity guide
│   │   └── requirements.txt                     # Python dependencies for this activity
│   └── Activity 4.2/                            # Interactive lab for Units 3 and 4
│       ├── main.py                              # Application entry point and demo registration
│       ├── core/                                # Shared app framework, widgets, viewport, and stepping
│       ├── demos/                               # Interactive lesson modes for graphics topics
│       ├── graphics/                            # Standalone implementations of graphics algorithms
│       ├── tests/                               # Checks for matrix and graphics calculations
│       ├── previews/                            # Demo screenshots
│       ├── README.md                            # Setup, controls, demos, and test instructions
│       └── requirements.txt                     # Python dependencies for this activity
└── Syllabus.pdf                                 # Course syllabus
```

This README is at the repository root, alongside the `Computer-Graphics/` directory.

## Lectures

The [`Lectures/`](Computer-Graphics/Lectures) directory contains the theory material for the
course sequence.

| Unit | Topics                                                                                                                                                             |
| ---- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| 1    | Computer graphics and rendering, raster images and graphics devices                                                                                                |
| 2    | Object representation, lines and curves, surfaces                                                                                                                  |
| 3    | Transformations, viewing and projection, clipping, rendering, scan conversion                                                                                      |
| 4    | Colour models and display considerations                                                                                                                           |
| 5    | Visibility, back-face culling, Painter's algorithm, Z-buffers, triangle rasterisation, depth and attribute interpolation, transparency, solid-object rasterisation |
| 6    | Computer animation, texture mapping                                                                                                                                |
| 7    | Hierarchical modelling, scene graphs, fractals and procedural generation                                                                                           |
| 8    | Event-driven interaction, camera control, selection, picking, object manipulation, graphics software and GPUs                                                      |
| 9    | Ray tracing                                                                                                                                                        |

## Activities

| Activity | Contents                                                                                                                                                                                   | Location                                                                 |
| -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------ |
| 1.3      | Three short Pygame-CE demonstrations: framebuffer pixels, drawing primitives, and aliasing/supersampling                                                                                   | [`Resources/Activity 1.3/`](Computer-Graphics/Resources/Activity%201.3/) |
| 4.2      | Interactive lab with ten demos covering 2D/3D transformations, viewing, clipping, illumination, Z-buffering, scan conversion, colour models, display processing, and the graphics pipeline | [`Resources/Activity 4.2/`](Computer-Graphics/Resources/Activity%204.2/) |

Each activity has its own README, dependency file, and run instructions. The
Activity 4.2 application also includes lecture-aligned examples, step-by-step
algorithm modes, and tests for its graphics calculations.

## Requirements

- Python 3
- Dependencies listed separately in each activity's `requirements.txt`
- Pygame-CE and NumPy for the Python demonstrations

## Installation

Create an environment and install dependencies from the activity you plan to
run. For example, on macOS or Linux:

```bash
cd "Computer-Graphics/Resources/Activity 4.2"
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
```

On Windows, use `py` and activate the environment with
`.venv\Scripts\activate`.

## Usage

Run the Activity 4.2 interactive lab:

```bash
cd "Computer-Graphics/Resources/Activity 4.2"
python3 main.py
```

Run an Activity 1.3 demonstration from its directory:

```bash
cd "Computer-Graphics/Resources/Activity 1.3"
python3 01_framebuffer.py
# or: python3 02_primitives.py
# or: python3 03_aliasing.py
```

For setup details, controls, learning objectives, and Activity 4.2 test and
preview options, see the README in the corresponding activity directory.

## Web Resource and GitHub Pages

The root `index.html` is a searchable course site for the lecture PDFs, lab
activities, syllabus, and numerical question bank. The PDF files are served
directly; the Pygame-CE activities link to their source and guides and must be
run locally with Python.

The workflow in `.github/workflows/pages.yml` builds the static site, creates a
PDF sitemap, and deploys it to GitHub Pages on pushes to `main`. In the GitHub
repository settings, set **Pages → Build and deployment → Source** to **GitHub
Actions**. After pushing the repository and enabling Pages, the workflow
publishes the site URL in its deployment environment.
