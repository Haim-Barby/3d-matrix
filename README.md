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

## Usage

From the repo root:

```
python Ex0.py file.nrrd file.csv file.mp4
```

The experiment video (six MRHead planes, one second each):

```
python Ex0.py data-NRRD/MRHead_1.nrrd video/experiment.csv video/experiment.mp4
```

Each CSV row is one plane. The file has a header `Number of Points (3 or 4),x1,y1,z1,...,x4,y4,z4`. A row starts with `3` (triangle `a, b, c`; the unused fourth point is empty) or `4` (trapezoid `a', b, a'', c`). `#` comments and blank lines are skipped. Coordinates are voxel indices. They may be fractional and may lie outside the volume.

The image is 1 voxel per pixel in index space. It is not scaled to millimetres. Gray values use one window for the volume: the 1st and 99th percentiles. Frames are centred on a single canvas whose sides are even. The MP4 is OpenCV `mp4v` at 1 fps.

## Layout

- `Ex0.py` — demo program
- `src/projection.py`, `src/io_utils.py` — projection, NRRD load, CSV load
- `data-NRRD/` — volumes
- `csv/` — `head.csv`, `croissant.csv`, `lecturer_example.csv`
- `video/` — `experiment.csv`, `experiment.mp4`, and a short write-up
- `tests/` — pytest tests, `benchmark.py`, and the testing notes
- `ALGORITHM.md`, `SRS.md`, `requirements.txt`

## Dataset

The volumes are the lecturer's NRRD files. They match the public Drive folder [1koJ83uaeMYdJt6AwvVlmMJk_wzczvmmG](https://drive.google.com/drive/folders/1koJ83uaeMYdJt6AwvVlmMJk_wzczvmmG). `croissant_1.nrrd` is that folder's `croissant.nrrd`.

Spacing below is the length of each index axis in the NRRD `space directions`, in mm per voxel. Sampling does not apply that spacing.

| File | Shape | dtype | Spacing x, y, z (mm) |
|---|---|---|---|
| MRHead_1.nrrd | 256×256×130 | int16 | 1, 1, 1.3 |
| biscuit_cake.nrrd | 256×256×130 | uint16 | 1, 1, 1.3 |
| croissant_1.nrrd | 500×500×500 | uint8 | 0.37, 0.37, 0.37 |
| onion.nrrd | 256×256×130 | uint8 | 0.55, 0.55, 0.715 |
| swiss_roll.nrrd | 256×256×130 | uint32 | 1.1, 1.1, 1.43 |

MRHead's z vector length in the header is 1.29999542 mm. `csv/head.csv` (280 planes) and `csv/croissant.csv` (100 planes) are copies from the Drive folder, as is the 4-plane `csv/lecturer_example.csv`.

## Experiment

Times below are projection only. One run on Linux 6.12.94+ x86_64. The per-plane table is in [video/README.md](video/README.md).

```
python Ex0.py data-NRRD/MRHead_1.nrrd video/experiment.csv video/experiment.mp4
volume (256, 256, 130) int16
planes: 6, frames: 6, size: 172x162
projection time: 0.005 s, 1132.5 planes/s
```

Six planes, no leg warnings: three isosceles triangles and three isosceles trapezoids (short side 40–42% of the long side). One coronal trapezoid runs past z=129, so that side of the frame is black. The MP4 is 1 fps, so each plane is on screen for one second.

Croissant on the lecturer CSV is a separate timing check. Every plane is 501×501; the MP4 canvas is 502×502 because both sides are rounded up to an even number. That MP4 is not stored in the repo.

```
python Ex0.py data-NRRD/croissant_1.nrrd csv/croissant.csv croissant.mp4
volume (500, 500, 500) uint8
planes: 100, frames: 100, size: 502x502
projection time: 0.979 s, 102.1 planes/s
```

`python tests/benchmark.py` times small, medium, and large planes on N = 64, 128, 256, and 500. On this machine the 500³ large plane (481×481) was 129.7 fps (must 30, target 100). The same 9×9 plane took 1.01× as long on 500³ as on 64³; the volume is 477× larger.

## Documents

- [ALGORITHM.md](ALGORITHM.md) — projection
- [SRS.md](SRS.md) — requirements
- [tests/TESTING.md](tests/TESTING.md) — tests and how to run them
- [video/README.md](video/README.md) — experiment video
