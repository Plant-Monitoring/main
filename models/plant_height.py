import numpy as np

def _load_rgb(img_path):
    """Read an image as float RGB in [0, 1] using Pillow (robust for PNG/JPG/...)."""
    try:
        from PIL import Image
    except ImportError:
        raise ValueError("This needs Pillow.  Run:  pip install pillow")
    try:
        with Image.open(img_path) as im:
            im = im.convert("RGB")
            img = np.asarray(im, dtype=np.float32) / 255.0
    except Exception as ex:
        raise ValueError(f"Could not read the image: {ex}")
    return img

# Model 1: colour / HSV
def measure_plant_height_color(img_path, pot_height_cm=9.0):
    img = _load_rgb(img_path)
    H, W = img.shape[:2]
    R, G, B = img[:, :, 0], img[:, :, 1], img[:, :, 2]

    V = np.max(img, axis=2)
    S = np.where(V > 0, (V - np.min(img, axis=2)) / V, 0)

    green_mask = (G > R * 1.05) & (G > B * 1.05) & (V > 0.08) & (S > 0.10)
    pot_mask   = (S < 0.12) & (V > 0.20) & (V < 0.65)

    kernel     = np.ones(11) / 11
    green_rows = np.convolve(green_mask.sum(axis=1).astype(float), kernel, mode="same")
    pot_rows   = np.convolve(pot_mask.sum(axis=1).astype(float),   kernel, mode="same")

    mid_start = int(H * 0.30)
    mid_end   = int(H * 0.92)
    pot_mid   = pot_rows[mid_start:mid_end]
    if pot_mid.size == 0 or pot_mid.max() == 0:
        # Fallback: locate the pot from the green plant instead. Assume the pot
        # sits just below the lowest strong green row and spans ~22% of height.
        if green_rows.max() == 0:
            raise ValueError("Could not detect the pot or the plant.")
        green_active_all = np.where(green_rows > green_rows.max() * 0.15)[0]
        pot_top_row = int(green_active_all[-1]) if green_active_all.size else int(H * 0.6)
        pot_bottom_row = min(pot_top_row + int(H * 0.22), H - 1)
    else:
        rim_threshold  = pot_mid.max() * 0.25
        rim_candidates = np.where(pot_mid > rim_threshold)[0]
        pot_top_row = int(rim_candidates[0]) + mid_start

        window      = max(5, int(H * 0.02))
        drop_thresh = pot_rows[pot_top_row:pot_top_row + 50].mean() * 0.25
        pot_bottom_row = pot_top_row + int(H * 0.25)
        for r in range(pot_top_row + int(H * 0.05), min(pot_top_row + int(H * 0.40), H - window)):
            if np.mean(pot_rows[r:r + window]) < drop_thresh:
                pot_bottom_row = r
                break

    pot_px = pot_bottom_row - pot_top_row
    if pot_px < 8:
        pot_bottom_row = min(pot_top_row + int(H * 0.20), H - 1)
        pot_px = pot_bottom_row - pot_top_row
    if pot_px < 8:
        raise ValueError("Detected pot is too small to measure.")
    pixels_per_cm = pot_px / pot_height_cm

    green_above = green_rows[:pot_top_row]
    if green_above.size == 0 or green_above.max() == 0:
        raise ValueError("Could not detect the plant.")
    green_thresh = green_above.max() * 0.15
    green_active = np.where(green_above > green_thresh)[0]
    plant_top_row = int(green_active[0]) if len(green_active) > 0 else 0

    plant_px        = pot_top_row - plant_top_row
    plant_height_cm = plant_px / pixels_per_cm if plant_px > 0 else 0.0

    return {
        "height_cm":   float(plant_height_cm),
        "image":       img,
        "orientation": "horizontal",
        "lines": [
            (plant_top_row,  "cyan",   "Plant top"),
            (pot_top_row,    "lime",   "Pot top"),
            (pot_bottom_row, "orange", "Pot base"),
        ],
        "span": (plant_top_row, pot_top_row),
    }

# Model 2: edge / Sobel (robust, row-profile)
def measure_plant_height_edge(img_path, pot_height_cm=9.0):
    """Sobel-edge height estimate.

    Uses edge-density profiles per row (with relative thresholds and fallbacks)
    so it returns a result on the same photos the colour model handles, instead
    of requiring a perfect band of zero-edge rows like the original script.
    """
    try:
        import scipy.ndimage as ndimage
    except ImportError:
        raise ValueError("This model needs scipy.  Run:  pip install scipy")

    img = _load_rgb(img_path)
    H, W = img.shape[:2]
    gray = ndimage.gaussian_filter(img.mean(2), 1.0)

    Sobel  = np.array([[1.0, 2.0, 1.0],
                       [0.0, 0.0, 0.0],
                       [-1.0, -2.0, -1.0]])
    Gy = ndimage.convolve(gray, Sobel)        # horizontal edges (pot rim / base)
    Gx = ndimage.convolve(gray, Sobel.T)      # vertical edges
    mag = np.sqrt(Gx ** 2 + Gy ** 2)

    # Relative threshold so it adapts to each image's contrast.
    thr = mag.mean() + mag.std()
    edge_mask = mag > thr
    if not edge_mask.any():
        raise ValueError("No clear edges detected in the image (edge model).")

    k = max(5, int(H * 0.01))
    kernel     = np.ones(k) / k
    edge_rows  = np.convolve(edge_mask.sum(axis=1).astype(float), kernel, mode="same")
    hedge_rows = np.convolve(np.abs(Gy).sum(axis=1),            kernel, mode="same")

    # Pot rim: strongest horizontal-edge row in the lower-middle band.
    lo, hi = int(H * 0.35), int(H * 0.92)
    band = hedge_rows[lo:hi]
    if band.size == 0 or band.max() == 0:
        raise ValueError("Could not detect the pot (edge model).")
    pot_top_row = int(np.argmax(band)) + lo

    # Pot base: strongest horizontal-edge row below the rim (fallback: fixed offset).
    start = pot_top_row + int(H * 0.03)
    below = hedge_rows[start:]
    if below.size > 0 and below.max() > 0:
        pot_bottom_row = int(np.argmax(below)) + start
    else:
        pot_bottom_row = min(pot_top_row + int(H * 0.25), H - 1)
    if pot_bottom_row - pot_top_row < max(8, int(H * 0.04)):
        pot_bottom_row = min(pot_top_row + int(H * 0.20), H - 1)

    pot_px = pot_bottom_row - pot_top_row
    if pot_px < 8:
        raise ValueError("Detected pot is too small (edge model).")
    pixels_per_cm = pot_px / pot_height_cm

    # Plant top: first row from the top with notable edge density (foliage).
    above = edge_rows[:pot_top_row]
    if above.size == 0 or above.max() == 0:
        raise ValueError("Could not detect the plant (edge model).")
    active = np.where(above > above.max() * 0.12)[0]
    plant_top_row = int(active[0]) if active.size else 0

    plant_px        = pot_top_row - plant_top_row
    plant_height_cm = plant_px / pixels_per_cm if plant_px > 0 else 0.0

    return {
        "height_cm":   float(plant_height_cm),
        "image":       img,
        "orientation": "horizontal",
        "lines": [
            (plant_top_row,  "cyan",   "Plant top"),
            (pot_top_row,    "lime",   "Pot top"),
            (pot_bottom_row, "orange", "Pot base"),
        ],
        "span": (plant_top_row, pot_top_row),
    }