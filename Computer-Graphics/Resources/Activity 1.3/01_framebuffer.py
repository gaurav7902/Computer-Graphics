"""A small NumPy framebuffer rendered through Pygame-CE.

This file keeps the rendering pipeline deliberately visible:
we write RGB values into a NumPy array, then ask Pygame to display that array.
"""

import os
import sys

import numpy as np
import pygame


# The logical framebuffer resolution. Each pixel stores one RGB colour.
WIDTH, HEIGHT = 800, 600

# The world-space region shown by the framebuffer.
# World coordinates are convenient for describing objects; screen coordinates
# are integer pixel addresses used by the raster display.
WORLD_LEFT, WORLD_RIGHT = -4.0, 4.0
WORLD_BOTTOM, WORLD_TOP = -3.0, 3.0

# RGB colours. Each component is an integer from 0 to 255.
BACKGROUND = (12, 16, 26)
AXIS_COLOUR = (120, 130, 150)
TICK_COLOUR = (70, 78, 96)
WHITE = (240, 244, 250)

# The first two numbers are world coordinates. The last tuple is the marker RGB.
MARKERS = [
    (-3.0, -2.0, (240, 92, 92)),
    (-1.4, 1.6, (96, 210, 140)),
    (1.7, -1.3, (250, 206, 96)),
    (3.2, 2.2, (94, 190, 240)),
]

# The framebuffer shape is [rows, columns, colour channels] or [y, x, rgb].
framebuffer = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)


def set_pixel(x, y, colour):
    """Store one RGB value in the framebuffer if the address is valid."""
    # Bounds checking keeps accidental coordinates outside the image harmless.
    if 0 <= x < WIDTH and 0 <= y < HEIGHT:
        # NumPy image indexing is [y, x], not [x, y].
        framebuffer[y, x] = colour


def world_to_screen(x, y):
    """Map world coordinates in [-4, 4] x [-3, 3] to pixel addresses."""
    # X increases to the right in both world space and screen space.
    screen_x = round((x - WORLD_LEFT) / (WORLD_RIGHT - WORLD_LEFT) * (WIDTH - 1))

    # Screen y increases downward, so world y must be inverted during mapping.
    screen_y = round((WORLD_TOP - y) / (WORLD_TOP - WORLD_BOTTOM) * (HEIGHT - 1))
    return int(screen_x), int(screen_y)


def draw_marker(world_x, world_y, colour):
    """Draw a small square marker centered at a world-space position."""
    screen_x, screen_y = world_to_screen(world_x, world_y)

    # Fill an 11 x 11 block of pixels so the marker is easy to see.
    for dy in range(-5, 6):
        for dx in range(-5, 6):
            set_pixel(screen_x + dx, screen_y + dy, colour)

    # Add a small white crosshair to show the exact mapped pixel location.
    for offset in range(-8, 9):
        set_pixel(screen_x + offset, screen_y, WHITE)
        set_pixel(screen_x, screen_y + offset, WHITE)


def draw_axes():
    """Draw the world x-axis and y-axis through the origin."""
    origin_x, origin_y = world_to_screen(0.0, 0.0)

    # The x-axis is a horizontal row of pixels at the mapped origin y.
    for x in range(WIDTH):
        set_pixel(x, origin_y, AXIS_COLOUR)

    # The y-axis is a vertical column of pixels at the mapped origin x.
    for y in range(HEIGHT):
        set_pixel(origin_x, y, AXIS_COLOUR)

    # Tick marks are still described in world coordinates, then mapped.
    for world_x in range(int(WORLD_LEFT), int(WORLD_RIGHT) + 1):
        tick_x, tick_y = world_to_screen(world_x, 0.0)
        for dy in range(-6, 7):
            set_pixel(tick_x, tick_y + dy, TICK_COLOUR)

    for world_y in range(int(WORLD_BOTTOM), int(WORLD_TOP) + 1):
        tick_x, tick_y = world_to_screen(0.0, world_y)
        for dx in range(-6, 7):
            set_pixel(tick_x + dx, tick_y, TICK_COLOUR)


def draw_scene():
    """Calculate every pixel value that makes up the rendered image."""
    # Fill every [y, x] pixel with the background colour.
    framebuffer[:, :, :] = BACKGROUND
    draw_axes()

    for world_x, world_y, colour in MARKERS:
        draw_marker(world_x, world_y, colour)


def framebuffer_to_surface():
    """Expose the NumPy framebuffer as a Pygame surface for presentation."""
    # Pygame surfaces use [x, y] ordering, so we transpose from [y, x].
    pixels_for_pygame = np.transpose(framebuffer, (1, 0, 2))
    return pygame.surfarray.make_surface(pixels_for_pygame)


def fit_rect(window_size):
    """Return a rectangle that fits the framebuffer inside the window."""
    window_width, window_height = window_size

    # Use one scale for both axes so resizing the window preserves aspect ratio.
    scale = min(window_width / WIDTH, window_height / HEIGHT)
    scaled_width = max(1, int(WIDTH * scale))
    scaled_height = max(1, int(HEIGHT * scale))
    x = (window_width - scaled_width) // 2
    y = (window_height - scaled_height) // 2
    return pygame.Rect(x, y, scaled_width, scaled_height)


def render_frame(window):
    """Draw the framebuffer and present it in the current window size."""
    # Rendering happens first: the framebuffer receives the final pixel values.
    draw_scene()
    framebuffer_surface = framebuffer_to_surface()

    # Presentation happens second: Pygame scales and blits the completed image.
    window.fill((4, 6, 10))
    target_rect = fit_rect(window.get_size())
    scaled_surface = pygame.transform.scale(framebuffer_surface, target_rect.size)
    window.blit(scaled_surface, target_rect)
    pygame.display.flip()


def preview_path_from_args():
    """Return a screenshot path when the script is run in verification mode."""
    if "--preview" in sys.argv:
        index = sys.argv.index("--preview")
        if index + 1 < len(sys.argv):
            return sys.argv[index + 1]
    return None


def save_preview(path, window):
    """Save the current window contents for README/checking workflows."""
    folder = os.path.dirname(path)
    if folder:
        os.makedirs(folder, exist_ok=True)
    pygame.image.save(window, path)


def main():
    preview_path = preview_path_from_args()

    pygame.init()
    pygame.display.set_caption("Activity 1.3 - NumPy framebuffer")

    # RESIZABLE lets the display window change while the framebuffer stays 800 x 600.
    window = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
    clock = pygame.time.Clock()

    # The preview path is used by automated checks to render one complete frame.
    if preview_path:
        render_frame(window)
        save_preview(preview_path, window)
        pygame.quit()
        return

    running = True
    while running:
        # 1. Handle input and window events.
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False
            elif event.type == pygame.VIDEORESIZE:
                window = pygame.display.set_mode(event.size, pygame.RESIZABLE)

        # 2 and 3. Prepare the image, then present the completed frame.
        render_frame(window)

        # 4. Optionally limit how fast this program repeats the loop.
        # This limits this program's frame rate; it does not change monitor refresh rate.
        clock.tick(60)

    pygame.quit()


if __name__ == "__main__":
    main()
