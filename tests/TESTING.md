# Test plan and test cases

Spec: [SRS.md](../SRS.md) and [ALGORITHM.md](../ALGORITHM.md). This run: 2026-10-25, Linux-6.12.94+-x86_64. Every case below passed.

## 1. Test plan (STP)

**Scope.** The projection (`src/projection.py`), NRRD and CSV loading (`src/io_utils.py`), and the demo `Ex0.py`. Out of scope: a GUI, formats other than NRRD, and scaling images to millimetres.

**Levels.**

| Level | What it covers | Cases |
|---|---|---|
| Unit | One image, or one rounding rule, on a volume of a few voxels | TC-01–TC-12 |
| Unit, scaled | The same invariants on N = 8, 32, 128, 256 | TC-13, TC-14 |
| Integration | NRRD round-trip, lecturer CSV, `Plane` with `PROJECT` | TC-16–TC-26, and the CSV half of TC-05 |
| System | `python Ex0.py file.nrrd file.csv file.mp4` | TC-27–TC-30 |
| Acceptance | Frames per second on a 500³ volume. Not part of pytest | TC-15 |

**Approach and tools.** Small problems first: a ramp `M[x,y,z] = x + 10y + 100z` and planes whose every pixel was calculated by hand (`round(v) = floor(v+0.5)`). Then the same checks on larger cubes, with planes kept about 16 voxels wide so the reference loop stays cheap. N = 500 is only in the benchmark. Tools: pytest, numpy, pynrrd, OpenCV. The vectorised `project` is compared with the loop `project_reference`.

**Environment and data.** Python 3, from the repo root, after `pip install -r requirements.txt`. Synthetic arrays. Lecturer files used as-is: `csv/lecturer_example.csv` (TC-24) and `csv/head.csv` (TC-25, count only). The automated tests do not need `data-NRRD/`.

**Entry.** SRS and ALGORITHM describe the behaviour, and the requirements are installed.

**Exit.** `pytest` passes (including the N=128 timing check), and `python tests/benchmark.py` reports at least 30 fps on the 500³ large plane. The target is 100.

**Risks.** The fps number moves with the machine; the recorded run is the exit check, the must is 30. `mp4v` is lossy and OpenCV reports it as `FMP4`, so TC-30 checks where the bright pixel landed, not the exact gray level. A bad plane is an error that names the file and line (FR-4, FR-5). The Drive `edge_cases.csv` instead asks for a black frame and a warning, so that file is not a test here.

## 2. Test cases (STD)

Preconditions for all rows: repo root, dependencies installed. Steps: `pytest` for TC-01–TC-14 and TC-16–TC-30, `python tests/benchmark.py` for TC-15. Result of this run: pass.

| ID | Title | Verifies | Input | Expected |
|---|---|---|---|---|
| TC-01 | Round halves up | FR-8 | ±0.5, ±1.5, 2.4, 2.5 | floor(v+0.5): 0.5→1, −0.5→0, 2.5→3 |
| TC-02 | Sample each end of each axis | FR-7, FR-8 | 3×3×3 ramp | −0.6 and 2.5 are 0; −0.5 and 2.4 are inside; no wrap to 222 |
| TC-03 | One-pixel apex | FR-2, FR-6, NFR-1 | 2×2×2, h=0.2, base 0.4, uint8 and uint32 | E = [[5]] |
| TC-04 | Axis-aligned triangle | FR-6, FR-7, NFR-1 | 5×5×1 ramp, apex (2,4,0), base length 4 | exact 5×5; both base ends; one apex pixel |
| TC-05 | Trapezoid, lecturer order | FR-3, FR-6, NFR-1 | 6×3×1 ramp; CSV `a', b, a'', c` | exact 3×5, short row centred; CSV gives the same E |
| TC-06 | Height and fence-post | FR-6, NFR-1 | legs 10, base 16, marked apex and ends | shape (7, 17), not 11 rows; pixels 100, 200, 300 |
| TC-07 | Non-integer base | FR-6, FR-8, NFR-1 | 3×3×3 ramp, base √5 | exact 3×3; both endpoints sampled |
| TC-08 | Plane outside the volume | FR-7, NFR-1 | 2×2×2, all corners x<0 | exact 3×3 zeros |
| TC-09 | Plane crossing the boundary | FR-7, NFR-1 | 4×4×1 ramp, base crosses x=0 | exact 4×5; the outside sample is 0 |
| TC-10 | Leg-warning threshold | FR-4 | gap of 1, then gap of 1.1 | gap 1 is silent; 1.1 warns; base ends are still hit |
| TC-11 | Degenerate planes | FR-4 | coincident, zero base, zero leg, collinear, zero height | ValueError naming the reason |
| TC-12 | Window and 8-bit image | FR-6 | one voxel 10 among zeros; samples over [0, 200]; constant 7 | p99 is 9.3, not the max; [[0,64,128,255,255]]; flat window is black |
| TC-13 | Invariants at larger N | FR-6, FR-7, NFR-1, NFR-2 | ramp N³, N = 8, 32, 128, 256; small planes | reference = vectorised; H/W formula; outside is 0; window is p1/p99; image is uint8 in 0..255 |
| TC-14 | N=128 timing sanity | NFR-5 | 128³, one 65×65 square, 10 calls | under 2 s. Skip with `pytest -m "not perf"` |
| TC-15 | Scaling benchmark | NFR-3, NFR-4, NFR-5 | N = 64, 128, 256, 500; small, medium, large squares | table below; 500³ large plane ≥ 30 fps, target 100 |
| TC-16 | NRRD uint16 axis order | FR-2, NFR-1 | 4×5×6, M = x+10y+100z | M[1,2,3] = 321 after a round trip |
| TC-17 | NRRD uint8 and uint32 | FR-2 | 2×2×2, M[1,1,1] = 7 | dtype and value survive |
| TC-18 | Bad NRRD | FR-5 | a text file; a 2D array | error names the file |
| TC-19 | CSV triangle and trapezoid | FR-3 | counts 3 and 4, a blank line | points kept; trapezoid maps to a', a'', b, c |
| TC-20 | Header, comments, blanks | FR-3 | header, blank, `#`, spaces, −1.5 | two planes; line numbers are the file lines |
| TC-21 | Bad CSV values | FR-5 | count 1; the word abc; nan | error names the file and the line |
| TC-22 | Count mismatch | FR-3, FR-5 | count 4 with 9 numbers; count 3 with 12 | error says the count does not match |
| TC-23 | Degenerate CSV row | FR-4, FR-5 | coincident, zero leg, zero height | error names the file and the line |
| TC-24 | lecturer_example.csv row 4 | FR-3, FR-4 | `csv/lecturer_example.csv` | 4 planes; equal legs, parallel sides, no warning |
| TC-25 | head.csv plane count | FR-3 | `csv/head.csv` | 280 planes, file lines 2–281, 60 triangles |
| TC-26 | Plane.project | FR-6 | 8×8×4, apex voxel 9 | matches the reference; centre pixel is 9 |
| TC-27 | Ex0 frame count | FR-1, FR-9, FR-10 | tiny NRRD, two CSV rows | 2 frames, 1 fps, fourcc read back as FMP4, even canvas, no traceback |
| TC-28 | Ex0 bad row | FR-5 | second row has count 1 | non-zero exit, message contains line 2, no MP4 |
| TC-29 | Ex0 usage and missing file | FR-1, FR-5 | one argument; missing NRRD | usage line; message names the path; no traceback |
| TC-30 | Ex0 centres the small frame | FR-10 | 8×8 canvas, then a 1×1 plane | the only bright pixel is at (3, 3), not the corner |

## 3. Traceability

| Requirement | Cases | Test function |
|---|---|---|
| FR-1 | TC-27, TC-29 | `test_tc27_ex0_one_frame_per_row`, `test_tc29_missing_file_and_usage` |
| FR-2 | TC-03, TC-16, TC-17 | `test_tc03_one_pixel_apex`, `test_tc16_nrrd_uint16_axis_order`, `test_tc17_nrrd_uint8_and_uint32` |
| FR-3 | TC-05, TC-19, TC-20, TC-22, TC-24, TC-25 | `test_tc05_trapezoid_lecturer_order_exact`, `test_tc19_csv_triangle_and_trapezoid`, `test_tc20_csv_header_comments_blanks`, `test_tc22_csv_count_mismatch`, `test_tc24_lecturer_example_row4`, `test_tc25_head_csv_has_280_planes` |
| FR-4 | TC-10, TC-11, TC-23, TC-24 | `test_tc10_leg_warning_threshold`, `test_tc11_degenerate_planes_are_rejected`, `test_tc23_degenerate_csv_names_the_line`, `test_tc24_lecturer_example_row4` |
| FR-5 | TC-18, TC-21, TC-22, TC-23, TC-28, TC-29 | `test_tc18_bad_nrrd_names_the_file`, `test_tc21_csv_bad_values_name_the_line`, `test_tc22_csv_count_mismatch`, `test_tc23_degenerate_csv_names_the_line`, `test_tc28_bad_row_exits`, `test_tc29_missing_file_and_usage` |
| FR-6 | TC-03–TC-07, TC-12, TC-13, TC-26 | `test_tc03_one_pixel_apex`, `test_tc04_axis_aligned_triangle_exact`, `test_tc05_trapezoid_lecturer_order_exact`, `test_tc06_height_and_fencepost_on_the_wide_triangle`, `test_tc07_non_integer_base_reaches_both_ends`, `test_tc12_window_and_to_image`, `test_tc13_invariants_hold_as_n_grows`, `test_tc26_plane_project_matches` |
| FR-7 | TC-02, TC-04, TC-08, TC-09, TC-13 | `test_tc02_sample_each_side_of_each_axis`, `test_tc04_axis_aligned_triangle_exact`, `test_tc08_plane_outside_is_all_zero`, `test_tc09_partial_plane_exact`, `test_tc13_invariants_hold_as_n_grows` |
| FR-8 | TC-01, TC-02, TC-07 | `test_tc01_round_halves_up`, `test_tc02_sample_each_side_of_each_axis`, `test_tc07_non_integer_base_reaches_both_ends` |
| FR-9 | TC-27 | `test_tc27_ex0_one_frame_per_row` |
| FR-10 | TC-27, TC-30 | `test_tc27_ex0_one_frame_per_row`, `test_tc30_smaller_frame_is_centred` |
| NFR-1 | TC-03–TC-09, TC-13, TC-16 | the exact-image tests and `test_tc13_invariants_hold_as_n_grows`, `test_tc16_nrrd_uint16_axis_order` |
| NFR-2 | TC-13 | `test_tc13_invariants_hold_as_n_grows` |
| NFR-3 | TC-15 | `tests/benchmark.py` (500³ large plane, target 100 fps) |
| NFR-4 | TC-15 | `tests/benchmark.py` (500³ large plane, must 30 fps) |
| NFR-5 | TC-14, TC-15 | `test_tc14_n128_projection_stays_cheap`, `tests/benchmark.py` |
| NFR-6 | TC-01–TC-14 | those tests import the modules and build their own arrays; they do not read `data-NRRD/` |

No SRS requirement is without a case.

## 4. How to run

From the repo root:

```
pytest
python tests/benchmark.py
```

`python -m pytest` is the same command. `pytest -m "not perf"` skips TC-14.

## 5. Measured results

`pytest`: **32 passed in 0.92 s**.

`python tests/benchmark.py`, projection only:

```
    N plane            HxW     pixels  reps  seconds    us/px      fps
   64 small        9x9             81   551    0.050    1.121  11014.7
   64 medium      17x17           289   519    0.050    0.333  10376.5
   64 large       45x45          2025   340    0.050    0.073   6797.7
  128 small        9x9             81   539    0.050    1.148  10758.5
  128 medium      33x33          1089   404    0.050    0.114   8071.9
  128 large      109x109        11881    89    0.050    0.048   1764.6
  256 small        9x9             81   552    0.050    1.120  11025.1
  256 medium      65x65          4225   239    0.050    0.050   4773.4
  256 large      237x237        56169    19    0.051    0.048    372.8
  500 small        9x9             81   545    0.050    1.133  10891.7
  500 medium     126x126        15876    97    0.050    0.033   1932.4
  500 large      481x481       231361    39    0.301    0.033    129.7
```

The same 9×9 plane takes 1.01× as long on a 500³ volume as on a 64³ volume. The volume is 477× larger, so the time is not following N³. The large-plane time ratio 500/64 is 52.4×, against a pixel ratio of 114.3× and that same volume ratio of 477×. Microseconds per pixel fall from 0.073 at 45×45 to 0.033 at 481×481.

500³ large plane: **129.7 fps**. Must 30, target 100. Result: meets the 100 fps target.
