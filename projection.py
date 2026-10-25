"""Project a 3D volume onto one triangle or trapezoid.

The definitions follow ALGORITHM.md sections 4 and 5. ``project_reference``
is the loop in section 4.1. ``project`` is the vectorised form in section 4.2.
Both return the same raw image ``E``. ``window`` and ``to_image`` turn ``E``
into an 8-bit grayscale image (section 4.4).
"""

import warnings

import numpy as np

# Distances below this are treated as zero (coincident points, zero base, flat).
_EPS = 1e-8


def round_half_up(values):
    """Round to the nearest integer. Halves round up: floor(v + 0.5).

    This is the only rounding rule used for sizes, row lengths and sample
    coordinates (ALGORITHM.md section 4.3). It is not banker's rounding.
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
    _warn_unequal_legs(ap, app, bb, cc)

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
    _warn_unequal_legs(ap, app, bb, cc)

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


def _is_collinear(ap, app, b, c):
    """True when the three or four corners lie on one line (zero area)."""
    edges = (app - ap, b - ap, c - ap)
    for i in range(3):
        for j in range(i + 1, 3):
            if np.linalg.norm(np.cross(edges[i], edges[j])) > _EPS:
                return False
    return True


def _geometry(a_prime, a_second, b, c):
    """Shared shape of the output image, or an error if the plane is degenerate."""
    ap = _as_point(a_prime, "a'")
    app = _as_point(a_second, "a''")
    bb = _as_point(b, "b")
    cc = _as_point(c, "c")

    corners = (ap, app, bb, cc)
    if all(_distance(corners[0], p) <= _EPS for p in corners[1:]):
        raise ValueError("degenerate plane: coincident points")
    if _distance(bb, cc) <= _EPS:
        raise ValueError("degenerate plane: zero base (b = c)")
    if _is_collinear(ap, app, bb, cc):
        raise ValueError("degenerate plane: collinear points")

    top_mid = (ap + app) / 2.0
    base_mid = (bb + cc) / 2.0
    height = _distance(top_mid, base_mid)
    if height <= _EPS:
        raise ValueError("degenerate plane: zero height")

    w_top = _distance(ap, app)
    w_base = _distance(bb, cc)
    H = round_half_up(height) + 1
    W = round_half_up(max(w_top, w_base)) + 1
    return ap, app, bb, cc, H, W


def _warn_unequal_legs(ap, app, b, c):
    """Issue 8: unequal legs are accepted, with a warning above 1 voxel."""
    left = _distance(ap, b)
    right = _distance(app, c)
    gap = abs(left - right)
    if gap > 1.0:
        warnings.warn(
            f"legs differ by {gap:.3f} voxels (more than 1); plane accepted",
            UserWarning,
            stacklevel=2,
        )
