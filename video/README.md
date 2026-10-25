# Video demo

One MP4 frame per CSV plane through an NRRD volume. Projection is the shared code in [ALGORITHM.md](../ALGORITHM.md): triangles and trapezoids, and one global 1st/99th percentile window.

Install: `pip install -r requirements.txt`

Usage, from the repo root: `python Ex0.py file.nrrd file.csv file.mp4`

Example: `python Ex0.py data-NRRD/MRHead_1.nrrd video/planes_mrhead.csv video/mrhead_planes.mp4`

CSV: one plane per line, voxel indices. A triangle is 9 numbers `ax,ay,az,bx,by,bz,cx,cy,cz`. A trapezoid is 12: `a'x,a'y,a'z,a''x,a''y,a''z,bx,by,bz,cx,cy,cz`.

Output: grayscale MP4 (mp4v, 5 fps). Frames are padded with black onto one canvas with even width and height. `planes_mrhead.csv` and `mrhead_planes.mp4` are the same six cuts of `MRHead_1.nrrd`: axial, coronal, and sagittal triangles, one tilted triangle, and two isosceles trapezoids. The CSV is reconstructed, not an original experiment file.

## Demo

From the repo root, on `data-NRRD/MRHead_1.nrrd`. These files produced no leg warnings. Frame counts match the CSV rows.

```
python Ex0.py data-NRRD/MRHead_1.nrrd video/planes_mrhead.csv video/mrhead_planes.mp4
volume (256, 256, 130) int16
planes: 6, frames: 6, size: 202x182
projection time: 0.006 s, 1075.5 planes/s
```

```
python Ex0.py data-NRRD/MRHead_1.nrrd video/demo_triangles.csv demo_triangles.mp4
volume (256, 256, 130) int16
planes: 3, frames: 3, size: 202x182
projection time: 0.003 s, 905.8 planes/s
```

```
python Ex0.py data-NRRD/MRHead_1.nrrd video/demo_trapezoids.csv demo_trapezoids.mp4
volume (256, 256, 130) int16
planes: 2, frames: 2, size: 182x162
projection time: 0.002 s, 976.6 planes/s
```

```
python Ex0.py data-NRRD/MRHead_1.nrrd video/demo_outside.csv demo_outside.mp4
volume (256, 256, 130) int16
planes: 2, frames: 2, size: 152x122
projection time: 0.001 s, 1428.9 planes/s
```

`demo_outside.csv`: the first frame is only partly black; the second (fully outside the volume) is black. The three extra MP4s are not in the repo.
