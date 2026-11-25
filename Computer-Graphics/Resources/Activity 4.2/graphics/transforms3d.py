"""3D transformation matrices in homogeneous coordinates (Lecture 3.1, second half).

A 3D point (x, y, z) becomes the column vector (x, y, z, 1). Every 3D
transformation is then one 4 x 4 matrix, and the ideas are exactly the same
as in 2D:

    translation  -> displacements in the last column
    scaling      -> scale factors on the diagonal
    rotation     -> a cos/sin block in the two coordinates that change;
                    the coordinate along the rotation axis stays unchanged

compose() from graphics/matrices.py works for 4 x 4 matrices too.
"""

import numpy as np

from graphics.matrices import compose  # noqa: F401  (re-exported for the demos)


def identity():
    return np.eye(4)


def translate(tx, ty, tz):
    """Slide 'Translation in 3D'."""
    return np.array([
        [1.0, 0.0, 0.0, tx],
        [0.0, 1.0, 0.0, ty],
        [0.0, 0.0, 1.0, tz],
        [0.0, 0.0, 0.0, 1.0],
    ])


def scale(sx, sy, sz):
    """Slide 'Scaling in 3D'."""
    return np.diag([sx, sy, sz, 1.0])


def rotate_x(theta_degrees):
    """Rotation about the x-axis: x stays unchanged while y and z rotate."""
    t = np.radians(theta_degrees)
    c, s = np.cos(t), np.sin(t)
    return np.array([
        [1.0, 0.0, 0.0, 0.0],
        [0.0, c, -s, 0.0],
        [0.0, s, c, 0.0],
        [0.0, 0.0, 0.0, 1.0],
    ])


def rotate_y(theta_degrees):
    """Rotation about the y-axis: y stays unchanged while x and z rotate.

    Note where the minus sign is: in the bottom-left, not the top-right.
    """
    t = np.radians(theta_degrees)
    c, s = np.cos(t), np.sin(t)
    return np.array([
        [c, 0.0, s, 0.0],
        [0.0, 1.0, 0.0, 0.0],
        [-s, 0.0, c, 0.0],
        [0.0, 0.0, 0.0, 1.0],
    ])


def rotate_z(theta_degrees):
    """Rotation about the z-axis: the 2D rotation, with z left unchanged."""
    t = np.radians(theta_degrees)
    c, s = np.cos(t), np.sin(t)
    return np.array([
        [c, -s, 0.0, 0.0],
        [s, c, 0.0, 0.0],
        [0.0, 0.0, 1.0, 0.0],
        [0.0, 0.0, 0.0, 1.0],
    ])


def to_homogeneous(points):
    """N x 3 array of (x, y, z) points -> 4 x N matrix of columns (x, y, z, 1)."""
    points = np.asarray(points, dtype=float)
    ones = np.ones((points.shape[0], 1))
    return np.hstack([points, ones]).T


def from_homogeneous(columns):
    """4 x N matrix of (x, y, z, w) columns -> N x 3 array of (x/w, y/w, z/w)."""
    return (columns[:3] / columns[3]).T


def apply(matrix, points):
    """Transform every 3D point with one matrix multiplication."""
    return from_homogeneous(matrix @ to_homogeneous(points))


def point_to_text(point, decimals=2):
    values = ", ".join(f"{round(float(v), decimals) + 0.0:.{decimals}f}" for v in point)
    return f"({values})"
