# Brief: Plane projection of a 3D volume (for discussion)

Use this file to discuss the algorithm and its optimization with another AI.

## Problem
- Volume M: integer array of size sx × sy × sz (8, 16, or 32-bit unsigned values), with indices 0 ≤ x < sx, 0 ≤ y < sy, 0 ≤ z < sz. Each dimension is below 1024.
- Plane p: an isosceles triangle with vertices a, b, c where dist(a,b) = dist(a,c). The 4-point variant is an isosceles trapezoid (two equal-length sides a'→b and a''→c).
- Output E: 2D image of size Dab × Dbc, where Dab = dist(a,b) = dist(a,c) and Dbc = dist(b,c).
- Input file: NRRD volume plus a CSV with one plane per row (3 or 4 points each).
- Output file: MP4 with one frame per plane, in CSV order.

## Algorithm (from the assignment)
```
Dab = dist(a,b) = dist(a,c)
Dbc = dist(b,c)
v_ab = (b - a) / Dab            # unit vector
v_ac = (c - a) / Dab            # unit vector
E = zeros(Dab, Dbc)             # output image
a1 = a; a2 = a

for y in 0 .. Dab-1:
    a1 = a1 + v_ab              # move left edge down
    a2 = a2 + v_ac              # move right edge down
    p  = a1
    d12 = dist(a1, a2)
    dp = (a2 - a1) / d12        # unit step along the row
    for x1 in 0 .. d12 (inclusive):
        v = M[p] if p inside M else 0
        x = Dbc/2 - d12/2 + x1  # center the row horizontally
        E[x][y] = v
        p = p + dp
return E
```

## Geometry in words
- Each iteration of the outer loop is one horizontal row of the output image.
- a1 slides along edge AB and a2 slides along edge AC, at the same speed.
- Each row is the segment a1→a2 in 3D space, sampled at unit steps.
- The row length d12 shrinks from near 0 at the apex to Dbc at the base.
- The row is centred in the output, so the image looks like a triangle.

## Decisions already made
- Language: Python 3. numpy is approved. Other libraries need approval.
- Coordinates in the CSV are voxel indices (IJK), not millimetres.
- Real-valued sample points are rounded to the nearest voxel.
- Points outside the volume give value 0.

## Open questions
1. Frame size for planes of different sizes: fixed size with padding, or per-frame size?
2. Video normalisation: global min-max over the volume, or per frame?
3. Whether to support the trapezoid (4 points) in the first version.

## Optimisation ideas to discuss
1. **Avoid multiplication in the inner loop.** Update `p += dp` instead of computing `a1 + t * dp`.
2. **Precompute the valid range of x1 per row.** Find where p stays inside M, then loop only over that range. This removes the per-sample bounds check.
3. **Hoist invariants.** v_ab, v_ac, and Dab/Dbc are computed once per plane.
4. **Flat memory layout.** Store M as a 1D array with index `x + sx*(y + sy*z)`, or use the memory layout that matches the sampling direction, to reduce cache misses.
5. **Vectorise rows with numpy.** Compute all sample points of a row at once: `pts = a1 + t[:, None] * dp`, then gather values with fancy indexing.
6. **Parallelise.** Rows are independent (each writes its own y), so they can run on multiple cores. Planes in the video are also independent.
7. **Reuse buffers.** Allocate E once and overwrite it. Avoid per-frame allocation.
8. **Separate timing.** Measure projection time apart from NRRD loading and MP4 encoding, since the FPS target refers to the projection.

## Questions to ask the other AI
- Is the sample-rounding rule consistent with the centring formula, or can it cause gaps or double-writes in the output?
- Is the row-range precomputation correct for triangles where the segment crosses the volume boundary?
- For numpy, is fancy indexing fast enough for 500³ volumes, or is a compiled extension (e.g. numba) needed?
- What is the expected error in d12 when the point coordinates are not integers?
- Edge cases: Dab = 0, degenerate triangles, planes that lie completely outside the volume.
