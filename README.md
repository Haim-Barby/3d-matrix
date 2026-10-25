# 3D Matrix: Plane Projection

## Problem
Given a 3D volume (for example, an MRI scan stored as NRRD) and a plane defined by 3 or 4 points, compute the 2D image of the volume on that plane.

## Scope
- **Input:** an NRRD file with the 3D volume, and a CSV file where each row is a plane (3 or 4 points, `x,y,z`).
- **Output:** an MP4 video with one frame per plane, in the same order as the CSV. Frames are padded to a uniform canvas size.
- **Algorithm:** ALGORITHM.md. Triangle and trapezoid are both in v1 (a triangle is the trapezoid with a' = a'' = a). The 8-bit image is part of the algorithm (one global 1st/99th percentile window per volume).
- **Performance:** at least 30 FPS on a 500×500×500 volume (100 FPS is the target).

Out of scope: GUI, editing the volume, formats other than NRRD.

## Usage (planned)
```
python Ex0.py file.nrrd file.csv file.mp4
```

## Status
The algorithm is designed (ALGORITHM.md). Implementation is in progress. The video encoding library and the Ex0 vs Ex1 script name are still open.

## Documents
- `ALGORITHM.md`: detailed projection algorithm
- `SRS.md`: software requirements
- `tests/TESTING.md`: testing strategy
- `video/`: MP4 demo (`python video/Ex0.py data-NRRD/MRHead_1.nrrd video/planes_mrhead.csv video/mrhead_planes.mp4`)

## Course
Introduction to Software Engineering (OOP/OOD), Ariel University. Assignment Ex1.
