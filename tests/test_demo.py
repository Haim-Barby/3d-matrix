"""End-to-end run of Ex0.py and a few user-error exits."""

import subprocess
import sys
import warnings
from pathlib import Path

import cv2
import nrrd
import numpy as np

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


def test_ex0_writes_one_frame_per_csv_row(tmp_path):
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
    assert capture.get(cv2.CAP_PROP_FPS) == 25
    capture.release()


def test_bad_column_count_names_the_line(tmp_path):
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


def test_missing_nrrd_and_wrong_usage(tmp_path):
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
