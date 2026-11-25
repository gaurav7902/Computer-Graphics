"""Demo 9: From Computed Colour to Displayed Pixel (Lecture 4.1, second half).

    GammaMode       the display's nonlinear response I = V^γ and encoding V = I^(1/γ)
    QuantiseMode    clamping to [0, 1] and storing values with a limited number of bits
    DitheringMode   hiding banding with ordered or error-diffusion dithering

Note: your own monitor applies its gamma to everything shown on screen. The
strips here SIMULATE the light a display would emit, so read them as
"relative brightness", not as a calibrated measurement.
"""

import numpy as np
import pygame

from core import theme
from core.demo import Demo, InfoSection, Mode
from core.draw_utils import blit_array, draw_text
from core.widgets import Slider
from graphics import colour as C


def grey_strip(values, height=8):
    """A 1D array of 0..1 values -> a grey image strip (uint8)."""
    v = (np.clip(values, 0, 1) * 255 + 0.5).astype(np.uint8)
    return np.repeat(np.repeat(v[np.newaxis, :, np.newaxis], height, axis=0), 3, axis=2)


class Plot:
    """A small x-y plot on the canvas, with both axes running from 0 to 1 (or a chosen range)."""

    def __init__(self, rect, x_range=(0, 1), y_range=(0, 1)):
        self.rect = pygame.Rect(rect)
        self.x_range, self.y_range = x_range, y_range

    def to_screen(self, x, y):
        (x0, x1), (y0, y1) = self.x_range, self.y_range
        sx = self.rect.left + (x - x0) / (x1 - x0) * self.rect.width
        sy = self.rect.bottom - (y - y0) / (y1 - y0) * self.rect.height
        return round(sx), round(sy)

    def draw_axes(self, surface, x_label, y_label, ticks=(0, 0.5, 1)):
        font = theme.fonts().small
        pygame.draw.rect(surface, theme.BACKGROUND, self.rect)
        for t in ticks:
            pygame.draw.line(surface, theme.GRID, self.to_screen(t, self.y_range[0]), self.to_screen(t, self.y_range[1]))
            pygame.draw.line(surface, theme.GRID, self.to_screen(self.x_range[0], t), self.to_screen(self.x_range[1], t))
            draw_text(surface, f"{t:g}", (self.to_screen(t, self.y_range[0])[0], self.rect.bottom + 12), theme.TEXT_FAINT, font, centre=True)
            draw_text(surface, f"{t:g}", (self.rect.left - 18, self.to_screen(self.x_range[0], t)[1]), theme.TEXT_FAINT, font, centre=True)
        pygame.draw.rect(surface, theme.PANEL_BORDER, self.rect, 1)
        draw_text(surface, x_label, (self.rect.centerx, self.rect.bottom + 32), theme.TEXT_DIM, font, centre=True)
        draw_text(surface, y_label, (self.rect.left, self.rect.top - 22), theme.TEXT_DIM, font)

    def draw_curve(self, surface, xs, ys, colour, width=2):
        points = [self.to_screen(x, y) for x, y in zip(xs, ys)]
        pygame.draw.lines(surface, colour, False, points, width)


# ===========================================================================
# Mode 1: gamma
# ===========================================================================

class GammaMode(Mode):
    name = "Gamma"
    controls = [("Drag", "γ or the desired light")]

    def __init__(self, demo):
        super().__init__(demo)
        canvas = demo.canvas_rect
        self.plot = Plot((canvas.left + 60, canvas.top + 50, 300, 300))
        self.gamma_slider = Slider((canvas.left + 410, canvas.top + 60, 240, 32), "γ (display response)", 1.0, 3.0, 2.2, 0.1, 1)
        self.target_slider = Slider((canvas.left + 410, canvas.top + 130, 240, 32), "desired light I", 0.0, 1.0, 0.5, 0.01, 2)
        self.strips = [pygame.Rect(canvas.left + 60, canvas.top + 440 + i * 90, canvas.width - 120, 44) for i in range(2)]

    def reset(self):
        self.gamma_slider.value, self.target_slider.value = 2.2, 0.5

    def handle_event(self, event):
        return self.gamma_slider.handle_event(event) or self.target_slider.handle_event(event)

    def draw(self, surface):
        fonts = theme.fonts()
        gamma, target = self.gamma_slider.value, self.target_slider.value
        plot = self.plot
        plot.draw_axes(surface, "signal V sent to the display", "emitted light I")
        xs = np.linspace(0, 1, 100)
        plot.draw_curve(surface, xs, xs, theme.TEXT_FAINT, 1)
        plot.draw_curve(surface, xs, C.display_response(xs, gamma), theme.YELLOW, 3)

        # Encoding: to emit `target`, send V = target^(1/γ).
        v = float(C.gamma_encode(target, gamma))
        pygame.draw.line(surface, theme.BLUE, plot.to_screen(0, target), plot.to_screen(v, target), 2)
        pygame.draw.line(surface, theme.BLUE, plot.to_screen(v, target), plot.to_screen(v, 0), 2)
        pygame.draw.circle(surface, theme.BLUE, plot.to_screen(v, target), 6)
        # The mistake: sending the light value directly.
        wrong = float(C.display_response(target, gamma))
        pygame.draw.line(surface, theme.RED, plot.to_screen(target, 0), plot.to_screen(target, wrong), 2)
        pygame.draw.circle(surface, theme.RED, plot.to_screen(target, wrong), 6)
        draw_text(surface, "yellow: I = V^γ   grey: ideal I = V", (plot.rect.left, plot.rect.bottom + 52), theme.TEXT_DIM, fonts.small)

        self.gamma_slider.draw(surface, theme.YELLOW)
        self.target_slider.draw(surface)
        notes = [(f"Send V = {target:.2f} directly:", theme.RED), (f"  emitted I = {wrong:.2f}", theme.RED),
                 (f"Encode first, V = {v:.2f}:", theme.BLUE), (f"  emitted I = {target:.2f}", theme.BLUE)]
        for i, (text, colour) in enumerate(notes):
            draw_text(surface, text, (self.gamma_slider.rect.left, self.target_slider.rect.bottom + 30 + i * 22), colour, fonts.body)

        ramp = np.linspace(0, 1, 256)
        labels = ["Light emitted if the light values are sent directly (too dark in the middle)",
                  "Light emitted if each value is gamma-encoded first (an even ramp)"]
        for rect, values, label in zip(self.strips, (C.display_response(ramp, gamma), ramp), labels):
            blit_array(surface, grey_strip(values), rect, smooth=True)
            pygame.draw.rect(surface, theme.PANEL_BORDER, rect, 1)
            draw_text(surface, label, (rect.left, rect.top - 22), theme.TEXT_DIM, fonts.small)

    def info_sections(self):
        gamma, target = self.gamma_slider.value, self.target_slider.value
        return [
            InfoSection("A simple gamma model", [
                "display:  I = V^γ",
                "encode:   V = I^(1/γ)",
            ], mono=True),
            InfoSection("Lecture example (γ = 2.2)", [
                f"V = 0.5  ->  I = 0.5^2.2 = {C.display_response(0.5, 2.2):.2f}",
                f"I = 0.5  needs  V = 0.5^(1/2.2) = {C.gamma_encode(0.5, 2.2):.2f}",
            ], mono=True),
            InfoSection(f"Now: γ = {gamma:.1f}, desired I = {target:.2f}", [
                f"encode: V = {float(C.gamma_encode(target, gamma)):.3f}",
                (f"γ = 1 would be a perfectly linear display." if gamma > 1 else "γ = 1: linear, no encoding needed.",
                 theme.TEXT_DIM),
            ]),
            InfoSection("Why it matters", [
                "Lighting calculations produce values proportional to light. Encode them before they are "
                "stored, so the display produces the intended light.",
            ]),
        ]


# ===========================================================================
# Mode 2: clamping and quantisation
# ===========================================================================

class QuantiseMode(Mode):
    name = "Clamp and quantise"
    controls = [("Drag", "bits"), ("Mouse", "point at the plot")]

    def __init__(self, demo):
        super().__init__(demo)
        canvas = demo.canvas_rect
        self.plot = Plot((canvas.left + 60, canvas.top + 60, canvas.width - 120, 300), x_range=(0, 1), y_range=(-0.3, 1.3))
        self.bits_slider = Slider((canvas.left + 60, canvas.top + 445, 260, 32), "bits per channel", 1, 8, 3, 1, 0)
        self.strip = pygame.Rect(canvas.left + 60, canvas.top + 520, canvas.width - 120, 50)
        self.reset()

    def reset(self):
        self.bits_slider.value = 3
        self.x = 0.5

    @staticmethod
    def computed(x):
        """Pretend lighting output along a surface: it can dip below 0 and overshoot 1."""
        return -0.25 + 1.5 * x

    def handle_event(self, event):
        if self.bits_slider.handle_event(event):
            return True
        if event.type == pygame.MOUSEMOTION and self.plot.rect.collidepoint(event.pos):
            self.x = (event.pos[0] - self.plot.rect.left) / self.plot.rect.width
            return True
        return False

    def draw(self, surface):
        fonts = theme.fonts()
        bits = int(self.bits_slider.value)
        plot = self.plot
        plot.draw_axes(surface, "position along a shaded surface", "value", ticks=(0, 0.5, 1))
        xs = np.linspace(0, 1, 400)
        raw = self.computed(xs)
        clamped = C.clamp(raw)
        stored = C.quantise(clamped, bits)
        plot.draw_curve(surface, xs, raw, theme.TEXT_FAINT, 1)
        plot.draw_curve(surface, xs, clamped, theme.YELLOW, 2)
        plot.draw_curve(surface, xs, stored, theme.BLUE, 3)
        x = self.x
        pygame.draw.line(surface, theme.TEXT_DIM, plot.to_screen(x, -0.3), plot.to_screen(x, 1.3), 1)
        draw_text(surface, "grey: computed   yellow: clamped to [0, 1]   blue: stored with limited bits",
                  (plot.rect.left, plot.rect.bottom + 52), theme.TEXT_DIM, fonts.small)

        self.bits_slider.draw(surface)
        draw_text(surface, f"{2 ** bits} levels per channel", (self.bits_slider.rect.right + 20, self.bits_slider.rect.top + 14),
                  theme.TEXT, fonts.body)
        blit_array(surface, grey_strip(C.quantise(xs, bits)), self.strip)
        pygame.draw.rect(surface, theme.PANEL_BORDER, self.strip, 1)
        draw_text(surface, "A smooth 0 -> 1 ramp stored with these bits: visible bands", (self.strip.left, self.strip.top - 22),
                  theme.TEXT_DIM, fonts.small)

    def info_sections(self):
        bits = int(self.bits_slider.value)
        raw = self.computed(self.x)
        clamped = float(C.clamp(raw))
        stored = float(C.quantise(clamped, bits))
        top = 2 ** bits - 1
        return [
            InfoSection("Clamp, then quantise", [
                "C_clamped = min(1, max(0, C))",
                f"level = round(C × {top}),  stored = level / {top}",
            ], mono=True),
            InfoSection("At the mouse position", [
                f"computed  {raw:6.3f}",
                f"clamped   {clamped:6.3f}",
                f"stored    {stored:6.3f}   (level {round(clamped * top)} of {top})",
            ], mono=True),
            InfoSection("Lecture examples", [
                "-0.15 -> 0,   0.72 -> 0.72,   1.18 -> 1",
                f"8 bits: 0.72 × 255 = 183.6 ≈ {round(0.72 * 255)}",
            ], mono=True),
            InfoSection("Two different limits", [
                "Clamping limits the RANGE.", "Quantisation limits the PRECISION.",
            ]),
        ]


# ===========================================================================
# Mode 3: dithering
# ===========================================================================

class DitheringMode(Mode):
    name = "Dithering"
    controls = [("O", "method"), ("Drag", "bits")]

    METHODS = ["none", "ordered (Bayer 4 × 4)", "error diffusion (Floyd–Steinberg)"]

    def __init__(self, demo):
        super().__init__(demo)
        canvas = demo.canvas_rect
        self.gradient_rect = pygame.Rect(canvas.left + 30, canvas.top + 70, canvas.width - 60, 80)
        self.sphere_rect = pygame.Rect(canvas.left + 30, canvas.top + 210, 300, 300)
        self.zoom_rect = pygame.Rect(canvas.left + 360, canvas.top + 210, 290, 300)
        self.bits_slider = Slider((canvas.left + 30, canvas.top + 560, 260, 32), "bits per channel", 1, 4, 1, 1, 0)
        self.gradient = np.tile(np.linspace(0, 1, 320), (40, 1))
        # A diffusely lit sphere, 150 × 150 pixels. Image rows go DOWN, so the
        # normal's y component is -y.
        y, x = np.mgrid[-1:1:150j, -1:1:150j]
        inside = x * x + y * y <= 1
        z = np.sqrt(np.clip(1 - x * x - y * y, 0, 1))
        light = np.array([-0.5, 0.6, 0.62]) / np.linalg.norm([-0.5, 0.6, 0.62])
        n_dot_l = x * light[0] + (-y) * light[1] + z * light[2]
        self.sphere = np.where(inside, 0.08 + 0.92 * np.clip(n_dot_l, 0, 1), 0.0)
        self.reset()

    def reset(self):
        self.method = 1
        self.bits_slider.value = 1
        self.render()

    def apply(self, image):
        bits = int(self.bits_slider.value)
        if self.method == 0:
            return C.quantise(image, bits)
        if self.method == 1:
            return C.ordered_dither(image, bits)
        return C.error_diffusion_dither(image, bits)

    def render(self):
        self.gradient_out = self.apply(self.gradient)
        self.sphere_out = self.apply(self.sphere)

    def handle_event(self, event):
        if self.bits_slider.handle_event(event):
            self.render()
            return True
        if event.type == pygame.KEYDOWN and event.key == pygame.K_o:
            self.method = (self.method + 1) % len(self.METHODS)
            self.render()
            return True
        return False

    @staticmethod
    def to_image(grey):
        v = (np.clip(grey, 0, 1) * 255 + 0.5).astype(np.uint8)
        return np.repeat(v[..., np.newaxis], 3, axis=2)

    def draw(self, surface):
        fonts = theme.fonts()
        blit_array(surface, self.to_image(self.gradient_out), self.gradient_rect)
        draw_text(surface, f"A smooth gradient stored with {2 ** int(self.bits_slider.value)} levels · dithering: {self.METHODS[self.method]}",
                  (self.gradient_rect.left, self.gradient_rect.top - 24), theme.TEXT_DIM, fonts.small)
        blit_array(surface, self.to_image(self.sphere_out), self.sphere_rect)
        draw_text(surface, "A shaded sphere", (self.sphere_rect.left, self.sphere_rect.top - 22), theme.TEXT_DIM, fonts.small)
        # Enlarged corner of the sphere so the individual pixels are visible.
        crop = self.sphere_out[60:90, 108:138]
        blit_array(surface, self.to_image(crop), self.zoom_rect)
        draw_text(surface, "Enlarged: a patch on the right of the sphere", (self.zoom_rect.left, self.zoom_rect.top - 22),
                  theme.TEXT_DIM, fonts.small)
        for rect in (self.gradient_rect, self.sphere_rect, self.zoom_rect):
            pygame.draw.rect(surface, theme.PANEL_BORDER, rect, 1)
        self.bits_slider.draw(surface)
        draw_text(surface, "Step back from the screen: the dots blend into in-between greys.",
                  (self.bits_slider.rect.right + 30, self.bits_slider.rect.top + 12), theme.TEXT_DIM, fonts.small)

    def info_sections(self):
        bits = int(self.bits_slider.value)
        return [
            InfoSection("Method (press O to change)", [(self.METHODS[self.method], theme.YELLOW)] + {
                0: ["Each pixel is rounded on its own. Nearby values land on the same level, so smooth areas become bands."],
                1: ["Each pixel is nudged by a fixed repeating 4 × 4 pattern before rounding, so neighbours round "
                    "to different levels."],
                2: ["Each pixel's rounding error is passed on to the neighbours still to be processed, so the "
                    "average brightness is preserved."],
            }[self.method]),
            InfoSection("Lecture example", [
                "want 0.5, can store only 0.4 or 0.6",
                "no dither:  0.4, 0.4, 0.4, 0.4",
                "dithered:   0.4, 0.6, 0.4, 0.6",
                "average:    (0.4 + 0.6) / 2 = 0.5",
            ], mono=True),
            InfoSection("Levels", [f"{bits} bit(s) per pixel = {2 ** bits} grey levels"]),
            InfoSection("The full journey", [
                "lighting -> RGB colour -> display encoding -> clamp -> quantise (+ dither) -> framebuffer pixel",
            ]),
        ]


class DisplayPipelineDemo(Demo):
    title = "Colour on the Display"
    lecture = "4.1"

    def setup(self, canvas_rect):
        super().setup(canvas_rect)
        self.modes = [GammaMode(self), QuantiseMode(self), DitheringMode(self)]
