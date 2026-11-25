"""Check every graphics/ module against the worked examples in Lectures 3.1–4.1.

Run from the Graphics Lab folder:
    python3 -m tests.test_graphics
"""

import colorsys

import numpy as np

from graphics import camera, clipping, colour, lighting, raster
from graphics import transforms3d as T3
from graphics.mesh import uv_sphere
from graphics.triangle_raster import FrameBuffer, rasterize_triangle

results = []


def check(name, got, expected, tolerance=1e-2):
    if isinstance(expected, str) or (isinstance(got, list) and not isinstance(got, np.ndarray)
                                     and got and isinstance(got[0], (str, tuple))):
        ok = got == expected          # exact comparison for text and lists of pixels
    else:
        ok = bool(np.allclose(np.asarray(got, dtype=float), np.asarray(expected, dtype=float), atol=tolerance))
    results.append(ok)
    print(f"{'PASS' if ok else 'FAIL'}  {name}")
    if not ok:
        print(f"      got      {got}\n      expected {expected}")


def lecture_3_1_3d():
    check("3.1  T(4,-1,2) moves (1,2,3) to (5,1,5)", T3.apply(T3.translate(4, -1, 2), [(1, 2, 3)])[0], (5, 1, 5))
    check("3.1  S(2,2,2) moves (1,1,1) to (2,2,2)", T3.apply(T3.scale(2, 2, 2), [(1, 1, 1)])[0], (2, 2, 2))
    check("3.1  Rz(60°) moves (3,0,2) to (1.5,2.598,2)", T3.apply(T3.rotate_z(60), [(3, 0, 2)])[0], (1.5, 2.598, 2))
    check("3.1  Rx(90°) moves (1,2,0) to (1,0,2)", T3.apply(T3.rotate_x(90), [(1, 2, 0)])[0], (1, 0, 2))
    check("3.1  Ry(90°) moves (0,2,1) to (1,2,0)", T3.apply(T3.rotate_y(90), [(0, 2, 1)])[0], (1, 2, 0))


def lecture_3_2():
    cam = camera.Camera(eye=(5, 2, 1), target=(5, 2, 10))
    r, u, f = cam.axes()
    check("3.2  aligned camera axes r, u, f", np.array([r, u, f]), np.eye(3))
    check("3.2  Pw (8,4,3) with E (5,2,1) gives Pc (3,2,2)", cam.world_to_camera([(8, 4, 3)])[0], (3, 2, 2))
    xy, _ = camera.project([(4, 2, 5), (4, 2, 10)], camera.orthographic_matrix())
    check("3.2  orthographic: (4,2,5) and (4,2,10) both give (4,2)", xy, [(4, 2), (4, 2)])
    xy, h = camera.project([(2, 1, 4)], camera.perspective_matrix(2))
    check("3.2  perspective Q gives (dx, dy, z, z)", h[0], (4, 2, 4, 4))
    check("3.2  perspective divide gives (dx/z, dy/z)", xy[0], (1.0, 0.5))


def lecture_3_3():
    window = clipping.ClipWindow(2, 8, 2, 6)
    check("3.3  outcode of (0,4) is 0001", clipping.code_text(clipping.outcode(0, 4, window)), "0001")
    check("3.3  outcode of (10,7) is 1010", clipping.code_text(clipping.outcode(10, 7, window)), "1010")
    steps = list(clipping.cohen_sutherland_steps((0, 4), (10, 7), window))
    check("3.3  first clip: P1 against Left gives A (2, 4.6)", steps[0]["point"], (2, 4.6))
    check("3.3  second clip: P2 against Top gives B (6.67, 6)", steps[1]["point"], (6.667, 6))
    check("3.3  then trivially accepted", [s["action"] for s in steps], ["clip", "clip", "accept"])
    check("3.3  trivial reject: both right of the window",
          clipping.cohen_sutherland((9, 3), (10, 5), window) is None, 1)
    triangle = [(0, 3), (6, 5), (5, 1)]
    clipped = clipping.sutherland_hodgman(triangle, clipping.ClipWindow(1, 8, 0, 8))
    check("3.3  Sutherland–Hodgman keeps every point inside the window",
          all(x >= 1 - 1e-9 for x, _ in clipped), 1)
    xs, ys = clipping.window_to_viewport(5, 4, window, clipping.ClipWindow(0, 600, 0, 400))
    check("3.3  window centre maps to viewport centre", (xs, ys), (300, 200))


def lecture_3_4():
    material = lighting.Material(ka=0.2, kd=0.6, ks=0.3, n=4)
    light = lighting.LightSettings(Ia=0.5, Il=1.0)
    terms = lighting.phong_from_dots(0.8, 0.9, material, light)
    check("3.4  worked example terms (0.10, 0.48, 0.197)", terms, (0.10, 0.48, 0.197), 1e-3)
    check("3.4  worked example total I ≈ 0.777", sum(terms), 0.777, 1e-3)
    N, L = np.array([0, 1, 0]), lighting.normalise([1, 1, 0])
    check("3.4  R is L mirrored about N", lighting.reflect(L, N), lighting.normalise([-1, 1, 0]))
    check("3.4  light behind the surface gives no diffuse light",
          lighting.phong_terms(N, -L, N, material, light)[1], 0.0)

    buffer = FrameBuffer(10, 10)
    red = lambda values: np.tile([1.0, 0, 0], (len(values), 1))
    blue = lambda values: np.tile([0, 0, 1.0], (len(values), 1))
    square = [(0, 0), (10, 0), (0, 10)]
    rasterize_triangle(buffer, square, [0.6] * 3, np.zeros((3, 1)), blue)
    rasterize_triangle(buffer, square, [0.35] * 3, np.zeros((3, 1)), red)
    report = rasterize_triangle(buffer, square, [0.8] * 3, np.zeros((3, 1)), blue)
    check("3.4  Z-buffer: blue 0.60, red 0.35 accepted, green 0.80 discarded",
          [*buffer.colour[1, 1], buffer.depth[1, 1], report.accepted.any()], [1, 0, 0, 0.35, 0])
    sphere = uv_sphere(stacks=6, slices=8)
    centres = sphere.vertices[sphere.faces].mean(axis=1)
    check("3.4  sphere faces all point outward",
          np.all(np.sum(sphere.face_normals() * centres, axis=1) > 0), 1)


def lecture_3_5():
    dda = [(s["px"], s["py"]) for s in raster.dda_line(2, 2, 7, 5)]
    check("3.5  DDA (2,2)→(7,5)", dda, [(2, 2), (3, 3), (4, 3), (5, 4), (6, 4), (7, 5)])
    steps = list(raster.bresenham_line(2, 2, 9, 6))
    check("3.5  Bresenham decision values 1,-5,3,-3,5,-1,7", [s["p"] for s in steps[1:]], [1, -5, 3, -3, 5, -1, 7])
    check("3.5  Bresenham pixels (2,2)→(9,6)", [(s["x"], s["y"]) for s in steps],
          [(2, 2), (3, 3), (4, 3), (5, 4), (6, 4), (7, 5), (8, 5), (9, 6)])
    reverse = [(s["x"], s["y"]) for s in raster.bresenham_line(9, 6, 2, 2)]
    check("3.5  Bresenham works right-to-left too", len(reverse) == 8 and reverse[-1] == (2, 2), 1)
    steep = [(s["x"], s["y"]) for s in raster.bresenham_line(0, 0, 2, 6)]
    check("3.5  Bresenham y-major line has one pixel per row", [y for _, y in steep], list(range(7)))
    circle = list(raster.midpoint_circle(5))
    check("3.5  midpoint circle R=5 points", [(s["x"], s["y"]) for s in circle], [(0, 5), (1, 5), (2, 5), (3, 4)])
    check("3.5  midpoint circle decisions -4,-1,4,3", [s["p"] for s in circle], [-4, -1, 4, 3])
    check("3.5  eight-way symmetry of (3,4)", len(raster.eight_way_symmetry(3, 4)), 8)
    u_shape = [(2, 1), (11, 1), (11, 9), (8, 9), (8, 4), (5, 4), (5, 9), (2, 9)]
    check("3.5  scan line y=6 crosses at 2, 5, 8, 11", raster.scanline_crossings(u_shape, 6), [2, 5, 8, 11])
    row = next(r for r in raster.scanline_fill(u_shape) if r["y"] == 6)
    check("3.5  spans [2,5] and [8,11]", row["spans"], [(2, 5), (8, 11)])


def lecture_4_1():
    check("4.1  (1.0, 0.5, 0.0) → (255, 128, 0)", colour.to_8bit(1.0, 0.5, 0.0), (255, 128, 0))
    check("4.1  hex #FF8000", colour.to_hex(1.0, 0.5, 0.0), "#FF8000")
    check("4.1  RGB (0.23,0.68,0.85) → HSV (196.5°, 0.729, 0.850)",
          colour.rgb_to_hsv(0.23, 0.68, 0.85), (196.5, 0.729, 0.850), 0.05)   # the slide rounds 196.45° to 196.5°
    check("4.1  RGB (0.23,0.68,0.85) → HSL (196.5°, 0.674, 0.540)",
          colour.rgb_to_hsl(0.23, 0.68, 0.85), (196.5, 0.674, 0.540), 0.05)
    check("4.1  CMY (0.7,0.5,0.6) → CMYK (0.2,0,0.1,0.5)", colour.cmy_to_cmyk(0.7, 0.5, 0.6), (0.2, 0.0, 0.1, 0.5))
    check("4.1  V = 0.5, γ = 2.2 → I ≈ 0.22", colour.display_response(0.5, 2.2), 0.22, 5e-3)
    check("4.1  to get I = 0.5 send V ≈ 0.73", colour.gamma_encode(0.5, 2.2), 0.73, 5e-3)
    check("4.1  clamp (-0.15, 0.72, 1.18)", colour.clamp(np.array([-0.15, 0.72, 1.18])), (0, 0.72, 1))
    check("4.1  0.72 × 255 = 183.6 ≈ 184", colour.quantise(0.72, 8) * 255, 184)

    rng = np.random.default_rng(1)
    agree = True
    for r, g, b in rng.random((200, 3)):
        h, s, v = colour.rgb_to_hsv(r, g, b)
        h2, s2, v2 = colorsys.rgb_to_hsv(r, g, b)
        hl, sl, ll = colour.rgb_to_hsl(r, g, b)
        h3, l3, s3 = colorsys.rgb_to_hls(r, g, b)
        agree &= np.allclose([h / 360, s, v], [h2, s2, v2]) and np.allclose([hl / 360, sl, ll], [h3, s3, l3])
        agree &= np.allclose(colour.hsv_to_rgb(h, s, v), (r, g, b))
        agree &= np.allclose(colour.hsl_to_rgb(hl, sl, ll), (r, g, b))
    check("4.1  HSV/HSL agree with Python's colorsys (200 random colours)", agree, 1)
    hsv = rng.random((50, 3)) * np.array([360, 1, 1])
    vector = colour.hsv_to_rgb_array(hsv[:, 0], hsv[:, 1], hsv[:, 2])
    scalar = [colour.hsv_to_rgb(*row) for row in hsv]
    check("4.1  hsv_to_rgb_array matches hsv_to_rgb", vector, scalar, 1e-9)

    flat = np.full((8, 8), 0.5)
    check("4.1  ordered dithering keeps the average of a 0.5 patch (1 bit)",
          colour.ordered_dither(flat, 1).mean(), 0.5)
    check("4.1  error diffusion keeps the average of a 0.5 patch (1 bit)",
          colour.error_diffusion_dither(flat, 1).mean(), 0.5, 0.05)


def main():
    for section in (lecture_3_1_3d, lecture_3_2, lecture_3_3, lecture_3_4, lecture_3_5, lecture_4_1):
        section()
    print(f"\n{sum(results)} of {len(results)} checks passed")


if __name__ == "__main__":
    main()
