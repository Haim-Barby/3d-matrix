"""Project a 3D volume onto one triangle or trapezoid.

The definitions follow ALGORITHM.md sections 4 and 5. ``project_reference``
is the loop in section 4.1. ``project`` is the vectorised form in section 4.2.
Both return the same raw image ``E``. ``window`` and ``to_image`` turn ``E``
into an 8-bit grayscale image (section 4.4).
"""

import numpy as np

# Lengths and distances, in voxel-index units. A difference of this size is
# still a valid plane. Anything larger raises ValueError. The same number is
# used for leg lengths, the height, the distance from a line, and the
# distance from a plane. It is not applied to an unnormalized cross product.
TOLERANCE = 0.001


def round_half_up(values):
    """Nearest integer. A value halfway between two integers rounds up.

    ``floor(v + 0.5)`` is nearest-neighbour sampling with one tie-break:
    ``1.5`` becomes ``2``, and ``-0.5`` becomes ``0``. It is not banker's
    rounding, and it is not interpolation. Sizes, row lengths, and sample
    coordinates all use this rule (ALGORITHM.md section 4.3).
    """
    arr = np.asarray(values, dtype=np.float64)
    rounded = np.floor(arr + 0.5)
    if arr.ndim == 0:
        return int(rounded)
    return rounded.astype(np.int64)


def sample(M, p):
    """SAMPLE(M, p). Nearest voxel, or 0 when that voxel is outside M.

    Round first, then test both ends of every axis. Negative indices are
    outside: numpy would otherwise wrap them to the far side of the volume.
    """
    sx, sy, sz = M.shape
    i, j, k = (int(v) for v in round_half_up(p))
    if 0 <= i < sx and 0 <= j < sy and 0 <= k < sz:
        return M[i, j, k]
    return 0


def project_reference(M, a_prime, a_second, b, c):
    """PROJECT by the section 4.1 loop. A triangle is a' = a'' = a."""
    _check_volume(M)
    ap, app, bb, cc, H, W = _geometry(a_prime, a_second, b, c)

    E = np.zeros((H, W), dtype=M.dtype)
    for y in range(H):
        t = y / (H - 1) if H > 1 else 0.0
        a1 = ap + t * (bb - ap)
        a2 = app + t * (cc - app)
        n = round_half_up(_distance(a1, a2))
        if n > 0:
            dp = (a2 - a1) / n
        else:
            dp = np.zeros(3, dtype=np.float64)
        x0 = (W - 1 - n) // 2
        for k in range(n + 1):
            p = a1 + k * dp
            x = x0 + k
            # x0 is non-negative when the row fits. Reject a bad index
            # instead of letting numpy wrap a negative column.
            if x < 0 or x >= W:
                raise RuntimeError(
                    f"sample column {x} is outside the image width {W}"
                )
            E[y, x] = sample(M, p)
    return E


def project(M, a_prime, a_second, b, c):
    """PROJECT with numpy, one image at a time (ALGORITHM.md section 4.2).

    Pixels outside the triangle or trapezoid, and samples outside the volume,
    stay 0. The result matches ``project_reference``.
    """
    _check_volume(M)
    ap, app, bb, cc, H, W = _geometry(a_prime, a_second, b, c)

    if H > 1:
        t = np.arange(H, dtype=np.float64) / (H - 1)
    else:
        t = np.zeros(1, dtype=np.float64)

    # Endpoints of every row: a1 on the left leg, a2 on the right leg.
    a1 = ap + t[:, None] * (bb - ap)
    a2 = app + t[:, None] * (cc - app)
    delta = a2 - a1
    n = round_half_up(np.linalg.norm(delta, axis=1))

    dp = np.zeros_like(delta)
    nonzero = n > 0
    dp[nonzero] = delta[nonzero] / n[nonzero, None]

    x0 = (W - 1 - n) // 2
    if np.any(x0 < 0) or np.any(x0 + n >= W):
        raise RuntimeError("a row does not fit in the image width")

    # k = x - x0. Columns with k outside 0..n are outside the polygon.
    columns = np.arange(W, dtype=np.int64)
    k = columns[None, :] - x0[:, None]
    inside_polygon = (k >= 0) & (k <= n[:, None])

    points = a1[:, None, :] + k[:, :, None] * dp[:, None, :]
    ijk = round_half_up(points)
    i = ijk[..., 0]
    j = ijk[..., 1]
    kk = ijk[..., 2]

    sx, sy, sz = M.shape
    inside_volume = (
        (i >= 0) & (i < sx)
        & (j >= 0) & (j < sy)
        & (kk >= 0) & (kk < sz)
    )
    mask = inside_polygon & inside_volume

    E = np.zeros((H, W), dtype=M.dtype)
    E[mask] = M[i[mask], j[mask], kk[mask]]
    return E


def window(M):
    """WINDOW(M): 1st and 99th percentiles of every voxel in the volume.

    One window is shared by every plane, so a voxel keeps the same gray level
    in every image. Returns ``(lo, hi)`` as floats.
    """
    lo, hi = np.percentile(np.asarray(M), (1, 99))
    return float(lo), float(hi)


def to_image(E, lo, hi):
    """TO_IMAGE(E, lo, hi): 8-bit grayscale in the global window.

    A constant window (``hi == lo``) returns an all-zero image, so there is
    no division by zero. Values outside [lo, hi] clip to black or white.
    """
    if hi == lo:
        return np.zeros(np.shape(E), dtype=np.uint8)
    scaled = (np.asarray(E, dtype=np.float64) - lo) / (hi - lo)
    np.clip(scaled, 0.0, 1.0, out=scaled)
    return np.floor(scaled * 255.0 + 0.5).astype(np.uint8)


def _check_volume(M):
    if not isinstance(M, np.ndarray) or M.ndim != 3:
        raise ValueError("M must be a 3D numpy array")


def _as_point(point, name):
    arr = np.asarray(point, dtype=np.float64)
    if arr.shape != (3,):
        raise ValueError(f"{name} must have 3 coordinates, got shape {arr.shape}")
    if not np.isfinite(arr).all():
        raise ValueError(f"{name} has non-finite coordinates")
    return arr.copy()


def _distance(p, q):
    delta = np.asarray(p, dtype=np.float64) - np.asarray(q, dtype=np.float64)
    return float(np.linalg.norm(delta))


def _point_line_distance(point, start, end):
    """Distance from ``point`` to the line through ``start`` and ``end``."""
    direction = end - start
    length = float(np.linalg.norm(direction))
    if length <= TOLERANCE:
        return float(np.linalg.norm(point - start))
    return float(np.linalg.norm(np.cross(point - start, direction)) / length)


def _plane_distance(point, a, b, c):
    """Distance from ``point`` to the plane through ``a``, ``b`` and ``c``.

    Returns None when those three points do not define a plane (the height
    of triangle a-b-c is within ``TOLERANCE``).
    """
    edge = b - a
    length = float(np.linalg.norm(edge))
    if length <= TOLERANCE:
        return None
    normal = np.cross(edge, c - a)
    height = float(np.linalg.norm(normal) / length)
    if height <= TOLERANCE:
        return None
    unit = normal / np.linalg.norm(normal)
    return abs(float(np.dot(point - a, unit)))


def _plane_normal(axis, other):
    """Unit normal of ``axis`` and ``other``, or None when they are parallel.

    ``axis`` is already a unit vector. The test is the length
    ``||axis × other|| / ||other||``, not the raw cross product.
    """
    length = float(np.linalg.norm(other))
    if length <= TOLERANCE:
        return None
    normal = np.cross(axis, other)
    if float(np.linalg.norm(normal)) / length <= TOLERANCE:
        return None
    return normal / np.linalg.norm(normal)


def _legs_cross(ap, app, bb, cc):
    """True when leg a'→b properly crosses leg a''→c."""
    top = app - ap
    top_len = float(np.linalg.norm(top))
    if top_len <= TOLERANCE:
        return False
    axis_u = top / top_len
    normal = _plane_normal(axis_u, bb - ap)
    if normal is None:
        normal = _plane_normal(axis_u, cc - bb)
    if normal is None:
        return False
    axis_v = np.cross(normal, axis_u)

    def flat(point):
        delta = point - ap
        return float(np.dot(delta, axis_u)), float(np.dot(delta, axis_v))

    return _segments_cross(flat(ap), flat(bb), flat(app), flat(cc))


def _segments_cross(p, q, r, s):
    """True when open segments pq and rs cross in 2D."""

    def orient(a, b, c):
        return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])

    o1 = orient(p, q, r)
    o2 = orient(p, q, s)
    o3 = orient(r, s, p)
    o4 = orient(r, s, q)
    return o1 * o2 < 0.0 and o3 * o4 < 0.0


def _validate(ap, app, bb, cc):
    """Raise ValueError if the four corners are not an isosceles plane.

    ``a' == a''`` is the triangle and is not an error. A trapezoid must be
    planar, with parallel bases in the same direction, equal legs, and the
    midline perpendicular to the bases (so a slanted parallelogram fails).
    """
    if all(_distance(ap, point) <= TOLERANCE for point in (app, bb, cc)):
        raise ValueError("degenerate plane: coincident points")
    base_len = _distance(bb, cc)
    if base_len <= TOLERANCE:
        raise ValueError("degenerate plane: zero base (b = c)")
    leg_left = _distance(ap, bb)
    leg_right = _distance(app, cc)
    if leg_left <= TOLERANCE or leg_right <= TOLERANCE:
        raise ValueError("degenerate plane: zero leg")

    top_len = _distance(ap, app)
    top_mid = (ap + app) / 2.0
    base_mid = (bb + cc) / 2.0
    if _distance(top_mid, base_mid) <= TOLERANCE:
        raise ValueError("degenerate plane: zero height")
    if top_len <= TOLERANCE:
        if _point_line_distance(ap, bb, cc) <= TOLERANCE:
            raise ValueError("degenerate plane: collinear points")
    elif (
        _point_line_distance(ap, bb, cc) <= TOLERANCE
        and _point_line_distance(app, bb, cc) <= TOLERANCE
    ):
        raise ValueError("degenerate plane: collinear points")

    if abs(leg_left - leg_right) > TOLERANCE:
        raise ValueError(
            f"degenerate plane: unequal legs ({leg_left:.4f} and {leg_right:.4f})"
        )
    if top_len <= TOLERANCE:
        return

    gap = _plane_distance(app, ap, bb, cc)
    if gap is None:
        gap = _plane_distance(cc, ap, app, bb)
    if gap is None:
        raise ValueError("degenerate plane: collinear points")
    if gap > TOLERANCE:
        raise ValueError(f"trapezoid is not planar (distance {gap:.4f})")

    base_vec = cc - bb
    top_vec = app - ap
    unit_base = base_vec / base_len
    parallel_gap = float(np.linalg.norm(top_vec - np.dot(top_vec, unit_base) * unit_base))
    if parallel_gap > TOLERANCE:
        raise ValueError(f"trapezoid bases are not parallel (gap {parallel_gap:.4f})")

    unit_top = top_vec / top_len
    if float(np.dot(unit_top, unit_base)) <= 0.0 or _legs_cross(ap, app, bb, cc):
        raise ValueError("trapezoid is self-intersecting")

    shift = abs(float(np.dot(top_mid - base_mid, unit_base)))
    if shift > TOLERANCE:
        raise ValueError(f"trapezoid is not symmetric (shift {shift:.4f})")


def _geometry(a_prime, a_second, b, c):
    """Shared shape of the output image, or an error if the plane is invalid."""
    ap = _as_point(a_prime, "a'")
    app = _as_point(a_second, "a''")
    bb = _as_point(b, "b")
    cc = _as_point(c, "c")
    _validate(ap, app, bb, cc)

    top_mid = (ap + app) / 2.0
    base_mid = (bb + cc) / 2.0
    height = _distance(top_mid, base_mid)
    w_top = _distance(ap, app)
    w_base = _distance(bb, cc)
    H = round_half_up(height) + 1
    W = round_half_up(max(w_top, w_base)) + 1
    return ap, app, bb, cc, H, W


def check_plane(a_prime, a_second, b, c):
    """Raise ValueError if the corners are not a valid triangle or trapezoid.

    Called by ``project`` and ``project_reference`` as well as by the CSV
    loader, so a direct call is held to the same rules.
    """
    _geometry(a_prime, a_second, b, c)
