# Testing strategy (To Do #5)

Status: **done**. Spec: [ALGORITHM.md](../ALGORITHM.md). Run everything from the repo root after `pip install -r requirements.txt`.

```
pytest
python tests/benchmark.py
python Ex0.py data-NRRD/MRHead_1.nrrd csv/head.csv video/mrhead_planes.mp4
```

`python -m pytest` is the same as `pytest`. This tree: 30 passed. The benchmark below is one run.

## Levels

1. **Unit tests** (`tests/test_projection.py`), on tiny arrays built in code.
   One test per issue in ALGORITHM.md §3 where that issue has a checkable result: axis order of `E`, the off-by-one width, rounding (halves up), true height `h`, the apex sample, samples outside the volume (including negative indices), and the isosceles warning. A triangle equals the trapezoid with `a' = a''`. An axis-aligned rectangle equals the matching slice of `M`.

2. **Reference vs vectorised.** The numpy `project` equals the loop `project_reference` on random triangles and trapezoids (fixed seed).

3. **I/O** (`tests/test_io.py`).
   - NRRD round-trip of a 4×5×6 volume with pynrrd `index_order='F'`: `M[1,2,3] == 321`. A non-3D file and a bad file are errors that name the path.
   - Lecturer CSV: header, `#` comments, blank lines, spaces, fractional and negative coordinates. Triangle rows may end with empty fields. A trapezoid is stored as `a', b, a'', c` and `corners()` returns `PROJECT` order `a', a'', b, c`.
   - `csv/lecturer_example.csv` row 4 (file line 5): equal legs, parallel top and base, and `project` emits no warning.
   - A count that is not 3 or 4, or a 3/4 that does not match the number of coordinates, is an error naming the file and line. So are non-numeric values, non-finite values, and degenerate planes (coincident points, zero leg, zero height).

4. **Performance** (`python tests/benchmark.py`). Projection only, on a Fortran-order 500³ `uint8` volume, 10 planes, 100 projections. Pass ≥ 30 fps, target ≥ 100. This run (Linux-6.12.94+-x86_64): 0.424 s, 235.8 fps, largest image 481×481. The script is not a pytest test.

5. **Demo / system** (`tests/test_demo.py` and the experiment video).
   - `test_demo.py` runs `Ex0.py` on a tiny synthetic NRRD. The MP4 exists, has one frame per CSV row, and is 25 fps. A bad row exits non-zero, names the file and line, and writes no traceback and no MP4. A missing NRRD and a wrong argument count do the same.
   - Experiment: `csv/head.csv` on `data-NRRD/MRHead_1.nrrd` writes `video/mrhead_planes.mp4` (280 frames, 256×256, 529.5 planes/s on the run recorded in the README). `csv/croissant.csv` on the 500³ volume: 100 frames, canvas 502×502, 102.1 planes/s. Small demo CSVs in `video/` cover triangles, trapezoids, and a plane that is partly or fully outside the volume.
