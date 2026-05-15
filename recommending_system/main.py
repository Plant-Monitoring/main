import pandas as pd
import numpy as np

# -------------------------------
# 1. Load plant data
# -------------------------------
df_plants = pd.read_csv("plants.csv")
# Convert existing_plants from string to list
df_plants["existing_plants"] = df_plants["existing_plants"].apply(
    lambda x: [p.strip() for p in x.split(",") if p.strip()] if isinstance(x, str) else []
)

# -------------------------------
# 2. Fuzzy matching functions
# -------------------------------
def triangular_membership(x, center, spread):
    """Return membership degree (0-1) for a triangular fuzzy set."""
    if spread <= 0:
        return 1.0 if x == center else 0.0
    return max(0.0, 1.0 - abs(x - center) / spread)

def fuzzy_match(user_val, plant_val, spread):
    """Crisp user preference -> fuzzy set, evaluate plant's crisp value."""
    return triangular_membership(plant_val, user_val, spread)

# -------------------------------
# 3. Recommendation engine
# -------------------------------
def recommend_plants(user_prefs, top_n=5):
    """
    user_prefs: dict with keys:
        water (float), sunlight (float), temp (float),
        pet_safe (bool or None), space (str or None),
        allergy_concern (bool), existing_plants (list of str)
    """
    # Default spreads
    WATER_SPREAD = 2.0
    SUNLIGHT_SPREAD = 2.0
    TEMP_SPREAD = 4.0

    scores = []

    for _, plant in df_plants.iterrows():
        # --- Fuzzy matches for numeric attributes ---
        w_match = fuzzy_match(user_prefs["water"], plant["water"], WATER_SPREAD)
        s_match = fuzzy_match(user_prefs["sunlight"], plant["sunlight"], SUNLIGHT_SPREAD)
        t_match = fuzzy_match(user_prefs["temp"], plant["temperature"], TEMP_SPREAD)

        # --- Binary matches ---
        # pet_safe: if user cares (not None), 1 if plant matches, else 0
        if user_prefs["pet_safe"] is not None:
            p_match = 1.0 if plant["pet_safe"] == user_prefs["pet_safe"] else 0.0
        else:
            p_match = None  # will be ignored

        # space: if user specifies, must match exactly
        if user_prefs["space"] is not None:
            space_match = 1.0 if plant["space"] == user_prefs["space"] else 0.0
        else:
            space_match = None

        # allergy: user allergy_concern=True -> prefer plants with pollen_allergies=False
        if user_prefs["allergy_concern"] is not None:
            if user_prefs["allergy_concern"]:
                a_match = 1.0 if not plant["pollen_allergies"] else 0.0
            else:
                a_match = 1.0  # user doesn't care about allergies
        else:
            a_match = None

        # existing plants compatibility
        user_existing = user_prefs.get("existing_plants", [])
        if user_existing:
            plant_compat_list = plant["existing_plants"]
            if plant_compat_list:
                # fraction of user's plants that appear in plant's compatible list
                exist_match = sum(1 for up in user_existing if up in plant_compat_list) / len(user_existing)
            else:
                exist_match = 0.0
        else:
            exist_match = None

        # --- Combine with dynamic weighting ---
        # base weights (sum = 1.0)
        weights = {
            "water": 0.15, "sunlight": 0.15, "temp": 0.15,
            "pet": 0.15, "space": 0.15, "allergy": 0.15,
            "existing": 0.10
        }
        components = {
            "water": w_match,
            "sunlight": s_match,
            "temp": t_match,
            "pet": p_match,
            "space": space_match,
            "allergy": a_match,
            "existing": exist_match
        }

        # Remove None components and redistribute their weights
        active = {k: v for k, v in components.items() if v is not None}
        if not active:
            continue
        active_weight_sum = sum(weights[k] for k in active)
        score = sum(v * weights[k] / active_weight_sum for k, v in active.items())
        scores.append((plant["name"], score))

    # Sort descending by score
    scores.sort(key=lambda x: x[1], reverse=True)
    return scores[:top_n]

# -------------------------------
# 4. Example usage
# -------------------------------
if __name__ == "__main__":
    # Example user: wants medium water, bright indirect light, moderate temp,
    # pet-safe, flat, allergic, and already has a Pothos.
    user = {
        "water": 5.0,
        "sunlight": 6.0,
        "temp": 22.0,
        "pet_safe": True,
        "space": "flat",
        "allergy_concern": True,
        "existing_plants": ["Pothos"]
    }

    recommendations = recommend_plants(user, top_n=5)
    print("Top recommendations for your preferences:")
    for rank, (name, score) in enumerate(recommendations, 1):
        print(f"{rank}. {name} (score: {score:.3f})")