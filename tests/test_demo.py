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
        "3,1,1,1, 1,6,1, 6,6,1,,,\n"
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


def test_tc28_bad_row_exits(tmp_path):
    """TC-28. FR-5. A bad row exits non-zero, names the line, and writes no MP4."""
    nrrd_path = tmp_path / "tiny.nrrd"
    csv_path = tmp_path / "bad.csv"
    mp4_path = tmp_path / "out.mp4"
    _write_volume(nrrd_path)
    csv_path.write_text(
        "3,1,1,1, 1,6,1, 6,6,1,,,\n"
        "1,2,3,4,5\n",
        encoding="utf-8",
    )

    result = _run([str(nrrd_path), str(csv_path), str(mp4_path)])
    assert result.returncode != 0
    assert "Traceback" not in result.stderr
    assert f"{csv_path}: line 2:" in result.stderr
    assert not mp4_path.exists()


def test_tc29_missing_file_and_usage(tmp_path):
    """TC-29. FR-1, FR-5. A missing NRRD and a short command line exit with a message."""
    missing = tmp_path / "missing.nrrd"
    csv_path = tmp_path / "planes.csv"
    csv_path.write_text("3,1,1,1, 1,6,1, 6,6,1,,,\n", encoding="utf-8")
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
