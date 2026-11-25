"""StepPlayer: run an algorithm one step at a time, or let it play by itself.

The algorithms in graphics/ are generators: each `yield` is one step.
A StepPlayer pulls those steps out when you press Space (step) or
P (play/pause), and remembers every step taken so far so the demo can draw
them and list them in the info panel.
"""


class StepPlayer:
    def __init__(self, make_steps, interval=0.35):
        """make_steps is a function that returns a NEW generator each time it is called."""
        self.make_steps = make_steps
        self.interval = interval          # seconds between steps while playing
        self.restart()

    def restart(self):
        self.generator = self.make_steps()
        self.done = []                    # every step taken so far, in order
        self.playing = False
        self.timer = 0.0
        # Look one step ahead, so we know we are finished as soon as the
        # last step has been shown (rather than one key press later).
        self.pending = next(self.generator, None)

    @property
    def finished(self):
        return self.pending is None

    def step(self):
        """Take one step. Returns False if there were no steps left."""
        if self.finished:
            self.playing = False
            return False
        self.done.append(self.pending)
        self.pending = next(self.generator, None)
        if self.finished:
            self.playing = False
        return True

    def run_to_end(self):
        while self.step():
            pass

    def toggle_play(self):
        if self.finished:
            self.restart()
        self.playing = not self.playing

    def update(self, dt):
        if not self.playing:
            return
        self.timer += dt
        while self.timer >= self.interval and self.playing:
            self.timer -= self.interval
            self.step()

    @property
    def current(self):
        """The most recent step, or None before the first one."""
        return self.done[-1] if self.done else None

    def status(self):
        if self.finished:
            return "finished"
        return "playing" if self.playing else "paused"
