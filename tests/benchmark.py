"""Projection speed as the volume and the image grow.

Projection only: the volume is already in memory, and nothing is encoded.
This file is not a pytest test. Run it directly:

    python tests/benchmark.py

N = 500 is the acceptance size. Must be at least 30 frames per second on
the large plane. The target is 100. Smaller N are there to show that the
time follows the image (H x W), not the volume (N³).
"""

import platform
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from projection import project

SIZES = (64, 128, 256, 500)


def _square(side, z):
    """Axis-aligned square of edge `side` voxels, at this z."""
    side = float(side)
    return ((0.0, 0.0, z), (side, 0.0, z), (0.0, side, z), (side, side, z))


def _kinds(n):
    """Small is the same square at every N. Large nearly fills the cube.

    The third item is the minimum seconds to time. The 500³ large plane
    is the acceptance measurement, so it gets a longer run.
    """
    accept = n >= 500
    return (
        ("small", 8, 0.05),
        ("medium", max(8, n // 4), 0.05),
        ("large", max(8, n - 20), 0.30 if accept else 0.05),
    )


def _time(volume, corners, min_seconds):
    project(volume, *corners)
    done = 0
    started = time.perf_counter()
    while True:
        project(volume, *corners)
        done += 1
        elapsed = time.perf_counter() - started
        if elapsed >= min_seconds:
            return elapsed, done


def main():
    print(f"machine: {platform.platform()}")
    print("projection only (volume already in memory, no encode)")
    print()
    header = f"{'N':>5} {'plane':<8} {'HxW':>11} {'pixels':>10} {'reps':>5} {'seconds':>8} {'us/px':>8} {'fps':>8}"
    print(header)
    rows = []
    for n in SIZES:
        volume = np.zeros((n, n, n), dtype=np.uint8, order="F")
        z = float(n // 2)
        for name, side, min_seconds in _kinds(n):
            corners = _square(side, z)
            shape = project(volume, *corners).shape
            pixels = shape[0] * shape[1]
            elapsed, repeats = _time(volume, corners, min_seconds)
            fps = repeats / elapsed
            us_per_px = elapsed / (repeats * pixels) * 1e6
            rows.append((n, name, shape, pixels, repeats, elapsed, us_per_px, fps))
            print(
                f"{n:5d} {name:<8} {shape[0]:>5d}x{shape[1]:<5d} {pixels:10d} "
                f"{repeats:5d} {elapsed:8.3f} {us_per_px:8.3f} {fps:8.1f}"
            )

    small = [row for row in rows if row[1] == "small"]
    large = [row for row in rows if row[1] == "large"]
    small_64, small_500 = small[0], small[-1]
    large_64, large_500 = large[0], large[-1]
    # seconds per projection, so the repeat counts cancel.
    small_time_ratio = (small_500[5] / small_500[4]) / (small_64[5] / small_64[4])
    large_time_ratio = (large_500[5] / large_500[4]) / (large_64[5] / large_64[4])
    large_pixel_ratio = large_500[3] / large_64[3]
    volume_ratio = (500 / 64) ** 3

    print()
    print(
        f"small plane (same pixels): time 500/64 = {small_time_ratio:.2f}x, "
        f"volume ratio = {volume_ratio:.0f}x"
    )
    print(
        f"large plane: time 500/64 = {large_time_ratio:.1f}x, "
        f"pixel ratio = {large_pixel_ratio:.1f}x, "
        f"volume ratio = {volume_ratio:.0f}x"
    )

    fps_500 = large_500[7]
    shape = large_500[2]
    print()
    print(f"500^3 large plane: {shape[0]}x{shape[1]}, {fps_500:.1f} fps")
    print("must: 30   target: 100")
    if fps_500 < 30:
        print("result: below the required 30 fps")
        return 1
    if fps_500 < 100:
        print("result: meets 30 fps, below the 100 fps target")
        return 0
    print("result: meets the 100 fps target")
    return 0


if __name__ == "__main__":
    sys.exit(main())
