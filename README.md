# DENSEmanualSegmentator

# DENSE Manual Segmentator

This repository provides a tool for manual segmentation of DENSE MRI data, enabling users to interactively edit contours and visualize results. 
The tool supports loading DICOM files and optionally uses MAT files (from the DENSE-Analysis toolbox) to initialize contours.

---

## Features

- **Interactive GUI**: Allows users to manually adjust contours (Epi and Endo) using draggable points.
- **DICOM Support**: Loads DICOM files for magnitude and phase data.
- **MAT File Integration**: Optionally initializes contours using splines from MAT files.
- **Customizable Parameters**: Supports setting the number of points for contours and selecting specific slices and volumes.

---

## Expected Data Structure

Since the `data` folder cannot be uploaded, ensure your data is organized as follows:

data/
**├── DICOM/
**│   ├── Mag/      # Magnitude DICOM files.
**│   ├── X-encPha/ # X-phase encoded DICOM files.
**│   ├── Y-encPha/ # Y-phase encoded DICOM files.
**│   └── Z-encPha/ # Z-phase encoded DICOM files.
**└── MAT/
    └── *.mat   # MAT files from the DENSE-Analysis toolbox (optional).
