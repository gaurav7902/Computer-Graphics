"""Demo 2: 3D Transformations (Lecture 3.1, from 'From 2D to 3D' onward).

    BuildMode3D        translate, scale and rotate a cube; stack steps into one 4 x 4 matrix
    SlideExamplesMode  the five worked examples from the lecture, one at a time

Drag the canvas to orbit the display camera; the wheel zooms.
"""

import copy

import numpy as np
import pygame

from core import theme
from core.demo import Demo, InfoSection, Mode
from core.draw_utils import draw_legend
from core.widgets import make_button_row
from demos.editable_transforms3d import default_transforms
from demos.scene3d import OrbitView
from graphics import transforms3d as T3
from graphics.matrices import compose, matrix_to_lines
from graphics.mesh import CUBE_EDGES

# The unit cube from (0, 0, 0) to (1, 1, 1). Vertex 6 is (1, 1, 1).
CUBE = np.array([
    (0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0),
    (0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1),
], dtype=float)
TRACKED_VERTEX = 6


class BuildMode3D(Mode):
    name = "Build"
    controls = [
        ("T S X Y Z", "choose step"),
        ("Arrows  [ ]", "change values"),
        ("Space", "animate"),
        ("Enter", "push"),
        ("U", "undo"),
        ("Drag", "orbit"),
    ]

    KEYS = [pygame.K_t, pygame.K_s, pygame.K_x, pygame.K_y, pygame.K_z]
    KEY_LETTERS = ["T", "S", "X", "Y", "Z"]
    ANIMATION_SECONDS = 1.2

    def __init__(self, demo):
        super().__init__(demo)
        self.reset()
        canvas = demo.canvas_rect
        labels = [f"{key}  {t.name}" for key, t in zip(self.KEY_LETTERS, self.transforms)]
        self.buttons = make_button_row(canvas.left + 12, canvas.top + 12, labels)

    def reset(self):
        self.transforms = default_transforms()
        self.selected = 0
        self.stack = []
        self.show_candidate = True
        self.progress = 1.0
        self.animating = False

    @property
    def candidate(self):
        return self.transforms[self.selected]

    def stack_matrix(self):
        return compose(*[step.matrix() for step in self.stack]) if self.stack else np.eye(4)

    def total_matrix(self):
        if self.show_candidate:
            return self.candidate.matrix(self.progress) @ self.stack_matrix()
        return self.stack_matrix()

    def select(self, index):
        self.selected, self.show_candidate, self.progress = index, True, 1.0

    def handle_event(self, event):
        for index, button in enumerate(self.buttons):
            if button.is_clicked(event):
                self.select(index)
                return True
        if self.demo.view.handle_event(event, [b.rect for b in self.buttons]):
            return True
        if event.type != pygame.KEYDOWN:
            return False

        directions = {
            pygame.K_LEFT: (-1, 0, 0), pygame.K_RIGHT: (1, 0, 0),
            pygame.K_DOWN: (0, -1, 0), pygame.K_UP: (0, 1, 0),
            pygame.K_LEFTBRACKET: (0, 0, -1), pygame.K_RIGHTBRACKET: (0, 0, 1),
        }
        if event.key in self.KEYS:
            self.select(self.KEYS.index(event.key))
        elif event.key in directions:
            self.candidate.adjust(*directions[event.key])
            self.show_candidate, self.progress = True, 1.0
        elif event.key == pygame.K_SPACE:
            self.show_candidate, self.progress, self.animating = True, 0.0, True
        elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
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

    def draw(self, surface):
        view = self.demo.view
        axis = getattr(self.candidate, "axis", None) if self.show_candidate else None
        view.draw_floor_and_axes(surface, highlight_axis=axis)

        view.draw_edges(surface, CUBE, CUBE_EDGES, theme.ORIGINAL, 1)
        if self.stack:
            view.draw_edges(surface, T3.apply(self.stack_matrix(), CUBE), CUBE_EDGES, theme.YELLOW, 2)
        if self.show_candidate:
            view.draw_edges(surface, T3.apply(self.total_matrix(), CUBE), CUBE_EDGES, theme.BLUE, 3)

        start = CUBE[TRACKED_VERTEX]
        end = T3.apply(self.total_matrix(), CUBE)[TRACKED_VERTEX]
        view.draw_point(surface, start, theme.ORIGINAL, "P")
        view.draw_point(surface, end, theme.BLUE if self.show_candidate else theme.YELLOW, "P'")

        legend = [(theme.ORIGINAL, "unit cube"), (theme.RED, "x axis"), (theme.GREEN, "y axis"), (theme.BLUE, "z axis")]
        if self.stack:
            legend.append((theme.YELLOW, "after the pushed steps"))
        draw_legend(surface, view.rect, legend)

        for index, button in enumerate(self.buttons):
            button.active = index == self.selected and self.show_candidate
            button.draw(surface)

    def info_sections(self):
        step = self.candidate
        names = [f"M{i}" for i in range(len(self.stack), 0, -1)]
        if self.show_candidate:
            names.insert(0, step.label())
        stack_lines = ([f"M{i} = {s.label()}" for i, s in enumerate(self.stack, start=1)]
                       or [("Empty. Press Enter to push the current step.", theme.TEXT_DIM)])
        p = CUBE[TRACKED_VERTEX]
        p_new = T3.apply(self.total_matrix(), CUBE)[TRACKED_VERTEX]
        return [
            InfoSection(f"Current step: {step.label()}", [(step.hint, theme.TEXT_DIM)]),
            InfoSection("Its 4 × 4 matrix", matrix_to_lines(step.matrix(self.progress)), mono=True),
            InfoSection("Stack", stack_lines),
            InfoSection(f"Combined:  M = {' · '.join(names) if names else 'I'}",
                        matrix_to_lines(self.total_matrix()), mono=True),
            InfoSection("Corner P of the cube", [
                f"P  = {T3.point_to_text(p)}",
                f"P' = M · P = {T3.point_to_text(p_new)}",
            ]),
        ]


class SlideExamplesMode(Mode):
    """Step through the worked examples on the 3D slides of Lecture 3.1."""

    name = "Slide examples"
    controls = [
        ("Left/Right", "choose example"),
        ("Space", "animate"),
        ("Drag", "orbit"),
    ]

    # Each example: (title, label, point P, axis to highlight, make_matrix).
    # make_matrix(amount) builds the matrix part of the way: amount = 0 is the
    # identity and amount = 1 is the full transformation, so we can animate it.
    EXAMPLES = [
        ("Translation in 3D", "T(4, -1, 2)", (1, 2, 3), None, lambda a: T3.translate(4 * a, -1 * a, 2 * a)),
        ("Scaling in 3D", "S(2, 2, 2)", (1, 1, 1), None, lambda a: T3.scale(1 + a, 1 + a, 1 + a)),
        ("Rotation about z", "Rz(60°)", (3, 0, 2), "z", lambda a: T3.rotate_z(60 * a)),
        ("Rotation about x", "Rx(90°)", (1, 2, 0), "x", lambda a: T3.rotate_x(90 * a)),
        ("Rotation about y", "Ry(90°)", (0, 2, 1), "y", lambda a: T3.rotate_y(90 * a)),
    ]

    def __init__(self, demo):
        super().__init__(demo)
        self.reset()

    def reset(self):
        self.index = 0
        self.progress = 1.0

    def example(self):
        return self.EXAMPLES[self.index]

    def matrix(self, amount=1.0):
        return self.example()[4](amount)

    def handle_event(self, event):
        if self.demo.view.handle_event(event):
            return True
        if event.type != pygame.KEYDOWN:
            return False
        if event.key in (pygame.K_LEFT, pygame.K_RIGHT):
            step = 1 if event.key == pygame.K_RIGHT else -1
            self.index = (self.index + step) % len(self.EXAMPLES)
            self.progress = 1.0
        elif event.key == pygame.K_SPACE:
            self.progress = 0.0
        else:
            return False
        return True

    def update(self, dt):
        self.progress = min(1.0, self.progress + dt / 1.2)

    def draw(self, surface):
        view = self.demo.view
        title, label, point, axis, _ = self.example()
        view.draw_floor_and_axes(surface, highlight_axis=axis)

        view.draw_edges(surface, CUBE, CUBE_EDGES, theme.ORIGINAL, 1)
        view.draw_edges(surface, T3.apply(self.matrix(self.progress), CUBE), CUBE_EDGES, theme.BLUE, 2)

        # The path of P while the animation runs: a straight line for
        # translation and scaling, an arc for rotation.
        path = [T3.apply(self.matrix(t), [point])[0] for t in np.linspace(0, 1, 30)]
        for a, b in zip(path, path[1:]):
            view.draw_segment(surface, a, b, theme.TEXT_DIM)
        view.draw_point(surface, point, theme.ORIGINAL, f"P {T3.point_to_text(point, 0)}")
        moved = T3.apply(self.matrix(self.progress), [point])[0]
        view.draw_point(surface, moved, theme.YELLOW, "P'")

        draw_legend(surface, view.rect, [(theme.ORIGINAL, "unit cube"), (theme.BLUE, f"cube after {label}"),
                                         (theme.YELLOW, "P' (the example's point)")])

    def info_sections(self):
        title, label, point, axis, _ = self.example()
        result = T3.apply(self.matrix(), [point])[0]
        lines = [f"P  = {T3.point_to_text(point, 0)}", (f"P' = {label} · P = {T3.point_to_text(result, 3)}", theme.YELLOW)]
        if axis:
            lines.append((f"The {axis} coordinate stays unchanged; the other two rotate.", theme.TEXT_DIM))
        return [
            InfoSection(f"Example {self.index + 1} of {len(self.EXAMPLES)}: {title}", lines),
            InfoSection(f"{label} as a 4 × 4 matrix", matrix_to_lines(self.matrix()), mono=True),
            InfoSection("One pattern behind 3D transformations", [
                "Translation: displacements in the last column",
                "Scaling: factors on the diagonal",
                "Rotation: a cos/sin block in the two coordinates that change",
            ]),
        ]


class Transforms3DDemo(Demo):
    title = "3D Transformations"
    lecture = "3.1"

    def setup(self, canvas_rect):
        super().setup(canvas_rect)
        self.view = OrbitView(canvas_rect, target=(1.5, 1.0, 1.0), distance=11)
        self.modes = [BuildMode3D(self), SlideExamplesMode(self)]
