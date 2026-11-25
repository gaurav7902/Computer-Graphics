"""The Phong local illumination model (Lecture 3.4).

    I = ka·Ia + kd·Il·max(0, N·L) + ks·Il·max(0, R·V)^n
        ambient   diffuse             specular

N, L, V and R are unit vectors starting at the surface point P:
    N  surface normal
    L  towards the light
    V  towards the viewer
    R  the mirror reflection of L about N

Every function here works on single vectors AND on whole NumPy arrays of
vectors (one per row), so the shading demo can light thousands of pixels in
one call. That is why dot() sums over the last axis.
"""

from dataclasses import dataclass

import numpy as np


@dataclass
class Material:
    ka: float = 0.2       # ambient coefficient
    kd: float = 0.6       # diffuse coefficient
    ks: float = 0.3       # specular coefficient
    n: float = 4.0        # shininess exponent


@dataclass
class LightSettings:
    Ia: float = 0.5       # ambient light intensity
    Il: float = 1.0       # light-source intensity
    ambient_on: bool = True
    diffuse_on: bool = True
    specular_on: bool = True


def dot(a, b):
    """Dot product over the last axis: works for one vector or a stack of them."""
    return np.sum(np.asarray(a) * np.asarray(b), axis=-1)


def normalise(v):
    v = np.asarray(v, dtype=float)
    length = np.linalg.norm(v, axis=-1, keepdims=True)
    return v / np.where(length == 0, 1.0, length)


def reflect(L, N):
    """Slide 'Where Would Perfect Reflection Go?': R = 2(N·L)N - L."""
    n_dot_l = dot(N, L)[..., np.newaxis]
    return 2.0 * n_dot_l * np.asarray(N) - np.asarray(L)


def phong_terms(N, L, V, material, light):
    """Return the three contributions (ambient, diffuse, specular) separately."""
    N, L, V = normalise(N), normalise(L), normalise(V)
    n_dot_l = dot(N, L)
    R = reflect(L, N)
    r_dot_v = dot(R, V)

    ambient = material.ka * light.Ia * np.ones_like(n_dot_l)
    diffuse = material.kd * light.Il * np.maximum(0.0, n_dot_l)
    specular = material.ks * light.Il * np.maximum(0.0, r_dot_v) ** material.n

    # A light behind the surface (N·L <= 0) cannot make a highlight either.
    specular = np.where(n_dot_l > 0.0, specular, 0.0)

    if not light.ambient_on:
        ambient = ambient * 0.0
    if not light.diffuse_on:
        diffuse = diffuse * 0.0
    if not light.specular_on:
        specular = specular * 0.0
    return ambient, diffuse, specular


def phong_intensity(N, L, V, material, light):
    """The local illumination model: the sum of the three terms."""
    ambient, diffuse, specular = phong_terms(N, L, V, material, light)
    return ambient + diffuse + specular


def phong_from_dots(n_dot_l, r_dot_v, material, light):
    """The same model written with the two dot products given directly.

    Useful for checking the lecture's worked example, where N·L = 0.8 and
    R·V = 0.9 are given as numbers.
    """
    ambient = material.ka * light.Ia
    diffuse = material.kd * light.Il * max(0.0, n_dot_l)
    specular = material.ks * light.Il * max(0.0, r_dot_v) ** material.n
    return ambient, diffuse, specular
