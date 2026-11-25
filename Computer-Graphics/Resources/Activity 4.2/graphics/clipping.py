"""Clipping against a rectangular window (Lecture 3.3).

    clip_point()                  point clipping: four inequalities
    cohen_sutherland_steps()      line clipping with 4-bit outcodes, one step at a time
    sutherland_hodgman_stages()   polygon clipping, one window boundary at a time
    window_to_viewport()          map clipped window coordinates to the viewport

The *_steps / *_stages functions are generators: each `yield` hands back one
step of the algorithm, so a demo can show the steps one by one.
"""

from dataclasses import dataclass


@dataclass
class ClipWindow:
    x_min: float
    x_max: float
    y_min: float
    y_max: float


# ---------------------------------------------------------------------------
# Point clipping
# ---------------------------------------------------------------------------

def clip_point(x, y, window):
    """Keep a point only when all four boundary tests succeed."""
    return window.x_min <= x <= window.x_max and window.y_min <= y <= window.y_max


# ---------------------------------------------------------------------------
# Cohen-Sutherland line clipping
# ---------------------------------------------------------------------------

# One bit per boundary, in the lecture's order Top, Bottom, Right, Left.
TOP = 0b1000
BOTTOM = 0b0100
RIGHT = 0b0010
LEFT = 0b0001
INSIDE = 0b0000

BIT_NAMES = {TOP: "Top", BOTTOM: "Bottom", RIGHT: "Right", LEFT: "Left"}


def outcode(x, y, window):
    """Slide 'Cohen-Sutherland Outcodes': a 1 bit means outside that boundary."""
    code = INSIDE
    if y > window.y_max:
        code |= TOP
    elif y < window.y_min:
        code |= BOTTOM
    if x > window.x_max:
        code |= RIGHT
    elif x < window.x_min:
        code |= LEFT
    return code


def code_text(code):
    """An outcode as four binary digits, for example 0b1010 -> '1010'."""
    return f"{code:04b}"


def intersect(p1, p2, bit, window):
    """Slide 'Intersection Mathematics': where the segment meets one boundary.

    Vertical boundary   x = x_edge:  y = y1 + m (x_edge - x1)
    Horizontal boundary y = y_edge:  x = x1 + (y_edge - y1) / m

    with m = (y2 - y1) / (x2 - x1). The code below multiplies out the slope
    so that vertical lines (where m would be infinite) still work.
    """
    (x1, y1), (x2, y2) = p1, p2
    if bit in (LEFT, RIGHT):
        x_edge = window.x_min if bit == LEFT else window.x_max
        y = y1 + (y2 - y1) * (x_edge - x1) / (x2 - x1)
        return (x_edge, y)
    y_edge = window.y_min if bit == BOTTOM else window.y_max
    x = x1 + (x2 - x1) * (y_edge - y1) / (y2 - y1)
    return (x, y_edge)


def cohen_sutherland_steps(p1, p2, window):
    """Run Cohen-Sutherland, yielding a dictionary describing every step.

    Each step has the current endpoints and their outcodes, plus:
        action   'accept', 'reject' or 'clip'
        endpoint 1 or 2, the endpoint that was replaced (for 'clip')
        bit      the boundary used (for 'clip')
        point    the intersection point that replaced it (for 'clip')
    """
    p1, p2 = tuple(p1), tuple(p2)
    while True:
        c1, c2 = outcode(*p1, window), outcode(*p2, window)
        step = {"p1": p1, "p2": p2, "c1": c1, "c2": c2}

        if c1 | c2 == INSIDE:            # both endpoints inside: trivial accept
            yield {**step, "action": "accept"}
            return
        if c1 & c2 != INSIDE:            # both outside the same boundary: trivial reject
            yield {**step, "action": "reject"}
            return

        # Otherwise pick an endpoint that is outside...
        endpoint = 1 if c1 != INSIDE else 2
        code = c1 if endpoint == 1 else c2
        # ...and one boundary it violates, checking Top, Bottom, Right, Left in turn.
        bit = next(b for b in (TOP, BOTTOM, RIGHT, LEFT) if code & b)
        point = intersect(p1, p2, bit, window)

        yield {**step, "action": "clip", "endpoint": endpoint, "bit": bit, "point": point}

        # Replace that endpoint by the intersection point, then test again.
        if endpoint == 1:
            p1 = point
        else:
            p2 = point


def cohen_sutherland(p1, p2, window):
    """Return the visible part of the segment as (p1, p2), or None if it is rejected."""
    last = None
    for last in cohen_sutherland_steps(p1, p2, window):
        pass
    return (last["p1"], last["p2"]) if last["action"] == "accept" else None


# ---------------------------------------------------------------------------
# Sutherland-Hodgman polygon clipping
# ---------------------------------------------------------------------------

BOUNDARIES = ["Left", "Right", "Bottom", "Top"]


def is_inside(point, boundary, window):
    x, y = point
    if boundary == "Left":
        return x >= window.x_min
    if boundary == "Right":
        return x <= window.x_max
    if boundary == "Bottom":
        return y >= window.y_min
    return y <= window.y_max


def boundary_intersection(v1, v2, boundary, window):
    bit = {"Left": LEFT, "Right": RIGHT, "Bottom": BOTTOM, "Top": TOP}[boundary]
    return intersect(v1, v2, bit, window)


def clip_against_boundary(vertices, boundary, window):
    """One Sutherland-Hodgman stage: clip a polygon against ONE boundary.

    Walk the directed edges V1 -> V2 and apply the four rules:

        inside  -> inside    output V2
        inside  -> outside   output the intersection I
        outside -> outside   output nothing
        outside -> inside    output I, then V2

    Returns (output_vertices, edge_records). Each record says which rule
    applied to which edge, so a demo can explain the stage.
    """
    output, records = [], []
    for i in range(len(vertices)):
        v1 = vertices[i]
        v2 = vertices[(i + 1) % len(vertices)]
        in1, in2 = is_inside(v1, boundary, window), is_inside(v2, boundary, window)

        if in1 and in2:
            emitted, rule = [v2], "inside -> inside: output V2"
        elif in1 and not in2:
            emitted, rule = [boundary_intersection(v1, v2, boundary, window)], "inside -> outside: output I"
        elif not in1 and not in2:
            emitted, rule = [], "outside -> outside: output nothing"
        else:
            emitted, rule = [boundary_intersection(v1, v2, boundary, window), v2], "outside -> inside: output I, V2"

        output.extend(emitted)
        records.append({"v1": v1, "v2": v2, "rule": rule, "emitted": emitted})
    return output, records


def sutherland_hodgman_stages(vertices, window):
    """Yield one stage per boundary: (boundary, input, output, edge_records).

    The output of one stage is the input to the next (slide 'Sutherland-
    Hodgman Polygon Pipeline'). An empty output means the polygon is
    completely outside.
    """
    current = list(vertices)
    for boundary in BOUNDARIES:
        if not current:
            yield boundary, [], [], []
            continue
        output, records = clip_against_boundary(current, boundary, window)
        yield boundary, current, output, records
        current = output


def sutherland_hodgman(vertices, window):
    """Return the clipped polygon's vertex list (possibly empty)."""
    result = list(vertices)
    for _, _, output, _ in sutherland_hodgman_stages(vertices, window):
        result = output
    return result


# ---------------------------------------------------------------------------
# Window-to-viewport mapping
# ---------------------------------------------------------------------------

def window_to_viewport(x, y, window, viewport, invert_y=True):
    """Slide 'After Clipping: Viewport Mapping'.

        xs = xv_min + (x - x_min) / (x_max - x_min) · (xv_max - xv_min)
        ys = yv_min + (y - y_min) / (y_max - y_min) · (yv_max - yv_min)

    `viewport` is a ClipWindow in screen pixels. Screen y grows downward, so
    with invert_y=True the y mapping is flipped.
    """
    u = (x - window.x_min) / (window.x_max - window.x_min)
    v = (y - window.y_min) / (window.y_max - window.y_min)
    if invert_y:
        v = 1.0 - v
    xs = viewport.x_min + u * (viewport.x_max - viewport.x_min)
    ys = viewport.y_min + v * (viewport.y_max - viewport.y_min)
    return xs, ys
