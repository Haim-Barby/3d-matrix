"""Unit tests for the projection algorithm (ALGORITHM.md sections 3–5)."""

import warnings

import numpy as np
import pytest

from projection import (
    project,
    project_reference,
    round_half_up,
    sample,
    to_image,
    window,
)


def _both(M, a_prime, a_second, b, c):
    """Run the loop and the vectorised code and require the same image."""
    ref = project_reference(M, a_prime, a_second, b, c)
    fast = project(M, a_prime, a_second, b, c)
    assert ref.shape == fast.shape
    assert ref.dtype == M.dtype
    assert fast.dtype == M.dtype
    assert np.array_equal(ref, fast)
    return ref


def test_round_half_up_not_bankers():
    # 0.5 and -1.5 distinguish floor(v + 0.5) from numpy's half-to-even.
    assert round_half_up(0.5) == 1
    assert round_half_up(-0.5) == 0
    assert round_half_up(1.5) == 2
    assert round_half_up(-1.5) == -1
    assert round_half_up(2.5) == 3
    assert round_half_up([-0.6, -0.4, 0.5]).tolist() == [-1, 0, 1]


def test_issue1_wide_triangle_uses_row_column_axes():
    # Dab = 10, Dbc = 16, true height h = 6. A swapped E[x][y] would not
    # have shape (H, W) = (7, 17), or would index past the short axis.
    M = np.zeros((17, 7, 1), dtype=np.uint16)
    apex = (8, 6, 0)
    base_left = (0, 0, 0)
    base_right = (16, 0, 0)
    image = _both(M, apex, apex, base_left, base_right)
    assert image.shape == (7, 17)
    assert image.shape[1] > image.shape[0]


def test_issue2_base_row_includes_both_endpoints():
    M = np.zeros((17, 7, 1), dtype=np.uint16)
    M[0, 0, 0] = 200
    M[16, 0, 0] = 300
    apex = (8, 6, 0)
    base_left = (0, 0, 0)
    base_right = (16, 0, 0)
    image = _both(M, apex, apex, base_left, base_right)
    # W = round(Dbc) + 1 = 17, so the base uses columns 0 and W - 1.
    assert image.shape[1] == 17
    assert image[-1, 0] == 200
    assert image[-1, -1] == 300


def test_issue3_non_integer_length_still_samples_far_vertex():
    # dist(b, c) = sqrt(20) ≈ 4.47. Stepping by 1 would stop short of c.
    # The apex is on the perpendicular bisector, so the legs match.
    M = np.zeros((6, 6, 6), dtype=np.uint16)
    apex = (2, 1, 5)
    base_left = (0, 0, 0)
    base_right = (4, 2, 0)
    M[0, 0, 0] = 11
    M[4, 2, 0] = 22
    image = _both(M, apex, apex, base_left, base_right)
    assert image[-1, 0] == 11
    assert image[-1, -1] == 22


def test_issue4_row_count_follows_true_height():
    # Dab = 10, Dbc = 16, h = 6, H = round(h) + 1 = 7, not Dab or Dab + 1.
    M = np.zeros((17, 7, 1), dtype=np.uint16)
    image = _both(M, (8, 6, 0), (8, 6, 0), (0, 0, 0), (16, 0, 0))
    assert image.shape[0] == 7


def test_issue5_apex_row_samples_the_apex_once():
    M = np.zeros((17, 7, 1), dtype=np.uint16)
    M[8, 6, 0] = 100
    image = _both(M, (8, 6, 0), (8, 6, 0), (0, 0, 0), (16, 0, 0))
    center = (image.shape[1] - 1) // 2
    assert center == 8
    assert image[0, center] == 100
    assert np.count_nonzero(image[0]) == 1


def test_issue6_rounds_before_bounds_check_on_both_sides():
    M = np.zeros((5, 5, 5), dtype=np.uint16)
    M[0, :, :] = 7
    M[4, :, :] = 999

    # -0.4 -> 0 (inside). -0.6 -> -1 (outside, not the far slice).
    assert sample(M, (-0.4, 2, 2)) == 7
    assert sample(M, (-0.5, 2, 2)) == 7
    assert sample(M, (-0.6, 2, 2)) == 0
    # 4.4 -> 4 (inside). 4.5 -> 5 (outside, not wrapped to x = 0).
    assert sample(M, (4.4, 2, 2)) == 999
    assert sample(M, (4.5, 2, 2)) == 0
    assert sample(M, (4.6, 2, 2)) == 0

    # A whole triangle sitting on x = -0.6 must not read M[4, ...].
    image = _both(
        M,
        (-0.6, 2, 2),
        (-0.6, 2, 2),
        (-0.6, 0, 0),
        (-0.6, 0, 4),
    )
    assert image.shape[0] > 0 and image.shape[1] > 0
    assert np.all(image == 0)


def test_issue8_unequal_legs_warn_and_still_reach_c():
    M = np.zeros((6, 6, 2), dtype=np.uint16)
    apex = (0.0, 0.0, 0.0)
    base_left = (4.0, 0.0, 0.0)
    # |ac| - |ab| = 1 exactly: accepted, no warning.
    base_right = (0.0, 5.0, 0.0)
    with warnings.catch_warnings():
        warnings.simplefilter("error", UserWarning)
        _both(M, apex, apex, base_left, base_right)

    # Gap of 1.1 voxels: warning, and the base still ends on round(c).
    base_right = (0.0, 5.1, 0.0)
    M[4, 0, 0] = 21
    M[0, 5, 0] = 22
    with pytest.warns(UserWarning, match="legs differ"):
        ref = project_reference(M, apex, apex, base_left, base_right)
    with pytest.warns(UserWarning, match="legs differ"):
        fast = project(M, apex, apex, base_left, base_right)
    assert np.array_equal(ref, fast)
    assert ref[-1, 0] == 21
    assert ref[-1, -1] == 22


def test_triangle_equals_trapezoid_with_zero_top():
    rng = np.random.default_rng(1)
    M = rng.integers(0, 400, size=(12, 10, 8), dtype=np.uint16)
    apex = np.array([4.0, 8.0, 2.0])
    base_left = np.array([1.0, 1.0, 2.0])
    base_right = np.array([7.0, 1.0, 2.0])
    triangle = _both(M, apex, apex, base_left, base_right)
    trapezoid = _both(M, apex, apex.copy(), base_left, base_right)
    assert np.array_equal(triangle, trapezoid)


def test_axis_aligned_rectangle_matches_volume_slice():
    rng = np.random.default_rng(2)
    M = rng.integers(0, 500, size=(12, 9, 4), dtype=np.uint16)
    z = 2
    # Rectangle x = 1..8, y = 2..7 at this z. E is indexed (y, x).
    image = _both(
        M,
        (1, 2, z),
        (8, 2, z),
        (1, 7, z),
        (8, 7, z),
    )
    assert image.shape == (6, 8)
    assert np.array_equal(image, M[1:9, 2:8, z].T)


def test_trapezoid_centers_the_shorter_row():
    M = np.zeros((12, 6, 2), dtype=np.uint16)
    M[0, 0, 0] = 1
    M[10, 0, 0] = 2
    M[3, 4, 0] = 3
    M[7, 4, 0] = 4
    image = _both(M, (0, 0, 0), (10, 0, 0), (3, 4, 0), (7, 4, 0))
    assert image.shape == (5, 11)
    assert image[0, 0] == 1
    assert image[0, 10] == 2
    # Base length 4 in a width of 11: x0 = (11 - 1 - 4) // 2 = 3.
    assert image[-1, 3] == 3
    assert image[-1, 7] == 4
    assert image[-1, 0] == 0
    assert image[-1, 10] == 0


def test_vectorized_matches_reference_on_random_planes():
    rng = np.random.default_rng(0)
    M = rng.integers(0, 1000, size=(24, 20, 18), dtype=np.uint16)
    triangles = 0
    trapezoids = 0
    for _ in range(80):
        if triangles >= 12 and trapezoids >= 6:
            break
        coords = rng.uniform(-2.0, 26.0, size=(4, 3))
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", UserWarning)
                if triangles < 12:
                    _both(M, coords[0], coords[0], coords[1], coords[2])
                    triangles += 1
                elif trapezoids < 6:
                    _both(M, coords[0], coords[1], coords[2], coords[3])
                    trapezoids += 1
        except ValueError:
            continue
    assert triangles == 12
    assert trapezoids == 6


def test_plane_entirely_outside_is_zero():
    M = np.arange(27, dtype=np.uint8).reshape(3, 3, 3)
    image = _both(
        M,
        (-10, -10, -8),
        (-10, -10, -8),
        (-8, -2, -6),
        (-4, -3, -9),
    )
    assert np.all(image == 0)
    assert image.dtype == np.uint8


def test_partial_plane_keeps_outside_samples_at_zero():
    M = np.full((8, 8, 8), 5, dtype=np.uint8)
    # Apex inside, both base vertices outside, legs equal.
    image = _both(M, (4, 6, 4), (4, 6, 4), (-2, 1, 4), (10, 1, 4))
    assert np.any(image == 5)
    assert np.any(image == 0)


def test_very_flat_plane_is_a_single_apex_row():
    # h = 0.2 rounds to 0, so H = 1. The only row is the apex (t = 0).
    M = np.zeros((5, 5, 3), dtype=np.uint8)
    M[1, 0, 1] = 42
    image = _both(M, (1, 0.2, 1), (1, 0.2, 1), (0, 0, 1), (2, 0, 1))
    assert image.shape[0] == 1
    assert image[0, (image.shape[1] - 1) // 2] == 42


def test_degenerate_planes_are_rejected():
    M = np.zeros((6, 6, 6), dtype=np.uint8)
    with pytest.raises(ValueError, match="coincident points"):
        project(M, (1, 1, 1), (1, 1, 1), (1, 1, 1), (1, 1, 1))
    with pytest.raises(ValueError, match="zero base"):
        project(M, (0, 5, 0), (0, 5, 0), (1, 0, 0), (1, 0, 0))
    # Height is not zero, but the three points are on one line.
    with pytest.raises(ValueError, match="collinear"):
        project(M, (0, 0, 0), (0, 0, 0), (1, 0, 0), (4, 0, 0))
    # Crossed trapezoid: the midpoints coincide, the corners are not collinear.
    with pytest.raises(ValueError, match="zero height"):
        project(M, (0, 0, 0), (2, 1, 0), (0, 1, 0), (2, 0, 0))
    with pytest.raises(ValueError, match="3 coordinates"):
        project(M, (0, 0), (0, 0), (1, 0, 0), (0, 1, 0))


def test_window_uses_global_percentiles():
    volume = np.arange(100, dtype=np.uint16)
    lo, hi = window(volume)
    assert lo == float(np.percentile(volume, 1))
    assert hi == float(np.percentile(volume, 99))
    assert lo < hi

    constant = np.full((4, 4, 4), 7, dtype=np.uint8)
    lo, hi = window(constant)
    assert lo == hi == 7.0


def test_to_image_scales_clips_and_handles_constant_window():
    raw = np.array([[0, 50, 100, 200, 400]], dtype=np.uint16)
    image = to_image(raw, 0, 200)
    assert image.dtype == np.uint8
    assert image.shape == raw.shape
    # 0 -> 0, 50/200*255 = 63.75 -> 64, 100/200*255 = 127.5 -> 128,
    # 200 -> 255, 400 clips to 255.
    assert image.tolist() == [[0, 64, 128, 255, 255]]

    black = to_image(np.array([[5, 0, 9]], dtype=np.uint8), 3, 3)
    assert black.dtype == np.uint8
    assert np.all(black == 0)

    below = to_image(np.array([[0, 10, 20, 30]], dtype=np.uint16), 10, 20)
    assert below.tolist() == [[0, 0, 255, 255]]
