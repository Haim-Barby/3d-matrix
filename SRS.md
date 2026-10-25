# Software Requirements Specification (SRS)
## Plane Projection of a 3D Volume

**Course:** Introduction to Software Engineering (OOP/OOD), Ariel University
**Assignment:** Ex1
**Version:** 1.2

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
- **Environment:** Python 3, numpy, and pynrrd (the NRRD reader). OpenCV is not used in the algorithm. The demo video library (task #7) is still to be decided.
- **Constraints:** 1 ≤ sx, sy, sz < 2^10. Each CSV row has 3 or 4 points.
- **Assumptions:** CSV coordinates are voxel indices (IJK), as in M[x][y][z].

---

## 3. Functional Requirements

### 3.1 Input
| ID | Requirement |
|---|---|
| FR-1 | The program shall accept three arguments: `file.nrrd`, `file.csv`, `file.mp4`. |
| FR-2 | The program shall load the volume from the NRRD file with pynrrd (`index_order='F'`), supporting 8, 16 and 32-bit unsigned voxels. |
| FR-3 | The program shall read each CSV row as one plane of 3 or 4 points. |
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
| FR-9 | The program shall write one MP4 file with one frame per plane, in CSV row order. |
| FR-10 | Each frame shall show image I. In the demo (video), frames are padded to a uniform canvas size so every MP4 frame has the same size. |

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

- **Command line:** `python Ex0.py file.nrrd file.csv file.mp4`
  Note: the assignment writes `Ex0.py`, while the title says Ex1. To be confirmed with the instructor.
- **NRRD input:** standard header fields `sizes`, `type`, `endian`, `encoding`.
- **CSV input:** one plane per line, comma-separated coordinates (real values allowed), e.g. `10,20,30,50,20,30,30,60,30` for a triangle.
- **MP4 output:** one frame per plane, in CSV order, padded to a uniform canvas size.

---

## 6. Open Items

| # | Item | Status |
|---|---|---|
| 1 | Script name: `Ex0.py` in the assignment, `Ex1` in the title | Ask instructor |
| 2 | Video encoding library for the demo (task #7) | Still to be decided |

---

## 7. Related Documents
- Algorithm details and edge-case handling: ALGORITHM.md.
- Test strategy: tests/TESTING.md. The full test plan and test cases are still to be written.
- Setup and usage: README.md.
