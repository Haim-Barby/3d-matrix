"""NRRD axis order and CSV plane parsing."""

import warnings

import numpy as np
import nrrd
import pytest

from io_utils import Plane, load_nrrd, load_planes


def test_issue7_nrrd_round_trip_axis_order(tmp_path):
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


def test_nrrd_rejects_bad_file_and_non_volume(tmp_path):
    bad = tmp_path / "notes.nrrd"
    bad.write_text("this is not an nrrd\n", encoding="utf-8")
    with pytest.raises(ValueError, match="notes.nrrd"):
        load_nrrd(bad)

    flat = np.arange(12, dtype=np.uint8).reshape(3, 4)
    flat_path = tmp_path / "flat.nrrd"
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        nrrd.write(str(flat_path), flat, index_order="F")
    with pytest.raises(AssertionError, match="3D"):
        load_nrrd(flat_path)


def test_csv_parses_triangles_and_trapezoids_in_order(tmp_path):
    path = tmp_path / "planes.csv"
    path.write_text(
        "\n".join(
            [
                "0, 0, 0, 0, 0, 10, 10, 0, 5",
                "",
                "0.5, 1, 2, 3, 4, 5, 6, 7, 8",
                "1, 1, 1, 4, 1, 1, 1, 5, 1, 4, 5, 1",
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
    apex, again, base_left, base_right = planes[0].corners()
    assert np.array_equal(apex, again)
    assert np.array_equal(base_right, [10, 0, 5])


def test_csv_bad_rows_name_the_file_and_line(tmp_path):
    path = tmp_path / "bad.csv"
    path.write_text(
        "\n".join(
            [
                "0,0,0, 1,0,0, 0,1,0",
                "1,2,3,4,5",
                "0,0,0, a,0,0, 0,1,0",
                "0,0,0, nan,0,0, 0,1,0",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match=r"bad\.csv: line 2:.*3 or 4 points"):
        load_planes(path)

    path.write_text("0,0,0, 1,0,0, 0,1,0\n0,0,0, abc,0,0, 0,1,0\n", encoding="utf-8")
    with pytest.raises(ValueError, match=r"bad\.csv: line 2:.*numbers"):
        load_planes(path)

    path.write_text("0,0,0, nan,0,0, 0,1,0\n", encoding="utf-8")
    with pytest.raises(ValueError, match=r"bad\.csv: line 1:.*finite"):
        load_planes(path)


def test_plane_project_matches_module_function():
    volume = np.zeros((8, 8, 4), dtype=np.uint8)
    volume[3, 6, 1] = 9
    plane = Plane([[3, 6, 1], [0, 1, 1], [6, 1, 1]])
    image = plane.project(volume)
    reference = plane.project_reference(volume)
    assert np.array_equal(image, reference)
    assert image.dtype == np.uint8
    center = (image.shape[1] - 1) // 2
    assert image[0, center] == 9


def test_plane_from_csv_names_the_row_when_degenerate(tmp_path):
    path = tmp_path / "flat.csv"
    path.write_text("0,0,0, 0,0,0, 0,0,0\n", encoding="utf-8")
    plane = load_planes(path)[0]
    volume = np.zeros((2, 2, 2), dtype=np.uint8)
    with pytest.raises(ValueError, match=r"line 1:.*coincident"):
        plane.project(volume)
