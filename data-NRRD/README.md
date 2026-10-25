# NRRD data set

Sample 3D volumes used to test and demo the plane projection.

## Contents
Each file is a 3D volume in NRRD format (`.nrrd`). Keep one file per volume and use a descriptive name, for example:

- `mri_brain_t1.nrrd`: MRI brain volume (from 3D Slicer sample data)

## Requirements for each file
- Dimensions: `1 ≤ sx, sy, sz < 1024`.
- Voxel type: unsigned integer, 8, 16 or 32 bit (`type: uint8`, `uint16` or `uint32`).
- Header `sizes` matches the data.

## Source
- Sample volumes from 3D Slicer (https://download.slicer.org).

## Notes
- Large files: if a file is above the GitHub size limit (100 MB), do not commit it. Keep it locally and note its name here.
