"""Load a volume from NRRD and planes from CSV.

NRRD is read with pynrrd ``index_order='F'``, so the array is ``M[x, y, z]``
and matches the header ``sizes`` (ALGORITHM.md issue 7).

CSV: one plane per line, comma-separated voxel coordinates. A triangle is
9 numbers ``ax,ay,az,bx,by,bz,cx,cy,cz`` (apex, then the two base vertices).
A trapezoid is 12 numbers ``a'x,a'y,a'z,a''x,a''y,a''z,bx,by,bz,cx,cy,cz``
(top-left, top-right, base-left, base-right). This is the layout in SRS.md.
Sample CSVs live in ``video/``.
"""

import numpy as np
import nrrd
from nrrd.errors import NRRDError

from projection import check_plane, project, project_reference


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
        """Return ``(a', a'', b, c)``. A triangle uses ``a' = a'' = a``."""
        if self.is_triangle:
            apex, base_left, base_right = (point.copy() for point in self.points)
            return apex, apex.copy(), base_left, base_right
        return tuple(point.copy() for point in self.points)

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


def load_nrrd(path):
    """Read a 3D NRRD file and return ``M`` indexed ``M[x, y, z]``.

    The array is 3-dimensional and its shape equals the header ``sizes``.
    """
    try:
        data, header = nrrd.read(str(path), index_order="F")
    except FileNotFoundError:
        raise ValueError(f"{path}: cannot read NRRD file") from None
    except OSError as exc:
        raise ValueError(f"{path}: cannot read NRRD file ({exc})") from exc
    except NRRDError as exc:
        raise ValueError(f"{path}: invalid NRRD ({exc})") from exc

    if getattr(data, "ndim", None) != 3:
        raise ValueError(f"{path}: expected a 3D volume, got shape {data.shape}")
    sizes = tuple(int(v) for v in header["sizes"])
    if tuple(data.shape) != sizes:
        raise ValueError(
            f"{path}: array shape {data.shape} does not match header sizes {sizes}"
        )
    return data


def load_planes(path):
    """Read planes from a CSV file. One plane per non-blank line, in order.

    A bad line raises ``ValueError`` naming the file and the 1-based line.
    """
    try:
        handle = open(path, "r", encoding="utf-8")
    except FileNotFoundError:
        raise ValueError(f"{path}: cannot read CSV file") from None
    except OSError as exc:
        raise ValueError(f"{path}: cannot read CSV file ({exc})") from exc

    planes = []
    with handle:
        for line_no, line in enumerate(handle, start=1):
            if line.strip() == "":
                continue
            plane = _parse_plane_line(line, line_no, path)
            try:
                check_plane(*plane.corners())
            except ValueError as exc:
                raise ValueError(f"{path}: line {line_no}: {exc}") from exc
            planes.append(plane)
    return planes


def _parse_plane_line(line, line_no, path):
    parts = [part.strip() for part in line.split(",")]
    if len(parts) not in (9, 12):
        raise ValueError(
            f"{path}: line {line_no}: expected 3 or 4 points "
            f"(9 or 12 comma-separated coordinates), got {len(parts)}"
        )
    try:
        coords = [float(part) for part in parts]
    except ValueError:
        raise ValueError(
            f"{path}: line {line_no}: coordinates must be numbers"
        ) from None
    if not all(np.isfinite(coords)):
        raise ValueError(
            f"{path}: line {line_no}: coordinates must be finite numbers"
        )
    n_points = len(coords) // 3
    points = np.asarray(coords, dtype=np.float64).reshape(n_points, 3)
    return Plane(points, line=line_no)
