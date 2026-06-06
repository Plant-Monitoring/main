import numpy as np
import matplotlib.image as mpimg

def _load_rgb(img_path):
    """Read an image as float RGB in [0, 1]."""
    raw = mpimg.imread(img_path)
    img = np.float32(raw)
    if img.max() > 1.0:           # JPEG/uint8 comes in as 0..255
        img /= 255.0
    if img.ndim == 2:             # grayscale -> rgb
        img = np.stack([img] * 3, axis=-1)
    if img.ndim == 3 and img.shape[2] == 4:   # drop alpha
        img = img[:, :, :3]
    return img

# Model 1: colour / HSV
def measure_plant_height_color(img_path, pot_height_cm=9.0):
    img = _load_rgb(img_path)
    H, W = img.shape[:2]
    R, G, B = img[:, :, 0], img[:, :, 1], img[:, :, 2]

    V = np.max(img, axis=2)
    S = np.where(V > 0, (V - np.min(img, axis=2)) / V, 0)

    # Green pixels = plant
    green_mask = (G > R * 1.05) & (G > B * 1.05) & (V > 0.08) & (S > 0.10)
    # Pot = low saturation (gray/brown), not too bright
    pot_mask = (S < 0.12) & (V > 0.20) & (V < 0.65)

    kernel     = np.ones(11) / 11
    green_rows = np.convolve(green_mask.sum(axis=1).astype(float), kernel, mode="same")
    pot_rows   = np.convolve(pot_mask.sum(axis=1).astype(float),   kernel, mode="same")

    # Pot rim = first strong pot peak in the middle vertical band
    mid_start = int(H * 0.30)
    mid_end   = int(H * 0.75)
    pot_mid   = pot_rows[mid_start:mid_end]
    if pot_mid.size == 0 or pot_mid.max() == 0:
        raise ValueError("Could not detect the pot rim.")

    rim_threshold  = pot_mid.max() * 0.25
    rim_candidates = np.where(pot_mid > rim_threshold)[0]
    if len(rim_candidates) == 0:
        raise ValueError("Could not detect the pot rim.")
    pot_top_row = int(rim_candidates[0]) + mid_start

    # Pot bottom = where pot pixels drop and stay low
    window      = max(5, int(H * 0.02))
    drop_thresh = pot_rows[pot_top_row:pot_top_row + 50].mean() * 0.25
    pot_bottom_row = pot_top_row + int(H * 0.25)   # fallback
    for r in range(pot_top_row + int(H * 0.05), min(pot_top_row + int(H * 0.40), H - window)):
        if np.mean(pot_rows[r:r + window]) < drop_thresh:
            pot_bottom_row = r
            break

    pot_px = pot_bottom_row - pot_top_row
    if pot_px < 10:
        raise ValueError("Detected pot is too small to measure.")
    pixels_per_cm = pot_px / pot_height_cm

    # Plant top = topmost green row above the pot
    green_above = green_rows[:pot_top_row]
    if green_above.size == 0 or green_above.max() == 0:
        raise ValueError("Could not detect the plant.")
    green_thresh = green_above.max() * 0.15
    green_active = np.where(green_above > green_thresh)[0]
    plant_top_row = int(green_active[0]) if len(green_active) > 0 else 0

    plant_px        = pot_top_row - plant_top_row
    plant_height_cm = plant_px / pixels_per_cm if plant_px > 0 else 0.0
    return float(plant_height_cm)

# Model 2: edge / Sobel
def measure_plant_height_edge(img_path, pot_height_cm=9.0):
    try:
        import scipy.ndimage as ndimage
    except ImportError:
        raise ValueError("This model needs scipy.  Run:  pip install scipy")

    slika = _load_rgb(img_path)
    slika = slika.transpose(1, 0, 2)
    filt  = slika.mean(2)
    filt2 = slika.mean(2)

    Sobel  = np.array([[1, 2, 1],
                       [0, 0, 0],
                       [-1, -2, -1]])
    Sobelv = Sobel.T

    filt = ndimage.convolve(filt, Sobelv)
    filt = filt > 0.3

    vertical = filt.sum(axis=1).astype(np.int64)

    region = vertical[:2000] if vertical.shape[0] >= 2000 else vertical
    zeroes = np.where(region == 0)[0]
    if zeroes.size == 0:
        raise ValueError("Could not detect the pot region (edge model).")
    first  = int(zeroes[-1])

    second = -1
    for i in range(first + 1, vertical.shape[0]):
        if vertical[i] == 0:
            second = i
            break
    if second == -1:
        raise ValueError("Could not detect the pot region (edge model).")

    filt     = filt[first:second]
    vertical = vertical[first:second]
    for i in range(vertical.shape[0] // 2, vertical.shape[0]):
        if vertical[i] // 10 == 0:
            second = i
            break
    filt = filt[:second]

    Gx = ndimage.convolve(filt2, Sobelv)
    Gy = ndimage.convolve(filt2, Sobel)
    G  = np.sqrt(Gx ** 2 + Gy ** 2)
    G  = G > 0.3

    mid  = G.shape[1] // 2
    G    = G[second + first:]
    line = G[:, mid]

    z = np.where(line == 1)[0]
    if z.size < 2:
        raise ValueError("Could not detect the pot base (edge model).")
    diffs = np.diff(z)
    ind   = int(np.where(diffs == diffs.max())[0][0])
    last  = int(z[ind + 1])
    if last <= 0:
        raise ValueError("Could not measure the pot (edge model).")

    pixl_cm_rat  = pot_height_cm / last
    plant_height = filt.shape[0] * pixl_cm_rat
    return float(plant_height)