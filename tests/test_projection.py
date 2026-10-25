"""Small, hand-checkable projections. Each test is one TC id.

Volumes are a few voxels on a side. M[x, y, z] = x + 10y + 100z unless a
test says otherwise, so every sampled voxel has a known value. Expected
images were worked out from PROJECT: t = y/(H-1), n = round(dist), and
round(v) = floor(v+0.5).
"""

import warnings

import numpy as np
import pytest

from io_utils import load_planes
from projection import (
    project,
    project_reference,
    round_half_up,
    sample,
    to_image,
    window,
)


def _ramp(shape, dtype=np.uint16):
    sx, sy, sz = shape
    x = np.arange(sx)[:, None, None]
    y = np.arange(sy)[None, :, None]
    z = np.arange(sz)[None, None, :]
    return (x + 10 * y + 100 * z).astype(dtype)


def _both(M, a_prime, a_second, b, c):
    """Loop and vectorised PROJECT must return the same E."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        ref = project_reference(M, a_prime, a_second, b, c)
        fast = project(M, a_prime, a_second, b, c)
    assert ref.dtype == M.dtype
    assert np.array_equal(ref, fast)
    return ref


def test_tc01_round_halves_up():
    """TC-01. FR-8. floor(v+0.5), not half-to-even."""
    assert round_half_up(0.5) == 1
    assert round_half_up(-0.5) == 0
    assert round_half_up(1.5) == 2
    assert round_half_up(-1.5) == -1
    assert round_half_up(2.5) == 3
    assert round_half_up(2.4) == 2
    assert round_half_up([-0.6, -0.4, 0.5]).tolist() == [-1, 0, 1]


def test_tc02_sample_each_side_of_each_axis():
    """TC-02. FR-7, FR-8. Round, then reject both ends of x, y and z.

    On a 3×3×3 ramp the far corner M[2,2,2] is 222. A negative index must
    come back as 0, not that corner.
    """
    M = _ramp((3, 3, 3))
    assert M[2, 2, 2] == 222

    # x: -0.5 → 0 (inside), -0.6 → -1 (outside), 2.4 → 2, 2.5 → 3 (outside).
    assert sample(M, (-0.5, 0, 0)) == 0
    assert sample(M, (-0.6, 0, 0)) == 0
    assert sample(M, (0.5, 0, 0)) == 1
    assert sample(M, (2.4, 0, 0)) == 2
    assert sample(M, (2.5, 0, 0)) == 0
    # y
    assert sample(M, (0, -0.5, 0)) == 0
    assert sample(M, (0, -0.6, 0)) == 0
    assert sample(M, (0, 2.4, 0)) == 20
    assert sample(M, (0, 2.5, 0)) == 0
    # z
    assert sample(M, (0, 0, -0.5)) == 0
    assert sample(M, (0, 0, -0.6)) == 0
    assert sample(M, (0, 0, 2.4)) == 200
    assert sample(M, (0, 0, 2.5)) == 0
    assert sample(M, (-0.6, -0.6, -0.6)) == 0


def test_tc03_one_pixel_apex():
    """TC-03. FR-2, FR-6, NFR-1. h = 0.2 and base 0.4 both round to 0, so E is 1×1.

    The only sample is the apex (0.2, 0.2, 0) → voxel (0, 0, 0).
    The same image is checked for uint8 and uint32.
    """
    for dtype in (np.uint8, np.uint32):
        M = np.zeros((2, 2, 2), dtype=dtype)
        M[0, 0, 0] = 5
        image = _both(M, (0.2, 0.2, 0), (0.2, 0.2, 0), (0, 0, 0), (0.4, 0, 0))
        assert np.array_equal(image, np.array([[5]], dtype=dtype))


def test_tc04_axis_aligned_triangle_exact():
    """TC-04. FR-6, FR-7, NFR-1.

    Apex (2, 4, 0), base (0, 0, 0)–(4, 0, 0) on a 5×5×1 ramp.
    Height 4 → H = 5. Base length 4 → W = 5. Passing the apex as both
    a' and a'' is the triangle.
    """
    M = _ramp((5, 5, 1))
    apex, left, right = (2, 4, 0), (0, 0, 0), (4, 0, 0)
    image = _both(M, apex, apex, left, right)
    expected = np.array(
        [
            [0, 0, 42, 0, 0],
            [0, 32, 33, 0, 0],
            [0, 21, 22, 23, 0],
            [11, 12, 13, 14, 0],
            [0, 1, 2, 3, 4],
        ],
        dtype=np.uint16,
    )
    assert np.array_equal(image, expected)
    # Base row uses columns 0 and W-1 (fence-post). Apex row is one pixel.
    assert image[-1, 0] == M[0, 0, 0]
    assert image[-1, -1] == M[4, 0, 0]
    assert np.count_nonzero(image[0]) == 1


def test_tc05_trapezoid_lecturer_order_exact(tmp_path):
    """TC-05. FR-3, FR-6, NFR-1.

    Top (2, 0, 0)–(4, 0, 0), base (1, 2, 0)–(5, 2, 0) on a 6×3×1 ramp.
    Height 2 → H = 3. Longer base 4 → W = 5. The top row is centred
    (x0 = 1). CSV order is a', b, a'', c.
    """
    M = _ramp((6, 3, 1))
    a_prime, a_second = (2, 0, 0), (4, 0, 0)
    b, c = (1, 2, 0), (5, 2, 0)
    image = _both(M, a_prime, a_second, b, c)
    expected = np.array(
        [
            [0, 2, 3, 4, 0],
            [12, 13, 14, 15, 0],
            [21, 22, 23, 24, 25],
        ],
        dtype=np.uint16,
    )
    assert np.array_equal(image, expected)

    path = tmp_path / "one.csv"
    path.write_text(
        "Number of Points (3 or 4),x1,y1,z1,x2,y2,z2,x3,y3,z3,x4,y4,z4\n"
        "4,2,0,0, 1,2,0, 4,0,0, 5,2,0\n",
        encoding="utf-8",
    )
    plane = load_planes(path)[0]
    assert np.array_equal(
        _both(M, *plane.corners()),
        expected,
    )


def test_tc06_height_and_fencepost_on_the_wide_triangle():
    """TC-06. FR-6, NFR-1.

    Legs 10, base 16, true height 6. H = 7, not round(10)+1 = 11.
    W = 17, and the base row holds both endpoints.
    """
    M = np.zeros((17, 7, 1), dtype=np.uint16)
    M[8, 6, 0] = 100
    M[0, 0, 0] = 200
    M[16, 0, 0] = 300
    image = _both(M, (8, 6, 0), (8, 6, 0), (0, 0, 0), (16, 0, 0))
    assert image.shape == (7, 17)
    assert image[0, 8] == 100
    assert np.count_nonzero(image[0]) == 1
    assert image[-1, 0] == 200
    assert image[-1, -1] == 300


def test_tc07_non_integer_base_reaches_both_ends():
    """TC-07. FR-6, FR-8, NFR-1.

    Base (0,0,0)–(2,1,0) has length sqrt(5) ≈ 2.24, so n = 2 on the base
    and both endpoints are sampled. Apex (1, 0.5, 2) rounds to (1, 1, 2).
    """
    M = _ramp((3, 3, 3))
    image = _both(M, (1, 0.5, 2), (1, 0.5, 2), (0, 0, 0), (2, 1, 0))
    expected = np.array(
        [
            [0, 211, 0],
            [101, 112, 0],
            [0, 11, 12],
        ],
        dtype=np.uint16,
    )
    assert np.array_equal(image, expected)
    assert image[-1, 0] == M[0, 0, 0]
    assert image[-1, -1] == M[2, 1, 0]


def test_tc08_plane_outside_is_all_zero():
    """TC-08. FR-7, NFR-1. Every corner has x < 0. E is still the right shape."""
    M = _ramp((2, 2, 2), dtype=np.uint8)
    image = _both(M, (-2, 2, 1), (-2, 2, 1), (-3, 0, 1), (-1, 0, 1))
    assert image.shape == (3, 3)
    assert np.array_equal(image, np.zeros((3, 3), dtype=np.uint8))


def test_tc09_partial_plane_exact():
    """TC-09. FR-7, NFR-1.

    Apex (1, 3, 0) inside a 4×4×1 ramp. Base (-1, 0, 0)–(3, 0, 0) crosses
    x = 0, so the left base sample is 0 and the inside samples are the ramp.
    """
    M = _ramp((4, 4, 1))
    image = _both(M, (1, 3, 0), (1, 3, 0), (-1, 0, 0), (3, 0, 0))
    expected = np.array(
        [
            [0, 0, 31, 0, 0],
            [0, 20, 22, 0, 0],
            [10, 11, 11, 12, 0],
            [0, 0, 1, 2, 3],
        ],
        dtype=np.uint16,
    )
    assert np.array_equal(image, expected)


def test_tc10_leg_warning_threshold():
    """TC-10. FR-4. A gap of 1 voxel is quiet. A gap of 1.1 warns.

    Both planes are still projected, and the base ends on b and on round(c).
    """
    M = np.zeros((6, 6, 2), dtype=np.uint16)
    apex = (0.0, 0.0, 0.0)
    base_left = (4.0, 0.0, 0.0)
    # |ab| = 4, |ac| = 5, gap = 1.
    with warnings.catch_warnings():
        warnings.simplefilter("error", UserWarning)
        quiet = _both(M, apex, apex, base_left, (0.0, 5.0, 0.0))
    assert quiet.shape == (4, 7)

    M[4, 0, 0] = 21
    M[0, 5, 0] = 22
    base_right = (0.0, 5.1, 0.0)
    with pytest.warns(UserWarning, match="1.100"):
        ref = project_reference(M, apex, apex, base_left, base_right)
    with pytest.warns(UserWarning, match="1.100"):
        fast = project(M, apex, apex, base_left, base_right)
    assert np.array_equal(ref, fast)
    assert ref[-1, 0] == 21
    assert ref[-1, -1] == 22


def test_tc11_degenerate_planes_are_rejected():
    """TC-11. FR-4. Only a broken plane is an error. The message says why."""
    M = np.zeros((6, 6, 6), dtype=np.uint8)
    with pytest.raises(ValueError, match="coincident"):
        project(M, (1, 1, 1), (1, 1, 1), (1, 1, 1), (1, 1, 1))
    with pytest.raises(ValueError, match="zero base"):
        project(M, (0, 5, 0), (0, 5, 0), (1, 0, 0), (1, 0, 0))
    with pytest.raises(ValueError, match="zero leg"):
        project(M, (0, 5, 0), (2, 5, 0), (0, 5, 0), (4, 0, 0))
    with pytest.raises(ValueError, match="collinear"):
        project(M, (0, 0, 0), (0, 0, 0), (1, 0, 0), (4, 0, 0))
    with pytest.raises(ValueError, match="zero height"):
        project(M, (0, 0, 0), (2, 1, 0), (0, 1, 0), (2, 0, 0))


def test_tc12_window_and_to_image():
    """TC-12. FR-6. One window for the volume. A flat window is a black image.

    Eight voxels, seven of them 0 and one 10. The 99th percentile is 9.3,
    not the maximum 10, so a sample of 10 clips to 255.
    """
    volume = np.zeros((2, 2, 2), dtype=np.uint16)
    volume[1, 1, 1] = 10
    lo, hi = window(volume)
    assert lo == 0.0
    assert hi == pytest.approx(9.3)
    assert np.array_equal(to_image(np.array([[0, 10]], dtype=np.uint16), lo, hi), [[0, 255]])

    # 0, 50, 100, 200 over [0, 200], and a value above the window.
    scaled = to_image(np.array([[0, 50, 100, 200, 400]], dtype=np.uint16), 0, 200)
    assert scaled.dtype == np.uint8
    assert scaled.tolist() == [[0, 64, 128, 255, 255]]

    constant = np.full((2, 2, 2), 7, dtype=np.uint8)
    assert window(constant) == (7.0, 7.0)
    black = to_image(np.array([[7, 0, 3]], dtype=np.uint8), 7, 7)
    assert black.dtype == np.uint8
    assert np.array_equal(black, [[0, 0, 0]])
