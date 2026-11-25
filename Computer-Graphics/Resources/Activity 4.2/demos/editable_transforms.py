"""Editable transformations for the 2D Transformations demo.

Each class is one transformation from Lecture 3.1. It stores its parameters
(for example tx and ty), lets the arrow keys change them, and builds its
matrix with graphics/matrices.py.

matrix(amount) takes a value from 0 to 1 so the demo can animate the step:
amount = 0 gives the identity (nothing has happened yet) and amount = 1 gives
the full transformation.
"""

from graphics import matrices as M


class EditableTransform:
    """The shared interface every transformation below follows."""

    name = "Transform"          # button label
    hint = ""                   # which arrow keys change which value

    def matrix(self, amount=1.0):
        raise NotImplementedError

    def label(self):
        """Short name with values, for example 'T(3, 2)'."""
        raise NotImplementedError

    def equations(self):
        """The coordinate equations from the slides, with values filled in."""
        raise NotImplementedError

    def adjust(self, dx, dy):
        """Arrow keys: dx is -1 (Left) or +1 (Right), dy is -1 (Down) or +1 (Up)."""


class Translation(EditableTransform):
    name = "Translate"
    hint = "Left/Right change tx, Up/Down change ty"

    def __init__(self, tx=3.0, ty=2.0):
        self.tx, self.ty = tx, ty

    def matrix(self, amount=1.0):
        return M.translate(amount * self.tx, amount * self.ty)

    def label(self):
        return f"T({self.tx:g}, {self.ty:g})"

    def equations(self):
        return [f"x' = x + {self.tx:g}", f"y' = y + {self.ty:g}"]

    def adjust(self, dx, dy):
        self.tx += 0.5 * dx
        self.ty += 0.5 * dy


class Scaling(EditableTransform):
    name = "Scale"
    hint = "Left/Right change sx, Up/Down change sy"

    def __init__(self, sx=2.0, sy=2.0):
        self.sx, self.sy = sx, sy

    def matrix(self, amount=1.0):
        # Animate from scale 1 (no change) towards the chosen factors.
        return M.scale(1 + amount * (self.sx - 1), 1 + amount * (self.sy - 1))

    def label(self):
        return f"S({self.sx:g}, {self.sy:g})"

    def equations(self):
        return [f"x' = {self.sx:g} · x", f"y' = {self.sy:g} · y"]

    def adjust(self, dx, dy):
        # Keep factors positive here; negative factors are covered by Reflect.
        self.sx = min(3.0, max(0.25, self.sx + 0.25 * dx))
        self.sy = min(3.0, max(0.25, self.sy + 0.25 * dy))


class Rotation(EditableTransform):
    name = "Rotate"
    hint = "Left/Right change θ by 15°"

    def __init__(self, theta=60.0):
        self.theta = theta

    def matrix(self, amount=1.0):
        return M.rotate(amount * self.theta)

    def label(self):
        return f"R({self.theta:g}°)"

    def equations(self):
        return [f"x' = x cos {self.theta:g}° - y sin {self.theta:g}°",
                f"y' = x sin {self.theta:g}° + y cos {self.theta:g}°"]

    def adjust(self, dx, dy):
        self.theta += 15 * dx


class Reflection(EditableTransform):
    hint = "No values to change"

    def __init__(self, axis="y"):
        self.axis = axis
        self.name = f"Reflect {axis}"

    def matrix(self, amount=1.0):
        # Animate by squashing the shape flat and out the other side:
        # the factor goes 1 -> 0 -> -1 as amount goes 0 -> 0.5 -> 1.
        flip = 1 - 2 * amount
        if self.axis == "x":
            return M.scale(1.0, flip)
        return M.scale(flip, 1.0)

    def label(self):
        return f"Ref_{self.axis}"

    def equations(self):
        if self.axis == "x":
            return ["x' = x", "y' = -y"]
        return ["x' = -x", "y' = y"]


class Shear(EditableTransform):
    name = "Shear"
    hint = "Left/Right change k by 0.25"

    def __init__(self, k=1.0):
        self.k = k

    def matrix(self, amount=1.0):
        return M.shear_x(amount * self.k)

    def label(self):
        return f"H(k={self.k:g})"

    def equations(self):
        return [f"x' = x + {self.k:g} · y", "y' = y"]

    def adjust(self, dx, dy):
        self.k = min(3.0, max(-3.0, self.k + 0.25 * dx))


def default_transforms():
    """One of each, using the values from the Lecture 3.1 examples."""
    return [Translation(3, 2), Scaling(2, 2), Rotation(60),
            Reflection("x"), Reflection("y"), Shear(1)]
