# Testing strategy (To Do #5) — task note

Status: **open**. Finish after the demo (To Do #7) is done.
Spec: [`ALGORITHM.md`](../ALGORITHM.md), section 6.

## Goal
Prove the projection is correct and fast enough, and that the demo
`python Ex0.py file.nrrd file.csv file.mp4` works end to end.

## Levels
1. **Unit tests (pytest)** on tiny synthetic volumes built in code, no files:
   one test per issue in `ALGORITHM.md` §3 (axes, off-by-one, rounding,
   true height `h`, apex, out-of-volume / negative indices, isosceles warning),
   triangle = trapezoid with `a' = a''`, axis-aligned plane = slice of `M`.
2. **Reference vs fast:** the numpy version must equal the loop version on
   random planes (fixed seed).
3. **I/O tests:** NRRD round-trip on a non-cubic `4×5×6` volume
   (`M[1,2,3] == 321`); CSV with 3 / 4 points, bad rows give a clear error.
4. **Performance:** projection only (no load, no encode) on a 500³ volume.
   Pass ≥ 30 fps, target ≥ 100 fps. Report the measured number and machine.
5. **Demo / system test (#7):** run `Ex0.py` on a real NRRD from the dataset
   (#4); check the MP4 exists, has one frame per CSV row, and frames look right.
   Keep the CSV and output used for the experiment (#8).

## To do
- [ ] Unit tests per issue
- [ ] Reference vs fast comparison
- [ ] NRRD / CSV tests
- [ ] FPS benchmark script
- [ ] Demo test after #7
- [ ] Short results note for #8
