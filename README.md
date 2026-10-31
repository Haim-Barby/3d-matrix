# 3D Matrix: Plane Projection

Project a 3D NRRD volume onto planes from a CSV file and write one MP4 frame per plane.

Course: Introduction to Software Engineering (OOP/OOD), Ariel University, assignment Ex1. The program is `Ex0.py`.

## Problem

The program projects a 3D NRRD volume onto a plane. The plane is an isosceles triangle or an isosceles trapezoid. Each projection is a 2D image.

## Scope

**In scope:** read a 3D NRRD volume, read planes from a CSV file (3 or 4 points per row), compute one 2D image per plane, and write those images as MP4 frames in CSV order.

**Out of scope:** a GUI, editing the volume, and formats other than NRRD.

**Assumptions:** CSV coordinates are voxel indices. One pixel is one voxel step, not one millimetre, so NRRD spacing is not applied. Each volume side is at least 1 and below 1024.

## Install

```
pip install -r requirements.txt
```

Dependencies: numpy, pynrrd, opencv-python, pytest.

### macOS

Run these from the project folder. No sudo, and no global install.

```
python3 -m venv .venv
source .venv/bin/activate

python -m pip install -r requirements.txt

python Ex0.py data-NRRD/MRHead_1.nrrd video/experiment.csv output.mp4

open output.mp4

python -m pytest
python tests/benchmark.py
```

## Usage

From the repo root:

```
python Ex0.py file.nrrd file.csv file.mp4
```

The experiment video (six MRHead planes, one second each):

```
python Ex0.py data-NRRD/MRHead_1.nrrd video/experiment.csv video/experiment.mp4
```

Each data row is one plane and one frame. The file has a header `Number of Points (3 or 4),x1,y1,z1,...,x4,y4,z4`. A row starts with `3` (triangle `a, b, c`; the unused fourth point is empty) or `4` (trapezoid `a', b, a'', c`). `#` comments and blank lines are skipped and do not make a frame. Coordinates are voxel indices. They may be fractional and may lie outside the volume.

A plane is valid when its lengths agree within 0.001 voxel. A triangle must have equal legs. A trapezoid must also be planar, with parallel bases, equal legs, and a symmetric (non-crossing) order. A rectangle is valid. Anything else raises `ValueError`. In the demo that row becomes a black error frame marked with the line number and the reason, the reason is printed on stderr, and the run continues. A missing file, a bad NRRD, a CSV with no data rows, or an output that cannot be opened stops the program with a non-zero exit.

Sampling is nearest voxel. A coordinate halfway between two voxels uses `floor(v + 0.5)`, so the tie always rounds up. The image is 1 voxel per pixel in index space. It is not scaled to millimetres. Gray values use one window for the volume: the 1st and 99th percentiles. Frames are centred on a single canvas whose sides are even. The MP4 is OpenCV `mp4v` at 1 fps.

## Layout

- `Ex0.py` — demo program
- `src/plane.py`, `src/projection.py`, `src/io_utils.py` — planes, projection, NRRD and CSV load
- `data-NRRD/` — volumes
- `csv/` — `head.csv`, `croissant.csv`, `lecturer_example.csv`
- `video/` — `experiment.csv`, `experiment.mp4`, and a short write-up
- `tests/` — pytest tests, `benchmark.py`, and the testing notes
- `ALGORITHM.md`, `SRS.md`, `requirements.txt`

## Dataset

The volumes are the lecturer's NRRD files. They match the public Drive folder [1koJ83uaeMYdJt6AwvVlmMJk_wzczvmmG](https://drive.google.com/drive/folders/1koJ83uaeMYdJt6AwvVlmMJk_wzczvmmG). `croissant_1.nrrd` is that folder's `croissant.nrrd`.

Spacing below is the length of each index axis in the NRRD `space directions`, in mm per voxel. Sampling does not apply that spacing.

| File | Shape | dtype | Spacing x, y, z (mm) | Why |
|---|---|---|---|---|
| MRHead_1.nrrd | 256×256×130 | int16 | 1, 1, 1.3 | signed int16; anisotropic spacing |
| biscuit_cake.nrrd | 256×256×130 | uint16 | 1, 1, 1.3 | uint16 voxels; anisotropic spacing |
| croissant_1.nrrd | 500×500×500 | uint8 | 0.37, 0.37, 0.37 | only 500³ volume: performance check |
| onion.nrrd | 256×256×130 | uint8 | 0.55, 0.55, 0.715 | uint8 voxels; anisotropic spacing |
| swiss_roll.nrrd | 256×256×130 | uint32 | 1.1, 1.1, 1.43 | uint32 voxels; anisotropic spacing |

MRHead's z vector length in the header is 1.29999542 mm. `csv/head.csv` (280 planes) and `csv/croissant.csv` (100 planes) are copies from the Drive folder, as is the 4-plane `csv/lecturer_example.csv`.

Automated tests do not read these files. They use synthetic volumes, including the ramp M = x + 10y + 100z and similar cases in [tests/TESTING.md](tests/TESTING.md).

## Experiment

Times below are projection only. One run on Linux 6.12.94+ x86_64. The per-plane table is in [video/README.md](video/README.md).

```
python Ex0.py data-NRRD/MRHead_1.nrrd video/experiment.csv /tmp/check_experiment.mp4
volume (256, 256, 130) int16
planes: 6, frames: 6, ok: 6, errors: 0, size: 172x162
projection time: 0.005 s, 1203.5 planes/s
```

Six valid planes: three isosceles triangles and three isosceles trapezoids (short side 40–42% of the long side). One coronal trapezoid runs past z=129, so that side of the frame is black. The MP4 is 1 fps, so each plane is on screen for one second. The stored `video/experiment.mp4` was not regenerated by this run.

Croissant on the lecturer CSV is a separate timing check. Every plane is 501×501; the MP4 canvas is 502×502 because both sides are rounded up to an even number. That MP4 is not stored in the repo.

```
python Ex0.py data-NRRD/croissant_1.nrrd csv/croissant.csv /tmp/croissant_check.mp4
volume (500, 500, 500) uint8
planes: 100, frames: 100, ok: 100, errors: 0, size: 502x502
projection time: 0.932 s, 107.3 planes/s
```

`python tests/benchmark.py` times small, medium, and large planes on N = 64, 128, 256, and 500. On this machine the 500³ large plane (481×481) was 130.2 fps (must 30, target 100). The same 9×9 plane took 0.92× as long on 500³ as on 64³; the volume is 477× larger.

## Documents

- [ALGORITHM.md](ALGORITHM.md) — projection
- [SRS.md](SRS.md) — requirements
- [tests/TESTING.md](tests/TESTING.md) — tests and how to run them
- [video/README.md](video/README.md) — experiment video
