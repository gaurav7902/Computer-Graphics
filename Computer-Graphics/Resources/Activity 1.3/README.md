# Activity 1.3: Pygame Rendering

This project gives you three short Pygame-CE demonstrations for showing how descriptions of objects become pixels on a raster display.

Use the examples in this order:

1. `01_framebuffer.py`
2. `02_primitives.py`
3. `03_aliasing.py`

## Setup

Windows:

```powershell
py -m venv .venv
.venv\Scripts\activate
py -m pip install -r requirements.txt
```

macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
```

Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
```

## Run

Windows:

```powershell
py 01_framebuffer.py
py 02_primitives.py
py 03_aliasing.py
```

macOS and Linux:

```bash
python3 01_framebuffer.py
python3 02_primitives.py
python3 03_aliasing.py
```

## Learning Objectives

`01_framebuffer.py`: You calculate RGB values in a NumPy framebuffer with shape `(HEIGHT, WIDTH, 3)` and type `np.uint8`. The code deliberately uses `framebuffer[y, x]` so you can connect pixel addresses to row-column array indexing. Pygame only presents the completed framebuffer.

`02_primitives.py`: You supply drawing primitives and their properties to Pygame. Pygame rasterises each point, line, rectangle, circle, ellipse, polygon and arc into discrete pixels on the display surface.

`03_aliasing.py`: You compare aliased rendering with supersampled anti-aliasing. The right panel first renders the same geometry on a larger off-screen surface, then uses `pygame.transform.smoothscale()` to estimate intermediate edge colours. This smooths boundaries; it does not increase the actual display resolution.

## Controls

`01_framebuffer.py`

- `Escape`: close the program
- Window close button: close the program

`02_primitives.py`

- `G`: show or hide the coordinate grid
- `Escape`: close the program
- Window close button: close the program

`03_aliasing.py`

- `G`: show or hide the magnified pixel grids
- `A`: switch between split comparison and full-width alternating view
- `1`, `2`, `4`, `8`: change the supersampling factor
- `Escape`: close the program
- Window close button: close the program

## Important Code Sections

In `01_framebuffer.py`, start with `framebuffer = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)`, then step through `set_pixel()`, `world_to_screen()`, `draw_axes()` and `framebuffer_to_surface()`. The transpose in `framebuffer_to_surface()` is there because NumPy image arrays are addressed as `[y, x]`, while Pygame surface arrays are arranged as `[x, y]`.

In `02_primitives.py`, focus on `draw_primitives()`. The `pygame.draw.*` calls are grouped in one place so you can point to each primitive description and then look at the pixels it produces.

In `03_aliasing.py`, compare `render_geometry_surface(size, 1)` with `render_geometry_surface(size, supersampling_factor)`. The geometry is the same; only the sampling method changes. The magnified insets show that aliasing abruptly selects pixels, while anti-aliasing blends colours near edges to approximate partial coverage.

## Frame Rate And Refresh Rate

Each example uses `clock.tick(60)` to limit the program's frame rate. That means the rendering loop aims to produce no more than about 60 frames per second. It does not set the physical display's refresh rate. Refresh rate belongs to the display device; frame rate belongs to the rendering program.

## Suggested 20-30 Minute Demonstration Flow

1. Spend 5-7 minutes on `01_framebuffer.py`. Show the framebuffer shape, RGB values, `[y, x]` indexing and the world-to-screen mapping.
2. Spend 6-8 minutes on `02_primitives.py`. Toggle the grid, then walk through the visible `pygame.draw` calls.
3. Spend 8-10 minutes on `03_aliasing.py`. Compare the split panels, zoom into the diagonal line, and change supersampling with `1`, `2`, `4` and `8`.
4. Use the final 3-5 minutes for questions and quick predictions before changing code values live.

## Questions To Ask

- Which part of the code describes the world, and which part stores pixels?
- Why does the screen y-coordinate decrease when world y increases?
- What changes when you draw an outlined shape instead of a filled shape?
- Where do you see evidence that a line or circle occupies discrete pixels?
- Does anti-aliasing create more display pixels, or does it choose better colours for the pixels already present?
- What visual change do you expect when the supersampling factor changes from `1` to `8`?

## Preview Screenshots

The `previews/` folder contains one rendered screenshot from each demonstration. They were generated with the same scripts using the `--preview` option.
