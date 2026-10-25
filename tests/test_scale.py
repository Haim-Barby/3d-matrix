"""Same invariants on larger cubes. The planes stay about 16 voxels wide.

N = 500 is reserved for tests/benchmark.py. Planes are about 16 voxels
wide, so the reference loop stays cheap inside an N³ ramp.
"""

import time
import warnings

import numpy as np
import pytest

from projection import project, project_reference, round_half_up, to_image, window

SIZES = [8, 32, 128, 256]


def _ramp(shape):
    sx, sy, sz = shape
    x = np.arange(sx)[:, None, None]
    y = np.arange(sy)[None, :, None]
    z = np.arange(sz)[None, None, :]
    return (x + 10 * y + 100 * z).astype(np.uint16)


def _expected_shape(a_prime, a_second, b, c):
    """H = round(h)+1, W = round(max(top, base))+1."""
    ap = np.asarray(a_prime, dtype=np.float64)
    app = np.asarray(a_second, dtype=np.float64)
    bb = np.asarray(b, dtype=np.float64)
    cc = np.asarray(c, dtype=np.float64)
    height = np.linalg.norm((ap + app) / 2.0 - (bb + cc) / 2.0)
    width = max(np.linalg.norm(app - ap), np.linalg.norm(cc - bb))
    return round_half_up(height) + 1, round_half_up(width) + 1


def _project(M, corners):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        ref = project_reference(M, *corners)
        fast = project(M, *corners)
    assert ref.dtype == M.dtype == fast.dtype
    assert np.array_equal(ref, fast)
    assert ref.shape == _expected_shape(*corners)
    return ref


def _volume(n):
    """N³ ramp. A corner-only ramp would leave the 99th percentile at 0."""
    return _ramp((n, n, n))


def _planes(n):
    """A rectangle, a plane outside the cube, a plane that crosses the edge."""
    side = 5
    rectangle = ((1, 1, 1), (side, 1, 1), (1, side, 1), (side, side, 1))
    outside = ((-4.0, -4.0, -4.0), (-4.0, -4.0, -4.0), (-8.0, -1.0, -3.0), (-1.0, -1.0, -6.0))
    # Apex inside the ramp, base past x = 0, legs equal.
    crossing = ((2.0, 4.0, 1.0), (2.0, 4.0, 1.0), (-2.0, 0.0, 1.0), (6.0, 0.0, 1.0))
    rng = np.random.default_rng(1000 + n)
    random_planes = []
    for _ in range(4):
        points = rng.uniform(-1.0, 12.0, size=(4, 3))
        # Triangle, then a trapezoid, alternating.
        if len(random_planes) % 2 == 0:
            random_planes.append((points[0], points[0], points[1], points[2]))
        else:
            random_planes.append(tuple(points))
    return rectangle, outside, crossing, random_planes


@pytest.mark.parametrize("n", SIZES)
def test_tc13_invariants_hold_as_n_grows(n):
    """TC-13. FR-6, FR-7, NFR-1, NFR-2. Reference == vectorised, shape, window."""
    volume = _volume(n)
    rectangle, outside, crossing, random_planes = _planes(n)

    rect = _project(volume, rectangle)
    assert np.any(rect != 0)

    blank = _project(volume, outside)
    assert np.array_equal(blank, np.zeros_like(blank))

    crossed = _project(volume, crossing)
    assert np.any(crossed == 0)
    assert np.any(crossed != 0)

    matched = 0
    for corners in random_planes:
        try:
            _project(volume, corners)
        except ValueError:
            continue
        matched += 1
    assert matched >= 2

    lo, hi = window(volume)
    assert lo == pytest.approx(float(np.percentile(volume, 1)))
    assert hi == pytest.approx(float(np.percentile(volume, 99)))
    assert lo < hi
    image = to_image(rect, lo, hi)
    assert image.dtype == np.uint8
    assert image.shape == rect.shape
    assert int(image.min()) >= 0
    assert int(image.max()) <= 255


@pytest.mark.perf
def test_tc14_n128_projection_stays_cheap():
    """TC-14. NFR-5. Projection only, at N=128. Not the 30 fps requirement.

    Skip with: pytest -m "not perf"
    """
    volume = np.zeros((128, 128, 128), dtype=np.uint8)
    corners = ((0, 0, 10), (64, 0, 10), (0, 64, 10), (64, 64, 10))
    project(volume, *corners)
    repeats = 10
    started = time.perf_counter()
    for _ in range(repeats):
        project(volume, *corners)
    elapsed = time.perf_counter() - started
    assert elapsed < 2.0
