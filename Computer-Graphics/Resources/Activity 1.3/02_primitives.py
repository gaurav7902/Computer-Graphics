"""A clean gallery of Pygame primitive drawing operations.

Each item in the gallery is described with a Pygame primitive call.
Pygame performs the rasterisation into pixels on the display surface.
"""

import math
import os
import sys

import pygame


# The window is the raster surface that Pygame will draw into.
WIDTH, HEIGHT = 800, 600

# Shared colours for the gallery. Pygame uses RGB tuples with 0-255 channels.
BACKGROUND = (12, 16, 24)
GRID_COLOUR = (28, 34, 46)
REGION_BORDER = (70, 80, 100)
TEXT = (232, 238, 246)
MUTED_TEXT = (168, 178, 194)

RED = (239, 90, 90)
ORANGE = (245, 159, 82)
YELLOW = (246, 205, 92)
GREEN = (88, 206, 136)
CYAN = (83, 190, 224)
BLUE = (96, 145, 245)
PURPLE = (177, 120, 245)
PINK = (238, 111, 176)


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


def draw_grid(surface):
    """Draw a subtle 25-pixel screen-space grid behind the primitives."""
    for x in range(0, WIDTH, 25):
        pygame.draw.line(surface, GRID_COLOUR, (x, 0), (x, HEIGHT), 1)
    for y in range(0, HEIGHT, 25):
        pygame.draw.line(surface, GRID_COLOUR, (0, y), (WIDTH, y), 1)


def gallery_regions():
    """Create a simple 3 x 3 layout for the primitive examples."""
    margin_x = 32
    top = 78
    gap = 16
    cell_width = 234
    cell_height = 150

    regions = []
    for row in range(3):
        for column in range(3):
            # Each region is a rectangle in screen coordinates.
            x = margin_x + column * (cell_width + gap)
            y = top + row * (cell_height + gap)
            regions.append(pygame.Rect(x, y, cell_width, cell_height))
    return regions


def draw_region(surface, font, rect, title):
    """Draw the boundary and label for one gallery cell."""
    pygame.draw.rect(surface, REGION_BORDER, rect, 1)
    draw_text(surface, font, title, (rect.x + 12, rect.y + 10), MUTED_TEXT)


def draw_primitives(surface, label_font):
    """Draw all primitive examples with easy-to-find pygame.draw calls."""
    regions = gallery_regions()
    titles = [
        "Point marker",
        "Line",
        "Outlined rectangle",
        "Filled rectangle",
        "Outlined circle",
        "Filled circle",
        "Ellipse",
        "Triangle polygon",
        "Arc",
    ]

    for rect, title in zip(regions, titles):
        draw_region(surface, label_font, rect, title)

    # A point is represented visually by a tiny filled circle plus a centre pixel.
    point_rect = regions[0]
    point = point_rect.center
    pygame.draw.circle(surface, ORANGE, point, 5)
    surface.set_at(point, TEXT)

    # A line primitive has endpoints, colour, and width.
    line_rect = regions[1]
    pygame.draw.line(
        surface,
        BLUE,
        (line_rect.left + 34, line_rect.bottom - 36),
        (line_rect.right - 34, line_rect.top + 52),
        4,
    )

    # A rectangle with a width argument draws only the outline.
    outline_rect = regions[2]
    pygame.draw.rect(
        surface,
        GREEN,
        pygame.Rect(outline_rect.left + 48, outline_rect.top + 54, 138, 62),
        4,
    )

    # Leaving out the width argument fills the whole rectangular region.
    filled_rect = regions[3]
    pygame.draw.rect(
        surface,
        RED,
        pygame.Rect(filled_rect.left + 54, filled_rect.top + 56, 126, 62),
    )

    # Circle outlines and filled circles use the same primitive with different widths.
    outline_circle = regions[4]
    pygame.draw.circle(surface, CYAN, outline_circle.center, 43, 4)

    filled_circle = regions[5]
    pygame.draw.circle(surface, PURPLE, filled_circle.center, 44)

    # An ellipse is drawn inside the bounding rectangle supplied here.
    ellipse_rect = regions[6]
    pygame.draw.ellipse(
        surface,
        YELLOW,
        pygame.Rect(ellipse_rect.left + 44, ellipse_rect.top + 55, 146, 62),
    )

    # A polygon is described by a list of vertices in screen coordinates.
    polygon_rect = regions[7]
    triangle = [
        (polygon_rect.left + 52, polygon_rect.bottom - 34),
        (polygon_rect.centerx + 12, polygon_rect.top + 48),
        (polygon_rect.right - 42, polygon_rect.bottom - 52),
    ]
    pygame.draw.polygon(surface, PINK, triangle)

    # Arc angles are measured in radians around the ellipse's bounding rectangle.
    arc_rect = regions[8]
    pygame.draw.arc(
        surface,
        ORANGE,
        pygame.Rect(arc_rect.left + 42, arc_rect.top + 45, 150, 86),
        math.radians(20),
        math.radians(320),
        5,
    )


def render_frame(window, show_grid, title_font, label_font, small_font):
    """Clear the window, redraw the gallery, then present the finished frame."""
    window.fill(BACKGROUND)

    # The grid is optional so the same image can be discussed with or without it.
    if show_grid:
        draw_grid(window)

    draw_text(window, title_font, "Pygame rasterises the primitives you describe.", (24, 14))
    draw_text(
        window,
        small_font,
        "G: grid   Escape: close   clock.tick(60) limits program frame rate, not display refresh rate.",
        (24, 42),
        MUTED_TEXT,
    )

    draw_primitives(window, label_font)
    pygame.display.flip()


def main():
    preview_path = preview_path_from_args()

    pygame.init()
    pygame.display.set_caption("Activity 1.3 - Rendering primitive shapes")
    window = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()

    # SysFont(None, size) asks Pygame for a reasonable default system font.
    title_font = pygame.font.SysFont(None, 26)
    label_font = pygame.font.SysFont(None, 22)
    small_font = pygame.font.SysFont(None, 20)

    show_grid = True

    # The preview path is used by automated checks to render one complete frame.
    if preview_path:
        render_frame(window, show_grid, title_font, label_font, small_font)
        save_preview(preview_path, window)
        pygame.quit()
        return

    running = True
    while running:
        # 1. Handle events: close, Escape, and the grid toggle.
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_g:
                    show_grid = not show_grid

        # 2 and 3. Prepare the image, then present the completed frame.
        render_frame(window, show_grid, title_font, label_font, small_font)

        # 4. Optionally limit how fast this program repeats the loop.
        # This limits this program's frame rate; it does not change monitor refresh rate.
        clock.tick(60)

    pygame.quit()


if __name__ == "__main__":
    main()
