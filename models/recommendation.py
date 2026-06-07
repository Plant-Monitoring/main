"""
Plant recommendation engine with fuzzy matching and optional
light/temperature data import from .bin / .npz files.
"""

import numpy as np
import os
from database.plants import df_plants

# ----------------------------------------------------------------------
#  Original fuzzy‑matching helpers
# ----------------------------------------------------------------------
def _triangular_membership(x, center, spread):
    if spread <= 0:
        return 1.0 if x == center else 0.0
    return max(0.0, 1.0 - abs(x - center) / spread)

def _fuzzy_match(user_val, plant_val, spread):
    return _triangular_membership(plant_val, user_val, spread)

# ----------------------------------------------------------------------
#  Public recommendation function
# ----------------------------------------------------------------------
def recommend_plants(user_prefs, top_n=5):
    """
    Return a list of (plant_name, score) tuples sorted by score.
    user_prefs is a dict that may contain:
        water, sunlight, temp, pet_safe, space,
        allergy_concern, existing_plants
    """
    if df_plants is None:
        return []

    scores = []
    for _, plant in df_plants.iterrows():
        w_match = _fuzzy_match(user_prefs["water"], plant["water"], 2.0)
        s_match = _fuzzy_match(user_prefs["sunlight"], plant["sunlight"], 2.0)
        t_match = _fuzzy_match(user_prefs["temp"], plant["temperature"], 4.0)

        p_match = (1.0 if plant["pet_safe"] == user_prefs["pet_safe"] else 0.0) \
                  if user_prefs.get("pet_safe") is not None else None

        space_match = (1.0 if plant["space"] == user_prefs["space"] else 0.0) \
                      if user_prefs.get("space") is not None else None

        if user_prefs.get("allergy_concern") is not None:
            a_match = (1.0 if not plant["pollen_allergies"] else 0.0) \
                      if user_prefs["allergy_concern"] else 1.0
        else:
            a_match = None

        user_existing = user_prefs.get("existing_plants", [])
        if user_existing:
            plant_compat_list = plant["existing_plants"]
            exist_match = (sum(1 for up in user_existing if up in plant_compat_list) /
                           len(user_existing)) if plant_compat_list else 0.0
        else:
            exist_match = None

        weights = {
            "water": 0.15, "sunlight": 0.15, "temp": 0.15,
            "pet": 0.15, "space": 0.15, "allergy": 0.15, "existing": 0.10
        }
        components = {
            "water": w_match, "sunlight": s_match, "temp": t_match,
            "pet": p_match, "space": space_match, "allergy": a_match,
            "existing": exist_match
        }
        active = {k: v for k, v in components.items() if v is not None}
        if not active:
            continue

        active_weight_sum = sum(weights[k] for k in active)
        score = sum(v * weights[k] / active_weight_sum for k, v in active.items())
        scores.append((plant["name"], score))

    scores.sort(key=lambda x: x[1], reverse=True)
    return scores[:top_n]

# ----------------------------------------------------------------------
#  New helper: map lux readings to a sunlight score (1–10)
# ----------------------------------------------------------------------
def _lux_to_sunlight(lux):
    """
    Convert an average lux value into a plant‑care sunlight scale 1–10.
    Thresholds are loosely based on indoor light levels.
    """
    # Piecewise linear mapping:
    thresholds = [
        (0,     100,   1.0,  2.0),
        (100,   250,   2.0,  3.0),
        (250,   500,   3.0,  4.0),
        (500,   1000,  4.0,  5.0),
        (1000,  2000,  5.0,  6.0),
        (2000,  4000,  6.0,  7.0),
        (4000,  8000,  7.0,  8.0),
        (8000,  16000, 8.0,  9.0),
        (16000, 32000, 9.0,  10.0),
        (32000, float("inf"), 10.0, 10.0),
    ]
    for low, high, low_s, high_s in thresholds:
        if low <= lux <= high:
            if high == float("inf"):
                return low_s
            fraction = (lux - low) / (high - low)
            return low_s + fraction * (high_s - low_s)
    return 5.0   # fallback

# ----------------------------------------------------------------------
#  File‑analysis entry point
# ----------------------------------------------------------------------
def analyze_environment_file(file_path):
    """
    Read a .bin or .npz file that may contain light and/or temperature data.

    Returns a dict with:
        - "sunlight" : float (1‑10) derived from average light
        - "temp"     : float or None (average temperature in °C)
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    ext = os.path.splitext(file_path)[1].lower()
    light_values = []
    temp_values  = []

    try:
        if ext == ".npz":
            with np.load(file_path, allow_pickle=True) as npz:
                # Look for known keys
                for key in npz.files:
                    arr = npz[key].flatten()
                    if key.lower() in ("light", "lux", "illuminance"):
                        light_values.extend(arr.tolist())
                    elif key.lower() in ("temp", "temperature", "celsius"):
                        temp_values.extend(arr.tolist())
                # If no known keys, treat everything as light (back‑compat with dashboard)
                if not light_values and not temp_values:
                    for key in npz.files:
                        light_values.extend(npz[key].flatten().tolist())

        elif ext == ".bin":
            raw = np.fromfile(file_path, dtype=np.float32)
            light_values = raw.tolist()
        else:
            raise ValueError("Unsupported file type. Use .bin or .npz")

    except Exception as e:
        raise RuntimeError(f"Failed to read environment file: {e}")

    # Compute sunlight from light data
    sunlight = None
    if light_values:
        avg_lux = sum(light_values) / len(light_values)
        sunlight = _lux_to_sunlight(avg_lux)
    else:
        sunlight = 5.0   # neutral guess if no light data

    # Compute temperature if available
    temp = None
    if temp_values:
        avg_temp = sum(temp_values) / len(temp_values)
        temp = round(avg_temp, 1)

    return {"sunlight": sunlight, "temp": temp}

# ----------------------------------------------------------------------
#  Convenience function that merges file‑derived values into prefs
# ----------------------------------------------------------------------
def merge_file_prefs(user_prefs, file_path):
    """
    Return a new user_prefs dict where 'sunlight' and 'temp' are
    replaced with values from the file, if available.
    Other keys are left untouched.
    """
    env = analyze_environment_file(file_path)
    merged = dict(user_prefs)  # shallow copy
    merged["sunlight"] = env["sunlight"]
    if env["temp"] is not None:
        merged["temp"] = env["temp"]
    # If no temperature was found, keep the original temp value
    return merged