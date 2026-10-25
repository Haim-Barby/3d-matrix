"""FPS of the vectorised projection on a 500^3 volume.

Projection only: the volume is already in memory, and nothing is encoded.
This file is not a pytest test. Run it directly:

    python tests/benchmark.py

Must be at least 30 frames per second. The target is 100.
"""

import platform
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from projection import project


def _planes():
    """Triangles and one rectangle that cut through a 500^3 volume."""
    planes = []
    for z0 in (50, 150, 250, 350, 450):
        planes.append(((250, 250, z0), (250, 250, z0), (20, 40, z0), (480, 40, z0)))
    for x0 in (100, 250, 400):
        planes.append(((x0, 250, 250), (x0, 250, 250), (x0, 30, 30), (x0, 30, 470)))
    planes.append(((250, 400, 250), (250, 400, 250), (40, 40, 40), (460, 40, 460)))
    planes.append(((10, 10, 250), (490, 10, 250), (10, 490, 250), (490, 490, 250)))
    return planes


def main():
    # Fortran order matches a volume loaded from NRRD with index_order='F'.
    volume = np.zeros((500, 500, 500), dtype=np.uint8, order="F")
    planes = _planes()
    shapes = [project(volume, *corners).shape for corners in planes]

    repeats = 10
    count = 0
    start = time.perf_counter()
    for _ in range(repeats):
        for corners in planes:
            project(volume, *corners)
            count += 1
    elapsed = time.perf_counter() - start
    fps = count / elapsed
    largest = max(shapes, key=lambda shape: shape[0] * shape[1])

    print(f"machine: {platform.platform()}")
    print(f"volume: {volume.shape[0]}x{volume.shape[1]}x{volume.shape[2]} {volume.dtype}")
    print(f"planes: {len(planes)}")
    print(f"largest image: {largest[0]}x{largest[1]}")
    print(f"projections: {count}")
    print(f"seconds: {elapsed:.3f}")
    print(f"fps: {fps:.1f}")
    print("must: 30   target: 100")
    if fps < 30:
        print("result: below the required 30 fps")
        return 1
    if fps < 100:
        print("result: meets 30 fps, below the 100 fps target")
        return 0
    print("result: meets the 100 fps target")
    return 0


if __name__ == "__main__":
    sys.exit(main())
