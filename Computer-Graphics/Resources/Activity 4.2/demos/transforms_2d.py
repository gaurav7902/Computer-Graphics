"""Demo 1: 2D Transformations (Lecture 3.1).

The demo has three modes (Tab switches between them):

    BuildMode            apply translate, scale, rotate, reflect and shear,
                         and stack several steps into one combined matrix
    PivotRotationMode    rotate about a pivot C as T(a, b) · R(θ) · T(-a, -b)
    OrderMattersMode     compare T · R with R · T side by side

All the mathematics comes from graphics/matrices.py. This file only decides
what to show and reacts to the keyboard and mouse.
"""

import copy

import numpy as np
import pygame

from core import theme
from core.demo import Demo, InfoSection, Mode
from core.draw_utils import (draw_arrow, draw_cross, draw_dashed_line, draw_dashed_polygon,
                             draw_filled_polygon, draw_legend, draw_marker)
from core.viewport import Viewport2D
from core.widgets import make_button_row
from demos.editable_transforms import default_transforms
from graphics import matrices as M


# A small house, in world coordinates. The chimney makes the shape lopsided,
# so you can always see whether it has been rotated or mirrored.
# Vertex 0 is A = (1, 1), the point used in the lecture's translation example.
HOUSE = np.array([
    (1.0, 1.0), (3.0, 1.0), (3.0, 2.5),
    (2.7, 2.8), (2.7, 3.5), (2.4, 3.5), (2.4, 3.1),
    (2.0, 3.5), (1.0, 2.5),
])
TRACKED_VERTEX = 0


def draw_world_polygon(surface, view, points, colour, style="filled"):
    """Draw a world-space polygon in one of three styles: filled, outline or dashed."""
    screen_points = view.points_to_screen(points)
    if style == "filled":
        draw_filled_polygon(surface, screen_points, colour)
    elif style == "outline":
        pygame.draw.polygon(surface, colour, screen_points, 2)
    else:
        draw_dashed_polygon(surface, screen_points, colour)


# ===========================================================================
# Mode 1: build transformations one step at a time
# ===========================================================================

class BuildMode(Mode):
    name = "Build"
    controls = [
        ("T S R X Y H", "choose step"),
        ("Arrows", "change values"),
        ("Space", "animate"),
        ("Enter", "push"),
        ("U", "undo push"),
    ]

    # Keyboard shortcut for each transformation, in the same order as
    # default_transforms(): translate, scale, rotate, reflect x, reflect y, shear.
    KEYS = [pygame.K_t, pygame.K_s, pygame.K_r, pygame.K_x, pygame.K_y, pygame.K_h]
    KEY_LETTERS = ["T", "S", "R", "X", "Y", "H"]

    ANIMATION_SECONDS = 1.2

    def __init__(self, demo):
        super().__init__(demo)
        self.reset()
        canvas = demo.canvas_rect
        labels = [f"{key}  {t.name}" for key, t in zip(self.KEY_LETTERS, self.transforms)]
        self.buttons = make_button_row(canvas.left + 12, canvas.top + 12, labels)

    def reset(self):
        self.transforms = default_transforms()
        self.selected = 0                 # index into self.transforms
        self.stack = []                   # steps pushed with Enter, first applied first
        self.show_candidate = True        # is the current step previewed?
        self.progress = 1.0               # 0 -> 1 while animating
        self.animating = False

    # -- The step being edited, and the matrices it produces --------------------

    @property
    def candidate(self):
        return self.transforms[self.selected]

    def stack_matrix(self):
        """All pushed steps combined: M = Mk · ... · M2 · M1."""
        return M.compose(*[step.matrix() for step in self.stack])

    def total_matrix(self):
        """The pushed steps, followed by the current step if it is being previewed."""
        if self.show_candidate:
            return self.candidate.matrix(self.progress) @ self.stack_matrix()
        return self.stack_matrix()

    # -- Input ---------------------------------------------------------------------

    def select(self, index):
        self.selected = index
        self.show_candidate = True
        self.progress = 1.0

    def handle_event(self, event):
        for index, button in enumerate(self.buttons):
            if button.is_clicked(event):
                self.select(index)
                return True

        if event.type != pygame.KEYDOWN:
            return False

        if event.key in self.KEYS:
            self.select(self.KEYS.index(event.key))
        elif event.key in (pygame.K_LEFT, pygame.K_RIGHT, pygame.K_UP, pygame.K_DOWN):
            dx = {pygame.K_LEFT: -1, pygame.K_RIGHT: 1}.get(event.key, 0)
            dy = {pygame.K_DOWN: -1, pygame.K_UP: 1}.get(event.key, 0)
            self.candidate.adjust(dx, dy)
            self.show_candidate = True
            self.progress = 1.0
        elif event.key == pygame.K_SPACE:
            self.show_candidate = True
            self.progress = 0.0
            self.animating = True
        elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            # Store a copy, so editing the current step later does not change
            # the step that is already on the stack.
            self.stack.append(copy.deepcopy(self.candidate))
            self.show_candidate = False
        elif event.key == pygame.K_u and self.stack:
            self.stack.pop()
        else:
            return False
        return True

    def update(self, dt):
        if self.animating:
            self.progress = min(1.0, self.progress + dt / self.ANIMATION_SECONDS)
            self.animating = self.progress < 1.0

    # -- Drawing ---------------------------------------------------------------------

    def draw(self, surface):
        view = self.demo.view
        view.draw_grid(surface)

        # The original house, dashed.
        draw_world_polygon(surface, view, HOUSE, theme.ORIGINAL, "dashed")

        # Faint outlines after each pushed step, so the history stays visible.
        running = M.identity()
        for step in self.stack[:-1]:
            running = step.matrix() @ running
            draw_world_polygon(surface, view, M.apply(running, HOUSE), theme.TEXT_FAINT, "outline")

        # The result of the whole stack, in yellow.
        if self.stack:
            style = "outline" if self.show_candidate else "filled"
            draw_world_polygon(surface, view, M.apply(self.stack_matrix(), HOUSE), theme.YELLOW, style)

        # The current step previewed on top, in blue.
        if self.show_candidate:
            draw_world_polygon(surface, view, M.apply(self.total_matrix(), HOUSE), theme.BLUE, "filled")

        # Follow vertex A from where it started to where it ends up.
        a_start = view.world_to_screen(*HOUSE[TRACKED_VERTEX])
        a_end = view.world_to_screen(*M.apply(self.total_matrix(), HOUSE)[TRACKED_VERTEX])
        draw_dashed_line(surface, a_start, a_end, theme.TEXT_DIM)
        draw_marker(surface, a_start, theme.ORIGINAL, "A")
        end_colour = theme.BLUE if self.show_candidate else theme.YELLOW
        draw_marker(surface, a_end, end_colour, "A'")

        legend = [(theme.ORIGINAL, "original (dashed)")]
        if self.stack:
            legend.append((theme.YELLOW, "after the pushed steps"))
        if self.show_candidate:
            legend.append((theme.BLUE, "with the current step"))
        draw_legend(surface, view.rect, legend)

        # Toolbar buttons last, so they sit on top of the drawing.
        for index, button in enumerate(self.buttons):
            button.active = index == self.selected and self.show_candidate
            button.draw(surface)

    # -- Info panel -------------------------------------------------------------------

    def info_sections(self):
        step = self.candidate
        sections = [
            InfoSection(f"Current step: {step.label()}",
                        step.equations() + [(step.hint, theme.TEXT_DIM)]),
            InfoSection("Its 3 × 3 matrix", M.matrix_to_lines(step.matrix(self.progress)), mono=True),
        ]

        if self.stack:
            stack_lines = [f"M{i} = {s.label()}" for i, s in enumerate(self.stack, start=1)]
            stack_lines.append(("Applied top to bottom.", theme.TEXT_DIM))
        else:
            stack_lines = [("Empty. Press Enter to push the current step.", theme.TEXT_DIM)]
        sections.append(InfoSection("Stack", stack_lines))

        # Write the product the way the slides do: the last step is on the left.
        names = [f"M{i}" for i in range(len(self.stack), 0, -1)]
        if self.show_candidate:
            names.insert(0, step.label())
        product = " · ".join(names) if names else "I"
        sections.append(InfoSection(f"Combined:  M = {product}",
                                    M.matrix_to_lines(self.total_matrix()), mono=True))

        a = HOUSE[TRACKED_VERTEX]
        a_new = M.apply(self.total_matrix(), HOUSE)[TRACKED_VERTEX]
        sections.append(InfoSection("Vertex A", [
            f"A  = {M.point_to_text(a)}",
            f"A' = M · A = {M.point_to_text(a_new)}",
        ]))

        sections.append(InfoSection("The same thing in NumPy", [
            "P = to_homogeneous(HOUSE)   # 3 × 9",
            "P_new = M @ P               # one product",
        ], mono=True))
        return sections


# ===========================================================================
# Mode 2: rotation about an arbitrary pivot
# ===========================================================================

class PivotRotationMode(Mode):
    name = "Pivot rotation"
    controls = [
        ("Space", "next step"),
        ("Left/Right", "change θ"),
        ("Click", "move pivot C"),
    ]

    STEP_COLOURS = [theme.PURPLE, theme.YELLOW, theme.BLUE]

    # The house moved right so that its corner is P = (4, 1), the point used in
    # the lecture's numerical example. P is then simply vertex 0 of the shape.
    SHAPE = HOUSE + np.array([3.0, 0.0])
    POINT = tuple(SHAPE[TRACKED_VERTEX])

    def __init__(self, demo):
        super().__init__(demo)
        self.reset()

    def reset(self):
        self.pivot = (2.0, 1.0)     # C = (a, b) from the lecture example
        self.theta = 90.0
        self.steps_done = 0         # 0, 1, 2 or 3

    def steps(self):
        """The three steps, as (label, description, matrix)."""
        a, b = self.pivot
        return [
            (f"T({-a:g}, {-b:g})", "move C to the origin", M.translate(-a, -b)),
            (f"R({self.theta:g}°)", "rotate about the origin", M.rotate(self.theta)),
            (f"T({a:g}, {b:g})", "move C back", M.translate(a, b)),
        ]

    def matrix_after(self, count):
        """The combined matrix of the first `count` steps."""
        return M.compose(*[matrix for _, _, matrix in self.steps()[:count]])

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                self.steps_done = (self.steps_done + 1) % 4
                return True
            if event.key in (pygame.K_LEFT, pygame.K_RIGHT):
                self.theta += 15 if event.key == pygame.K_RIGHT else -15
                return True
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            view = self.demo.view
            if view.contains_pixel(event.pos):
                x, y = view.screen_to_world(*event.pos)
                # Snap to the nearest half unit so the numbers stay readable.
                self.pivot = (round(x * 2) / 2, round(y * 2) / 2)
                return True
        return False

    def draw(self, surface):
        view = self.demo.view
        view.draw_grid(surface)

        draw_world_polygon(surface, view, self.SHAPE, theme.ORIGINAL, "dashed")
        previous_point = view.world_to_screen(*self.POINT)
        draw_marker(surface, previous_point, theme.ORIGINAL, "P")

        # One shape per completed step; only the newest one is filled.
        for count in range(1, self.steps_done + 1):
            matrix = self.matrix_after(count)
            colour = self.STEP_COLOURS[count - 1]
            style = "filled" if count == self.steps_done else "outline"
            draw_world_polygon(surface, view, M.apply(matrix, self.SHAPE), colour, style)

            point = view.world_to_screen(*M.apply(matrix, [self.POINT])[0])
            draw_arrow(surface, previous_point, point, colour)
            draw_marker(surface, point, colour, f"P{count}")
            previous_point = point

        # After the last step, P has moved on a circle centred on C.
        if self.steps_done == 3:
            radius = np.hypot(self.POINT[0] - self.pivot[0], self.POINT[1] - self.pivot[1])
            centre = view.world_to_screen(*self.pivot)
            pygame.draw.circle(surface, theme.TEXT_FAINT, centre, round(radius * view.pixels_per_unit), 1)

        draw_cross(surface, view.world_to_screen(*self.pivot), theme.RED)
        draw_marker(surface, view.world_to_screen(*self.pivot), theme.RED, "C", radius=0)

        legend = [(theme.ORIGINAL, "original (dashed)"), (theme.RED, "pivot C")]
        for number, (label, description, _) in enumerate(self.steps()[:self.steps_done], start=1):
            legend.append((self.STEP_COLOURS[number - 1], f"after step {number}: {label}"))
        draw_legend(surface, view.rect, legend)

    def info_sections(self):
        a, b = self.pivot
        sections = [InfoSection(f"Rotate about C = ({a:g}, {b:g}) by θ = {self.theta:g}°", [
            "M = T(a, b) · R(θ) · T(-a, -b)",
            ("Press Space to apply one step at a time.", theme.TEXT_DIM),
        ])]

        lines = [f"Start:  P = {M.point_to_text(self.POINT)}"]
        for number, (label, description, _) in enumerate(self.steps(), start=1):
            if number <= self.steps_done:
                point = M.apply(self.matrix_after(number), [self.POINT])[0]
                lines.append((f"{number}. {label}: {description}", self.STEP_COLOURS[number - 1]))
                lines.append((f"    P{number} = {M.point_to_text(point)}", self.STEP_COLOURS[number - 1]))
            else:
                lines.append((f"{number}. {label}: {description}", theme.TEXT_FAINT))
        sections.append(InfoSection("Following the point P", lines))

        sections.append(InfoSection(f"Matrix of the first {self.steps_done} step(s)",
                                    M.matrix_to_lines(self.matrix_after(self.steps_done)), mono=True))

        if self.steps_done == 3:
            same = np.allclose(self.matrix_after(3), M.rotate_about_point(self.theta, a, b))
            sections.append(InfoSection("Check with NumPy", [
                "np.allclose(M,",
                f"    rotate_about_point({self.theta:g}, {a:g}, {b:g}))",
                f"-> {same}",
            ], mono=True))
        return sections


# ===========================================================================
# Mode 3: the order of the steps matters
# ===========================================================================

class OrderMattersMode(Mode):
    name = "Order matters"
    controls = [
        ("Left/Right", "change θ"),
        ("Up/Down", "change tx"),
        ("Space", "show/hide halfway shapes"),
    ]

    # The house moved down so that its corner is P = (1, 0), the point used on
    # the lecture's 'Order Matters' slide.
    SHAPE = HOUSE + np.array([0.0, -1.0])
    POINT = tuple(SHAPE[TRACKED_VERTEX])

    def __init__(self, demo):
        super().__init__(demo)
        self.reset()

    def reset(self):
        self.theta = 90.0
        self.tx = 2.0
        self.show_halfway = True

    def matrices(self):
        R = M.rotate(self.theta)
        T = M.translate(self.tx, 0.0)
        return R, T

    def handle_event(self, event):
        if event.type != pygame.KEYDOWN:
            return False
        if event.key in (pygame.K_LEFT, pygame.K_RIGHT):
            self.theta += 15 if event.key == pygame.K_RIGHT else -15
        elif event.key in (pygame.K_UP, pygame.K_DOWN):
            self.tx += 0.5 if event.key == pygame.K_UP else -0.5
        elif event.key == pygame.K_SPACE:
            self.show_halfway = not self.show_halfway
        else:
            return False
        return True

    def draw(self, surface):
        view = self.demo.view
        view.draw_grid(surface)
        R, T = self.matrices()

        draw_world_polygon(surface, view, self.SHAPE, theme.ORIGINAL, "dashed")
        draw_marker(surface, view.world_to_screen(*self.POINT), theme.ORIGINAL, "P")

        # Where each case is after its first step.
        if self.show_halfway:
            draw_world_polygon(surface, view, M.apply(R, self.SHAPE), theme.BLUE, "dashed")
            draw_world_polygon(surface, view, M.apply(T, self.SHAPE), theme.YELLOW, "dashed")

        # Case A: rotate first, then translate  ->  T @ R
        # Case B: translate first, then rotate  ->  R @ T
        same = np.allclose(T @ R, R @ T)
        cases = [(T @ R, theme.BLUE, "P'(A) = P'(B)" if same else "P'(A)"),
                 (R @ T, theme.YELLOW, None if same else "P'(B)")]
        for matrix, colour, label in cases:
            draw_world_polygon(surface, view, M.apply(matrix, self.SHAPE), colour, "filled")
            point = view.world_to_screen(*M.apply(matrix, [self.POINT])[0])
            draw_marker(surface, point, colour, label)

        legend = [(theme.ORIGINAL, "original (dashed)"),
                  (theme.BLUE, "case A: T · R  (rotate first)"),
                  (theme.YELLOW, "case B: R · T  (translate first)")]
        if self.show_halfway:
            legend.append((theme.TEXT_DIM, "dashed colour: after the first step"))
        draw_legend(surface, view.rect, legend)

    def info_sections(self):
        R, T = self.matrices()
        p_a = M.apply(T @ R, [self.POINT])[0]
        p_b = M.apply(R @ T, [self.POINT])[0]
        equal = np.allclose(T @ R, R @ T)

        return [
            InfoSection("The same two steps", [
                f"R = rotate by {self.theta:g}° about O",
                f"T = translate by ({self.tx:g}, 0)",
                f"P = {M.point_to_text(self.POINT)}",
            ]),
            InfoSection("Case A: rotate, then translate",
                        [("M_A = T · R", theme.BLUE)] + M.matrix_to_lines(T @ R)
                        + [(f"P' = {M.point_to_text(p_a)}", theme.BLUE)], mono=True),
            InfoSection("Case B: translate, then rotate",
                        [("M_B = R · T", theme.YELLOW)] + M.matrix_to_lines(R @ T)
                        + [(f"P' = {M.point_to_text(p_b)}", theme.YELLOW)], mono=True),
            InfoSection("Are they the same?", [
                (f"np.allclose(T @ R, R @ T) -> {equal}", theme.GREEN if equal else theme.RED),
                "Matrix multiplication is generally not commutative, so the order of the steps matters.",
                ("Try θ = 0° or tx = 0: when do the two cases agree?", theme.TEXT_DIM),
            ]),
        ]


# ===========================================================================
# The demo itself
# ===========================================================================

class Transforms2DDemo(Demo):
    title = "2D Transformations"
    lecture = "3.1"
    shared_controls = [("Wheel / + -", "zoom")]

    def setup(self, canvas_rect):
        super().setup(canvas_rect)
        # One coordinate mapper shared by all three modes: 16 world units tall.
        self.view = Viewport2D(canvas_rect, units_tall=18)
        self.modes = [BuildMode(self), PivotRotationMode(self), OrderMattersMode(self)]

    def handle_event(self, event):
        """Zooming works in every mode, so the demo handles it before the mode."""
        if event.type == pygame.MOUSEWHEEL:
            self.view.zoom(1.1 if event.y > 0 else 1 / 1.1)
            return True
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_EQUALS, pygame.K_PLUS, pygame.K_KP_PLUS):
            self.view.zoom(1.25)
            return True
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_MINUS, pygame.K_KP_MINUS):
            self.view.zoom(1 / 1.25)
            return True
        return super().handle_event(event)
