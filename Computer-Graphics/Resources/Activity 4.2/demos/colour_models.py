"""Demo 8: Colour Models (Lecture 4.1, first half).

    ColourModelsMode     one colour, three coordinate systems (RGB, HSV, HSL),
                         plus 8-bit, hex, CMY and CMYK readouts
    MixingMode           additive light (RGB) versus subtractive ink (CMY)
    InterpolationMode    blending two colours in RGB, HSV and HSL
    BrightnessMode       an image split into brightness and colour information
"""

import numpy as np
import pygame

from core import theme
from core.demo import Demo, InfoSection, Mode
from core.draw_utils import blit_array, draw_text
from core.widgets import Slider
from graphics import colour as C


def to_rgb255(rgb):
    return tuple(int(np.clip(c, 0, 1) * 255 + 0.5) for c in rgb)


def as_image(rgb_float):
    """Float RGB array (0..1) -> uint8 array for display."""
    return (np.clip(rgb_float, 0, 1) * 255 + 0.5).astype(np.uint8)


# ===========================================================================
# Mode 1: one colour in RGB, HSV and HSL
# ===========================================================================

class ColourModelsMode(Mode):
    name = "RGB, HSV, HSL"
    controls = [("Drag", "any slider"), ("E", "lecture example"), ("O", "orange")]

    def __init__(self, demo):
        super().__init__(demo)
        canvas = demo.canvas_rect
        column = (canvas.width - 60) // 3
        top = canvas.top + 400
        def group(index, specs):
            left = canvas.left + 20 + index * (column + 10)
            return [Slider((left, top + 30 + i * 56, column, 32), label, lo, hi, 0, step, decimals)
                    for i, (label, lo, hi, step, decimals) in enumerate(specs)]
        self.groups = {
            "RGB": group(0, [("R", 0, 1, 0.01, 2), ("G", 0, 1, 0.01, 2), ("B", 0, 1, 0.01, 2)]),
            "HSV": group(1, [("H (degrees)", 0, 359.9, 0.5, 1), ("S", 0, 1, 0.01, 3), ("V", 0, 1, 0.01, 3)]),
            "HSL": group(2, [("H (degrees)", 0, 359.9, 0.5, 1), ("S", 0, 1, 0.01, 3), ("L", 0, 1, 0.01, 3)]),
        }
        self.swatch = pygame.Rect(canvas.left + 20, canvas.top + 40, 200, 200)
        self.wheel_rect = pygame.Rect(canvas.left + 260, canvas.top + 40, 200, 200)
        self.cube_origin = (canvas.left + 505, canvas.top + 215)
        self.reset()

    def reset(self):
        self.set_rgb((0.23, 0.68, 0.85))        # the lecture's 'One Colour, Different Coordinates' sample

    def set_rgb(self, rgb):
        """Store the colour and move every slider to match it."""
        self.rgb = tuple(float(c) for c in rgb)
        for slider, value in zip(self.groups["RGB"], self.rgb):
            slider.value = value
        for slider, value in zip(self.groups["HSV"], C.rgb_to_hsv(*self.rgb)):
            slider.value = value
        for slider, value in zip(self.groups["HSL"], C.rgb_to_hsl(*self.rgb)):
            slider.value = value
        self.wheel = self.make_wheel(self.groups["HSV"][2].value)

    def make_wheel(self, value, size=200):
        """A hue/saturation disc at the current V: hue goes round, saturation goes out."""
        y, x = np.mgrid[0:size, 0:size]
        dx, dy = (x - size / 2) / (size / 2), (size / 2 - y) / (size / 2)
        hue = (np.degrees(np.arctan2(dy, dx)) + 360) % 360
        saturation = np.hypot(dx, dy)
        image = C.hsv_to_rgb_array(hue, np.minimum(saturation, 1), np.full_like(hue, value))
        image[saturation > 1] = np.array(theme.CANVAS) / 255
        return as_image(image)

    def handle_event(self, event):
        for name, sliders in self.groups.items():
            for slider in sliders:
                if slider.handle_event(event):
                    values = [s.value for s in sliders]
                    if name == "RGB":
                        self.set_rgb(values)
                    elif name == "HSV":
                        self.set_rgb(C.hsv_to_rgb(*values))
                    else:
                        self.set_rgb(C.hsl_to_rgb(*values))
                    return True
        if event.type == pygame.KEYDOWN and event.key == pygame.K_e:
            self.set_rgb((0.23, 0.68, 0.85))
            return True
        if event.type == pygame.KEYDOWN and event.key == pygame.K_o:
            self.set_rgb((1.0, 0.5, 0.0))
            return True
        return False

    def draw_rgb_cube(self, surface):
        """A small oblique RGB cube with the current colour marked inside it."""
        ox, oy = self.cube_origin
        size = 105
        def project(r, g, b):
            # R to the right, G up, B back-and-up (an oblique sketch, not a camera).
            return (ox + r * size + b * size * 0.45, oy - g * size - b * size * 0.35)
        corners = {(r, g, b): project(r, g, b) for r in (0, 1) for g in (0, 1) for b in (0, 1)}
        for a in corners:
            for axis in range(3):
                if a[axis] == 0:
                    b = list(a)
                    b[axis] = 1
                    pygame.draw.line(surface, theme.GRID_MAJOR, corners[a], corners[tuple(b)], 1)
        for rgb, label in (((0, 0, 0), "Black"), ((1, 1, 1), "White"), ((1, 0, 0), "R"), ((0, 1, 0), "G"), ((0, 0, 1), "B")):
            pygame.draw.circle(surface, to_rgb255(rgb), corners[rgb], 6)
            draw_text(surface, label, (corners[rgb][0] + 8, corners[rgb][1] - 8), theme.TEXT_DIM, theme.fonts().small)
        pygame.draw.line(surface, theme.TEXT_FAINT, corners[(0, 0, 0)], corners[(1, 1, 1)], 1)
        point = project(*self.rgb)
        pygame.draw.circle(surface, to_rgb255(self.rgb), point, 9)
        pygame.draw.circle(surface, theme.TEXT, point, 9, 2)
        draw_text(surface, "RGB cube", (ox - 10, oy + 26), theme.TEXT_DIM, theme.fonts().small)
        draw_text(surface, "grey diagonal: R = G = B", (ox - 10, oy + 44), theme.TEXT_FAINT, theme.fonts().small)

    def draw(self, surface):
        fonts = theme.fonts()
        pygame.draw.rect(surface, to_rgb255(self.rgb), self.swatch, border_radius=10)
        draw_text(surface, "The colour", (self.swatch.left, self.swatch.top - 24), theme.TEXT_DIM, fonts.small)

        blit_array(surface, self.wheel, self.wheel_rect)
        h, s, v = C.rgb_to_hsv(*self.rgb)
        angle = np.radians(h)
        marker = (self.wheel_rect.centerx + np.cos(angle) * s * 100, self.wheel_rect.centery - np.sin(angle) * s * 100)
        pygame.draw.circle(surface, theme.TEXT, marker, 7, 2)
        draw_text(surface, f"Hue around, saturation outward (V = {v:.2f})", (self.wheel_rect.left - 10, self.wheel_rect.top - 24),
                  theme.TEXT_DIM, fonts.small)
        for degrees, label in ((0, "0° red"), (120, "120° green"), (240, "240° blue")):
            a = np.radians(degrees)
            draw_text(surface, label, (self.wheel_rect.centerx + np.cos(a) * 120 - 20, self.wheel_rect.centery - np.sin(a) * 112),
                      theme.TEXT_FAINT, fonts.small)

        self.draw_rgb_cube(surface)

        for index, (name, sliders) in enumerate(self.groups.items()):
            draw_text(surface, name, (sliders[0].rect.left, sliders[0].rect.top - 32), theme.HEADING, fonts.heading)
            for slider in sliders:
                slider.draw(surface)

    def info_sections(self):
        r, g, b = self.rgb
        h, s, v = C.rgb_to_hsv(r, g, b)
        hl, sl, l = C.rgb_to_hsl(r, g, b)
        c, m, y = C.rgb_to_cmy(r, g, b)
        c2, m2, y2, k = C.cmy_to_cmyk(c, m, y)
        return [
            InfoSection("Stored in the framebuffer", [
                f"normalised  ({r:.2f}, {g:.2f}, {b:.2f})",
                f"8-bit       {C.to_8bit(r, g, b)}",
                f"hex         {C.to_hex(r, g, b)}",
            ], mono=True),
            InfoSection("The same colour, other coordinates", [
                f"HSV  ({h:.1f}°, {s:.3f}, {v:.3f})",
                f"HSL  ({hl:.1f}°, {sl:.3f}, {l:.3f})",
                "V = max(R, G, B)",
                "L = (max + min) / 2",
            ], mono=True),
            InfoSection("For printing", [
                f"CMY  = 1 - RGB  = ({c:.2f}, {m:.2f}, {y:.2f})",
                f"K    = min(C, M, Y) = {k:.2f}",
                f"CMYK = ({c2:.2f}, {m2:.2f}, {y2:.2f}, {k:.2f})",
            ], mono=True),
            InfoSection("Try", [("Move V down in HSV: same hue, darker. Move S down: same hue, greyer. "
                                 "Notice how all three RGB sliders change together.", theme.TEXT_DIM)]),
        ]


# ===========================================================================
# Mode 2: additive and subtractive mixing
# ===========================================================================

class MixingMode(Mode):
    name = "Mixing"
    controls = [("Drag", "a slider")]

    SIZE = 260

    def __init__(self, demo):
        super().__init__(demo)
        canvas = demo.canvas_rect
        self.left_rect = pygame.Rect(canvas.left + 30, canvas.top + 60, self.SIZE, self.SIZE)
        self.right_rect = pygame.Rect(canvas.right - 30 - self.SIZE, canvas.top + 60, self.SIZE, self.SIZE)
        self.light_sliders = [Slider((self.left_rect.left, self.left_rect.bottom + 40 + i * 50, self.SIZE, 32), name, 0, 1, 1, 0.05, 2)
                              for i, name in enumerate(("red light", "green light", "blue light"))]
        self.ink_sliders = [Slider((self.right_rect.left, self.right_rect.bottom + 40 + i * 50, self.SIZE, 32), name, 0, 1, 1, 0.05, 2)
                            for i, name in enumerate(("cyan ink", "magenta ink", "yellow ink"))]
        self.reset()

    def reset(self):
        for slider in self.light_sliders + self.ink_sliders:
            slider.value = 1.0
        self.render()

    def circles(self):
        """Three overlapping discs as boolean masks, one per primary."""
        y, x = np.mgrid[0:self.SIZE, 0:self.SIZE]
        c = self.SIZE / 2
        radius = self.SIZE * 0.27
        centres = [(c, c - 45), (c - 45, c + 35), (c + 45, c + 35)]
        return [np.hypot(x - cx, y - cy) < radius for cx, cy in centres]

    def render(self):
        masks = self.circles()
        # Additive: start from black and ADD each light into its own channel.
        additive = np.zeros((self.SIZE, self.SIZE, 3))
        for channel, (mask, slider) in enumerate(zip(masks, self.light_sliders)):
            additive[..., channel] += mask * slider.value
        # Subtractive (ideal inks): start from white paper. Cyan absorbs red,
        # magenta absorbs green, yellow absorbs blue.
        subtractive = np.ones((self.SIZE, self.SIZE, 3))
        for channel, (mask, slider) in enumerate(zip(masks, self.ink_sliders)):
            subtractive[..., channel] -= mask * slider.value
        self.images = as_image(additive), as_image(subtractive)

    def handle_event(self, event):
        for slider in self.light_sliders + self.ink_sliders:
            if slider.handle_event(event):
                self.render()
                return True
        return False

    def draw(self, surface):
        fonts = theme.fonts()
        blit_array(surface, self.images[0], self.left_rect)
        blit_array(surface, self.images[1], self.right_rect)
        draw_text(surface, "Additive: lights on black", (self.left_rect.left, self.left_rect.top - 28), theme.TEXT, fonts.heading)
        draw_text(surface, "Subtractive: inks on white", (self.right_rect.left, self.right_rect.top - 28), theme.TEXT, fonts.heading)
        for slider, colour in zip(self.light_sliders, (theme.RED, theme.GREEN, theme.BLUE)):
            slider.draw(surface, colour)
        for slider, colour in zip(self.ink_sliders, ((0, 200, 220), (220, 60, 200), (230, 210, 40))):
            slider.draw(surface, colour)

    def info_sections(self):
        return [
            InfoSection("Additive (displays)", [
                "Start from black; add red, green and blue light.",
                "R + G = yellow,  G + B = cyan,  R + B = magenta",
                "R + G + B = white",
            ]),
            InfoSection("Subtractive (printing)", [
                "Start from white paper; each ink absorbs one part of the light.",
                "cyan absorbs red, magenta absorbs green, yellow absorbs blue",
                "C + M + Y = black (in this ideal model)",
                ("Real inks make a muddy dark brown, which is why printers add K (black).", theme.TEXT_DIM),
            ]),
            InfoSection("In code", [
                "additive[..., channel] += mask * light",
                "subtractive[..., channel] -= mask * ink",
            ], mono=True),
        ]


# ===========================================================================
# Mode 3: interpolation in different colour spaces
# ===========================================================================

class InterpolationMode(Mode):
    name = "Interpolation"
    controls = [("N", "next colour pair"), ("Mouse", "point at a strip")]

    PAIRS = [("red to cyan", (1.0, 0.0, 0.0), (0.0, 1.0, 1.0)),
             ("blue to yellow", (0.1, 0.2, 0.9), (1.0, 0.9, 0.1)),
             ("orange to purple", (1.0, 0.5, 0.0), (0.5, 0.1, 0.8))]

    def __init__(self, demo):
        super().__init__(demo)
        canvas = demo.canvas_rect
        self.strips = [pygame.Rect(canvas.left + 30, canvas.top + 90 + i * 150, canvas.width - 60, 70) for i in range(3)]
        self.reset()

    def reset(self):
        self.index = 0
        self.t = 0.5

    def blends(self, steps=256):
        """The same two colours blended three ways."""
        _, a, b = self.PAIRS[self.index]
        t = np.linspace(0, 1, steps)[:, np.newaxis]
        rgb = (1 - t) * np.array(a) + t * np.array(b)                       # C(t) = (1 - t) C0 + t C1

        def hue_blend(to_model, from_model):
            pa, pb = np.array(to_model(*a)), np.array(to_model(*b))
            values = (1 - t) * pa + t * pb                                    # hue goes straight from H0 to H1
            return np.array([from_model(*v) for v in values])

        hsv = hue_blend(C.rgb_to_hsv, C.hsv_to_rgb)
        hsl = hue_blend(C.rgb_to_hsl, C.hsl_to_rgb)
        return {"RGB": rgb, "HSV": hsv, "HSL": hsl}

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_n:
            self.index = (self.index + 1) % len(self.PAIRS)
            return True
        if event.type == pygame.MOUSEMOTION:
            for strip in self.strips:
                if strip.collidepoint(event.pos):
                    self.t = (event.pos[0] - strip.left) / strip.width
                    return True
        return False

    def draw(self, surface):
        fonts = theme.fonts()
        for strip, (name, values) in zip(self.strips, self.blends().items()):
            image = as_image(np.tile(values[np.newaxis, :, :], (8, 1, 1)))
            blit_array(surface, image, strip, smooth=True)
            pygame.draw.rect(surface, theme.PANEL_BORDER, strip, 1)
            draw_text(surface, f"Interpolate in {name}", (strip.left, strip.top - 26), theme.TEXT, fonts.heading)
            x = strip.left + round(self.t * strip.width)
            pygame.draw.line(surface, theme.TEXT, (x, strip.top - 4), (x, strip.bottom + 4), 2)
        draw_text(surface, f"Pair: {self.PAIRS[self.index][0]}  ·  t = {self.t:.2f}",
                  (self.strips[0].left, self.strips[-1].bottom + 30), theme.TEXT_DIM, fonts.body)

    def info_sections(self):
        blends = self.blends(steps=101)
        i = round(self.t * 100)
        lines = []
        for name, values in blends.items():
            r, g, b = values[i]
            lines.append((f"{name}:  ({r:.2f}, {g:.2f}, {b:.2f})", to_rgb255(values[i]) if max(values[i]) > 0.25 else theme.TEXT))
        return [
            InfoSection("C(t) = (1 - t)·C0 + t·C1", [
                "RGB blends the channels directly.",
                "HSV and HSL blend the hue angle, so the path goes round the colour wheel.",
            ]),
            InfoSection(f"At t = {self.t:.2f}", lines, mono=True),
            InfoSection("Which one?", [
                "For lighting and shading, blend in RGB: the channels are amounts of light.",
                ("For a colourful transition (red -> yellow -> green -> cyan), blending the hue can be nicer. "
                 "Look at the grey middle of the RGB strip for red to cyan.", theme.TEXT_DIM),
            ]),
        ]


# ===========================================================================
# Mode 4: brightness information and colour information
# ===========================================================================

class BrightnessMode(Mode):
    name = "Brightness vs colour"
    controls = []

    SIZE = (200, 150)

    def __init__(self, demo):
        super().__init__(demo)
        canvas = demo.canvas_rect
        w, h = 200, 150
        self.rects = [pygame.Rect(canvas.left + 20 + i * (w + 20), canvas.top + 200, w, h) for i in range(3)]
        self.images = self.make_images()

    def make_scene(self):
        """A tiny generated picture: blue sky, yellow sun, green hills with shading."""
        w, h = self.SIZE
        y, x = np.mgrid[0:h, 0:w] / np.array([h, w])[:, None, None]
        image = np.zeros((h, w, 3))
        image[:] = np.stack([0.35 + 0.3 * y, 0.6 + 0.25 * y, 0.95 * np.ones_like(y)], axis=-1)   # sky
        sun = np.hypot(x - 0.75, y - 0.25) < 0.1
        image[sun] = (1.0, 0.85, 0.2)
        hill = y > 0.62 + 0.1 * np.sin(x * 7)
        shade = (0.55 + 0.45 * (1 - y))[..., np.newaxis]
        image[hill] = (np.array([0.25, 0.7, 0.3]) * shade)[hill]
        return image

    def make_images(self):
        scene = self.make_scene()
        lum = C.luminance(scene)
        brightness = np.repeat(lum[..., np.newaxis], 3, axis=2)
        # Colour information: what is left after removing brightness, shown around mid-grey.
        colour_only = np.clip(scene - brightness + 0.5, 0, 1)
        return [as_image(scene), as_image(brightness), as_image(colour_only)]

    def draw(self, surface):
        fonts = theme.fonts()
        titles = ["Original", "Brightness (luminance-like)", "Colour differences"]
        notes = ["", "keeps shape, edges, shading", "grey = no colour difference"]
        for rect, image, title, note in zip(self.rects, self.images, titles, notes):
            blit_array(surface, image, rect)
            pygame.draw.rect(surface, theme.PANEL_BORDER, rect, 1)
            draw_text(surface, title, (rect.left, rect.top - 26), theme.TEXT, fonts.heading)
            draw_text(surface, note, (rect.left, rect.bottom + 10), theme.TEXT_DIM, fonts.small)
        draw_text(surface, "Colour image ≈ brightness information + colour information",
                  (self.demo.canvas_rect.centerx, self.rects[0].bottom + 80), theme.TEXT, fonts.body, centre=True)

    def info_sections(self):
        return [
            InfoSection("Two kinds of information", [
                "Brightness: which regions are light or dark; it carries edges, shapes and shading.",
                "Colour: the sky is blue, the ground green, the sun yellow.",
            ]),
            InfoSection("How the middle image was made", [
                "lum = 0.299 R + 0.587 G + 0.114 B",
            ], mono=True),
            InfoSection("Why separate them?", [
                "Human vision notices brightness detail much more than colour detail, so image and video "
                "systems can store colour with less detail.",
                ("This is a conceptual split. HSV Value and HSL Lightness are NOT luminance.", theme.TEXT_DIM),
            ]),
        ]


class ColourModelsDemo(Demo):
    title = "Colour Models"
    lecture = "4.1"

    def setup(self, canvas_rect):
        super().setup(canvas_rect)
        self.modes = [ColourModelsMode(self), MixingMode(self), InterpolationMode(self), BrightnessMode(self)]
