# Video demo

One MP4 frame per CSV plane. Projection is the shared code in [ALGORITHM.md](../ALGORITHM.md): triangles and trapezoids, one global 1st/99th percentile window, 1 voxel per pixel in index space.

Install: `pip install -r requirements.txt`

Usage, from the repo root: `python Ex0.py file.nrrd file.csv file.mp4`

Example: `python Ex0.py data-NRRD/MRHead_1.nrrd csv/head.csv video/mrhead_planes.mp4`

CSV: lecturer format. Header `Number of Points (3 or 4),x1,y1,z1,...,x4,y4,z4`. A triangle row starts with `3` and is `a, b, c` (trailing fields empty). A trapezoid row starts with `4` and is `a', b, a'', c`. `#` comments and blank lines are skipped.

Output: grayscale MP4 (OpenCV `mp4v`, 25 fps). Frames are centred on one canvas; width and height are rounded up to even numbers. `video/mrhead_planes.mp4` is `csv/head.csv` through `MRHead_1.nrrd` (280 frames). The smaller demo CSVs in this folder use the same format.

## Demo

From the repo root, on `data-NRRD/MRHead_1.nrrd`. These runs printed no leg warnings. Frame counts match the CSV rows.

```
python Ex0.py data-NRRD/MRHead_1.nrrd csv/head.csv video/mrhead_planes.mp4
volume (256, 256, 130) int16
planes: 280, frames: 280, size: 256x256
projection time: 0.529 s, 529.5 planes/s
```

```
python Ex0.py data-NRRD/MRHead_1.nrrd video/demo_triangles.csv demo_triangles.mp4
volume (256, 256, 130) int16
planes: 3, frames: 3, size: 202x182
projection time: 0.003 s, 951.7 planes/s
```

```
python Ex0.py data-NRRD/MRHead_1.nrrd video/demo_trapezoids.csv demo_trapezoids.mp4
volume (256, 256, 130) int16
planes: 2, frames: 2, size: 182x162
projection time: 0.002 s, 991.0 planes/s
```

```
python Ex0.py data-NRRD/MRHead_1.nrrd video/demo_outside.csv demo_outside.mp4
volume (256, 256, 130) int16
planes: 2, frames: 2, size: 152x122
projection time: 0.001 s, 1384.0 planes/s
```

`demo_outside.csv`: the first frame is only partly black (9022 nonzero pixels); the second, fully outside the volume, is black. Those three extra MP4s are not in the repo. The croissant 500³ run (100 frames, 502×502, 102.1 planes/s) is in the root README.
