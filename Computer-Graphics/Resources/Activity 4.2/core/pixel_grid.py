"""PixelGrid: a magnified raster where every pixel is drawn as a large square.

Used by demos about scan conversion and Z-buffering, where seeing the
individual pixels is the whole point.

Pixel (x, y) has integer coordinates and y increases UPWARD, as in the
lecture's figures. Its centre is at the grid point (x, y), and the square
it covers runs from x - 0.5 to x + 0.5.
"""

import pygame

from core import theme
from core.draw_utils import draw_text


class PixelGrid:
    def __init__(self, rect, x_range, y_range, margin=36):
        """x_range and y_range are inclusive integer ranges, for example (0, 12)."""
        self.rect = pygame.Rect(rect)
        self.x_min, self.x_max = x_range
        self.y_min, self.y_max = y_range
        columns = self.x_max - self.x_min + 1
        rows = self.y_max - self.y_min + 1

        # Square cells, as large as will fit, with room for axis labels.
        self.cell = min((self.rect.width - 2 * margin) // columns, (self.rect.height - 2 * margin) // rows)
        grid_width, grid_height = self.cell * columns, self.cell * rows
        self.left = self.rect.left + (self.rect.width - grid_width) // 2
        self.top = self.rect.top + (self.rect.height - grid_height) // 2
        self.grid_rect = pygame.Rect(self.left, self.top, grid_width, grid_height)

    # -- Converting coordinates ----------------------------------------------

    def to_screen(self, x, y):
        """Continuous grid coordinates -> screen pixel. Integer (x, y) is a pixel centre."""
        sx = self.left + (x - self.x_min + 0.5) * self.cell
        sy = self.top + (self.y_max - y + 0.5) * self.cell
        return round(sx), round(sy)

    def cell_rect(self, x, y):
        sx, sy = self.to_screen(x, y)
        half = self.cell // 2
        return pygame.Rect(sx - half, sy - half, self.cell, self.cell)

    def pixel_at(self, position):
        """Which pixel is under a screen position (for example the mouse)? None if outside."""
        if not self.grid_rect.collidepoint(position):
            return None
        x = self.x_min + (position[0] - self.left) // self.cell
        y = self.y_max - (position[1] - self.top) // self.cell
        return int(x), int(y)

    def contains(self, x, y):
        return self.x_min <= x <= self.x_max and self.y_min <= y <= self.y_max

    # -- Drawing ---------------------------------------------------------------

    def fill(self, surface, x, y, colour, inset=1):
        if self.contains(x, y):
            pygame.draw.rect(surface, colour, self.cell_rect(x, y).inflate(-2 * inset, -2 * inset), border_radius=3)

    def outline(self, surface, x, y, colour, width=2):
        if self.contains(x, y):
            pygame.draw.rect(surface, colour, self.cell_rect(x, y), width, border_radius=3)

    def draw_grid(self, surface, label_every=1, show_centres=True):
        """Cell borders, a dot at every pixel centre, and coordinate labels."""
        font = theme.fonts().small
        for x in range(self.x_min, self.x_max + 2):
            sx = self.left + (x - self.x_min) * self.cell
            pygame.draw.line(surface, theme.GRID_MAJOR, (sx, self.top), (sx, self.grid_rect.bottom))
        for y in range(self.y_min, self.y_max + 2):
            sy = self.top + (y - self.y_min) * self.cell
            pygame.draw.line(surface, theme.GRID_MAJOR, (self.left, sy), (self.grid_rect.right, sy))

        if show_centres:
            for x in range(self.x_min, self.x_max + 1):
                for y in range(self.y_min, self.y_max + 1):
                    pygame.draw.circle(surface, theme.GRID_MAJOR, self.to_screen(x, y), 2)

        for x in range(self.x_min, self.x_max + 1):
            if x % label_every == 0:
                sx, _ = self.to_screen(x, self.y_min)
                draw_text(surface, str(x), (sx, self.grid_rect.bottom + 12), theme.TEXT_FAINT, font, centre=True)
        for y in range(self.y_min, self.y_max + 1):
            if y % label_every == 0:
                _, sy = self.to_screen(self.x_min, y)
                draw_text(surface, str(y), (self.left - 14, sy), theme.TEXT_FAINT, font, centre=True)
