"""2D transformation matrices in homogeneous coordinates (Lecture 3.1).

This file is pure mathematics: it uses NumPy and no Pygame at all.

A 2D point (x, y) is written as the column vector (x, y, 1). With that extra
1, every transformation, including translation, is a single 3 x 3 matrix:

    P' = M @ P            (@ is NumPy's matrix multiplication operator)

A whole shape is moved at once by stacking its points as the COLUMNS of a
3 x N matrix and multiplying once:

    [x1' x2' ... xN']       [x1 x2 ... xN]
    [y1' y2' ... yN']  = M  [y1 y2 ... yN]
    [ 1   1  ...  1 ]       [ 1  1 ...  1]
"""

import numpy as np


# ---------------------------------------------------------------------------
# The basic transformations (one function per slide)
# ---------------------------------------------------------------------------

def identity():
    """The 'do nothing' transformation: I @ P == P."""
    return np.eye(3)


def translate(tx, ty):
    """Slide 'Translation in Matrix Form': the displacement goes in the last column."""
    return np.array([
        [1.0, 0.0, tx],
        [0.0, 1.0, ty],
        [0.0, 0.0, 1.0],
    ])


def scale(sx, sy):
    """Slide 'Scaling in Matrix Form': the scale factors go on the diagonal."""
    return np.array([
        [sx, 0.0, 0.0],
        [0.0, sy, 0.0],
        [0.0, 0.0, 1.0],
    ])


def rotate(theta_degrees):
    """Slide 'Rotation in Matrix Form': counter-clockwise about the origin.

    NumPy's trigonometric functions expect radians, so we convert first.
    """
    t = np.radians(theta_degrees)
    c, s = np.cos(t), np.sin(t)
    return np.array([
        [c, -s, 0.0],
        [s, c, 0.0],
        [0.0, 0.0, 1.0],
    ])


def reflect_across_x_axis():
    """Mirror across the x-axis: x' = x, y' = -y."""
    return scale(1.0, -1.0)


def reflect_across_y_axis():
    """Mirror across the y-axis: x' = -x, y' = y."""
    return scale(-1.0, 1.0)


def shear_x(k):
    """Slide 'Shear in Matrix Form': horizontal shear, x' = x + k*y, y' = y."""
    return np.array([
        [1.0, k, 0.0],
        [0.0, 1.0, 0.0],
        [0.0, 0.0, 1.0],
    ])


# ---------------------------------------------------------------------------
# Combining transformations
# ---------------------------------------------------------------------------

def compose(*matrices_in_order_applied):
    """Combine transformations, listed in the order they are APPLIED.

    compose(M1, M2, M3) returns M3 @ M2 @ M1.

    With column vectors the RIGHTMOST matrix acts first (slide 'Combining
    Transformations'). Listing steps in the order they happen and building
    the product here avoids that common source of mistakes.
    """
    # Works for 3 x 3 (2D) and 4 x 4 (3D) matrices alike: start from an
    # identity of the same size as the matrices we were given.
    size = matrices_in_order_applied[0].shape[0] if matrices_in_order_applied else 3
    result = np.eye(size)
    for matrix in matrices_in_order_applied:
        result = matrix @ result      # each new step multiplies on the LEFT
    return result


def rotate_about_point(theta_degrees, a, b):
    """Rotate about the pivot C = (a, b) (slide 'Rotation About an Arbitrary Point').

    1. translate by (-a, -b) so C moves to the origin
    2. rotate by theta about the origin
    3. translate by (a, b) to put C back

    M = T(a, b) @ R(theta) @ T(-a, -b)
    """
    return compose(translate(-a, -b), rotate(theta_degrees), translate(a, b))


# ---------------------------------------------------------------------------
# Applying a matrix to points
# ---------------------------------------------------------------------------

def to_homogeneous(points):
    """N x 2 array of (x, y) points -> 3 x N matrix of columns (x, y, 1)."""
    points = np.asarray(points, dtype=float)       # shape (N, 2)
    ones = np.ones((points.shape[0], 1))           # shape (N, 1)
    return np.hstack([points, ones]).T             # (N, 3) transposed -> (3, N)


def from_homogeneous(columns):
    """3 x N matrix of (x, y, w) columns -> N x 2 array of (x/w, y/w) points.

    For the affine transformations in this lecture w stays 1, so dividing
    changes nothing. The division matters in Lecture 3.2 (perspective).
    """
    return (columns[:2] / columns[2]).T


def apply(matrix, points):
    """Transform every point with one matrix multiplication."""
    return from_homogeneous(matrix @ to_homogeneous(points))


# ---------------------------------------------------------------------------
# Text helpers for showing values in the info panel
# ---------------------------------------------------------------------------

def clean(value, decimals=2):
    """Round a number for display. Adding 0.0 turns -0.0 into 0.0."""
    return round(float(value), decimals) + 0.0


def matrix_to_lines(matrix, decimals=2, width=7):
    """Format a matrix as aligned text rows, for example '[  1.00   0.00   3.00 ]'."""
    lines = []
    for row in np.asarray(matrix):
        cells = "".join(f"{clean(v, decimals):{width}.{decimals}f}" for v in row)
        lines.append(f"[{cells} ]")
    return lines


def point_to_text(point, decimals=2):
    x, y = point
    return f"({clean(x, decimals):.{decimals}f}, {clean(y, decimals):.{decimals}f})"
