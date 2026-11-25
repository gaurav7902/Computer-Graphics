"""Demo 4: Clipping (Lecture 3.3).

    PointClippingMode     click to add points; each one is kept or discarded
    CohenSutherlandMode   outcodes, trivial accept/reject and step-by-step line clipping
    SutherlandHodgmanMode clip a polygon against one window boundary at a time
    ViewportMappingMode   map the clipping window onto a viewport on the screen

The window is the lecture's example: 2 <= x <= 8 and 2 <= y <= 6.
"""

import math

import pygame

from core import theme
from core.demo import Demo, InfoSection, Mode
from core.draw_utils import draw_dashed_line, draw_dashed_polygon, draw_filled_polygon, draw_legend, draw_marker, draw_text
from core.stepper import StepPlayer
from core.viewport import Viewport2D
from graphics import clipping as C

WINDOW = C.ClipWindow(2.0, 8.0, 2.0, 6.0)
STEP_CONTROLS = [("Space", "step"), ("P", "play/pause"), ("Enter", "run to end")]


def draw_window(surface, view, window=WINDOW, extend=True):
    """The clipping window, plus its four boundaries extended across the canvas."""
    if extend:
        for x in (window.x_min, window.x_max):
            draw_dashed_line(surface, view.world_to_screen(x, view.y_min), view.world_to_screen(x, view.y_max), theme.TEXT_FAINT)
        for y in (window.y_min, window.y_max):
            draw_dashed_line(surface, view.world_to_screen(view.x_min, y), view.world_to_screen(view.x_max, y), theme.TEXT_FAINT)
    corners = [(window.x_min, window.y_min), (window.x_max, window.y_min),
               (window.x_max, window.y_max), (window.x_min, window.y_max)]
    draw_filled_polygon(surface, view.points_to_screen(corners), theme.YELLOW, fill_alpha=25, width=2)


def nearest(points, position, view, radius=14):
    """Index of the point closest to a mouse position, if it is within radius pixels."""
    best, best_distance = None, radius
    for i, p in enumerate(points):
        sx, sy = view.world_to_screen(*p)
        distance = math.hypot(position[0] - sx, position[1] - sy)
        if distance < best_distance:
            best, best_distance = i, distance
    return best


def snap(view, position):
    x, y = view.screen_to_world(*position)
    return (round(x * 2) / 2, round(y * 2) / 2)


def fmt(p):
    return f"({p[0]:.2f}, {p[1]:.2f})"


# ===========================================================================
# Mode 1: point clipping
# ===========================================================================

class PointClippingMode(Mode):
    name = "Points"
    controls = [("Click", "add a point")]

    def __init__(self, demo):
        super().__init__(demo)
        self.reset()

    def reset(self):
        # P3 lies exactly on x_min, as on the slide: boundary points are inside.
        self.points = [(4.0, 4.5), (2.0, 3.0), (9.5, 5.0), (5.0, 7.0)]

    def handle_event(self, event):
        view = self.demo.view
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and view.contains_pixel(event.pos):
            self.points.append(snap(view, event.pos))
            return True
        return False

    def draw(self, surface):
        view = self.demo.view
        view.draw_grid(surface)
        draw_window(surface, view, extend=False)
        for i, (x, y) in enumerate(self.points, start=1):
            kept = C.clip_point(x, y, WINDOW)
            draw_marker(surface, view.world_to_screen(x, y), theme.GREEN if kept else theme.RED, f"P{i}", radius=6)
        draw_legend(surface, view.rect, [(theme.GREEN, "kept (inside)"), (theme.RED, "discarded (outside)")])

    def info_sections(self):
        x, y = self.points[-1] if self.points else (0, 0)
        tests = [
            (f"x_min <= x :  {WINDOW.x_min:g} <= {x:g}", WINDOW.x_min <= x),
            (f"x <= x_max :  {x:g} <= {WINDOW.x_max:g}", x <= WINDOW.x_max),
            (f"y_min <= y :  {WINDOW.y_min:g} <= {y:g}", WINDOW.y_min <= y),
            (f"y <= y_max :  {y:g} <= {WINDOW.y_max:g}", y <= WINDOW.y_max),
        ]
        lines = [(f"{text}   {'yes' if ok else 'NO'}", theme.GREEN if ok else theme.RED) for text, ok in tests]
        kept = all(ok for _, ok in tests)
        return [
            InfoSection("Window", [f"{WINDOW.x_min:g} <= x <= {WINDOW.x_max:g},   {WINDOW.y_min:g} <= y <= {WINDOW.y_max:g}"]),
            InfoSection(f"Last point P{len(self.points)} = ({x:g}, {y:g})", lines, mono=True),
            InfoSection("Decision", [
                ("Keep it: every test succeeds." if kept else "Discard it: at least one test fails.",
                 theme.GREEN if kept else theme.RED),
                ("A point has no size, so it is either inside or outside. Points on the boundary count as inside.",
                 theme.TEXT_DIM),
            ]),
        ]


# ===========================================================================
# Mode 2: Cohen-Sutherland line clipping
# ===========================================================================

class CohenSutherlandMode(Mode):
    name = "Cohen–Sutherland"
    controls = STEP_CONTROLS + [("Drag", "move an endpoint")]

    def __init__(self, demo):
        super().__init__(demo)
        self.reset()

    def reset(self):
        self.endpoints = [(0.0, 4.0), (10.0, 7.0)]      # the lecture example
        self.dragging = None
        self.restart()

    def restart(self):
        p1, p2 = self.endpoints
        self.player = StepPlayer(lambda: C.cohen_sutherland_steps(p1, p2, WINDOW), interval=0.8)

    def handle_event(self, event):
        view = self.demo.view
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.dragging = nearest(self.endpoints, event.pos, view)
            return self.dragging is not None
        if event.type == pygame.MOUSEBUTTONUP:
            self.dragging = None
        if event.type == pygame.MOUSEMOTION and self.dragging is not None:
            self.endpoints[self.dragging] = snap(view, event.pos)
            self.restart()
            return True
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                self.player.step()
            elif event.key == pygame.K_p:
                self.player.toggle_play()
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                self.player.run_to_end()
            else:
                return False
            return True
        return False

    def update(self, dt):
        self.player.update(dt)

    def draw_region_codes(self, surface, view):
        """Write the 4-bit outcode in each of the nine regions."""
        xs = [(view.x_min + WINDOW.x_min) / 2, (WINDOW.x_min + WINDOW.x_max) / 2, (WINDOW.x_max + view.x_max) / 2]
        ys = [(view.y_min + WINDOW.y_min) / 2, (WINDOW.y_min + WINDOW.y_max) / 2, (WINDOW.y_max + view.y_max) / 2]
        for x in xs:
            for y in ys:
                code = C.code_text(C.outcode(x, y, WINDOW))
                draw_text(surface, code, view.world_to_screen(x, y), theme.TEXT_FAINT, theme.fonts().mono, centre=True)

    def draw(self, surface):
        view = self.demo.view
        view.draw_grid(surface)
        draw_window(surface, view)
        self.draw_region_codes(surface, view)

        p1, p2 = self.endpoints
        draw_dashed_line(surface, view.world_to_screen(*p1), view.world_to_screen(*p2), theme.TEXT_DIM)

        step = self.player.current
        if step is not None:
            # The segment as it stands after this step.
            a, b = step["p1"], step["p2"]
            if step["action"] == "clip":
                a, b = (step["point"], b) if step["endpoint"] == 1 else (a, step["point"])
            colour = {"accept": theme.GREEN, "reject": theme.RED}.get(step["action"], theme.BLUE)
            pygame.draw.line(surface, colour, view.world_to_screen(*a), view.world_to_screen(*b), 4)
            for s in self.player.done:
                if s["action"] == "clip":
                    draw_marker(surface, view.world_to_screen(*s["point"]), theme.YELLOW, None, radius=6)

        for name, point in (("P1", p1), ("P2", p2)):
            code = C.code_text(C.outcode(*point, WINDOW))
            draw_marker(surface, view.world_to_screen(*point), theme.TEXT, f"{name}  {code}", radius=7)

        draw_legend(surface, view.rect, [(theme.YELLOW, "window and intersection points"),
                                         (theme.BLUE, "segment while clipping"),
                                         (theme.GREEN, "accepted"), (theme.RED, "rejected")])

    def info_sections(self):
        p1, p2 = self.endpoints
        c1, c2 = C.outcode(*p1, WINDOW), C.outcode(*p2, WINDOW)
        sections = [
            InfoSection("Outcodes  (bits: Top Bottom Right Left)", [
                f"P1 = {fmt(p1)}  ->  {C.code_text(c1)}",
                f"P2 = {fmt(p2)}  ->  {C.code_text(c2)}",
                f"C1 | C2 = {C.code_text(c1 | c2)}   (0000 -> accept)",
                f"C1 & C2 = {C.code_text(c1 & c2)}   (≠ 0000 -> reject)",
            ], mono=True),
        ]

        log = []
        for number, s in enumerate(self.player.done, start=1):
            if s["action"] == "clip":
                name = f"P{s['endpoint']}"
                log.append(f"{number}. Neither test applies.")
                log.append((f"   Clip {name} against {C.BIT_NAMES[s['bit']]} -> {fmt(s['point'])}", theme.YELLOW))
            elif s["action"] == "accept":
                log.append((f"{number}. Both outcodes 0000: accept", theme.GREEN))
                log.append((f"   {fmt(s['p1'])} to {fmt(s['p2'])}", theme.GREEN))
            else:
                log.append((f"{number}. Both outside the same boundary: reject", theme.RED))
        if not log:
            log = [("Press Space to take the first step.", theme.TEXT_DIM)]
        sections.append(InfoSection(f"Steps ({self.player.status()})", log))
        sections.append(InfoSection("Intersection with a boundary", [
            "vertical x = x_e:   y = y1 + m (x_e - x1)",
            "horizontal y = y_e: x = x1 + (y_e - y1) / m",
        ], mono=True))
        return sections


# ===========================================================================
# Mode 3: Sutherland-Hodgman polygon clipping
# ===========================================================================

class SutherlandHodgmanMode(Mode):
    name = "Sutherland–Hodgman"
    controls = STEP_CONTROLS + [("Drag", "move a vertex")]
    STAGE_COLOURS = {"Left": theme.BLUE, "Right": theme.PURPLE, "Bottom": theme.GREEN, "Top": theme.RED}

    def __init__(self, demo):
        super().__init__(demo)
        self.reset()

    def reset(self):
        self.polygon = [(0.5, 3.0), (5.0, 7.5), (9.5, 4.5), (6.0, 0.5)]
        self.dragging = None
        self.restart()

    def restart(self):
        polygon = list(self.polygon)
        self.player = StepPlayer(lambda: C.sutherland_hodgman_stages(polygon, WINDOW), interval=1.2)

    def handle_event(self, event):
        view = self.demo.view
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.dragging = nearest(self.polygon, event.pos, view)
            return self.dragging is not None
        if event.type == pygame.MOUSEBUTTONUP:
            self.dragging = None
        if event.type == pygame.MOUSEMOTION and self.dragging is not None:
            self.polygon[self.dragging] = snap(view, event.pos)
            self.restart()
            return True
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                self.player.step()
            elif event.key == pygame.K_p:
                self.player.toggle_play()
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                self.player.run_to_end()
            else:
                return False
            return True
        return False

    def update(self, dt):
        self.player.update(dt)

    def draw_boundary(self, surface, view, boundary):
        """Thick line along one boundary, with the outside half-plane shaded."""
        colour = self.STAGE_COLOURS[boundary]
        if boundary in ("Left", "Right"):
            x = WINDOW.x_min if boundary == "Left" else WINDOW.x_max
            a, b = view.world_to_screen(x, view.y_min), view.world_to_screen(x, view.y_max)
            outside = [(view.x_min, view.y_min), (x, view.y_min), (x, view.y_max), (view.x_min, view.y_max)] \
                if boundary == "Left" else [(x, view.y_min), (view.x_max, view.y_min), (view.x_max, view.y_max), (x, view.y_max)]
        else:
            y = WINDOW.y_min if boundary == "Bottom" else WINDOW.y_max
            a, b = view.world_to_screen(view.x_min, y), view.world_to_screen(view.x_max, y)
            outside = [(view.x_min, view.y_min), (view.x_max, view.y_min), (view.x_max, y), (view.x_min, y)] \
                if boundary == "Bottom" else [(view.x_min, y), (view.x_max, y), (view.x_max, view.y_max), (view.x_min, view.y_max)]
        layer = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        pygame.draw.polygon(layer, (*theme.RED, 28), view.points_to_screen(outside))
        surface.blit(layer, (0, 0))
        pygame.draw.line(surface, colour, a, b, 3)

    def draw(self, surface):
        view = self.demo.view
        view.draw_grid(surface)
        draw_window(surface, view, extend=False)
        draw_dashed_polygon(surface, view.points_to_screen(self.polygon), theme.TEXT_DIM)

        stage = self.player.current
        if stage is None:
            draw_filled_polygon(surface, view.points_to_screen(self.polygon), theme.BLUE, fill_alpha=40)
        else:
            boundary, vertices_in, vertices_out, records = stage
            self.draw_boundary(surface, view, boundary)
            colour = self.STAGE_COLOURS[boundary]
            if len(vertices_out) >= 3:
                draw_filled_polygon(surface, view.points_to_screen(vertices_out), colour, fill_alpha=60)
            for i, p in enumerate(vertices_out, start=1):
                draw_marker(surface, view.world_to_screen(*p), colour, f"{i}", radius=5, label_offset=(8, 4))

        for i, p in enumerate(self.polygon, start=1):
            draw_marker(surface, view.world_to_screen(*p), theme.TEXT, f"V{i}", radius=6)
        draw_legend(surface, view.rect, [(theme.TEXT_DIM, "input polygon (dashed)"), (theme.RED, "outside the current boundary"),
                                         (theme.YELLOW, "clipping window")])

    def info_sections(self):
        stages = self.player.done
        order = " -> ".join(
            f"[{b}]" if stages and stages[-1][0] == b else b for b in C.BOUNDARIES)
        sections = [InfoSection("Clip against one boundary at a time", [order])]
        stage = self.player.current
        if stage is None:
            sections.append(InfoSection("Input polygon", [fmt(p) for p in self.polygon], mono=True))
            sections.append(InfoSection("Next", [("Press Space to clip against the Left boundary.", theme.TEXT_DIM)]))
            return sections

        boundary, vertices_in, vertices_out, records = stage
        rule_lines = []
        for r in records:
            rule_lines.append(f"{fmt(r['v1'])} -> {fmt(r['v2'])}")
            rule_lines.append((f"   {r['rule']}", self.STAGE_COLOURS[boundary]))
        sections.append(InfoSection(f"Stage {len(stages)}: {boundary} boundary — edge by edge", rule_lines))
        out = [fmt(p) for p in vertices_out] or [("(no vertices: the polygon is completely outside)", theme.RED)]
        sections.append(InfoSection(f"Output list: {len(vertices_out)} vertices", out, mono=True))
        if self.player.finished:
            sections.append(InfoSection("Done", [("The last output list is the clipped, closed polygon.", theme.GREEN)]))
        return sections


# ===========================================================================
# Mode 4: window-to-viewport mapping
# ===========================================================================

class ViewportMappingMode(Mode):
    name = "Viewport mapping"
    controls = [("Move mouse", "over the world"), ("I", "invert y on/off")]

    HOUSE = [(1.0, 1.0), (6.0, 1.0), (6.0, 4.5), (3.5, 7.0), (1.0, 4.5)]

    def __init__(self, demo):
        super().__init__(demo)
        canvas = demo.canvas_rect
        world_rect = pygame.Rect(canvas.left + 10, canvas.top + 50, 330, 420)
        self.world = Viewport2D(world_rect, units_tall=9.5 * world_rect.height / world_rect.width, centre=(5.0, 4.0))
        # The viewport is a real rectangle on the screen; its coordinates are pixels.
        # It has the same 3 : 2 shape as the window, so nothing is stretched.
        self.viewport_rect = pygame.Rect(canvas.left + 370, canvas.top + 160, 288, 192)
        self.reset()

    def reset(self):
        self.point = (5.0, 4.0)
        self.invert_y = True

    def viewport(self):
        r = self.viewport_rect
        return C.ClipWindow(r.left, r.right, r.top, r.bottom)

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION and self.world.contains_pixel(event.pos):
            self.point = self.world.screen_to_world(*event.pos)
            return True
        if event.type == pygame.KEYDOWN and event.key == pygame.K_i:
            self.invert_y = not self.invert_y
            return True
        return False

    def map(self, p):
        return C.window_to_viewport(p[0], p[1], WINDOW, self.viewport(), self.invert_y)

    def draw(self, surface):
        world = self.world
        fonts = theme.fonts()
        world.draw_grid(surface)
        draw_text(surface, "World: window 2 ≤ x ≤ 8, 2 ≤ y ≤ 6", (world.rect.left, world.rect.top - 24), theme.TEXT_DIM, fonts.small)
        draw_window(surface, world, extend=False)

        # Clip the house to the window, then map the clipped polygon to the viewport.
        clipped = C.sutherland_hodgman(self.HOUSE, WINDOW)
        draw_dashed_polygon(surface, world.points_to_screen(self.HOUSE), theme.TEXT_DIM)
        if len(clipped) >= 3:
            draw_filled_polygon(surface, world.points_to_screen(clipped), theme.BLUE)

        pygame.draw.rect(surface, theme.BACKGROUND, self.viewport_rect)
        pygame.draw.rect(surface, theme.YELLOW, self.viewport_rect, 2)
        r = self.viewport_rect
        draw_text(surface, "Viewport on the screen (pixels)", (r.left, r.top - 44), theme.TEXT_DIM, fonts.small)
        draw_text(surface, f"({r.left}, {r.top})", (r.left, r.top - 20), theme.TEXT_FAINT, fonts.small)
        draw_text(surface, f"({r.right}, {r.bottom})", (r.right - 70, r.bottom + 6), theme.TEXT_FAINT, fonts.small)
        if len(clipped) >= 3:
            draw_filled_polygon(surface, [tuple(map(round, self.map(p))) for p in clipped], theme.BLUE)

        # Corners of the window map to corners of the viewport.
        for corner, colour in (((WINDOW.x_min, WINDOW.y_min), theme.GREEN), ((WINDOW.x_max, WINDOW.y_max), theme.RED)):
            a = world.world_to_screen(*corner)
            b = tuple(map(round, self.map(corner)))
            draw_dashed_line(surface, a, b, colour)
            draw_marker(surface, a, colour, None)
            draw_marker(surface, b, colour, None)

        a = world.world_to_screen(*self.point)
        b = tuple(map(round, self.map(self.point)))
        draw_marker(surface, a, theme.TEXT, "P", radius=6)
        draw_marker(surface, b, theme.TEXT, "P'", radius=6)
        draw_legend(surface, self.demo.canvas_rect, [(theme.GREEN, "(x_min, y_min) corner"), (theme.RED, "(x_max, y_max) corner"),
                                                     (theme.BLUE, "house after clipping")], corner="right")

    def info_sections(self):
        x, y = self.point
        v = self.viewport()
        xs, ys = self.map(self.point)
        u = (x - WINDOW.x_min) / (WINDOW.x_max - WINDOW.x_min)
        t = (y - WINDOW.y_min) / (WINDOW.y_max - WINDOW.y_min)
        return [
            InfoSection("Window -> viewport", [
                "xs = xv_min + (x - x_min)/(x_max - x_min)",
                "              · (xv_max - xv_min)",
                "ys = yv_min + (y - y_min)/(y_max - y_min)",
                "              · (yv_max - yv_min)",
            ], mono=True),
            InfoSection(f"For P = ({x:.2f}, {y:.2f})", [
                f"x is {u:.2f} of the way across the window",
                f"y is {t:.2f} of the way up the window",
                f"viewport x: {v.x_min:g} .. {v.x_max:g},  y: {v.y_min:g} .. {v.y_max:g}",
                (f"P' = ({xs:.1f}, {ys:.1f}) screen pixels", theme.YELLOW),
            ]),
            InfoSection(f"Invert y: {'on' if self.invert_y else 'off'}  (press I)", [
                ("Screen y grows downward, so the y mapping is flipped: the top of the window goes to the top of the viewport."
                 if self.invert_y else "Without inversion the picture comes out upside down. Look at the house!",
                 theme.TEXT_DIM),
            ]),
        ]


class ClippingDemo(Demo):
    title = "Clipping"
    lecture = "3.3"

    def setup(self, canvas_rect):
        super().setup(canvas_rect)
        self.view = Viewport2D(canvas_rect, units_tall=13, centre=(5.0, 4.0))
        self.modes = [PointClippingMode(self), CohenSutherlandMode(self), SutherlandHodgmanMode(self),
                      ViewportMappingMode(self)]
