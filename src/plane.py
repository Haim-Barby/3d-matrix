"""One triangle or trapezoid plane from a CSV row."""

import numpy as np

from projection import project, project_reference


class Plane:
    """A triangle (3 points) or an isosceles trapezoid (4 points).

    Points are voxel indices, possibly real-valued, stored as a float64
    array of shape ``(3, 3)`` or ``(4, 3)`` in CSV order.
    """

    def __init__(self, points, line=None):
        pts = np.asarray(points, dtype=np.float64)
        if pts.ndim != 2 or pts.shape[1] != 3 or pts.shape[0] not in (3, 4):
            raise ValueError(
                "a plane needs 3 points (triangle) or 4 points (trapezoid), "
                f"each with 3 coordinates; got shape {pts.shape}"
            )
        if not np.isfinite(pts).all():
            raise ValueError("plane coordinates must be finite numbers")
        self.points = pts
        self.line = line

    def __repr__(self):
        kind = "triangle" if self.is_triangle else "trapezoid"
        return f"Plane({kind}, line={self.line})"

    @property
    def is_triangle(self):
        return self.points.shape[0] == 3

    def corners(self):
        """Return ``(a', a'', b, c)`` for PROJECT.

        CSV order is ``a, b, c`` or ``a', b, a'', c``. A triangle uses
        ``a' = a'' = a``.
        """
        if self.is_triangle:
            apex, base_left, base_right = (point.copy() for point in self.points)
            return apex, apex.copy(), base_left, base_right
        a_prime, base_left, a_second, base_right = (
            point.copy() for point in self.points
        )
        return a_prime, a_second, base_left, base_right

    def project(self, volume):
        """Vectorised projection of this plane (ALGORITHM.md section 4.2)."""
        return self._project(project, volume)

    def project_reference(self, volume):
        """Loop projection of this plane (ALGORITHM.md section 4.1)."""
        return self._project(project_reference, volume)

    def _project(self, function, volume):
        try:
            return function(volume, *self.corners())
        except ValueError as exc:
            if self.line is None:
                raise
            raise ValueError(f"line {self.line}: {exc}") from exc
