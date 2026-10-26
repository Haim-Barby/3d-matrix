"""NRRD axis order and CSV plane parsing."""

import warnings
from pathlib import Path

import numpy as np
import nrrd
import pytest

from io_utils import load_nrrd, load_planes
from plane import Plane
from projection import project


def test_tc16_nrrd_uint16_axis_order(tmp_path):
    """TC-16. FR-2, NFR-1. 4×5×6 uint16, index_order F, so M[1,2,3] stays 321."""
    # Non-cubic 4 x 5 x 6 volume. M[x, y, z] = x + 10y + 100z, so M[1, 2, 3] = 321.
    sx, sy, sz = 4, 5, 6
    x = np.arange(sx, dtype=np.uint16)[:, None, None]
    y = np.arange(sy, dtype=np.uint16)[None, :, None]
    z = np.arange(sz, dtype=np.uint16)[None, None, :]
    volume = x + 10 * y + 100 * z
    assert volume.shape == (4, 5, 6)
    assert volume[1, 2, 3] == 321

    path = tmp_path / "axis_order.nrrd"
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        nrrd.write(str(path), volume, index_order="F")

    loaded = load_nrrd(path)
    assert loaded.shape == (4, 5, 6)
    assert loaded.dtype == np.uint16
    assert loaded[1, 2, 3] == 321
    assert np.array_equal(loaded, volume)


def test_tc17_nrrd_uint8_and_uint32(tmp_path):
    """TC-17. FR-2. 8-bit and 32-bit volumes come back as M[x, y, z]."""
    for dtype in (np.uint8, np.uint32):
        volume = np.zeros((2, 2, 2), dtype=dtype)
        volume[1, 1, 1] = 7
        path = tmp_path / f"v_{dtype.__name__}.nrrd"
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            nrrd.write(str(path), volume, index_order="F")
        loaded = load_nrrd(path)
        assert loaded.dtype == dtype
        assert loaded.shape == (2, 2, 2)
        assert loaded[1, 1, 1] == 7
        assert np.array_equal(loaded, volume)


def test_tc31_int16_negative_voxel(tmp_path):
    """TC-31. FR-2, FR-7. A negative int16 voxel survives load and projection.

    The base of the triangle is at y=3, outside a volume of size 2, so those
    samples are 0. The apex is the negative voxel.
    """
    volume = np.zeros((2, 2, 2), dtype=np.int16)
    volume[0, 0, 0] = -4
    path = tmp_path / "signed.nrrd"
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        nrrd.write(str(path), volume, index_order="F")

    loaded = load_nrrd(path)
    assert loaded.dtype == np.int16
    assert loaded[0, 0, 0] == -4
    assert np.array_equal(loaded, volume)

    image = project(loaded, (0, 0, 0), (0, 0, 0), (-1, 3, 0), (1, 3, 0))
    assert image.dtype == np.int16
    assert image.shape == (4, 3)
    assert image[0, 1] == -4
    assert np.array_equal(image[3], [0, 0, 0])


def test_tc18_bad_nrrd_names_the_file(tmp_path):
    """TC-18. FR-5. A bad file and a 2D array name the path. Neither is a volume."""
    bad = tmp_path / "notes.nrrd"
    bad.write_text("this is not an nrrd\n", encoding="utf-8")
    with pytest.raises(ValueError, match="notes.nrrd"):
        load_nrrd(bad)

    flat = np.arange(12, dtype=np.uint8).reshape(3, 4)
    flat_path = tmp_path / "flat.nrrd"
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        nrrd.write(str(flat_path), flat, index_order="F")
    with pytest.raises(ValueError, match="3D"):
        load_nrrd(flat_path)


def test_tc19_csv_triangle_and_trapezoid(tmp_path):
    """TC-19. FR-3. Count 3 then count 4. Trapezoid order is a', b, a'', c."""
    path = tmp_path / "planes.csv"
    path.write_text(
        "\n".join(
            [
                "3,0, 0, 0, 0, 0, 10, 10, 0, 5,,,",
                "",
                "3,0.5, 1, 2, 3, 4, 5, 6, 7, 8,,,",
                "4,1, 1, 1, 1, 5, 1, 4, 1, 1, 4, 5, 1",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    planes = load_planes(path)
    assert len(planes) == 3
    assert all(isinstance(plane, Plane) for plane in planes)
    assert planes[0].is_triangle
    assert planes[0].line == 1
    assert np.array_equal(
        planes[0].points,
        np.array([[0, 0, 0], [0, 0, 10], [10, 0, 5]], dtype=np.float64),
    )
    assert planes[1].is_triangle
    assert planes[1].line == 3
    assert planes[1].points[0, 0] == 0.5
    assert not planes[2].is_triangle
    assert planes[2].points.shape == (4, 3)
    assert planes[2].line == 4
    # CSV order a', b, a'', c maps to PROJECT order a', a'', b, c.
    a_prime, a_second, base_left, base_right = planes[2].corners()
    assert np.array_equal(a_prime, [1, 1, 1])
    assert np.array_equal(a_second, [4, 1, 1])
    assert np.array_equal(base_left, [1, 5, 1])
    assert np.array_equal(base_right, [4, 5, 1])
    apex, again, base_left, base_right = planes[0].corners()
    assert np.array_equal(apex, again)
    assert np.array_equal(base_right, [10, 0, 5])


def test_tc21_csv_bad_values_name_the_line(tmp_path):
    """TC-21. FR-5. A bad count, a word, or a non-finite value names the line."""
    path = tmp_path / "bad.csv"
    path.write_text(
        "\n".join(
            [
                "3,0,0,0, 1,0,0, 0,1,0,,,",
                "1,2,3,4,5",
                "3,0,0,0, a,0,0, 0,1,0,,,",
                "3,0,0,0, nan,0,0, 0,1,0,,,",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match=r"bad\.csv: line 2:.*3 or 4 points"):
        load_planes(path)

    path.write_text(
        "3,0,0,0, 1,0,0, 0,1,0,,,\n3,0,0,0, abc,0,0, 0,1,0,,,\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match=r"bad\.csv: line 2:.*numbers"):
        load_planes(path)

    path.write_text("3,0,0,0, nan,0,0, 0,1,0,,,\n", encoding="utf-8")
    with pytest.raises(ValueError, match=r"bad\.csv: line 1:.*finite"):
        load_planes(path)


def test_tc26_plane_project_matches():
    """TC-26. FR-6. Plane.project uses PROJECT order and hits the apex voxel."""
    volume = np.zeros((8, 8, 4), dtype=np.uint8)
    volume[3, 6, 1] = 9
    plane = Plane([[3, 6, 1], [0, 1, 1], [6, 1, 1]])
    image = plane.project(volume)
    reference = plane.project_reference(volume)
    assert np.array_equal(image, reference)
    assert image.dtype == np.uint8
    center = (image.shape[1] - 1) // 2
    assert image[0, center] == 9


def test_tc23_degenerate_csv_names_the_line(tmp_path):
    """TC-23. FR-4, FR-5. Degenerate rows name the file and the line."""
    path = tmp_path / "flat.csv"
    path.write_text("3,0,0,0, 0,0,0, 0,0,0,,,\n", encoding="utf-8")
    with pytest.raises(ValueError, match=r"flat\.csv: line 1:.*coincident"):
        load_planes(path)

    path.write_text("3,0,5,0, 0,5,0, 4,0,0,,,\n", encoding="utf-8")
    with pytest.raises(ValueError, match=r"flat\.csv: line 1:.*zero leg"):
        load_planes(path)

    # a', b, a'', c with the same midpoint on the top and the base.
    path.write_text("4,0,0,0, 0,1,0, 2,1,0, 2,0,0\n", encoding="utf-8")
    with pytest.raises(ValueError, match=r"flat\.csv: line 1:.*zero height"):
        load_planes(path)


def test_tc20_csv_header_comments_blanks(tmp_path):
    """TC-20. FR-3. Header, blanks, comments, spaces, and a negative fraction."""
    path = tmp_path / "planes.csv"
    path.write_text(
        "\n".join(
            [
                "Number of Points (3 or 4),x1,y1,z1,x2,y2,z2,x3,y3,z3,x4,y4,z4",
                "",
                "# a comment, with spaces below",
                "  3 ,  -1.5 , 0 , 0 ,  0 , 0 , 4 ,  4 , 0 , 4 , , , ",
                "4, 1, 1, 1, 1, 5, 1, 4, 1, 1, 4, 5, 1",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    planes = load_planes(path)
    assert len(planes) == 2
    assert planes[0].is_triangle
    assert planes[0].line == 4
    assert planes[0].points[0, 0] == -1.5
    assert not planes[1].is_triangle
    assert planes[1].line == 5
    a_prime, a_second, b, c = planes[1].corners()
    assert np.array_equal(a_prime, [1, 1, 1])
    assert np.array_equal(b, [1, 5, 1])
    assert np.array_equal(a_second, [4, 1, 1])
    assert np.array_equal(c, [4, 5, 1])


def test_tc22_csv_count_mismatch(tmp_path):
    """TC-22. FR-3, FR-5. Count 4 with only 9 numbers, or count 3 with 12."""
    path = tmp_path / "bad.csv"
    path.write_text(
        "Number of Points (3 or 4),x1,y1,z1,x2,y2,z2,x3,y3,z3,x4,y4,z4\n"
        "4,0,0,0,1,0,0,0,1,0,,,\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match=r"bad\.csv: line 2:.*count"):
        load_planes(path)

    path.write_text("3,0,0,0,1,0,0,0,1,0,1,1,1\n", encoding="utf-8")
    with pytest.raises(ValueError, match=r"bad\.csv: line 1:.*count"):
        load_planes(path)


def test_tc24_lecturer_example_row4():
    """TC-24. FR-3, FR-4. Row 4 of lecturer_example.csv: equal legs, no warning."""
    path = Path(__file__).resolve().parents[1] / "csv" / "lecturer_example.csv"
    planes = load_planes(path)
    assert len(planes) == 4
    plane = planes[3]
    assert not plane.is_triangle
    assert plane.line == 5

    a_prime, a_second, b, c = plane.corners()
    # Legs a'→b and a''→c are equal; the top a'→a'' is parallel to the base b→c.
    assert abs(np.linalg.norm(a_prime - b) - np.linalg.norm(a_second - c)) <= 1
    assert np.linalg.norm(np.cross(a_second - a_prime, c - b)) < 1e-6

    volume = np.zeros((2, 2, 2), dtype=np.uint8)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        plane.project(volume)
    assert caught == []


def test_tc25_head_csv_has_280_planes():
    """TC-25. FR-3. head.csv is one header plus 280 planes, the last 60 triangles."""
    path = Path(__file__).resolve().parents[1] / "csv" / "head.csv"
    planes = load_planes(path)
    assert len(planes) == 280
    assert planes[0].line == 2
    assert planes[-1].line == 281
    assert sum(plane.is_triangle for plane in planes) == 60
    assert sum(not plane.is_triangle for plane in planes) == 220
