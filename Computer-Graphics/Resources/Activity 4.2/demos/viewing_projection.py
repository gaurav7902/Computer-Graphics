"""Demo 3: Viewing and Projection (Lecture 3.2).

    CameraFrameMode   place a camera (eye E, target C, up a), build r, u, f and
                      the view matrix V, and follow one world point into camera space
    ProjectionMode    compare orthographic and perspective projection, with the
                      side view of the projection rays and the resulting image
"""

import math

import numpy as np
import pygame

from core import theme
from core.demo import Demo, InfoSection, Mode
from core.draw_utils import draw_arrow, draw_dashed_line, draw_legend, draw_marker, draw_text
from core.viewport import Viewport2D
from graphics import camera as cam
from graphics.matrices import matrix_to_lines
from graphics.mesh import CUBE_EDGES
from graphics.transforms3d import point_to_text


def box_corners(centre, size):
    """The 8 corners of an axis-aligned box, in the same order as CUBE_EDGES expects."""
    cx, cy, cz = centre
    s = size / 2
    return np.array([
        (cx - s, cy - s, cz - s), (cx + s, cy - s, cz - s), (cx + s, cy + s, cz - s), (cx - s, cy + s, cz - s),
        (cx - s, cy - s, cz + s), (cx + s, cy - s, cz + s), (cx + s, cy + s, cz + s), (cx - s, cy + s, cz + s),
    ])


def clip_to_near_plane(a, b, near=0.1):
    """Keep only the part of a camera-space segment with z >= near.

    Perspective division needs z > 0, so geometry behind the camera must be
    removed first. This is the 'Near' plane of the view volume (Lecture 3.3).
    """
    a, b = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    if a[2] < near and b[2] < near:
        return None
    if a[2] < near or b[2] < near:
        t = (near - a[2]) / (b[2] - a[2])
        crossing = a + t * (b - a)
        a, b = (crossing, b) if a[2] < near else (a, crossing)
    return a, b


class CameraImage:
    """Draws camera-space line segments as the camera would see them, inside a rect."""

    def __init__(self, rect):
        self.rect = pygame.Rect(rect)

    def to_screen(self, image_xy, half_width):
        """Map image coordinates (x', y') in [-half_width, half_width] to pixels."""
        half_height = half_width * self.rect.height / self.rect.width
        sx = self.rect.centerx + image_xy[0] / half_width * self.rect.width / 2
        sy = self.rect.centery - image_xy[1] / half_height * self.rect.height / 2
        return round(sx), round(sy)

    def draw_segments(self, surface, segments, projection, half_width, colour, width=2):
        for a, b in segments:
            clipped = clip_to_near_plane(a, b)
            if clipped is None:
                continue
            xy, _ = cam.project(np.array(clipped), projection)
            pygame.draw.line(surface, colour, self.to_screen(xy[0], half_width),
                             self.to_screen(xy[1], half_width), width)

    def draw_point(self, surface, point, projection, half_width, colour, label):
        if point[2] <= 0.1:
            return
        xy, _ = cam.project(np.array([point]), projection)
        draw_marker(surface, self.to_screen(xy[0], half_width), colour, label)

    def draw_frame(self, surface, title):
        pygame.draw.rect(surface, theme.BACKGROUND, self.rect)
        pygame.draw.rect(surface, theme.PANEL_BORDER, self.rect, 1)
        pygame.draw.line(surface, theme.GRID, (self.rect.centerx, self.rect.top), (self.rect.centerx, self.rect.bottom))
        pygame.draw.line(surface, theme.GRID, (self.rect.left, self.rect.centery), (self.rect.right, self.rect.centery))
        draw_text(surface, title, (self.rect.left + 8, self.rect.top + 6), theme.TEXT_DIM, theme.fonts().small)


# ===========================================================================
# Mode 1: the camera frame and the view matrix
# ===========================================================================

class CameraFrameMode(Mode):
    name = "Camera and view matrix"
    controls = [
        ("Drag", "move E or C"),
        ("Left/Right", "turn"),
        ("Up/Down", "move"),
        ("[ ]", "eye height"),
    ]

    # A few boxes in the world: (centre, size, colour).
    BOXES = [((8.0, 1.0, 7.0), 2.0, theme.GREEN), ((3.0, 1.5, 10.0), 3.0, theme.PURPLE),
             ((11.0, 1.0, 13.0), 2.0, theme.RED)]
    POINT = np.array([8.0, 4.0, 3.0])     # Pw from the lecture example

    def __init__(self, demo):
        super().__init__(demo)
        canvas = demo.canvas_rect
        # Top-down map: world x to the right, world z up the screen.
        self.map = Viewport2D(canvas, units_tall=22, centre=(6.0, 7.0))
        self.inset = CameraImage((canvas.right - 292, canvas.top + 12, 280, 210))
        self.reset()

    def reset(self):
        # The lecture example: E = (5, 2, 1) with axes aligned to the world.
        self.camera = cam.Camera(eye=(5.0, 2.0, 1.0), target=(5.0, 2.0, 8.0), up=(0.0, 1.0, 0.0))
        self.dragging = None

    # -- Input ---------------------------------------------------------------------

    def map_position(self, point3d):
        return self.map.world_to_screen(point3d[0], point3d[2])

    def handle_event(self, event):
        c = self.camera
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and not self.inset.rect.collidepoint(event.pos):
            for name, point in (("eye", c.eye), ("target", c.target)):
                px, py = self.map_position(point)
                if math.hypot(event.pos[0] - px, event.pos[1] - py) < 14:
                    self.dragging = name
                    return True
        elif event.type == pygame.MOUSEBUTTONUP:
            self.dragging = None
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            x, z = self.map.screen_to_world(*event.pos)
            point = c.eye if self.dragging == "eye" else c.target
            moved = np.array([round(x * 2) / 2, point[1], round(z * 2) / 2])
            other = c.target if self.dragging == "eye" else c.eye
            if np.linalg.norm((moved - other)[[0, 2]]) > 0.5:      # keep E and C apart
                point[:] = moved
            return True
        elif event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_LEFT, pygame.K_RIGHT):
                self.turn(-10 if event.key == pygame.K_LEFT else 10)
            elif event.key in (pygame.K_UP, pygame.K_DOWN):
                _, _, f = c.axes()
                step = f * (0.5 if event.key == pygame.K_UP else -0.5)
                c.eye += step
                c.target += step
            elif event.key in (pygame.K_LEFTBRACKET, pygame.K_RIGHTBRACKET):
                c.eye[1] += 0.5 if event.key == pygame.K_RIGHTBRACKET else -0.5
            else:
                return False
            return True
        return False

    def turn(self, degrees):
        """Swing the target around the eye in the horizontal (x, z) plane."""
        c = self.camera
        offset = c.target - c.eye
        a = math.radians(degrees)
        x, z = offset[0], offset[2]
        offset[0], offset[2] = x * math.cos(a) + z * math.sin(a), -x * math.sin(a) + z * math.cos(a)
        c.target = c.eye + offset

    # -- Drawing -------------------------------------------------------------------

    def world_segments(self):
        segments = []
        for centre, size, colour in self.BOXES:
            corners = box_corners(centre, size)
            segments.append((colour, [(corners[i], corners[j]) for i, j in CUBE_EDGES]))
        return segments

    def draw(self, surface):
        c = self.camera
        self.map.draw_grid(surface)
        draw_text(surface, "Top-down view of the world (x to the right, z up)", (self.map.rect.left + 12, self.map.rect.top + 10),
                  theme.TEXT_DIM, theme.fonts().small)

        # The boxes' footprints on the map.
        for centre, size, colour in self.BOXES:
            corners = box_corners(centre, size)[[0, 1, 5, 4]]
            pygame.draw.polygon(surface, colour, [self.map_position(p) for p in corners], 2)

        # Field of view: two rays either side of the forward direction.
        r, u, f = c.axes()
        eye_px = self.map_position(c.eye)
        for side in (-1, 1):
            direction = f + side * math.tan(math.radians(25)) * r
            far = c.eye + direction * 20
            draw_dashed_line(surface, eye_px, self.map_position(far), theme.TEXT_FAINT)

        # The camera axes r and f, drawn 2 units long.
        draw_arrow(surface, eye_px, self.map_position(c.eye + 2 * r), theme.RED, 3)
        draw_arrow(surface, eye_px, self.map_position(c.eye + 2 * f), theme.BLUE, 3)
        draw_text(surface, "r", self.map_position(c.eye + 2.4 * r), theme.RED, theme.fonts().body, centre=True)
        draw_text(surface, "f", self.map_position(c.eye + 2.4 * f), theme.BLUE, theme.fonts().body, centre=True)

        draw_marker(surface, eye_px, theme.YELLOW, "E (eye)", radius=7)
        draw_marker(surface, self.map_position(c.target), theme.GREEN, "C (target)", radius=7)

        # The tracked world point and the displacement d = Pw - E.
        point_px = self.map_position(self.POINT)
        draw_dashed_line(surface, eye_px, point_px, theme.TEXT_DIM)
        draw_marker(surface, point_px, theme.TEXT, "Pw")

        # What the camera sees.
        self.inset.draw_frame(surface, "Camera view (perspective, d = 1)")
        projection = cam.perspective_matrix(1.0)
        previous_clip = surface.get_clip()
        surface.set_clip(self.inset.rect.inflate(-2, -2))
        for colour, segments in self.world_segments():
            camera_segments = [tuple(c.world_to_camera(np.array(seg))) for seg in segments]
            self.inset.draw_segments(surface, camera_segments, projection, 0.6, colour)
        self.inset.draw_point(surface, c.world_to_camera([self.POINT])[0], projection, 0.6, theme.TEXT, "Pw")
        surface.set_clip(previous_clip)

        draw_legend(surface, self.map.rect, [(theme.RED, "r: camera right"), (theme.BLUE, "f: camera forward"),
                                             (theme.TEXT_FAINT, "field of view")])

    def info_sections(self):
        c = self.camera
        r, u, f = c.axes()
        d = self.POINT - c.eye
        pc = c.world_to_camera([self.POINT])[0]
        fmt = lambda v: point_to_text(v, 2)
        return [
            InfoSection("Camera", [f"E = {fmt(c.eye)}", f"C = {fmt(c.target)}", f"a = {fmt(c.up)}  (approximate up)"]),
            InfoSection("Camera axes", [
                (f"f = (C - E) / |C - E| = {fmt(f)}", theme.BLUE),
                (f"r = (a × f) / |a × f| = {fmt(r)}", theme.RED),
                (f"u = f × r = {fmt(u)}", theme.GREEN),
            ]),
            InfoSection("View matrix V  (each axis is one row)", matrix_to_lines(c.view_matrix()), mono=True),
            InfoSection("Following Pw into camera space", [
                f"Pw = {fmt(self.POINT)}",
                f"d = Pw - E = {fmt(d)}",
                f"Pc = (r·d, u·d, f·d) = {fmt(pc)}",
                (("In front of the camera (z > 0)" if pc[2] > 0 else "Behind the camera (z <= 0): not visible"),
                 theme.GREEN if pc[2] > 0 else theme.RED),
            ]),
        ]


# ===========================================================================
# Mode 2: orthographic versus perspective projection
# ===========================================================================

class ProjectionMode(Mode):
    name = "Projection"
    controls = [
        ("Space", "orthographic / perspective"),
        ("Left/Right", "change d"),
        ("Up/Down", "move far post"),
    ]

    def __init__(self, demo):
        super().__init__(demo)
        canvas = demo.canvas_rect
        # Top: side view of camera space (z to the right, y up). Bottom: the image.
        side_rect = pygame.Rect(canvas.left, canvas.top + 34, canvas.width, 300)
        self.side = Viewport2D(side_rect, units_tall=21 * side_rect.height / side_rect.width, centre=(9.5, 0.0))
        self.image = CameraImage((canvas.left + 24, side_rect.bottom + 30, 400, 280))
        self.reset()

    def reset(self):
        self.perspective = True
        self.d = 2.0
        self.far_z = 10.0

    def posts(self):
        """Equal vertical posts on both sides of the view, in camera space.

        The tops of the right-hand posts at z = 5 and z = far_z are the
        lecture's points P1 = (4, 2, 5) and P2 = (4, 2, 10).
        """
        depths = [5.0, self.far_z, self.far_z + 5]
        return [((x, -2.0, z), (x, 2.0, z)) for z in depths for x in (-4.0, 4.0)]

    def rails(self):
        """Lines along the viewing direction. In perspective they meet at a vanishing point."""
        return [((x, y, 5.0), (x, y, 40.0)) for x in (-4.0, 4.0) for y in (-2.0, 2.0)]

    def projection(self):
        return cam.perspective_matrix(self.d) if self.perspective else cam.orthographic_matrix()

    def half_width(self):
        return 1.2 * self.d if self.perspective else 6.0

    def tracked_points(self):
        return {"P1": np.array([4.0, 2.0, 5.0]), "P2": np.array([4.0, 2.0, self.far_z])}

    def handle_event(self, event):
        if event.type != pygame.KEYDOWN:
            return False
        if event.key == pygame.K_SPACE:
            self.perspective = not self.perspective
        elif event.key in (pygame.K_LEFT, pygame.K_RIGHT):
            self.d = min(4.5, max(0.5, self.d + (0.5 if event.key == pygame.K_RIGHT else -0.5)))
        elif event.key in (pygame.K_UP, pygame.K_DOWN):
            self.far_z = min(14.0, max(6.0, self.far_z + (1.0 if event.key == pygame.K_UP else -1.0)))
        else:
            return False
        return True

    def draw(self, surface):
        side = self.side
        fonts = theme.fonts()
        kind = "Perspective" if self.perspective else "Orthographic"
        side.draw_grid(surface)
        draw_text(surface, "Side view of camera space (z to the right, y up)", (side.rect.left + 12, side.rect.top - 26),
                  theme.TEXT_DIM, fonts.small)

        # Camera at the origin and the image plane.
        origin = side.world_to_screen(0, 0)
        plane_z = self.d if self.perspective else 1.0
        top, bottom = side.world_to_screen(plane_z, 4.0), side.world_to_screen(plane_z, -4.0)
        pygame.draw.line(surface, theme.YELLOW, top, bottom, 2)
        draw_text(surface, f"image plane z = {plane_z:g}", (top[0] + 4, top[1] + 2), theme.YELLOW, fonts.small)
        draw_marker(surface, origin, theme.TEXT, "O", radius=6)

        # The posts seen from the side, and a projection ray from each top.
        for z in sorted({p[0][2] for p in self.posts()}):
            pygame.draw.line(surface, theme.GREEN, side.world_to_screen(z, -2), side.world_to_screen(z, 2), 4)
        for name, p in self.tracked_points().items():
            tip = side.world_to_screen(p[2], p[1])
            if self.perspective:
                y_on_plane = self.d * p[1] / p[2]        # similar triangles: y' = d·y / z
                hit = side.world_to_screen(self.d, y_on_plane)
                pygame.draw.line(surface, theme.BLUE, tip, origin, 1)
            else:
                hit = side.world_to_screen(plane_z, p[1])  # parallel ray, perpendicular to the plane
                pygame.draw.line(surface, theme.BLUE, tip, hit, 1)
            draw_marker(surface, tip, theme.TEXT, name)
            pygame.draw.circle(surface, theme.BLUE, hit, 5)

        # The image the camera produces.
        self.image.draw_frame(surface, f"{kind} image")
        previous_clip = surface.get_clip()
        surface.set_clip(self.image.rect.inflate(-2, -2))
        self.image.draw_segments(surface, self.rails(), self.projection(), self.half_width(), theme.TEXT_FAINT, 1)
        self.image.draw_segments(surface, self.posts(), self.projection(), self.half_width(), theme.GREEN, 3)
        # If both points land in the same place (orthographic), label them together.
        p1, p2 = self.tracked_points().values()
        same = np.allclose(cam.project(np.array([p1, p2]), self.projection())[0][0],
                           cam.project(np.array([p1, p2]), self.projection())[0][1])
        self.image.draw_point(surface, p1, self.projection(), self.half_width(), theme.BLUE, "P1 = P2" if same else "P1")
        if not same:
            self.image.draw_point(surface, p2, self.projection(), self.half_width(), theme.BLUE, "P2")
        surface.set_clip(previous_clip)

        notes = ["Green posts: all the same height (4),", f"standing at z = 5, {self.far_z:g} and {self.far_z + 5:g}.",
                 "", "Grey lines run straight away", "from the camera, along z.", "",
                 "Blue dots: where P1 and P2", "land on the image."]
        for i, line in enumerate(notes):
            draw_text(surface, line, (self.image.rect.right + 20, self.image.rect.top + 8 + i * 20),
                      theme.TEXT_DIM, fonts.small)

        draw_legend(surface, side.rect, [(theme.GREEN, "posts"), (theme.YELLOW, "image plane"),
                                         (theme.BLUE, "projection rays")], corner="right")

    def info_sections(self):
        q = self.projection()
        kind = "Perspective" if self.perspective else "Orthographic"
        lines = []
        for name, p in self.tracked_points().items():
            xy, h = cam.project(np.array([p]), q)
            lines.append(f"{name} = {point_to_text(p, 0)}")
            lines.append(f"  Q·P = {point_to_text(h[0], 2)}")
            lines.append((f"  ÷w  -> (x', y') = {point_to_text(xy[0], 2)}", theme.BLUE))
        if self.perspective:
            rule = [f"x' = d·x / z,  y' = d·y / z   (d = {self.d:g})",
                    ("Farther away -> smaller. The rails meet at a vanishing point.", theme.TEXT_DIM)]
            heading = f"Q with d = {self.d:g}, then divide by w = z"
        else:
            rule = ["x' = x,  y' = y   (z is simply dropped)",
                    ("Depth does not change size. Rails along z collapse to points.", theme.TEXT_DIM)]
            heading = "Matrix (w stays 1: dividing changes nothing)"
        return [
            InfoSection(f"{kind} projection", rule),
            InfoSection(heading, matrix_to_lines(q), mono=True),
            InfoSection("The two lecture points", lines, mono=True),
        ]


class ViewingProjectionDemo(Demo):
    title = "Viewing and Projection"
    lecture = "3.2"

    def setup(self, canvas_rect):
        super().setup(canvas_rect)
        self.modes = [CameraFrameMode(self), ProjectionMode(self)]
