"""Demo 7: Scan Conversion (Lecture 3.5).

    DDAMode              step along the dominant axis, round each position
    BresenhamMode        integer decision parameter p_k chooses E or NE
    MidpointCircleMode   implicit-function test at the midpoint, plus 8-way symmetry
    ScanlineFillMode     crossings, even-odd parity and filled spans, row by row

Every pixel here is chosen by the algorithms in graphics/raster.py. Pygame
only paints the squares. The thin red line or circle is the ideal shape.
"""

import pygame

from core import theme
from core.demo import Demo, InfoSection, Mode
from core.draw_utils import draw_text
from core.pixel_grid import PixelGrid
from core.stepper import StepPlayer
from graphics import raster

STEP_CONTROLS = [("Space", "step"), ("P", "play/pause"), ("Enter", "run to end")]


class SteppingMode(Mode):
    """Shared behaviour: a StepPlayer driven by Space / P / Enter, and draggable points."""

    controls = STEP_CONTROLS

    def __init__(self, demo, x_range, y_range):
        super().__init__(demo)
        self.grid = PixelGrid(demo.canvas_rect, x_range, y_range)
        self.dragging = None
        self.reset()

    def make_steps(self):
        raise NotImplementedError

    def restart(self):
        self.player = StepPlayer(self.make_steps, interval=0.35)

    def handle_step_keys(self, event):
        if event.type != pygame.KEYDOWN:
            return False
        if event.key == pygame.K_SPACE:
            self.player.step()
        elif event.key == pygame.K_p:
            self.player.toggle_play()
        elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            self.player.run_to_end()
        else:
            return False
        return True

    def update(self, dt):
        self.player.update(dt)


class LineMode(SteppingMode):
    """A line from P1 to P2 whose endpoints can be dragged to any pixel."""

    controls = STEP_CONTROLS + [("Drag", "move an endpoint")]
    START = ((2, 2), (9, 6))

    def __init__(self, demo):
        super().__init__(demo, (0, 16), (0, 12))

    def reset(self):
        self.endpoints = [list(self.START[0]), list(self.START[1])]
        self.restart()

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pixel = self.grid.pixel_at(event.pos)
            for i, p in enumerate(self.endpoints):
                if pixel == tuple(p):
                    self.dragging = i
                    return True
        elif event.type == pygame.MOUSEBUTTONUP:
            self.dragging = None
        elif event.type == pygame.MOUSEMOTION and self.dragging is not None:
            pixel = self.grid.pixel_at(event.pos)
            if pixel and pixel != tuple(self.endpoints[1 - self.dragging]):
                self.endpoints[self.dragging] = list(pixel)
                self.restart()
            return True
        return self.handle_step_keys(event)

    def draw_line_scene(self, surface, pixels, extra=None):
        grid = self.grid
        grid.draw_grid(surface)
        for x, y in pixels:
            grid.fill(surface, x, y, theme.BLUE)
        if extra:
            extra(surface)
        (x1, y1), (x2, y2) = self.endpoints
        pygame.draw.line(surface, theme.RED, grid.to_screen(x1, y1), grid.to_screen(x2, y2), 2)
        for name, (x, y) in zip(("P1", "P2"), self.endpoints):
            grid.outline(surface, x, y, theme.YELLOW, 3)
            draw_text(surface, f"{name} ({x}, {y})", (grid.to_screen(x, y)[0] + 10, grid.to_screen(x, y)[1] - 30),
                      theme.YELLOW, theme.fonts().small)


# ===========================================================================
# DDA
# ===========================================================================

class DDAMode(LineMode):
    name = "DDA"
    START = ((2, 2), (7, 5))          # the lecture's DDA example

    def make_steps(self):
        (x1, y1), (x2, y2) = self.endpoints
        return raster.dda_line(x1, y1, x2, y2)

    def draw(self, surface):
        steps = self.player.done

        def exact_positions(surface):
            # Orange dots: the exact (fractional) positions before rounding.
            for s in steps:
                pygame.draw.circle(surface, theme.YELLOW, self.grid.to_screen(s["x"], s["y"]), 5)

        self.draw_line_scene(surface, [(s["px"], s["py"]) for s in steps], exact_positions)

    def info_sections(self):
        (x1, y1), (x2, y2) = self.endpoints
        dx, dy = x2 - x1, y2 - y1
        steps = max(abs(dx), abs(dy))
        rows = [f"{s['k']:>2}  ({s['x']:5.2f}, {s['y']:5.2f})  ->  ({s['px']}, {s['py']})" for s in self.player.done[-14:]]
        return [
            InfoSection("Set-up", [
                f"Δx = {dx},  Δy = {dy},  steps = max(|Δx|, |Δy|) = {steps}",
                f"x_inc = Δx / steps = {dx / steps if steps else 0:.2f}",
                f"y_inc = Δy / steps = {dy / steps if steps else 0:.2f}",
            ]),
            InfoSection("k   exact position      ->  pixel", rows or [("Press Space to plot the first pixel.", theme.TEXT_DIM)], mono=True),
            InfoSection("What DDA still does every step", [
                ("It keeps fractional coordinates and rounds each one. Bresenham avoids both.", theme.TEXT_DIM)]),
        ]


# ===========================================================================
# Bresenham
# ===========================================================================

class BresenhamMode(LineMode):
    name = "Bresenham"
    START = ((2, 2), (9, 6))          # the lecture's worked example

    def make_steps(self):
        (x1, y1), (x2, y2) = self.endpoints
        return raster.bresenham_line(x1, y1, x2, y2)

    def first_octant(self):
        (x1, y1), (x2, y2) = self.endpoints
        return x2 >= x1 and y2 >= y1 and (y2 - y1) <= (x2 - x1)

    def draw(self, surface):
        steps = self.player.done

        def candidates(surface):
            # Before the next step, outline the two candidate pixels.
            if self.player.finished or not steps or not self.first_octant():
                return
            x, y = steps[-1]["x"], steps[-1]["y"]
            for cx, cy, label in ((x + 1, y, "E"), (x + 1, y + 1, "NE")):
                self.grid.outline(surface, cx, cy, theme.GREEN, 2)
                draw_text(surface, label, self.grid.to_screen(cx, cy), theme.GREEN, theme.fonts().small, centre=True)

        self.draw_line_scene(surface, [(s["x"], s["y"]) for s in steps], candidates)

    def info_sections(self):
        (x1, y1), (x2, y2) = self.endpoints
        dx, dy = abs(x2 - x1), abs(y2 - y1)
        major, minor = (dy, dx) if dy > dx else (dx, dy)
        octant = self.first_octant()
        names = {"straight": "E" if octant else "straight", "diagonal": "NE" if octant else "diagonal"}
        rows = []
        for s in self.player.done[-14:]:
            if s["p"] is None:
                rows.append(f"start         ({s['x']}, {s['y']})")
            else:
                rows.append(f"p = {s['p']:>4}  {names[s['move']]:>8}  ({s['x']}, {s['y']})")
        notes = ["p < 0  -> E,  p += 2Δy", "p >= 0 -> NE, p += 2Δy - 2Δx"]
        if not octant:
            notes.append(("Other slopes: swap the roles of x and y and/or step backwards; the rule is the same.",
                          theme.TEXT_DIM))
        return [
            InfoSection("Set-up", [
                f"Δx = {dx},  Δy = {dy}" + ("   (y is dominant)" if dy > dx else ""),
                f"p0 = 2Δy - Δx = 2·{minor} - {major} = {2 * minor - major}",
            ] + notes),
            InfoSection("decision    move     pixel", rows or [("Press Space.", theme.TEXT_DIM)], mono=True),
            InfoSection("Why it is fast", [("Only integer additions and comparisons: no fractions, no rounding.",
                                            theme.TEXT_DIM)]),
        ]


# ===========================================================================
# Midpoint circle
# ===========================================================================

class MidpointCircleMode(SteppingMode):
    name = "Midpoint circle"
    controls = STEP_CONTROLS + [("Up/Down", "radius")]

    def __init__(self, demo):
        super().__init__(demo, (-8, 8), (-8, 8))

    def reset(self):
        self.radius = 5                 # the lecture's worked example
        self.restart()

    def make_steps(self):
        return raster.midpoint_circle(self.radius)

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_UP, pygame.K_DOWN):
            self.radius = max(1, min(8, self.radius + (1 if event.key == pygame.K_UP else -1)))
            self.restart()
            return True
        return self.handle_step_keys(event)

    def draw(self, surface):
        grid = self.grid
        grid.draw_grid(surface, label_every=2)

        # The octant 0 <= x <= y is between the y-axis and the line x = y.
        pygame.draw.line(surface, theme.TEXT_FAINT, grid.to_screen(0, 0), grid.to_screen(8, 8), 1)
        draw_text(surface, "x = y", grid.to_screen(7.3, 8), theme.TEXT_FAINT, theme.fonts().small)

        for s in self.player.done:
            for px, py in raster.eight_way_symmetry(s["x"], s["y"]):
                grid.fill(surface, px, py, theme.BLUE)
            grid.fill(surface, s["x"], s["y"], theme.YELLOW)

        # The midpoint M between the next two candidates, E and SE.
        current = self.player.current
        if current and current["move"]:
            x, y = current["x"], current["y"]
            grid.outline(surface, x + 1, y, theme.GREEN, 2)
            grid.outline(surface, x + 1, y - 1, theme.GREEN, 2)
            pygame.draw.circle(surface, theme.GREEN, grid.to_screen(x + 1, y - 0.5), 5)
            draw_text(surface, "M", grid.to_screen(x + 1.3, y - 0.5), theme.GREEN, theme.fonts().small)

        centre = grid.to_screen(0, 0)
        pygame.draw.circle(surface, theme.RED, centre, round(self.radius * grid.cell), 2)

    def info_sections(self):
        rows = [f"({s['x']}, {s['y']})  p = {s['p']:>3}  -> {s['move'] or 'stop'}" for s in self.player.done]
        return [
            InfoSection(f"Radius R = {self.radius}", [
                f"Start at (0, R) with p0 = 1 - R = {1 - self.radius}",
                "p < 0  -> E,  p += 2x + 3",
                "p >= 0 -> SE, p += 2x - 2y + 5",
                ("Stop before accepting a point with x > y.", theme.TEXT_DIM),
            ]),
            InfoSection("computed octant (yellow)", rows or [("Press Space.", theme.TEXT_DIM)], mono=True),
            InfoSection("Eight-way symmetry", [
                "Each computed (x, y) also gives (y, x), (-x, y), (-y, x), (x, -y), (y, -x), (-x, -y), (-y, -x).",
                ("Blue pixels are the reflected copies.", theme.TEXT_DIM),
            ]),
        ]


# ===========================================================================
# Scan-line polygon fill
# ===========================================================================

class ScanlineFillMode(SteppingMode):
    name = "Scan-line fill"
    controls = STEP_CONTROLS + [("N", "next polygon")]

    POLYGONS = [
        ("U shape", "Scan line y = 6 crosses at 2, 5, 8, 11, as in the lecture.",
         [(2, 1), (11, 1), (11, 9), (8, 9), (8, 4), (5, 4), (5, 9), (2, 9)]),
        ("Triangle", "The simplest case: two crossings on every scan line.", [(1, 1), (13, 3), (5, 10)]),
        ("Arrow", "Has pass-through vertices, a local minimum and a local maximum.",
         [(1, 5), (6, 1), (6, 3), (13, 3), (13, 7), (6, 7), (6, 9)]),
    ]

    def __init__(self, demo):
        super().__init__(demo, (0, 14), (0, 10))

    def reset(self):
        self.index = 0
        self.restart()

    @property
    def polygon(self):
        return self.POLYGONS[self.index][2]

    def make_steps(self):
        return raster.scanline_fill(self.polygon)

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_n:
            self.index = (self.index + 1) % len(self.POLYGONS)
            self.restart()
            return True
        return self.handle_step_keys(event)

    def draw(self, surface):
        grid = self.grid
        grid.draw_grid(surface)
        for row in self.player.done:
            for x, y in row["pixels"]:
                grid.fill(surface, x, y, theme.BLUE)

        current = self.player.current
        if current:
            y = current["y"]
            left, right = grid.to_screen(grid.x_min - 0.5, y), grid.to_screen(grid.x_max + 0.5, y)
            pygame.draw.line(surface, theme.YELLOW, left, right, 2)
            for x in current["crossings"]:
                pygame.draw.circle(surface, theme.YELLOW, grid.to_screen(x, y), 6)

        points = [grid.to_screen(x, y) for x, y in self.polygon]
        pygame.draw.polygon(surface, theme.RED, points, 2)

    def info_sections(self):
        current = self.player.current
        name, note, _ = self.POLYGONS[self.index]
        sections = [InfoSection(f"Polygon: {name}", [
            (note, theme.YELLOW),
            "For each scan line: find the crossings, sort them, then fill x0-x1, x2-x3, ... (even-odd rule).",
            ("Edges are counted at their lower end, not their upper end, and horizontal edges are ignored.",
             theme.TEXT_DIM),
        ])]
        if current:
            crossings = ", ".join(f"{x:g}" for x in current["crossings"]) or "none"
            spans = ", ".join(f"[{a:g}, {b:g}]" for a, b in current["spans"]) or "none"
            sections.append(InfoSection(f"Scan line y = {current['y']}", [
                f"crossings: {crossings}",
                f"spans:     {spans}",
                f"pixels filled: {len(current['pixels'])}",
            ], mono=True))
        rows = [f"y = {r['y']:>2}: {len(r['crossings'])} crossings, {len(r['pixels']):>2} pixels" for r in self.player.done[-10:]]
        sections.append(InfoSection("Rows so far", rows or [("Press Space for the first scan line.", theme.TEXT_DIM)], mono=True))
        return sections


class ScanConversionDemo(Demo):
    title = "Scan Conversion"
    lecture = "3.5"

    def setup(self, canvas_rect):
        super().setup(canvas_rect)
        self.modes = [DDAMode(self), BresenhamMode(self), MidpointCircleMode(self), ScanlineFillMode(self)]
