"""Project an NRRD volume onto CSV planes and write an MP4.

Usage: python Ex0.py file.nrrd file.csv file.mp4

Each data row is one frame, in order. A valid row is a projection. A row
that cannot be parsed or is not an isosceles triangle or trapezoid becomes
an error frame, and the run continues. The header, comments, and blank
lines are not frames.
"""

import sys
import time
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from io_utils import load_nrrd, read_plane_rows
from projection import project, to_image, window

USAGE = "usage: python Ex0.py file.nrrd file.csv file.mp4"
# Large enough to read the line number and the reason.
ERROR_WIDTH = 480
ERROR_HEIGHT = 160


def main():
    if len(sys.argv) != 4:
        sys.exit(USAGE)
    nrrd_path, csv_path, mp4_path = sys.argv[1:]

    try:
        volume = load_nrrd(nrrd_path)
        rows = read_plane_rows(csv_path)
    except (OSError, ValueError) as exc:
        sys.exit(str(exc))
    if not rows:
        sys.exit(f"{csv_path}: no planes")

    lo, hi = window(volume)
    started = time.perf_counter()
    frames = []
    errors = 0
    for line_no, plane, error in rows:
        if error is not None:
            errors += 1
            print(f"{csv_path}: line {line_no}: {error}", file=sys.stderr)
            frames.append(("error", line_no, error))
            continue
        try:
            raw = project(volume, *plane.corners())
        except ValueError as exc:
            errors += 1
            print(f"{csv_path}: line {line_no}: {exc}", file=sys.stderr)
            frames.append(("error", line_no, str(exc)))
            continue
        frames.append(("image", to_image(raw, lo, hi)))
    elapsed = time.perf_counter() - started

    width, height = _canvas_size(frames)
    writer = None
    try:
        writer = cv2.VideoWriter(
            mp4_path, cv2.VideoWriter_fourcc(*"mp4v"), 1, (width, height)
        )
        if not writer.isOpened():
            sys.exit(f"cannot open {mp4_path} for writing")
        for frame in frames:
            if frame[0] == "error":
                canvas = _error_frame(frame[1], frame[2], width, height)
            else:
                canvas = _place(frame[1], width, height)
            writer.write(canvas)
    finally:
        if writer is not None:
            writer.release()

    ok = len(frames) - errors
    print(f"volume {volume.shape} {volume.dtype}")
    print(
        f"planes: {len(frames)}, frames: {len(frames)}, "
        f"ok: {ok}, errors: {errors}, size: {width}x{height}"
    )
    if ok and elapsed > 0:
        print(f"projection time: {elapsed:.3f} s, {ok / elapsed:.1f} planes/s")
    else:
        print("projection time: 0.000 s, 0 planes/s")


def _canvas_size(frames):
    images = [frame[1] for frame in frames if frame[0] == "image"]
    errors = len(frames) - len(images)
    if images:
        height = max(image.shape[0] for image in images)
        width = max(image.shape[1] for image in images)
    else:
        height = 0
        width = 0
    if errors:
        height = max(height, ERROR_HEIGHT)
        width = max(width, ERROR_WIDTH)
    height += height % 2
    width += width % 2
    return width, height


def _place(image, width, height):
    canvas = np.zeros((height, width, 3), dtype=np.uint8)
    y0 = (height - image.shape[0]) // 2
    x0 = (width - image.shape[1]) // 2
    gray = canvas[:, :, 0]
    gray[y0 : y0 + image.shape[0], x0 : x0 + image.shape[1]] = image
    canvas[:, :, 1] = gray
    canvas[:, :, 2] = gray
    return canvas


def _error_frame(line_no, reason, width, height):
    canvas = np.zeros((height, width, 3), dtype=np.uint8)
    white = (255, 255, 255)
    cv2.line(canvas, (6, 6), (width - 7, height - 7), white, 2)
    cv2.line(canvas, (width - 7, 6), (6, height - 7), white, 2)
    text = f"line {line_no}: {reason}"
    y = 28
    for line in _wrap(text, width - 24):
        cv2.putText(
            canvas, line, (12, y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, white, 1, cv2.LINE_AA
        )
        y += 22
        if y >= height - 8:
            break
    return canvas


def _wrap(text, limit):
    lines = []
    current = ""
    for word in text.split():
        trial = word if current == "" else current + " " + word
        width = cv2.getTextSize(trial, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)[0][0]
        if width <= limit:
            current = trial
            continue
        if current:
            lines.append(current)
        current = word
    if current:
        lines.append(current)
    return lines


if __name__ == "__main__":
    main()
