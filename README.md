# DENSE Manual Segmentator

This repository provides a tool for manual segmentation of DENSE MRI data, enabling users to interactively edit contours and visualize results. 
The tool supports loading DICOM files and optionally uses MAT files (from the DENSE-Analysis toolbox) to initialize contours.

[![Python 3.8+](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## ✨ Features

- **Interactive GUI**: Allows users to manually adjust contours (Epi and Endo) using draggable points.
- **DICOM Support**: Loads DICOM files for magnitude and phase data.
- **MAT File Integration**: Optionally initializes contours using splines from MAT files.
- **Customizable Parameters**: Supports setting the number of points for contours and selecting specific slices and volumes.

---

## 🏗️ Expected Data Structure

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
---

## 🚀 How to Run

1.  **Prepare your data**: Organize your `DICOM` and (optional) `MAT` files in the `data/` directory as shown above.
2.  **Execute the script**: Run the main script after modifying the inputs and corresponding folder path at the 'Input Dicom' section. 

* `--slice`: The slice number to process.
* `--volume`: The volume or subject ID.
* `--num_points`: The number of control points per contour (default is 8).
* `--use_mat`: An optional flag to initialize contours from a `.mat` file.

---

## 🎮 GUI Controls

The graphical user interface (GUI) is designed for efficient manual segmentation.

### Mouse Controls 🖱️

| Action                       | Effect                                                                                                                                                             |
| ---------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Left Click + Drag** | **Move a Control Point**: Click and drag a yellow control point to adjust the shape of the contour.                                                                  |
| **`Shift` + Left Click + Drag** | **Move an Entire Contour**: Hold `Shift`, then click near a contour line and drag to move the whole shape. Dragging the outer (Epi) contour moves both contours together. |
| **Right Click + Drag** | **Pan View**: Click and drag with the right mouse button to pan the view. All six panels will move in sync.                                                          |
| **Mouse Scroll Wheel** | **Zoom**: Scroll up to zoom in and scroll down to zoom out. The zoom is centered on your mouse cursor's position.                                                     |

### Keyboard Shortcuts ⌨️

| Key(s)           | Action                                                                   |
| ---------------- | ------------------------------------------------------------------------ |
| **`→` (Right Arrow)** | Go to the **next** time frame.                                           |
| **`←` (Left Arrow)** | Go to the **previous** time frame.                                       |
| **`Ctrl` + `Z`** | **Undo** the last contour modification on the *current frame*.           |
| **`Enter`** | **Close** the application window (does not save automatically).          |

### Control Buttons

* **`<< Prev` / `Next >>`**: Navigate between time frames.
* **`Copy from << Prev Frame`**: Replaces the current frame's contours with the contours from the previous frame.
* **`Copy from >> Next Frame`**: Replaces the current frame's contours with the contours from the next frame.
* **`Reset Zoom`**: Resets the zoom and pan to the default full view.
* **`Save Results`**: Saves the magnitude, phase, and final mask data as NIfTI files in the `data/NIFTI/` directory.

---

## 📖 Citation

*(                                 )*

---

## 🔑 License

This project is licensed under the MIT License. See the `LICENSE` file for details.
