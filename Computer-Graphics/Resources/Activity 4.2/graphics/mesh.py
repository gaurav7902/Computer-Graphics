"""Simple polygon meshes built from triangles (used by Lectures 3.4 and 3.5 demos).

A mesh is two NumPy arrays:
    vertices  V x 3 float array, one (x, y, z) per row
    faces     F x 3 int array, three vertex indices per triangle,
              listed counter-clockwise when seen from outside
"""

from dataclasses import dataclass

import numpy as np


@dataclass
class Mesh:
    vertices: np.ndarray
    faces: np.ndarray
    vertex_normals: np.ndarray

    def face_normals(self):
        """One normal per triangle, from the cross product of two edges."""
        a = self.vertices[self.faces[:, 0]]
        b = self.vertices[self.faces[:, 1]]
        c = self.vertices[self.faces[:, 2]]
        normals = np.cross(b - a, c - a)
        return normals / np.linalg.norm(normals, axis=1, keepdims=True)


def uv_sphere(radius=1.0, stacks=8, slices=12):
    """A sphere made of flat triangles. Fewer stacks/slices -> more visible facets."""
    vertices = []
    for i in range(stacks + 1):
        phi = np.pi * i / stacks                    # 0 at the north pole, pi at the south
        for j in range(slices):
            theta = 2 * np.pi * j / slices
            vertices.append((np.sin(phi) * np.cos(theta), np.cos(phi), np.sin(phi) * np.sin(theta)))
    vertices = np.array(vertices) * radius

    faces = []
    for i in range(stacks):
        for j in range(slices):
            a = i * slices + j
            b = i * slices + (j + 1) % slices
            c = (i + 1) * slices + j
            d = (i + 1) * slices + (j + 1) % slices
            if i != 0:
                faces.append((a, b, c))
            if i != stacks - 1:
                faces.append((b, d, c))
    faces = np.array(faces)

    # On a sphere centred at the origin the true normal points straight out.
    vertex_normals = vertices / np.linalg.norm(vertices, axis=1, keepdims=True)
    mesh = Mesh(vertices, faces, vertex_normals)

    # Make every triangle counter-clockwise when seen from outside.
    centres = vertices[faces].mean(axis=1)
    flip = np.sum(mesh.face_normals() * centres, axis=1) < 0
    faces[flip] = faces[flip][:, [0, 2, 1]]
    return mesh


def cube(size=1.0):
    """An axis-aligned cube centred at the origin, 12 triangles."""
    s = size / 2
    vertices = np.array([
        (-s, -s, -s), (s, -s, -s), (s, s, -s), (-s, s, -s),
        (-s, -s, s), (s, -s, s), (s, s, s), (-s, s, s),
    ])
    faces = np.array([
        (0, 3, 2), (0, 2, 1),      # z = -s
        (4, 5, 6), (4, 6, 7),      # z = +s
        (0, 1, 5), (0, 5, 4),      # y = -s
        (3, 7, 6), (3, 6, 2),      # y = +s
        (0, 4, 7), (0, 7, 3),      # x = -s
        (1, 2, 6), (1, 6, 5),      # x = +s
    ])
    vertex_normals = vertices / np.linalg.norm(vertices, axis=1, keepdims=True)
    mesh = Mesh(vertices, faces, vertex_normals)
    centres = vertices[faces].mean(axis=1)
    flip = np.sum(mesh.face_normals() * centres, axis=1) < 0
    faces[flip] = faces[flip][:, [0, 2, 1]]
    return mesh


CUBE_EDGES = [(0, 1), (1, 2), (2, 3), (3, 0), (4, 5), (5, 6), (6, 7), (7, 4),
              (0, 4), (1, 5), (2, 6), (3, 7)]
