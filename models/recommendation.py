from database.plants import df_plants

def _triangular_membership(x, center, spread):
    if spread <= 0: return 1.0 if x == center else 0.0
    return max(0.0, 1.0 - abs(x-center)/spread)

def _fuzzy_match(user_val, plant_val, spread):
    return _triangular_membership(plant_val, user_val, spread)

def recommend_plants(user_prefs, top_n=5):
    if df_plants is None: return []
    scores = []
    for _, plant in df_plants.iterrows():
        w_match = _fuzzy_match(user_prefs["water"],    plant["water"],       2.0)
        s_match = _fuzzy_match(user_prefs["sunlight"], plant["sunlight"],    2.0)
        t_match = _fuzzy_match(user_prefs["temp"],     plant["temperature"], 4.0)
        p_match = (1.0 if plant["pet_safe"] == user_prefs["pet_safe"] else 0.0) if user_prefs.get("pet_safe") is not None else None
        space_match = (1.0 if plant["space"] == user_prefs["space"] else 0.0) if user_prefs.get("space") is not None else None
        if user_prefs.get("allergy_concern") is not None:
            a_match = (1.0 if not plant["pollen_allergies"] else 0.0) if user_prefs["allergy_concern"] else 1.0
        else:
            a_match = None
        user_existing = user_prefs.get("existing_plants", [])
        if user_existing:
            plant_compat_list = plant["existing_plants"]
            exist_match = (sum(1 for up in user_existing if up in plant_compat_list)/len(user_existing)) if plant_compat_list else 0.0
        else:
            exist_match = None
        weights = {"water":0.15,"sunlight":0.15,"temp":0.15,"pet":0.15,"space":0.15,"allergy":0.15,"existing":0.10}
        components = {"water":w_match,"sunlight":s_match,"temp":t_match,"pet":p_match,"space":space_match,"allergy":a_match,"existing":exist_match}
        active = {k:v for k,v in components.items() if v is not None}
        if not active: continue
        active_weight_sum = sum(weights[k] for k in active)
        score = sum(v*weights[k]/active_weight_sum for k,v in active.items())
        scores.append((plant["name"], score))
    scores.sort(key=lambda x: x[1], reverse=True)
    return scores[:top_n]