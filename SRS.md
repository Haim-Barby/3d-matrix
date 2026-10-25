# Software Requirements Specification (SRS)
## Plane Projection of a 3D Volume

**Course:** Introduction to Software Engineering (OOP/OOD), Ariel University
**Assignment:** Ex1
**Version:** 1.1

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
- Planes that are not isosceles triangles or isosceles trapezoids.
- GUI, editing the volume, formats other than NRRD.

### 1.3 Definitions
| Term | Meaning |
|---|---|
| Volume M | 3D array of size sx × sy × sz, unsigned integer voxels of 8, 16 or 32 bits |
| Voxel | One cell of M, addressed by integer indices (x, y, z) |
| Plane | A plane given by 3 points (isosceles triangle) or 4 points (isosceles trapezoid) |
| Image E | 2D output for one plane, size Dab × Dbc |
| FPS | Planes processed per second |

---

## 2. Overall Description

- **Form:** Command-line program, one run produces one MP4 file.
- **User:** Student or grader running the demo.
- **Environment:** Python 3, with numpy. Other libraries require approval.
- **Constraints:** 1 ≤ sx, sy, sz < 2^10. Each CSV row has 3 or 4 points.
- **Assumptions:** CSV coordinates are voxel indices (IJK), as in M[x][y][z].

---

## 3. Functional Requirements

### 3.1 Input
| ID | Requirement |
|---|---|
| FR-1 | The program shall accept three arguments: `file.nrrd`, `file.csv`, `file.mp4`. |
| FR-2 | The program shall load the volume from the NRRD file, supporting 8, 16 and 32-bit unsigned voxels. |
| FR-3 | The program shall read each CSV row as one plane of 3 or 4 points. |
| FR-4 | The program shall reject a plane that is not an isosceles triangle or trapezoid, or that has Dab = 0, with an error naming the row. |
| FR-5 | The program shall reject malformed NRRD or CSV input with an error naming the file and line, and exit with a non-zero code. |

### 3.2 Projection
| ID | Requirement |
|---|---|
| FR-6 | For each plane, the program shall compute image E of size Dab × Dbc using the Projection algorithm of the assignment. |
| FR-7 | A sample point outside the volume shall have value 0. |
| FR-8 | Real-valued sample points shall be converted to voxel indices by rounding to the nearest integer. |

### 3.3 Output
| ID | Requirement |
|---|---|
| FR-9 | The program shall write one MP4 file with one frame per plane, in CSV row order. |
| FR-10 | Each frame shall show image E, normalised to 8-bit grayscale (0–255). |

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
- **CSV input:** one plane per line, comma-separated integers, e.g. `10,20,30,50,20,30,30,60,30` for a triangle.
- **MP4 output:** one frame per plane, in CSV order.

---

## 6. Open Items

| # | Item | Status |
|---|---|---|
| 1 | Script name: `Ex0.py` in the assignment, `Ex1` in the title | Ask instructor |
| 2 | Frame size when planes differ in size | Proposed: fixed size from the largest plane, padded with 0 |
| 3 | Trapezoid (4 points) support | Optional, after the triangle works |
| 4 | Video normalisation: global min-max or per frame | Proposed: global min-max over the volume |
| 5 | External libraries | numpy approved. Ask before using pynrrd or OpenCV |

---

## 7. Related Documents
- Algorithm details and edge-case handling: EDD (to be written).
- Test plan and test cases: STP and STD (to be written).
- Setup and usage: README.md.
