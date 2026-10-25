# Plane Projection of a 3D Volume: Algorithm Specification

This document defines, in detail, the algorithm that projects a 3D volume onto a
plane given by an isosceles triangle (or isosceles trapezoid) and returns a 2D image.
It starts from the method given in the assignment, lists the problems found in it,
and defines the corrected algorithm that the implementation follows.

Scope: the algorithm takes a volume and one plane and produces (a) the raw
projection `E` and (b) the 8-bit grayscale image `I` of that plane. Out of scope:
reading the CSV, putting images into a common frame size, assembling frames into a
video, and MP4 encoding (these belong to the demo, To Do #7).

---

## 1. Inputs, outputs and conventions

**Volume `M`**
- A 3D array of unsigned integers (8, 16 or 32 bit) of size `sx × sy × sz`,
  `1 ≤ sx, sy, sz < 1024`.
- Accessed as `M[x, y, z]` with `0 ≤ x < sx`, `0 ≤ y < sy`, `0 ≤ z < sz`.
- Loaded from NRRD with `pynrrd` using `index_order='F'`, so the array indices match
  `M[x][y][z]` of the assignment (see issue 7).

**Plane**
- Triangle: three points `a, b, c` in voxel index coordinates (IJK),
  where `a` is the apex and `b, c` are the base. Nominally `|ab| = |ac|`.
- Trapezoid: four points `a', a'', b, c`, where `a'→a''` is the top edge,
  `a'→b` and `a''→c` are the two legs (nominally equal in length), and `b→c` is the base.
- Points may be real-valued.
- The CSV lists a trapezoid as `a', b, a'', c` (legs `a'→b` and `a''→c`) and a
  triangle as `a, b, c`. `load_planes` maps a trapezoid row to
  `PROJECT(M, a', a'', b, c)`.

**Pixel size**
- `dist` and the image grid are in voxel index space. One pixel is one voxel
  step along the plane. NRRD spacing in millimetres is not applied, so an
  anisotropic volume is not rescaled.

**Output `E`**
- A 2D array of shape `(H, W)` (rows, columns), same dtype as `M`, indexed `E[y, x]`.
- Row `y = 0` is the apex (or top edge); row `y = H-1` is the base.
- Pixels outside the triangle, and samples that fall outside the volume, are `0`.

**Image `I`**
- A 2D `uint8` array of the same shape `(H, W)`, grayscale `0..255`, produced from
  `E` as defined in section 4.4.

**Notation**
- `dist(p, q)` is the Euclidean distance.
- `round(·)` is round to nearest integer (rule fixed in section 4.3).

---

## 2. The original algorithm (from the assignment)

```
1. Dab = dist(a,b) = dist(a,c);  Dbc = dist(b,c)
2. v(ab) = vector(a,b) / Dab;   v(ac) = vector(a,c) / Dab
3. E = matrix of size Dab*Dbc
4. a1 = a; a2 = a
5. for (y = 0; y < Dab; y++)
     a. a1 = a1 + v(ab)
     b. a2 = a2 + v(ac)
     c. p = a1
     d. d12 = dist(a1, a2)
     e. dp = vector(a1, a2) / d12
     f. for (x1 = 0; x1 <= d12; x1++)
          i.   v = M[p]            # v = 0 if p is not in M
          ii.  x = Dbc/2 - d12/2 + x1
          iii. E[x][y] = v
          iv.  p = p + dp
6. return E
```

The assignment notes that this is not well defined for implementation. Section 3
lists the issues; section 4 defines the corrected algorithm.

---

## 3. Issues found and fixes

### Issue 1: Output axes are swapped
**Problem.** `E` is defined as `Dab × Dbc` (rows × columns) but written as `E[x][y]`,
where `x` ranges up to `Dbc`. For a wide triangle (`Dbc > Dab`) this raises an index
error; for a narrow one the image comes out transposed.
**Fix.** `E` has shape `(H, W)` and is always written as `E[y, x]` (row, column).

### Issue 2: Off-by-one at the base row (fence-post)
**Problem.** The inner loop `x1 = 0 .. d12` is inclusive, so a row of length `d12`
has `d12 + 1` samples. On the base row `d12 = Dbc`, so the last sample lands at
`x = Dbc`, but a row of width `Dbc` has indices `0 .. Dbc-1`.
Example: `Dbc = 10` gives 11 samples, indices `0..10`, in an image of width 10.
**Fix.** `W = round(Dbc) + 1`. Sampling stays inclusive so both edges of the
triangle (`AB` and `AC`) are sampled, keeping the image symmetric.

### Issue 3: Real-valued distances used as sizes and indices
**Problem.** `Dab`, `Dbc`, `d12` and `x` are real numbers. An array cannot have a
real size, and `x` cannot index it. Also, stepping exactly one voxel while
`x1 <= d12` leaves a remainder: for `d12 = 7.07` the loop stops after 7 steps and
never reaches `a2` (on the base row, `c` itself is not sampled).
**Fix.** Round once per quantity, then work with integers only:
- per row, `n = round(dist(a1, a2))` steps;
- step `dp = (a2 - a1) / n` (for `n > 0`), so the step is approximately one voxel
  and the last sample lands exactly on `a2`;
- the `k`-th sample is computed directly as `a1 + k·dp` (no accumulated
  `p = p + dp`, so no floating-point drift along the row);
- integer centring offset `x0 = (W - 1 - n) // 2`. Since `n ≤ W - 1`,
  `x0 + n ≤ W - 1` and no write is out of range.

### Issue 4: Vertical stretching (geometric distortion)
**Problem.** `a1` and `a2` advance one voxel along the slanted legs, but rows of the
image are stacked along the triangle's height. The true height is

$$ h = \sqrt{D_{ab}^2 - (D_{bc}/2)^2} $$

so consecutive rows are only `h / Dab` voxels apart in 3D while each occupies a full
pixel in `E`. The image is stretched vertically by a factor `Dab / h`.
Example: `Dab = 10`, `Dbc = 16` gives `h = 6`; the triangle is 6 voxels tall but the
image has 10 rows, a 1.67× stretch. Circles appear as ellipses and vertical
distances are wrong. The error is small for narrow triangles and grows as the base widens.
**Fix (deliberate deviation from the assignment's `Dab × Dbc` size).** The number of
rows follows the true height: `H = round(h) + 1`. Each row is a fraction
`t = y / (H - 1)` of the way from the apex to the base:

```
a1 = a + t · (b - a)     # point on AB
a2 = a + t · (c - a)     # point on AC
```

Both image axes then have about one voxel per pixel (square pixels).
*Alternative considered:* keep `H` from `Dab` as written in the assignment. Rejected
because it distorts the anatomy and makes measurements in the image unreliable.

### Issue 5: The apex is never sampled
**Problem.** `a1` and `a2` are advanced before the first sample, so row 0 starts one
step below `a`.
**Fix.** Covered by issue 4: at `t = 0`, `a1 = a2 = a`, so row 0 is the apex itself.
At `t = 1`, `a1 = b` and `a2 = c`, so the base is sampled exactly.

### Issue 6: "Outside the volume" check and negative indices
**Problem.** In numpy, negative indices are valid (`M[-1]` is the last slice), so a
point slightly outside the volume (e.g. `x = -0.6`, rounded to `-1`) silently reads a
value from the opposite side. Checking only the upper bound is not enough.
**Fix.** Round first, then check both bounds on all three axes:

```
(i, j, k) = round(p)
if 0 ≤ i < sx and 0 ≤ j < sy and 0 ≤ k < sz:  v = M[i, j, k]
else:                                         v = 0
```

Rounding before the check makes the boundary consistent: `-0.4 → 0` is inside,
`-0.6 → -1` is outside.

### Issue 7: Axis order when reading NRRD
**Problem.** NRRD stores data with `x` varying fastest. Read into numpy in the default
C order, the array is `[z, y, x]`; indexed as `[x, y, z]`, the projection silently
samples the wrong plane. A cubic volume (e.g. 500³) gives no shape error to reveal it.
**Fix.** Read with `pynrrd`, `index_order='F'`, so the array is `M[x, y, z]`, and
check that `M.shape` equals the header `sizes`. The program does not parse NRRD
itself. `pynrrd` and numpy are the dependencies of this algorithm.

### Issue 8: Exact isosceles assumption
**Problem.** The method assumes `dist(a,b) = dist(a,c)` exactly and divides both legs
by `Dab`. With real or integer voxel coordinates this rarely holds exactly; if
`|ac| ≠ |ab|`, `a2` does not end at `c`.
**Fix.** The parametrisation of issue 4 does not depend on leg lengths: `a2` reaches
`c` exactly at `t = 1` regardless of `|ac|`. The plane is still accepted; a warning is
issued if `| |ab| − |ac| | > 1` voxel.

---

## 4. The corrected algorithm

### 4.1 Unified form (triangle and trapezoid)

A triangle is treated as a trapezoid whose top edge has zero length:
`a' = a'' = a`. One procedure handles both.

```
PROJECT(M, a', a'', b, c) -> E

  # geometry
  top_mid  = (a' + a'') / 2
  base_mid = (b + c) / 2
  h        = dist(top_mid, base_mid)          # true height
  Wtop     = dist(a', a'')                     # 0 for a triangle
  Wbase    = dist(b, c)
  H        = round(h) + 1
  W        = round(max(Wtop, Wbase)) + 1

  E = zeros((H, W), dtype of M)

  for y in 0 .. H-1:
      t  = y / (H - 1)            if H > 1 else 0
      a1 = a'  + t · (b - a')      # left leg
      a2 = a'' + t · (c - a'')     # right leg
      n  = round(dist(a1, a2))
      dp = (a2 - a1) / n           if n > 0 else 0
      x0 = (W - 1 - n) // 2        # centre the row
      for k in 0 .. n:             # inclusive: samples a1 and a2
          p = a1 + k · dp
          E[y, x0 + k] = SAMPLE(M, p)

  return E


SAMPLE(M, p):
  (i, j, k) = round(p)
  if 0 ≤ i < sx and 0 ≤ j < sy and 0 ≤ k < sz: return M[i, j, k]
  return 0
```

For a triangle, `PROJECT(M, a, a, b, c)`.
The full per-plane result is `I = TO_IMAGE(PROJECT(M, a', a'', b, c), lo, hi)`.

### 4.2 Vectorised form (implementation)

The loops above are the reference definition. The implementation computes a whole
image at once with numpy, with no Python loop over pixels:

1. Build the row parameters `t[y]` (length `H`) and per-row endpoints `a1[y]`, `a2[y]`
   (arrays of shape `(H, 3)`).
2. Compute `n[y]`, `x0[y]`, `dp[y]`.
3. Build the grid of column positions `k = x - x0[y]` for all `(y, x)`; pixels with
   `k < 0` or `k > n[y]` are outside the triangle (mask A).
4. Compute all sample points `P[y, x] = a1[y] + k · dp[y]` (shape `(H, W, 3)`), round to
   integers.
5. Mask B: all three indices inside the volume.
6. Gather `E[A & B] = M[i, j, k]` with one fancy-indexing operation; the rest stay 0.

Buffers that depend only on `(H, W)` can be reused between planes of the same size.
Per-plane cost is `O(H · W)`; it does not depend on the volume size.

The "avoid multiplication in the inner loop" idea (`p = p + dp`) is not used: in numpy
it gives no speed-up and accumulates rounding error along the row.

### 4.3 Rounding rule

All real-to-integer conversions (sizes, `n`, sample coordinates) use one rule:
`round(v) = floor(v + 0.5)` (halves round up). It is used consistently, so a point
exactly halfway between two voxels always maps to the same voxel.

### 4.4 From projection E to image I

`E` holds the raw voxel values. The image `I` is the 8-bit grayscale of that plane.
The intensity window `[lo, hi]` is computed once per volume from `M`: `lo` is the
1st percentile and `hi` the 99th percentile of `M`'s values. The window is global,
not per plane, so the same voxel value gives the same gray level in every image of
that volume.

It is not computed per plane: brightness would change between planes and images
could not be compared. Percentiles are used rather than the minimum and the maximum:
one outlier voxel would darken the whole image.

```
WINDOW(M) -> (lo, hi)

  lo = 1st percentile of the values of M
  hi = 99th percentile of the values of M
  return (lo, hi)


TO_IMAGE(E, lo, hi) -> I

  if hi == lo:                       # constant volume: no division by zero
      return zeros(shape of E, uint8)
  I = round(clip((E - lo) / (hi - lo), 0, 1) * 255) as uint8
  return I
```

Pixels outside the triangle or trapezoid, and samples outside the volume, are `0`
in `E`. They appear black in `I`. When `lo > 0` they map to `0` by clipping, which
is the intended result.

Vectorised: `I` is one numpy expression on the whole image. `WINDOW` is computed
once at load time, not per plane.

---

## 5. Edge cases

| Case | Behaviour |
|---|---|
| Plane entirely outside the volume | Valid; returns an all-zero image. |
| Plane partly outside the volume | Samples outside are 0 (issue 6). |
| Apex row (`t = 0`, triangle) | `n = 0`, a single sample at `a`, centred. |
| `b = c` (zero base) | Degenerate; rejected with an error. |
| `a`, `b`, `c` collinear, or `h = 0` | Degenerate; rejected with an error. |
| Coincident points | Degenerate; rejected with an error. |
| Legs differ by more than 1 voxel | Accepted, with a warning (issue 8). |
| Point coordinates not numeric, or wrong count | Rejected with an error naming the row. |
| Constant volume (`hi = lo`) | `I` is all zeros. |

