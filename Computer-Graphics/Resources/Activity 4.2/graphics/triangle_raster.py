"""Filling triangles into a framebuffer, with a Z-buffer (Lectures 3.4 and 3.5).

Coverage test
    A pixel is covered when its CENTRE (x + 0.5, y + 0.5) lies inside the
    triangle. We test this with three "edge functions": the sign tells which
    side of an edge a point is on (the same idea as the implicit-function sign
    test used for the midpoint circle in Lecture 3.5). The covered pixels on
    each row form one span, just like scan-line filling.

Interpolation
    The edge functions also give barycentric weights (w0, w1, w2) that add up
    to 1. Any per-vertex value (depth, colour, normal) is interpolated as
        value = w0·value0 + w1·value1 + w2·value2
    This is how Gouraud shading spreads vertex colours and how Phong shading
    spreads vertex normals across the triangle.

Depth test (Lecture 3.4, 'The Z-Buffer Idea')
    Keep a fragment only if z_new < z_stored, then update colour AND depth.

Everything is vectorised with NumPy: a whole triangle's pixels are handled
by array operations instead of a Python loop over pixels.
"""

from dataclasses import dataclass

import numpy as np


class FrameBuffer:
    """A colour buffer (H x W x 3, values 0..1) and a depth buffer (H x W)."""

    def __init__(self, width, height, background=(0.0, 0.0, 0.0), far_depth=np.inf):
        self.width, self.height = width, height
        self.background = np.asarray(background, dtype=float)
        # The depth an empty pixel starts with. The lecture uses 1.0 (the far
        # end of a 0..1 depth range); np.inf means "nothing drawn yet".
        self.far_depth = far_depth
        self.clear()

    def clear(self):
        self.colour = np.empty((self.height, self.width, 3))
        self.colour[:, :] = self.background
        self.depth = np.full((self.height, self.width), float(self.far_depth))

    def to_uint8(self):
        """Colours as 0..255 integers, ready to show on screen."""
        return (np.clip(self.colour, 0.0, 1.0) * 255 + 0.5).astype(np.uint8)


@dataclass
class FragmentReport:
    """What happened to every fragment of one triangle (for the Z-buffer demo)."""
    rows: np.ndarray
    cols: np.ndarray
    depth: np.ndarray
    accepted: np.ndarray


def rasterize_triangle(buffer, screen_xy, depth, attributes, shade, depth_test=True):
    """Fill one triangle.

    buffer      FrameBuffer to draw into
    screen_xy   3 x 2 array: the vertices in pixel coordinates (x right, y down)
    depth       3 values: camera-space depth at each vertex (smaller = nearer)
    attributes  3 x k array: any per-vertex values to interpolate
    shade       function (m x k interpolated attributes) -> (m x 3 colours)
    depth_test  False draws in arrival order (no Z-buffer), for comparison

    Returns a FragmentReport.
    """
    v0, v1, v2 = np.asarray(screen_xy, dtype=float)
    depth = np.asarray(depth, dtype=float)
    attributes = np.asarray(attributes, dtype=float)

    def edge(a, b, px, py):
        """Positive on one side of the line a -> b, negative on the other."""
        return (b[0] - a[0]) * (py - a[1]) - (b[1] - a[1]) * (px - a[0])

    area = edge(v0, v1, v2[0], v2[1])
    empty = FragmentReport(np.array([], int), np.array([], int), np.array([]), np.array([], bool))
    if abs(area) < 1e-9:
        return empty                      # degenerate (zero-area) triangle

    # Only test pixels inside the triangle's bounding box, clamped to the buffer.
    x_lo = max(int(np.floor(min(v0[0], v1[0], v2[0]))), 0)
    x_hi = min(int(np.ceil(max(v0[0], v1[0], v2[0]))), buffer.width - 1)
    y_lo = max(int(np.floor(min(v0[1], v1[1], v2[1]))), 0)
    y_hi = min(int(np.ceil(max(v0[1], v1[1], v2[1]))), buffer.height - 1)
    if x_lo > x_hi or y_lo > y_hi:
        return empty

    # Pixel centres of the box, as two 2D arrays (one entry per pixel).
    px, py = np.meshgrid(np.arange(x_lo, x_hi + 1) + 0.5, np.arange(y_lo, y_hi + 1) + 0.5)

    # Barycentric weights. Dividing by the signed area makes them positive
    # inside the triangle, whichever way round its vertices are listed.
    w0 = edge(v1, v2, px, py) / area
    w1 = edge(v2, v0, px, py) / area
    w2 = edge(v0, v1, px, py) / area
    inside = (w0 >= 0) & (w1 >= 0) & (w2 >= 0)

    local_rows, local_cols = np.nonzero(inside)
    rows, cols = local_rows + y_lo, local_cols + x_lo
    w = np.stack([w0[inside], w1[inside], w2[inside]], axis=1)     # m x 3

    z = w @ depth                                                 # interpolated depth
    if depth_test:
        accepted = z < buffer.depth[rows, cols]
    else:
        accepted = np.ones(len(z), dtype=bool)

    if np.any(accepted):
        values = w[accepted] @ attributes                         # m x k
        buffer.colour[rows[accepted], cols[accepted]] = shade(values)
        buffer.depth[rows[accepted], cols[accepted]] = z[accepted]

    return FragmentReport(rows, cols, z, accepted)
