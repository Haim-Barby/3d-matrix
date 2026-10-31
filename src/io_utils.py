"""Load a volume from NRRD and planes from CSV.

NRRD is read with pynrrd ``index_order='F'``, so the array is ``M[x, y, z]``
and matches the header ``sizes`` (ALGORITHM.md issue 7).

CSV (lecturer format): a header line, then one plane per row. A row starts
with ``3`` or ``4``. A triangle is ``a, b, c`` (9 coordinates) and may end
with empty fields. A trapezoid is ``a', b, a'', c`` (12 coordinates); the
equal legs are ``a'→b`` and ``a''→c``. ``Plane.corners`` maps that order to
``PROJECT(a', a'', b, c)``. Blank lines and ``#`` comments are skipped.
Coordinates are voxel indices (real values and out-of-volume points allowed).
Sample files live in ``csv/`` and ``video/``.
"""

import numpy as np
import nrrd
from nrrd.errors import NRRDError

from plane import Plane
from projection import check_plane


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
    """Read planes from a lecturer-format CSV file, in row order.

    Skips the header, blank lines, and ``#`` comments. A bad line raises
    ``ValueError`` naming the file and the 1-based line. The demo uses
    ``read_plane_rows`` instead, so one bad row does not stop the video.
    """
    planes = []
    for line_no, plane, error in read_plane_rows(path):
        if error is not None:
            raise ValueError(f"{path}: line {line_no}: {error}") from None
        planes.append(plane)
    return planes


def read_plane_rows(path):
    """One result per data row: ``(line_no, plane, error)``.

    ``plane`` is set when the row parses and passes ``check_plane``.
    ``error`` is a short reason otherwise. The header, blank lines, and
    ``#`` comments produce no entry. A missing or unreadable file raises
    ``ValueError``.
    """
    try:
        handle = open(path, "r", encoding="utf-8")
    except FileNotFoundError:
        raise ValueError(f"{path}: cannot read CSV file") from None
    except OSError as exc:
        raise ValueError(f"{path}: cannot read CSV file ({exc})") from exc

    rows = []
    with handle:
        for line_no, line in enumerate(handle, start=1):
            stripped = line.strip()
            if stripped == "" or stripped.startswith("#"):
                continue
            if stripped.startswith("Number of Points"):
                continue
            try:
                plane = _parse_plane_line(line)
                check_plane(*plane.corners())
            except ValueError as exc:
                rows.append((line_no, None, str(exc)))
                continue
            plane.line = line_no
            rows.append((line_no, plane, None))
    return rows


def _parse_plane_line(line):
    parts = [part.strip() for part in line.split(",")]
    if not parts or parts[0] == "":
        raise ValueError("expected 3 or 4 points, got nothing")
    try:
        count = int(parts[0])
    except ValueError:
        raise ValueError(f"expected 3 or 4 points, got {parts[0]!r}") from None
    if count not in (3, 4):
        raise ValueError(f"expected 3 or 4 points, got {count}")

    # A triangle row may pad the unused 4th point with empty fields.
    fields = parts[1:]
    while fields and fields[-1] == "":
        fields.pop()
    if any(field == "" for field in fields) or len(fields) != count * 3:
        raise ValueError(
            f"point count is {count} but the line has {len(fields)} coordinates"
        )
    try:
        coords = [float(part) for part in fields]
    except ValueError:
        raise ValueError("coordinates must be numbers") from None
    if not all(np.isfinite(coords)):
        raise ValueError("coordinates must be finite numbers")
    points = np.asarray(coords, dtype=np.float64).reshape(count, 3)
    return Plane(points)
