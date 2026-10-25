# Software Requirements Specification (SRS)
## Plane Projection of a 3D Volume

**Course:** Introduction to Software Engineering (OOP/OOD), Ariel University
**Assignment:** Ex1
**Version:** 1.3

---

## 1. Introduction

### 1.1 Purpose
Specify what the program must do: project a 3D volume (MRI-style raster data) onto a set of planes and write each resulting 2D image as a frame of an MP4 video.

### 1.2 Scope
**In scope:**
- Read a 3D volume from an NRRD file.
- Read planes from a CSV file (3 or 4 points per row).
- Compute a 2D image for each plane.
- Write the images as MP4 frames, in CSV row order.

**Out of scope:**
- GUI, editing the volume, formats other than NRRD.

### 1.3 Definitions
| Term | Meaning |
|---|---|
| Volume M | 3D array of size sx × sy × sz, unsigned integer voxels of 8, 16 or 32 bits |
| Voxel | One cell of M, addressed by integer indices (x, y, z) |
| Plane | 3 points (triangle) or 4 points (trapezoid). Legs are nominally equal. A triangle is the trapezoid with a' = a'' = a |
| Projection E | Raw 2D samples for one plane, shape (H, W), same dtype as M |
| Image I | 8-bit grayscale of E, same shape, produced by the projection algorithm |
| FPS | Planes processed per second |

---

## 2. Overall Description

- **Form:** Command-line program, one run produces one MP4 file.
- **User:** Student or grader running the demo.
- **Environment:** Python 3. numpy and pynrrd load the volume (`index_order='F'`). The projection does not parse NRRD itself. OpenCV (`cv2.VideoWriter`, fourcc `mp4v`, 1 fps) writes the MP4 only.
- **Constraints:** 1 ≤ sx, sy, sz < 2^10. Each CSV row has 3 or 4 points.
- **Assumptions:** CSV coordinates are voxel indices (IJK), as in M[x][y][z]. Distances and pixels are in that index space: one pixel is one voxel step, not one millimetre. NRRD spacing is not applied.

---

## 3. Functional Requirements

### 3.1 Input
| ID | Requirement |
|---|---|
| FR-1 | The program shall accept three arguments: `file.nrrd`, `file.csv`, `file.mp4`. |
| FR-2 | The program shall load the volume from the NRRD file with pynrrd (`index_order='F'`), supporting 8, 16 and 32-bit unsigned voxels. |
| FR-3 | The program shall read the lecturer CSV: a header line, optional `#` comments and blank lines, then one plane per row. The row starts with `3` (triangle `a, b, c`; unused fields may be empty) or `4` (trapezoid `a', b, a'', c`, mapped to PROJECT `a', a'', b, c`). Coordinates may be real and may lie outside the volume. |
| FR-4 | The program shall accept a plane whose legs are not exactly equal, and shall warn if they differ by more than 1 voxel. It shall reject only a truly degenerate plane (zero base, zero height, collinear or coincident points), with an error naming the row, as ALGORITHM.md section 5 specifies. |
| FR-5 | The program shall reject malformed NRRD or CSV input with an error naming the file and line, and exit with a non-zero code. |

### 3.2 Projection
| ID | Requirement |
|---|---|
| FR-6 | For each plane, the program shall compute projection E of shape (H, W) and image I, following ALGORITHM.md (the detailed design; a deliberate refinement of the assignment's loose Dab × Dbc projection). H = round(h)+1 and W = round(Dbc)+1, with true height h = sqrt(Dab^2 − (Dbc/2)^2) when the legs are equal (no vertical distortion). For a trapezoid, and whenever the legs differ, h is the distance between the midpoints of the top and base edges and W = round(max(top, base))+1. A triangle is that trapezoid with a' = a'' = a. I = TO_IMAGE(E, lo, hi) is part of the algorithm: lo and hi are the 1st and 99th percentiles of M, computed once per volume; a constant volume (hi = lo) yields an all-zero image. |
| FR-7 | A sample point outside the volume shall have value 0. |
| FR-8 | Real-valued sample points shall be converted to voxel indices by rounding to the nearest integer, with halves rounding up (ALGORITHM.md section 4.3). |

### 3.3 Output
| ID | Requirement |
|---|---|
| FR-9 | The program shall write one MP4 file with one frame per plane, in CSV row order, at 1 fps, using OpenCV fourcc `mp4v`. |
| FR-10 | Each frame shall show image I, centred on one canvas. The canvas is the maximum frame width and height, rounded up so both sides are even. |

---

## 4. Non-Functional Requirements

| ID | Requirement |
|---|---|
| NFR-1 | **Correctness:** for each test volume with a known answer, the output image equals the expected image. |
| NFR-2 | **Stability:** the program shall not crash on any valid input within the constraints in Section 2. |
| NFR-3 | **Performance (target):** at least 100 FPS for a 500 × 500 × 500 volume. |
| NFR-4 | **Performance (must):** at least 30 FPS for a 500 × 500 × 500 volume. |
| NFR-5 | **Measurement:** NFR-3 and NFR-4 measure the projection only. NRRD loading and MP4 encoding are reported separately. |
| NFR-6 | **Design:** the code shall be split into modules (NRRD loading, plane parsing, projection, video output, entry point), each testable without real MRI data. |

---

## 5. External Interfaces

- **Command line:** `python Ex0.py file.nrrd file.csv file.mp4` (the assignment's script name).
- **NRRD input:** pynrrd, `index_order='F'`. Header fields `sizes`, `type`, `endian`, `encoding`.
- **CSV input:** header `Number of Points (3 or 4),x1,y1,z1,...,x4,y4,z4`. A triangle row is `3,ax,ay,az,bx,by,bz,cx,cy,cz,,,`. A trapezoid row is `4` then `a', b, a'', c`. `#` comments, blank lines, and spaces are allowed.
- **MP4 output:** one frame per plane, in CSV order, centred on one even canvas, 1 fps, `mp4v`.

---

## 6. Decisions

These points are closed.

| # | Item | Decision |
|---|---|---|
| 1 | Script name | `Ex0.py`, the name in the assignment command line |
| 2 | Video library | OpenCV `VideoWriter`, fourcc `mp4v`, 1 fps |
| 3 | Frame padding | Centred on one canvas; width and height rounded up to even |
| 4 | CSV format | Lecturer header, a leading count of 3 or 4, empty trailing fields on triangles, `#` comments, blank lines |
| 5 | Point order | Triangle `a, b, c`. Trapezoid `a', b, a'', c`, mapped to PROJECT(`a', a'', b, c`) |
| 6 | Normalization | 1st and 99th percentiles of the volume, once. Not the minimum and maximum |
| 7 | NRRD reader | pynrrd with `index_order='F'`. The program has no NRRD parser of its own |
| 8 | Trapezoid | In scope. A triangle is the trapezoid with `a' = a'' = a` |

---

## 7. Related Documents
- Algorithm details and edge-case handling: ALGORITHM.md.
- Tests and how to run them: tests/TESTING.md.
- Setup, dataset, and experiment results: README.md.
