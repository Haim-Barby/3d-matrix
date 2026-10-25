# 3D Matrix: Plane Projection

Project a 3D NRRD volume onto planes from a CSV file and write one MP4 frame per plane.

Course: Introduction to Software Engineering (OOP/OOD), Ariel University, assignment Ex1. The program is `Ex0.py`.

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

The experiment video (280 frames of MRHead):

```
python Ex0.py data-NRRD/MRHead_1.nrrd csv/head.csv video/mrhead_planes.mp4
```

Each CSV row is one plane. The file has a header `Number of Points (3 or 4),x1,y1,z1,...,x4,y4,z4`. A row starts with `3` (triangle `a, b, c`; the unused fourth point is empty) or `4` (trapezoid `a', b, a'', c`). `#` comments and blank lines are skipped. Coordinates are voxel indices. They may be fractional and may lie outside the volume.

The image is 1 voxel per pixel in index space. It is not scaled to millimetres. Gray values use one window for the volume: the 1st and 99th percentiles. Frames are centred on a single canvas whose sides are even. The MP4 is OpenCV `mp4v` at 1 fps.

## Layout

- `Ex0.py` — demo program
- `src/projection.py`, `src/io_utils.py` — projection, NRRD load, CSV load
- `data-NRRD/` — volumes
- `csv/` — `head.csv`, `croissant.csv`, `lecturer_example.csv`
- `video/` — `mrhead_planes.mp4` and the small demo CSVs
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

Times below are projection only. One run on Linux 6.12.94+ x86_64.

`video/mrhead_planes.mp4` is this command (280 frames, 256×256, 1 fps, 3,230,424 bytes):

```
python Ex0.py data-NRRD/MRHead_1.nrrd csv/head.csv video/mrhead_planes.mp4
volume (256, 256, 130) int16
planes: 280, frames: 280, size: 256x256
projection time: 0.529 s, 529.5 planes/s
```

Rows 1–220 are 256×256 rectangles (a sweep in z, then a 180° rotation). Rows 221–280 are triangles of 181×157, centred on that canvas. The run printed no leg warning.

Croissant on the lecturer CSV. Every plane is 501×501; the MP4 canvas is 502×502 because both sides are rounded up to an even number. That MP4 is not stored in the repo.

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
- [video/README.md](video/README.md) — demo commands
