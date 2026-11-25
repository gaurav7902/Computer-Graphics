"""App: owns the window, runs the main loop and switches between demos.

The main loop is the same one you saw in Activity 1.3:

    1. handle input events
    2. update (animations)
    3. draw the frame
    4. wait so the loop runs at most FPS times per second
"""

import os
import time

import pygame

from core import theme
from core.widgets import ControlsBar, Header, InfoPanel, Sidebar


class App:
    def __init__(self, caption="Graphics Lab"):
        pygame.init()
        pygame.display.set_caption(caption)
        self.window = pygame.display.set_mode((theme.WINDOW_WIDTH, theme.WINDOW_HEIGHT))
        self.clock = pygame.time.Clock()

        # Split the window into the five regions drawn in core/theme.py.
        canvas_left = theme.SIDEBAR_WIDTH
        canvas_width = theme.WINDOW_WIDTH - theme.SIDEBAR_WIDTH - theme.INFO_WIDTH
        canvas_top = theme.HEADER_HEIGHT
        canvas_height = theme.WINDOW_HEIGHT - theme.HEADER_HEIGHT - theme.FOOTER_HEIGHT

        self.canvas_rect = pygame.Rect(canvas_left, canvas_top, canvas_width, canvas_height)
        self.sidebar = Sidebar((0, 0, theme.SIDEBAR_WIDTH, theme.WINDOW_HEIGHT))
        self.header = Header((canvas_left, 0, canvas_width, theme.HEADER_HEIGHT))
        self.footer = ControlsBar((canvas_left, self.canvas_rect.bottom, canvas_width, theme.FOOTER_HEIGHT))
        self.info_panel = InfoPanel((self.canvas_rect.right, 0, theme.INFO_WIDTH, theme.WINDOW_HEIGHT))

        self.demos = []
        self.demo_index = 0
        self.running = True

        # A short message shown in the footer, for example after a screenshot.
        self.message = None
        self.message_until = 0.0

    # -- Demos -----------------------------------------------------------------

    def register(self, demo):
        """Add a demo to the sidebar. The demo builds its modes in setup()."""
        demo.setup(self.canvas_rect)
        self.demos.append(demo)
        self.sidebar.set_demos(self.demos)
        if len(self.demos) == 1:
            self.select_demo(0)

    @property
    def demo(self):
        return self.demos[self.demo_index]

    def select_demo(self, index):
        if 0 <= index < len(self.demos):
            self.demo_index = index
            self.header.layout_tabs(self.demo)

    # -- The main loop -----------------------------------------------------------

    def run(self):
        while self.running:
            for event in pygame.event.get():
                self.handle_event(event)

            # tick() returns milliseconds since the previous frame.
            dt = self.clock.tick(theme.FPS) / 1000.0
            self.demo.update(dt)

            self.draw()
            pygame.display.flip()
        pygame.quit()

    def handle_event(self, event):
        """Keys shared by the whole app first, then the sidebar and tabs, then the demo."""
        if event.type == pygame.QUIT:
            self.running = False
            return

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.running = False
                return
            if event.key == pygame.K_s and event.mod & (pygame.KMOD_CTRL | pygame.KMOD_META):
                self.save_screenshot()
                return
            if pygame.K_1 <= event.key <= pygame.K_9:
                self.select_demo(event.key - pygame.K_1)
                return
            if event.key == pygame.K_0:             # 0 opens the tenth demo
                self.select_demo(9)
                return

        if event.type == pygame.MOUSEBUTTONDOWN:
            index = self.sidebar.clicked_index(event)
            if index is not None:
                self.select_demo(index)
                return
            tab = self.header.clicked_tab(event)
            if tab is not None:
                self.demo.set_mode(tab)
                return

        self.demo.handle_event(event)

    def draw(self):
        surface = self.window
        surface.fill(theme.BACKGROUND)

        # The canvas is clipped so that a demo can never draw over the panels.
        pygame.draw.rect(surface, theme.CANVAS, self.canvas_rect)
        surface.set_clip(self.canvas_rect)
        self.demo.draw(surface)
        surface.set_clip(None)

        self.sidebar.draw(surface, self.demos, self.demo_index)
        self.header.draw(surface, self.demo)
        self.info_panel.draw(surface, self.demo.info_sections())

        message = self.message if time.time() < self.message_until else None
        self.footer.draw(surface, self.demo.controls(), self.demo.shared_controls, message)

    # -- Screenshots and previews ---------------------------------------------------

    def save_screenshot(self, path=None):
        if path is None:
            os.makedirs("screenshots", exist_ok=True)
            path = os.path.join("screenshots", time.strftime("graphics_lab_%Y%m%d_%H%M%S.png"))
        pygame.image.save(self.window, path)
        self.message = f"Saved {path}"
        self.message_until = time.time() + 2.5

    def save_preview(self, path):
        """Draw a single frame, save it and quit. Used to produce README images."""
        folder = os.path.dirname(path)
        if folder:
            os.makedirs(folder, exist_ok=True)
        self.draw()
        pygame.image.save(self.window, path)
        pygame.quit()
