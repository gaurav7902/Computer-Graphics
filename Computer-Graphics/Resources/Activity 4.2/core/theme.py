"""Shared look-and-feel for every demo: window layout, colours and fonts.

Keeping these values in one file means every demo looks the same, and a
student can change a colour or a font size in exactly one place.
"""

import pygame


# ---------------------------------------------------------------------------
# Window layout (in screen pixels)
# ---------------------------------------------------------------------------
#
#   +-----------+---------------------------------+----------------+
#   |           |  header: demo title + mode tabs |                |
#   |  sidebar  +---------------------------------+   info panel   |
#   |  (demos)  |                                 |  (formulas and |
#   |           |            canvas               |   live values) |
#   |           |                                 |                |
#   |           +---------------------------------+                |
#   |           |  footer: keyboard controls      |                |
#   +-----------+---------------------------------+----------------+

WINDOW_WIDTH, WINDOW_HEIGHT = 1280, 800
SIDEBAR_WIDTH = 220
INFO_WIDTH = 380
HEADER_HEIGHT = 60
FOOTER_HEIGHT = 64

# The program redraws at most this many frames per second.
FPS = 60


# ---------------------------------------------------------------------------
# Colours (R, G, B), each component from 0 to 255
# ---------------------------------------------------------------------------

BACKGROUND = (12, 16, 26)
PANEL = (19, 24, 37)
PANEL_BORDER = (44, 52, 72)
CANVAS = (14, 18, 28)
GRID = (28, 34, 50)
GRID_MAJOR = (40, 48, 68)
AXIS = (120, 130, 150)

TEXT = (230, 234, 242)
TEXT_DIM = (140, 150, 170)
TEXT_FAINT = (95, 104, 124)
HEADING = (94, 190, 240)

BUTTON = (32, 40, 58)
BUTTON_HOVER = (44, 54, 78)
BUTTON_ACTIVE = (40, 92, 130)

# Colours used for shapes. "ORIGINAL" is the untouched object; the others
# mark successive results so students can tell them apart.
ORIGINAL = (120, 130, 150)
BLUE = (94, 190, 240)
YELLOW = (250, 206, 96)
GREEN = (96, 210, 140)
RED = (240, 92, 92)
PURPLE = (190, 140, 240)


# ---------------------------------------------------------------------------
# Fonts
# ---------------------------------------------------------------------------

# Pygame tries each name in turn and uses the first font installed.
SANS_FONTS = "helveticaneue,helvetica,arial,segoeui,dejavusans"
MONO_FONTS = "menlo,consolas,dejavusansmono,couriernew"


class Fonts:
    """All the fonts the program uses, created once after pygame.init()."""

    def __init__(self):
        self.title = pygame.font.SysFont(SANS_FONTS, 22, bold=True)
        self.heading = pygame.font.SysFont(SANS_FONTS, 16, bold=True)
        self.body = pygame.font.SysFont(SANS_FONTS, 15)
        self.small = pygame.font.SysFont(SANS_FONTS, 13)
        self.mono = pygame.font.SysFont(MONO_FONTS, 14)


_fonts = None


def fonts():
    """Return the shared Fonts object, creating it on first use."""
    global _fonts
    if _fonts is None:
        _fonts = Fonts()
    return _fonts
