# Load libraries
import os
import numpy as np
import pydicom
import re



# Load Each Dicom File
def load_dicom_folder(folder_path):
    """
    Loads DICOM frames from a folder and returns a 3D numpy array (H, W, T).
    Sorts files by InstanceNumber if available.
    """
    dicoms = []
    for fname in os.listdir(folder_path):
        path = os.path.join(folder_path, fname)
        if os.path.isfile(path) and fname.lower().endswith('.dcm'):
            dcm = pydicom.dcmread(path)
            dicoms.append((dcm, dcm.InstanceNumber if hasattr(dcm, "InstanceNumber") else 0))

    # Sort by InstanceNumber
    dicoms.sort(key=lambda x: x[1])
    frames = [dcm.pixel_array.astype(np.float64) for dcm, _ in dicoms]

    return np.stack(frames, axis=-1)  # (H, W, T)


# Load All Modalities
def load_modalities_from_folders(mag_dir, px_dir, py_dir, pz_dir, vol_num, slice_num):
    """
    Loads DENSE magnitude and phase data from four separate directories.
    Returns: mag, phase_x, phase_y, phase_z as (H, W, T) arrays.
    """
    # First check the header info of the dicom files to perform negate or swap
    header_check = dicom_header(mag_dir, px_dir, py_dir, pz_dir, vol_num, slice_num)

    # Get the swap and negate info
    swap_xy = header_check['Swap XY']
    negate_flags = header_check['Negate (X/Y/Z)']

    # Load the Magnitude
    mag = load_dicom_folder(mag_dir) / 4095.0  # Normalize to [0, 1] as original data is uint16
    
    # Load the Phase data
    if swap_xy == 0:
        phase_x = load_dicom_folder(px_dir) / 4095.0
        phase_y = load_dicom_folder(py_dir) / 4095.0
        phase_z = load_dicom_folder(pz_dir) / 4095.0
    else: # Swap X and Y when swap_xy is 1
        phase_x = load_dicom_folder(py_dir) / 4095.0  # Swap X and Y
        phase_y = load_dicom_folder(px_dir) / 4095.0  # Swap X and Y
        phase_z = load_dicom_folder(pz_dir) / 4095.0
    
    # Normalized between [-0.5, 0.5],  we dont need to normalize again to -pi to pi
    phase_x = phase_x - 0.5
    phase_y = phase_y - 0.5
    phase_z = phase_z - 0.5

    # Apply negation if needed
    if negate_flags[0] == 1:
        phase_x = -phase_x
    
    if negate_flags[1] == 1:
        phase_y = -phase_y
    
    if negate_flags[2] == 1:
        phase_z = -phase_z
    

    return mag, phase_x, phase_y, phase_z


# Extract Dicom Header Data
def extract_dicom_header_info(dicom_file_path):
    ds = pydicom.dcmread(dicom_file_path)
    header_info = {}
    
    # File name
    header_info['File Name'] = os.path.basename(dicom_file_path)
    
    # Voxel size (PixelSpacing and SliceThickness)
    try:
        pixel_spacing = ds.PixelSpacing  # e.g. [x_spacing, y_spacing]
    except AttributeError:
        pixel_spacing = [None, None]
    slice_thickness = getattr(ds, 'SliceThickness', None)
    header_info['PixelSpacing'] = pixel_spacing
    header_info['SliceThickness'] = slice_thickness
    
    # Image Size (Rows x Columns)
    header_info['Image Size'] = (getattr(ds, 'Rows', None), getattr(ds, 'Columns', None))
    
    # Slice Location
    header_info['Slice Location'] = getattr(ds, 'SliceLocation', None)
    
    # ImageComments tag (0020,4000) contain Encoding Frequency, Swap XY, Negate flags, and Scale.
    encoding_frequency = None
    swap_xy = None
    negate_flags = None
    scale = None
    if (0x0020, 0x4000) in ds:
        image_comments = ds[(0x0020, 0x4000)].value
        # Encoding Frequency pattern "EncFreq:xxx"
        match = re.search(r"EncFreq:([\d\.]+)", image_comments)
        if match:
            encoding_frequency = float(match.group(1))
            
        # Swap XY pattern "RCswap:x"
        swap_match = re.search(r"RCswap:(\d+)", image_comments)
        if swap_match:
            swap_xy = int(swap_match.group(1))
            
        # Negate flags pattern "RCSflip:x/y/z"
        flip_match = re.search(r"RCSflip:([\d/]+)", image_comments)
        if flip_match:
            negate_flags = [int(x) for x in flip_match.group(1).split('/')]
            
        # Scale pattern "Scale:xxx" (only in phase files)
        scale_match = re.search(r"Scale:([\d\.]+)", image_comments)
        if scale_match:
            scale = float(scale_match.group(1))
    else:
        print("ImageComments (0020,4000) not found in this DICOM file.")
        
    header_info['Encoding Frequency'] = encoding_frequency
    header_info['Swap XY'] = swap_xy
    header_info['Negate (X/Y/Z)'] = negate_flags
    header_info['Scale'] = scale

    return header_info

# Evaluate the First Dicom File
def get_first_dicom_file(directory):
    for fname in sorted(os.listdir(directory)):
        if fname.lower().endswith('.dcm'):
            return os.path.join(directory, fname)
    return None

# Export and Save the Dicom Header data
def dicom_header(mag_dir, px_dir, py_dir, pz_dir, vol_num, slice_num):
    """
    Loads header information from one DICOM file in each directory 
    and aggregates the info into a single dictionary with the keys:
    
    dicom_headers = {
         'Slice Name', 'Pixel Spacing', 'Slice Thickness', 'Image Size',
         'Slice Location', 'Swap XY', 'Negate (X/Y/Z)', 'Encoding Frequency (X/Y/Z)', 'Scale'
    }
    
    The common header info is taken from the magnitude file; phase directories
    provide their own encoding frequencies and scale.
    """

    # Get one DICOM file from each directory.
    mag_file = get_first_dicom_file(mag_dir)
    px_file = get_first_dicom_file(px_dir)
    py_file = get_first_dicom_file(py_dir)
    pz_file = get_first_dicom_file(pz_dir)
    
    if not all([mag_file, px_file, py_file, pz_file]):
        raise ValueError("One or more directories do not contain any DICOM files.")
    
    header_mag = extract_dicom_header_info(mag_file)
    header_px = extract_dicom_header_info(px_file)
    header_py = extract_dicom_header_info(py_file)
    header_pz = extract_dicom_header_info(pz_file)

    # Slice Name
    slice_name = f"DENSE{slice_num:02d}"
    
    dicom_headers = {
        'Slice Name': slice_name,
        'Pixel Spacing': header_mag['PixelSpacing'],
        'Slice Thickness': header_mag['SliceThickness'],
        'Image Size': header_mag['Image Size'],
        'Slice Location': header_mag['Slice Location'],
        'Swap XY': header_mag['Swap XY'],
        'Negate (X/Y/Z)': header_mag['Negate (X/Y/Z)'],
        'Enc. Freq. (X/Y/Z)': [
            header_px["Encoding Frequency"],
            header_py["Encoding Frequency"],
            header_pz["Encoding Frequency"],
        ],
        'Scale': header_px["Scale"]  # assumed constant for phases
    }
    
    return dicom_headers