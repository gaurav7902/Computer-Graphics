"""Demo 6: The Z-Buffer (Lecture 3.4, 'When Two Surfaces Reach the Same Pixel').

    OnePixelMode     the lecture's walkthrough: three fragments arrive at one pixel
    TrianglesMode    three overlapping triangles drawn into a small framebuffer;
                     inspect any pixel's history, view the depth buffer, or
                     switch the depth test off to see what goes wrong
"""

import numpy as np
import pygame

from core import theme
from core.demo import Demo, InfoSection, Mode
from core.draw_utils import draw_arrow, draw_legend, draw_text
from core.stepper import StepPlayer
from graphics.triangle_raster import FrameBuffer, rasterize_triangle

STEP_CONTROLS = [("Space", "next"), ("P", "play/pause"), ("Enter", "all")]

COLOURS = {"blue": (0.37, 0.75, 0.94), "red": (0.94, 0.36, 0.36), "green": (0.38, 0.82, 0.55)}


def to_rgb255(colour):
    return tuple(int(c * 255) for c in colour)


def handle_step_keys(event, player):
    if event.type != pygame.KEYDOWN:
        return False
    if event.key == pygame.K_SPACE:
        player.step()
    elif event.key == pygame.K_p:
        player.toggle_play()
    elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
        player.run_to_end()
    else:
        return False
    return True


# ===========================================================================
# Mode 1: one pixel, three fragments (the slide example)
# ===========================================================================

class OnePixelMode(Mode):
    name = "One pixel"
    controls = STEP_CONTROLS

    # (colour name, depth) in arrival order, from the lecture slide.
    FRAGMENTS = [("blue", 0.60), ("red", 0.35), ("green", 0.80)]

    def __init__(self, demo):
        super().__init__(demo)
        self.reset()

    def reset(self):
        self.player = StepPlayer(self.depth_tests, interval=1.0)

    def depth_tests(self):
        """The Z-buffer rule, applied to each arriving fragment in turn."""
        stored_colour, stored_depth = None, 1.0          # an empty pixel starts at depth 1.0
        for name, z in self.FRAGMENTS:
            accepted = z < stored_depth                  # z_new < z_stored ?
            before = stored_depth
            if accepted:
                stored_colour, stored_depth = name, z    # replace BOTH colour and depth
            yield {"name": name, "z": z, "before": before, "accepted": accepted,
                   "colour": stored_colour, "depth": stored_depth}

    def handle_event(self, event):
        return handle_step_keys(event, self.player)

    def update(self, dt):
        self.player.update(dt)

    def draw(self, surface):
        canvas = self.demo.canvas_rect
        fonts = theme.fonts()
        state = self.player.current
        colour_name = state["colour"] if state else None
        depth = state["depth"] if state else 1.0

        # The two buffers for the same pixel (x, y).
        colour_box = pygame.Rect(canvas.left + 120, canvas.top + 70, 160, 160)
        depth_box = pygame.Rect(canvas.left + 400, canvas.top + 70, 160, 160)
        fill = to_rgb255(COLOURS[colour_name]) if colour_name else theme.BACKGROUND
        pygame.draw.rect(surface, fill, colour_box, border_radius=8)
        pygame.draw.rect(surface, theme.TEXT_DIM, colour_box, 2, border_radius=8)
        pygame.draw.rect(surface, theme.BACKGROUND, depth_box, border_radius=8)
        pygame.draw.rect(surface, theme.TEXT_DIM, depth_box, 2, border_radius=8)
        draw_text(surface, f"{depth:.2f}", depth_box.center, theme.TEXT, fonts.title, centre=True)
        draw_text(surface, "Colour buffer at (x, y)", (colour_box.centerx, colour_box.top - 22), theme.TEXT_DIM, fonts.small, centre=True)
        draw_text(surface, "Depth buffer at (x, y)", (depth_box.centerx, depth_box.top - 22), theme.TEXT_DIM, fonts.small, centre=True)
        draw_text(surface, colour_name or "background", (colour_box.centerx, colour_box.bottom + 16), theme.TEXT, fonts.body, centre=True)

        # One card per fragment, showing the test it went through.
        top = canvas.top + 300
        for i, (name, z) in enumerate(self.FRAGMENTS):
            card = pygame.Rect(canvas.left + 40 + i * 210, top, 190, 230)
            done = i < len(self.player.done)
            pygame.draw.rect(surface, theme.PANEL, card, border_radius=8)
            pygame.draw.rect(surface, theme.PANEL_BORDER, card, 1, border_radius=8)
            swatch = pygame.Rect(card.left + 16, card.top + 16, 40, 40)
            pygame.draw.rect(surface, to_rgb255(COLOURS[name]), swatch, border_radius=4)
            draw_text(surface, f"Fragment {i + 1}: {name}", (swatch.right + 10, swatch.top + 2), theme.TEXT, fonts.body)
            draw_text(surface, f"z = {z:.2f}", (swatch.right + 10, swatch.top + 22), theme.TEXT_DIM, fonts.small)
            if done:
                result = self.player.done[i]
                verdict = "nearer: update" if result["accepted"] else "farther: discard"
                sign = "<" if result["accepted"] else ">"
                colour = theme.GREEN if result["accepted"] else theme.RED
                draw_text(surface, f"{z:.2f} {sign} {result['before']:.2f}", (card.left + 16, card.top + 90), colour, fonts.title)
                draw_text(surface, verdict, (card.left + 16, card.top + 126), colour, fonts.body)
                draw_text(surface, f"stored: {result['colour']}, {result['depth']:.2f}", (card.left + 16, card.top + 170),
                          theme.TEXT_DIM, fonts.small)
            else:
                draw_text(surface, "waiting...", (card.left + 16, card.top + 100), theme.TEXT_FAINT, fonts.body)
            if i < 2:
                draw_arrow(surface, (card.right + 2, card.centery), (card.right + 18, card.centery), theme.TEXT_FAINT)

    def info_sections(self):
        lines = ["Initial: stored depth 1.0 (empty)"]
        for r in self.player.done:
            lines.append((f"{r['name']}: {r['z']:.2f} {'<' if r['accepted'] else '>'} {r['before']:.2f} -> "
                          f"{'update' if r['accepted'] else 'discard'}", theme.GREEN if r["accepted"] else theme.RED))
        if self.player.finished:
            lines.append((f"Final stored colour: {self.player.current['colour'].upper()} at depth "
                          f"{self.player.current['depth']:.2f}", theme.YELLOW))
        return [
            InfoSection("The Z-buffer idea", [
                "Keep a depth buffer the same size as the image.",
                "For each fragment: if z_new < z_stored, replace the stored depth AND the colour; otherwise keep "
                "what is there.",
            ]),
            InfoSection("This pixel", lines),
            InfoSection("Question", [("Would the final colour change if the fragments arrived in a different order?",
                                      theme.TEXT_DIM)]),
        ]


# ===========================================================================
# Mode 2: whole triangles in a small framebuffer
# ===========================================================================

class TrianglesMode(Mode):
    name = "Triangles"
    controls = STEP_CONTROLS + [("Z", "depth test on/off"), ("D", "show depth"), ("Mouse", "inspect a pixel")]

    WIDTH, HEIGHT = 32, 24

    # (name, three vertices in pixel coordinates, depth at each vertex).
    # The red triangle is tilted: its depth changes across it, so it passes
    # through the blue one, which is flat at depth 0.60.
    TRIANGLES = [
        ("blue", [(2, 3), (29, 6), (8, 22)], [0.60, 0.60, 0.60]),
        ("red", [(5, 18), (30, 21), (20, 1)], [0.20, 0.90, 0.55]),
        ("green", [(12, 2), (31, 14), (1, 15)], [0.80, 0.80, 0.80]),
    ]

    def __init__(self, demo):
        super().__init__(demo)
        canvas = demo.canvas_rect
        self.cell = min((canvas.width - 40) // self.WIDTH, (canvas.height - 120) // self.HEIGHT)
        self.grid_left = canvas.left + (canvas.width - self.cell * self.WIDTH) // 2
        self.grid_top = canvas.top + 50
        self.reset()

    def reset(self):
        self.depth_test = True
        self.show_depth = False
        self.inspected = None
        self.restart()

    def restart(self):
        self.buffer = FrameBuffer(self.WIDTH, self.HEIGHT, background=(0.055, 0.07, 0.11), far_depth=1.0)
        self.history = {}            # (row, col) -> list of (name, z, accepted)
        self.player = StepPlayer(self.draw_triangles, interval=1.0)
        if self.inspected is None:
            self.inspected = self.find_interesting_pixel()

    def draw_triangles(self):
        """Rasterise one triangle per step and record what happened at every pixel."""
        for name, vertices, depths in self.TRIANGLES:
            colour = np.array(COLOURS[name])
            # A pixel is covered when its centre lies inside the triangle.
            report = rasterize_triangle(self.buffer, vertices, depths, np.zeros((3, 1)),
                                        lambda values, c=colour: np.tile(c, (len(values), 1)),
                                        depth_test=self.depth_test)
            for r, c, z, ok in zip(report.rows, report.cols, report.depth, report.accepted):
                self.history.setdefault((int(r), int(c)), []).append((name, float(z), bool(ok)))
            yield name

    def find_interesting_pixel(self):
        """Pick a pixel where blue is drawn, red wins and green is discarded (like the slide)."""
        player = StepPlayer(self.draw_triangles)
        player.run_to_end()
        for key, events in sorted(self.history.items()):
            if [e[0] for e in events] == ["blue", "red", "green"] and [e[2] for e in events] == [True, True, False]:
                found = key
                break
        else:
            found = (12, 16)
        # Start again with empty buffers.
        self.buffer = FrameBuffer(self.WIDTH, self.HEIGHT, background=(0.055, 0.07, 0.11), far_depth=1.0)
        self.history = {}
        self.player = StepPlayer(self.draw_triangles, interval=1.0)
        return found

    def cell_rect(self, row, col):
        return pygame.Rect(self.grid_left + col * self.cell, self.grid_top + row * self.cell, self.cell, self.cell)

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            col = (event.pos[0] - self.grid_left) // self.cell
            row = (event.pos[1] - self.grid_top) // self.cell
            if 0 <= row < self.HEIGHT and 0 <= col < self.WIDTH:
                self.inspected = (row, col)
                return True
        if event.type == pygame.KEYDOWN and event.key == pygame.K_z:
            self.depth_test = not self.depth_test
            steps = len(self.player.done)
            self.restart()
            for _ in range(steps):                     # redo the same number of triangles
                self.player.step()
            return True
        if event.type == pygame.KEYDOWN and event.key == pygame.K_d:
            self.show_depth = not self.show_depth
            return True
        return handle_step_keys(event, self.player)

    def update(self, dt):
        self.player.update(dt)

    def draw(self, surface):
        fonts = theme.fonts()
        colours = self.buffer.to_uint8()
        for row in range(self.HEIGHT):
            for col in range(self.WIDTH):
                rect = self.cell_rect(row, col)
                if self.show_depth:
                    # Near = dark, far = light; an empty pixel shows 1.0 = white.
                    g = int(40 + 215 * self.buffer.depth[row, col])
                    fill = (g, g, g)
                else:
                    fill = tuple(int(v) for v in colours[row, col])
                pygame.draw.rect(surface, fill, rect)
                pygame.draw.rect(surface, theme.GRID, rect, 1)

        # Ideal triangle outlines on top, so you can compare them with the pixels.
        for name, vertices, _ in self.TRIANGLES[:len(self.player.done)]:
            points = [(self.grid_left + x * self.cell, self.grid_top + y * self.cell) for x, y in vertices]
            pygame.draw.polygon(surface, to_rgb255(COLOURS[name]), points, 1)

        if self.inspected:
            pygame.draw.rect(surface, theme.YELLOW, self.cell_rect(*self.inspected), 3)

        title = "Depth buffer (dark = near, white = 1.0 = empty)" if self.show_depth else "Colour buffer"
        test = "depth test ON" if self.depth_test else "depth test OFF: the last triangle drawn wins"
        draw_text(surface, f"{title}  ·  {test}", (self.grid_left, self.grid_top - 30),
                  theme.TEXT_DIM if self.depth_test else theme.RED, fonts.small)
        legend = [(to_rgb255(COLOURS[n]), f"{n}: depth {d[0]:.2f}" + (" to 0.90 (tilted)" if n == "red" else ""))
                  for n, _, d in self.TRIANGLES]
        draw_legend(surface, self.demo.canvas_rect, legend)

    def info_sections(self):
        drawn = [name for name in self.player.done]
        sections = [
            InfoSection(f"Triangles drawn: {len(drawn)} of 3", [
                ("Order: blue, then red, then green." if drawn else "Press Space to draw the first triangle.", theme.TEXT_DIM),
                (f"Depth test: {'ON' if self.depth_test else 'OFF'}  (press Z)", theme.GREEN if self.depth_test else theme.RED),
            ]),
        ]
        if self.inspected:
            row, col = self.inspected
            events = self.history.get(self.inspected, [])
            lines = [f"stored colour: {self.stored_name(row, col)}",
                     f"stored depth:  {self.buffer.depth[row, col]:.2f}"]
            stored = 1.0
            for name, z, ok in events:
                comparison = f"{z:.2f} {'<' if z < stored else '>='} {stored:.2f}" if self.depth_test else f"z = {z:.2f}"
                lines.append((f"{name}: {comparison} -> {'update' if ok else 'discard'}", theme.GREEN if ok else theme.RED))
                if ok:
                    stored = z
            if not events:
                lines.append(("No fragments here yet.", theme.TEXT_DIM))
            sections.append(InfoSection(f"Pixel (row {row}, column {col})", lines, mono=True))
        sections.append(InfoSection("What to notice", [
            "Where red passes through blue, the visible colour changes along a line: the Z-buffer handles "
            "intersecting surfaces pixel by pixel.",
            "Turn the depth test off (Z): green, drawn last, covers everything even though it is farther away.",
        ]))
        return sections

    def stored_name(self, row, col):
        events = self.history.get((row, col), [])
        accepted = [name for name, _, ok in events if ok]
        return accepted[-1] if accepted else "background"


class ZBufferDemo(Demo):
    title = "Z-Buffer"
    lecture = "3.4"

    def setup(self, canvas_rect):
        super().setup(canvas_rect)
        self.modes = [OnePixelMode(self), TrianglesMode(self)]
