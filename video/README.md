# Video demo

One MP4 frame per CSV plane through an NRRD volume. Projection is the shared code in [ALGORITHM.md](../ALGORITHM.md): triangles and trapezoids, and one global 1st/99th percentile window.

Install: `pip install -r requirements.txt`

Usage: `python video/Ex0.py file.nrrd file.csv file.mp4`

Example: `python video/Ex0.py data-NRRD/MRHead_1.nrrd video/planes_mrhead.csv video/mrhead_planes.mp4`

CSV: one plane per line, voxel indices. A triangle is 9 numbers `ax,ay,az,bx,by,bz,cx,cy,cz`. A trapezoid is 12: `a'x,a'y,a'z,a''x,a''y,a''z,bx,by,bz,cx,cy,cz`.

Output: grayscale MP4 (mp4v, 5 fps). Frames are padded with black onto one canvas with even width and height. `planes_mrhead.csv` and `mrhead_planes.mp4` are the same six cuts of `MRHead_1.nrrd`: axial, coronal, and sagittal triangles, one tilted triangle, and two isosceles trapezoids. The CSV is reconstructed, not an original experiment file.
