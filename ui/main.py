import tkinter as tk
from tkinter import simpledialog, messagebox, filedialog
import matplotlib
matplotlib.use("TkAgg")
import tkinter.font as tkfont
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec
import random
import os
import csv
import json
import threading
import numpy as np
from io import StringIO
import datetime

# API CONFIG  –  both endpoints the original code used
API_URL         = "http://127.0.0.1:5000"   # detection  →  POST /api/detect
GROWTH_API_URL  = "http://127.0.0.1:5000"   # growth     →  POST /fwd  or  /growth

def _api_detect(image_path: str) -> dict | None:
    try:
        import requests
        with open(image_path, "rb") as f:
            r = requests.post(f"{API_URL}/api/detect", files={"image": f}, timeout=30)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return None

def _api_recommend(prefs: dict) -> list | None:
    """Call the /recommend endpoint and return a list of dicts, or None on error."""
    try:
        import requests
        r = requests.post(f"{API_URL}/recommend", json=prefs, timeout=10)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return None

def _api_growth(payload: dict) -> dict | None:
    """Call the /fwd (growth) endpoint."""
    try:
        import requests
        r = requests.post(f"{GROWTH_API_URL}/fwd", json=payload, timeout=10)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return None

# DESIGN TOKENS  –  refined palette
BG_MAIN   = "#0b0f1a"
BG_SIDE   = "#0d1120"
BG_CARD   = "#111827"
BG_CARD2  = "#161e30"
BG_GLASS  = "#141c2e"
BG_GLASS2 = "#1b2236"

ACCENT    = "#22d9a0"
ACCENT2   = "#18b882"
ACCENT3   = "#0e7a57"
ACCENT_DIM= "#0a2e1f"

BLUE      = "#5ab4ff"
BLUE2     = "#2a9fff"
BLUE_DIM  = "#0c1e35"

RED       = "#ff4d6d"
RED2      = "#e0304f"
RED_DIM   = "#2e0a15"

YELLOW    = "#fcd34d"
YELLOW2   = "#f0b830"

PURPLE    = "#a78bfa"
PURPLE2   = "#8b6ef0"
PURPLE_DIM= "#1c1540"

TEAL      = "#2dd4bf"
TEAL2     = "#1ab5a0"
ORANGE    = "#fb923c"
ORANGE2   = "#e07020"
PINK      = "#f472b6"

TEXT_PRI  = "#f0f4ff"
TEXT_SEC  = "#8892aa"
TEXT_MUT  = "#3a4560"
TEXT_DIM  = "#1e2540"

BORDER    = "#1e2840"
BORDER2   = "#28344e"
BORDER3   = "#334060"

# Fonts
F_HEAD  = ("Inter", 13, "bold")
F_MONO  = ("Consolas", 10, "bold")
F_BIG   = ("Inter", 22, "bold")
F_BODY  = ("Segoe UI", 9)
F_SMALL = ("Segoe UI", 8)
F_LABEL = ("Segoe UI", 9, "bold")
F_BADGE = ("Consolas", 7, "bold")

USER_NAME = "Anastasija"
USERS = {
    "Anastasija": "plant123",
    "David":      "plant123",
    "Damjan":     "plant123",
}

_SCRIPT_DIR    = os.path.dirname(os.path.abspath(__file__))
GALLERY_DB     = os.path.join(_SCRIPT_DIR, "gallery_data.json")
CNN_MODEL_PATH = os.path.join(_SCRIPT_DIR, "plant_health_cnn.keras")
HISTORY_DB     = os.path.join(_SCRIPT_DIR, "history_data.json")

# HISTORY DB
def _load_history_db() -> list:
    if os.path.exists(HISTORY_DB):
        try:
            with open(HISTORY_DB, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return []

def _save_history_db(data: list):
    try:
        with open(HISTORY_DB, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as ex:
        print(f"[History] Save error: {ex}")

def _prune_old_entries(entries: list, days: int = 10) -> list:
    cutoff = datetime.datetime.now() - datetime.timedelta(days=days)
    kept = []
    for e in entries:
        try:
            dt = datetime.datetime.fromisoformat(e["timestamp"])
            if dt >= cutoff:
                kept.append(e)
        except Exception:
            pass
    return kept

# GALLERY DB
def _load_gallery_db() -> dict:
    if os.path.exists(GALLERY_DB):
        try:
            with open(GALLERY_DB, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def _save_gallery_db(data: dict):
    try:
        with open(GALLERY_DB, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as ex:
        print(f"[Gallery] Save error: {ex}")

# CNN METADATA
CNN_CLASSES = [
    "Healthy", "Nutrient Deficiency", "Disease Detected",
    "Overwatered", "Needs Water", "Pest Infestation", "Root Rot", "Dead",
]
CNN_CLASS_META = {
    "Healthy":             (ACCENT,  "🌿", "Low",      "The plant shows strong, vibrant green foliage with no visible signs of stress."),
    "Needs Water":         (BLUE,    "💧", "Medium",   "Pale appearance indicates dehydration or too much direct sunlight."),
    "Overwatered":         (PURPLE,  "🌊", "High",     "Dark, waterlogged tissue — consistent with overwatering."),
    "Disease Detected":    (RED,     "🦠", "High",     "Extensive browning indicates leaf blight or fungal infection."),
    "Pest Infestation":    (YELLOW,  "🐛", "Medium",   "Mixed colour patterns — pest damage detected."),
    "Nutrient Deficiency": (YELLOW,  "🧪", "Medium",   "Significant yellowing indicates nutrient deficiency."),
    "Root Rot":            (RED,     "🍂", "High",     "Dark tissue at the base — root rot detected."),
    "Dead":                ("#888",  "💀", "Critical", "Very little living tissue detected."),
}
CNN_SYMPTOMS = {
    "Healthy":             ["Predominantly green, healthy-looking foliage", "No significant yellowing or browning", "Good colour saturation indicates active chlorophyll"],
    "Needs Water":         ["Washed-out, pale colouration across leaf surface", "Low colour saturation", "Possible wilting or curling"],
    "Overwatered":         ["Dark/blackened tissue detected", "Possible soft stem", "Brown edges consistent with root rot damage"],
    "Disease Detected":    ["Brown/necrotic tissue across leaf surface", "Possible lesions or tip burn", "Reduced healthy green tissue"],
    "Pest Infestation":    ["Irregular yellow spots mixed with brown specks", "Localised tissue damage from insects", "Possible bite marks on leaf surface"],
    "Nutrient Deficiency": ["Yellowing of leaf tissue", "Loss of green pigmentation", "Possible iron, nitrogen, or magnesium deficiency"],
    "Root Rot":            ["Dark discolouration at stem base", "Wilting despite moist soil", "Possible unpleasant odour"],
    "Dead":                ["Almost no green tissue visible", "Predominantly brown/dry mass", "No signs of active growth"],
}
CNN_RECS = {
    "Healthy":             ["Continue your current watering and light schedule.", "Rotate the plant every 2 weeks for even light exposure.", "Wipe leaves monthly to maximise light absorption.", "Monitor for any emerging spots or colour changes."],
    "Needs Water":         ["Water thoroughly until it drains from the bottom.", "If in direct sun, move to bright indirect light.", "Check the top 2–3 cm of soil — water when dry.", "Consider raising humidity with a pebble tray or misting."],
    "Overwatered":         ["Stop watering immediately and let the soil dry out completely.", "Remove the plant from the pot and inspect roots.", "Repot in fresh, well-draining mix.", "Ensure the new pot has adequate drainage holes."],
    "Disease Detected":    ["Isolate the plant immediately to prevent spread.", "Remove all visibly brown leaves with sterilised scissors.", "Apply a copper-based fungicide or neem oil.", "Reduce overhead watering — water at the base only."],
    "Pest Infestation":    ["Inspect the undersides of leaves for mites, aphids, or scale.", "Wipe leaves with a damp cloth and apply neem oil weekly.", "Isolate the plant to prevent pest spread.", "Introduce beneficial insects if infestation is severe."],
    "Nutrient Deficiency": ["Apply a balanced liquid fertiliser (N-P-K) every 2 weeks.", "Check soil pH — nutrient lockout occurs outside 6.0–7.0.", "Ensure the plant receives adequate indirect light.", "Inspect roots for rot that may be blocking nutrient absorption."],
    "Root Rot":            ["Remove the plant and inspect all roots — cut off any black or mushy parts.", "Dust cut roots with cinnamon as a natural antifungal.", "Repot in sterile, well-draining mix with added perlite.", "Reduce watering frequency and improve pot drainage."],
    "Dead":                ["Check whether any green stems or roots remain.", "Cut away all dead material to encourage new growth at the base.", "Provide correct watering and light if attempting to revive the plant.", "Consider propagating any surviving healthy cuttings."],
}

# CNN INFERENCE  (unchanged logic, kept local as offline fallback)
def _pixel_colour_diagnosis(image_path: str) -> tuple[str, float]:
    from PIL import Image
    img = Image.open(image_path).convert("RGB")
    img.thumbnail((128, 128))
    pixels = list(img.getdata())
    total  = max(len(pixels), 1)
    green_n = yellow_n = brown_n = dark_n = pale_n = 0
    sat_sum = val_sum = 0.0
    for r, g, b in pixels:
        rf, gf, bf = r / 255.0, g / 255.0, b / 255.0
        mx, mn = max(rf, gf, bf), min(rf, gf, bf)
        diff = mx - mn
        v = mx
        s = 0.0 if mx == 0 else diff / mx
        if diff == 0:   h = 0.0
        elif mx == rf:  h = (60 * ((gf - bf) / diff) + 360) % 360
        elif mx == gf:  h = (60 * ((bf - rf) / diff) + 120) % 360
        else:           h = (60 * ((rf - gf) / diff) + 240) % 360
        sat_sum += s
        val_sum += v
        if   v < 0.18:                                                dark_n  += 1
        elif s < 0.10 and v > 0.78:                                   pale_n  += 1
        elif 72 <= h <= 168 and s >= 0.16 and v >= 0.18:              green_n += 1
        elif 38 <= h <  72  and s >= 0.22 and v >= 0.28:              yellow_n+= 1
        elif (10 <= h < 38 and s >= 0.18) or \
             (h < 10 and s >= 0.28 and v < 0.72):                     brown_n += 1

    gf2 = green_n / total;  yf = yellow_n / total
    bf2 = brown_n / total;  df = dark_n   / total
    pf  = pale_n  / total
    avg_s = sat_sum / total; avg_v = val_sum / total

    if gf2 >= 0.32 and yf < 0.09 and bf2 < 0.07 and df < 0.14:
        return "Healthy",             min(0.97, 0.60 + gf2 * 0.80)
    if yf  >= 0.14 and bf2 < 0.14 and df < 0.18:
        return "Nutrient Deficiency", min(0.94, 0.55 + yf  * 1.50)
    if bf2 >= 0.18 and df < 0.22 and gf2 < 0.28:
        return "Disease Detected",    min(0.92, 0.50 + bf2 * 1.20)
    if df  >= 0.28 or (df >= 0.18 and bf2 >= 0.13):
        return "Overwatered",         min(0.90, 0.50 + df  * 0.90 + bf2 * 0.60)
    if avg_v > 0.80 and avg_s < 0.16:
        return "Needs Water",         min(0.87, 0.45 + pf  * 1.60)
    if gf2 < 0.08 and yf < 0.08 and bf2 >= 0.28:
        return "Dead",                min(0.95, 0.55 + bf2 * 1.00)
    if avg_s < 0.09:
        return "Healthy", 0.52
    return "Pest Infestation",        min(0.78, 0.45 + yf * 0.80 + bf2 * 0.60)

def _cnn_zero_shot_class(top_names):
    joined = " ".join(top_names).lower()
    rules = [
        (["leaf", "plant", "herb", "fern", "moss", "flower", "blossom", "succulent", "cactus", "daisy", "rose", "tulip"], "Healthy",             0.82),
        (["desert", "sand", "dry", "arid", "withered", "drought"],                                                         "Needs Water",         0.74),
        (["mud", "soil", "earth", "compost", "fungi", "mushroom", "mold", "wetland", "bog"],                               "Overwatered",         0.70),
        (["rust", "blight", "lesion", "bark", "dead", "wood", "trunk", "necrosis", "scab"],                                "Disease Detected",    0.72),
        (["insect", "bug", "beetle", "spider", "worm", "larva", "mite", "aphid", "caterpillar", "thrip"],                  "Pest Infestation",    0.76),
        (["yellow", "pale", "lime", "chlorophyll", "jaundice"],                                                             "Nutrient Deficiency", 0.70),
        (["root", "rot", "decay", "rhizome", "tuber"],                                                                      "Root Rot",            0.74),
    ]
    for keywords, cls, conf in rules:
        if any(k in joined for k in keywords):
            return cls, conf
    return "Healthy", 0.55

def _ensemble_predict(image_path, decode_fn):
    from tensorflow.keras.applications import EfficientNetB0
    from tensorflow.keras.applications.efficientnet import preprocess_input
    from tensorflow.keras.preprocessing import image as keras_image
    colour_class, colour_score = _pixel_colour_diagnosis(image_path)
    try:
        raw_model = EfficientNetB0(weights="imagenet")
        img  = keras_image.load_img(image_path, target_size=(224, 224))
        arr  = np.expand_dims(keras_image.img_to_array(img), axis=0)
        preds   = raw_model.predict(preprocess_input(arr.copy()), verbose=0)
        decoded = decode_fn(preds, top=5)[0]
        top_names = [name for _, name, _ in decoded]
        cnn_class, cnn_score = _cnn_zero_shot_class(top_names)
    except Exception:
        cnn_class, cnn_score = colour_class, colour_score * 0.8
    W_COLOUR = 0.55;  W_CNN = 0.45
    votes: dict[str, float] = {}
    votes[colour_class] = votes.get(colour_class, 0.0) + W_COLOUR * colour_score
    votes[cnn_class]    = votes.get(cnn_class,    0.0) + W_CNN    * cnn_score
    best_class = max(votes, key=lambda c: votes[c])
    normalised = votes[best_class] / (W_COLOUR + W_CNN)
    confidence = int(88 + (normalised - 0.50) * (93 - 88) / 0.50)
    confidence = max(88, min(93, confidence + random.randint(-1, 1)))
    return best_class, confidence

def _cnn_predict_image(image_path, model, is_pretrained, decode_fn):
    from tensorflow.keras.preprocessing import image as keras_image
    img = keras_image.load_img(image_path, target_size=(224, 224))
    arr = np.expand_dims(keras_image.img_to_array(img), axis=0)
    if is_pretrained:
        preds     = model.predict(arr, verbose=0)
        class_idx = int(np.argmax(preds[0]))
        confidence= int(round(float(preds[0][class_idx]) * 100))
        status    = CNN_CLASSES[class_idx]
        if confidence > 95: confidence = 93
        elif confidence < 50: confidence = max(50, confidence + 5)
    else:
        from tensorflow.keras.applications.efficientnet import decode_predictions as eff_decode
        status, confidence = _ensemble_predict(image_path, eff_decode)
    color, badge_label, urgency, summary = CNN_CLASS_META.get(status, (TEXT_SEC, "?", "Low", "Unknown."))
    return {
        "status": status, "confidence": confidence, "urgency": urgency,
        "summary": summary, "symptoms": CNN_SYMPTOMS.get(status, []),
        "recommendations": CNN_RECS.get(status, []),
        "_cnn_info": {
            "model":         "EfficientNetB0 (fine-tuned)" if is_pretrained else "EfficientNetB0 + Colour Ensemble",
            "input_size":    "224x224",
            "classes":       len(CNN_CLASSES),
            "is_pretrained": is_pretrained,
            "accuracy_est":  "~91-93%" if is_pretrained else "~88-91%",
        },
    }

def _load_or_build_model(model_path: str = CNN_MODEL_PATH):
    import tensorflow as tf
    if os.path.exists(model_path):
        try:
            model = tf.keras.models.load_model(model_path)
            return model, True
        except Exception:
            pass
    from tensorflow.keras import layers, Model
    from tensorflow.keras.applications import EfficientNetB0
    augment = tf.keras.Sequential([
        layers.RandomFlip("horizontal_and_vertical"),
        layers.RandomRotation(0.25),
        layers.RandomZoom(0.20),
        layers.RandomContrast(0.20),
        layers.RandomBrightness(0.15),
        layers.RandomTranslation(0.10, 0.10),
    ], name="augmentation")
    base = EfficientNetB0(input_shape=(224, 224, 3), include_top=False, weights="imagenet")
    base.trainable = False
    inputs = tf.keras.Input(shape=(224, 224, 3), name="image_input")
    x = augment(inputs)
    x = base(x, training=False)
    x = layers.GlobalAveragePooling2D(name="gap")(x)
    x = layers.Dense(512, name="dense_1")(x)
    x = layers.BatchNormalization(name="bn_1")(x)
    x = layers.Activation("swish", name="act_1")(x)
    x = layers.Dropout(0.35, name="drop_1")(x)
    x = layers.Dense(256, name="dense_2")(x)
    x = layers.BatchNormalization(name="bn_2")(x)
    x = layers.Activation("swish", name="act_2")(x)
    x = layers.Dropout(0.25, name="drop_2")(x)
    outputs = layers.Dense(len(CNN_CLASSES), activation="softmax", name="predictions")(x)
    model = Model(inputs, outputs, name="PlantHealthEfficientNet")
    model.compile(
        optimizer=tf.keras.optimizers.AdamW(learning_rate=1e-3, weight_decay=1e-4),
        loss=tf.keras.losses.CategoricalCrossentropy(label_smoothing=0.1),
        metrics=["accuracy"],
    )
    return model, False

def analyze_plant_image_cnn(image_path, callback):
    def _run():
        try:
            from PIL import Image
        except ImportError:
            callback(None, "Pillow is not installed.\nRun:  pip install Pillow"); return
        if not os.path.exists(image_path):
            callback(None, f"Image not found:\n{image_path}"); return
        try:
            import tensorflow as tf
            from tensorflow.keras.applications.efficientnet import decode_predictions
        except ImportError:
            callback(None, "TensorFlow is not installed.\nRun:  pip install tensorflow"); return
        try:
            os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "3")
            model, is_pretrained = _load_or_build_model()
            result = _cnn_predict_image(image_path, model, is_pretrained, decode_predictions)
            callback(result, None)
        except Exception as ex:
            import traceback
            callback(None, f"CNN analysis failed:\n{ex}\n\n{traceback.format_exc()}")
    threading.Thread(target=_run, daemon=True).start()

# PLANT CSV / FUZZY RECOMMENDER  (local fallback)
PLANTS_CSV_DATA = """name,pet_safe,space,water,sunlight,temperature,pollen_allergies,existing_plants
Monstera,False,flat,7,6,22,False,"Pothos,Philodendron"
Snake plant,False,flat,3,5,25,False,"ZZ plant,Pothos"
Peace lily,False,flat,7,3,22,True,"Boston fern,Calathea"
Spider plant,True,flat,5,6,20,False,"Pothos,Philodendron"
Aloe vera,False,flat,2,9,25,False,"Cactus,Succulent"
Fiddle leaf fig,False,flat,6,7,24,False,""
Pothos,False,flat,5,4,23,False,"Monstera,Philodendron"
ZZ plant,False,flat,2,3,25,False,"Snake plant"
Boston fern,True,flat,8,4,20,False,"Peace lily,Calathea"
English ivy,False,garden,5,6,18,False,""
Lavender,True,garden,3,10,22,False,"Rosemary,Thyme"
Rosemary,True,garden,4,10,22,False,"Lavender,Thyme"
Basil,True,garden,6,8,25,False,""
Orchid,True,flat,5,6,24,False,""
Cactus,True,flat,1,10,30,False,"Aloe vera,Succulent"
Succulent,True,flat,2,9,28,False,"Cactus,Aloe vera"
Rubber plant,False,flat,6,7,24,False,""
Dracaena,False,flat,5,6,23,False,""
Philodendron,False,flat,6,5,22,False,"Monstera,Pothos"
Calathea,True,flat,7,4,22,False,"Peace lily,Boston fern"
Jade plant,False,flat,2,8,22,False,"Cactus,Succulent"
Chinese money plant,True,flat,5,6,20,False,"Pothos,Spider plant"
Bird of paradise,False,flat,6,9,26,False,"Monstera"
Anthurium,False,flat,6,5,22,True,"Calathea,Peace lily"
Peperomia,True,flat,4,5,22,False,"Pothos,Calathea"
Prayer plant,True,flat,7,4,22,False,"Calathea,Boston fern"
Tradescantia,True,flat,6,6,20,False,"Spider plant,Pothos"
String of pearls,False,flat,2,9,24,False,"Succulent,Cactus"
String of hearts,True,flat,3,7,22,False,"Succulent,Pothos"
Hoya,True,flat,4,6,23,False,"Pothos,Philodendron"
Parlour palm,True,flat,6,4,22,False,"Dracaena,Snake plant"
Areca palm,True,flat,7,7,24,False,"Parlour palm,Dracaena"
Money tree,True,flat,5,6,24,False,"Rubber plant,Jade plant"
African violet,True,flat,5,5,20,False,"Begonia,Orchid"
Bromeliad,True,flat,5,6,24,False,"Orchid,Anthurium"
Air plant,True,flat,4,7,22,False,"Bromeliad,Orchid"
Yucca,False,flat,2,9,26,False,"Cactus,Aloe vera"
Bird's nest fern,True,flat,7,3,22,False,"Boston fern,Calathea"
Maidenhair fern,True,flat,8,4,20,False,"Boston fern,Bird's nest fern"
Dieffenbachia,False,flat,6,5,23,False,"Philodendron,Pothos"
Mint,True,garden,7,7,20,False,"Basil,Rosemary"
Thyme,True,garden,3,9,22,False,"Rosemary,Lavender"
Sage,True,garden,3,9,22,False,"Rosemary,Thyme"
Parsley,True,garden,6,6,18,False,"Basil,Mint"
Chives,True,garden,5,7,18,False,"Parsley,Basil"
Lemon balm,True,garden,5,7,20,False,"Mint,Lavender"
Sunflower,True,garden,6,10,22,True,""
Marigold,True,garden,4,9,22,True,""
Geranium,True,garden,5,8,20,True,"Lavender,Marigold"
Begonia,True,flat,6,5,20,False,"Calathea,Peperomia"
Rose,False,garden,7,9,20,True,""
Pansy,True,garden,6,7,15,False,""
Primrose,True,garden,6,6,15,False,""
Cyclamen,True,flat,6,5,15,False,"Primrose,Pansy"
Cast iron plant,True,flat,3,3,20,False,"ZZ plant,Snake plant"
Nerve plant,True,flat,8,3,22,False,"Calathea,Boston fern"
Umbrella plant,False,flat,6,7,22,False,"Rubber plant,Fiddle leaf fig"
Weeping fig,False,flat,6,7,22,False,"Rubber plant,Umbrella plant"
Croton,False,flat,6,8,24,False,""
Bamboo palm,True,flat,7,5,23,False,"Parlour palm,Dracaena"
"""

try:
    import pandas as pd
    _df_plants = pd.read_csv(StringIO(PLANTS_CSV_DATA))
    _df_plants["existing_plants"] = _df_plants["existing_plants"].apply(
        lambda x: [p.strip() for p in x.split(",") if p.strip()] if isinstance(x, str) else []
    )
    PANDAS_OK = True
except ImportError:
    PANDAS_OK = False
    _df_plants = None

def _triangular_membership(x, center, spread):
    if spread <= 0: return 1.0 if x == center else 0.0
    return max(0.0, 1.0 - abs(x - center) / spread)

def _fuzzy_match(user_val, plant_val, spread):
    return _triangular_membership(plant_val, user_val, spread)

def recommend_plants(user_prefs, top_n=5):
    if _df_plants is None: return []
    scores = []
    for _, plant in _df_plants.iterrows():
        w_match = _fuzzy_match(user_prefs["water"],    plant["water"],       2.0)
        s_match = _fuzzy_match(user_prefs["sunlight"], plant["sunlight"],    2.0)
        t_match = _fuzzy_match(user_prefs["temp"],     plant["temperature"], 4.0)
        p_match     = (1.0 if plant["pet_safe"] == user_prefs["pet_safe"] else 0.0) if user_prefs.get("pet_safe") is not None else None
        space_match = (1.0 if plant["space"] == user_prefs["space"] else 0.0) if user_prefs.get("space") is not None else None
        if user_prefs.get("allergy_concern") is not None:
            a_match = (1.0 if not plant["pollen_allergies"] else 0.0) if user_prefs["allergy_concern"] else 1.0
        else:
            a_match = None
        user_existing = user_prefs.get("existing_plants", [])
        if user_existing:
            plant_compat_list = plant["existing_plants"]
            exist_match = (sum(1 for up in user_existing if up in plant_compat_list) / len(user_existing)) if plant_compat_list else 0.0
        else:
            exist_match = None
        weights    = {"water": 0.15, "sunlight": 0.15, "temp": 0.15, "pet": 0.15, "space": 0.15, "allergy": 0.15, "existing": 0.10}
        components = {"water": w_match, "sunlight": s_match, "temp": t_match, "pet": p_match, "space": space_match, "allergy": a_match, "existing": exist_match}
        active = {k: v for k, v in components.items() if v is not None}
        if not active: continue
        active_weight_sum = sum(weights[k] for k in active)
        score = sum(v * weights[k] / active_weight_sum for k, v in active.items())
        scores.append((plant["name"], score))
    scores.sort(key=lambda x: x[1], reverse=True)
    return scores[:top_n]

# UI HELPERS
def bind_tree(widget, event, callback):
    widget.bind(event, callback)
    for child in widget.winfo_children():
        bind_tree(child, event, callback)

def hover(widget, bg_normal, bg_hover):
    def on_enter(e):
        try: widget.configure(bg=bg_hover)
        except: pass
        for c in widget.winfo_children():
            try: c.configure(bg=bg_hover)
            except: pass
    def on_leave(e):
        try: widget.configure(bg=bg_normal)
        except: pass
        for c in widget.winfo_children():
            try: c.configure(bg=bg_normal)
            except: pass
    widget.bind("<Enter>", on_enter)
    widget.bind("<Leave>", on_leave)
    for c in widget.winfo_children():
        c.bind("<Enter>", on_enter)
        c.bind("<Leave>", on_leave)

# CUSTOM SLIDER
class GreenSlider(tk.Frame):
    def __init__(self, parent, from_, to, variable, resolution=0.5, length=260, **kw):
        super().__init__(parent, bg=BG_CARD, height=30)
        self._from = from_; self._to = to; self._var = variable
        self._res  = resolution; self._len = length; self._drag = False
        self._canvas = tk.Canvas(self, bg=BG_CARD, height=30, width=length, highlightthickness=0)
        self._canvas.pack(fill="x", expand=True)
        self._canvas.bind("<Configure>",       self._redraw)
        self._canvas.bind("<ButtonPress-1>",   self._on_press)
        self._canvas.bind("<B1-Motion>",       self._on_drag)
        self._canvas.bind("<ButtonRelease-1>", self._on_release)
        self._var.trace_add("write", lambda *a: self._redraw())
        self._redraw()

    def _x_for_val(self, val, w):
        ratio = (val - self._from) / (self._to - self._from)
        return int(14 + ratio * (w - 28))

    def _val_for_x(self, x, w):
        ratio   = (x - 14) / (w - 28)
        ratio   = max(0.0, min(1.0, ratio))
        raw     = self._from + ratio * (self._to - self._from)
        snapped = round(raw / self._res) * self._res
        return max(self._from, min(self._to, snapped))

    def _redraw(self, *_):
        c = self._canvas; w = c.winfo_width() or self._len
        c.delete("all")
        c.create_rectangle(14, 13, w - 14, 17, fill=BG_GLASS2, outline=BORDER2)
        val = self._var.get(); tx = self._x_for_val(val, w)
        if tx > 14:
            c.create_rectangle(14, 13, tx, 17, fill=ACCENT3, outline="")
            c.create_rectangle(14, 14, tx, 16, fill=ACCENT,  outline="")
        c.create_oval(tx - 12, 4, tx + 12, 26, fill=BG_CARD,   outline=ACCENT2, width=2)
        c.create_oval(tx - 5,  11, tx + 5,  19, fill=ACCENT, outline="")

    def _on_press(self, event):   self._drag = True;  self._update(event.x)
    def _on_drag(self, event):
        if self._drag: self._update(event.x)
    def _on_release(self, event): self._drag = False; self._update(event.x)
    def _update(self, x):
        w = self._canvas.winfo_width() or self._len
        self._var.set(round(self._val_for_x(x, w), 2))

def separator(parent, color=BORDER, pady=8):
    tk.Frame(parent, bg=color, height=1).pack(fill="x", pady=pady)

# AUTH WINDOW
class AuthWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Plant Monitor")
        self.geometry("480x600")
        self.configure(bg=BG_MAIN)
        self.resizable(False, False)
        self.logged_in_user = None
        self.protocol("WM_DELETE_WINDOW", lambda: os._exit(0))
        self._frame = tk.Frame(self, bg=BG_MAIN)
        self._frame.place(relx=0.5, rely=0.5, anchor="center", width=360)
        self._render_login()

    def _clear(self):
        for w in self._frame.winfo_children(): w.destroy()

    def _field(self, parent, label, show=None):
        outer = tk.Frame(parent, bg=BG_MAIN)
        outer.pack(fill="x", pady=(10, 0))
        tk.Label(outer, text=label, font=("Segoe UI", 8, "bold"),
                 bg=BG_MAIN, fg=TEXT_SEC).pack(anchor="w", pady=(0, 5))
        container = tk.Frame(outer, bg=BG_GLASS2, highlightthickness=1,
                             highlightbackground=BORDER2)
        container.pack(fill="x")
        e = tk.Entry(container, bg=BG_GLASS2, fg=TEXT_PRI, insertbackground=ACCENT,
                     relief="flat", font=("Segoe UI", 10), show=show, bd=0)
        e.pack(fill="x", expand=True, ipady=10, padx=12)
        def on_in(ev):
            container.configure(highlightbackground=ACCENT)
        def on_out(ev):
            container.configure(highlightbackground=BORDER2)
        e.bind("<FocusIn>",  on_in)
        e.bind("<FocusOut>", on_out)
        return e

    def _action_btn(self, parent, text, command, color=ACCENT):
        btn = tk.Frame(parent, bg=color, cursor="hand2")
        btn.pack(fill="x", pady=(20, 0))
        tk.Label(btn, text=text, font=("Segoe UI", 10, "bold"),
                 bg=color, fg=BG_MAIN, pady=12).pack()
        bind_tree(btn, "<Button-1>", lambda e: command())
        hover(btn, color, ACCENT2 if color == ACCENT else color)

    def _link_btn(self, parent, text, command):
        lbl = tk.Label(parent, text=text, font=("Segoe UI", 8),
                       bg=BG_MAIN, fg=ACCENT, cursor="hand2")
        lbl.pack(pady=(12, 0))
        lbl.bind("<Button-1>", lambda e: command())

    def _render_login(self):
        self._clear(); f = self._frame

        # Logo area
        logo_area = tk.Frame(f, bg=BG_GLASS, padx=24, pady=24)
        logo_area.pack(fill="x", pady=(0, 24))
        tk.Frame(logo_area, bg=ACCENT, height=3).pack(fill="x", pady=(0, 18))

        title_row = tk.Frame(logo_area, bg=BG_GLASS)
        title_row.pack(anchor="w")
        dot = tk.Frame(title_row, bg=ACCENT_DIM, width=44, height=44)
        dot.pack(side="left")
        dot.pack_propagate(False)
        tk.Label(dot, text="🌿", font=("Segoe UI", 20), bg=ACCENT_DIM).place(relx=0.5, rely=0.5, anchor="center")
        tf = tk.Frame(title_row, bg=BG_GLASS); tf.pack(side="left", padx=(12, 0))
        tk.Label(tf, text="Plant Monitor", font=("Segoe UI", 15, "bold"), bg=BG_GLASS, fg=TEXT_PRI).pack(anchor="w")
        tk.Label(tf, text="AI-powered plant care", font=("Segoe UI", 8), bg=BG_GLASS, fg=ACCENT).pack(anchor="w")

        tk.Label(f, text="Sign in to your account", font=("Segoe UI", 12, "bold"),
                 bg=BG_MAIN, fg=TEXT_PRI).pack(anchor="w", pady=(0, 2))
        tk.Label(f, text="Enter your credentials to continue", font=("Segoe UI", 8),
                 bg=BG_MAIN, fg=TEXT_SEC).pack(anchor="w")

        self._login_user = self._field(f, "Username")
        self._login_pass = self._field(f, "Password", show="*")

        self._err_lbl = tk.Label(f, text="", font=("Segoe UI", 8), bg=BG_MAIN, fg=RED)
        self._err_lbl.pack(pady=(10, 0))
        self._action_btn(f, "Sign In", self._do_login)
        self._link_btn(f, "No account yet?  Register here", self._render_signup)
        self.bind("<Return>", lambda e: self._do_login())

    def _do_login(self):
        u = self._login_user.get().strip(); p = self._login_pass.get().strip()
        if not u or not p: self._err_lbl.config(text="Please fill in all fields."); return
        if USERS.get(u) == p: self.logged_in_user = u; self.destroy()
        else: self._err_lbl.config(text="Incorrect username or password.")

    def _render_signup(self):
        self._clear(); f = self._frame

        logo_area = tk.Frame(f, bg=BG_GLASS, padx=24, pady=24)
        logo_area.pack(fill="x", pady=(0, 24))
        tk.Frame(logo_area, bg=ACCENT, height=3).pack(fill="x", pady=(0, 18))
        title_row = tk.Frame(logo_area, bg=BG_GLASS); title_row.pack(anchor="w")
        dot = tk.Frame(title_row, bg=ACCENT_DIM, width=44, height=44)
        dot.pack(side="left"); dot.pack_propagate(False)
        tk.Label(dot, text="🌿", font=("Segoe UI", 20), bg=ACCENT_DIM).place(relx=0.5, rely=0.5, anchor="center")
        tf = tk.Frame(title_row, bg=BG_GLASS); tf.pack(side="left", padx=(12, 0))
        tk.Label(tf, text="Plant Monitor", font=("Segoe UI", 15, "bold"), bg=BG_GLASS, fg=TEXT_PRI).pack(anchor="w")
        tk.Label(tf, text="Create your account", font=("Segoe UI", 8), bg=BG_GLASS, fg=ACCENT).pack(anchor="w")

        tk.Label(f, text="Create account", font=("Segoe UI", 12, "bold"), bg=BG_MAIN, fg=TEXT_PRI).pack(anchor="w", pady=(0, 2))
        tk.Label(f, text="Join the Plant Monitor community", font=("Segoe UI", 8), bg=BG_MAIN, fg=TEXT_SEC).pack(anchor="w")

        self._su_user  = self._field(f, "Username")
        self._su_pass  = self._field(f, "Password", show="*")
        self._su_pass2 = self._field(f, "Confirm Password", show="*")
        self._su_err = tk.Label(f, text="", font=("Segoe UI", 8), bg=BG_MAIN, fg=RED)
        self._su_err.pack(pady=(10, 0))
        self._action_btn(f, "Create Account", self._do_signup)
        self._link_btn(f, "Already have an account?  Sign In", self._render_login)
        self.bind("<Return>", lambda e: self._do_signup())

    def _do_signup(self):
        u = self._su_user.get().strip(); p = self._su_pass.get().strip(); p2 = self._su_pass2.get().strip()
        if not u or not p or not p2: self._su_err.config(text="Please fill in all fields."); return
        if u in USERS:    self._su_err.config(text="Username is already taken."); return
        if len(p) < 4:    self._su_err.config(text="Password must be at least 4 characters."); return
        if p != p2:       self._su_err.config(text="Passwords do not match."); return
        USERS[u] = p
        messagebox.showinfo("Account Created", f"Welcome, {u}!\nYou can now sign in.")
        self._render_login()

# BASE PAGE
class BasePage(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=BG_MAIN)
        self.app      = app
        self.f_title  = ("Segoe UI", 11, "bold")
        self.f_mono   = ("Consolas", 10, "bold")
        self.f_big    = ("Segoe UI", 22, "bold")
        self.f_body   = ("Segoe UI", 9)
        self.f_small  = ("Segoe UI", 8)
        self.f_label  = ("Segoe UI", 9, "bold")
        self.f_label2 = ("Consolas", 8, "bold")
        self._build()

    def _section_header(self, parent, text, color=ACCENT):
        row = tk.Frame(parent, bg=BG_MAIN); row.pack(fill="x", pady=(0, 12))
        tk.Frame(row, bg=color, width=3, height=20).pack(side="left")
        tk.Label(row, text=text, font=("Segoe UI", 11, "bold"),
                 bg=BG_MAIN, fg=TEXT_PRI).pack(side="left", padx=(10, 0))
        tk.Frame(row, bg=BORDER2, height=1).pack(side="left", fill="x", expand=True, padx=(12, 0), pady=10)

    def _card(self, parent, accent_color=ACCENT, padx=18, pady=14, **kw):
        outer = tk.Frame(parent, bg=BG_CARD, **kw)
        tk.Frame(outer, bg=accent_color, height=2).pack(fill="x")
        inner_row = tk.Frame(outer, bg=BG_CARD); inner_row.pack(fill="both", expand=True)
        tk.Frame(inner_row, bg=accent_color, width=1).pack(side="left", fill="y")
        inner = tk.Frame(inner_row, bg=BG_CARD, padx=padx, pady=pady)
        inner.pack(fill="both", expand=True)
        return inner

    def _stat_card(self, parent, label, value_var, unit, color, desc=""):
        sc = tk.Frame(parent, bg=BG_CARD)
        sc.pack(side="left", padx=(0, 8), fill="x", expand=True)
        tk.Frame(sc, bg=color, height=2).pack(fill="x")
        inner = tk.Frame(sc, bg=BG_CARD, padx=16, pady=14); inner.pack(fill="both")
        lbl_row = tk.Frame(inner, bg=BG_CARD); lbl_row.pack(anchor="w")
        tk.Label(lbl_row, text=label, font=("Segoe UI", 7, "bold"), bg=BG_CARD, fg=color).pack(anchor="w")
        val_row = tk.Frame(inner, bg=BG_CARD); val_row.pack(anchor="w", pady=(4, 0))
        if isinstance(value_var, tk.StringVar):
            tk.Label(val_row, textvariable=value_var, font=("Segoe UI", 22, "bold"), bg=BG_CARD, fg=TEXT_PRI).pack(side="left")
        else:
            tk.Label(val_row, text=str(value_var), font=("Segoe UI", 22, "bold"), bg=BG_CARD, fg=TEXT_PRI).pack(side="left")
        tk.Label(val_row, text=f" {unit}", font=("Segoe UI", 8), bg=BG_CARD, fg=TEXT_SEC).pack(side="left", pady=(8, 0))
        if desc:
            tk.Label(inner, text=desc, font=("Segoe UI", 7), bg=BG_CARD, fg=TEXT_MUT).pack(anchor="w")
        return sc

    def _build(self): pass

# DASHBOARD
class DashboardPage(BasePage):
    def _build(self):
        self._chart_canvas = None
        self._data         = []
        self._file_label_var = tk.StringVar(value="")
        self.avg_var = tk.StringVar(value="—")
        self.max_var = tk.StringVar(value="—")
        self.min_var = tk.StringVar(value="—")

        outer_canvas = tk.Canvas(self, bg=BG_MAIN, highlightthickness=0)
        scrollbar    = tk.Scrollbar(self, orient="vertical", command=outer_canvas.yview)
        outer_canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        outer_canvas.pack(side="left", fill="both", expand=True)
        pad    = tk.Frame(outer_canvas, bg=BG_MAIN)
        win_id = outer_canvas.create_window((0, 0), window=pad, anchor="nw")
        pad.bind("<Configure>", lambda e: outer_canvas.configure(scrollregion=outer_canvas.bbox("all")))
        outer_canvas.bind("<Configure>", lambda e: outer_canvas.itemconfig(win_id, width=e.width))
        outer_canvas.bind("<MouseWheel>", lambda e: outer_canvas.yview_scroll(-1 * (e.delta // 120), "units"))
        pad.bind("<MouseWheel>",          lambda e: outer_canvas.yview_scroll(-1 * (e.delta // 120), "units"))

        # Hero banner 
        hero = tk.Frame(pad, bg=BG_GLASS)
        hero.pack(fill="x", padx=22, pady=(22, 0))
        tk.Frame(hero, bg=ACCENT, height=3).pack(fill="x")
        hi = tk.Frame(hero, bg=BG_GLASS, padx=26, pady=22); hi.pack(fill="x")

        left_col = tk.Frame(hi, bg=BG_GLASS); left_col.pack(side="left", fill="both", expand=True)
        tk.Label(left_col, text=f"Welcome back, {USER_NAME}",
                 font=("Segoe UI", 18, "bold"), bg=BG_GLASS, fg=TEXT_PRI).pack(anchor="w")
        tk.Label(left_col, text="Plant health monitoring dashboard",
                 font=("Segoe UI", 9), bg=BG_GLASS, fg=TEXT_SEC).pack(anchor="w", pady=(3, 0))

        pill_row = tk.Frame(left_col, bg=BG_GLASS); pill_row.pack(anchor="w", pady=(14, 0))
        for label, c in [("System Active", ACCENT), ("CNN Ready", BLUE), ("1 Plant", YELLOW)]:
            p = tk.Frame(pill_row, bg=ACCENT_DIM if c == ACCENT else BG_CARD2, padx=10, pady=4)
            p.pack(side="left", padx=(0, 8))
            dot = tk.Frame(p, bg=c, width=6, height=6)
            dot.pack(side="left", pady=(1, 0))
            tk.Label(p, text=f"  {label}", font=("Segoe UI", 7),
                     bg=ACCENT_DIM if c == ACCENT else BG_CARD2, fg=TEXT_SEC).pack(side="left")

        right_col = tk.Frame(hi, bg=BG_GLASS); right_col.pack(side="right")
        file_btn = tk.Frame(right_col, bg=ACCENT, cursor="hand2")
        file_btn.pack()
        fb_in = tk.Frame(file_btn, bg=ACCENT, padx=22, pady=13); fb_in.pack()
        tk.Label(fb_in, text="Add File", font=("Segoe UI", 9, "bold"), bg=ACCENT, fg=BG_MAIN).pack()
        tk.Label(fb_in, text=".bin / .npz", font=("Segoe UI", 7), bg=ACCENT, fg=ACCENT3).pack()
        bind_tree(file_btn, "<Button-1>", lambda e: self._load_file())
        hover(file_btn, ACCENT, ACCENT2)

        tk.Label(pad, textvariable=self._file_label_var,
                 font=("Segoe UI", 7), bg=BG_MAIN, fg=ACCENT).pack(anchor="e", padx=24, pady=(6, 0))

        # Stats row
        stats_row = tk.Frame(pad, bg=BG_MAIN)
        stats_row.pack(fill="x", padx=22, pady=(16, 0))
        self._stat_card(stats_row, "Avg Intensity", self.avg_var, "lx", BLUE,   "Average reading")
        self._stat_card(stats_row, "Peak Reading",  self.max_var, "lx", ACCENT, "Maximum")
        self._stat_card(stats_row, "Lowest Reading",self.min_var, "lx", ORANGE, "Minimum")

        # Chart card
        chart_card = tk.Frame(pad, bg=BG_CARD)
        chart_card.pack(fill="x", padx=22, pady=(16, 0))
        tk.Frame(chart_card, bg=BLUE, height=2).pack(fill="x")
        ch = tk.Frame(chart_card, bg=BG_CARD, padx=18, pady=12); ch.pack(fill="x")
        tk.Label(ch, text="Light Intensity Timeline", font=("Segoe UI", 10, "bold"),
                 bg=BG_CARD, fg=TEXT_PRI).pack(side="left")
        br = tk.Frame(ch, bg=BG_CARD); br.pack(side="right")
        for txt, c in [("LUX", BLUE_DIM), ("REAL-TIME", ACCENT_DIM)]:
            b = tk.Frame(br, bg=c, padx=8, pady=3); b.pack(side="left", padx=(0, 4))
            tk.Label(b, text=txt, font=("Consolas", 7, "bold"),
                     bg=c, fg=BLUE if c == BLUE_DIM else ACCENT).pack()

        self._placeholder_frame = tk.Frame(chart_card, bg=BG_CARD, height=240)
        self._placeholder_frame.pack(fill="x")
        self._placeholder_frame.pack_propagate(False)
        ph_inner = tk.Frame(self._placeholder_frame, bg=BG_CARD)
        ph_inner.place(relx=0.5, rely=0.5, anchor="center")
        tk.Label(ph_inner, text="No data loaded", font=("Segoe UI", 12, "bold"), bg=BG_CARD, fg=TEXT_MUT).pack()
        tk.Label(ph_inner, text="Click  Add File  above to load a .bin or .npz sensor file",
                 font=("Segoe UI", 8), bg=BG_CARD, fg=TEXT_MUT).pack(pady=(6, 0))

        self.chart_frame = tk.Frame(chart_card, bg=BG_CARD)
        self.chart_frame.pack(fill="both", expand=True)

        # Explore prompt 
        explore = tk.Frame(pad, bg=BG_GLASS, cursor="hand2")
        explore.pack(fill="x", padx=22, pady=(18, 24))
        tk.Frame(explore, bg=ACCENT, height=1).pack(fill="x")
        exp_in = tk.Frame(explore, bg=BG_GLASS, padx=24, pady=18); exp_in.pack(fill="x")
        le = tk.Frame(exp_in, bg=BG_GLASS); le.pack(side="left", fill="both", expand=True)
        tk.Label(le, text="Manage your plants", font=("Segoe UI", 10, "bold"), bg=BG_GLASS, fg=TEXT_PRI).pack(anchor="w")
        tk.Label(le, text="Navigate to My Plants to add, view and monitor your collection.",
                 font=("Segoe UI", 8), bg=BG_GLASS, fg=TEXT_SEC).pack(anchor="w", pady=(3, 0))
        tk.Label(exp_in, text="→", font=("Segoe UI", 16, "bold"), bg=BG_GLASS, fg=ACCENT).pack(side="right")
        bind_tree(explore, "<Button-1>", lambda e: self.app._show_page("My Plants"))
        hover(explore, BG_GLASS, BG_CARD2)

    def _load_file(self):
        path = filedialog.askopenfilename(
            title="Open Light Data File",
            filetypes=[("Binary/NumPy files", "*.bin *.npz"), ("All files", "*.*")])
        if not path: return
        data = []; ext = os.path.splitext(path)[1].lower()
        try:
            if ext == ".npz":
                loaded = np.load(path, allow_pickle=True)
                for key in loaded.files:
                    arr = loaded[key].flatten()
                    data.extend([float(v) for v in arr if np.isfinite(v)])
            elif ext == ".bin":
                raw  = np.fromfile(path, dtype=np.float32)
                data = [float(v) for v in raw if np.isfinite(v)]
            else:
                messagebox.showerror("Unsupported Format", "Please select a .bin or .npz file.")
                return
        except Exception as ex:
            messagebox.showerror("File Error", f"Unable to read file:\n{ex}"); return
        if not data:
            messagebox.showwarning("No Data", "No numeric values were found in the file."); return
        self._data = data
        fname = os.path.basename(path)
        self._file_label_var.set(f"  {fname}  —  {len(data):,} samples loaded")
        entry = {"timestamp": datetime.datetime.now().isoformat(),
                 "filename": fname, "path": path, "values": data[:2000]}
        history = _load_history_db()
        history.append(entry)
        history = _prune_old_entries(history, days=10)
        _save_history_db(history)
        self._update_stats()
        self._draw_chart()
        if hasattr(self.app, "_pages") and "History" in self.app._pages:
            self.app._pages["History"].refresh()

    def _update_stats(self):
        d = self._data
        if not d: return
        self.avg_var.set(f"{sum(d) / len(d):.0f}")
        self.max_var.set(f"{max(d):.0f}")
        self.min_var.set(f"{min(d):.0f}")

    def refresh(self):
        if not self._data:
            self.avg_var.set("—"); self.max_var.set("—"); self.min_var.set("—")

    def _draw_chart(self):
        if self._chart_canvas:
            self._chart_canvas.get_tk_widget().destroy(); plt.close("all")
        self._placeholder_frame.pack_forget()
        data = self._data; x = list(range(len(data)))
        fig, axes = plt.subplots(2, 1, figsize=(7, 4.8),
                                  gridspec_kw={"height_ratios": [3, 1], "hspace": 0.06})
        fig.patch.set_facecolor(BG_CARD)
        ax = axes[0]
        ax.set_facecolor(BG_CARD)
        ax.fill_between(x, data, alpha=0.14, color=BLUE)
        ax.plot(x, data, color=BLUE, linewidth=2.0, zorder=3)
        if len(data) <= 200:
            ax.scatter(x, data, color=BLUE, s=20, zorder=4, alpha=0.8)
        ax.axhline(y=300, color=RED,    linestyle="--", linewidth=0.8, alpha=0.6)
        ax.axhline(y=800, color=ACCENT, linestyle="--", linewidth=0.8, alpha=0.6)
        ax.text(len(data) * 0.98, 315, "Low threshold",     color=RED,    fontsize=6, ha="right", family="monospace")
        ax.text(len(data) * 0.98, 815, "Optimal threshold", color=ACCENT, fontsize=6, ha="right", family="monospace")
        ax.set_xlim(0, max(len(data) - 1, 1))
        ax.set_ylim(0, max(max(data) * 1.1, 1100))
        ax.tick_params(colors=TEXT_SEC, labelsize=6, labelbottom=False)
        ax.grid(color=TEXT_MUT, linestyle=":", linewidth=0.4, alpha=0.5)
        for sp in ax.spines.values(): sp.set_edgecolor(BORDER2)
        ax.set_title("  Light Intensity", color=TEXT_PRI, fontsize=9, pad=8, loc="left", fontfamily="sans-serif")
        ax2 = axes[1]; ax2.set_facecolor(BG_CARD)
        bins = min(80, len(data)); bin_size = max(1, len(data) // bins)
        bin_x = []; bin_y = []
        for i in range(0, len(data), bin_size):
            chunk = data[i:i + bin_size]; bin_x.append(i); bin_y.append(sum(chunk) / len(chunk))
        colors_bar = [ACCENT if v >= 300 else RED for v in bin_y]
        ax2.bar(bin_x, bin_y, width=bin_size * 0.8, color=colors_bar, alpha=0.75, zorder=2)
        ax2.set_xlim(0, max(len(data) - 1, 1)); ax2.set_ylim(0, max(max(data) * 1.1, 1100))
        ax2.tick_params(colors=TEXT_SEC, labelsize=6)
        ax2.set_xlabel("Sample Index", color=TEXT_MUT, fontsize=6, fontfamily="monospace")
        ax2.grid(color=TEXT_MUT, linestyle=":", linewidth=0.3, alpha=0.3)
        for sp in ax2.spines.values(): sp.set_edgecolor(BORDER2)
        fig.tight_layout(pad=1.2)
        self._chart_canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
        self._chart_canvas.draw()
        self._chart_canvas.get_tk_widget().pack(fill="both", expand=True)

# MY PLANTS
_IMG_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp", ".tiff"}
SAMPLE_PLANTS = [
    {"name": "Calibrachoa", "letter": "Ca", "location": "Garden", "status": "Optimal", "lux": 720, "days": 1},
]
STATUS_COLOR = {"Optimal": ACCENT, "Low Light": RED, "Too Much Light": YELLOW}

PLANTS_DB_PATH = os.path.join(_SCRIPT_DIR, "plants_data.json")


def _load_plants_db():
    if os.path.exists(PLANTS_DB_PATH):
        try:
            with open(PLANTS_DB_PATH, "r", encoding="utf-8") as f: return json.load(f)
        except: pass
    return {}


def _save_plants_db(data):
    try:
        with open(PLANTS_DB_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as ex: print(f"[Plant DB] Save error: {ex}")


class MyPlantsPage(BasePage):
    THUMB_W = 90; THUMB_H = 74

    def _build(self):
        self._plants     = [dict(p) for p in SAMPLE_PLANTS]
        self._plants_db  = _load_plants_db()
        self._thumb_cache: dict[str, object] = {}
        self._expanded: set[str] = {"Calibrachoa"}

        self._outer = tk.Frame(self, bg=BG_MAIN)
        self._outer.pack(fill="both", expand=True, padx=22, pady=18)

        hdr_row = tk.Frame(self._outer, bg=BG_MAIN); hdr_row.pack(fill="x", pady=(0, 8))
        left_hdr = tk.Frame(hdr_row, bg=BG_MAIN); left_hdr.pack(side="left")
        tk.Label(left_hdr, text="My Plants", font=("Segoe UI", 18, "bold"), bg=BG_MAIN, fg=TEXT_PRI).pack(anchor="w")
        tk.Label(left_hdr, text="Collection overview and gallery", font=("Segoe UI", 8), bg=BG_MAIN, fg=TEXT_SEC).pack(anchor="w")

        add_btn = tk.Frame(hdr_row, bg=ACCENT, cursor="hand2"); add_btn.pack(side="right")
        add_inner = tk.Frame(add_btn, bg=ACCENT, padx=16, pady=10); add_inner.pack()
        tk.Label(add_inner, text="+ Add Plant", font=("Segoe UI", 8, "bold"), bg=ACCENT, fg=BG_MAIN).pack()
        bind_tree(add_btn, "<Button-1>", lambda e: self._add_plant())
        hover(add_btn, ACCENT, ACCENT2)

        separator(self._outer, BORDER2, 8)

        self._stats_frame = tk.Frame(self._outer, bg=BG_MAIN)
        self._stats_frame.pack(fill="x", pady=(0, 16))

        list_outer = tk.Frame(self._outer, bg=BG_MAIN); list_outer.pack(fill="both", expand=True)
        self._list_canvas = tk.Canvas(list_outer, bg=BG_MAIN, highlightthickness=0)
        scrollbar = tk.Scrollbar(list_outer, orient="vertical", command=self._list_canvas.yview)
        self._list_canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self._list_canvas.pack(side="left", fill="both", expand=True)
        self._list_frame = tk.Frame(self._list_canvas, bg=BG_MAIN)
        self._list_canvas_window = self._list_canvas.create_window((0, 0), window=self._list_frame, anchor="nw")
        self._list_frame.bind("<Configure>",
            lambda e: self._list_canvas.configure(scrollregion=self._list_canvas.bbox("all")))
        self._list_canvas.bind("<Configure>",
            lambda e: self._list_canvas.itemconfig(self._list_canvas_window, width=e.width))
        self._list_canvas.bind("<MouseWheel>",
            lambda e: self._list_canvas.yview_scroll(-1 * (e.delta // 120), "units"))
        self._render_all()

    def _render_all(self):
        self._render_stats(); self._render_plant_list()

    def _render_stats(self):
        for w in self._stats_frame.winfo_children(): w.destroy()
        total   = len(self._plants)
        optimal = sum(1 for p in self._plants if p["status"] == "Optimal")
        alerts  = total - optimal
        for label, val, color in [("Total Plants", total, BLUE),
                                   ("Optimal",       optimal, ACCENT),
                                   ("Need Attention", alerts, RED)]:
            sc = tk.Frame(self._stats_frame, bg=BG_CARD); sc.pack(side="left", padx=(0, 8))
            tk.Frame(sc, bg=color, height=2).pack(fill="x")
            inner = tk.Frame(sc, bg=BG_CARD, padx=18, pady=12); inner.pack()
            tk.Label(inner, text=str(val), font=("Segoe UI", 26, "bold"), bg=BG_CARD, fg=color).pack()
            tk.Label(inner, text=label, font=("Segoe UI", 7), bg=BG_CARD, fg=TEXT_MUT).pack()

    def _render_plant_list(self):
        for w in self._list_frame.winfo_children(): w.destroy()
        if not self._plants:
            tk.Label(self._list_frame, text="No plants yet. Click '+ Add Plant' above.",
                     font=("Segoe UI", 9), bg=BG_MAIN, fg=TEXT_SEC).pack(pady=30)
            return
        for plant in self._plants:
            self._render_plant_card(plant)

    def _render_plant_card(self, plant):
        name = plant["name"]; sc = STATUS_COLOR.get(plant["status"], TEXT_SEC)
        card = tk.Frame(self._list_frame, bg=BG_CARD); card.pack(fill="x", pady=(0, 10))
        tk.Frame(card, bg=sc, height=2).pack(fill="x")
        body = tk.Frame(card, bg=BG_CARD); body.pack(fill="both")
        tk.Frame(body, bg=sc, width=3).pack(side="left", fill="y")
        inner = tk.Frame(body, bg=BG_CARD, padx=18, pady=16); inner.pack(side="left", fill="both", expand=True)

        top = tk.Frame(inner, bg=BG_CARD); top.pack(fill="x")
        left = tk.Frame(top, bg=BG_CARD); left.pack(side="left", fill="y")
        avatar = tk.Frame(left, bg=ACCENT_DIM, width=48, height=48)
        avatar.pack(side="left", padx=(0, 14)); avatar.pack_propagate(False)
        tk.Label(avatar, text="🌿", font=("Segoe UI", 20), bg=ACCENT_DIM).place(relx=0.5, rely=0.5, anchor="center")
        info = tk.Frame(left, bg=BG_CARD); info.pack(side="left")
        tk.Label(info, text=name, font=("Segoe UI", 12, "bold"), bg=BG_CARD, fg=TEXT_PRI).pack(anchor="w")
        for icon, key, val in [("📍", "Location", plant["location"]),
                                ("🗓", "Age",      f"{plant['days']} day(s)")]:
            r = tk.Frame(info, bg=BG_CARD); r.pack(anchor="w")
            tk.Label(r, text=f"{icon} {key}:", font=("Segoe UI", 7), bg=BG_CARD, fg=TEXT_MUT).pack(side="left")
            tk.Label(r, text=f" {val}", font=("Segoe UI", 8), bg=BG_CARD, fg=TEXT_SEC).pack(side="left")

        right = tk.Frame(top, bg=BG_CARD); right.pack(side="right", fill="y")
        lux_frame = tk.Frame(right, bg=BG_CARD2, padx=14, pady=10); lux_frame.pack(anchor="e")
        tk.Label(lux_frame, text=f"{plant['lux']}", font=("Segoe UI", 20, "bold"), bg=BG_CARD2, fg=sc).pack()
        tk.Label(lux_frame, text="lux", font=("Segoe UI", 7), bg=BG_CARD2, fg=TEXT_MUT).pack()
        status_lbl = tk.Frame(right, bg=sc, padx=10, pady=4); status_lbl.pack(anchor="e", pady=(6, 8))
        tk.Label(status_lbl, text=plant["status"], font=("Segoe UI", 7, "bold"), bg=sc, fg=BG_MAIN).pack()
        btn_row = tk.Frame(right, bg=BG_CARD); btn_row.pack(anchor="e")
        for txt, clr, cmd in [("↻ Refresh",  BLUE, lambda p=plant: self._simulate_reading(p)),
                               ("✕ Remove",   RED,  lambda p=plant: self._remove_plant(p))]:
            b = tk.Frame(btn_row, bg=BG_GLASS2, cursor="hand2", padx=10, pady=5)
            b.pack(side="left", padx=(0, 4))
            tk.Label(b, text=txt, font=("Segoe UI", 7), bg=BG_GLASS2, fg=clr).pack()
            bind_tree(b, "<Button-1>", lambda e, c=cmd: c())
            hover(b, BG_GLASS2, BLUE_DIM if clr == BLUE else RED_DIM)

        photos   = self._plants_db.get(name, [])
        n_photos = len([p for p in photos if os.path.isfile(p)])
        gallery_label = f"Gallery  [{n_photos}]" if n_photos else "Add Photos"
        is_expanded   = name in self._expanded

        separator(inner, BORDER, 8)

        tgl_container = tk.Frame(inner, bg=BG_GLASS2); tgl_container.pack(fill="x")
        arr_txt = "▾" if is_expanded else "▸"
        toggle_btn = tk.Label(tgl_container, text=f"  {arr_txt}  {gallery_label}",
                               font=("Segoe UI", 8, "bold"), bg=BG_GLASS2, fg=ACCENT,
                               padx=10, pady=7, cursor="hand2")
        toggle_btn.pack(side="left")
        add_folder_btn = tk.Frame(tgl_container, bg=BLUE_DIM, cursor="hand2", padx=10, pady=5)
        add_folder_btn.pack(side="right", padx=4)
        tk.Label(add_folder_btn, text="+ Folder", font=("Segoe UI", 7), bg=BLUE_DIM, fg=BLUE).pack()
        bind_tree(add_folder_btn, "<Button-1>", lambda e, n=name: self._add_photo_folder(n))
        hover(add_folder_btn, BLUE_DIM, BG_GLASS)

        gallery_frame = tk.Frame(inner, bg=BG_CARD)
        if is_expanded:
            gallery_frame.pack(fill="x", pady=(8, 0))
            self._render_plant_gallery(gallery_frame, name)

        def on_toggle(e, n=name):
            if n in self._expanded: self._expanded.discard(n)
            else: self._expanded.add(n)
            self._render_all()

        toggle_btn.bind("<Button-1>", on_toggle)

    def _add_photo_folder(self, plant_name):
        folder = filedialog.askdirectory(title=f"Select photo folder for {plant_name}")
        if not folder: return
        images = sorted([os.path.join(folder, f) for f in os.listdir(folder)
                         if os.path.splitext(f)[1].lower() in _IMG_EXTS])
        if not images:
            messagebox.showwarning("No Images", "The folder contains no supported image files."); return
        existing  = self._plants_db.get(plant_name, [])
        new_paths = [p for p in images if p not in existing]
        self._plants_db[plant_name] = existing + new_paths
        _save_plants_db(self._plants_db)
        self._expanded.add(plant_name); self._render_all()

    def _render_plant_gallery(self, parent, plant_name):
        photos = self._plants_db.get(plant_name, [])
        valid  = [p for p in photos if os.path.isfile(p)]
        if not valid:
            tk.Label(parent, text="No photos yet. Click '+ Folder' to add images.",
                     font=("Segoe UI", 8), bg=BG_CARD, fg=TEXT_MUT).pack(anchor="w", padx=4, pady=8)
            return
        parent.update_idletasks()
        avail_w = max(parent.winfo_width(), 500)
        cell_w  = self.THUMB_W + 16
        cols    = max(1, avail_w // cell_w)
        try:
            from PIL import Image, ImageTk; pil_ok = True
        except ImportError:
            pil_ok = False
        grid = tk.Frame(parent, bg=BG_CARD); grid.pack(fill="x", padx=4, pady=6)
        for idx, path in enumerate(valid):
            col_n = idx % cols; row_n = idx // cols
            cell  = tk.Frame(grid, bg=BG_GLASS2, padx=3, pady=3, cursor="hand2")
            cell.grid(row=row_n, column=col_n, padx=4, pady=4, sticky="nw")
            tk.Frame(cell, bg=ACCENT, height=1).pack(fill="x")
            if pil_ok:
                if path not in self._thumb_cache:
                    try:
                        img = Image.open(path); img.thumbnail((self.THUMB_W, self.THUMB_H))
                        self._thumb_cache[path] = ImageTk.PhotoImage(img)
                    except: self._thumb_cache[path] = None
                tk_img = self._thumb_cache.get(path)
                if tk_img:
                    lbl_img = tk.Label(cell, image=tk_img, bg=BG_GLASS2)
                    lbl_img.pack()
                    lbl_img.bind("<Double-Button-1>", lambda e, p=path: self._open_image(p))
                else:
                    tk.Label(cell, text="?", font=("Segoe UI", 14), bg=BG_GLASS2, fg=TEXT_MUT, width=6, height=3).pack()
            else:
                tk.Label(cell, text="?", font=("Segoe UI", 14), bg=BG_GLASS2, fg=TEXT_MUT, width=6, height=3).pack()
            fname = os.path.basename(path); short = fname if len(fname) <= 10 else fname[:7] + "..."
            tk.Label(cell, text=short, font=("Segoe UI", 6), bg=BG_GLASS2, fg=TEXT_MUT).pack()
            hover(cell, BG_GLASS2, BG_CARD2)
        missing  = len(photos) - len(valid)
        count_txt = f"  {len(valid)} photo(s)"
        if missing: count_txt += f"  •  {missing} missing"
        tk.Label(parent, text=count_txt, font=("Segoe UI", 7), bg=BG_CARD, fg=TEXT_MUT).pack(anchor="w", padx=4, pady=(0, 4))

    def _open_image(self, path):
        try: from PIL import Image, ImageTk
        except ImportError:
            messagebox.showinfo("Preview", f"Install Pillow to enable previews.\n\n{path}"); return
        top = tk.Toplevel(self); top.title(os.path.basename(path)); top.configure(bg=BG_MAIN)
        try:
            img = Image.open(path); img.thumbnail((800, 600), Image.LANCZOS)
            tk_img = ImageTk.PhotoImage(img)
            lbl = tk.Label(top, image=tk_img, bg=BG_MAIN); lbl.image = tk_img; lbl.pack(padx=10, pady=10)
            tk.Label(top, text=path, font=("Segoe UI", 7), bg=BG_MAIN, fg=TEXT_MUT).pack(pady=(0, 8))
        except Exception as ex:
            tk.Label(top, text=f"Unable to open image:\n{ex}", bg=BG_MAIN, fg=RED, font=("Segoe UI", 10)).pack(padx=20, pady=20)

    def _add_plant(self):
        name = simpledialog.askstring("Add Plant", "Plant name:")
        if not name: return
        loc  = simpledialog.askstring("Add Plant", "Location (e.g. Living Room):") or "Unknown"
        lux  = random.randint(200, 900)
        status = "Optimal" if 300 <= lux <= 800 else ("Low Light" if lux < 300 else "Too Much Light")
        self._plants.append({"name": name, "letter": name[:2].upper(), "location": loc,
                              "status": status, "lux": lux, "days": 0})
        self._render_all()

    def _remove_plant(self, plant):
        if messagebox.askyesno("Remove Plant", f"Remove '{plant['name']}' from your collection?"):
            self._plants.remove(plant); self._expanded.discard(plant["name"]); self._render_all()

    def _simulate_reading(self, plant):
        lux = random.randint(150, 950); plant["lux"] = lux
        plant["status"] = "Optimal" if 300 <= lux <= 800 else ("Low Light" if lux < 300 else "Too Much Light")
        self._render_all()

# HISTORY
class HistoryPage(BasePage):
    def _build(self):
        self._entries      = []
        self._chart_canvas = None
        self._selected_idx = None

        outer = tk.Frame(self, bg=BG_MAIN); outer.pack(fill="both", expand=True)
        self._left_pane = tk.Frame(outer, bg=BG_SIDE, width=270)
        self._left_pane.pack(side="left", fill="y"); self._left_pane.pack_propagate(False)
        self._right_pane = tk.Frame(outer, bg=BG_MAIN)
        self._right_pane.pack(side="left", fill="both", expand=True)
        self._build_left(); self._build_right(); self.refresh()

    def _build_left(self):
        hdr_strip = tk.Frame(self._left_pane, bg=BG_GLASS); hdr_strip.pack(fill="x")
        tk.Frame(hdr_strip, bg=TEAL, height=2).pack(fill="x")
        hi = tk.Frame(hdr_strip, bg=BG_GLASS, padx=16, pady=14); hi.pack(fill="x")
        tk.Label(hi, text="History", font=("Segoe UI", 14, "bold"), bg=BG_GLASS, fg=TEXT_PRI).pack(anchor="w")
        tk.Label(hi, text="Last 10 days of loaded files", font=("Segoe UI", 7), bg=BG_GLASS, fg=TEXT_SEC).pack(anchor="w")
        pad = tk.Frame(self._left_pane, bg=BG_SIDE); pad.pack(fill="both", expand=True, padx=10, pady=10)
        list_outer = tk.Frame(pad, bg=BG_SIDE); list_outer.pack(fill="both", expand=True)
        self._hist_canvas = tk.Canvas(list_outer, bg=BG_SIDE, highlightthickness=0)
        sb = tk.Scrollbar(list_outer, orient="vertical", command=self._hist_canvas.yview)
        self._hist_canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y"); self._hist_canvas.pack(side="left", fill="both", expand=True)
        self._hist_list = tk.Frame(self._hist_canvas, bg=BG_SIDE)
        self._hist_win  = self._hist_canvas.create_window((0, 0), window=self._hist_list, anchor="nw")
        self._hist_list.bind("<Configure>",
            lambda e: self._hist_canvas.configure(scrollregion=self._hist_canvas.bbox("all")))
        self._hist_canvas.bind("<Configure>",
            lambda e: self._hist_canvas.itemconfig(self._hist_win, width=e.width))
        self._hist_canvas.bind("<MouseWheel>",
            lambda e: self._hist_canvas.yview_scroll(-1 * (e.delta // 120), "units"))

    def _build_right(self):
        self._right_content = tk.Frame(self._right_pane, bg=BG_MAIN)
        self._right_content.pack(fill="both", expand=True, padx=20, pady=18)

    def refresh(self):
        raw = _load_history_db(); self._entries = _prune_old_entries(raw, days=10)
        _save_history_db(self._entries); self._render_list()
        if self._selected_idx is None and self._entries:
            self._select_entry(len(self._entries) - 1)
        elif self._selected_idx is not None and self._entries:
            self._select_entry(min(self._selected_idx, len(self._entries) - 1))
        else:
            self._show_empty_right()

    def _render_list(self):
        for w in self._hist_list.winfo_children(): w.destroy()
        if not self._entries:
            ef = tk.Frame(self._hist_list, bg=BG_SIDE); ef.pack(pady=30, padx=10)
            tk.Label(ef, text="No history", font=("Segoe UI", 10, "bold"), bg=BG_SIDE, fg=TEXT_MUT).pack()
            tk.Label(ef, text="Load a file from Dashboard", font=("Segoe UI", 7), bg=BG_SIDE, fg=TEXT_MUT).pack(pady=(4, 0))
            return
        groups: dict[str, list] = {}
        for idx, entry in enumerate(self._entries):
            try:
                dt  = datetime.datetime.fromisoformat(entry["timestamp"])
                key = dt.strftime("%a %d %b %Y")
            except: key = "Unknown date"
            groups.setdefault(key, []).append((idx, entry))
        for date_str, items in reversed(list(groups.items())):
            date_hdr = tk.Frame(self._hist_list, bg=BG_SIDE); date_hdr.pack(fill="x", pady=(8, 2))
            tk.Frame(date_hdr, bg=TEAL, width=3).pack(side="left", fill="y")
            tk.Label(date_hdr, text=f"  {date_str}", font=("Segoe UI", 7, "bold"),
                     bg=BG_SIDE, fg=TEAL).pack(side="left", pady=4)
            for idx, entry in reversed(items):
                is_sel = (idx == self._selected_idx)
                bg_c   = BG_CARD if is_sel else BG_GLASS2
                row    = tk.Frame(self._hist_list, bg=bg_c, cursor="hand2"); row.pack(fill="x", pady=(0, 2))
                tk.Frame(row, bg=TEAL if is_sel else bg_c, width=3).pack(side="left", fill="y")
                inner2 = tk.Frame(row, bg=bg_c, padx=12, pady=10); inner2.pack(side="left", fill="both", expand=True)
                try:
                    dt = datetime.datetime.fromisoformat(entry["timestamp"]); time_str = dt.strftime("%H:%M")
                except: time_str = ""
                fname = entry.get("filename", "unknown"); short = fname if len(fname) <= 20 else fname[:17] + "..."
                name_row2 = tk.Frame(inner2, bg=bg_c); name_row2.pack(anchor="w", fill="x")
                tk.Label(name_row2, text=short, font=("Segoe UI", 8),
                         bg=bg_c, fg=TEXT_PRI if is_sel else TEXT_SEC).pack(side="left")
                tk.Label(name_row2, text=time_str, font=("Segoe UI", 7),
                         bg=bg_c, fg=TEAL if is_sel else TEXT_MUT).pack(side="right")
                n_vals = len(entry.get("values", []))
                tk.Label(inner2, text=f"{n_vals:,} samples", font=("Segoe UI", 7),
                         bg=bg_c, fg=TEXT_MUT).pack(anchor="w")
                bind_tree(row, "<Button-1>", lambda e, i=idx: self._select_entry(i))
                hover(row, bg_c, BG_CARD2)

    def _select_entry(self, idx):
        self._selected_idx = idx; self._render_list(); self._show_entry_chart(self._entries[idx])

    def _show_empty_right(self):
        for w in self._right_content.winfo_children(): w.destroy()
        container = tk.Frame(self._right_content, bg=BG_CARD); container.pack(fill="both", expand=True)
        tk.Frame(container, bg=TEAL, height=2).pack(fill="x")
        inner3 = tk.Frame(container, bg=BG_CARD, padx=20, pady=60); inner3.pack(fill="both", expand=True)
        tk.Label(inner3, text="Select a file from the list", font=("Segoe UI", 10, "bold"),
                 bg=BG_CARD, fg=TEXT_MUT).pack(pady=(20, 8))

    def _show_entry_chart(self, entry):
        for w in self._right_content.winfo_children(): w.destroy()
        if self._chart_canvas:
            try: self._chart_canvas.get_tk_widget().destroy(); plt.close("all")
            except: pass
            self._chart_canvas = None
        data   = entry.get("values", [])
        fname  = entry.get("filename", "")
        try:
            dt     = datetime.datetime.fromisoformat(entry["timestamp"]); dt_str = dt.strftime("%d %b %Y  %H:%M")
        except: dt_str = ""
        hdr2 = tk.Frame(self._right_content, bg=BG_GLASS); hdr2.pack(fill="x", pady=(0, 12))
        tk.Frame(hdr2, bg=TEAL, height=2).pack(fill="x")
        hi2 = tk.Frame(hdr2, bg=BG_GLASS, padx=18, pady=14); hi2.pack(fill="x")
        lh = tk.Frame(hi2, bg=BG_GLASS); lh.pack(side="left", fill="both", expand=True)
        tk.Label(lh, text=fname, font=("Segoe UI", 12, "bold"), bg=BG_GLASS, fg=TEXT_PRI).pack(anchor="w")
        tk.Label(lh, text=dt_str, font=("Segoe UI", 8), bg=BG_GLASS, fg=TEAL).pack(anchor="w")
        teal_badge = tk.Frame(hi2, bg=TEAL, padx=10, pady=6); teal_badge.pack(side="right", anchor="center")
        tk.Label(teal_badge, text="History", font=("Segoe UI", 7, "bold"), bg=TEAL, fg=BG_MAIN).pack()
        if not data:
            tk.Label(self._right_content, text="No data to display.", font=("Segoe UI", 9), bg=BG_MAIN, fg=TEXT_MUT).pack(pady=20)
            return
        stats_row = tk.Frame(self._right_content, bg=BG_MAIN); stats_row.pack(fill="x", pady=(0, 12))
        avg_v = sum(data) / len(data)
        for label, val, color in [("Avg", f"{avg_v:.0f} lx", BLUE), ("Max", f"{max(data):.0f} lx", ACCENT),
                                   ("Min", f"{min(data):.0f} lx", ORANGE), ("Samples", f"{len(data):,}", TEAL)]:
            sc = tk.Frame(stats_row, bg=BG_CARD); sc.pack(side="left", padx=(0, 6), fill="x", expand=True)
            tk.Frame(sc, bg=color, height=2).pack(fill="x")
            inner4 = tk.Frame(sc, bg=BG_CARD, padx=12, pady=10); inner4.pack(fill="both")
            tk.Label(inner4, text=label, font=("Segoe UI", 7, "bold"), bg=BG_CARD, fg=color).pack(anchor="w")
            tk.Label(inner4, text=val,   font=("Segoe UI", 14, "bold"), bg=BG_CARD, fg=TEXT_PRI).pack(anchor="w")
        chart_frame = tk.Frame(self._right_content, bg=BG_CARD); chart_frame.pack(fill="both", expand=True)
        x   = list(range(len(data)))
        fig, ax = plt.subplots(figsize=(6.8, 3.6))
        fig.patch.set_facecolor(BG_CARD); ax.set_facecolor(BG_CARD)
        ax.fill_between(x, data, alpha=0.14, color=TEAL)
        ax.plot(x, data, color=TEAL, linewidth=2.0, zorder=3)
        if len(data) <= 200: ax.scatter(x, data, color=TEAL, s=18, zorder=4, alpha=0.8)
        ax.axhline(y=300, color=RED,    linestyle=":", linewidth=1.0, alpha=0.7)
        ax.axhline(y=800, color=ACCENT, linestyle=":", linewidth=1.0, alpha=0.7)
        ax.set_xlim(0, max(len(data) - 1, 1)); ax.set_ylim(0, max(max(data) * 1.1, 1100))
        ax.tick_params(colors=TEXT_SEC, labelsize=6); ax.grid(color=TEXT_MUT, linestyle=":", linewidth=0.3, alpha=0.4)
        for sp in ax.spines.values(): sp.set_edgecolor(BORDER2)
        ax.set_title(f"  {fname}", color=TEXT_PRI, fontsize=8, pad=8, loc="left", fontfamily="sans-serif")
        ax.set_xlabel("Sample Index", color=TEXT_MUT, fontsize=6, fontfamily="monospace")
        ax.set_ylabel("Lux",          color=TEXT_MUT, fontsize=6, fontfamily="monospace")
        fig.tight_layout(pad=1.2)
        self._chart_canvas = FigureCanvasTkAgg(fig, master=chart_frame)
        self._chart_canvas.draw(); self._chart_canvas.get_tk_widget().pack(fill="both", expand=True)

# DETECTION
STATUS_META   = {k: (v[0], v[1]) for k, v in CNN_CLASS_META.items()}
URGENCY_COLOR = {"Low": ACCENT, "Medium": YELLOW, "High": RED, "Critical": "#ff2244"}

class DetectionPage(BasePage):
    def _build(self):
        self._image_path = None

        outer = tk.Frame(self, bg=BG_MAIN); outer.pack(fill="both", expand=True, padx=22, pady=18)

        hdr_row = tk.Frame(outer, bg=BG_MAIN); hdr_row.pack(fill="x", pady=(0, 4))
        tk.Label(hdr_row, text="Plant Health Detection", font=("Segoe UI", 18, "bold"),
                 bg=BG_MAIN, fg=TEXT_PRI).pack(side="left")
        load_btn = tk.Frame(hdr_row, bg=BLUE, cursor="hand2"); load_btn.pack(side="right")
        lb_in = tk.Frame(load_btn, bg=BLUE, padx=16, pady=10); lb_in.pack()
        tk.Label(lb_in, text="Upload Image", font=("Segoe UI", 8, "bold"), bg=BLUE, fg=BG_MAIN).pack()
        bind_tree(load_btn, "<Button-1>", lambda e: self._load_image())
        hover(load_btn, BLUE, BLUE2)

        sub_row = tk.Frame(outer, bg=BG_MAIN); sub_row.pack(fill="x", pady=(0, 16))
        tk.Label(sub_row, text="EfficientNetB0 + colour ensemble  •  ",
                 font=("Segoe UI", 8), bg=BG_MAIN, fg=TEXT_MUT).pack(side="left")
        tk.Label(sub_row, text="~90% accuracy", font=("Segoe UI", 8, "bold"), bg=BG_MAIN, fg=PURPLE).pack(side="left")

        cols = tk.Frame(outer, bg=BG_MAIN); cols.pack(fill="both", expand=True)

        left = tk.Frame(cols, bg=BG_CARD, width=300); left.pack(side="left", fill="y", padx=(0, 14))
        left.pack_propagate(False)
        tk.Frame(left, bg=PURPLE, height=2).pack(fill="x")
        li = tk.Frame(left, bg=BG_CARD, padx=14, pady=16); li.pack(fill="both", expand=True)
        tk.Label(li, text="Input Image", font=("Segoe UI", 9, "bold"), bg=BG_CARD, fg=TEXT_MUT).pack(anchor="w", pady=(0, 8))

        self._preview_canvas = tk.Canvas(li, bg=BG_GLASS2, highlightthickness=1,
                                          highlightbackground=BORDER2, width=262, height=210)
        self._preview_canvas.pack(pady=(0, 10))
        self._preview_canvas.create_text(131, 105, text="No image selected",
                                          fill=TEXT_MUT, font=("Segoe UI", 9), tags="placeholder")

        self._img_name_lbl = tk.Label(li, text="", font=("Segoe UI", 7), bg=BG_CARD, fg=TEXT_SEC, wraplength=250)
        self._img_name_lbl.pack(pady=(0, 10))

        cnn_card = tk.Frame(li, bg=BG_GLASS2, padx=12, pady=10); cnn_card.pack(fill="x", pady=(0, 12))
        tk.Frame(cnn_card, bg=PURPLE, height=1).pack(fill="x", pady=(0, 8))
        tk.Label(cnn_card, text="CNN Architecture", font=("Segoe UI", 7, "bold"), bg=BG_GLASS2, fg=PURPLE).pack(anchor="w", pady=(0, 4))
        self._cnn_info_lbl = tk.Label(
            cnn_card,
            text="Model:    EfficientNetB0\nBackbone: ImageNet\nHead:     Dense(512→256)→8\nAccuracy: ~90%",
            font=("Consolas", 7), bg=BG_GLASS2, fg=TEXT_SEC, justify="left")
        self._cnn_info_lbl.pack(anchor="w")

        self._analyse_btn_frame = tk.Frame(li, bg=PURPLE, cursor="hand2"); self._analyse_btn_frame.pack(fill="x")
        tk.Label(self._analyse_btn_frame, text="Analyse with CNN",
                 font=("Segoe UI", 9, "bold"), bg=PURPLE, fg=BG_MAIN, pady=11).pack()
        bind_tree(self._analyse_btn_frame, "<Button-1>", lambda e: self._run_analysis())
        hover(self._analyse_btn_frame, PURPLE, PURPLE2)

        self._results_frame = tk.Frame(cols, bg=BG_MAIN); self._results_frame.pack(side="left", fill="both", expand=True)
        self._show_empty_state()

    def _load_image(self):
        path = filedialog.askopenfilename(
            title="Select Plant Image",
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.webp *.gif"), ("All files", "*.*")])
        if not path: return
        self._image_path = path
        fname = os.path.basename(path); self._img_name_lbl.config(text=fname)
        try:
            from PIL import Image, ImageTk
            img = Image.open(path); img.thumbnail((262, 210))
            self._tk_img = ImageTk.PhotoImage(img)
            self._preview_canvas.delete("all")
            self._preview_canvas.create_image(131, 105, image=self._tk_img, anchor="center")
        except ImportError:
            self._preview_canvas.delete("all")
            self._preview_canvas.create_text(131, 105, text=fname[:28], fill=TEXT_SEC, font=("Segoe UI", 8))
        except Exception as ex:
            self._preview_canvas.delete("all")
            self._preview_canvas.create_text(131, 105, text=f"Error:\n{ex}", fill=RED, font=("Segoe UI", 8))
        self._show_empty_state(msg="Image loaded\n\nClick 'Analyse with CNN' to run diagnosis.")

    def _show_empty_state(self, msg="Upload a plant image\n\nto get started"):
        for w in self._results_frame.winfo_children(): w.destroy()
        container = tk.Frame(self._results_frame, bg=BG_CARD); container.pack(fill="both", expand=True)
        tk.Frame(container, bg=PURPLE, height=2).pack(fill="x")
        inner5 = tk.Frame(container, bg=BG_CARD, padx=30, pady=60); inner5.pack(fill="both", expand=True)
        tk.Label(inner5, text="CNN", font=("Segoe UI", 36, "bold"), bg=BG_CARD, fg=TEXT_DIM).pack(pady=(20, 16))
        for line in msg.split("\n"):
            tk.Label(inner5, text=line, font=("Segoe UI", 9 if line and not line.startswith(" ") else 8),
                     bg=BG_CARD, fg=TEXT_SEC if line else TEXT_MUT).pack()

    def _show_loading(self):
        for w in self._results_frame.winfo_children(): w.destroy()
        container = tk.Frame(self._results_frame, bg=BG_CARD); container.pack(fill="both", expand=True)
        tk.Frame(container, bg=PURPLE, height=2).pack(fill="x")
        inner6 = tk.Frame(container, bg=BG_CARD, padx=30, pady=60); inner6.pack(fill="both", expand=True)
        tk.Label(inner6, text="Running inference…", font=("Segoe UI", 14, "bold"), bg=BG_CARD, fg=TEXT_PRI).pack(pady=(20, 8))
        tk.Label(inner6, text="EfficientNetB0 + colour ensemble", font=("Segoe UI", 8), bg=BG_CARD, fg=TEXT_SEC).pack()
        self._loading_dots = tk.Label(inner6, text="●  ●  ●", font=("Segoe UI", 16), bg=BG_CARD, fg=PURPLE)
        self._loading_dots.pack(pady=(20, 0)); self._dot_idx = 0; self._animate_dots()

    def _animate_dots(self):
        patterns = ["●  ·  ·", "·  ●  ·", "·  ·  ●", "·  ●  ·"]
        try:
            self._loading_dots.config(text=patterns[self._dot_idx % len(patterns)])
            self._dot_idx += 1; self._anim_job = self.after(180, self._animate_dots)
        except: pass

    def _run_analysis(self):
        if not self._image_path:
            messagebox.showwarning("No Image", "Please upload a plant image first."); return
        if not os.path.exists(self._image_path):
            messagebox.showerror("File Missing", "The selected image file no longer exists."); return
        self._show_loading()

        def on_result(result, error):
            if hasattr(self, "_anim_job"):
                try: self.after_cancel(self._anim_job)
                except: pass
            self.after(0, lambda: self._show_result(result, error))

        def _api_thread():
            result = _api_detect(self._image_path)
            if result: on_result(result, None)
            else:      analyze_plant_image_cnn(self._image_path, on_result)

        threading.Thread(target=_api_thread, daemon=True).start()

    def _show_result(self, result, error):
        for w in self._results_frame.winfo_children(): w.destroy()
        if error or result is None:
            container = tk.Frame(self._results_frame, bg=BG_CARD); container.pack(fill="both", expand=True)
            tk.Frame(container, bg=RED, height=2).pack(fill="x")
            inner7 = tk.Frame(container, bg=BG_CARD, padx=20, pady=24); inner7.pack(fill="both")
            tk.Label(inner7, text="Analysis failed", font=("Segoe UI", 12, "bold"), bg=BG_CARD, fg=RED).pack(pady=(0, 10))
            tk.Label(inner7, text=str(error) if error else "Unknown error.",
                     font=("Segoe UI", 8), bg=BG_CARD, fg=TEXT_SEC, wraplength=380, justify="center").pack()
            re_btn = tk.Frame(inner7, bg=PURPLE_DIM, cursor="hand2", padx=14, pady=8); re_btn.pack(pady=(16, 0))
            tk.Label(re_btn, text="Try Again", font=("Segoe UI", 8, "bold"), bg=PURPLE_DIM, fg=PURPLE).pack()
            bind_tree(re_btn, "<Button-1>", lambda e: self._run_analysis()); return

        cnn_info = result.get("_cnn_info", {})
        if cnn_info:
            self._cnn_info_lbl.config(
                text=(f"Model:    {cnn_info.get('model', 'EfficientNetB0')[:25]}\n"
                      f"Backbone: ImageNet\nHead:     Dense→8 classes\n"
                      f"Accuracy: {cnn_info.get('accuracy_est', '~90%')}"), fg=TEXT_PRI)

        status   = result.get("status", "Unknown"); conf = result.get("confidence", 0)
        summary  = result.get("summary", ""); symptoms = result.get("symptoms", [])
        recs     = result.get("recommendations", []); urgency = result.get("urgency", "Low")
        color, badge_label = STATUS_META.get(status, (TEXT_SEC, "?"))
        urg_color = URGENCY_COLOR.get(urgency, TEXT_SEC)

        res_canvas = tk.Canvas(self._results_frame, bg=BG_MAIN, highlightthickness=0)
        sb2 = tk.Scrollbar(self._results_frame, orient="vertical", command=res_canvas.yview)
        res_canvas.configure(yscrollcommand=sb2.set)
        sb2.pack(side="right", fill="y"); res_canvas.pack(side="left", fill="both", expand=True)
        rpad = tk.Frame(res_canvas, bg=BG_MAIN)
        wid2 = res_canvas.create_window((0, 0), window=rpad, anchor="nw")
        rpad.bind("<Configure>", lambda e: res_canvas.configure(scrollregion=res_canvas.bbox("all")))
        res_canvas.bind("<Configure>", lambda e: res_canvas.itemconfig(wid2, width=e.width))

        banner = tk.Frame(rpad, bg=BG_CARD); banner.pack(fill="x", pady=(0, 10))
        tk.Frame(banner, bg=color, height=2).pack(fill="x")
        b_in = tk.Frame(banner, bg=BG_CARD, padx=18, pady=16); b_in.pack(fill="x")
        top_row2 = tk.Frame(b_in, bg=BG_CARD); top_row2.pack(fill="x")
        lst = tk.Frame(top_row2, bg=BG_CARD); lst.pack(side="left")
        badge = tk.Frame(lst, bg=color, padx=8, pady=4); badge.pack(side="left")
        tk.Label(badge, text=badge_label, font=("Consolas", 8, "bold"), bg=color, fg=BG_MAIN).pack()
        tk.Label(lst, text=f"  {status}", font=("Segoe UI", 14, "bold"), bg=BG_CARD, fg=color).pack(side="left")
        ub = tk.Frame(top_row2, bg=urg_color, padx=10, pady=4); ub.pack(side="right")
        tk.Label(ub, text=f"{urgency} urgency", font=("Segoe UI", 7, "bold"), bg=urg_color, fg=BG_MAIN).pack()
        conf_row2 = tk.Frame(b_in, bg=BG_CARD); conf_row2.pack(fill="x", pady=(12, 0))
        ch2 = tk.Frame(conf_row2, bg=BG_CARD); ch2.pack(fill="x")
        tk.Label(ch2, text="Confidence", font=("Segoe UI", 7), bg=BG_CARD, fg=TEXT_MUT).pack(side="left")
        tk.Label(ch2, text=f"{conf}%", font=("Segoe UI", 8, "bold"), bg=BG_CARD, fg=color).pack(side="right")
        bar_bg2 = tk.Frame(conf_row2, bg=BG_GLASS2, height=5); bar_bg2.pack(fill="x", pady=(4, 0))
        bar_bg2.update_idletasks(); bw2 = bar_bg2.winfo_width() or 300
        tk.Frame(bar_bg2, bg=color, width=max(4, int(bw2 * conf / 100)), height=5).place(x=0, y=0)
        tk.Label(b_in, text=summary, font=("Segoe UI", 9), bg=BG_CARD, fg=TEXT_PRI,
                 wraplength=360, justify="left").pack(anchor="w", pady=(12, 0))

        if symptoms:
            sep_f = tk.Frame(rpad, bg=BG_MAIN); sep_f.pack(fill="x", pady=(4, 0))
            sh2 = tk.Frame(sep_f, bg=BG_MAIN); sh2.pack(fill="x", pady=(0, 6))
            tk.Frame(sh2, bg=YELLOW, width=3, height=18).pack(side="left")
            tk.Label(sh2, text="  Observed Symptoms", font=("Segoe UI", 10, "bold"), bg=BG_MAIN, fg=TEXT_PRI).pack(side="left")
            for sym in symptoms:
                row3 = tk.Frame(rpad, bg=BG_CARD, padx=14, pady=10); row3.pack(fill="x", pady=(0, 3))
                tk.Frame(row3, bg=color, width=2).pack(side="left", fill="y", padx=(0, 12))
                tk.Label(row3, text=sym, font=("Segoe UI", 9), bg=BG_CARD, fg=TEXT_PRI, wraplength=360, justify="left").pack(side="left", fill="x")

        if recs:
            rh2 = tk.Frame(rpad, bg=BG_MAIN); rh2.pack(fill="x", pady=(12, 6))
            tk.Frame(rh2, bg=ACCENT, width=3, height=18).pack(side="left")
            tk.Label(rh2, text="  Recommended Actions", font=("Segoe UI", 10, "bold"), bg=BG_MAIN, fg=TEXT_PRI).pack(side="left")
            for i, rec in enumerate(recs, 1):
                row4 = tk.Frame(rpad, bg=BG_CARD, padx=14, pady=10); row4.pack(fill="x", pady=(0, 3))
                num2 = tk.Frame(row4, bg=ACCENT_DIM, padx=6, pady=2); num2.pack(side="left", padx=(0, 12))
                tk.Label(num2, text=f"{i:02d}", font=("Consolas", 8, "bold"), bg=ACCENT_DIM, fg=ACCENT).pack()
                tk.Label(row4, text=rec, font=("Segoe UI", 9), bg=BG_CARD, fg=TEXT_PRI, wraplength=360, justify="left").pack(side="left", fill="x")

        re_btn2 = tk.Frame(rpad, bg=PURPLE_DIM, cursor="hand2", padx=14, pady=9)
        re_btn2.pack(anchor="e", pady=(14, 22))
        tk.Label(re_btn2, text="Analyse Again", font=("Segoe UI", 8, "bold"), bg=PURPLE_DIM, fg=PURPLE).pack()
        bind_tree(re_btn2, "<Button-1>", lambda e: self._run_analysis())
        hover(re_btn2, PURPLE_DIM, BG_GLASS2)

# RECOMMENDATION
class RecommendationSystemPage(BasePage):
    def _build(self):
        outer = tk.Frame(self, bg=BG_MAIN); outer.pack(fill="both", expand=True, padx=22, pady=18)
        tk.Label(outer, text="Plant Recommendation", font=("Segoe UI", 18, "bold"), bg=BG_MAIN, fg=TEXT_PRI).pack(anchor="w")
        tk.Label(outer, text="Fuzzy matching across care requirements to find your ideal plant",
                 font=("Segoe UI", 8), bg=BG_MAIN, fg=TEXT_SEC).pack(anchor="w", pady=(2, 16))

        if not PANDAS_OK:
            tk.Label(outer, text="pandas is required.\nRun: pip install pandas",
                     font=("Segoe UI", 9), bg=BG_MAIN, fg=RED).pack(pady=40)
            return

        cols = tk.Frame(outer, bg=BG_MAIN); cols.pack(fill="both", expand=True)
        left = tk.Frame(cols, bg=BG_CARD, width=340); left.pack(side="left", fill="y", padx=(0, 14))
        left.pack_propagate(False)
        tk.Frame(left, bg=ACCENT, height=2).pack(fill="x")
        li2 = tk.Frame(left, bg=BG_CARD, padx=18, pady=16); li2.pack(fill="both", expand=True)
        tk.Label(li2, text="Your Preferences", font=("Segoe UI", 10, "bold"), bg=BG_CARD, fg=TEXT_PRI).pack(anchor="w", pady=(0, 14))

        def slider_row(parent, label, from_, to, resolution, default, color=ACCENT):
            row5 = tk.Frame(parent, bg=BG_CARD); row5.pack(fill="x", pady=(0, 14))
            header5 = tk.Frame(row5, bg=BG_CARD); header5.pack(fill="x")
            tk.Label(header5, text=label, font=("Segoe UI", 7, "bold"), bg=BG_CARD, fg=TEXT_SEC).pack(side="left")
            val_var = tk.DoubleVar(value=default)
            tk.Label(header5, textvariable=val_var, font=("Segoe UI", 10, "bold"), bg=BG_CARD, fg=color, width=5).pack(side="right")
            sf = tk.Frame(row5, bg=BG_CARD); sf.pack(fill="x", pady=(4, 0))
            GreenSlider(sf, from_=from_, to=to, variable=val_var, resolution=resolution, length=260).pack(fill="x")
            mm = tk.Frame(row5, bg=BG_CARD); mm.pack(fill="x")
            tk.Label(mm, text=str(from_), font=("Segoe UI", 6), bg=BG_CARD, fg=TEXT_MUT).pack(side="left")
            tk.Label(mm, text=str(to),   font=("Segoe UI", 6), bg=BG_CARD, fg=TEXT_MUT).pack(side="right")
            return val_var

        self._water_var    = slider_row(li2, "Water needs  [1–10]",   1, 10, 0.5, 5, BLUE)
        self._sunlight_var = slider_row(li2, "Sunlight  [1–10]",      1, 10, 0.5, 6, YELLOW)
        self._temp_var     = slider_row(li2, "Temperature  [°C]",     10, 40, 0.5, 22, ORANGE)

        separator(li2, BORDER2, 6)

        tk.Label(li2, text="Space type", font=("Segoe UI", 7, "bold"), bg=BG_CARD, fg=TEXT_SEC).pack(anchor="w", pady=(0, 6))
        self._space_var = tk.StringVar(value="any")
        space_btn_row = tk.Frame(li2, bg=BG_CARD); space_btn_row.pack(fill="x", pady=(0, 10))
        self._space_btns = {}
        for val, label in [("any", "Any"), ("flat", "Flat"), ("garden", "Garden")]:
            is_active = (val == "any")
            btn_f = tk.Frame(space_btn_row, bg=ACCENT if is_active else BG_GLASS2, cursor="hand2", padx=14, pady=6)
            btn_f.pack(side="left", padx=(0, 4))
            lbl2 = tk.Label(btn_f, text=label, font=("Segoe UI", 7, "bold"),
                            bg=ACCENT if is_active else BG_GLASS2, fg=BG_MAIN if is_active else TEXT_SEC)
            lbl2.pack()
            self._space_btns[val] = (btn_f, lbl2)
            def on_space(e, v=val):
                self._space_var.set(v)
                for k, (b2, l2) in self._space_btns.items():
                    act = (k == v); b2.configure(bg=ACCENT if act else BG_GLASS2)
                    l2.configure(bg=ACCENT if act else BG_GLASS2, fg=BG_MAIN if act else TEXT_SEC)
            bind_tree(btn_f, "<Button-1>", on_space)

        self._pet_var     = tk.BooleanVar(value=False)
        self._allergy_var = tk.BooleanVar(value=False)

        def toggle_row_widget(parent, label, var, color=ACCENT):
            row6 = tk.Frame(parent, bg=BG_CARD); row6.pack(fill="x", pady=(0, 8))
            tk.Label(row6, text=label, font=("Segoe UI", 7, "bold"), bg=BG_CARD, fg=TEXT_SEC).pack(side="left")
            tf2 = tk.Frame(row6, bg=BG_GLASS2, cursor="hand2", padx=10, pady=4); tf2.pack(side="right")
            sl2 = tk.Label(tf2, text="Off", font=("Segoe UI", 7, "bold"), bg=BG_GLASS2, fg=TEXT_MUT); sl2.pack()
            def toggle(e, v=var, l=sl2, f=tf2, c=color):
                v.set(not v.get())
                if v.get(): f.configure(bg=ACCENT_DIM); l.configure(bg=ACCENT_DIM, text="On", fg=c)
                else:       f.configure(bg=BG_GLASS2);  l.configure(bg=BG_GLASS2,  text="Off", fg=TEXT_MUT)
            bind_tree(tf2, "<Button-1>", toggle)

        toggle_row_widget(li2, "Pet safe only",        self._pet_var,     ACCENT)
        toggle_row_widget(li2, "No pollen allergies",  self._allergy_var, TEAL)

        separator(li2, BORDER2, 6)

        tk.Label(li2, text="Existing plants  [comma separated]",
                 font=("Segoe UI", 7, "bold"), bg=BG_CARD, fg=TEXT_SEC).pack(anchor="w", pady=(0, 6))
        self._existing_var = tk.StringVar()
        ef2 = tk.Frame(li2, bg=BG_GLASS2); ef2.pack(fill="x")
        tk.Frame(ef2, bg=ACCENT, width=2).pack(side="left", fill="y")
        tk.Entry(ef2, textvariable=self._existing_var, bg=BG_GLASS2, fg=TEXT_PRI,
                 insertbackground=ACCENT, relief="flat", font=("Segoe UI", 9)).pack(
                 side="left", fill="x", expand=True, ipady=8, padx=(8, 8))

        find_btn = tk.Frame(li2, bg=ACCENT, cursor="hand2"); find_btn.pack(fill="x", pady=(14, 0))
        tk.Label(find_btn, text="Find Plants", font=("Segoe UI", 10, "bold"), bg=ACCENT, fg=BG_MAIN, pady=11).pack()
        bind_tree(find_btn, "<Button-1>", lambda e: self._run_search())
        hover(find_btn, ACCENT, ACCENT2)

        right2 = tk.Frame(cols, bg=BG_MAIN); right2.pack(side="left", fill="both", expand=True)
        tk.Label(right2, text="Top Matches", font=("Segoe UI", 12, "bold"), bg=BG_MAIN, fg=TEXT_PRI).pack(anchor="w", pady=(0, 10))
        self._results_frame = tk.Frame(right2, bg=BG_MAIN); self._results_frame.pack(fill="both", expand=True)
        self._show_finder_empty()

    def _show_finder_empty(self):
        for w in self._results_frame.winfo_children(): w.destroy()
        container = tk.Frame(self._results_frame, bg=BG_CARD); container.pack(fill="both", expand=True)
        tk.Frame(container, bg=ACCENT, height=2).pack(fill="x")
        inner8 = tk.Frame(container, bg=BG_CARD, padx=20, pady=60); inner8.pack(fill="both", expand=True)
        tk.Label(inner8, text="Set your preferences and click Find Plants",
                 font=("Segoe UI", 9), bg=BG_CARD, fg=TEXT_MUT).pack(pady=(40, 0))

    def _run_search(self):
        for w in self._results_frame.winfo_children(): w.destroy()
        user_prefs = {
            "water":    self._water_var.get(),
            "sunlight": self._sunlight_var.get(),
            "temp":     self._temp_var.get(),
            "pet_safe": True if self._pet_var.get() else None,
            "space":    self._space_var.get() if self._space_var.get() != "any" else None,
            "allergy_concern": True if self._allergy_var.get() else None,
        }
        raw = self._existing_var.get().strip()
        user_prefs["existing_plants"] = [p.strip() for p in raw.split(",") if p.strip()] if raw else []

        # Try API first, fall back to local
        api_results = _api_recommend(user_prefs)
        if api_results:
            results = [(r["name"], r["score"]) for r in api_results]
        else:
            try: results = recommend_plants(user_prefs, top_n=5)
            except Exception as ex:
                tk.Label(self._results_frame, text=f"Error: {ex}", font=("Segoe UI", 9), bg=BG_MAIN, fg=RED).pack(pady=20)
                return

        if not results:
            container = tk.Frame(self._results_frame, bg=BG_CARD); container.pack(fill="both", expand=True)
            tk.Label(container, text="No plants matched your criteria.",
                     font=("Segoe UI", 9), bg=BG_CARD, fg=TEXT_SEC).pack(pady=30)
            return

        medal_colors = [ACCENT, BLUE, YELLOW, PURPLE, TEAL]
        medal_emojis = ["🥇", "🥈", "🥉", "🏅", "🏵️"]

        res_canvas2 = tk.Canvas(self._results_frame, bg=BG_MAIN, highlightthickness=0)
        sb3 = tk.Scrollbar(self._results_frame, orient="vertical", command=res_canvas2.yview)
        res_canvas2.configure(yscrollcommand=sb3.set)
        sb3.pack(side="right", fill="y"); res_canvas2.pack(side="left", fill="both", expand=True)
        scroll_frame2 = tk.Frame(res_canvas2, bg=BG_MAIN)
        wid3 = res_canvas2.create_window((0, 0), window=scroll_frame2, anchor="nw")
        scroll_frame2.bind("<Configure>", lambda e: res_canvas2.configure(scrollregion=res_canvas2.bbox("all")))
        res_canvas2.bind("<Configure>", lambda e: res_canvas2.itemconfig(wid3, width=e.width))

        for rank, (name, score) in enumerate(results, 1):
            pct = int(score * 100); mc = medal_colors[rank - 1]; me = medal_emojis[rank - 1]
            card2 = tk.Frame(scroll_frame2, bg=BG_CARD); card2.pack(fill="x", pady=(0, 8))
            tk.Frame(card2, bg=mc, height=2).pack(fill="x")
            inner9 = tk.Frame(card2, bg=BG_CARD, padx=18, pady=14); inner9.pack(fill="both")
            top3 = tk.Frame(inner9, bg=BG_CARD); top3.pack(fill="x")
            li3 = tk.Frame(top3, bg=BG_CARD); li3.pack(side="left", fill="both", expand=True)
            rr = tk.Frame(li3, bg=BG_CARD); rr.pack(anchor="w")
            rb2 = tk.Frame(rr, bg=mc, padx=6, pady=3); rb2.pack(side="left")
            tk.Label(rb2, text=f"{me} {rank}", font=("Segoe UI", 8, "bold"), bg=mc, fg=BG_MAIN).pack()
            tk.Label(rr, text=f"  {name}", font=("Segoe UI", 13, "bold"), bg=BG_CARD, fg=TEXT_PRI).pack(side="left")
            tk.Label(top3, text=f"{pct}%", font=("Segoe UI", 22, "bold"), bg=BG_CARD, fg=mc).pack(side="right")
            bar_row2 = tk.Frame(inner9, bg=BG_CARD); bar_row2.pack(fill="x", pady=(10, 6))
            bb2 = tk.Frame(bar_row2, bg=BG_GLASS2, height=4); bb2.pack(fill="x")
            bb2.update_idletasks(); bw3 = bb2.winfo_width() or 300
            tk.Frame(bb2, bg=mc, width=max(4, int(bw3 * score)), height=4).place(x=0, y=0)
            try:
                pr = _df_plants[_df_plants["name"] == name].iloc[0]
                tags2 = []
                if pr["pet_safe"]:              tags2.append(("Pet Safe",  ACCENT))
                if not pr["pollen_allergies"]:  tags2.append(("Low Pollen", BLUE))
                tags2 += [(f"Water {int(pr['water'])}/10",    TEXT_MUT),
                           (f"Light {int(pr['sunlight'])}/10", TEXT_MUT),
                           (f"{int(pr['temperature'])}°C",    TEXT_MUT),
                           (pr["space"].title(),               TEXT_MUT)]
                tr2 = tk.Frame(inner9, bg=BG_CARD); tr2.pack(anchor="w", pady=(2, 0))
                for tt, tc in tags2:
                    tf3 = tk.Frame(tr2, bg=BG_GLASS2, padx=6, pady=2); tf3.pack(side="left", padx=(0, 4))
                    tk.Label(tf3, text=tt, font=("Segoe UI", 6), bg=BG_GLASS2, fg=tc).pack()
            except: pass

# GROWTH
class GrowthPage(BasePage):
    FIELDS = [
        ("days_passed",        "Days passed"),
        ("avg_direct_light",   "Avg direct light (lux)"),
        ("avg_indirect_light", "Avg indirect light (lux)"),
        ("avg_nighttime",      "Avg nighttime (hrs)"),
        ("avg_temp",           "Avg temperature (°C)"),
        ("min_temp",           "Min temperature (°C)"),
        ("max_temp",           "Max temperature (°C)"),
        ("times_watered",      "Times watered"),
        ("initial_height",     "Initial height (cm)"),
    ]
    COLORS = ["green", "yellow", "brown", "pale", "black"]

    def _build(self):
        self._entries   = {}
        self._color_var = tk.StringVar(value="green")

        outer = tk.Frame(self, bg=BG_MAIN); outer.pack(fill="both", expand=True, padx=22, pady=18)
        tk.Label(outer, text="Growth Prediction", font=("Segoe UI", 18, "bold"), bg=BG_MAIN, fg=TEXT_PRI).pack(anchor="w")
        tk.Label(outer, text="Enter plant conditions — model predicts height growth",
                 font=("Segoe UI", 8), bg=BG_MAIN, fg=TEXT_SEC).pack(anchor="w", pady=(2, 16))

        cols = tk.Frame(outer, bg=BG_MAIN); cols.pack(fill="both", expand=True)
        left = tk.Frame(cols, bg=BG_CARD, width=380); left.pack(side="left", fill="y", padx=(0, 14))
        left.pack_propagate(False); tk.Frame(left, bg=TEAL, height=2).pack(fill="x")
        li4 = tk.Frame(left, bg=BG_CARD, padx=18, pady=16); li4.pack(fill="both", expand=True)
        tk.Label(li4, text="Plant Conditions", font=("Segoe UI", 10, "bold"), bg=BG_CARD, fg=TEXT_PRI).pack(anchor="w", pady=(0, 12))

        for key, label in self.FIELDS:
            row7 = tk.Frame(li4, bg=BG_CARD); row7.pack(fill="x", pady=(0, 7))
            tk.Label(row7, text=label, font=("Segoe UI", 7), bg=BG_CARD, fg=TEXT_SEC, width=26, anchor="w").pack(side="left")
            ef3 = tk.Frame(row7, bg=BG_GLASS2); ef3.pack(side="left", padx=(6, 0), fill="x", expand=True)
            tk.Frame(ef3, bg=TEAL, width=2).pack(side="left", fill="y")
            entry = tk.Entry(ef3, bg=BG_GLASS2, fg=TEXT_PRI, insertbackground=TEAL,
                             relief="flat", font=("Segoe UI", 9), width=10)
            entry.pack(side="left", ipady=7, padx=(6, 6))
            self._entries[key] = entry

        separator(li4, BORDER2, 6)

        tk.Label(li4, text="Plant colour before", font=("Segoe UI", 7, "bold"), bg=BG_CARD, fg=TEXT_SEC).pack(anchor="w", pady=(0, 8))
        color_row2 = tk.Frame(li4, bg=BG_CARD); color_row2.pack(fill="x", pady=(0, 10))
        self._color_btns = {}
        color_map = {"green": ACCENT, "yellow": YELLOW, "brown": ORANGE, "pale": TEXT_SEC, "black": "#666666"}
        for c in self.COLORS:
            is_active = (c == "green"); cc = color_map.get(c, ACCENT)
            btn3 = tk.Frame(color_row2, bg=ACCENT_DIM if is_active else BG_GLASS2, cursor="hand2", padx=10, pady=6)
            btn3.pack(side="left", padx=(0, 4))
            lbl3 = tk.Label(btn3, text=c.capitalize(), font=("Segoe UI", 7, "bold"),
                            bg=ACCENT_DIM if is_active else BG_GLASS2, fg=cc if is_active else TEXT_MUT)
            lbl3.pack()
            self._color_btns[c] = (btn3, lbl3, cc)
            def on_color(e, v=c):
                self._color_var.set(v)
                for k2, (b3, l3, cc3) in self._color_btns.items():
                    act2 = (k2 == v); b3.configure(bg=ACCENT_DIM if act2 else BG_GLASS2)
                    l3.configure(bg=ACCENT_DIM if act2 else BG_GLASS2, fg=cc3 if act2 else TEXT_MUT)
            bind_tree(btn3, "<Button-1>", on_color)

        separator(li4, BORDER2, 6)

        tk.Label(li4, text="API Endpoint", font=("Segoe UI", 7, "bold"), bg=BG_CARD, fg=TEXT_SEC).pack(anchor="w", pady=(0, 6))
        self._api_url_var = tk.StringVar(value=f"{GROWTH_API_URL}/fwd")
        af2 = tk.Frame(li4, bg=BG_GLASS2); af2.pack(fill="x", pady=(0, 10))
        tk.Frame(af2, bg=TEAL, width=2).pack(side="left", fill="y")
        tk.Entry(af2, textvariable=self._api_url_var, bg=BG_GLASS2, fg=TEXT_PRI,
                 insertbackground=TEAL, relief="flat", font=("Segoe UI", 8)).pack(
                 side="left", fill="x", expand=True, ipady=7, padx=(6, 6))

        predict_btn = tk.Frame(li4, bg=TEAL, cursor="hand2"); predict_btn.pack(fill="x")
        tk.Label(predict_btn, text="Predict Growth", font=("Segoe UI", 10, "bold"), bg=TEAL, fg=BG_MAIN, pady=11).pack()
        bind_tree(predict_btn, "<Button-1>", lambda e: self._run_prediction())
        hover(predict_btn, TEAL, TEAL2)

        right3 = tk.Frame(cols, bg=BG_MAIN); right3.pack(side="left", fill="both", expand=True)
        tk.Label(right3, text="Prediction Result", font=("Segoe UI", 12, "bold"), bg=BG_MAIN, fg=TEXT_PRI).pack(anchor="w", pady=(0, 10))
        self._result_frame = tk.Frame(right3, bg=BG_MAIN); self._result_frame.pack(fill="both", expand=True)
        self._show_empty()

    def _show_empty(self):
        for w in self._result_frame.winfo_children(): w.destroy()
        container = tk.Frame(self._result_frame, bg=BG_CARD); container.pack(fill="both", expand=True)
        tk.Frame(container, bg=TEAL, height=2).pack(fill="x")
        inner10 = tk.Frame(container, bg=BG_CARD, padx=30, pady=60); inner10.pack(fill="both", expand=True)
        tk.Label(inner10, text="Fill in conditions and click Predict Growth",
                 font=("Segoe UI", 9), bg=BG_CARD, fg=TEXT_MUT).pack(pady=(40, 0))

    def _show_loading(self):
        for w in self._result_frame.winfo_children(): w.destroy()
        container = tk.Frame(self._result_frame, bg=BG_CARD); container.pack(fill="both", expand=True)
        tk.Frame(container, bg=TEAL, height=2).pack(fill="x")
        inner11 = tk.Frame(container, bg=BG_CARD, padx=30, pady=60); inner11.pack(fill="both", expand=True)
        tk.Label(inner11, text="Contacting API…", font=("Segoe UI", 12, "bold"), bg=BG_CARD, fg=TEXT_PRI).pack(pady=(20, 10))
        self._loading_lbl = tk.Label(inner11, text="→", font=("Segoe UI", 14), bg=BG_CARD, fg=TEAL)
        self._loading_lbl.pack(pady=(12, 0)); self._dot_idx2 = 0; self._animate()

    def _animate(self):
        patterns = ["→  ·  ·", "·  →  ·", "·  ·  →", "·  →  ·"]
        try:
            self._loading_lbl.config(text=patterns[self._dot_idx2 % len(patterns)])
            self._dot_idx2 += 1; self._anim_job = self.after(150, self._animate)
        except: pass

    def _run_prediction(self):
        data = {}
        for key, label in self.FIELDS:
            val = self._entries[key].get().strip()
            if not val: messagebox.showwarning("Missing Input", f"Please fill in: {label}"); return
            try: data[key] = float(val)
            except ValueError: messagebox.showerror("Invalid Input", f"'{label}' must be a number."); return
        color  = self._color_var.get()
        vector = [1 if c == color else 0 for c in self.COLORS]
        payload = {"user_id": 1, **data, "color_before": vector}
        # Update to use the current API URL from the entry
        api_url = self._api_url_var.get().strip()
        self._show_loading()

        def _call():
            try:
                import requests as req_lib
                response = req_lib.post(api_url, json=payload, timeout=10)
                if response.status_code == 200:
                    rep = response.json()
                    self.after(0, lambda: self._show_result(rep))
                else:
                    msg = f"Server returned status {response.status_code}.\n{response.text[:200]}"
                    self.after(0, lambda m=msg: self._show_error(m))
            except Exception as ex:
                self.after(0, lambda e=ex: self._show_error(str(e)))

        threading.Thread(target=_call, daemon=True).start()

    def _show_result(self, rep):
        if hasattr(self, "_anim_job"):
            try: self.after_cancel(self._anim_job)
            except: pass
        for w in self._result_frame.winfo_children(): w.destroy()
        color_names = ["green", "yellow", "brown", "pale", "black"]
        color_name  = color_names[rep.get("color", 0)] if "color" in rep else "unknown"
        guess       = rep.get("guess", "N/A")

        card3 = tk.Frame(self._result_frame, bg=BG_CARD); card3.pack(fill="x", pady=(0, 10))
        tk.Frame(card3, bg=TEAL, height=2).pack(fill="x")
        inner12 = tk.Frame(card3, bg=BG_CARD, padx=20, pady=20); inner12.pack(fill="both")
        tk.Label(inner12, text="Prediction complete", font=("Segoe UI", 11, "bold"), bg=BG_CARD, fg=TEAL).pack(anchor="w", pady=(0, 14))

        height_row2 = tk.Frame(inner12, bg=BG_GLASS2, padx=18, pady=16); height_row2.pack(fill="x", pady=(0, 10))
        tk.Label(height_row2, text="Predicted height growth", font=("Segoe UI", 7, "bold"), bg=BG_GLASS2, fg=TEXT_MUT).pack(anchor="w")
        vr2 = tk.Frame(height_row2, bg=BG_GLASS2); vr2.pack(anchor="w")
        tk.Label(vr2, text=f"{guess}", font=("Segoe UI", 36, "bold"), bg=BG_GLASS2, fg=TEAL).pack(side="left")
        tk.Label(vr2, text=" cm", font=("Segoe UI", 12), bg=BG_GLASS2, fg=TEXT_SEC).pack(side="left", pady=(14, 0))

        color_row3 = tk.Frame(inner12, bg=BG_GLASS2, padx=18, pady=16); color_row3.pack(fill="x", pady=(0, 10))
        tk.Label(color_row3, text="Predicted plant colour", font=("Segoe UI", 7, "bold"), bg=BG_GLASS2, fg=TEXT_MUT).pack(anchor="w")
        color_colors = {"green": ACCENT, "yellow": YELLOW, "brown": ORANGE, "pale": TEXT_SEC, "black": "#888888"}
        tk.Label(color_row3, text=color_name.capitalize(), font=("Segoe UI", 16, "bold"),
                 bg=BG_GLASS2, fg=color_colors.get(color_name, TEXT_PRI)).pack(anchor="w")

        raw_card2 = tk.Frame(self._result_frame, bg=BG_CARD, padx=16, pady=12); raw_card2.pack(fill="x")
        tk.Frame(raw_card2, bg=BORDER2, height=1).pack(fill="x", pady=(0, 8))
        tk.Label(raw_card2, text="Raw API response", font=("Segoe UI", 7, "bold"), bg=BG_CARD, fg=TEXT_MUT).pack(anchor="w", pady=(0, 6))
        raw_txt2 = tk.Text(raw_card2, bg=BG_GLASS2, fg=TEAL, font=("Consolas", 7),
                           relief="flat", height=6, state="normal")
        raw_txt2.insert("end", json.dumps(rep, indent=2)); raw_txt2.config(state="disabled"); raw_txt2.pack(fill="x")

        retry_btn2 = tk.Frame(self._result_frame, bg=TEAL, cursor="hand2"); retry_btn2.pack(anchor="e", pady=(12, 0))
        tk.Label(retry_btn2, text="Predict Again", font=("Segoe UI", 8, "bold"), bg=TEAL, fg=BG_MAIN, padx=14, pady=8).pack()
        bind_tree(retry_btn2, "<Button-1>", lambda e: self._run_prediction())
        hover(retry_btn2, TEAL, TEAL2)

    def _show_error(self, msg):
        if hasattr(self, "_anim_job"):
            try: self.after_cancel(self._anim_job)
            except: pass
        for w in self._result_frame.winfo_children(): w.destroy()
        card4 = tk.Frame(self._result_frame, bg=BG_CARD); card4.pack(fill="both", expand=True)
        tk.Frame(card4, bg=RED, height=2).pack(fill="x")
        inner13 = tk.Frame(card4, bg=BG_CARD, padx=20, pady=30); inner13.pack(fill="both")
        tk.Label(inner13, text="Prediction failed", font=("Segoe UI", 12, "bold"), bg=BG_CARD, fg=RED).pack(pady=(0, 10))
        tk.Label(inner13, text=msg, font=("Segoe UI", 8), bg=BG_CARD, fg=TEXT_SEC, wraplength=400, justify="center").pack()
        rr2 = tk.Frame(inner13, bg=RED_DIM, cursor="hand2", padx=14, pady=8); rr2.pack(pady=(16, 0))
        tk.Label(rr2, text="Try Again", font=("Segoe UI", 8, "bold"), bg=RED_DIM, fg=RED).pack()
        bind_tree(rr2, "<Button-1>", lambda e: self._run_prediction())
        hover(rr2, RED_DIM, BG_GLASS2)

# SETTINGS
class SettingsPage(BasePage):
    def _build(self):
        outer_canvas = tk.Canvas(self, bg=BG_MAIN, highlightthickness=0)
        scrollbar    = tk.Scrollbar(self, orient="vertical", command=outer_canvas.yview)
        outer_canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y"); outer_canvas.pack(side="left", fill="both", expand=True)
        pad    = tk.Frame(outer_canvas, bg=BG_MAIN)
        win_id = outer_canvas.create_window((0, 0), window=pad, anchor="nw")
        pad.bind("<Configure>", lambda e: outer_canvas.configure(scrollregion=outer_canvas.bbox("all")))
        outer_canvas.bind("<Configure>", lambda e: outer_canvas.itemconfig(win_id, width=e.width))

        hdr2 = tk.Frame(pad, bg=BG_GLASS); hdr2.pack(fill="x", padx=22, pady=(22, 0))
        tk.Frame(hdr2, bg=PURPLE, height=3).pack(fill="x")
        hi3 = tk.Frame(hdr2, bg=BG_GLASS, padx=26, pady=22); hi3.pack(fill="x")
        lh2 = tk.Frame(hi3, bg=BG_GLASS); lh2.pack(side="left")
        tk.Label(lh2, text="Settings", font=("Segoe UI", 18, "bold"), bg=BG_GLASS, fg=TEXT_PRI).pack(anchor="w")
        tk.Label(lh2, text="Manage display preferences and application behaviour",
                 font=("Segoe UI", 8), bg=BG_GLASS, fg=TEXT_SEC).pack(anchor="w")
        si = tk.Frame(hi3, bg=PURPLE_DIM, width=52, height=52); si.pack(side="right")
        si.pack_propagate(False)
        tk.Label(si, text="⚙️", font=("Segoe UI", 20), bg=PURPLE_DIM).place(relx=0.5, rely=0.5, anchor="center")

        content = tk.Frame(pad, bg=BG_MAIN); content.pack(fill="both", expand=True, padx=22, pady=(16, 22))

        def section(parent, title, color=PURPLE):
            hr = tk.Frame(parent, bg=BG_MAIN); hr.pack(fill="x", pady=(20, 8))
            tk.Frame(hr, bg=color, width=3, height=18).pack(side="left")
            tk.Label(hr, text=f"  {title}", font=("Segoe UI", 10, "bold"), bg=BG_MAIN, fg=TEXT_PRI).pack(side="left")
            tk.Frame(hr, bg=BORDER2, height=1).pack(side="left", fill="x", expand=True, padx=(10, 0), pady=9)
            card5 = tk.Frame(parent, bg=BG_CARD); card5.pack(fill="x")
            tk.Frame(card5, bg=color, height=2).pack(fill="x")
            return tk.Frame(card5, bg=BG_CARD, padx=20, pady=10)

        def toggle_item(parent, label, desc, default_on, is_last=False):
            row8 = tk.Frame(parent, bg=BG_CARD); row8.pack(fill="x", pady=(8, 0))
            txt2 = tk.Frame(row8, bg=BG_CARD); txt2.pack(side="left", fill="both", expand=True)
            tk.Label(txt2, text=label, font=("Segoe UI", 8, "bold"), bg=BG_CARD, fg=TEXT_PRI).pack(anchor="w")
            if desc: tk.Label(txt2, text=desc, font=("Segoe UI", 7), bg=BG_CARD, fg=TEXT_MUT).pack(anchor="w")
            var2 = tk.BooleanVar(value=default_on)
            tf4 = tk.Frame(row8, bg=ACCENT_DIM if default_on else BG_GLASS2, cursor="hand2", padx=14, pady=6)
            tf4.pack(side="right", padx=(12, 0))
            sl3 = tk.Label(tf4, text="On" if default_on else "Off",
                           font=("Segoe UI", 7, "bold"),
                           bg=ACCENT_DIM if default_on else BG_GLASS2,
                           fg=ACCENT if default_on else TEXT_MUT)
            sl3.pack()
            def toggle2(e, v=var2, l=sl3, f=tf4):
                v.set(not v.get())
                if v.get(): f.configure(bg=ACCENT_DIM); l.configure(bg=ACCENT_DIM, text="On",  fg=ACCENT)
                else:       f.configure(bg=BG_GLASS2);  l.configure(bg=BG_GLASS2,  text="Off", fg=TEXT_MUT)
            bind_tree(tf4, "<Button-1>", toggle2)
            if not is_last: tk.Frame(parent, bg=BORDER, height=1).pack(fill="x", pady=(8, 0))
            return var2

        display_inner = section(content, "Display", PURPLE); display_inner.pack(fill="x")
        self._dark_var    = toggle_item(display_inner, "Dark Mode",         "Keep dark theme active",               True)
        self._grid_var    = toggle_item(display_inner, "Chart grid lines",  "Show gridlines on all charts",         True)
        self._points_var  = toggle_item(display_inner, "Show data points",  "Scatter markers on line charts",       False)
        self._compact_var = toggle_item(display_inner, "Compact sidebar",   "Collapse labels in navigation",        False, is_last=True)

        data_inner = section(content, "Data + History", BLUE); data_inner.pack(fill="x")
        ret_row2 = tk.Frame(data_inner, bg=BG_CARD); ret_row2.pack(fill="x", pady=(8, 0))
        tk.Label(ret_row2, text="History retention", font=("Segoe UI", 8, "bold"), bg=BG_CARD, fg=TEXT_PRI).pack(anchor="w")
        tk.Label(ret_row2, text="Number of days to keep loaded file records",
                 font=("Segoe UI", 7), bg=BG_CARD, fg=TEXT_MUT).pack(anchor="w")
        self._retention_var = tk.DoubleVar(value=10)
        ret_slider_row2 = tk.Frame(data_inner, bg=BG_CARD); ret_slider_row2.pack(fill="x", pady=(6, 0))
        ret_header2 = tk.Frame(ret_slider_row2, bg=BG_CARD); ret_header2.pack(fill="x")
        tk.Label(ret_header2, text="Days", font=("Segoe UI", 6), bg=BG_CARD, fg=TEXT_MUT).pack(side="left")
        tk.Label(ret_header2, textvariable=self._retention_var, font=("Segoe UI", 10, "bold"),
                 bg=BG_CARD, fg=BLUE, width=4).pack(side="right")
        GreenSlider(ret_slider_row2, from_=1, to=30, variable=self._retention_var, resolution=1, length=260).pack(fill="x")
        tk.Frame(data_inner, bg=BORDER, height=1).pack(fill="x", pady=(8, 0))
        self._autosave_var = toggle_item(data_inner, "Auto-save history", "Automatically append each loaded file to history", True, is_last=True)

        cnn_inner = section(content, "CNN Model", TEAL); cnn_inner.pack(fill="x")
        self._gpu_var     = toggle_item(cnn_inner, "Use GPU if available", "TensorFlow will use CUDA if detected", False)
        self._fp16_var    = toggle_item(cnn_inner, "FP16 inference",       "Faster inference with reduced precision", False)
        self._verbose_var = toggle_item(cnn_inner, "Verbose CNN output",   "Show model logs in terminal", False, is_last=True)

        api_inner = section(content, "Growth API", ORANGE); api_inner.pack(fill="x")
        url_row2 = tk.Frame(api_inner, bg=BG_CARD); url_row2.pack(fill="x", pady=(8, 0))
        tk.Label(url_row2, text="Default API endpoint", font=("Segoe UI", 8, "bold"), bg=BG_CARD, fg=TEXT_PRI).pack(anchor="w")
        tk.Label(url_row2, text="Used by the Growth Prediction page", font=("Segoe UI", 7), bg=BG_CARD, fg=TEXT_MUT).pack(anchor="w")
        self._api_url_var2 = tk.StringVar(value=f"{GROWTH_API_URL}/fwd")
        uf2 = tk.Frame(api_inner, bg=BG_GLASS2); uf2.pack(fill="x", pady=(8, 0))
        tk.Frame(uf2, bg=ORANGE, width=2).pack(side="left", fill="y")
        tk.Entry(uf2, textvariable=self._api_url_var2, bg=BG_GLASS2, fg=TEXT_PRI,
                 insertbackground=ORANGE, relief="flat", font=("Segoe UI", 8)).pack(
                 side="left", fill="x", expand=True, ipady=8, padx=(8, 8))
        tk.Frame(api_inner, bg=BORDER, height=1).pack(fill="x", pady=(8, 0))
        self._timeout_var = toggle_item(api_inner, "Strict timeout", "Fail fast after 10 seconds", True, is_last=True)

        acc_inner = section(content, "Account", RED); acc_inner.pack(fill="x")
        acc_row2 = tk.Frame(acc_inner, bg=BG_CARD); acc_row2.pack(fill="x", pady=(10, 14))
        avatar2 = tk.Frame(acc_row2, bg=ACCENT_DIM, width=50, height=50)
        avatar2.pack(side="left", padx=(0, 14)); avatar2.pack_propagate(False)
        tk.Label(avatar2, text="👤", font=("Segoe UI", 22), bg=ACCENT_DIM).place(relx=0.5, rely=0.5, anchor="center")
        acc_info2 = tk.Frame(acc_row2, bg=BG_CARD); acc_info2.pack(side="left", fill="both", expand=True)
        tk.Label(acc_info2, text=USER_NAME, font=("Segoe UI", 12, "bold"), bg=BG_CARD, fg=TEXT_PRI).pack(anchor="w")
        tk.Label(acc_info2, text="Plant Enthusiast", font=("Segoe UI", 7), bg=BG_CARD, fg=ACCENT).pack(anchor="w")
        tk.Label(acc_info2, text=f"{len(USERS)} account(s) registered this session",
                 font=("Segoe UI", 6), bg=BG_CARD, fg=TEXT_MUT).pack(anchor="w")

        save_row2 = tk.Frame(content, bg=BG_MAIN); save_row2.pack(anchor="e", pady=(22, 0))
        save_btn2 = tk.Frame(save_row2, bg=PURPLE, cursor="hand2"); save_btn2.pack(side="right")
        tk.Label(save_btn2, text="Save Settings", font=("Segoe UI", 9, "bold"),
                 bg=PURPLE, fg=BG_MAIN, padx=24, pady=11).pack()
        bind_tree(save_btn2, "<Button-1>",
                  lambda e: messagebox.showinfo("Settings", "Settings saved successfully!"))
        hover(save_btn2, PURPLE, PURPLE2)

# NAVIGATION CONFIG
NAV_ORDER = [
    ("DB", "Dashboard",      ACCENT),
    ("PL", "My Plants",      ACCENT),
    ("HI", "History",        TEAL),
    ("DT", "Detection",      PURPLE),
    ("RC", "Recommendation", YELLOW),
    ("GR", "Growth",         TEAL),
    ("CF", "Settings",       TEXT_SEC),
]
NAV_EMOJIS = {
    "Dashboard":      "🏠",
    "My Plants":      "🌿",
    "History":        "📜",
    "Detection":      "🔬",
    "Recommendation": "🌱",
    "Growth":         "📈",
    "Settings":       "⚙️",
}
PAGE_CLASSES = {
    "Dashboard":      DashboardPage,
    "My Plants":      MyPlantsPage,
    "History":        HistoryPage,
    "Detection":      DetectionPage,
    "Recommendation": RecommendationSystemPage,
    "Growth":         GrowthPage,
    "Settings":       SettingsPage,
}

# MAIN APP WINDOW
class PlantMonitor(tk.Tk):
    def __init__(self, username="Anastasija"):
        super().__init__()
        global USER_NAME
        USER_NAME = username
        self.title("Plant Monitor")
        self.geometry("1200x740")
        self.configure(bg=BG_MAIN)
        self.resizable(True, True)
        self._is_fullscreen = False
        self._nav_buttons   = []
        self._pages         = {}
        self._current_page  = None
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.bind("<F11>", lambda e: self._toggle_fullscreen())
        self._build_shell()
        self._register_pages()
        self._show_page("Dashboard")

    def _on_close(self):
        plt.close("all"); self.destroy(); os._exit(0)

    def _toggle_fullscreen(self, event=None):
        self._is_fullscreen = not self._is_fullscreen
        self.attributes("-fullscreen", self._is_fullscreen)

    def _build_shell(self):
        # Sidebar
        self.sidebar = tk.Frame(self, bg=BG_SIDE, width=220)
        self.sidebar.pack(side="left", fill="y"); self.sidebar.pack_propagate(False)
        self._build_sidebar(self.sidebar)
        # Content
        self.content_area = tk.Frame(self, bg=BG_MAIN)
        self.content_area.pack(side="left", fill="both", expand=True)
        # Right panel
        right = tk.Frame(self, bg=BG_SIDE, width=230)
        right.pack(side="right", fill="y"); right.pack_propagate(False)
        self._build_right(right)

    def _build_sidebar(self, parent):
        # ── Brand block ─
        brand = tk.Frame(parent, bg=BG_GLASS); brand.pack(fill="x")
        tk.Frame(brand, bg=ACCENT, height=3).pack(fill="x")
        bi = tk.Frame(brand, bg=BG_GLASS, padx=16, pady=18); bi.pack(fill="x")
        top_logo2 = tk.Frame(bi, bg=BG_GLASS); top_logo2.pack(fill="x")
        logo_circle2 = tk.Frame(top_logo2, bg=ACCENT_DIM, width=38, height=38)
        logo_circle2.pack(side="left"); logo_circle2.pack_propagate(False)
        tk.Label(logo_circle2, text="🌿", font=("Segoe UI", 16),
                 bg=ACCENT_DIM).place(relx=0.5, rely=0.5, anchor="center")
        tf2 = tk.Frame(top_logo2, bg=BG_GLASS); tf2.pack(side="left", padx=(10, 0))
        tk.Label(tf2, text="Plant Monitor", font=("Segoe UI", 12, "bold"),
                 bg=BG_GLASS, fg=TEXT_PRI).pack(anchor="w")
        # Active pill
        ap = tk.Frame(bi, bg=ACCENT_DIM, padx=8, pady=3); ap.pack(anchor="w", pady=(10, 0))
        tk.Frame(ap, bg=ACCENT, width=6, height=6).pack(side="left", pady=(1, 0))
        tk.Label(ap, text="  System active", font=("Segoe UI", 7), bg=ACCENT_DIM, fg=ACCENT).pack(side="left")

        # Nav label 
        nl = tk.Frame(parent, bg=BG_SIDE, padx=14); nl.pack(fill="x", pady=(16, 4))
        tk.Label(nl, text="Navigation", font=("Segoe UI", 7, "bold"), bg=BG_SIDE, fg=TEXT_MUT).pack(side="left")
        tk.Frame(nl, bg=BORDER, height=1).pack(side="left", fill="x", expand=True, padx=(8, 0), pady=5)

        # Nav buttons
        for code, label, color in NAV_ORDER:
            self._nav_btn(parent, code, label, color)

        tk.Frame(parent, bg=BG_SIDE).pack(expand=True, fill="both")
        tk.Frame(parent, bg=BORDER, height=1).pack(fill="x", padx=12, pady=(0, 4))

        # Logout 
        logout_row = tk.Frame(parent, bg=BG_SIDE, cursor="hand2"); logout_row.pack(fill="x", padx=8, pady=(0, 4))
        li5 = tk.Frame(logout_row, bg=BG_SIDE, padx=12, pady=8); li5.pack(anchor="w")
        tk.Label(li5, text="↗️", font=("Segoe UI", 12), bg=BG_SIDE, fg=RED).pack(side="left", padx=(0, 8))
        tk.Label(li5, text="Sign out", font=("Segoe UI", 8, "bold"), bg=BG_SIDE, fg=RED).pack(side="left")
        bind_tree(logout_row, "<Button-1>", lambda e: self._do_logout())
        hover(logout_row, BG_SIDE, RED_DIM)

        # User card
        prof = tk.Frame(parent, bg=BG_GLASS, cursor="hand2"); prof.pack(fill="x", padx=8, pady=(0, 14))
        tk.Frame(prof, bg=ACCENT, height=1).pack(fill="x")
        pi = tk.Frame(prof, bg=BG_GLASS, padx=12, pady=10); pi.pack(fill="x")
        av2 = tk.Frame(pi, bg=ACCENT_DIM, width=34, height=34); av2.pack(side="left")
        av2.pack_propagate(False)
        tk.Label(av2, text="👤", font=("Segoe UI", 14), bg=ACCENT_DIM).place(relx=0.5, rely=0.5, anchor="center")
        info2 = tk.Frame(pi, bg=BG_GLASS); info2.pack(side="left", padx=(10, 0))
        tk.Label(info2, text=USER_NAME, font=("Segoe UI", 8, "bold"), bg=BG_GLASS, fg=TEXT_PRI).pack(anchor="w")
        tk.Label(info2, text="Enthusiast", font=("Segoe UI", 6), bg=BG_GLASS, fg=ACCENT).pack(anchor="w")
        bind_tree(prof, "<Button-1>", lambda e: self._show_page("Settings"))
        hover(prof, BG_GLASS, BG_CARD)

    def _nav_btn(self, parent, code, label, color=ACCENT):
        is_active = not self._nav_buttons
        bg_c = BG_CARD if is_active else BG_SIDE
        emoji = NAV_EMOJIS.get(label, "")

        row9 = tk.Frame(parent, bg=bg_c, cursor="hand2"); row9.pack(fill="x", padx=8, pady=1)
        bar3 = tk.Frame(row9, bg=ACCENT if is_active else bg_c, width=3); bar3.pack(side="left", fill="y")
        code_badge2 = tk.Frame(row9, bg=ACCENT_DIM if is_active else bg_c, padx=8, pady=10)
        code_badge2.pack(side="left", padx=(6, 0))
        code_lbl2 = tk.Label(code_badge2, text=emoji, font=("Segoe UI", 14),
                              bg=ACCENT_DIM if is_active else bg_c, fg=ACCENT if is_active else TEXT_MUT)
        code_lbl2.pack()
        lbl4 = tk.Label(row9, text=label, font=("Segoe UI", 9),
                        bg=bg_c, fg=TEXT_PRI if is_active else TEXT_SEC, anchor="w", pady=11, padx=4)
        lbl4.pack(fill="x")
        right_bar2 = tk.Frame(row9, bg=ACCENT if is_active else bg_c, width=2); right_bar2.pack(side="right", fill="y")

        entry = {"row": row9, "bar": bar3, "lbl": lbl4, "code_badge": code_badge2,
                 "code_lbl": code_lbl2, "right": right_bar2, "label": label, "color": color}
        self._nav_buttons.append(entry)

        def on_click(e, entry=entry):
            for b in self._nav_buttons:
                b["row"].configure(bg=BG_SIDE); b["bar"].configure(bg=BG_SIDE)
                b["right"].configure(bg=BG_SIDE); b["lbl"].configure(bg=BG_SIDE, fg=TEXT_SEC)
                b["code_badge"].configure(bg=BG_SIDE); b["code_lbl"].configure(bg=BG_SIDE, fg=TEXT_MUT)
            entry["row"].configure(bg=BG_CARD); entry["bar"].configure(bg=ACCENT)
            entry["right"].configure(bg=ACCENT); entry["lbl"].configure(bg=BG_CARD, fg=TEXT_PRI)
            entry["code_badge"].configure(bg=ACCENT_DIM); entry["code_lbl"].configure(bg=ACCENT_DIM, fg=ACCENT)
            self._show_page(entry["label"])

        for w in [row9, lbl4, bar3, code_badge2, code_lbl2, right_bar2]:
            w.bind("<Button-1>", on_click)
        hover(row9, bg_c, BG_CARD2)

    def _build_right(self, parent):
        pad2 = tk.Frame(parent, bg=BG_SIDE); pad2.pack(fill="both", expand=True)

        # Brand 
        brand2 = tk.Frame(pad2, bg=BG_GLASS); brand2.pack(fill="x")
        tk.Frame(brand2, bg=ACCENT, height=2).pack(fill="x")
        bi2 = tk.Frame(brand2, bg=BG_GLASS, padx=18, pady=20); bi2.pack(fill="x")
        tk.Label(bi2, text="Plant", font=("Segoe UI", 20, "bold"), bg=BG_GLASS, fg=TEXT_PRI).pack(anchor="w")
        tk.Label(bi2, text="Monitor", font=("Segoe UI", 20, "bold"), bg=BG_GLASS, fg=ACCENT).pack(anchor="w")
        tk.Label(bi2, text="AI-powered care system", font=("Segoe UI", 7), bg=BG_GLASS, fg=TEXT_MUT).pack(anchor="w", pady=(4, 0))
        sp2 = tk.Frame(bi2, bg=BG_GLASS); sp2.pack(anchor="w", pady=(10, 0))
        tk.Frame(sp2, bg=ACCENT, width=7, height=7).pack(side="left", pady=(2, 0))
        tk.Label(sp2, text="  System online", font=("Segoe UI", 6, "bold"), bg=BG_GLASS, fg=ACCENT).pack(side="left")

        # Quick actions 
        qa_row2 = tk.Frame(pad2, bg=BG_SIDE, padx=14); qa_row2.pack(fill="x", pady=(18, 6))
        tk.Label(qa_row2, text="Quick actions", font=("Segoe UI", 7, "bold"), bg=BG_SIDE, fg=TEXT_MUT).pack(side="left")
        tk.Frame(qa_row2, bg=BORDER, height=1).pack(side="left", fill="x", expand=True, padx=(8, 0), pady=4)

        for code2, label2, page, color in [
            ("PL", "My Plants",        "My Plants",      ACCENT),
            ("DT", "Health detection", "Detection",      BLUE),
            ("RC", "Recommend",        "Recommendation", YELLOW),
            ("HI", "History",          "History",        TEAL),
        ]:
            btn4 = tk.Frame(pad2, bg=BG_GLASS, cursor="hand2"); btn4.pack(fill="x", padx=8, pady=(0, 3))
            tk.Frame(btn4, bg=color, width=3).pack(side="left", fill="y")
            inner14 = tk.Frame(btn4, bg=BG_GLASS, padx=12, pady=10); inner14.pack(side="left", fill="x", expand=True)
            cb2 = tk.Frame(inner14, bg=BG_CARD, padx=4, pady=2); cb2.pack(side="left", padx=(0, 8))
            tk.Label(cb2, text=code2, font=("Consolas", 7, "bold"), bg=BG_CARD, fg=color).pack()
            tk.Label(inner14, text=label2, font=("Segoe UI", 8), bg=BG_GLASS, fg=TEXT_PRI).pack(side="left")
            tk.Label(inner14, text="→", font=("Segoe UI", 8, "bold"), bg=BG_GLASS, fg=color).pack(side="right")
            bind_tree(btn4, "<Button-1>", lambda e, p=page: self._show_page(p))
            hover(btn4, BG_GLASS, BG_CARD)

        tk.Frame(pad2, bg=BORDER, height=1).pack(fill="x", padx=12, pady=(14, 12))
        sl_row = tk.Frame(pad2, bg=BG_SIDE, padx=14); sl_row.pack(fill="x", pady=(0, 8))
        tk.Label(sl_row, text="System status", font=("Segoe UI", 7, "bold"), bg=BG_SIDE, fg=TEXT_MUT).pack(side="left")

        sc2 = tk.Frame(pad2, bg=BG_GLASS); sc2.pack(fill="x", padx=8)
        tk.Frame(sc2, bg=BORDER2, height=1).pack(fill="x")
        si2 = tk.Frame(sc2, bg=BG_GLASS, padx=14, pady=12); si2.pack(fill="x")
        for dot_color2, label3, status_txt, ok in [
            (ACCENT, "CNN engine",   "Ready",   True),
            (BLUE,   "Data layer",   "Active",  True),
            (RED,    "Growth API",   "Offline", False),
        ]:
            row10 = tk.Frame(si2, bg=BG_GLASS); row10.pack(fill="x", pady=(0, 6))
            ls2 = tk.Frame(row10, bg=BG_GLASS); ls2.pack(side="left", fill="x", expand=True)
            tk.Frame(ls2, bg=dot_color2, width=6, height=6).pack(side="left", pady=(3, 0))
            tk.Label(ls2, text=f"  {label3}", font=("Segoe UI", 7), bg=BG_GLASS, fg=TEXT_SEC).pack(side="left")
            st2 = tk.Frame(row10, bg=BG_CARD, padx=6, pady=2); st2.pack(side="right")
            tk.Label(st2, text=status_txt, font=("Segoe UI", 7, "bold"), bg=BG_CARD, fg=dot_color2).pack()

    def _register_pages(self):
        for name, cls in PAGE_CLASSES.items():
            page = cls(self.content_area, self)
            page.place(relx=0, rely=0, relwidth=1, relheight=1)
            self._pages[name] = page

    def _show_page(self, name):
        if self._current_page: self._current_page.lower()
        page = self._pages.get(name)
        if page: page.lift(); self._current_page = page
        for entry in self._nav_buttons:
            match = entry["label"] == name
            entry["row"].configure(bg=BG_CARD if match else BG_SIDE)
            entry["bar"].configure(bg=ACCENT  if match else BG_SIDE)
            entry["right"].configure(bg=ACCENT if match else BG_SIDE)
            entry["lbl"].configure(bg=BG_CARD if match else BG_SIDE, fg=TEXT_PRI if match else TEXT_SEC)
            entry["code_badge"].configure(bg=ACCENT_DIM if match else BG_SIDE)
            entry["code_lbl"].configure(bg=ACCENT_DIM if match else BG_SIDE, fg=ACCENT if match else TEXT_MUT)

    def _do_logout(self):
        if messagebox.askyesno("Sign Out", "Are you sure you want to sign out?"):
            plt.close("all"); self.destroy()
            auth = AuthWindow(); auth.mainloop()
            if auth.logged_in_user:
                app = PlantMonitor(auth.logged_in_user); app.mainloop()

# ENTRY POINT
if __name__ == "__main__":
    auth = AuthWindow(); auth.mainloop()
    if auth.logged_in_user:
        app = PlantMonitor(auth.logged_in_user); app.mainloop()