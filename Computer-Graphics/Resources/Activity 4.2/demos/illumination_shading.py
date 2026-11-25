"""Demo 5: Illumination and Shading (Lecture 3.4).

    ReflectionModelMode   the Phong reflection model at ONE surface point:
                          drag the light and the eye, adjust ka, kd, ks, n
    ShadingMode           a low-poly sphere with flat, Gouraud or Phong shading
    CompareShadingMode    the three shading methods side by side

The sphere is drawn with our own triangle filler and Z-buffer
(graphics/triangle_raster.py), not with pygame.draw.
"""

import math
import time

import numpy as np
import pygame

from core import theme
from core.demo import Demo, InfoSection, Mode
from core.draw_utils import blit_array, draw_arrow, draw_text
from core.widgets import Slider, make_slider_column
from graphics import lighting
from graphics.mesh import uv_sphere
from graphics.triangle_raster import FrameBuffer, rasterize_triangle

BASE_COLOUR = np.array([0.95, 0.55, 0.25])    # the surface colour (orange)
HIGHLIGHT_COLOUR = np.array([1.0, 1.0, 1.0])  # specular highlights are the light's colour


def light_settings(state):
    return lighting.LightSettings(Ia=state["Ia"], Il=state["Il"], ambient_on=state["ambient_on"],
                                  diffuse_on=state["diffuse_on"], specular_on=state["specular_on"])


def toggle_term(state, key):
    """A, D and S switch the ambient, diffuse and specular terms on and off."""
    names = {pygame.K_a: "ambient_on", pygame.K_d: "diffuse_on", pygame.K_s: "specular_on"}
    if key in names:
        state[names[key]] = not state[names[key]]
        return True
    return False


def terms_line(state):
    flags = [("A", "ambient", state["ambient_on"]), ("D", "diffuse", state["diffuse_on"]), ("S", "specular", state["specular_on"])]
    return [(f"{key}: {name} {'on' if on else 'off'}", theme.GREEN if on else theme.TEXT_FAINT) for key, name, on in flags]


# ===========================================================================
# Mode 1: the reflection model at one point
# ===========================================================================

class ReflectionModelMode(Mode):
    name = "One point"
    controls = [("Drag", "move light or eye"), ("A D S", "terms on/off"), ("E", "lecture example")]

    def __init__(self, demo):
        super().__init__(demo)
        canvas = demo.canvas_rect
        self.point = (canvas.left + 250, canvas.top + 400)      # P on the surface, in screen pixels
        self.radius = 230                                       # how far the icons sit from P
        self.bar_area = pygame.Rect(canvas.left + 500, canvas.top + 40, 160, 330)
        left, top = canvas.left + 30, canvas.top + 470
        self.sliders = (
            make_slider_column(left, top, 290, [("ka (ambient coefficient)", 0, 1, 0.2, 0.05, 2),
                                                ("kd (diffuse coefficient)", 0, 1, 0.6, 0.05, 2),
                                                ("ks (specular coefficient)", 0, 1, 0.3, 0.05, 2)], gap=56)
            + make_slider_column(left + 330, top, 290, [("n (shininess)", 1, 64, 4, 1, 0),
                                                        ("Ia (ambient light)", 0, 1, 0.5, 0.05, 2),
                                                        ("Il (light intensity)", 0, 1, 1.0, 0.05, 2)], gap=56)
        )
        self.reset()

    def reset(self):
        self.load_lecture_example()
        self.state = {"Ia": 0.5, "Il": 1.0, "ambient_on": True, "diffuse_on": True, "specular_on": True}
        self.dragging = None

    def load_lecture_example(self):
        """Angles chosen so that N·L = 0.8 and R·V = 0.9, as in the worked example."""
        self.light_angle = -math.degrees(math.acos(0.8))                  # L is 36.87° left of N
        self.eye_angle = math.degrees(math.acos(0.8)) - math.degrees(math.acos(0.9))   # V is 25.84° from R
        for slider, value in zip(self.sliders, (0.2, 0.6, 0.3, 4, 0.5, 1.0)):
            slider.value = value

    # -- Geometry: all vectors lie in the plane of the screen, N points straight up --

    @staticmethod
    def direction(angle_degrees):
        """Unit vector at an angle from N = (0, 1, 0); positive angles lean to the right."""
        a = math.radians(angle_degrees)
        return np.array([math.sin(a), math.cos(a), 0.0])

    def vectors(self):
        N = np.array([0.0, 1.0, 0.0])
        L = self.direction(self.light_angle)
        V = self.direction(self.eye_angle)
        R = lighting.reflect(L, N)
        return N, L, V, R

    def material(self):
        ka, kd, ks, n, _, _ = (s.value for s in self.sliders)
        return lighting.Material(ka=ka, kd=kd, ks=ks, n=n)

    def screen_of(self, vector, length):
        return (round(self.point[0] + vector[0] * length), round(self.point[1] - vector[1] * length))

    def angle_from_mouse(self, pos):
        dx, dy = pos[0] - self.point[0], self.point[1] - pos[1]
        return max(-89.0, min(89.0, math.degrees(math.atan2(dx, max(dy, 1e-6)))))

    # -- Input ----------------------------------------------------------------------

    def handle_event(self, event):
        for slider in self.sliders:
            if slider.handle_event(event):
                self.state["Ia"], self.state["Il"] = self.sliders[4].value, self.sliders[5].value
                return True
        N, L, V, R = self.vectors()
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for name, vector in (("light", L), ("eye", V)):
                x, y = self.screen_of(vector, self.radius)
                if math.hypot(event.pos[0] - x, event.pos[1] - y) < 22:
                    self.dragging = name
                    return True
        elif event.type == pygame.MOUSEBUTTONUP:
            self.dragging = None
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            angle = self.angle_from_mouse(event.pos)
            if self.dragging == "light":
                self.light_angle = angle
            else:
                self.eye_angle = angle
            return True
        elif event.type == pygame.KEYDOWN:
            if toggle_term(self.state, event.key):
                return True
            if event.key == pygame.K_e:
                self.load_lecture_example()
                self.state["Ia"], self.state["Il"] = 0.5, 1.0
                return True
        return False

    # -- Drawing ------------------------------------------------------------------------

    def draw(self, surface):
        fonts = theme.fonts()
        N, L, V, R = self.vectors()
        px, py = self.point
        canvas = self.demo.canvas_rect

        # The surface: a horizontal line through P, shaded underneath.
        pygame.draw.rect(surface, theme.PANEL, (canvas.left, py, 470, 50))
        pygame.draw.line(surface, theme.AXIS, (canvas.left + 20, py), (canvas.left + 470, py), 3)
        draw_text(surface, "surface", (canvas.left + 30, py + 10), theme.TEXT_DIM, fonts.small)

        for vector, colour, name, length in ((N, theme.TEXT, "N", 150), (L, theme.YELLOW, "L", 190),
                                             (R, theme.PURPLE, "R", 190), (V, theme.BLUE, "V", 190)):
            end = self.screen_of(vector, length)
            draw_arrow(surface, (px, py), end, colour, 3, 14)
            draw_text(surface, name, self.screen_of(vector, length + 20), colour, fonts.heading, centre=True)

        # Draggable icons: the light (a sun) and the eye.
        lx, ly = self.screen_of(L, self.radius)
        pygame.draw.circle(surface, theme.YELLOW, (lx, ly), 14)
        for k in range(8):
            a = k * math.pi / 4
            pygame.draw.line(surface, theme.YELLOW, (lx + 18 * math.cos(a), ly + 18 * math.sin(a)),
                             (lx + 24 * math.cos(a), ly + 24 * math.sin(a)), 2)
        ex, ey = self.screen_of(V, self.radius)
        pygame.draw.ellipse(surface, theme.BLUE, (ex - 18, ey - 10, 36, 20), 2)
        pygame.draw.circle(surface, theme.BLUE, (ex, ey), 6)
        pygame.draw.circle(surface, theme.TEXT, (px, py), 5)
        draw_text(surface, "P", (px - 18, py + 6), theme.TEXT, fonts.body)

        self.draw_bars(surface)
        for slider in self.sliders:
            slider.draw(surface)

    def draw_bars(self, surface):
        """A bar for each term and for the total, scaled so 1.0 fills the area."""
        fonts = theme.fonts()
        N, L, V, R = self.vectors()
        ambient, diffuse, specular = (float(t) for t in lighting.phong_terms(N, L, V, self.material(), light_settings(self.state)))
        area = self.bar_area
        draw_text(surface, "Intensity at P", (area.left, area.top - 26), theme.TEXT_DIM, fonts.small)
        pygame.draw.line(surface, theme.AXIS, (area.left, area.bottom), (area.right, area.bottom))
        bars = [("amb", ambient, theme.GREEN), ("diff", diffuse, theme.YELLOW),
                ("spec", specular, theme.PURPLE), ("I", ambient + diffuse + specular, theme.BLUE)]
        width = area.width // len(bars)
        for i, (name, value, colour) in enumerate(bars):
            height = round(min(value, 1.2) / 1.2 * area.height)
            bar = pygame.Rect(area.left + i * width + 6, area.bottom - height, width - 12, height)
            pygame.draw.rect(surface, colour, bar, border_radius=3)
            draw_text(surface, f"{value:.3f}", (bar.centerx, bar.top - 12), theme.TEXT, fonts.small, centre=True)
            draw_text(surface, name, (bar.centerx, area.bottom + 12), theme.TEXT_DIM, fonts.small, centre=True)

    def info_sections(self):
        N, L, V, R = self.vectors()
        m = self.material()
        s = light_settings(self.state)
        ambient, diffuse, specular = (float(t) for t in lighting.phong_terms(N, L, V, m, s))
        n_dot_l, r_dot_v = float(lighting.dot(N, L)), float(lighting.dot(R, V))
        return [
            InfoSection("The Phong reflection model", [
                "I = ka·Ia + kd·Il·max(0, N·L)",
                "      + ks·Il·max(0, R·V)^n",
            ], mono=True),
            InfoSection("Dot products (unit vectors)", [
                f"N·L = cos θ = {n_dot_l:.3f}",
                f"R·V = {r_dot_v:.3f}",
                "R = 2(N·L)N - L",
            ], mono=True),
            InfoSection("With these values", [
                f"ambient  = {m.ka:.2f} × {s.Ia:.2f} = {ambient:.3f}",
                f"diffuse  = {m.kd:.2f} × {s.Il:.2f} × {max(0, n_dot_l):.3f} = {diffuse:.3f}",
                f"specular = {m.ks:.2f} × {s.Il:.2f} × {max(0, r_dot_v):.3f}^{m.n:g}",
                f"         = {specular:.3f}",
                (f"I = {ambient + diffuse + specular:.3f}", theme.BLUE),
            ], mono=True),
            InfoSection("Terms", terms_line(self.state)
                        + [("Press E for the lecture example (I ≈ 0.777).", theme.TEXT_DIM)]),
        ]


# ===========================================================================
# Rendering the sphere (shared by modes 2 and 3)
# ===========================================================================

class SphereRenderer:
    """Draws a triangle-mesh sphere into a FrameBuffer with one of three shading methods.

    The camera looks along +z with an orthographic projection, so the
    direction to the viewer is V = (0, 0, -1) everywhere, and a smaller z
    means nearer to the camera.
    """

    METHODS = ["Flat", "Gouraud", "Phong"]
    VIEW = np.array([0.0, 0.0, -1.0])

    def __init__(self, size):
        self.size = size
        self.buffer = FrameBuffer(size, size, background=(0.055, 0.07, 0.11))
        self.evaluations = 0          # how many times the lighting model ran

    def to_screen(self, vertices):
        """Orthographic: x and y become pixel positions, z is kept as depth."""
        scale = self.size * 0.42
        xy = np.stack([self.size / 2 + vertices[:, 0] * scale, self.size / 2 - vertices[:, 1] * scale], axis=1)
        return xy, vertices[:, 2]

    def shade_colour(self, normals, L, material, light):
        """Phong reflection model -> RGB: (ambient + diffuse) tint the surface colour,
        specular adds white."""
        ambient, diffuse, specular = lighting.phong_terms(normals, L, self.VIEW, material, light)
        self.evaluations += np.size(ambient)
        return ((ambient + diffuse)[..., np.newaxis] * BASE_COLOUR
                + np.asarray(specular)[..., np.newaxis] * HIGHLIGHT_COLOUR)

    def render(self, mesh, method, L, material, light):
        self.buffer.clear()
        self.evaluations = 0
        xy, depth = self.to_screen(mesh.vertices)
        face_normals = mesh.face_normals()

        if method == "Gouraud":
            # Lighting once per VERTEX, then colours are interpolated.
            vertex_colours = self.shade_colour(mesh.vertex_normals, L, material, light)

        for face, face_normal in zip(mesh.faces, face_normals):
            if np.dot(face_normal, self.VIEW) <= 0:
                continue                                    # facing away: cannot be seen
            if method == "Flat":
                # Lighting once per FACE; the whole triangle gets that colour.
                colour = self.shade_colour(face_normal, L, material, light)
                attributes = np.tile(colour, (3, 1))
                shade = lambda values: values
            elif method == "Gouraud":
                attributes = vertex_colours[face]
                shade = lambda values: values
            else:
                # Phong shading: interpolate NORMALS, then light every fragment.
                attributes = mesh.vertex_normals[face]
                shade = lambda values: self.shade_colour(lighting.normalise(values), L, material, light)
            rasterize_triangle(self.buffer, xy[face], depth[face], attributes, shade)
        return self.buffer.to_uint8()


class ShadingState:
    """Settings shared by the shading modes."""

    def __init__(self):
        self.stacks, self.slices = 8, 12
        self.light_dir = lighting.normalise([-0.5, 0.6, -0.65])
        self.ka, self.kd, self.ks, self.n = 0.15, 0.7, 0.6, 32.0
        self.terms = {"Ia": 0.6, "Il": 1.0, "ambient_on": True, "diffuse_on": True, "specular_on": True}
        self.wireframe = False

    def mesh(self):
        return uv_sphere(1.0, self.stacks, self.slices)

    def material(self):
        return lighting.Material(self.ka, self.kd, self.ks, self.n)

    def light_from_mouse(self, pos, centre, radius):
        """Point the light towards where the mouse is over the sphere's picture."""
        x = (pos[0] - centre[0]) / radius
        y = (centre[1] - pos[1]) / radius
        length = min(1.0, math.hypot(x, y))
        if length > 0.98:
            x, y = x / length * 0.98, y / length * 0.98
        z = -math.sqrt(max(0.0, 1 - x * x - y * y))        # towards the viewer
        self.light_dir = lighting.normalise([x, y, z])

    def handle_key(self, key):
        if toggle_term(self.terms, key):
            return True
        if key == pygame.K_w:
            self.wireframe = not self.wireframe
        elif key == pygame.K_RIGHTBRACKET:
            self.stacks, self.slices = min(24, self.stacks + 2), min(36, self.slices + 3)
        elif key == pygame.K_LEFTBRACKET:
            self.stacks, self.slices = max(4, self.stacks - 2), max(6, self.slices - 3)
        elif key in (pygame.K_UP, pygame.K_DOWN):
            self.n = min(128.0, max(1.0, self.n * (2 if key == pygame.K_UP else 0.5)))
        else:
            return False
        return True


def make_coefficient_sliders(left, top, width):
    """Three sliders in a row for ka, kd and ks."""
    each = (width - 40) // 3
    specs = [("ka (ambient)", 0.15), ("kd (diffuse)", 0.7), ("ks (specular)", 0.6)]
    return [Slider((left + i * (each + 20), top, each, 32), label, 0, 1, value, 0.05, 2)
            for i, (label, value) in enumerate(specs)]


def apply_sliders(sliders, settings, event):
    """Pass an event to the sliders; copy any change into the settings. Returns True if used."""
    for slider in sliders:
        if slider.handle_event(event):
            settings.ka, settings.kd, settings.ks = (sl.value for sl in sliders)
            return True
    return False


def draw_wireframe(surface, renderer, mesh, rect):
    """Overlay the visible triangle edges, to show the mesh's flat facets."""
    xy, _ = renderer.to_screen(mesh.vertices)
    scale = rect.width / renderer.size
    screen = xy * scale + np.array(rect.topleft)
    for face, normal in zip(mesh.faces, mesh.face_normals()):
        if np.dot(normal, renderer.VIEW) > 0:
            pygame.draw.polygon(surface, (40, 48, 66), [tuple(screen[i]) for i in face], 1)


# ===========================================================================
# Mode 2: one sphere, choose the shading method
# ===========================================================================

class ShadingMode(Mode):
    name = "Shading"
    controls = [("F G P", "flat / Gouraud / Phong"), ("Drag", "light"), ("A D S", "terms"),
                ("Up/Down", "shininess"), ("[ ]", "mesh"), ("W", "wireframe")]

    def __init__(self, demo):
        super().__init__(demo)
        canvas = demo.canvas_rect
        self.image_rect = pygame.Rect(canvas.left + 20, canvas.top + 50, 480, 480)
        self.renderer = SphereRenderer(160)
        self.sliders = make_coefficient_sliders(canvas.left + 20, self.image_rect.bottom + 40, canvas.width - 40)
        self.reset()

    def reset(self):
        self.settings = ShadingState()
        for slider, value in zip(self.sliders, (self.settings.ka, self.settings.kd, self.settings.ks)):
            slider.value = value
        self.method = "Phong"
        self.dirty = True

    def handle_event(self, event):
        if apply_sliders(self.sliders, self.settings, event):
            self.dirty = True
            return True
        if event.type == pygame.KEYDOWN:
            methods = {pygame.K_f: "Flat", pygame.K_g: "Gouraud", pygame.K_p: "Phong"}
            if event.key in methods:
                self.method = methods[event.key]
            elif not self.settings.handle_key(event.key):
                return False
            self.dirty = True
            return True
        if (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 or
                event.type == pygame.MOUSEMOTION and event.buttons[0]) and self.image_rect.collidepoint(event.pos):
            self.settings.light_from_mouse(event.pos, self.image_rect.center, self.image_rect.width * 0.42)
            self.dirty = True
            return True
        return False

    def update(self, dt):
        if self.dirty:
            start = time.perf_counter()
            s = self.settings
            self.mesh = s.mesh()
            self.pixels = self.renderer.render(self.mesh, self.method, s.light_dir, s.material(), light_settings(s.terms))
            self.render_ms = (time.perf_counter() - start) * 1000
            self.dirty = False

    def draw(self, surface):
        self.update(0)
        blit_array(surface, self.pixels, self.image_rect)
        if self.settings.wireframe:
            draw_wireframe(surface, self.renderer, self.mesh, self.image_rect)
        pygame.draw.rect(surface, theme.PANEL_BORDER, self.image_rect, 1)
        fonts = theme.fonts()
        draw_text(surface, f"{self.method} shading  ·  {self.renderer.size} × {self.renderer.size} framebuffer, enlarged",
                  (self.image_rect.left, self.image_rect.top - 28), theme.TEXT_DIM, fonts.small)
        notes = ["Drag on the sphere", "to move the light.", "", "Lighting is evaluated:"]
        where = {"Flat": ["once per face"], "Gouraud": ["once per vertex,", "then colours are", "interpolated"],
                 "Phong": ["once per fragment,", "after interpolating", "the normals"]}[self.method]
        for i, line in enumerate(notes + where):
            colour = theme.YELLOW if line in where else theme.TEXT_DIM
            draw_text(surface, line, (self.image_rect.right + 18, self.image_rect.top + 10 + i * 20), colour, fonts.small)
        for slider in self.sliders:
            slider.draw(surface)

    def info_sections(self):
        s = self.settings
        mesh = self.mesh if hasattr(self, "mesh") else s.mesh()
        counts = {"Flat": "one per face", "Gouraud": "one per vertex", "Phong": "one per fragment"}
        return [
            InfoSection(f"{self.method} shading", {
                "Flat": ["One normal per polygon. Cheap, but the mesh looks faceted: brightness jumps at shared edges."],
                "Gouraud": ["Light the vertices, interpolate their colours. Smooth, but a narrow highlight between "
                            "vertices can be missed. Try a high shininess."],
                "Phong": ["Interpolate the vertex normals, normalise, and light every fragment. Highlights can appear "
                          "between vertices; it costs more."],
            }[self.method]),
            InfoSection("Cost of this frame", [
                f"mesh: {len(mesh.vertices)} vertices, {len(mesh.faces)} triangles",
                f"lighting evaluations: {self.renderer.evaluations} ({counts[self.method]})",
                f"render time: {getattr(self, 'render_ms', 0):.0f} ms",
            ]),
            InfoSection("Material and light", [
                f"ka = {s.ka:.2f}, kd = {s.kd:.2f}, ks = {s.ks:.2f}, n = {s.n:g}",
                f"L = ({s.light_dir[0]:.2f}, {s.light_dir[1]:.2f}, {s.light_dir[2]:.2f})",
                "V = (0, 0, -1)  (orthographic camera)",
            ]),
            InfoSection("Terms", terms_line(s.terms)),
            InfoSection("Do not confuse", [("The Phong REFLECTION MODEL says how bright one point is. Phong SHADING says "
                                            "how normals vary across a polygon. They are different ideas.", theme.TEXT_DIM)]),
        ]


# ===========================================================================
# Mode 3: flat, Gouraud and Phong side by side
# ===========================================================================

class CompareShadingMode(Mode):
    name = "Side by side"
    controls = [("Drag", "light"), ("A D S", "terms"), ("Up/Down", "shininess"), ("[ ]", "mesh"), ("W", "wireframe")]

    def __init__(self, demo):
        super().__init__(demo)
        canvas = demo.canvas_rect
        size = (canvas.width - 60) // 3
        self.rects = [pygame.Rect(canvas.left + 15 + i * (size + 15), canvas.top + 150, size, size) for i in range(3)]
        self.renderers = [SphereRenderer(110) for _ in range(3)]
        self.sliders = make_coefficient_sliders(canvas.left + 20, self.rects[0].bottom + 120, canvas.width - 40)
        self.reset()

    def reset(self):
        self.settings = ShadingState()
        for slider, value in zip(self.sliders, (self.settings.ka, self.settings.kd, self.settings.ks)):
            slider.value = value
        self.dirty = True

    def handle_event(self, event):
        if apply_sliders(self.sliders, self.settings, event):
            self.dirty = True
            return True
        if event.type == pygame.KEYDOWN and self.settings.handle_key(event.key):
            self.dirty = True
            return True
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 or event.type == pygame.MOUSEMOTION and event.buttons[0]:
            for rect in self.rects:
                if rect.collidepoint(event.pos):
                    self.settings.light_from_mouse(event.pos, rect.center, rect.width * 0.42)
                    self.dirty = True
                    return True
        return False

    def update(self, dt):
        if self.dirty:
            s = self.settings
            self.mesh = s.mesh()
            self.images = [r.render(self.mesh, method, s.light_dir, s.material(), light_settings(s.terms))
                           for r, method in zip(self.renderers, SphereRenderer.METHODS)]
            self.dirty = False

    def draw(self, surface):
        self.update(0)
        fonts = theme.fonts()
        where = ["once per face", "at the vertices", "at each fragment"]
        what = ["constant face colour", "interpolate colours", "interpolate normals"]
        for rect, image, renderer, method, w, x in zip(self.rects, self.images, self.renderers,
                                                        SphereRenderer.METHODS, where, what):
            blit_array(surface, image, rect)
            if self.settings.wireframe:
                draw_wireframe(surface, renderer, self.mesh, rect)
            pygame.draw.rect(surface, theme.PANEL_BORDER, rect, 1)
            draw_text(surface, method, (rect.centerx, rect.top - 60), theme.TEXT, fonts.heading, centre=True)
            draw_text(surface, w, (rect.centerx, rect.top - 36), theme.YELLOW, fonts.small, centre=True)
            draw_text(surface, x, (rect.centerx, rect.top - 18), theme.TEXT_DIM, fonts.small, centre=True)
            draw_text(surface, f"{renderer.evaluations} lighting evaluations", (rect.centerx, rect.bottom + 16),
                      theme.TEXT_DIM, fonts.small, centre=True)
        draw_text(surface, "Same mesh and light; different sampling of the illumination model",
                  (self.demo.canvas_rect.centerx, self.rects[0].bottom + 60), theme.TEXT_DIM, fonts.body, centre=True)
        for slider in self.sliders:
            slider.draw(surface)

    def info_sections(self):
        s = self.settings
        return [
            InfoSection("Where is lighting evaluated?", [
                "Flat: once per face",
                "Gouraud: at vertices, colours interpolated",
                "Phong: at every fragment, normals interpolated",
            ]),
            InfoSection("Things to try", [
                "Press [ to make the mesh coarser: flat shading shows the facets, Gouraud's highlight smears.",
                "Press Up for a tighter highlight (larger n): Gouraud may lose it, Phong keeps it.",
                "Press W to see the triangles.",
            ]),
            InfoSection("Settings", [f"mesh: {s.stacks} stacks × {s.slices} slices", f"shininess n = {s.n:g}"]
                        + terms_line(s.terms)),
        ]


class IlluminationShadingDemo(Demo):
    title = "Illumination and Shading"
    lecture = "3.4"

    def setup(self, canvas_rect):
        super().setup(canvas_rect)
        self.modes = [ReflectionModelMode(self), ShadingMode(self), CompareShadingMode(self)]
