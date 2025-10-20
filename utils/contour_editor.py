
# Load the libraries
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
from scipy.interpolate import splprep, splev
from matplotlib.widgets import Button
import copy
import matplotlib.path as mpath
from matplotlib.colors import ListedColormap
import nibabel as nib
import os


def draw_draggable_dual_contour(mag, phase_x, phase_y, phase_z, headers, nifti_path, initial_frame=0, 
                                use_mat_splines=False, control_points_per_frame=None, num_point=8):

    # Get the shape of the images
    H, W, num_frames = mag.shape

    # plot
    fig, axes = plt.subplots(2, 3, figsize=(12, 6))
    axs = axes.flatten()

    # fig.subplots_adjust(bottom=0.25)
    fig.subplots_adjust(left=0.02, right=0.74, top=0.93, bottom=0.02)
    fig.subplots_adjust(wspace=0.01, hspace=0.01)

    title_text = fig.suptitle(f"Frame: {initial_frame + 1}/{num_frames}", fontsize=18, fontweight='bold')

    titles = ['Magnitude', 'Spline & Mask', 'Mask', 'Phase-X', 'Phase-Y', 'Phase-Z']
    image_arrays = [mag, mag, mag, phase_x, phase_y, phase_z]
    images = []

    for i, ax in enumerate(axs):
        # add a title to the top left corner of each image
        ax.text(0.02, 0.96, titles[i], transform=ax.transAxes,
        fontsize=12, color='gold', verticalalignment='top', bbox=dict(facecolor='black', alpha=0.5, pad=5))
        img = ax.imshow(image_arrays[i][:, :, initial_frame], cmap='gray')
        images.append(img)
        ax.axis('off')

    # Get the center of the image in x and y direction
    cx, cy = W // 2, H // 2

    # number of points for spline
    num_point = num_point

    # Function to create a circle of control points (used for epi and endo)
    def make_circle(radius):
        angles = np.linspace(0, 2 * np.pi, num_point, endpoint=False)
        return np.array([[cx + radius * np.cos(a), cy + radius * np.sin(a)] for a in angles])

    # If using MAT splines, load the control points from the MAT file, otherwise create them:
    if use_mat_splines==False:  # Create control points
        control_points_per_frame = {
            f: {
                'epi': make_circle(10),     # Outer circle radius (epi)
                'endo': make_circle(7)      # Inner circle radius (endo)
            } for f in range(num_frames)
        }
    else:  # Load control points from the MAT file
        control_points_per_frame=control_points_per_frame

    ############################## 

    current_frame = initial_frame  # Set the initial frame for the GUI first plot
    control_points = control_points_per_frame[current_frame]

    colors = {
        'epi': ('red', 'yellow'),
        'endo': ('blue', 'yellow'),
    }

    circles = {curve: [[None for _ in axs] for _ in range(num_point)] for curve in control_points}              # Draggable points on the curves
    lines = {curve: [ax.plot([], [], colors[curve][0], lw=2)[0] for ax in axs] for curve in control_points}     # Spline lines

    selected = None 

    # Global dictionary to store the final mask
    final_mask_per_frame = {}

    # Update the mask segmentation each time the curves are updated
    def update_mask_segmentation():
        # Construct the smooth outer contour (epi)
        x, y = control_points['epi'][:, 0], control_points['epi'][:, 1]
        x = np.r_[x, x[0]]                                      # Close the line by repeating the first point
        y = np.r_[y, y[0]]                                      # Close the line by repeating the first point
        tck, _ = splprep([x, y], s=0, per=True)                 # Spline representation
        outer_x, outer_y = splev(np.linspace(0, 1, 200), tck)   # 200 points for smoothness
        outer_poly = np.column_stack((outer_x, outer_y))        # Convert to 2D array
        
        # Construct the smooth inner contour (endo)
        x, y = control_points['endo'][:, 0], control_points['endo'][:, 1]
        x = np.r_[x, x[0]]
        y = np.r_[y, y[0]]
        tck, _ = splprep([x, y], s=0, per=True)
        inner_x, inner_y = splev(np.linspace(0, 1, 200), tck)
        inner_poly = np.column_stack((inner_x, inner_y))
        
        # Create Path objects for both contours.
        outer_path = mpath.Path(outer_poly)
        inner_path = mpath.Path(inner_poly)
        
        # Create grid of pixel centers.
        y_grid, x_grid = np.meshgrid(np.arange(H), np.arange(W), indexing='ij')     
        points = np.column_stack((x_grid.ravel(), y_grid.ravel()))
        
        # Build two masks:
        # True for pixels inside epi; True for pixels inside endo.
        epi_mask = outer_path.contains_points(points).reshape(H, W)
        endo_mask = inner_path.contains_points(points).reshape(H, W)
        
        # Build segmentation as a 3-class map:
        seg = np.zeros((H, W), dtype=np.uint8)  # 0: background
        seg[epi_mask] = 1                       # 1: Myocardium
        seg[epi_mask & endo_mask] = 2           # 2: Cavity

         # Store the mask for the current frame
        final_mask_per_frame[current_frame] = seg
        
        # Create an extent to match your image display.
        extent = [-0.5, W - 0.5, H - 0.5, -0.5]     # Considering the Height and width as (80*80) as example, because voxels are visualized (center of the voxels) from 0 to 79, the plotting lim range is -0.5 to 79.5
                                                    # The reason for y-axis to be inverted is that in matplotlib, when you display images, the coordinate
                                                    # system has its origin in the top-left corner (for images).
        
        # Define a custom colormap: 
        cmap = ListedColormap([[0, 0, 0, 0],    # 0: background (black)
                           [0, 1, 0, 0.5],      # 1: myocardium (green)
                           [0, 0, 1, 0.5]])     # 2: cavity (blue)
    
        extent = [-0.5, W - 0.5, H - 0.5, -0.5]
        for ax in [axs[1], axs[2]]:
            if hasattr(ax, "mask_im"):          # Check if the mask image already exists (As the mask doesnt exist in the first place)
                ax.mask_im.set_data(seg)
            else:
                ax.mask_im = ax.imshow(seg, cmap=cmap,
                                    interpolation='none', extent=extent)


    # Update the curve each time the points are moved
    def update_curves(): 
        for curve, pts in control_points.items():
            x, y = pts[:, 0], pts[:, 1]
            x = np.r_[x, x[0]]
            y = np.r_[y, y[0]]
            tck, _ = splprep([x, y], s=0, per=True)
            x_new, y_new = splev(np.linspace(0, 1, 200), tck)
            for i, ax in enumerate(axs):
                # For the third plot (index 2), hide the spline line and circle markers
                if i == 2:
                    lines[curve][i].set_visible(False)
                    for j in range(num_point):
                        circles[curve][j][i].set_visible(False)
                else:
                    lines[curve][i].set_data(x_new, y_new)
                    lines[curve][i].set_visible(True)
                    for j in range(num_point):
                        circles[curve][j][i].center = pts[j]
                        circles[curve][j][i].set_visible(True)
        fig.canvas.draw_idle()
        update_mask_segmentation()

    # Update the images as the frame changes (e.g. when panning, zooming, etc.)
    def update_images():    
        for i in range(6):
            images[i].set_data(image_arrays[i][:, :, current_frame])
        title_text.set_text(f"Frame: {current_frame + 1}/{num_frames}")
        fig.canvas.draw_idle()

    def load_frame(f):
        nonlocal control_points
        control_points = control_points_per_frame[f]
        update_curves()
        update_images()

    # Initialize panning support variables
    panning = False
    pan_start = None
    orig_limits = {}  # store original limits for each axis at pan start

    # Smoothing parameters (reset on pan start) - As during panning and dragging, the points jerk a lot,there is a need to smooth the movement
    last_dx = 0
    last_dy = 0
    smooth_factor = 0.5  # Control the smoothing level
    movement_counter = 0  # Counter to track the number of movements

    # Add an undo stack for each frame
    undo_stack_per_frame = {}  # key: frame index, value: list of control state copies

    def get_undo_stack():
        nonlocal current_frame
        if current_frame not in undo_stack_per_frame:
            undo_stack_per_frame[current_frame] = []
        return undo_stack_per_frame[current_frame]

    # Variables for curve dragging
    curve_dragging = False 
    selected_curve_drag = None   
    curve_drag_start = None
    curve_points_orig = None  # Stores a copy of control_points for translation

    # Compute the distance from a point to contour
    def point_to_segment_distance(px, py, x1, y1, x2, y2):
        """
        Computes the minimum distance from a point (px, py) to a line segment defined by (x1, y1) and (x2, y2).

        This function determines the closest point on a segment (e.g., Epi and Endo curves) to a given point 
        and calculates the Euclidean distance between the two. It is primarily used to detect if a user's 
        click is near a curve, rather than directly on the main control points of the curve.

        The main purpose of this function is to enable interaction by detecting if a user's click is close 
        enough to a curve, as used in the `on_press` event handler for DRAGGING.
        """
        # Compute projection factor t of point onto segment
        dx = x2 - x1
        dy = y2 - y1
        if dx == 0 and dy == 0:
            return np.hypot(px - x1, py - y1)
        t = ((px - x1) * dx + (py - y1) * dy) / (dx*dx + dy*dy)
        t = max(0, min(1, t))
        proj_x = x1 + t * dx
        proj_y = y1 + t * dy
        return np.hypot(px - proj_x, py - proj_y)   # Euclidean distance from point to projection

    # On press event handler
    def on_press(event):
        nonlocal selected, panning, pan_start, orig_limits, movement_counter, last_dx, last_dy, curve_dragging, selected_curve_drag, curve_drag_start, curve_points_orig

        # Perform panning if right mouse button is pressed
        if event.button == 3 and event.inaxes is not None: # Right click for panning
            panning = True
            pan_start = (event.xdata, event.ydata)
            # Reset smoothing counters on pan start
            movement_counter = 0
            last_dx = 0
            last_dy = 0
            for ax in axs:
                orig_limits[ax] = (ax.get_xlim(), ax.get_ylim())
            return

        # If left-click with shift held, full curve dragging
        if event.button == 1 and event.inaxes is not None \
           and event.key is not None and 'shift' in event.key.lower():
            tolerance = 1  
            found = None
            
            # Use the approximated spline points stored in lines data.
            for curve in ['epi', 'endo']:
                # Get control points, form a closed polygon
                pts = control_points[curve]
                poly = np.vstack((pts, pts[0]))
                # Check each segment distance
                dists = []
                for i in range(len(poly)-1):
                    d = point_to_segment_distance(event.xdata, event.ydata, poly[i,0], poly[i,1], poly[i+1,0], poly[i+1,1])
                    dists.append(d)
                if min(dists) < tolerance:
                    found = curve
                    break
            if found is not None:
                # Save status for undo before starting the dragging
                stack = get_undo_stack()
                stack.append(copy.deepcopy(control_points))
                curve_dragging = True
                selected_curve_drag = found
                curve_drag_start = (event.xdata, event.ydata)
                if found == 'epi':
                    curve_points_orig = copy.deepcopy(control_points)
                else:
                    curve_points_orig = {'endo': copy.deepcopy(control_points['endo'])}
                return

        # Check if a control point is selected for dragging
        for ax_idx, ax in enumerate(axs):
            if event.inaxes == ax:
                for curve in ['epi', 'endo']:
                    for i in range(num_point):
                        circ = circles[curve][i][ax_idx]
                        contains, _ = circ.contains(event)
                        if contains:
                            
                            stack = get_undo_stack()  # This function returns the stack for current_frame.
                            if selected is None:
                                stack.append(copy.deepcopy(control_points))
                            selected = (curve, i)
                            return

    # Motion event handler
    def on_motion(event):
        nonlocal panning, pan_start, last_dx, last_dy, movement_counter, orig_limits, curve_dragging, curve_drag_start, selected, control_points, axs, fig

        # Panning logic
        if panning:
            if event.xdata is None or event.ydata is None:
                return
            dx = event.xdata - pan_start[0]
            dy = event.ydata - pan_start[1]

            threshold = 0.5
            if abs(dx) < threshold and abs(dy) < threshold:
                return

            movement_counter += 1

            # skip smoothing for the first few movements to avoid initial lag and sudden jumps
            dx = smooth_factor * dx + (1 - smooth_factor) * last_dx
            dy = smooth_factor * dy + (1 - smooth_factor) * last_dy

            for ax in axs: # Force the 0.5 pixel limit during panning
                (xlim, ylim) = orig_limits.get(ax, (ax.get_xlim(), ax.get_ylim()))
                new_xlim = (xlim[0] - dx, xlim[1] - dx)
                new_ylim = (ylim[0] - dy, ylim[1] - dy)

                view_width = xlim[1] - xlim[0]
                new_xlim = (max(new_xlim[0], -0.5), max(new_xlim[0], -0.5) + view_width)
                if new_xlim[1] > W - 0.5:
                    new_xlim = (W - 0.5 - view_width, W - 0.5)

                view_height = ylim[0] - ylim[1]
                new_ylim = (min(new_ylim[0], H - 0.5), min(new_ylim[0], H - 0.5) - view_height)
                if new_ylim[1] < -0.5:
                    new_ylim = (new_ylim[1] + view_height, -0.5)

                ax.set_xlim(new_xlim)
                ax.set_ylim(new_ylim)
            fig.canvas.draw_idle()

            last_dx = dx
            last_dy = dy
            return

        # Curve dragging logic
        if curve_dragging:
            if event.xdata is None or event.ydata is None:
                return
            dx = event.xdata - curve_drag_start[0]
            dy = event.ydata - curve_drag_start[1]
            if selected_curve_drag == 'epi':
                control_points['epi'] = curve_points_orig['epi'] + np.array([dx, dy])
                control_points['endo'] = curve_points_orig['endo'] + np.array([dx, dy])
            else:
                control_points['endo'] = curve_points_orig['endo'] + np.array([dx, dy])
            update_curves()
            return

        # Control point dragging logic
        if selected is None or event.inaxes is None:
            return
        curve, idx = selected
        control_points[curve][idx] = [event.xdata, event.ydata]
        update_curves()

    # Modified on_release event handler
    def on_release(event):
        nonlocal selected, panning, pan_start, orig_limits, curve_dragging, selected_curve_drag, curve_drag_start, curve_points_orig
        selected = None
        if panning:
            panning = False
            pan_start = None
            orig_limits = {}
        if curve_dragging:
            curve_dragging = False
            selected_curve_drag = None
            curve_drag_start = None
            curve_points_orig = None

    def on_key(event):
        nonlocal control_points, current_frame
        if event.key == 'enter':
            plt.close(fig)
        elif event.key == 'left':  # Previous frame
            prev_frame(event)
        elif event.key == 'right':  # Next frame
            next_frame(event)
        # Check for undo (ctrl+z). Adjust the key string if necessary.
        elif event.key.lower() in ['ctrl+z', 'control+z']:
            stack = get_undo_stack()
            if stack:
                # Restore the last undo state
                control_points = stack.pop()
                # Update the dictionary that holds the frame's control points as well
                control_points_per_frame[current_frame] = control_points
                update_curves()

    def next_frame(event):
        nonlocal current_frame
        if current_frame < num_frames - 1:
            current_frame += 1
            load_frame(current_frame)

    def prev_frame(event):
        nonlocal current_frame
        if current_frame > 0:
            current_frame -= 1
            load_frame(current_frame)

    def copy_from_prev(event):
        nonlocal control_points
        if current_frame > 0:
            source = control_points_per_frame[current_frame - 1]
            control_points_per_frame[current_frame] = {
                'epi': copy.deepcopy(source['epi']),
                'endo': copy.deepcopy(source['endo']),
            }
            control_points = control_points_per_frame[current_frame]
            update_curves()

    def copy_from_next(event):
        nonlocal control_points
        if current_frame < num_frames - 1:
            source = control_points_per_frame[current_frame + 1]
            control_points_per_frame[current_frame] = {
                'epi': copy.deepcopy(source['epi']),
                'endo': copy.deepcopy(source['endo']),
            }
            control_points = control_points_per_frame[current_frame]
            update_curves()

    def zoom(event, zoom_factor=1.1):
        # Get the original axis limits before zooming
        x_min, x_max = axs[0].get_xlim()
        y_min, y_max = axs[0].get_ylim()

        
        # Get the cursor position relative to the image (used as zoom center)
        cursor_x = event.xdata
        cursor_y = event.ydata

        # Original image size (using the first frame size as a reference)
        original_width = W
        original_height = H


        # Calculate new region size based on cursor position
        if event.button == 'up':  # Zoom In (3/4 of previous region size)
            zoom_factor_in = 3 / 4
        elif event.button == 'down':  # Zoom Out (4/3 of previous region size)
            zoom_factor_in = 4 / 3

        # Calculate new width and height based on zoom factor
        width_temp = (x_max - x_min) * zoom_factor_in
        height_temp = (y_max - y_min) * zoom_factor_in

        # Calculate new zoom center based on cursor position
        x_center = cursor_x
        y_center = cursor_y

        # Ensure that the zoom region doesn't go out of the image bounds
        half_width = width_temp / 2
        half_height = height_temp / 2

        # Clip the center of the zoom region to prevent it from going out of bounds
        x_center = np.clip(x_center, half_width, original_width - half_width)
        y_center = np.clip(y_center, half_height, original_height - half_height)

        # Calculate the new limits while making sure they stay inside the image bounds
        new_x_min = x_center - half_width
        new_x_max = x_center + half_width
        new_y_min = y_center - half_height
        new_y_max = y_center + half_height

        # Force min and max to be within orignial image size
        if not 0 <= new_x_min <= original_width:
            new_x_min_temp = np.clip(new_x_min, 0, original_width)

            diff_x = new_x_min_temp - new_x_min

            new_x_min = new_x_min_temp

            new_x_max = new_x_max + diff_x
            new_x_max = np.clip(new_x_max, 0, original_width)
            
        
        if not 0 <= new_x_max <= original_width:
            new_x_max_temp = np.clip(new_x_max, 0, original_width)

            diff_x = new_x_max_temp - new_x_max

            new_x_max = new_x_max_temp

            new_x_min = new_x_min + diff_x
            new_x_min = np.clip(new_x_min, 0, original_width)
            

        
        if not 0 <= new_y_min <= original_height:
            new_y_min_temp = np.clip(new_y_min, 0, original_height)

            diff_y = new_y_min_temp - new_y_min

            new_y_min = new_y_min_temp

            new_y_max_temp = new_y_max + diff_y
            new_y_max = np.clip(new_y_max_temp, 0, original_height)
            
        
        if not 0 <= new_y_max <= original_height:
            new_y_max_temp = np.clip(new_y_max, 0, original_height)

            diff_y = new_y_max_temp - new_y_max

            new_y_max = new_y_max_temp

            new_y_min_temp = new_y_min + diff_y
            new_y_min = np.clip(new_y_min_temp, 0, original_height)


        new_x_min -= 0.5
        new_x_max -= 0.5
        new_y_min -= 0.5
        new_y_max -= 0.5
        
        # Update axis limits based on the new zoom center and region size
        for ax in axs:
            ax.set_xlim(new_x_min, new_x_max)
            ax.set_ylim(new_y_min, new_y_max) # In matplotlib, when you display images, the coordinate 


        fig.canvas.draw_idle()

    def reset_zoom(event):
        for ax in axs:
            ax.set_xlim(0 - 0.5, W - 0.5)
            ax.set_ylim(H - 0.5, 0 - 0.5) # Invert Y-axis for image display
        fig.canvas.draw_idle()

    for curve in ['epi', 'endo']:
        for pt_idx in range(num_point):
            for ax_idx, ax in enumerate(axs):
                circ = Circle(control_points[curve][pt_idx], radius=1,
                              color=colors[curve][1], picker=True)
                ax.add_patch(circ)
                circles[curve][pt_idx][ax_idx] = circ
    
    
    ################### Saving block
    def images_to_nifti(images, output_nifti_path):
        # check if if the path exists, if not create the directory
        if not os.path.exists(os.path.dirname(output_nifti_path)):
            os.makedirs(os.path.dirname(output_nifti_path))
        # Save the images as a NIfTI file
        nifti_image = nib.Nifti1Image(images, affine=np.eye(4))
        nib.save(nifti_image, output_nifti_path)

    def on_save(event):
        # Use the original image dimensions and number of frames from mag.
        H, W, num_frames = mag.shape

        # Stack the final masks from final_mask_per_frame into a 3D array.
        mask_stack = np.zeros((H, W, num_frames), dtype=np.uint8)
        for f in range(num_frames):
            if f in final_mask_per_frame:
                mask_stack[..., f] = final_mask_per_frame[f]
            else:
                mask_stack[..., f] = np.zeros((H, W), dtype=np.uint8)

        mag_nifti_path     = nifti_path["mag_nifti_path"]
        phase_x_nifti_path = nifti_path["phase_x_nifti_path"]
        phase_y_nifti_path = nifti_path["phase_y_nifti_path"]
        phase_z_nifti_path = nifti_path["phase_z_nifti_path"]
        mask_nifti_path    = nifti_path["mask_nifti_path"]

        images_to_nifti(mag, mag_nifti_path)
        images_to_nifti(phase_x, phase_x_nifti_path)
        images_to_nifti(phase_y, phase_y_nifti_path)
        images_to_nifti(phase_z, phase_z_nifti_path)
        images_to_nifti(mask_stack, mask_nifti_path)

        print("NIfTI files saved successfully.")
    
    
    ################### GUI Interface Block
    fig.canvas.mpl_connect('button_press_event', on_press)
    fig.canvas.mpl_connect('motion_notify_event', on_motion)
    fig.canvas.mpl_connect('button_release_event', on_release)
    fig.canvas.mpl_connect('key_press_event', on_key)

    # Navigation + copy buttons
    ax_prev = fig.add_axes([0.77, 0.25, 0.08, 0.08])   # x, y, width, height
    ax_next = fig.add_axes([0.87, 0.25, 0.08, 0.08])
    btn_prev = Button(ax_prev, '<< Prev', color='skyblue', hovercolor='cornflowerblue')
    btn_next = Button(ax_next, 'Next >>', color='skyblue', hovercolor='cornflowerblue')
    btn_prev.on_clicked(prev_frame)
    btn_next.on_clicked(next_frame)

    ax_copy_prev = fig.add_axes([0.77, 0.15, 0.08, 0.08])
    ax_copy_next = fig.add_axes([0.87, 0.15, 0.08, 0.08])
    btn_copy_prev = Button(ax_copy_prev, f'Copy from \n<< Prev Frame', color='lightgreen', hovercolor='mediumseagreen')
    btn_copy_next = Button(ax_copy_next, f'Copy from \n>> Next Frame', color='lightgreen', hovercolor='mediumseagreen')
    btn_copy_prev.on_clicked(copy_from_prev)
    btn_copy_next.on_clicked(copy_from_next)

    # Bind mouse scroll event for zoom
    fig.canvas.mpl_connect('scroll_event', zoom)

    # Reset Zoom button
    ax_reset_zoom = fig.add_axes([0.77, 0.05, 0.18, 0.08])
    btn_reset_zoom = Button(ax_reset_zoom, 'Reset Zoom', color='plum', hovercolor='orchid')
    btn_reset_zoom.on_clicked(reset_zoom)

    # Save Button
    ax_save = fig.add_axes([0.77, 0.35, 0.18, 0.08])
    btn_save = Button(ax_save, "Save Results", color="lightgray", hovercolor="gray")
    btn_save.on_clicked(on_save)

    # Add header table display in the top right
    ax_header = fig.add_axes([0.77, 0.64, 0.18, 0.3])
    ax_header.axis("off")

    # Convert headers dictionary to a list of rows: [[key, value], ...]
    table_data = [[str(key), str(value)] for key, value in headers.items()]

    # Create the table in the axes
    header_table = ax_header.table(cellText=table_data,
                                colLabels=["Header", "Value"],
                                loc='center',
                                cellLoc='center')
    header_table.auto_set_font_size(False)
    header_table.set_fontsize(12)

    # Iterate over the cells to apply alternating row colors
    # Skip the header row (row 0). Use white for even, gold for odd rows.
    for (row, col), cell in header_table.get_celld().items():
        if row == 0:
            cell.set_text_props(weight='bold', color='white')
            cell.set_facecolor('black')
        else:
            if (row - 1) % 2 == 0:
                cell.set_facecolor("white")
                if col==0:
                    cell.set_text_props(weight='bold')
            else:
                cell.set_facecolor("gold")
                if col==0:
                    cell.set_text_props(weight='bold')

    update_curves()
    update_images()

    plt.show()

    return control_points_per_frame

