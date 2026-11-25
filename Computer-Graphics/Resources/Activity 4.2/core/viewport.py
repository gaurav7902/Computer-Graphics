"""Viewport2D: maps world coordinates onto pixels of the canvas.

We describe shapes in world coordinates: x increases to the right and y
increases UPWARD, as in mathematics. Screen pixels are different: y
increases DOWNWARD and the origin is the top-left corner.

This mapping is the window-to-viewport transformation from Lecture 3.3:

    xs = xv_min + (x - x_min) / (x_max - x_min) * (xv_max - xv_min)
    ys = yv_max - (y - y_min) / (y_max - y_min) * (yv_max - yv_min)

(y is inverted because screen y grows downward.)
"""

import pygame

from core import theme


class Viewport2D:
    """A world-space window [x_min, x_max] x [y_min, y_max] shown in a screen rect."""

    def __init__(self, screen_rect, units_tall=16.0, centre=(0.0, 0.0)):
        self.rect = pygame.Rect(screen_rect)

        # Choose the world width so one world unit is the same number of pixels
        # horizontally and vertically. Otherwise circles would look like ellipses.
        aspect = self.rect.width / self.rect.height
        units_wide = units_tall * aspect

        cx, cy = centre
        self.x_min, self.x_max = cx - units_wide / 2, cx + units_wide / 2
        self.y_min, self.y_max = cy - units_tall / 2, cy + units_tall / 2

    def zoom(self, factor):
        """Zoom about the centre of the window. factor > 1 zooms in."""
        cx, cy = (self.x_min + self.x_max) / 2, (self.y_min + self.y_max) / 2
        half_w = (self.x_max - self.x_min) / 2 / factor
        half_h = (self.y_max - self.y_min) / 2 / factor
        if not 3 <= half_h <= 25:          # keep the zoom within sensible limits
            return
        self.x_min, self.x_max = cx - half_w, cx + half_w
        self.y_min, self.y_max = cy - half_h, cy + half_h

    @property
    def pixels_per_unit(self):
        return self.rect.height / (self.y_max - self.y_min)

    # -- Converting coordinates ----------------------------------------------

    def world_to_screen(self, x, y):
        """World point (x, y) -> integer pixel position on the window."""
        sx = self.rect.left + (x - self.x_min) / (self.x_max - self.x_min) * self.rect.width
        sy = self.rect.bottom - (y - self.y_min) / (self.y_max - self.y_min) * self.rect.height
        return round(sx), round(sy)

    def points_to_screen(self, points):
        """Convert a list (or N x 2 NumPy array) of world points."""
        return [self.world_to_screen(x, y) for x, y in points]

    def screen_to_world(self, sx, sy):
        """The inverse mapping: a pixel (for example a mouse click) -> world point."""
        x = self.x_min + (sx - self.rect.left) / self.rect.width * (self.x_max - self.x_min)
        y = self.y_min + (self.rect.bottom - sy) / self.rect.height * (self.y_max - self.y_min)
        return x, y

    def contains_pixel(self, position):
        return self.rect.collidepoint(position)

    # -- Drawing the coordinate grid -----------------------------------------

    def draw_grid(self, surface, label_every=2):
        """Draw unit grid lines, the x and y axes, and numbered tick labels."""
        font = theme.fonts().small

        for x in range(int(self.x_min), int(self.x_max) + 1):
            colour = theme.GRID_MAJOR if x % label_every == 0 else theme.GRID
            top = self.world_to_screen(x, self.y_max)
            bottom = self.world_to_screen(x, self.y_min)
            pygame.draw.line(surface, colour, top, bottom)

        for y in range(int(self.y_min), int(self.y_max) + 1):
            colour = theme.GRID_MAJOR if y % label_every == 0 else theme.GRID
            left = self.world_to_screen(self.x_min, y)
            right = self.world_to_screen(self.x_max, y)
            pygame.draw.line(surface, colour, left, right)

        # The axes pass through the world origin (0, 0).
        origin = self.world_to_screen(0, 0)
        pygame.draw.line(surface, theme.AXIS, (self.rect.left, origin[1]), (self.rect.right, origin[1]))
        pygame.draw.line(surface, theme.AXIS, (origin[0], self.rect.top), (origin[0], self.rect.bottom))

        # Tick labels along both axes.
        # Labels right at the edge of the canvas would be cut off, so skip them.
        for x in range(int(self.x_min) + 1, int(self.x_max)):
            if x != 0 and x % label_every == 0:
                sx, sy = self.world_to_screen(x, 0)
                label = font.render(str(x), True, theme.TEXT_FAINT)
                surface.blit(label, (sx - label.get_width() // 2, sy + 4))
        for y in range(int(self.y_min) + 1, int(self.y_max)):
            if y != 0 and y % label_every == 0:
                sx, sy = self.world_to_screen(0, y)
                label = font.render(str(y), True, theme.TEXT_FAINT)
                surface.blit(label, (sx + 5, sy - label.get_height() // 2))

        label = font.render("O", True, theme.TEXT_FAINT)
        surface.blit(label, (origin[0] + 5, origin[1] + 4))
