"""Viewing and projection (Lecture 3.2).

Conventions, as in the lecture:
    camera space: x = right, y = up, z = forward (into the scene)
    points in front of the camera have POSITIVE camera-space z

Pipeline covered here:

    world point Pw --V--> camera point Pc --Q--> homogeneous image point --÷w--> (x', y')
"""

import numpy as np


def normalise(v):
    v = np.asarray(v, dtype=float)
    return v / np.linalg.norm(v)


class Camera:
    """A camera described by eye E, target C and an approximate up direction a."""

    def __init__(self, eye, target, up=(0.0, 1.0, 0.0)):
        self.eye = np.asarray(eye, dtype=float)
        self.target = np.asarray(target, dtype=float)
        self.up = np.asarray(up, dtype=float)

    def axes(self):
        """Slide 'Constructing the Camera Axes'. Returns (r, u, f), all unit vectors.

            f = (C - E) / |C - E|        forward
            r = (a × f) / |a × f|        right
            u = f × r                    corrected up

        This needs C != E, and a must not be parallel to f.
        """
        f = normalise(self.target - self.eye)
        r = normalise(np.cross(self.up, f))
        u = np.cross(f, r)
        return r, u, f

    def view_matrix(self):
        """Slide 'The View Matrix'. Each camera axis becomes one row.

            [ rx  ry  rz  -r·E ]
        V = [ ux  uy  uz  -u·E ]
            [ fx  fy  fz  -f·E ]
            [  0   0   0    1  ]
        """
        r, u, f = self.axes()
        e = self.eye
        return np.array([
            [r[0], r[1], r[2], -np.dot(r, e)],
            [u[0], u[1], u[2], -np.dot(u, e)],
            [f[0], f[1], f[2], -np.dot(f, e)],
            [0.0, 0.0, 0.0, 1.0],
        ])

    def world_to_camera(self, points):
        """Apply V to an N x 3 array of world points; returns N x 3 camera points."""
        points = np.asarray(points, dtype=float)
        homogeneous = np.hstack([points, np.ones((len(points), 1))]).T
        return (self.view_matrix() @ homogeneous)[:3].T


# ---------------------------------------------------------------------------
# Projection
# ---------------------------------------------------------------------------

def orthographic_matrix():
    """Slide 'Orthographic Projection': x' = x, y' = y.

    z is kept in the third row (it is useful later for depth testing), and
    w stays 1, so the divide changes nothing.
    """
    return np.eye(4)


def perspective_matrix(d):
    """Slide 'Making Perspective Fit the Matrix Pipeline'.

        [ d 0 0 0 ]   [x]   [d·x]
    Q = [ 0 d 0 0 ] · [y] = [d·y]
        [ 0 0 1 0 ]   [z]   [ z ]
        [ 0 0 1 0 ]   [1]   [ z ]  <- w = z stores the depth
    """
    return np.array([
        [d, 0.0, 0.0, 0.0],
        [0.0, d, 0.0, 0.0],
        [0.0, 0.0, 1.0, 0.0],
        [0.0, 0.0, 1.0, 0.0],
    ])


def project(camera_points, projection):
    """Project N x 3 camera-space points.

    Returns (image_xy, homogeneous):
        homogeneous  N x 4 rows (x_h, y_h, z_h, w_h) straight after the matrix
        image_xy     N x 2 rows (x_h / w_h, y_h / w_h) after the divide
    """
    camera_points = np.asarray(camera_points, dtype=float)
    columns = np.hstack([camera_points, np.ones((len(camera_points), 1))]).T
    homogeneous = (projection @ columns).T
    # Points with w = 0 (z = 0 in perspective) cannot be divided. Clipping
    # (Lecture 3.3) removes them before this matters, so silence the warning.
    with np.errstate(divide="ignore", invalid="ignore"):
        image_xy = homogeneous[:, :2] / homogeneous[:, 3:4]
    return image_xy, homogeneous
