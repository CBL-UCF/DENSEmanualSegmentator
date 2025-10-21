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

```text
data/
├── DICOM/            # ------------------ INPUT -------------------
    ├── Mag/          # Magnitude DICOM files
    ├── X-encPha/     # X-phase encoded
    ├── Y-encPha/     # Y-phase encoded
    └── Z-encPha/     # Z-phase encoded
├── MAT/              # ------------- INPUT (Optional) -------------
    └── *.mat         # MAT files from the DENSE-Analysis toolbox (optional)
└── NIFTI/            # ------------------ OUTPUT ------------------
    ├── Mag/          # Magnitude
    ├── Mask/         # Mask (main output)
    ├── PhsX/         # Phase-X
    ├── PhsY/         # Phase-Y
    └── PhsZ/         # Phase-Z
```

