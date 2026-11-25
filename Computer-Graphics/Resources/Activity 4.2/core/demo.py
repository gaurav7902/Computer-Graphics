"""The two base classes every demo is built from: Demo and Mode.

A Demo is one entry in the sidebar, usually one lecture topic
(for example "2D Transformations", Lecture 3.1).

A Mode is one way of exploring that topic (for example "Build a
transformation" or "Rotate about a pivot"). A demo holds one or more modes,
and the Tab key moves between them.

The App (core/app.py) only ever talks to a Demo. The Demo then passes the
work on to whichever Mode is active. So to add a new demo you:

    1. write one or more Mode subclasses,
    2. write a Demo subclass that creates them in setup(),
    3. register the demo in main.py.
"""

from dataclasses import dataclass, field

import pygame


@dataclass
class InfoSection:
    """One titled block of text for the info panel on the right.

    Each line is either a plain string or a (string, colour) pair.
    Set mono=True for matrices and code so the columns line up.
    """

    heading: str
    lines: list = field(default_factory=list)
    mono: bool = False


class Mode:
    """One way of exploring a demo's topic. Subclasses override these methods."""

    # The name shown on the mode's tab in the header.
    name = "Mode"

    # (key, what it does) pairs shown in the footer while this mode is active.
    controls = []

    def __init__(self, demo):
        # Keep a link to the demo so a mode can use what it shares
        # (for example the canvas rectangle or a coordinate mapper).
        self.demo = demo

    def reset(self):
        """Put the mode back to its starting state (Backspace)."""

    def handle_event(self, event):
        """React to one Pygame event. Return True if the event was used."""
        return False

    def update(self, dt):
        """Advance any animation. dt is the time since the last frame, in seconds."""

    def draw(self, surface):
        """Draw this mode onto the canvas area of the window."""

    def info_sections(self):
        """Return a list of InfoSection objects for the info panel."""
        return []


class Demo:
    """One sidebar entry. Holds its modes and passes work to the active one."""

    title = "Untitled demo"
    lecture = "?"

    # Controls that work in every mode of this demo (shown in the footer's second row).
    shared_controls = []

    def __init__(self):
        self.modes = []
        self.mode_index = 0
        self.canvas_rect = None

    def setup(self, canvas_rect):
        """Called once by the App. Subclasses create their modes here."""
        self.canvas_rect = canvas_rect

    # -- Choosing a mode ---------------------------------------------------

    @property
    def mode(self):
        return self.modes[self.mode_index]

    def set_mode(self, index):
        self.mode_index = index % len(self.modes)

    def next_mode(self):
        self.set_mode(self.mode_index + 1)

    # -- Work the App asks for each frame ----------------------------------

    def handle_event(self, event):
        """Keys shared by every demo come first; everything else goes to the mode."""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_TAB:
                self.next_mode()
                return True
            if event.key == pygame.K_BACKSPACE:
                self.mode.reset()
                return True
        return self.mode.handle_event(event)

    def update(self, dt):
        self.mode.update(dt)

    def draw(self, surface):
        self.mode.draw(surface)

    def info_sections(self):
        return self.mode.info_sections()

    def controls(self):
        return self.mode.controls
