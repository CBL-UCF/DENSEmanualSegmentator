import numpy as np
import scipy.io

def resample_contour(contour, num_point=8):
    """
    Given a 2D contour (N x 2 array), return num_points approximately equally spaced points.
    Ensures the contour is closed.
    """
    if not np.allclose(contour[0], contour[-1]):
        contour = np.vstack([contour, contour[0]])
    # Compute cumulative distances
    deltas = np.diff(contour, axis=0)
    seg_lengths = np.sqrt((deltas**2).sum(axis=1))
    cum_dist = np.insert(np.cumsum(seg_lengths), 0, 0)
    total_length = cum_dist[-1]
    # Determine equally spaced distances
    sample_dists = np.linspace(0, total_length, num_point + 1)[:-1]
    resampled = []
    for sd in sample_dists:
        idx = np.searchsorted(cum_dist, sd) - 1
        idx = max(idx, 0)
        length_segment = cum_dist[idx+1] - cum_dist[idx] + 1e-6
        frac = (sd - cum_dist[idx]) / length_segment
        pt = contour[idx] + frac * (contour[idx+1] - contour[idx])
        resampled.append(pt)
    return np.array(resampled)

def process_mat_file_get_control_points(mat_file_path, num_point=8):
    """
    Loads the MATLAB file, extracts the epicardial and endocardial contours,
    converts to 0-based Python indexing, and resamples each contour to exactly
    num_points. Returns a dictionary:
    control_points_per_frame[frame] = { 'epi': resampled_epi, 'endo': resampled_endo }
    
    If contour data are missing for a frame, that frame is skipped.
    """
    matlab_data = scipy.io.loadmat(mat_file_path)
    height, width, num_frames = matlab_data['ImageInfo']['Xwrap'][0, 0].shape
    roi_info = matlab_data['ROIInfo']['Contour'][0][0]
    all_array_epi = [entry[0] for entry in roi_info]
    all_array_endo = [entry[1] for entry in roi_info]

    control_points_per_frame = {}
    for f in range(num_frames):
        if len(all_array_epi[f]) == 0 or len(all_array_endo[f]) == 0:
            print(f"Warning: Empty contour data at frame {f} in {mat_file_path}")
            continue

        # Convert contours to float and use 0-based indexing. (minus 1)
        epi = all_array_epi[f].astype(np.float64)
        endo = all_array_endo[f].astype(np.float64)
        epi[:, 0] -= 1
        epi[:, 1] -= 1
        endo[:, 0] -= 1
        endo[:, 1] -= 1

        resampled_epi = resample_contour(epi, num_point=num_point)
        resampled_endo = resample_contour(endo, num_point=num_point)
        control_points_per_frame[f] = {'epi': resampled_epi,
                                       'endo': resampled_endo}
    return control_points_per_frame