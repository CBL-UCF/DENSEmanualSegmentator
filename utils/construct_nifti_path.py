import os
import re


def construct_nifti_paths_from_mag_dir(vol_num, slice_num):
    """
    Given the volume number and slice number, constructs file paths for
    magnitude, phase (X, Y, Z), and mask NIfTI files based on a predefined directory structure.
    """
    
    # Format subject and slice strings
    subject_str = f"subject{vol_num:03d}"
    slice_str = f"slice{slice_num:02d}"

    # Build the base directory 
    nifti_base = r"data\NIFTI"
    if not os.path.exists(nifti_base):
        os.makedirs(nifti_base)

    paths = {
        "mag_nifti_path": os.path.join(nifti_base, "Mag", f"{subject_str}_{slice_str}_0000.nii.gz"),
        "phase_x_nifti_path": os.path.join(nifti_base, "PhsX", f"{subject_str}_{slice_str}_0001.nii.gz"),
        "phase_y_nifti_path": os.path.join(nifti_base, "PhsY", f"{subject_str}_{slice_str}_0002.nii.gz"),
        "phase_z_nifti_path": os.path.join(nifti_base, "PhsZ", f"{subject_str}_{slice_str}_0003.nii.gz"),
        "mask_nifti_path": os.path.join(nifti_base, "Mask", f"{subject_str}_{slice_str}.nii.gz")
    }
    return paths