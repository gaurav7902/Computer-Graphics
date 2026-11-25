"""Check graphics/matrices.py against the worked examples in Lecture 3.1.

Run from the Graphics Lab folder:
    python3 -m tests.test_matrices
"""

import numpy as np

from graphics import matrices as M


def check(name, got, expected):
    ok = np.allclose(got, expected, atol=1e-3)
    print(f"{'PASS' if ok else 'FAIL'}  {name}: got {np.round(got, 3).tolist()}, expected {np.round(np.asarray(expected, dtype=float), 3).tolist()}")
    return ok


def main():
    results = [
        check("Translation A(1,1) by (3,2)", M.apply(M.translate(3, 2), [(1, 1)])[0], (4, 3)),
        check("Scaling B(3,1) by 2", M.apply(M.scale(2, 2), [(3, 1)])[0], (6, 2)),
        check("Rotation P(3,0) by 60°", M.apply(M.rotate(60), [(3, 0)])[0], (1.5, 2.598)),
        check("Reflection (2,1) across y-axis", M.apply(M.reflect_across_y_axis(), [(2, 1)])[0], (-2, 1)),
        check("Shear P(1,2) with k=1", M.apply(M.shear_x(1), [(1, 2)])[0], (3, 2)),
        check("Pivot: P(4,1) about C(2,1) by 90°", M.apply(M.rotate_about_point(90, 2, 1), [(4, 1)])[0], (2, 3)),
        check("Order: T·R P(1,0)", M.apply(M.translate(2, 0) @ M.rotate(90), [(1, 0)])[0], (2, 1)),
        check("Order: R·T P(1,0)", M.apply(M.rotate(90) @ M.translate(2, 0), [(1, 0)])[0], (0, 3)),
        check("compose(M1, M2) == M2 @ M1",
              M.compose(M.rotate(90), M.translate(2, 0)), M.translate(2, 0) @ M.rotate(90)),
    ]
    print(f"\n{sum(results)} of {len(results)} checks passed")


if __name__ == "__main__":
    main()
