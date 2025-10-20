from utils.dicom_loader import load_modalities_from_folders, dicom_header
from utils.contour_editor import draw_draggable_dual_contour
from utils.mat_loader import process_mat_file_get_control_points
import matplotlib.pyplot as plt
from utils.construct_nifti_path import construct_nifti_paths_from_mag_dir



###################################### Inputs Dicom #####################################

# Volume and Slice numbers
vol_num = 33
slice_num = 9

# Dicom folders
mag_dir = r"data\DICOM\Mag"
px_dir =  r"data\DICOM\X-encPha"
py_dir =  r"data\DICOM\Y-encPha"
pz_dir =  r"data\DICOM\Z-encPha"

# If you have a MAT files (from DENSE-Analysis toolbox) as the starting point
use_mat_splines = True  # Set to True if you want to use the splines from the mat file
mat_file_path = r"data\MAT\DENSE09_bh_3dir_3pc_ke10_2SI_4000RO_2p5x2p5x8.mat" # Modify the path to the MAT file accordingly if NEEDED

# Number of Points to construct contours
num_point = 8

################################# Construct Nifti Paths ##################################
nifti_paths = construct_nifti_paths_from_mag_dir(vol_num, slice_num)
print()
print("Nifti Paths: ")
[print(f"   {key:<25} {value}") for key, value in nifti_paths.items()]
print()

##################################### Handle MAT #########################################

if use_mat_splines:  
    mat_file_path = mat_file_path # Ensure the path is set
    control_points_per_frame = process_mat_file_get_control_points(mat_file_path, num_point=num_point)
else:
    mat_file_path = None
    control_points_per_frame = None

#################################### Run the GUI #########################################

# Read the data
mag, phase_x, phase_y, phase_z = load_modalities_from_folders(mag_dir, px_dir, py_dir, pz_dir, vol_num, slice_num)
headers = dicom_header(mag_dir, px_dir, py_dir, pz_dir, vol_num, slice_num)


# Call the GUI
contours = draw_draggable_dual_contour(mag, phase_x, phase_y, phase_z, headers=headers, initial_frame=0, nifti_path=nifti_paths,
                                        use_mat_splines=use_mat_splines, control_points_per_frame=control_points_per_frame, num_point=num_point)

