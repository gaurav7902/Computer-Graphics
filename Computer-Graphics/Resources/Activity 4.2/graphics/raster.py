"""Scan conversion (Lecture 3.5): choosing pixels for lines, circles and polygons.

Pixels here have INTEGER coordinates and sit at the integer grid points,
as in the lecture's figures. y increases upward.

Each algorithm is a generator: every `yield` reports one decision, so the
demo can show the algorithm step by step. To just get all the pixels, use
list(...) on it.
"""

import math


# ---------------------------------------------------------------------------
# DDA
# ---------------------------------------------------------------------------

def dda_line(x1, y1, x2, y2):
    """Slide 'DDA: Step Along the Line'.

    steps = max(|Δx|, |Δy|), x_inc = Δx / steps, y_inc = Δy / steps.
    Add the increments repeatedly and round each position to a pixel.

    Yields dictionaries: k, the exact (x, y) and the rounded pixel (px, py).
    """
    dx, dy = x2 - x1, y2 - y1
    steps = max(abs(dx), abs(dy))
    if steps == 0:
        yield {"k": 0, "x": x1, "y": y1, "px": x1, "py": y1, "x_inc": 0, "y_inc": 0}
        return
    x_inc, y_inc = dx / steps, dy / steps
    x, y = float(x1), float(y1)
    for k in range(steps + 1):
        # Round half up, like the lecture (2.5 -> 3). Python's round() would
        # round 2.5 to 2 ("banker's rounding"), so we use floor(v + 0.5).
        yield {"k": k, "x": x, "y": y, "px": math.floor(x + 0.5), "py": math.floor(y + 0.5),
               "x_inc": x_inc, "y_inc": y_inc}
        x += x_inc
        y += y_inc


# ---------------------------------------------------------------------------
# Bresenham
# ---------------------------------------------------------------------------

def bresenham_line(x1, y1, x2, y2):
    """Slides 'Bresenham's Update Rules' and 'What About Other Slopes?'.

    For 0 <= m <= 1 with x increasing:
        p0 = 2Δy - Δx
        p < 0  -> choose E,  p += 2Δy
        p >= 0 -> choose NE, p += 2Δy - 2Δx

    Other slopes use the same rule after choosing the dominant (main)
    coordinate and the step direction of each axis.

    Yields dictionaries: k, the pixel (x, y), p (the decision value used to
    reach this pixel, None for the first pixel) and the move taken:
    'straight' (E in the first octant) or 'diagonal' (NE).
    """
    dx, dy = abs(x2 - x1), abs(y2 - y1)
    step_x = 1 if x2 >= x1 else -1
    step_y = 1 if y2 >= y1 else -1
    y_major = dy > dx                     # is y the dominant coordinate?
    if y_major:
        dx, dy = dy, dx                   # swap roles: now 'dx' is along the main axis

    x, y = x1, y1
    p = 2 * dy - dx
    yield {"k": 0, "x": x, "y": y, "p": None, "move": None, "y_major": y_major}

    for k in range(1, dx + 1):
        p_used = p
        if p < 0:
            move = "straight"             # only the main coordinate changes
            p += 2 * dy
        else:
            move = "diagonal"             # both coordinates change
            p += 2 * dy - 2 * dx
            if y_major:
                x += step_x
            else:
                y += step_y
        if y_major:
            y += step_y
        else:
            x += step_x
        yield {"k": k, "x": x, "y": y, "p": p_used, "move": move, "y_major": y_major}


# ---------------------------------------------------------------------------
# Midpoint circle
# ---------------------------------------------------------------------------

def midpoint_circle(radius):
    """Slides 'The Midpoint Circle Decision' and 'Midpoint Circle Update Rules'.

    Computes the octant 0 <= x <= y of a circle centred at the origin:
        x0 = 0, y0 = R, p0 = 1 - R
        p < 0  -> choose E,  p += 2x + 3
        p >= 0 -> choose SE, p += 2x - 2y + 5   (x, y before the move)
    Stop before accepting a point with x > y.

    Yields dictionaries: the point (x, y), p (the decision value at this
    point) and the move chosen from it ('E', 'SE', or None at the end).
    """
    x, y, p = 0, radius, 1 - radius
    while x <= y:
        if p < 0:
            move, next_p, next_x, next_y = "E", p + 2 * x + 3, x + 1, y
        else:
            move, next_p, next_x, next_y = "SE", p + 2 * x - 2 * y + 5, x + 1, y - 1
        is_last = next_x > next_y
        yield {"x": x, "y": y, "p": p, "move": None if is_last else move}
        x, y, p = next_x, next_y, next_p


def eight_way_symmetry(x, y, cx=0, cy=0):
    """Slide 'Eight-way symmetry': one computed point gives up to eight pixels."""
    points = [(x, y), (y, x), (-x, y), (-y, x), (x, -y), (y, -x), (-x, -y), (-y, -x)]
    unique = []
    for px, py in points:
        if (px + cx, py + cy) not in unique:
            unique.append((px + cx, py + cy))
    return unique


# ---------------------------------------------------------------------------
# Scan-line polygon filling
# ---------------------------------------------------------------------------

def scanline_crossings(polygon, y):
    """Where scan line y crosses the polygon's edges, sorted left to right.

    Slide 'Vertices and Horizontal Edges Need Care': include an edge at its
    lower endpoint, exclude it at its upper endpoint, and ignore horizontal
    edges. This counts crossing EVENTS correctly at vertices.
    """
    xs = []
    for i in range(len(polygon)):
        (xa, ya), (xb, yb) = polygon[i], polygon[(i + 1) % len(polygon)]
        if ya == yb:
            continue                                   # horizontal edge
        if ya > yb:
            (xa, ya), (xb, yb) = (xb, yb), (xa, ya)    # make (xa, ya) the lower end
        if ya <= y < yb:                               # lower included, upper excluded
            xs.append(xa + (y - ya) * (xb - xa) / (yb - ya))
    return sorted(xs)


def scanline_fill(polygon):
    """Slide 'Scan-Line Polygon Filling', one scan line per `yield`.

    For each integer y: find the crossings, pair them up with the even-odd
    rule (x0-x1, x2-x3, ...), and fill the pixels whose x lies in each span.

    Yields dictionaries: y, crossings, spans [(x_start, x_end), ...] and the
    list of filled pixels on that row.
    """
    ys = [y for _, y in polygon]
    for y in range(math.ceil(min(ys)), math.floor(max(ys)) + 1):
        crossings = scanline_crossings(polygon, y)
        spans = [(crossings[i], crossings[i + 1]) for i in range(0, len(crossings) - 1, 2)]
        pixels = []
        for start, end in spans:
            for x in range(math.ceil(start), math.floor(end) + 1):
                pixels.append((x, y))
        yield {"y": y, "crossings": crossings, "spans": spans, "pixels": pixels}
