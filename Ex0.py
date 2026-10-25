"""Project an NRRD volume onto CSV planes and write an MP4.

Usage: python Ex0.py file.nrrd file.csv file.mp4

Each row is one plane, in order: 9 numbers for a triangle (a, b, c) or 12 for
a trapezoid (a', a'', b, c). The projection and the grayscale window come from
src/ (ALGORITHM.md).
"""

import sys
import time
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from io_utils import load_nrrd, load_planes
from projection import project, to_image, window

USAGE = "usage: python Ex0.py file.nrrd file.csv file.mp4"


def main():
    if len(sys.argv) != 4:
        sys.exit(USAGE)
    nrrd_path, csv_path, mp4_path = sys.argv[1:]

    try:
        volume = load_nrrd(nrrd_path)
        planes = load_planes(csv_path)
    except (OSError, ValueError) as exc:
        sys.exit(str(exc))
    if not planes:
        sys.exit(f"{csv_path}: no planes")

    started = time.perf_counter()
    raw = []
    try:
        for plane in planes:
            raw.append(project(volume, *plane.corners()))
    except ValueError as exc:
        line = plane.line if plane.line is not None else "?"
        sys.exit(f"{csv_path}: line {line}: {exc}")
    elapsed = time.perf_counter() - started

    # One window for the whole volume (1st and 99th percentiles).
    lo, hi = window(volume)
    frames = [to_image(image, lo, hi) for image in raw]

    # One canvas for every frame. Round up so both sides are even.
    height = max(frame.shape[0] for frame in frames)
    width = max(frame.shape[1] for frame in frames)
    height += height % 2
    width += width % 2

    writer = cv2.VideoWriter(
        mp4_path, cv2.VideoWriter_fourcc(*"mp4v"), 5, (width, height)
    )
    if not writer.isOpened():
        sys.exit(f"cannot open {mp4_path} for writing")
    for frame in frames:
        canvas = np.zeros((height, width), dtype=np.uint8)
        canvas[: frame.shape[0], : frame.shape[1]] = frame
        writer.write(cv2.cvtColor(canvas, cv2.COLOR_GRAY2BGR))
    writer.release()

    print(f"volume {volume.shape} {volume.dtype}")
    print(f"planes: {len(planes)}, frames: {len(frames)}, size: {width}x{height}")
    print(f"projection time: {elapsed:.3f} s, {len(frames) / elapsed:.1f} planes/s")


if __name__ == "__main__":
    main()
