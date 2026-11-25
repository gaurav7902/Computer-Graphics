"""Editable 3D transformations for the 3D Transformations demo (Lecture 3.1).

These mirror the 2D classes in editable_transforms.py, with 4 x 4 matrices.
adjust() takes three directions: dx (Left/Right), dy (Up/Down) and
dz ([ and ] keys).
"""

from graphics import transforms3d as T3


class EditableTransform3D:
    name = "Transform"
    hint = ""

    def matrix(self, amount=1.0):
        raise NotImplementedError

    def label(self):
        raise NotImplementedError

    def adjust(self, dx, dy, dz):
        pass


class Translation3D(EditableTransform3D):
    name = "Translate"
    hint = "Left/Right tx, Up/Down ty, [ ] tz"

    def __init__(self, tx=4.0, ty=-1.0, tz=2.0):
        self.tx, self.ty, self.tz = tx, ty, tz

    def matrix(self, amount=1.0):
        return T3.translate(amount * self.tx, amount * self.ty, amount * self.tz)

    def label(self):
        return f"T({self.tx:g}, {self.ty:g}, {self.tz:g})"

    def adjust(self, dx, dy, dz):
        self.tx += 0.5 * dx
        self.ty += 0.5 * dy
        self.tz += 0.5 * dz


class Scaling3D(EditableTransform3D):
    name = "Scale"
    hint = "Left/Right sx, Up/Down sy, [ ] sz"

    def __init__(self, sx=2.0, sy=2.0, sz=2.0):
        self.sx, self.sy, self.sz = sx, sy, sz

    def matrix(self, amount=1.0):
        return T3.scale(1 + amount * (self.sx - 1), 1 + amount * (self.sy - 1), 1 + amount * (self.sz - 1))

    def label(self):
        return f"S({self.sx:g}, {self.sy:g}, {self.sz:g})"

    def adjust(self, dx, dy, dz):
        self.sx = min(3.0, max(0.25, self.sx + 0.25 * dx))
        self.sy = min(3.0, max(0.25, self.sy + 0.25 * dy))
        self.sz = min(3.0, max(0.25, self.sz + 0.25 * dz))


class AxisRotation(EditableTransform3D):
    """Rotation about one coordinate axis: the coordinate along that axis is unchanged."""

    hint = "Left/Right change θ by 15°"
    FUNCTIONS = {"x": T3.rotate_x, "y": T3.rotate_y, "z": T3.rotate_z}

    def __init__(self, axis, theta):
        self.axis = axis
        self.theta = theta
        self.name = f"Rotate {axis}"

    def matrix(self, amount=1.0):
        return self.FUNCTIONS[self.axis](amount * self.theta)

    def label(self):
        return f"R{self.axis}({self.theta:g}°)"

    def adjust(self, dx, dy, dz):
        self.theta += 15 * dx


def default_transforms():
    """Values from the Lecture 3.1 examples."""
    return [Translation3D(4, -1, 2), Scaling3D(2, 2, 2),
            AxisRotation("x", 90), AxisRotation("y", 90), AxisRotation("z", 60)]
