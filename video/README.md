# Video demo

One MP4 frame per CSV plane. Projection is the shared code in [ALGORITHM.md](../ALGORITHM.md): triangles and trapezoids, one global 1st/99th percentile window, 1 voxel per pixel in index space.

Install: `pip install -r requirements.txt`

Usage, from the repo root: `python Ex0.py file.nrrd file.csv file.mp4`

Example: `python Ex0.py data-NRRD/MRHead_1.nrrd video/experiment.csv video/experiment.mp4`

CSV: lecturer format. Header `Number of Points (3 or 4),x1,y1,z1,...,x4,y4,z4`. A triangle row starts with `3` and is `a, b, c` (trailing fields empty). A trapezoid row starts with `4` and is `a', b, a'', c`. `#` comments and blank lines are skipped.

Output: grayscale MP4 (OpenCV `mp4v`, 1 fps, so each plane stays on screen for one second). Frames are centred on one canvas; width and height are rounded up to even numbers.

## Experiment

Goal: six large isosceles cuts through `data-NRRD/MRHead_1.nrrd`. Three triangles and three trapezoids, with the short side 40–42% of the long side. One coronal trapezoid runs past the volume.

```
python Ex0.py data-NRRD/MRHead_1.nrrd video/experiment.csv video/experiment.mp4
```

| Frame | Shape | Orientation | Image | Visible |
|---|---|---|---|---|
| 1 | triangle | axial, y=120 | 161×85 | axial brain; apex on top, base along the bottom |
| 2 | trapezoid | coronal, x=145 | 115×156 | coronal face, top of the head up; short side is 42% of the base |
| 3 | triangle | sagittal, z=65 | 171×141 | sagittal profile; apex on top |
| 4 | trapezoid | axial, y=118 | 151×76 | axial brain; short side is 40% of the base |
| 5 | triangle | oblique | 170×162 | oblique cut of the head; apex on top |
| 6 | trapezoid | coronal, x=140 | 161×161 | coronal face; the long base runs past z=129 |

The run printed no leg warnings. Projection took 0.005 s (1132.5 planes/s), writing 6 frames at 1 fps on a 172×162 canvas. Nonzero row widths narrow toward the top: 1→161, 49→115, 1→171, 61→151, 1→170, and 65→115. Frame 6 is 161×161 with 14618 nonzero pixels; its base stays at width 115 because z runs past 129.
