# 3D Matrix: Plane Projection

## Problem
Given a 3D volume (for example, an MRI scan stored as NRRD) and a plane defined by 3 or 4 points, compute the 2D image of the volume on that plane.

## Scope
- **Input:** an NRRD file with the 3D volume, and a CSV file where each row is a plane (3 or 4 points, `x,y,z`).
- **Output:** an MP4 video with one frame per plane, in the same order as the CSV.
- **Algorithm:** the Projection algorithm from the course assignment (isosceles triangle; trapezoid optional).
- **Performance:** at least 30 FPS on a 500×500×500 volume (100 FPS is the target).

Out of scope: planes that are not isosceles, GUI, editing the volume, formats other than NRRD.

## Usage (planned)
```
python Ex0.py file.nrrd file.csv file.mp4
```

## Status
Planning stage. The SRS, algorithm details, test strategy, and implementation are still in progress.

## Documents
- `SRS.md`: software requirements (planned)

## Course
Introduction to Software Engineering (OOP/OOD), Ariel University. Assignment Ex1.
