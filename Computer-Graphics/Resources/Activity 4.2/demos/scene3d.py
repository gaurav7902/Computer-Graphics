"""OrbitView: shows a 3D scene on the canvas through a camera you can orbit.

This is only for DISPLAYING 3D demos. It uses the viewing and perspective
projection from Lecture 3.2 (graphics/camera.py) to turn world points into
canvas pixels. Dragging the mouse moves this display camera around the
scene; it never changes the objects themselves.
"""

import math

import numpy as np
import pygame

from core import theme
from core.draw_utils import draw_text
from graphics.camera import Camera, perspective_matrix, project


class OrbitView:
    def __init__(self, rect, target=(0.5, 0.5, 0.5), distance=13.0, yaw=-35.0, pitch=25.0, fov=50.0):
        self.rect = pygame.Rect(rect)
        self.target = np.asarray(target, dtype=float)
        self.distance, self.yaw, self.pitch = distance, yaw, pitch
        self.fov = fov
        self.dragging = False
        self.last_mouse = None

    # -- The display camera ------------------------------------------------------

    def camera(self):
        """Place the eye on a sphere around the target, from yaw and pitch angles."""
        yaw, pitch = math.radians(self.yaw), math.radians(self.pitch)
        offset = np.array([math.cos(pitch) * math.sin(yaw), math.sin(pitch), -math.cos(pitch) * math.cos(yaw)])
        return Camera(self.target + self.distance * offset, self.target)

    def to_screen(self, points):
        """World points (N x 3) -> (screen positions N x 2, camera depth N).

        Steps: view matrix V, perspective matrix Q with d = 1, divide by w,
        then map the image plane onto the canvas (y flipped for the screen).
        """
        camera_points = self.camera().world_to_camera(points)
        image_xy, _ = project(camera_points, perspective_matrix(1.0))
        pixels_per_unit = self.rect.height / (2 * math.tan(math.radians(self.fov) / 2))
        sx = self.rect.centerx + image_xy[:, 0] * pixels_per_unit
        sy = self.rect.centery - image_xy[:, 1] * pixels_per_unit
        return np.stack([sx, sy], axis=1), camera_points[:, 2]

    # -- Mouse -----------------------------------------------------------------------

    def handle_event(self, event, blocked_rects=()):
        """Left-drag orbits; the wheel moves closer or further. Returns True if used."""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos) and not any(r.collidepoint(event.pos) for r in blocked_rects):
                self.dragging, self.last_mouse = True, event.pos
                return True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.dragging = False
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            dx, dy = event.pos[0] - self.last_mouse[0], event.pos[1] - self.last_mouse[1]
            self.yaw -= dx * 0.4
            self.pitch = max(-85.0, min(85.0, self.pitch + dy * 0.4))
            self.last_mouse = event.pos
            return True
        elif event.type == pygame.MOUSEWHEEL:
            self.distance = max(4.0, min(40.0, self.distance * (0.9 if event.y > 0 else 1.1)))
            return True
        return False

    # -- Drawing helpers ----------------------------------------------------------------

    def draw_segment(self, surface, a, b, colour, width=1):
        """Draw one 3D line segment, skipping it if either end is behind the camera."""
        (pa, pb), depth = self.to_screen(np.array([a, b]))
        if depth.min() > 0.1:
            pygame.draw.line(surface, colour, pa, pb, width)

    def draw_edges(self, surface, points, edges, colour, width=2):
        screen, depth = self.to_screen(points)
        for i, j in edges:
            if depth[i] > 0.1 and depth[j] > 0.1:
                pygame.draw.line(surface, colour, screen[i], screen[j], width)

    def draw_point(self, surface, point, colour, label=None, radius=5):
        (p,), (z,) = self.to_screen(np.array([point]))
        if z > 0.1:
            pygame.draw.circle(surface, colour, p, radius)
            if label:
                draw_text(surface, label, (p[0] + 8, p[1] - 20), colour, theme.fonts().small)

    def draw_floor_and_axes(self, surface, size=6, highlight_axis=None):
        """A faint grid on the plane y = 0, plus the x (red), y (green) and z (blue) axes."""
        for i in range(-size, size + 1):
            self.draw_segment(surface, (i, 0, -size), (i, 0, size), theme.GRID)
            self.draw_segment(surface, (-size, 0, i), (size, 0, i), theme.GRID)
        axes = [("x", (1, 0, 0), theme.RED), ("y", (0, 1, 0), theme.GREEN), ("z", (0, 0, 1), theme.BLUE)]
        for name, direction, colour in axes:
            end = np.array(direction) * size
            width = 4 if name == highlight_axis else 2
            self.draw_segment(surface, (0, 0, 0), end, colour, width)
            self.draw_point(surface, end, colour, name, radius=3)
