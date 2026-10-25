# Video demo

One MP4 frame per CSV plane. Projection is the shared code in [ALGORITHM.md](../ALGORITHM.md): triangles and trapezoids, one global 1st/99th percentile window, 1 voxel per pixel in index space.

Install: `pip install -r requirements.txt`

Usage, from the repo root: `python Ex0.py file.nrrd file.csv file.mp4`

Example: `python Ex0.py data-NRRD/MRHead_1.nrrd video/experiment.csv video/experiment.mp4`

CSV: lecturer format. Header `Number of Points (3 or 4),x1,y1,z1,...,x4,y4,z4`. A triangle row starts with `3` and is `a, b, c` (trailing fields empty). A trapezoid row starts with `4` and is `a', b, a'', c`. `#` comments and blank lines are skipped.

Output: grayscale MP4 (OpenCV `mp4v`, 1 fps, so each plane stays on screen for one second). Frames are centred on one canvas; width and height are rounded up to even numbers.

## Experiment

Goal: five cuts through `data-NRRD/MRHead_1.nrrd` that are easy to tell apart. Three are orthogonal trapezoids (axial, coronal, sagittal). One is an oblique triangle. One coronal triangle leaves the volume.

```
python Ex0.py data-NRRD/MRHead_1.nrrd video/experiment.csv video/experiment.mp4
```

| Frame | Shape | Orientation | Image | Visible |
|---|---|---|---|---|
| 1 | trapezoid | axial, y=112 | 225×115 | axial slice: skull, brain, orbits |
| 2 | trapezoid | coronal, x=140 | 115×201 | coronal slice, top of the head up |
| 3 | trapezoid | sagittal, z=65 | 225×211 | sagittal profile, face to one side |
| 4 | triangle | oblique | 146×111 | oblique cut through the upper head |
| 5 | triangle | coronal, x=128 | 151×121 | brain, with black where the base leaves the volume |

The run printed no leg warnings. Projection took 0.006 s (840.6 planes/s). The file has 5 frames at 1 fps on a 226×212 canvas. Frames 1–4 are tissue; the black around the smaller ones is the shared canvas. Frame 5 is the outside case: 9022 of its 18271 pixels are nonzero, and the part of the base with z < 0 is black.
