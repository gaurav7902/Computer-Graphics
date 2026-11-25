"""Demo 10: From Objects to Pixels, the whole pipeline (Lecture 3.5, 'End of Unit 3').

One small scene (two cubes) is taken through every stage of Units 3 and 4,
reusing the modules the earlier demos use:

    1 object space  ->  2 model (world)  ->  3 view (camera)  ->  4 projection
    ->  5 clipping  ->  6 viewport mapping  ->  7 scan conversion
    ->  8 fragment colour  ->  9 visibility (Z-buffer) and framebuffer

Right / Space moves to the next stage, Left goes back.
"""

import numpy as np
import pygame

from core import theme
from core.demo import Demo, InfoSection, Mode
from core.draw_utils import draw_dashed_polygon, draw_filled_polygon, draw_legend, draw_marker, draw_text
from core.viewport import Viewport2D
from demos.scene3d import OrbitView
from graphics import camera as cam
from graphics import clipping
from graphics import lighting
from graphics import transforms3d as T3
from graphics.matrices import matrix_to_lines
from graphics.mesh import CUBE_EDGES, cube
from graphics.triangle_raster import FrameBuffer, rasterize_triangle

STAGES = [
    ("1. Object space", "The model's own coordinates: a cube centred on its own origin."),
    ("2. Model transformation", "P_w = M · P_o places each object in the shared world."),
    ("3. View transformation", "P_c = V · P_w measures every point from the camera."),
    ("4. Projection", "Q and the divide by w turn camera points into image-plane points."),
    ("5. Clipping", "Keep only what lies inside the window; trim what crosses it."),
    ("6. Viewport mapping", "Map the window onto the framebuffer's pixel rectangle."),
    ("7. Scan conversion", "Find the pixels each triangle covers: each one is a candidate fragment."),
    ("8. Fragment colour", "Light each fragment (here: one Phong evaluation per face)."),
    ("9. Visibility and framebuffer", "The Z-buffer keeps the nearest fragment; its colour is stored."),
]

FB_WIDTH, FB_HEIGHT = 64, 48                  # the low-resolution framebuffer
WINDOW = clipping.ClipWindow(-0.5, 0.5, -0.375, 0.375)   # image-plane window (4 : 3)
D = 1.0                                       # distance to the image plane
TRACKED = 6                                   # cube vertex (1, 1, 1) of object A


class Scene:
    """The two cubes, the camera and the light, plus everything computed from them."""

    def __init__(self):
        self.mesh = cube(2.0)                 # vertices at ±1
        self.angle = 30.0
        self.camera = cam.Camera(eye=(-2.0, 2.5, -4.0), target=(-0.3, 1.0, 0.8))
        self.light_dir = lighting.normalise([-0.4, 0.8, -0.5])
        self.material = lighting.Material(ka=0.25, kd=0.7, ks=0.35, n=16)
        self.compute()

    def model_matrices(self):
        a = T3.compose(T3.rotate_y(self.angle), T3.translate(0.0, 1.0, 0.0))
        b = T3.compose(T3.scale(0.9, 0.9, 0.9), T3.rotate_y(-25.0), T3.translate(3.2, 0.9, 2.0))
        return [("A (orange)", a, np.array([0.95, 0.55, 0.25])), ("B (blue)", b, np.array([0.35, 0.65, 0.95]))]

    def compute(self):
        """Run every stage once and keep the results for drawing."""
        V = self.camera.view_matrix()
        Q = cam.perspective_matrix(D)
        light = lighting.LightSettings(Ia=0.6, Il=1.0)
        self.objects, self.triangles = [], []
        for name, M, colour in self.model_matrices():
            world = T3.apply(M, self.mesh.vertices)
            camera_points = self.camera.world_to_camera(world)
            image, homogeneous = cam.project(camera_points, Q)
            self.objects.append({"name": name, "M": M, "colour": colour, "world": world,
                                 "camera": camera_points, "image": image, "homogeneous": homogeneous})
            for face in self.mesh.faces:
                a, b, c = world[face]
                normal = lighting.normalise(np.cross(b - a, c - a))
                to_eye = lighting.normalise(self.camera.eye - (a + b + c) / 3)
                amb, diff, spec = lighting.phong_terms(normal, self.light_dir, to_eye, self.material, light)
                shaded = np.clip((amb + diff) * colour + spec, 0, 1)
                self.triangles.append({"image": image[face], "depth": camera_points[face, 2], "colour": shaded})
        self.V, self.Q = V, Q

        # 5. Clipping: Sutherland-Hodgman on every projected triangle.
        for tri in self.triangles:
            tri["clipped"] = clipping.sutherland_hodgman([tuple(p) for p in tri["image"]], WINDOW)

        # 6. Viewport mapping: image window -> framebuffer pixels (y flipped).
        viewport = clipping.ClipWindow(0, FB_WIDTH, 0, FB_HEIGHT)
        for tri in self.triangles:
            tri["pixels"] = np.array([clipping.window_to_viewport(x, y, WINDOW, viewport) for x, y in tri["image"]])

        # 7-9. Rasterise three times: to count coverage, without and with the depth test.
        self.coverage = np.zeros((FB_HEIGHT, FB_WIDTH), dtype=int)
        self.painter = FrameBuffer(FB_WIDTH, FB_HEIGHT, background=(0.055, 0.07, 0.11))
        self.zbuffer = FrameBuffer(FB_WIDTH, FB_HEIGHT, background=(0.055, 0.07, 0.11))
        self.fragments = self.accepted = 0
        for tri in self.triangles:
            flat = lambda values, c=tri["colour"]: np.tile(c, (len(values), 1))
            report = rasterize_triangle(self.painter, tri["pixels"], tri["depth"], np.zeros((3, 1)), flat, depth_test=False)
            np.add.at(self.coverage, (report.rows, report.cols), 1)
            report = rasterize_triangle(self.zbuffer, tri["pixels"], tri["depth"], np.zeros((3, 1)), flat, depth_test=True)
            self.fragments += len(report.depth)
            self.accepted += int(report.accepted.sum())


class PipelineMode(Mode):
    name = "Stages 1 to 9"
    controls = [("Right / Space", "next stage"), ("Left", "back"), ("[ ]", "turn cube A"),
                ("Drag", "orbit (stages 1-3)"), ("D", "depth (stage 9)")]

    def __init__(self, demo):
        super().__init__(demo)
        canvas = demo.canvas_rect
        self.object_view = OrbitView(canvas, target=(0, 0, 0), distance=8)
        self.world_view = OrbitView(canvas, target=(0.5, 1.2, -0.8), distance=14, yaw=-65, pitch=28)
        image_rect = pygame.Rect(canvas.left + 20, canvas.top + 90, canvas.width - 40, (canvas.width - 40) * 3 // 4)
        # Show a little more than the window so geometry outside it is visible.
        self.image_view = Viewport2D(image_rect, units_tall=0.9, centre=(0.0, 0.0))
        self.reset()

    def reset(self):
        self.stage = 0
        self.show_depth = False
        self.scene = Scene()

    # -- Input -------------------------------------------------------------------

    def handle_event(self, event):
        if self.stage in (0, 1, 2):
            view = self.object_view if self.stage == 0 else self.world_view
            if view.handle_event(event):
                return True
        if event.type != pygame.KEYDOWN:
            return False
        if event.key in (pygame.K_RIGHT, pygame.K_SPACE):
            self.stage = min(len(STAGES) - 1, self.stage + 1)
        elif event.key == pygame.K_LEFT:
            self.stage = max(0, self.stage - 1)
        elif event.key in (pygame.K_LEFTBRACKET, pygame.K_RIGHTBRACKET):
            self.scene.angle += 15 if event.key == pygame.K_RIGHTBRACKET else -15
            self.scene.compute()
        elif event.key == pygame.K_d:
            self.show_depth = not self.show_depth
        else:
            return False
        return True

    # -- Drawing helpers ---------------------------------------------------------------

    def window_corners(self):
        return [(WINDOW.x_min, WINDOW.y_min), (WINDOW.x_max, WINDOW.y_min),
                (WINDOW.x_max, WINDOW.y_max), (WINDOW.x_min, WINDOW.y_max)]

    def pixel_rect(self, row, col):
        """Where framebuffer pixel (row, col) sits on the canvas, inside the window."""
        left, top = self.image_view.world_to_screen(WINDOW.x_min, WINDOW.y_max)
        right, bottom = self.image_view.world_to_screen(WINDOW.x_max, WINDOW.y_min)
        w, h = (right - left) / FB_WIDTH, (bottom - top) / FB_HEIGHT
        return pygame.Rect(round(left + col * w), round(top + row * h), round(left + (col + 1) * w) - round(left + col * w),
                           round(top + (row + 1) * h) - round(top + row * h))

    def draw_pixels(self, surface, colours):
        """Paint an H x W x 3 uint8 array as framebuffer pixels inside the window."""
        for row in range(FB_HEIGHT):
            for col in range(FB_WIDTH):
                pygame.draw.rect(surface, tuple(int(v) for v in colours[row, col]), self.pixel_rect(row, col))

    def draw_pixel_grid(self, surface):
        for col in range(FB_WIDTH + 1):
            x = self.pixel_rect(0, min(col, FB_WIDTH - 1)).left if col < FB_WIDTH else self.pixel_rect(0, FB_WIDTH - 1).right
            pygame.draw.line(surface, theme.GRID, (x, self.pixel_rect(0, 0).top), (x, self.pixel_rect(FB_HEIGHT - 1, 0).bottom))
        for row in range(FB_HEIGHT + 1):
            y = self.pixel_rect(min(row, FB_HEIGHT - 1), 0).top if row < FB_HEIGHT else self.pixel_rect(FB_HEIGHT - 1, 0).bottom
            pygame.draw.line(surface, theme.GRID, (self.pixel_rect(0, 0).left, y), (self.pixel_rect(0, FB_WIDTH - 1).right, y))

    def draw_image_plane(self, surface, clipped_only=False):
        view = self.image_view
        draw_filled_polygon(surface, view.points_to_screen(self.window_corners()), theme.YELLOW, fill_alpha=18, width=2)
        for tri, obj_colour in self.triangle_colours():
            points = view.points_to_screen(tri["image"])
            if not clipped_only:
                pygame.draw.polygon(surface, obj_colour, points, 1)
            else:
                draw_dashed_polygon(surface, points, theme.TEXT_FAINT, 4, 4)
                if len(tri["clipped"]) >= 3:
                    draw_filled_polygon(surface, view.points_to_screen(tri["clipped"]), obj_colour, fill_alpha=40, width=1)

    def triangle_colours(self):
        per_object = len(self.scene.mesh.faces)
        for i, tri in enumerate(self.scene.triangles):
            colour = tuple(int(c * 255) for c in self.scene.objects[i // per_object]["colour"])
            yield tri, colour

    def draw_camera(self, surface, view):
        """The camera: eye E, its r, u, f axes and the viewing frustum through the window."""
        c = self.scene.camera
        r, u, f = c.axes()
        reach = 3.0
        corners = [c.eye + reach * (x * r + y * u + D * f) for x, y in self.window_corners()]
        for corner in corners:
            view.draw_segment(surface, c.eye, corner, theme.YELLOW)
        for a, b in zip(corners, corners[1:] + corners[:1]):
            view.draw_segment(surface, a, b, theme.YELLOW, 2)
        for axis, colour, name in ((r, theme.RED, "r"), (u, theme.GREEN, "u"), (f, theme.BLUE, "f")):
            view.draw_segment(surface, c.eye, c.eye + 1.5 * axis, colour, 3)
            view.draw_point(surface, c.eye + 1.7 * axis, colour, name, radius=2)
        view.draw_point(surface, c.eye, theme.YELLOW, "E", radius=6)

    # -- Drawing -------------------------------------------------------------------------

    def draw(self, surface):
        s = self.scene
        stage = self.stage
        fonts = theme.fonts()
        title, explanation = STAGES[stage]
        canvas = self.demo.canvas_rect

        if stage == 0:
            view = self.object_view
            view.draw_floor_and_axes(surface, size=3)
            view.draw_edges(surface, s.mesh.vertices, CUBE_EDGES, theme.YELLOW, 3)
            view.draw_point(surface, s.mesh.vertices[TRACKED], theme.TEXT, "P_o (1, 1, 1)")
        elif stage in (1, 2):
            view = self.world_view
            view.draw_floor_and_axes(surface, size=6)
            for obj in s.objects:
                view.draw_edges(surface, obj["world"], CUBE_EDGES, tuple(int(c * 255) for c in obj["colour"]), 3)
            view.draw_point(surface, s.objects[0]["world"][TRACKED], theme.TEXT, "P_w")
            if stage == 2:
                self.draw_camera(surface, view)
        elif stage in (3, 4):
            self.image_view.draw_grid(surface, label_every=1)
            self.draw_image_plane(surface, clipped_only=(stage == 4))
            p = s.objects[0]["image"][TRACKED]
            draw_marker(surface, self.image_view.world_to_screen(*p), theme.TEXT, "P'")
        elif stage == 5:
            self.draw_pixel_grid(surface)
            for tri, colour in self.triangle_colours():
                points = [self.pixel_to_screen(px, py) for px, py in tri["pixels"]]
                pygame.draw.polygon(surface, colour, points, 1)
        elif stage == 6:
            heat = {0: theme.CANVAS, 1: (40, 92, 130), 2: (94, 190, 240), 3: (250, 206, 96)}
            colours = np.zeros((FB_HEIGHT, FB_WIDTH, 3), dtype=np.uint8)
            for count, colour in heat.items():
                colours[s.coverage == count] = colour
            colours[s.coverage >= 4] = theme.RED
            self.draw_pixels(surface, colours)
            self.draw_pixel_grid(surface)
            draw_legend(surface, canvas, [(heat[1], "1 fragment"), (heat[2], "2 fragments"), (heat[3], "3"),
                                          (theme.RED, "4 or more")], corner="right")
        elif stage == 7:
            self.draw_pixels(surface, s.painter.to_uint8())
        else:
            if self.show_depth:
                depth = s.zbuffer.depth
                finite = np.isfinite(depth)
                grey = np.full(depth.shape, 255.0)
                if finite.any():
                    lo, hi = depth[finite].min(), depth[finite].max()
                    grey[finite] = 40 + 180 * (depth[finite] - lo) / max(hi - lo, 1e-9)
                colours = np.repeat(grey[..., np.newaxis], 3, axis=2).astype(np.uint8)
            else:
                colours = s.zbuffer.to_uint8()
            self.draw_pixels(surface, colours)

        # Stage title strip and a progress bar of the nine stages.
        draw_text(surface, title, (canvas.left + 20, canvas.top + 14), theme.TEXT, fonts.heading)
        draw_text(surface, explanation, (canvas.left + 20, canvas.top + 38), theme.TEXT_DIM, fonts.small)
        for i in range(len(STAGES)):
            colour = theme.BLUE if i == stage else (theme.BUTTON_ACTIVE if i < stage else theme.BUTTON)
            pygame.draw.rect(surface, colour, (canvas.left + 20 + i * 72, canvas.bottom - 22, 66, 8), border_radius=4)

    def pixel_to_screen(self, px, py):
        """Continuous framebuffer coordinates (x right, y down) -> canvas pixels."""
        left, top = self.image_view.world_to_screen(WINDOW.x_min, WINDOW.y_max)
        right, bottom = self.image_view.world_to_screen(WINDOW.x_max, WINDOW.y_min)
        return (round(left + px / FB_WIDTH * (right - left)), round(top + py / FB_HEIGHT * (bottom - top)))

    # -- Info panel -------------------------------------------------------------------------

    def info_sections(self):
        s = self.scene
        a = s.objects[0]
        p_o = s.mesh.vertices[TRACKED]
        p_w = a["world"][TRACKED]
        p_c = a["camera"][TRACKED]
        h = a["homogeneous"][TRACKED]
        p_img = a["image"][TRACKED]
        fmt = T3.point_to_text
        stage = self.stage
        sections = [InfoSection(STAGES[stage][0], [STAGES[stage][1]])]

        if stage == 0:
            sections.append(InfoSection("Cube vertices (object space)", [fmt(v, 0) for v in s.mesh.vertices], mono=True))
        elif stage == 1:
            sections.append(InfoSection("M for cube A = T(0, 1, 0) · Ry(θ)", matrix_to_lines(a["M"]), mono=True))
            sections.append(InfoSection("Following one corner", [f"P_o = {fmt(p_o, 0)}", f"P_w = M · P_o = {fmt(p_w)}",
                                                                 (f"θ = {s.angle:g}°  (press [ or ])", theme.TEXT_DIM)]))
        elif stage == 2:
            sections.append(InfoSection("View matrix V", matrix_to_lines(s.V), mono=True))
            sections.append(InfoSection("Following one corner", [f"P_w = {fmt(p_w)}", f"P_c = V · P_w = {fmt(p_c)}",
                                                                 ("z > 0: in front of the camera", theme.GREEN)]))
        elif stage == 3:
            sections.append(InfoSection(f"Perspective Q (d = {D:g})", matrix_to_lines(s.Q), mono=True))
            sections.append(InfoSection("Following one corner", [f"P_c   = {fmt(p_c)}", f"Q·P_c = {fmt(h)}",
                                                                 f"÷ w   = ({p_img[0]:.3f}, {p_img[1]:.3f})"], mono=True))
        elif stage == 4:
            inside = sum(1 for t in s.triangles if all(clipping.clip_point(x, y, WINDOW) for x, y in t["image"]))
            rejected = sum(1 for t in s.triangles if len(t["clipped"]) < 3)
            sections.append(InfoSection("Sutherland–Hodgman on each triangle", [
                f"{len(s.triangles)} triangles: {inside} completely inside,",
                f"{rejected} completely outside, {len(s.triangles) - inside - rejected} trimmed",
                (f"window: {WINDOW.x_min} ≤ x' ≤ {WINDOW.x_max},  {WINDOW.y_min} ≤ y' ≤ {WINDOW.y_max}", theme.TEXT_DIM),
            ]))
        elif stage == 5:
            px, py = clipping.window_to_viewport(*p_img, WINDOW, clipping.ClipWindow(0, FB_WIDTH, 0, FB_HEIGHT))
            sections.append(InfoSection(f"Window -> {FB_WIDTH} × {FB_HEIGHT} framebuffer", [
                f"P' = ({p_img[0]:.3f}, {p_img[1]:.3f})",
                f"-> pixel coordinates ({px:.1f}, {py:.1f})",
                ("y is flipped: row 0 is the top of the image.", theme.TEXT_DIM),
            ]))
        elif stage == 6:
            covered = int((s.coverage > 0).sum())
            sections.append(InfoSection("Coverage", [
                f"{int(s.coverage.sum())} fragments over {covered} pixels",
                f"most fragments at one pixel: {int(s.coverage.max())}",
                ("Front and back faces both produce fragments, and cube A overlaps cube B. "
                 "Visibility is decided later, at stage 9.", theme.TEXT_DIM),
                ("The rasteriser only visits pixels inside the framebuffer, which is the same as the clipped region.",
                 theme.TEXT_DIM),
            ]))
        elif stage == 7:
            sections.append(InfoSection("Phong reflection, once per face", [
                f"ka = {s.material.ka}, kd = {s.material.kd}, ks = {s.material.ks}, n = {s.material.n:g}",
                ("Drawn in arrival order WITHOUT a depth test: back faces and the farther cube can be painted "
                 "over nearer surfaces. Look for wrong overlaps.", theme.RED),
            ]))
        else:
            sections.append(InfoSection("Z-buffer", [
                f"{s.fragments} fragments tested",
                f"{s.accepted} accepted (nearer than what was stored)",
                f"{s.fragments - s.accepted} discarded",
                (f"Showing: {'depth buffer (dark = near)' if self.show_depth else 'colour buffer'}  (press D)", theme.TEXT_DIM),
            ]))
            sections.append(InfoSection("Done", [("Every pixel of the framebuffer now holds the colour of the nearest "
                                                  "surface: the image is ready for the display (Lecture 4.1).", theme.GREEN)]))
        return sections


class PipelineWalkthroughDemo(Demo):
    title = "Objects to Pixels"
    lecture = "3.5"

    def setup(self, canvas_rect):
        super().setup(canvas_rect)
        self.modes = [PipelineMode(self)]
