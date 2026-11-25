"""Small drawing helpers shared by the demos.

These are only for drawing labels and overlays. When a lecture is about how
pixels are chosen (scan conversion, for example), the demo uses its own
algorithm instead of these helpers.
"""

import math

import pygame

from core import theme


def draw_text(surface, text, position, colour=theme.TEXT, font=None, centre=False):
    """Draw one line of text. Returns the rectangle it covers."""
    font = font or theme.fonts().body
    image = font.render(text, True, colour)
    rect = image.get_rect()
    if centre:
        rect.center = position
    else:
        rect.topleft = position
    surface.blit(image, rect)
    return rect


def draw_filled_polygon(surface, points, colour, fill_alpha=70, width=2):
    """Draw a polygon with a see-through fill and a solid outline.

    Pygame's draw functions cannot blend colours, so the fill is drawn on a
    separate transparent surface and then blended (blitted) on top.
    """
    if len(points) < 3:
        return
    # Only make the transparent layer as large as the polygon's bounding box.
    xs = [x for x, _ in points]
    ys = [y for _, y in points]
    left, top = min(xs), min(ys)
    size = (max(xs) - left + 1, max(ys) - top + 1)
    layer = pygame.Surface(size, pygame.SRCALPHA)
    local_points = [(x - left, y - top) for x, y in points]
    pygame.draw.polygon(layer, (*colour, fill_alpha), local_points)
    surface.blit(layer, (left, top))
    pygame.draw.polygon(surface, colour, points, width)


def draw_dashed_polygon(surface, points, colour, dash=8, gap=6):
    """Draw a polygon outline with dashed edges (used for 'before' shapes)."""
    for i in range(len(points)):
        draw_dashed_line(surface, points[i], points[(i + 1) % len(points)], colour, dash, gap)


def draw_dashed_line(surface, start, end, colour, dash=8, gap=6, width=1):
    x1, y1 = start
    x2, y2 = end
    length = math.hypot(x2 - x1, y2 - y1)
    if length == 0:
        return
    step = dash + gap
    for d in range(0, int(length), step):
        t1 = d / length
        t2 = min(d + dash, length) / length
        a = (x1 + (x2 - x1) * t1, y1 + (y2 - y1) * t1)
        b = (x1 + (x2 - x1) * t2, y1 + (y2 - y1) * t2)
        pygame.draw.line(surface, colour, a, b, width)


def draw_arrow(surface, start, end, colour, width=2, head=10):
    """Draw a straight arrow from start to end."""
    pygame.draw.line(surface, colour, start, end, width)
    angle = math.atan2(end[1] - start[1], end[0] - start[0])
    for side in (-1, 1):
        tip_angle = angle + math.pi + side * math.radians(25)
        tip = (end[0] + head * math.cos(tip_angle), end[1] + head * math.sin(tip_angle))
        pygame.draw.line(surface, colour, end, tip, width)


def draw_marker(surface, position, colour, label=None, radius=5, label_offset=(8, -20)):
    """Draw a dot with an optional text label beside it (above-right by default)."""
    pygame.draw.circle(surface, colour, position, radius)
    pygame.draw.circle(surface, theme.BACKGROUND, position, radius, 1)
    if label:
        x, y = position[0] + label_offset[0], position[1] + label_offset[1]
        draw_text(surface, label, (x, y), colour, theme.fonts().small)


def draw_cross(surface, position, colour, size=7, width=2):
    """Draw an X marker, for example to show a pivot point."""
    x, y = position
    pygame.draw.line(surface, colour, (x - size, y - size), (x + size, y + size), width)
    pygame.draw.line(surface, colour, (x - size, y + size), (x + size, y - size), width)


def draw_legend(surface, rect, entries, corner="left"):
    """Draw a small key in the bottom-left (or bottom-right) corner of rect.

    entries is a list of (colour, text) pairs.
    """
    font = theme.fonts().small
    line_height = font.get_linesize() + 4
    width = max(font.size(text)[0] for _, text in entries) + 44
    height = line_height * len(entries) + 12
    left = rect.left + 12 if corner == "left" else rect.right - width - 12
    box = pygame.Rect(left, rect.bottom - height - 12, width, height)

    layer = pygame.Surface(box.size, pygame.SRCALPHA)
    layer.fill((*theme.PANEL, 220))
    surface.blit(layer, box.topleft)
    pygame.draw.rect(surface, theme.PANEL_BORDER, box, 1, border_radius=4)

    y = box.top + 8
    for colour, text in entries:
        pygame.draw.line(surface, colour, (box.left + 10, y + 8), (box.left + 28, y + 8), 3)
        draw_text(surface, text, (box.left + 36, y), theme.TEXT_DIM, font)
        y += line_height


def blit_array(surface, pixels, rect, smooth=False):
    """Show a NumPy image (H x W x 3, uint8) scaled to fill rect.

    As in Activity 1.3: NumPy images are indexed [y, x], while Pygame
    surfaces are [x, y], so the array is transposed before display.
    Without smoothing each array pixel becomes a crisp block on screen.
    """
    image = pygame.surfarray.make_surface(pixels.transpose(1, 0, 2))
    scale = pygame.transform.smoothscale if smooth else pygame.transform.scale
    surface.blit(scale(image, rect.size), rect.topleft)
