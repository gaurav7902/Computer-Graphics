"""The pieces of the common window: buttons, sidebar, header, info panel, footer.

None of these classes knows anything about computer graphics. They only
show what a Demo gives them, which keeps the lecture code in the demos.
"""

import pygame

from core import theme
from core.draw_utils import draw_text


class Button:
    """A clickable rectangle with a label."""

    def __init__(self, rect, label, active=False):
        self.rect = pygame.Rect(rect)
        self.label = label
        self.active = active

    def is_clicked(self, event):
        return (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
            and self.rect.collidepoint(event.pos)
        )

    def draw(self, surface):
        hovered = self.rect.collidepoint(pygame.mouse.get_pos())
        if self.active:
            colour = theme.BUTTON_ACTIVE
        elif hovered:
            colour = theme.BUTTON_HOVER
        else:
            colour = theme.BUTTON
        pygame.draw.rect(surface, colour, self.rect, border_radius=6)
        pygame.draw.rect(surface, theme.PANEL_BORDER, self.rect, 1, border_radius=6)
        text_colour = theme.TEXT if (self.active or hovered) else theme.TEXT_DIM
        draw_text(surface, self.label, self.rect.center, text_colour, theme.fonts().small, centre=True)


def make_button_row(left, top, labels, height=28, gap=6, padding=14):
    """Create Buttons side by side, each just wide enough for its label."""
    font = theme.fonts().small
    buttons = []
    x = left
    for label in labels:
        width = font.size(label)[0] + 2 * padding
        buttons.append(Button((x, top, width, height), label))
        x += width + gap
    return buttons


class Sidebar:
    """The list of demos on the left. Clicking an entry selects that demo."""

    def __init__(self, rect):
        self.rect = pygame.Rect(rect)
        self.buttons = []

    def set_demos(self, demos):
        self.buttons = []
        top = self.rect.top + 70
        for number, demo in enumerate(demos, start=1):
            rect = (self.rect.left + 12, top, self.rect.width - 24, 48)
            self.buttons.append(Button(rect, f"{number}. {demo.title}"))
            top += 56

    def clicked_index(self, event):
        for index, button in enumerate(self.buttons):
            if button.is_clicked(event):
                return index
        return None

    def draw(self, surface, demos, current_index):
        pygame.draw.rect(surface, theme.PANEL, self.rect)
        pygame.draw.line(surface, theme.PANEL_BORDER, self.rect.topright, self.rect.bottomright)

        fonts = theme.fonts()
        draw_text(surface, "Graphics Lab", (self.rect.left + 16, self.rect.top + 16), theme.TEXT, fonts.title)
        draw_text(surface, "NCSD302 · Units 3 and 4", (self.rect.left + 16, self.rect.top + 44), theme.TEXT_DIM, fonts.small)

        for index, (button, demo) in enumerate(zip(self.buttons, demos)):
            button.active = index == current_index
            self.draw_entry(surface, button, demo)

    def draw_entry(self, surface, button, demo):
        """Draw one demo entry: its title, with the lecture number underneath."""
        hovered = button.rect.collidepoint(pygame.mouse.get_pos())
        colour = theme.BUTTON_ACTIVE if button.active else (theme.BUTTON_HOVER if hovered else theme.PANEL)
        pygame.draw.rect(surface, colour, button.rect, border_radius=6)
        fonts = theme.fonts()
        draw_text(surface, button.label, (button.rect.left + 10, button.rect.top + 6), theme.TEXT, fonts.body)
        draw_text(surface, f"Lecture {demo.lecture}", (button.rect.left + 10, button.rect.top + 27), theme.TEXT_DIM, fonts.small)


class Header:
    """The bar above the canvas: demo title on the left, mode tabs on the right."""

    def __init__(self, rect):
        self.rect = pygame.Rect(rect)
        self.tabs = []

    def layout_tabs(self, demo):
        """Build one tab per mode, lined up against the right edge."""
        font = theme.fonts().small
        widths = [font.size(mode.name)[0] + 24 for mode in demo.modes]
        x = self.rect.right - 12 - sum(widths) - 6 * (len(widths) - 1)
        self.tabs = []
        for mode, width in zip(demo.modes, widths):
            self.tabs.append(Button((x, self.rect.top + 16, width, 28), mode.name))
            x += width + 6

    def clicked_tab(self, event):
        for index, tab in enumerate(self.tabs):
            if tab.is_clicked(event):
                return index
        return None

    def draw(self, surface, demo):
        pygame.draw.rect(surface, theme.PANEL, self.rect)
        pygame.draw.line(surface, theme.PANEL_BORDER, self.rect.bottomleft, self.rect.bottomright)
        draw_text(surface, demo.title, (self.rect.left + 16, self.rect.top + 10), theme.TEXT, theme.fonts().title)
        draw_text(surface, f"Lecture {demo.lecture}",
                  (self.rect.left + 16, self.rect.top + 37), theme.TEXT_DIM, theme.fonts().small)
        for index, tab in enumerate(self.tabs):
            tab.active = index == demo.mode_index
            tab.draw(surface)


class InfoPanel:
    """The panel on the right. Shows the InfoSection list from the active mode."""

    def __init__(self, rect):
        self.rect = pygame.Rect(rect)

    def draw(self, surface, sections):
        pygame.draw.rect(surface, theme.PANEL, self.rect)
        pygame.draw.line(surface, theme.PANEL_BORDER, self.rect.topleft, self.rect.bottomleft)

        fonts = theme.fonts()
        left = self.rect.left + 18
        width = self.rect.width - 36
        y = self.rect.top + 16

        for section in sections:
            draw_text(surface, section.heading, (left, y), theme.HEADING, fonts.heading)
            y += 24
            font = fonts.mono if section.mono else fonts.body
            for line in section.lines:
                text, colour = (line, theme.TEXT) if isinstance(line, str) else line
                # Plain text is wrapped to fit the panel; mono text is kept as-is
                # so that matrix columns stay aligned.
                pieces = [text] if section.mono else wrap_text(text, font, width)
                for piece in pieces:
                    draw_text(surface, piece, (left, y), colour, font)
                    y += font.get_linesize() + 1
            y += 14
            if y > self.rect.bottom - 20:
                break


def wrap_text(text, font, max_width):
    """Split text into lines no wider than max_width pixels."""
    words = text.split(" ")
    lines, current = [], ""
    for word in words:
        trial = word if not current else current + " " + word
        if font.size(trial)[0] <= max_width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word
    lines.append(current)
    return lines


class ControlsBar:
    """The footer under the canvas, listing the keys that work right now."""

    GLOBAL_CONTROLS = [
        ("1–9, 0", "demo"),
        ("Tab", "next mode"),
        ("Backspace", "reset"),
        ("Ctrl/Cmd+S", "screenshot"),
        ("Esc", "quit"),
    ]

    def __init__(self, rect):
        self.rect = pygame.Rect(rect)

    def draw(self, surface, mode_controls, demo_controls=(), message=None):
        pygame.draw.rect(surface, theme.PANEL, self.rect)
        pygame.draw.line(surface, theme.PANEL_BORDER, self.rect.topleft, self.rect.topright)
        self.draw_row(surface, mode_controls, self.rect.top + 10, theme.TEXT)
        if message:
            draw_text(surface, message, (self.rect.left + 16, self.rect.top + 36), theme.GREEN, theme.fonts().small)
        else:
            self.draw_row(surface, list(demo_controls) + self.GLOBAL_CONTROLS, self.rect.top + 36, theme.TEXT_DIM)

    def draw_row(self, surface, controls, y, colour):
        """Draw 'Key action' pairs in a row, with the key names highlighted."""
        fonts = theme.fonts()
        x = self.rect.left + 16
        for key, action in controls:
            key_rect = draw_text(surface, key, (x, y), theme.YELLOW, fonts.small)
            action_rect = draw_text(surface, action, (key_rect.right + 6, y), colour, fonts.small)
            x = action_rect.right + 18


class Slider:
    """A horizontal slider for one number. Drag the handle or click the track."""

    def __init__(self, rect, label, minimum, maximum, value, step=None, decimals=2):
        self.rect = pygame.Rect(rect)
        self.label = label
        self.minimum, self.maximum = minimum, maximum
        self.step = step
        self.decimals = decimals
        self.value = value
        self.dragging = False

    def track_rect(self):
        """The bar itself sits under the label, leaving room for the value on the right."""
        return pygame.Rect(self.rect.left, self.rect.top + 20, self.rect.width - 56, 8)

    def set_from_pixel(self, x):
        track = self.track_rect()
        fraction = min(1.0, max(0.0, (x - track.left) / track.width))
        value = self.minimum + fraction * (self.maximum - self.minimum)
        if self.step:
            value = round(value / self.step) * self.step
        self.value = min(self.maximum, max(self.minimum, value))

    def handle_event(self, event):
        """Return True if this event changed the value."""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.track_rect().inflate(0, 16).collidepoint(event.pos):
                self.dragging = True
                self.set_from_pixel(event.pos[0])
                return True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.dragging = False
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            self.set_from_pixel(event.pos[0])
            return True
        return False

    def draw(self, surface, colour=theme.BLUE):
        fonts = theme.fonts()
        draw_text(surface, self.label, (self.rect.left, self.rect.top), theme.TEXT_DIM, fonts.small)
        track = self.track_rect()
        pygame.draw.rect(surface, theme.BUTTON, track, border_radius=4)
        fraction = (self.value - self.minimum) / (self.maximum - self.minimum)
        filled = pygame.Rect(track.left, track.top, round(track.width * fraction), track.height)
        pygame.draw.rect(surface, colour, filled, border_radius=4)
        handle = (track.left + round(track.width * fraction), track.centery)
        pygame.draw.circle(surface, theme.TEXT, handle, 7)
        draw_text(surface, f"{self.value:.{self.decimals}f}", (track.right + 10, track.top - 5), theme.TEXT, fonts.small)


def make_slider_column(left, top, width, specs, gap=40):
    """Create Sliders stacked vertically from (label, min, max, value, step, decimals) tuples."""
    sliders = []
    for label, minimum, maximum, value, step, decimals in specs:
        sliders.append(Slider((left, top, width, 32), label, minimum, maximum, value, step, decimals))
        top += gap
    return sliders
