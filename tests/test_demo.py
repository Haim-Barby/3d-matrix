"""End-to-end run of Ex0.py and a few user-error exits."""

import subprocess
import sys
import warnings
from pathlib import Path

import cv2
import nrrd
import numpy as np

from projection import project, to_image, window

ROOT = Path(__file__).resolve().parents[1]
EX0 = ROOT / "Ex0.py"


def _run(args):
    return subprocess.run(
        [sys.executable, str(EX0), *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )


def _write_volume(path):
    volume = np.arange(8 * 8 * 8, dtype=np.uint16).reshape(8, 8, 8)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        nrrd.write(str(path), volume, index_order="F")


def _frame_count(path):
    capture = cv2.VideoCapture(str(path))
    reported = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
    read = 0
    while True:
        ok, _frame = capture.read()
        if not ok:
            break
        read += 1
    capture.release()
    return reported, read


def test_tc27_ex0_one_frame_per_row(tmp_path):
    """TC-27. FR-1, FR-9, FR-10. One frame per row, 1 fps, mp4v, even canvas."""
    nrrd_path = tmp_path / "tiny.nrrd"
    csv_path = tmp_path / "planes.csv"
    mp4_path = tmp_path / "out.mp4"
    _write_volume(nrrd_path)
    csv_path.write_text(
        "3,3.5,1,1, 1,6,1, 6,6,1,,,\n"
        "4,0,0,2, 0,5,2, 4,0,2, 4,5,2\n",
        encoding="utf-8",
    )

    result = _run([str(nrrd_path), str(csv_path), str(mp4_path)])
    assert result.returncode == 0, result.stderr
    assert "Traceback" not in result.stderr
    assert mp4_path.is_file()
    reported, read = _frame_count(mp4_path)
    assert reported == 2
    assert read == 2
    assert "frames: 2" in result.stdout
    capture = cv2.VideoCapture(str(mp4_path))
    assert capture.get(cv2.CAP_PROP_FPS) == 1
    width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
    assert width % 2 == 0 and height % 2 == 0
    # OpenCV reads the mp4v writer back as FMP4.
    fourcc = int(capture.get(cv2.CAP_PROP_FOURCC))
    code = "".join(chr((fourcc >> (8 * i)) & 0xFF) for i in range(4))
    assert code == "FMP4"
    capture.release()


def _read_frames(path):
    capture = cv2.VideoCapture(str(path))
    frames = []
    while True:
        ok, frame = capture.read()
        if not ok:
            break
        frames.append(frame)
    size = (
        int(capture.get(cv2.CAP_PROP_FRAME_WIDTH)),
        int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT)),
    )
    capture.release()
    return frames, size


def test_tc28_bad_row_is_an_error_frame(tmp_path):
    """TC-28. FR-5. A bad row is an error frame. The valid row is still written."""
    nrrd_path = tmp_path / "tiny.nrrd"
    csv_path = tmp_path / "bad.csv"
    mp4_path = tmp_path / "out.mp4"
    _write_volume(nrrd_path)
    csv_path.write_text(
        "3,3.5,1,1, 1,6,1, 6,6,1,,,\n"
        "1,2,3,4,5\n",
        encoding="utf-8",
    )

    result = _run([str(nrrd_path), str(csv_path), str(mp4_path)])
    assert result.returncode == 0, result.stderr
    assert "Traceback" not in result.stderr
    assert f"{csv_path}: line 2:" in result.stderr
    assert "errors: 1" in result.stdout
    frames, (width, height) = _read_frames(mp4_path)
    assert len(frames) == 2
    assert width % 2 == 0 and height % 2 == 0
    assert width >= 480 and height >= 160
    assert _is_error_mark(frames[1])
    assert not _is_error_mark(frames[0])


def test_tc29_missing_file_and_usage(tmp_path):
    """TC-29. FR-1, FR-5. A missing NRRD and a short command line exit with a message."""
    missing = tmp_path / "missing.nrrd"
    csv_path = tmp_path / "planes.csv"
    csv_path.write_text("3,3.5,1,1, 1,6,1, 6,6,1,,,\n", encoding="utf-8")
    mp4_path = tmp_path / "out.mp4"

    result = _run([str(missing), str(csv_path), str(mp4_path)])
    assert result.returncode != 0
    assert "Traceback" not in result.stderr
    assert str(missing) in result.stderr

    usage = _run(["only-one-arg"])
    assert usage.returncode != 0
    assert "usage: python Ex0.py" in usage.stderr
    assert "Traceback" not in usage.stderr


def test_tc30_smaller_frame_is_centred(tmp_path):
    """TC-30. FR-10. A 1×1 frame is placed in the middle of the 8×8 canvas.

    The large plane forces an 8×8 frame. The second plane is one pixel at
    voxel (7, 7, 1). Offset is (8-1)//2 = 3. mp4v changes the gray level,
    but the only bright pixel is still at [3, 3], not in the corner.
    """
    volume = np.zeros((8, 8, 2), dtype=np.uint16)
    volume[:, :, 0] = 20
    volume[7, 7, 1] = 400
    nrrd_path = tmp_path / "tiny.nrrd"
    csv_path = tmp_path / "planes.csv"
    mp4_path = tmp_path / "out.mp4"
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        nrrd.write(str(nrrd_path), volume, index_order="F")
    csv_path.write_text(
        "Number of Points (3 or 4),x1,y1,z1,x2,y2,z2,x3,y3,z3,x4,y4,z4\n"
        "4,0,0,0, 0,7,0, 7,0,0, 7,7,0\n"
        "3,7.2,7.2,1, 7.0,7.0,1, 7.4,7.0,1,,,\n",
        encoding="utf-8",
    )

    result = _run([str(nrrd_path), str(csv_path), str(mp4_path)])
    assert result.returncode == 0, result.stderr

    small = to_image(
        project(volume, (7.2, 7.2, 1), (7.2, 7.2, 1), (7.0, 7.0, 1), (7.4, 7.0, 1)),
        *window(volume),
    )
    assert small.shape == (1, 1)
    assert int(small[0, 0]) == 255

    capture = cv2.VideoCapture(str(mp4_path))
    frames = []
    while True:
        ok, frame = capture.read()
        if not ok:
            break
        frames.append(frame)
    capture.release()
    assert len(frames) == 2
    gray = frames[1][:, :, 0]
    assert gray.shape == (8, 8)
    # mp4v is lossy, so the stored pixel is not exactly 255. It is still
    # the one bright pixel, and it sits at the centre rather than at (0, 0).
    assert tuple(int(v) for v in np.unravel_index(int(np.argmax(gray)), gray.shape)) == (3, 3)
    assert int(gray[3, 3]) > 200
    assert np.argwhere(gray > 20).tolist() == [[3, 3]]
    assert int(gray[0, 0]) < 20


def _is_error_mark(frame):
    """The error frame is black, with a white X through the corners.

    Projection frames from these tests are smaller than the 480×160 error
    canvas, so a short frame is not an error mark.
    """
    gray = frame[:, :, 0]
    if gray.shape[0] < 160 or gray.shape[1] < 480:
        return False
    if int(gray[6, 6]) < 200 or int(gray[-7, -7]) < 200:
        return False
    return float(gray.mean()) < 80


def test_tc38_valid_bad_valid_keeps_order(tmp_path):
    """TC-38. FR-5, FR-9. Three rows: projection, error, projection."""
    volume = np.zeros((8, 8, 4), dtype=np.uint16)
    # A whole slice keeps the 99th percentile above the 1st, so 200 is white.
    volume[:, :, 2] = 200
    nrrd_path = tmp_path / "tiny.nrrd"
    csv_path = tmp_path / "planes.csv"
    mp4_path = tmp_path / "out.mp4"
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        nrrd.write(str(nrrd_path), volume, index_order="F")
    csv_path.write_text(
        "\n".join(
            [
                "3,3.5,1,1, 1,6,1, 6,6,1,,,",
                "3,0,0,0, abc,0,0, 1,1,0,,,",
                "3,2,2,2, 0,0,2, 4,0,2,,,",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    result = _run([str(nrrd_path), str(csv_path), str(mp4_path)])
    assert result.returncode == 0, result.stderr
    assert f"{csv_path}: line 2:" in result.stderr
    assert "numbers" in result.stderr
    assert "ok: 2, errors: 1" in result.stdout
    frames, _size = _read_frames(mp4_path)
    assert len(frames) == 3
    assert not _is_error_mark(frames[0])
    assert _is_error_mark(frames[1])
    assert not _is_error_mark(frames[2])

    expected = to_image(
        project(volume, (2, 2, 2), (2, 2, 2), (0, 0, 2), (4, 0, 2)),
        *window(volume),
    )
    assert expected[0, expected.shape[1] // 2] == 255
    placed = frames[2][:, :, 0]
    y0 = (placed.shape[0] - expected.shape[0]) // 2
    x0 = (placed.shape[1] - expected.shape[1]) // 2
    apex = placed[y0, x0 + expected.shape[1] // 2]
    assert int(apex) > 200


def test_tc39_consecutive_bad_rows(tmp_path):
    """TC-39. FR-5. Several bad rows in a row each become an error frame."""
    nrrd_path = tmp_path / "tiny.nrrd"
    csv_path = tmp_path / "bad.csv"
    mp4_path = tmp_path / "out.mp4"
    _write_volume(nrrd_path)
    csv_path.write_text(
        "\n".join(
            [
                "1,2,3",
                "3,0,0,0, abc,0,0, 1,0,0,,,",
                "3,0,0,0, nan,0,0, 1,1,0,,,",
                "3,0,2,0, 0,0,0, inf,0,0,,,",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    result = _run([str(nrrd_path), str(csv_path), str(mp4_path)])
    assert result.returncode == 0, result.stderr
    assert "Traceback" not in result.stderr
    for line_no in (1, 2, 3, 4):
        assert f"{csv_path}: line {line_no}:" in result.stderr
    assert "numbers" in result.stderr
    assert "finite" in result.stderr
    assert "ok: 0, errors: 4" in result.stdout
    frames, (width, height) = _read_frames(mp4_path)
    assert len(frames) == 4
    assert (width, height) == (480, 160)
    assert all(_is_error_mark(frame) for frame in frames)


def test_tc40_all_bad_rows_still_write_a_video(tmp_path):
    """TC-40. FR-5. A file of only bad rows is a video of error frames."""
    nrrd_path = tmp_path / "tiny.nrrd"
    csv_path = tmp_path / "bad.csv"
    mp4_path = tmp_path / "out.mp4"
    _write_volume(nrrd_path)
    csv_path.write_text(
        "4,0,0,0, 1,0,0, 0,1,0, 1,1,1\n"
        "3,0,0,0, 1,0,0, 3,0,0,,,\n",
        encoding="utf-8",
    )
    result = _run([str(nrrd_path), str(csv_path), str(mp4_path)])
    assert result.returncode == 0, result.stderr
    assert "errors: 2" in result.stdout
    frames, (width, height) = _read_frames(mp4_path)
    assert len(frames) == 2
    assert width % 2 == 0 and height % 2 == 0
    assert all(_is_error_mark(frame) for frame in frames)


def test_tc41_header_comments_and_blanks_add_no_frames(tmp_path):
    """TC-41. FR-3, FR-9. Only data rows become frames."""
    nrrd_path = tmp_path / "tiny.nrrd"
    csv_path = tmp_path / "planes.csv"
    mp4_path = tmp_path / "out.mp4"
    _write_volume(nrrd_path)
    csv_path.write_text(
        "\n".join(
            [
                "Number of Points (3 or 4),x1,y1,z1,x2,y2,z2,x3,y3,z3,x4,y4,z4",
                "",
                "# comment",
                "3,3.5,1,1, 1,6,1, 6,6,1,,,",
                "   ",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    result = _run([str(nrrd_path), str(csv_path), str(mp4_path)])
    assert result.returncode == 0, result.stderr
    assert result.stderr == ""
    assert "frames: 1" in result.stdout
    assert "errors: 0" in result.stdout
    frames, _size = _read_frames(mp4_path)
    assert len(frames) == 1
    assert not _is_error_mark(frames[0])


def test_tc42_global_failures_exit_nonzero(tmp_path):
    """TC-42. FR-5. No data rows, a bad NRRD, or an unwritable path stops the run."""
    nrrd_path = tmp_path / "tiny.nrrd"
    _write_volume(nrrd_path)
    empty = tmp_path / "empty.csv"
    empty.write_text(
        "Number of Points (3 or 4),x1,y1,z1,x2,y2,z2,x3,y3,z3,x4,y4,z4\n# none\n\n",
        encoding="utf-8",
    )
    result = _run([str(nrrd_path), str(empty), str(tmp_path / "out.mp4")])
    assert result.returncode != 0
    assert "no planes" in result.stderr
    assert "Traceback" not in result.stderr
    assert not (tmp_path / "out.mp4").exists()

    notes = tmp_path / "notes.nrrd"
    notes.write_text("not an nrrd\n", encoding="utf-8")
    csv_path = tmp_path / "one.csv"
    csv_path.write_text("3,3.5,1,1, 1,6,1, 6,6,1,,,\n", encoding="utf-8")
    bad_nrrd = _run([str(notes), str(csv_path), str(tmp_path / "out.mp4")])
    assert bad_nrrd.returncode != 0
    assert str(notes) in bad_nrrd.stderr
    assert "Traceback" not in bad_nrrd.stderr

    blocked = tmp_path / "missing-dir" / "out.mp4"
    cannot = _run([str(nrrd_path), str(csv_path), str(blocked)])
    assert cannot.returncode != 0
    assert "cannot open" in cannot.stderr
    assert "Traceback" not in cannot.stderr
