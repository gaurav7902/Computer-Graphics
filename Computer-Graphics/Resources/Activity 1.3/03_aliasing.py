"""Aliasing and supersampled anti-aliasing comparison.

The left side draws directly at final resolution. The right side draws the
same geometry at a larger off-screen resolution, then smooth-scales it down.
"""

import os
import sys

import pygame


# The visible display size stays fixed so the comparison is easy to discuss.
WIDTH, HEIGHT = 800, 600

# Colours are RGB tuples. The two panels share colours so sampling is the only
# intentional visual difference.
BACKGROUND = (12, 15, 22)
PANEL_BACKGROUND = (18, 23, 33)
PANEL_BORDER = (78, 90, 112)
TEXT = (232, 238, 246)
MUTED_TEXT = (168, 178, 194)
GRID_COLOUR = (28, 32, 42)

LINE_COLOUR = (248, 223, 104)
CIRCLE_COLOUR = (84, 190, 228)
TRIANGLE_COLOUR = (239, 104, 128)

SUPERSAMPLING_FACTORS = [1, 2, 4, 8]


def preview_path_from_args():
    """Return a screenshot path when the script is run in verification mode."""
    if "--preview" in sys.argv:
        index = sys.argv.index("--preview")
        if index + 1 < len(sys.argv):
            return sys.argv[index + 1]
    return None


def save_preview(path, window):
    """Save the current window contents for visual checking."""
    folder = os.path.dirname(path)
    if folder:
        os.makedirs(folder, exist_ok=True)
    pygame.image.save(window, path)


def draw_text(surface, font, text, position, colour=TEXT):
    """Render text as pixels, then copy those pixels onto the surface."""
    image = font.render(text, True, colour)
    surface.blit(image, position)


def scale_point(point, factor):
    """Scale a final-resolution point into supersampled coordinates."""
    return int(round(point[0] * factor)), int(round(point[1] * factor))


def geometry_points(width, height):
    """Return the same scene geometry for any panel size."""
    # Values are fractions of panel width/height so split and full views match.
    line_start = (width * 0.10, height * 0.82)
    line_end = (width * 0.88, height * 0.18)
    circle_center = (width * 0.72, height * 0.68)
    circle_radius = min(width, height) * 0.17
    triangle = [
        (width * 0.17, height * 0.22),
        (width * 0.47, height * 0.12),
        (width * 0.35, height * 0.50),
    ]
    return line_start, line_end, circle_center, circle_radius, triangle


def render_geometry_surface(size, supersampling_factor):
    """Render the same geometry, optionally through a larger off-screen surface."""
    factor = max(1, supersampling_factor)
    width, height = size

    # A factor of 4 means drawing into a surface 4 times wider and 4 times taller.
    # The final display panel size remains unchanged.
    large_size = (width * factor, height * factor)
    surface = pygame.Surface(large_size)
    surface.fill(PANEL_BACKGROUND)

    line_start, line_end, circle_center, circle_radius, triangle = geometry_points(width, height)

    # Primitive coordinates must be scaled by the same amount as the surface.
    scaled_line_start = scale_point(line_start, factor)
    scaled_line_end = scale_point(line_end, factor)
    scaled_circle_center = scale_point(circle_center, factor)
    scaled_radius = int(round(circle_radius * factor))
    scaled_triangle = [scale_point(point, factor) for point in triangle]

    pygame.draw.line(surface, LINE_COLOUR, scaled_line_start, scaled_line_end, max(1, factor))
    pygame.draw.circle(surface, CIRCLE_COLOUR, scaled_circle_center, scaled_radius, max(1, 3 * factor))
    pygame.draw.polygon(surface, TRIANGLE_COLOUR, scaled_triangle)

    # Factor 1 is the aliased case: the surface is already final resolution.
    if factor == 1:
        return surface

    # Smooth scaling estimates intermediate colours near geometric boundaries.
    # It does not add more display pixels; it chooses smoother colours for them.
    return pygame.transform.smoothscale(surface, size)


def diagonal_crop_rect(size):
    """Choose a small final-resolution region along the diagonal line."""
    width, height = size
    line_start, line_end, _, _, _ = geometry_points(width, height)

    # Pick a point partway along the line, then crop a small pixel neighbourhood.
    t = 0.30
    center_x = line_start[0] + (line_end[0] - line_start[0]) * t
    center_y = line_start[1] + (line_end[1] - line_start[1]) * t
    crop_width = 40
    crop_height = 30
    left = int(round(center_x - crop_width / 2))
    top = int(round(center_y - crop_height / 2))
    return pygame.Rect(left, top, crop_width, crop_height)


def draw_pixel_grid(surface, rect, columns, rows):
    """Overlay a grid where each cell corresponds to one source pixel."""
    for column in range(columns + 1):
        x = rect.left + round(column * rect.width / columns)
        pygame.draw.line(surface, GRID_COLOUR, (x, rect.top), (x, rect.bottom), 1)
    for row in range(rows + 1):
        y = rect.top + round(row * rect.height / rows)
        pygame.draw.line(surface, GRID_COLOUR, (rect.left, y), (rect.right, y), 1)


def draw_inset(window, source_surface, target_rect, title, show_grid, font):
    """Magnify a small part of the line so individual pixels are visible."""
    crop_rect = diagonal_crop_rect(source_surface.get_size())
    crop = source_surface.subsurface(crop_rect).copy()

    # Regular scale keeps the source pixel blocks crisp in the magnified inset.
    magnified = pygame.transform.scale(crop, target_rect.size)

    window.blit(magnified, target_rect)
    pygame.draw.rect(window, PANEL_BORDER, target_rect, 1)

    if show_grid:
        draw_pixel_grid(window, target_rect, crop_rect.width, crop_rect.height)

    draw_text(window, font, title, (target_rect.x, target_rect.y - 22), MUTED_TEXT)


def draw_panel(window, rect, title, supersampling_factor, title_font):
    """Render one comparison panel and return its surface for the inset."""
    panel_surface = render_geometry_surface(rect.size, supersampling_factor)
    window.blit(panel_surface, rect)
    pygame.draw.rect(window, PANEL_BORDER, rect, 1)
    title_image = title_font.render(title, True, TEXT)
    title_x = rect.centerx - title_image.get_width() // 2
    window.blit(title_image, (title_x, rect.y - 30))
    return panel_surface


def draw_controls(window, title_font, small_font, supersampling_factor, split_view):
    """Draw the title, keyboard controls, and current sampling settings."""
    mode = "split comparison" if split_view else "full-width alternating"
    draw_text(window, title_font, "Aliasing changes at the sampling step, not in the geometry.", (24, 12))
    draw_text(
        window,
        small_font,
        "G: grid   A: split/full   1/2/4/8: supersampling   Escape: close",
        (24, 38),
        MUTED_TEXT,
    )
    draw_text(
        window,
        small_font,
        f"Supersampling: {supersampling_factor}x   View: {mode}   clock.tick(60) limits program frame rate.",
        (24, 58),
        MUTED_TEXT,
    )


def render_split_view(window, title_font, label_font, show_grid, supersampling_factor):
    """Show aliased and anti-aliased rendering side by side."""
    left_rect = pygame.Rect(52, 102, 300, 300)
    right_rect = pygame.Rect(448, 102, 300, 300)
    left_inset = pygame.Rect(102, 428, 200, 150)
    right_inset = pygame.Rect(498, 428, 200, 150)

    aliased = draw_panel(window, left_rect, "Aliased Rendering", 1, title_font)
    antialiased = draw_panel(window, right_rect, "Anti-aliased Rendering", supersampling_factor, title_font)

    # The insets make the sampling difference visible at individual-pixel scale.
    draw_inset(window, aliased, left_inset, "Aliased line pixels", show_grid, label_font)
    draw_inset(window, antialiased, right_inset, "Anti-aliased line pixels", show_grid, label_font)


def render_full_view(window, title_font, label_font, show_grid, supersampling_factor):
    """Use the full width and alternate between aliased and anti-aliased views."""
    ticks = pygame.time.get_ticks()

    # The alternating view changes automatically so the edge treatment is easy to compare.
    show_antialiased = (ticks // 900) % 2 == 1
    factor = supersampling_factor if show_antialiased else 1
    title = "Anti-aliased Rendering" if show_antialiased else "Aliased Rendering"

    panel_rect = pygame.Rect(60, 102, 680, 310)
    inset_rect = pygame.Rect(300, 428, 200, 150)

    panel_surface = draw_panel(window, panel_rect, title, factor, title_font)
    draw_inset(window, panel_surface, inset_rect, f"{title} inset", show_grid, label_font)


def render_frame(window, title_font, label_font, small_font, show_grid, supersampling_factor, split_view):
    """Clear the window, draw the selected comparison view, and present it."""
    window.fill(BACKGROUND)
    draw_controls(window, title_font, small_font, supersampling_factor, split_view)

    if split_view:
        render_split_view(window, title_font, label_font, show_grid, supersampling_factor)
    else:
        render_full_view(window, title_font, label_font, show_grid, supersampling_factor)

    pygame.display.flip()


def main():
    preview_path = preview_path_from_args()

    pygame.init()
    pygame.display.set_caption("Activity 1.3 - Aliasing and anti-aliasing")
    window = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()

    title_font = pygame.font.SysFont(None, 26)
    label_font = pygame.font.SysFont(None, 21)
    small_font = pygame.font.SysFont(None, 19)

    # These are the interactive state variables changed by keyboard events.
    show_grid = True
    split_view = True
    supersampling_factor = 4

    # The preview path is used by automated checks to render one complete frame.
    if preview_path:
        render_frame(window, title_font, label_font, small_font, show_grid, supersampling_factor, split_view)
        save_preview(preview_path, window)
        pygame.quit()
        return

    running = True
    while running:
        # 1. Handle events: close, toggles, and supersampling factor changes.
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_g:
                    show_grid = not show_grid
                elif event.key == pygame.K_a:
                    split_view = not split_view
                elif event.unicode in ("1", "2", "4", "8"):
                    supersampling_factor = int(event.unicode)

        # 2 and 3. Prepare the image, then present the completed frame.
        render_frame(window, title_font, label_font, small_font, show_grid, supersampling_factor, split_view)

        # 4. Optionally limit how fast this program repeats the loop.
        # This limits this program's frame rate; it does not change monitor refresh rate.
        clock.tick(60)

    pygame.quit()


if __name__ == "__main__":
    main()
