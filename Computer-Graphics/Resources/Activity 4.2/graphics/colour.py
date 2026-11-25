"""Colour models and display considerations (Lecture 4.1).

All colour components are NORMALISED: they run from 0 to 1. Hue is the
exception: it is an angle in degrees, 0 <= H < 360.

    RGB <-> HSV, RGB <-> HSL      different coordinates for the same colour
    RGB -> CMY -> CMYK            subtractive printing
    to_8bit(), to_hex()           how a framebuffer stores a colour
    gamma, clamp, quantise        getting a computed value onto the display
    ordered / error-diffusion dithering

Python's standard library has colorsys, which does some of this. We write
the formulas out so you can compare them with the slides; tests/ checks
that the results agree with colorsys.
"""

import math

import numpy as np


# ---------------------------------------------------------------------------
# HSV and HSL
# ---------------------------------------------------------------------------

def _hue(r, g, b, c_max, delta):
    """The hue angle shared by HSV and HSL. Undefined (we return 0) for greys."""
    if delta == 0:
        return 0.0
    if c_max == r:
        h = ((g - b) / delta) % 6
    elif c_max == g:
        h = (b - r) / delta + 2
    else:
        h = (r - g) / delta + 4
    return 60.0 * h


def rgb_to_hsv(r, g, b):
    """V = max(R, G, B); S = (max - min) / max; H from which channel is largest."""
    c_max, c_min = max(r, g, b), min(r, g, b)
    delta = c_max - c_min
    v = c_max
    s = 0.0 if c_max == 0 else delta / c_max
    return _hue(r, g, b, c_max, delta), s, v


def rgb_to_hsl(r, g, b):
    """L = (max + min) / 2; saturation is defined differently from HSV."""
    c_max, c_min = max(r, g, b), min(r, g, b)
    delta = c_max - c_min
    lightness = (c_max + c_min) / 2
    s = 0.0 if delta == 0 else delta / (1 - abs(2 * lightness - 1))
    return _hue(r, g, b, c_max, delta), s, lightness


def _rgb_from_chroma(h, chroma, m):
    """Shared final step of HSV -> RGB and HSL -> RGB."""
    h_sector = (h % 360) / 60.0
    x = chroma * (1 - abs(h_sector % 2 - 1))
    sector = int(h_sector) % 6
    r, g, b = [(chroma, x, 0), (x, chroma, 0), (0, chroma, x),
               (0, x, chroma), (x, 0, chroma), (chroma, 0, x)][sector]
    return r + m, g + m, b + m


def hsv_to_rgb(h, s, v):
    chroma = v * s
    return _rgb_from_chroma(h, chroma, v - chroma)


def hsl_to_rgb(h, s, lightness):
    chroma = (1 - abs(2 * lightness - 1)) * s
    return _rgb_from_chroma(h, chroma, lightness - chroma / 2)


def hsv_to_rgb_array(h, s, v):
    """hsv_to_rgb for whole NumPy arrays at once (used to draw colour wheels).

    Same formula as hsv_to_rgb, but the six-way choice of sector is done with
    boolean masks instead of an if statement.
    """
    h, s, v = np.broadcast_arrays(np.asarray(h, float), np.asarray(s, float), np.asarray(v, float))
    chroma = v * s
    h_sector = (h % 360) / 60.0
    x = chroma * (1 - np.abs(h_sector % 2 - 1))
    zero = np.zeros_like(h)
    sector = np.floor(h_sector).astype(int) % 6
    choices = [(chroma, x, zero), (x, chroma, zero), (zero, chroma, x),
               (zero, x, chroma), (x, zero, chroma), (chroma, zero, x)]
    rgb = np.zeros(h.shape + (3,))
    for index, (r, g, b) in enumerate(choices):
        mask = sector == index
        rgb[mask] = np.stack([r[mask], g[mask], b[mask]], axis=-1)
    return rgb + (v - chroma)[..., np.newaxis]


def luminance(rgb):
    """A brightness-like value: 0.299 R + 0.587 G + 0.114 B (the classic video weights).

    Green counts most because human vision is most sensitive to it.
    """
    rgb = np.asarray(rgb, dtype=float)
    return rgb[..., 0] * 0.299 + rgb[..., 1] * 0.587 + rgb[..., 2] * 0.114


# ---------------------------------------------------------------------------
# CMY and CMYK
# ---------------------------------------------------------------------------

def rgb_to_cmy(r, g, b):
    """Slide 'Subtractive Colour with CMY': C = 1 - R, M = 1 - G, Y = 1 - B."""
    return 1 - r, 1 - g, 1 - b


def cmy_to_cmyk(c, m, y):
    """Slide 'Why Printers Add Black': move the shared amount into K.

    K = min(C, M, Y), then C' = C - K, M' = M - K, Y' = Y - K.
    (A simplified extraction, not a real printer profile.)
    """
    k = min(c, m, y)
    return c - k, m - k, y - k, k


# ---------------------------------------------------------------------------
# Storing a colour
# ---------------------------------------------------------------------------

def to_8bit(r, g, b):
    """Normalised RGB -> 0..255 integers: round(channel × 255)."""
    return tuple(int(np.floor(c * 255 + 0.5)) for c in (r, g, b))


def to_hex(r, g, b):
    """The same three bytes written in hexadecimal, for example '#FF8000'."""
    return "#" + "".join(f"{c:02X}" for c in to_8bit(r, g, b))


# ---------------------------------------------------------------------------
# Getting a computed colour onto the display
# ---------------------------------------------------------------------------

def display_response(signal, gamma):
    """Slide 'A Simple Gamma Model': emitted light I = V^γ."""
    return np.power(signal, gamma)


def gamma_encode(intensity, gamma):
    """The signal to send so the display emits the intended light: V = I^(1/γ)."""
    return np.power(intensity, 1.0 / gamma)


def clamp(values):
    """Slide 'Storage Limits': C_clamped = min(1, max(0, C))."""
    return np.minimum(1.0, np.maximum(0.0, values))


def quantise(values, bits):
    """Round each value to one of 2^bits evenly spaced stored levels in [0, 1]."""
    top = 2 ** bits - 1
    return np.floor(np.asarray(values) * top + 0.5) / top


# The 4 x 4 Bayer matrix: a fixed pattern of thresholds for ordered dithering.
BAYER_4 = np.array([
    [0, 8, 2, 10],
    [12, 4, 14, 6],
    [3, 11, 1, 9],
    [15, 7, 13, 5],
]) / 16.0


def ordered_dither(image, bits):
    """Ordered dithering: nudge each pixel by a repeating pattern before quantising.

    Neighbouring pixels then round to different levels, and the eye blends
    them into an in-between tone (slide 'When Quantisation Is Visible').
    """
    image = np.asarray(image, dtype=float)
    height, width = image.shape[:2]
    top = 2 ** bits - 1
    # Tile the 4 x 4 pattern over the whole image; values in [-0.5, 0.5).
    pattern = np.tile(BAYER_4, (height // 4 + 1, width // 4 + 1))[:height, :width] - 0.5
    if image.ndim == 3:
        pattern = pattern[:, :, np.newaxis]
    return clamp(np.floor(image * top + 0.5 + pattern) / top)


def error_diffusion_dither(image, bits):
    """Floyd–Steinberg dithering: push each pixel's rounding error onto its neighbours.

        error goes   right: 7/16,  below-left: 3/16,  below: 5/16,  below-right: 1/16

    This one needs a loop, because each pixel depends on the ones before it.
    The loop uses plain Python lists of floats, which is much faster than
    indexing a NumPy array one element at a time.
    """
    image = np.asarray(image, dtype=float)
    if image.ndim == 3:                       # colour: dither each channel separately
        return np.stack([error_diffusion_dither(image[..., c], bits) for c in range(image.shape[2])], axis=-1)

    top = 2 ** bits - 1
    work = image.tolist()
    height, width = len(work), len(work[0])
    for y in range(height):
        row = work[y]
        below = work[y + 1] if y + 1 < height else None
        for x in range(width):
            old = row[x]
            new = math.floor(min(1.0, max(0.0, old)) * top + 0.5) / top
            row[x] = new
            error = old - new
            if x + 1 < width:
                row[x + 1] += error * 7 / 16
            if below is not None:
                if x > 0:
                    below[x - 1] += error * 3 / 16
                below[x] += error * 5 / 16
                if x + 1 < width:
                    below[x + 1] += error * 1 / 16
    return clamp(np.array(work))
