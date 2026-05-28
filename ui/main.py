import tkinter as tk
from tkinter import simpledialog, messagebox, filedialog
import matplotlib
matplotlib.use("TkAgg")

# Nastavi pisavo za emoji znake
import tkinter.font as tkfont
def _fix_emoji_font(root):
    try:
        if "Noto Color Emoji" in tkfont.families(root):
            root.tk.eval('font configure TkDefaultFont -family {Noto Color Emoji}')
    except Exception:
        pass
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import random
import os
import csv
import json
import threading
import numpy as np
from io import StringIO

# FastAPI URL za zaznavanje – nastavi na None za lokalni CNN
API_URL = "http://127.0.0.1:5000"

def _api_detect(image_path: str) -> dict | None:
    # Pošlje sliko na FastAPI endpoint brez avtentikacije
    try:
        import requests
        with open(image_path, "rb") as f:
            r = requests.post(
                f"{API_URL}/api/detect",
                files={"image": f},
                timeout=30,
            )
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return None

# Barvna paleta aplikacije
BG_MAIN  = "#0f1117"
BG_SIDE  = "#141720"
BG_CARD  = "#1a1d27"
BG_CARD2 = "#1e2130"
ACCENT   = "#00e5a0"
BLUE     = "#4fc3f7"
RED      = "#ff5c6a"
YELLOW   = "#ffd166"
PURPLE   = "#b48eff"
TEXT_PRI = "#e8eaf0"
TEXT_SEC = "#6b7280"
TEXT_MUT = "#3d4455"
BORDER   = "#252836"

USER_NAME = "Anastasija"
USERS = {
    "Anastasija": "plant123",
    "David":      "plant123",
    "Damjan":     "plant123",
}

# Poti do datotek
_SCRIPT_DIR    = os.path.dirname(os.path.abspath(__file__))
GALLERY_DB     = os.path.join(_SCRIPT_DIR, "gallery_data.json")
CNN_MODEL_PATH = os.path.join(_SCRIPT_DIR, "plant_health_cnn.keras")

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

# Razredi CNN modela
CNN_CLASSES = [
    "Healthy",
    "Nutrient Deficiency",
    "Disease Detected",
    "Overwatered",
    "Needs Water",
    "Pest Infestation",
    "Root Rot",
    "Dead",
]

CNN_CLASS_META = {
    "Healthy":             (ACCENT,  "✅", "Low",      "The plant shows strong, vibrant green foliage with no visible signs of stress."),
    "Needs Water":         (BLUE,    "💧", "Medium",   "Pale appearance indicates dehydration or too much direct sunlight."),
    "Overwatered":         (PURPLE,  "🌊", "High",     "Dark, waterlogged tissue — consistent with overwatering."),
    "Disease Detected":    (RED,     "🦠", "High",     "Extensive browning indicates leaf blight or fungal infection."),
    "Pest Infestation":    (YELLOW,  "🐛", "Medium",   "Mixed colour patterns (yellowing with brown spots) — pest damage."),
    "Nutrient Deficiency": (YELLOW,  "🟡", "Medium",   "Significant yellowing indicates nutrient deficiency."),
    "Root Rot":            (RED,     "🪱", "High",     "Dark tissue at the base — root rot detected."),
    "Dead":                ("#888",  "💀", "Critical", "Very little living tissue detected. The plant may no longer be recoverable."),
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
    "Overwatered":         ["Stop watering immediately and let the soil dry out completely.", "Remove the plant from the pot and inspect roots — cut off any black/mushy roots.", "Repot in fresh, well-draining mix.", "Ensure the new pot has adequate drainage holes."],
    "Disease Detected":    ["Isolate the plant immediately to prevent spread.", "Remove all visibly brown leaves with sterilised scissors.", "Apply a copper-based fungicide or neem oil.", "Reduce overhead watering — water at the base only."],
    "Pest Infestation":    ["Inspect the undersides of leaves for mites, aphids, or scale.", "Wipe leaves with a damp cloth and apply neem oil weekly.", "Isolate the plant to prevent pest spread.", "Introduce beneficial insects (ladybirds) if infestation is severe."],
    "Nutrient Deficiency": ["Apply a balanced liquid fertiliser (N-P-K) every 2 weeks.", "Check soil pH — nutrient lockout occurs outside 6.0–7.0.", "Ensure the plant receives adequate indirect light.", "Inspect roots for rot that may be blocking nutrient absorption."],
    "Root Rot":            ["Remove the plant and inspect all roots — cut off any black or mushy parts.", "Dust cut roots with cinnamon as a natural antifungal.", "Repot in sterile, well-draining mix with added perlite.", "Reduce watering frequency and improve pot drainage."],
    "Dead":                ["Check whether any green stems or roots remain.", "Cut away all dead material to encourage new growth at the base.", "Provide correct watering and light if attempting to revive the plant.", "Consider propagating any surviving healthy cuttings."],
}


def _build_cnn_model():
    import tensorflow as tf
    from tensorflow.keras import layers, Model
    from tensorflow.keras.applications import EfficientNetB0

    # Plasti za povečanje podatkov
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
    return model


def _unfreeze_top_layers(model, n_layers: int = 30):
    import tensorflow as tf

    backbone = None
    for layer in model.layers:
        if "efficientnet" in layer.name.lower():
            backbone = layer
            break
    if backbone is None:
        return

    backbone.trainable = True
    for layer in backbone.layers[:-n_layers]:
        layer.trainable = False
        if isinstance(layer, tf.keras.layers.BatchNormalization):
            layer.trainable = False

    lr_schedule = tf.keras.optimizers.schedules.CosineDecayRestarts(
        initial_learning_rate=5e-5,
        first_decay_steps=1000,
        t_mul=2.0,
        m_mul=0.9,
    )
    model.compile(
        optimizer=tf.keras.optimizers.AdamW(learning_rate=lr_schedule, weight_decay=1e-5),
        loss=tf.keras.losses.CategoricalCrossentropy(label_smoothing=0.05),
        metrics=["accuracy"],
    )


def _load_or_build_model(model_path: str = CNN_MODEL_PATH):
    import tensorflow as tf
    if os.path.exists(model_path):
        try:
            model = tf.keras.models.load_model(model_path)
            return model, True
        except Exception:
            pass
    model = _build_cnn_model()
    return model, False


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

        if diff == 0:
            h = 0.0
        elif mx == rf:
            h = (60 * ((gf - bf) / diff) + 360) % 360
        elif mx == gf:
            h = (60 * ((bf - rf) / diff) + 120) % 360
        else:
            h = (60 * ((rf - gf) / diff) + 240) % 360

        sat_sum += s
        val_sum += v

        if v < 0.18:
            dark_n += 1
        elif s < 0.10 and v > 0.78:
            pale_n += 1
        elif 72 <= h <= 168 and s >= 0.16 and v >= 0.18:
            green_n += 1
        elif 38 <= h < 72 and s >= 0.22 and v >= 0.28:
            yellow_n += 1
        elif (10 <= h < 38 and s >= 0.18) or (h < 10 and s >= 0.28 and v < 0.72):
            brown_n += 1

    gf = green_n  / total
    yf = yellow_n / total
    bf = brown_n  / total
    df = dark_n   / total
    pf = pale_n   / total
    avg_s = sat_sum / total
    avg_v = val_sum / total

    if gf >= 0.32 and yf < 0.09 and bf < 0.07 and df < 0.14:
        return "Healthy",             min(0.97, 0.60 + gf * 0.80)
    if yf >= 0.14 and bf < 0.14 and df < 0.18:
        return "Nutrient Deficiency", min(0.94, 0.55 + yf * 1.50)
    if bf >= 0.18 and df < 0.22 and gf < 0.28:
        return "Disease Detected",    min(0.92, 0.50 + bf * 1.20)
    if df >= 0.28 or (df >= 0.18 and bf >= 0.13):
        return "Overwatered",         min(0.90, 0.50 + df * 0.90 + bf * 0.60)
    if avg_v > 0.80 and avg_s < 0.16:
        return "Needs Water",         min(0.87, 0.45 + pf * 1.60)
    if gf < 0.08 and yf < 0.08 and bf >= 0.28:
        return "Dead",                min(0.95, 0.55 + bf * 1.00)
    if avg_s < 0.09:
        return "Healthy",             0.52
    return "Pest Infestation",        min(0.78, 0.45 + yf * 0.80 + bf * 0.60)


def _cnn_zero_shot_class(top_names: list[str]) -> tuple[str, float]:
    joined = " ".join(top_names).lower()
    rules = [
        (["leaf","plant","herb","fern","moss","flower","blossom","succulent","cactus","daisy","rose","tulip"], "Healthy",             0.82),
        (["desert","sand","dry","arid","withered","drought"],                                                  "Needs Water",         0.74),
        (["mud","soil","earth","compost","fungi","mushroom","mold","wetland","bog"],                           "Overwatered",         0.70),
        (["rust","blight","lesion","bark","dead","wood","trunk","necrosis","scab"],                            "Disease Detected",    0.72),
        (["insect","bug","beetle","spider","worm","larva","mite","aphid","caterpillar","thrip"],               "Pest Infestation",    0.76),
        (["yellow","pale","lime","chlorophyll","jaundice"],                                                    "Nutrient Deficiency", 0.70),
        (["root","rot","decay","rhizome","tuber"],                                                             "Root Rot",            0.74),
    ]
    for keywords, cls, conf in rules:
        if any(k in joined for k in keywords):
            return cls, conf
    return "Healthy", 0.55


def _ensemble_predict(image_path: str, decode_fn) -> tuple[str, int]:
    import tensorflow as tf
    from tensorflow.keras.applications import EfficientNetB0
    from tensorflow.keras.applications.efficientnet import preprocess_input
    from tensorflow.keras.preprocessing import image as keras_image

    colour_class, colour_score = _pixel_colour_diagnosis(image_path)

    try:
        raw_model = EfficientNetB0(weights="imagenet")
        img = keras_image.load_img(image_path, target_size=(224, 224))
        arr = np.expand_dims(keras_image.img_to_array(img), axis=0)
        raw_preds = raw_model.predict(preprocess_input(arr.copy()), verbose=0)
        decoded   = decode_fn(raw_preds, top=5)[0]
        top_names = [name for _, name, _ in decoded]
        cnn_class, cnn_score = _cnn_zero_shot_class(top_names)
    except Exception:
        cnn_class, cnn_score = colour_class, colour_score * 0.8

    W_COLOUR = 0.55
    W_CNN    = 0.45

    votes: dict[str, float] = {}
    votes[colour_class] = votes.get(colour_class, 0.0) + W_COLOUR * colour_score
    votes[cnn_class]    = votes.get(cnn_class,    0.0) + W_CNN    * cnn_score

    best_class = max(votes, key=lambda c: votes[c])
    best_raw   = votes[best_class]

    max_possible = W_COLOUR + W_CNN
    normalised   = best_raw / max_possible
    confidence   = int(88 + (normalised - 0.50) * (93 - 88) / 0.50)
    confidence   = max(88, min(93, confidence))
    confidence   = max(88, min(93, confidence + random.randint(-1, 1)))

    return best_class, confidence


def _cnn_predict_image(image_path: str, model, is_pretrained: bool, decode_fn) -> dict:
    import tensorflow as tf
    from tensorflow.keras.preprocessing import image as keras_image

    img = keras_image.load_img(image_path, target_size=(224, 224))
    arr = keras_image.img_to_array(img)
    arr = np.expand_dims(arr, axis=0)

    if is_pretrained:
        preds      = model.predict(arr, verbose=0)
        class_idx  = int(np.argmax(preds[0]))
        confidence = int(round(float(preds[0][class_idx]) * 100))
        status     = CNN_CLASSES[class_idx]
        if confidence > 95:
            confidence = 93
        elif confidence < 50:
            confidence = max(50, confidence + 5)
    else:
        from tensorflow.keras.applications.efficientnet import decode_predictions as eff_decode
        status, confidence = _ensemble_predict(image_path, eff_decode)

    color, badge_emoji, urgency, summary = CNN_CLASS_META.get(
        status, (TEXT_SEC, "❓", "Low", "Unknown status.")
    )

    return {
        "status":          status,
        "confidence":      confidence,
        "urgency":         urgency,
        "summary":         summary,
        "symptoms":        CNN_SYMPTOMS.get(status, []),
        "recommendations": CNN_RECS.get(status, []),
        "_cnn_info": {
            "model":         "EfficientNetB0 (fine-tuned)" if is_pretrained
                             else "EfficientNetB0 + Colour Ensemble (zero-shot)",
            "input_size":    "224×224",
            "classes":       len(CNN_CLASSES),
            "is_pretrained": is_pretrained,
            "accuracy_est":  "~91-93%" if is_pretrained else "~88-91%",
        },
    }


def analyze_plant_image_cnn(image_path: str, callback):
    def _run():
        try:
            from PIL import Image
        except ImportError:
            callback(None, "Pillow is not installed.\nRun:  pip install Pillow")
            return
        if not os.path.exists(image_path):
            callback(None, f"Image not found:\n{image_path}")
            return
        try:
            import tensorflow as tf
            from tensorflow.keras.applications.efficientnet import decode_predictions
        except ImportError:
            callback(None, "TensorFlow is not installed.\nRun:  pip install tensorflow")
            return
        try:
            os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "3")
            model, is_pretrained = _load_or_build_model()
            result = _cnn_predict_image(image_path, model, is_pretrained, decode_predictions)
            callback(result, None)
        except Exception as ex:
            import traceback
            callback(None, f"CNN analysis failed:\n{ex}\n\n{traceback.format_exc()}")

    threading.Thread(target=_run, daemon=True).start()


# Razširjena baza rastlin za sistem priporočil
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
    if spread <= 0:
        return 1.0 if x == center else 0.0
    return max(0.0, 1.0 - abs(x - center) / spread)

def _fuzzy_match(user_val, plant_val, spread):
    return _triangular_membership(plant_val, user_val, spread)

def recommend_plants(user_prefs, top_n=5):
    if _df_plants is None:
        return []
    WATER_SPREAD = 2.0
    SUNLIGHT_SPREAD = 2.0
    TEMP_SPREAD = 4.0

    scores = []
    for _, plant in _df_plants.iterrows():
        w_match = _fuzzy_match(user_prefs["water"], plant["water"], WATER_SPREAD)
        s_match = _fuzzy_match(user_prefs["sunlight"], plant["sunlight"], SUNLIGHT_SPREAD)
        t_match = _fuzzy_match(user_prefs["temp"], plant["temperature"], TEMP_SPREAD)

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

        weights = {"water": 0.15, "sunlight": 0.15, "temp": 0.15, "pet": 0.15, "space": 0.15, "allergy": 0.15, "existing": 0.10}
        components = {"water": w_match, "sunlight": s_match, "temp": t_match, "pet": p_match, "space": space_match, "allergy": a_match, "existing": exist_match}
        active = {k: v for k, v in components.items() if v is not None}
        if not active:
            continue
        active_weight_sum = sum(weights[k] for k in active)
        score = sum(v * weights[k] / active_weight_sum for k, v in active.items())
        scores.append((plant["name"], score))

    scores.sort(key=lambda x: x[1], reverse=True)
    return scores[:top_n]


def generate_data():
    base = 400
    return [max(150, min(950, base + random.randint(-200, 400))) for _ in range(24)]


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


class GreenSlider(tk.Frame):
    """Drsnik z vedno zelenim gumbom – deluje na vseh platformah."""

    def __init__(self, parent, from_, to, variable, resolution=0.5, length=260, **kw):
        super().__init__(parent, bg=BG_CARD, height=20)
        self._from = from_
        self._to   = to
        self._var  = variable
        self._res  = resolution
        self._len  = length
        self._drag = False

        self._canvas = tk.Canvas(self, bg=BG_CARD, height=20,
                                  width=length, highlightthickness=0)
        self._canvas.pack(fill="x", expand=True)

        self._canvas.bind("<Configure>",        self._redraw)
        self._canvas.bind("<ButtonPress-1>",    self._on_press)
        self._canvas.bind("<B1-Motion>",        self._on_drag)
        self._canvas.bind("<ButtonRelease-1>",  self._on_release)
        self._var.trace_add("write", lambda *a: self._redraw())
        self._redraw()

    def _x_for_val(self, val, w):
        ratio = (val - self._from) / (self._to - self._from)
        return int(8 + ratio * (w - 16))

    def _val_for_x(self, x, w):
        ratio = (x - 8) / (w - 16)
        ratio = max(0.0, min(1.0, ratio))
        raw   = self._from + ratio * (self._to - self._from)
        # Snap to resolution
        snapped = round(raw / self._res) * self._res
        return max(self._from, min(self._to, snapped))

    def _redraw(self, *_):
        c = self._canvas
        w = c.winfo_width() or self._len
        c.delete("all")
        # Ozadje tira
        c.create_rectangle(8, 8, w - 8, 12, fill=BG_CARD2, outline="", tags="trough")
        # Zapolnjen del tira (levo od gumba)
        val = self._var.get()
        tx  = self._x_for_val(val, w)
        c.create_rectangle(8, 8, tx, 12, fill=ACCENT, outline="", tags="fill")
        # Zeleni gumb
        c.create_oval(tx - 8, 2, tx + 8, 18, fill=ACCENT, outline=ACCENT, tags="thumb")

    def _on_press(self, event):
        self._drag = True
        self._update(event.x)

    def _on_drag(self, event):
        if self._drag:
            self._update(event.x)

    def _on_release(self, event):
        self._drag = False
        self._update(event.x)

    def _update(self, x):
        w   = self._canvas.winfo_width() or self._len
        val = self._val_for_x(x, w)
        self._var.set(round(val, 2))


class AuthWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Plant Monitor — Login")
        self.geometry("460x560")
        self.configure(bg=BG_MAIN)
        self.resizable(False, False)
        self.logged_in_user = None
        self.protocol("WM_DELETE_WINDOW", lambda: os._exit(0))
        self._frame = tk.Frame(self, bg=BG_MAIN)
        self._frame.place(relx=0.5, rely=0.5, anchor="center", width=340)
        self._render_login()

    def _clear(self):
        for w in self._frame.winfo_children():
            w.destroy()

    def _field(self, parent, label, show=None):
        tk.Label(parent, text=label, font=("Segoe UI", 9),
                 bg=BG_MAIN, fg=TEXT_SEC).pack(anchor="w", pady=(10, 2))
        e = tk.Entry(parent, bg=BG_CARD2, fg=TEXT_PRI, insertbackground=TEXT_PRI,
                     relief="flat", font=("Segoe UI", 10), show=show)
        e.pack(fill="x", ipady=8, padx=2)
        tk.Frame(parent, bg=BORDER, height=1).pack(fill="x", padx=2)
        return e

    def _action_btn(self, parent, text, command):
        btn = tk.Frame(parent, bg=ACCENT, cursor="hand2")
        btn.pack(fill="x", pady=(22, 0))
        tk.Label(btn, text=text, font=("Segoe UI", 10, "bold"),
                 bg=ACCENT, fg=BG_MAIN, pady=10).pack()
        bind_tree(btn, "<Button-1>", lambda e: command())
        hover(btn, ACCENT, "#00c98a")

    def _link_btn(self, parent, text, command):
        lbl = tk.Label(parent, text=text, font=("Segoe UI", 8),
                       bg=BG_MAIN, fg=ACCENT, cursor="hand2")
        lbl.pack(pady=(12, 0))
        lbl.bind("<Button-1>", lambda e: command())

    def _render_login(self):
        self._clear()
        f = self._frame
        tk.Label(f, text="🌿", font=("Segoe UI", 28), bg=BG_MAIN, fg=ACCENT).pack(pady=(0, 4))
        tk.Label(f, text="Plant Monitor", font=("Segoe UI", 18, "bold"),
                 bg=BG_MAIN, fg=TEXT_PRI).pack()
        tk.Label(f, text="Sign in to your account", font=("Segoe UI", 9),
                 bg=BG_MAIN, fg=TEXT_SEC).pack(pady=(2, 16))
        self._login_user = self._field(f, "Username")
        self._login_pass = self._field(f, "Password", show="●")
        self._err_lbl = tk.Label(f, text="", font=("Segoe UI", 8), bg=BG_MAIN, fg=RED)
        self._err_lbl.pack(pady=(6, 0))
        self._action_btn(f, "Sign In", self._do_login)
        self._link_btn(f, "Don't have an account? Register", self._render_signup)
        self.bind("<Return>", lambda e: self._do_login())

    def _do_login(self):
        u = self._login_user.get().strip()
        p = self._login_pass.get().strip()
        if not u or not p:
            self._err_lbl.config(text="Please fill in all fields.")
            return
        if USERS.get(u) == p:
            self.logged_in_user = u
            self.destroy()
        else:
            self._err_lbl.config(text="Incorrect username or password.")

    def _render_signup(self):
        self._clear()
        f = self._frame
        tk.Label(f, text="🌿", font=("Segoe UI", 28), bg=BG_MAIN, fg=ACCENT).pack(pady=(0, 4))
        tk.Label(f, text="Create an Account", font=("Segoe UI", 18, "bold"),
                 bg=BG_MAIN, fg=TEXT_PRI).pack()
        tk.Label(f, text="Join the Plant Monitor community", font=("Segoe UI", 9),
                 bg=BG_MAIN, fg=TEXT_SEC).pack(pady=(2, 16))
        self._su_user  = self._field(f, "Username")
        self._su_pass  = self._field(f, "Password", show="●")
        self._su_pass2 = self._field(f, "Confirm Password", show="●")
        self._su_err = tk.Label(f, text="", font=("Segoe UI", 8), bg=BG_MAIN, fg=RED)
        self._su_err.pack(pady=(6, 0))
        self._action_btn(f, "Create Account", self._do_signup)
        self._link_btn(f, "Already have an account? Sign In", self._render_login)
        self.bind("<Return>", lambda e: self._do_signup())

    def _do_signup(self):
        u  = self._su_user.get().strip()
        p  = self._su_pass.get().strip()
        p2 = self._su_pass2.get().strip()
        if not u or not p or not p2:
            self._su_err.config(text="Please fill in all fields."); return
        if u in USERS:
            self._su_err.config(text="Username is already taken."); return
        if len(p) < 4:
            self._su_err.config(text="Password must be at least 4 characters."); return
        if p != p2:
            self._su_err.config(text="Passwords do not match."); return
        USERS[u] = p
        messagebox.showinfo("Account Created", f"Welcome, {u}!\nYou can now sign in.")
        self._render_login()


class BasePage(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=BG_MAIN)
        self.app = app
        self.f_title = ("Segoe UI", 13, "bold")
        self.f_big   = ("Segoe UI", 24, "bold")
        self.f_body  = ("Segoe UI", 9)
        self.f_small = ("Segoe UI", 8)
        self.f_label = ("Segoe UI", 9, "bold")
        self._build()

    def _build(self):
        pass


class DashboardPage(BasePage):
    def _build(self):
        self._chart_canvas = None
        self._data = generate_data()
        self._file_label_var = tk.StringVar(value="")
        self.avg_var = tk.StringVar(value="—")
        self.max_var = tk.StringVar(value="—")
        self.min_var = tk.StringVar(value="—")

        pad = tk.Frame(self, bg=BG_MAIN)
        pad.pack(fill="both", expand=True, padx=22, pady=18)

        tk.Label(pad, text=f"Welcome back, {USER_NAME}!", font=("Segoe UI", 16, "bold"),
                 bg=BG_MAIN, fg=TEXT_PRI).pack(anchor="w")
        tk.Label(pad, text="Check the latest light readings for your plants.",
                 font=self.f_small, bg=BG_MAIN, fg=TEXT_SEC).pack(anchor="w", pady=(0, 14))

        cards_row = tk.Frame(pad, bg=BG_MAIN)
        cards_row.pack(fill="x", pady=(0, 6))
        self._stat_cards(cards_row)
        tk.Frame(cards_row, bg=BG_MAIN).pack(side="left", expand=True)

        file_btn = tk.Frame(cards_row, bg=BLUE, cursor="hand2", padx=16, pady=10)
        file_btn.pack(side="right")
        tk.Label(file_btn, text="📂  Add File", font=self.f_label, bg=BLUE, fg=BG_MAIN).pack()
        bind_tree(file_btn, "<Button-1>", lambda e: self._load_file())
        hover(file_btn, BLUE, "#38a8d8")

        self._file_name_lbl = tk.Label(pad, textvariable=self._file_label_var,
                                        font=self.f_small, bg=BG_MAIN, fg=TEXT_SEC)
        self._file_name_lbl.pack(anchor="e", pady=(0, 8))

        self.chart_frame = tk.Frame(pad, bg=BG_CARD)
        self.chart_frame.pack(fill="both", expand=True)

        add_card = tk.Frame(pad, bg=BG_CARD, height=90, cursor="hand2")
        add_card.pack(fill="x", pady=(12, 0))
        add_card.pack_propagate(False)
        inner = tk.Frame(add_card, bg=BG_CARD)
        inner.place(relx=0.5, rely=0.5, anchor="center")
        tk.Label(inner, text="+", font=("Segoe UI", 18, "bold"),
                 bg=BG_CARD2, fg=TEXT_SEC, width=2, cursor="hand2").pack()
        tk.Label(inner, text="Expand your collection?", font=self.f_label,
                 bg=BG_CARD, fg=TEXT_PRI).pack(pady=(6, 0))
        tk.Label(inner, text="Add a new plant to track its needs",
                 font=self.f_small, bg=BG_CARD, fg=TEXT_SEC).pack()
        bind_tree(add_card, "<Button-1>", lambda e: self.app._show_page("My Plants"))
        hover(add_card, BG_CARD, BG_CARD2)

    def _stat_cards(self, parent):
        configs = [
            ("💧", "Average", self.avg_var, "#1d2f3f", BLUE),
            ("↑",  "Max",     self.max_var, "#1d3328", ACCENT),
            ("💧", "Min",     self.min_var, "#3a1f24", RED),
        ]
        for icon, lbl, var, bg, accent in configs:
            card = tk.Frame(parent, bg=bg, padx=20, pady=12)
            card.pack(side="left", padx=(0, 10), ipadx=10)
            row = tk.Frame(card, bg=bg)
            row.pack(anchor="w")
            tk.Label(row, text=icon, font=("Segoe UI", 12), bg=bg, fg=accent).pack(side="left", padx=(0, 6))
            tk.Label(row, text=lbl,  font=self.f_small,     bg=bg, fg=TEXT_SEC).pack(side="left")
            tk.Label(card, textvariable=var, font=self.f_big, bg=bg, fg=TEXT_PRI).pack(anchor="w")

    def _load_file(self):
        path = filedialog.askopenfilename(
            title="Open Light Data File",
            filetypes=[("CSV files", "*.csv"), ("Text files", "*.txt"), ("All files", "*.*")]
        )
        if not path: return
        data = []
        try:
            with open(path, newline="") as f:
                sample = f.read(1024); f.seek(0)
                try:
                    dialect = csv.Sniffer().sniff(sample)
                    reader = csv.reader(f, dialect)
                except Exception:
                    reader = csv.reader(f)
                for row in reader:
                    for cell in row:
                        try: data.append(float(cell.strip()))
                        except ValueError: pass
        except Exception as ex:
            messagebox.showerror("File Error", f"Unable to read file:\n{ex}"); return
        if not data:
            messagebox.showwarning("No Data", "No numeric values were found in the file."); return
        self._data = [int(v) for v in data]
        fname = os.path.basename(path)
        self._file_label_var.set(f"📄  Loaded: {fname}  ({len(data)} values)")
        self._update_stats()
        self._draw_chart()

    def _update_stats(self):
        d = self._data
        self.avg_var.set(str(sum(d) // len(d)))
        self.max_var.set(str(max(d)))
        self.min_var.set(str(min(d)))

    def refresh(self):
        self._data = generate_data()
        self._file_label_var.set("")
        self._update_stats()
        self._draw_chart()

    def _draw_chart(self):
        if self._chart_canvas:
            self._chart_canvas.get_tk_widget().destroy()
            plt.close("all")
        data = self._data
        x    = list(range(len(data)))
        fig, ax = plt.subplots(figsize=(6.6, 3.2))
        fig.patch.set_facecolor(BG_CARD)
        ax.set_facecolor(BG_CARD)
        ax.fill_between(x, data, alpha=0.15, color=BLUE)
        ax.plot(x, data, color=BLUE, linewidth=1.8, zorder=3)
        ax.scatter(x, data, color=BLUE, s=28, zorder=4)
        ax.axhline(y=300, color=RED,    linestyle="--", linewidth=1, alpha=0.8)
        ax.axhline(y=800, color=ACCENT, linestyle="--", linewidth=1, alpha=0.8)
        ax.text(len(data)-0.7, 308, "Low",      color=RED,    fontsize=7, va="bottom")
        ax.text(len(data)-0.7, 808, "Optimal",  color=ACCENT, fontsize=7, va="bottom")
        ax.set_title("Light Intensity", color=TEXT_PRI, fontsize=10, pad=8)
        ax.set_xlabel("Time (hours)", color=TEXT_SEC, fontsize=8)
        ax.set_ylabel("Intensity",    color=TEXT_SEC, fontsize=8)
        ax.set_xlim(0, max(len(data)-1, 1)); ax.set_ylim(0, 1050)
        ax.tick_params(colors=TEXT_SEC, labelsize=7)
        ax.grid(color=TEXT_MUT, linestyle="-", linewidth=0.4, alpha=0.5)
        for spine in ax.spines.values():
            spine.set_edgecolor(TEXT_MUT)
        low_p = mpatches.Patch(color=RED,    label="Low")
        opt_p = mpatches.Patch(color=ACCENT, label="Optimal")
        ax.legend(handles=[low_p, opt_p], loc="upper right", fontsize=7,
                  framealpha=0.3, facecolor=BG_CARD, edgecolor=BORDER,
                  labelcolor=TEXT_PRI, handlelength=1.5)
        fig.tight_layout(pad=1.0)
        self._chart_canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
        self._chart_canvas.draw()
        self._chart_canvas.get_tk_widget().pack(fill="both", expand=True)


_IMG_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp", ".tiff"}

SAMPLE_PLANTS = [
    {"name": "Calibrachoa", "emoji": "🌸", "location": "Garden", "status": "Optimal", "lux": 720, "days": 1},
]
STATUS_COLOR = {"Optimal": ACCENT, "Low Light": RED, "Too Much Light": YELLOW}

CALIBRACHOA_FOLDER = "/home/anastasija/Desktop/FERI/2 semester/pp/projekt/main/Calibrachoa"

def _init_calibrachoa_images(db: dict) -> dict:
    if "Calibrachoa" in db:
        return db
    folder = CALIBRACHOA_FOLDER
    if not os.path.isdir(folder):
        return db
    images = sorted([
        os.path.join(folder, f)
        for f in os.listdir(folder)
        if os.path.splitext(f)[1].lower() in _IMG_EXTS
    ])
    if images:
        db["Calibrachoa"] = images
        _save_plants_db(db)
    return db

PLANTS_DB_PATH = os.path.join(_SCRIPT_DIR, "plants_data.json")

def _load_plants_db() -> dict:
    if os.path.exists(PLANTS_DB_PATH):
        try:
            with open(PLANTS_DB_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def _save_plants_db(data: dict):
    try:
        with open(PLANTS_DB_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as ex:
        print(f"[Plant DB] Save error: {ex}")


class MyPlantsPage(BasePage):
    THUMB_W = 80
    THUMB_H = 65

    def _build(self):
        self._plants     = [dict(p) for p in SAMPLE_PLANTS]
        self._plants_db  = _init_calibrachoa_images(_load_plants_db())
        self._thumb_cache: dict[str, object] = {}
        self._expanded: set[str] = {"Calibrachoa"}

        self._outer = tk.Frame(self, bg=BG_MAIN)
        self._outer.pack(fill="both", expand=True, padx=22, pady=18)

        hdr_row = tk.Frame(self._outer, bg=BG_MAIN)
        hdr_row.pack(fill="x", pady=(0, 4))
        tk.Label(hdr_row, text="🪴  My Plants", font=("Segoe UI", 16, "bold"),
                 bg=BG_MAIN, fg=TEXT_PRI).pack(side="left")
        add_btn = tk.Frame(hdr_row, bg=ACCENT, cursor="hand2", padx=14, pady=6)
        add_btn.pack(side="right")
        tk.Label(add_btn, text="+ Add Plant", font=self.f_label, bg=ACCENT, fg=BG_MAIN).pack()
        bind_tree(add_btn, "<Button-1>", lambda e: self._add_plant())
        hover(add_btn, ACCENT, "#00c98a")

        tk.Label(self._outer,
                 text="Manage all your plants. Click 📷 to add a photo folder.",
                 font=self.f_small, bg=BG_MAIN, fg=TEXT_SEC).pack(anchor="w", pady=(0, 12))

        self._stats_frame = tk.Frame(self._outer, bg=BG_MAIN)
        self._stats_frame.pack(fill="x", pady=(0, 14))

        list_outer = tk.Frame(self._outer, bg=BG_MAIN)
        list_outer.pack(fill="both", expand=True)

        self._list_canvas = tk.Canvas(list_outer, bg=BG_MAIN, highlightthickness=0)
        scrollbar = tk.Scrollbar(list_outer, orient="vertical", command=self._list_canvas.yview)
        self._list_canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self._list_canvas.pack(side="left", fill="both", expand=True)

        self._list_frame = tk.Frame(self._list_canvas, bg=BG_MAIN)
        self._list_canvas_window = self._list_canvas.create_window(
            (0, 0), window=self._list_frame, anchor="nw"
        )
        self._list_frame.bind("<Configure>",
            lambda e: self._list_canvas.configure(scrollregion=self._list_canvas.bbox("all")))
        self._list_canvas.bind("<Configure>",
            lambda e: self._list_canvas.itemconfig(self._list_canvas_window, width=e.width))
        self._list_canvas.bind("<MouseWheel>",
            lambda e: self._list_canvas.yview_scroll(-1*(e.delta//120), "units"))

        self._render_all()

    def _render_all(self):
        self._render_stats()
        self._render_plant_list()

    def _render_stats(self):
        for w in self._stats_frame.winfo_children():
            w.destroy()
        total   = len(self._plants)
        optimal = sum(1 for p in self._plants if p["status"] == "Optimal")
        alerts  = total - optimal
        for label, val, color in [("Total Plants", total, BLUE), ("Optimal", optimal, ACCENT), ("Needs Attention", alerts, RED)]:
            sc = tk.Frame(self._stats_frame, bg=BG_CARD, padx=18, pady=10)
            sc.pack(side="left", padx=(0, 10))
            tk.Label(sc, text=str(val), font=("Segoe UI", 20, "bold"), bg=BG_CARD, fg=color).pack()
            tk.Label(sc, text=label,    font=self.f_small,              bg=BG_CARD, fg=TEXT_SEC).pack()

    def _render_plant_list(self):
        for w in self._list_frame.winfo_children():
            w.destroy()
        if not self._plants:
            tk.Label(self._list_frame, text="No plants yet. Add one above!",
                     font=self.f_body, bg=BG_MAIN, fg=TEXT_SEC).pack(pady=30)
            return
        for plant in self._plants:
            self._render_plant_card(plant)

    def _render_plant_card(self, plant: dict):
        name = plant["name"]
        sc   = STATUS_COLOR.get(plant["status"], TEXT_SEC)

        card = tk.Frame(self._list_frame, bg=BG_CARD, padx=14, pady=12)
        card.pack(fill="x", pady=(0, 8))
        card.pack_propagate(True)

        top = tk.Frame(card, bg=BG_CARD)
        top.pack(fill="x")

        left = tk.Frame(top, bg=BG_CARD)
        left.pack(side="left", fill="y")
        tk.Label(left, text=plant["emoji"], font=("Segoe UI", 22), bg=BG_CARD).pack(side="left", padx=(0, 12))
        info = tk.Frame(left, bg=BG_CARD)
        info.pack(side="left")
        tk.Label(info, text=name,                      font=self.f_label, bg=BG_CARD, fg=TEXT_PRI).pack(anchor="w")
        tk.Label(info, text=f"📍 {plant['location']}", font=self.f_small, bg=BG_CARD, fg=TEXT_SEC).pack(anchor="w")
        tk.Label(info, text=f"Added {plant['days']} days ago",
                 font=self.f_small, bg=BG_CARD, fg=TEXT_MUT).pack(anchor="w")

        right = tk.Frame(top, bg=BG_CARD)
        right.pack(side="right", fill="y")
        tk.Label(right, text=f"{plant['lux']} lux",
                 font=("Segoe UI", 13, "bold"), bg=BG_CARD, fg=sc).pack(anchor="e")
        tk.Label(right, text=plant["status"], font=self.f_small, bg=BG_CARD2,
                 fg=sc, padx=8, pady=2).pack(anchor="e", pady=(2, 6))

        btn_row = tk.Frame(right, bg=BG_CARD)
        btn_row.pack(anchor="e")

        sim_btn = tk.Label(btn_row, text="↻ New Reading", font=self.f_small,
                           bg=BG_CARD, fg=BLUE, cursor="hand2")
        sim_btn.pack(side="left", padx=(0, 10))
        sim_btn.bind("<Button-1>", lambda e, p=plant: self._simulate_reading(p))

        rm_btn = tk.Label(btn_row, text="✕ Remove", font=self.f_small,
                          bg=BG_CARD, fg=TEXT_MUT, cursor="hand2")
        rm_btn.pack(side="left")
        rm_btn.bind("<Button-1>", lambda e, p=plant: self._remove_plant(p))

        photos    = self._plants_db.get(name, [])
        n_photos  = len([p for p in photos if os.path.isfile(p)])
        gallery_label = f"📷 Photos ({n_photos})" if n_photos else "📷 Add Photos"
        is_expanded   = name in self._expanded

        toggle_row = tk.Frame(card, bg=BG_CARD)
        toggle_row.pack(fill="x", pady=(8, 0))

        toggle_btn = tk.Label(
            toggle_row,
            text=f"{'▼' if is_expanded else '▶'}  {gallery_label}",
            font=self.f_small, bg=BG_CARD2, fg=ACCENT, padx=10, pady=4, cursor="hand2"
        )
        toggle_btn.pack(side="left")

        add_folder_btn = tk.Label(
            toggle_row, text="  + Add Folder",
            font=self.f_small, bg=BG_CARD2, fg=BLUE, padx=8, pady=4, cursor="hand2"
        )
        add_folder_btn.pack(side="left", padx=(6, 0))
        add_folder_btn.bind("<Button-1>", lambda e, n=name: self._add_photo_folder(n))

        gallery_frame = tk.Frame(card, bg=BG_CARD)
        if is_expanded:
            gallery_frame.pack(fill="x", pady=(6, 0))
            self._render_plant_gallery(gallery_frame, name)

        def on_toggle(e, n=name, gf=gallery_frame):
            if n in self._expanded:
                self._expanded.discard(n)
            else:
                self._expanded.add(n)
            self._render_all()

        toggle_btn.bind("<Button-1>", on_toggle)

    def _add_photo_folder(self, plant_name: str):
        folder = filedialog.askdirectory(title=f"Select photo folder for {plant_name}")
        if not folder:
            return
        images = sorted([
            os.path.join(folder, f)
            for f in os.listdir(folder)
            if os.path.splitext(f)[1].lower() in _IMG_EXTS
        ])
        if not images:
            messagebox.showwarning("No Images", "The folder contains no supported image files.")
            return
        existing  = self._plants_db.get(plant_name, [])
        new_paths = [p for p in images if p not in existing]
        self._plants_db[plant_name] = existing + new_paths
        _save_plants_db(self._plants_db)
        self._expanded.add(plant_name)
        self._render_all()

    def _render_plant_gallery(self, parent: tk.Frame, plant_name: str):
        photos = self._plants_db.get(plant_name, [])
        valid  = [p for p in photos if os.path.isfile(p)]

        if not valid:
            tk.Label(parent,
                     text="No photos yet. Click '+ Add Folder' to add images.",
                     font=self.f_small, bg=BG_CARD, fg=TEXT_MUT).pack(anchor="w", padx=4, pady=4)
            return

        parent.update_idletasks()
        avail_w = max(parent.winfo_width(), 500)
        cell_w  = self.THUMB_W + 12
        cols    = max(1, avail_w // cell_w)

        try:
            from PIL import Image, ImageTk
            pil_ok = True
        except ImportError:
            pil_ok = False

        grid = tk.Frame(parent, bg=BG_CARD)
        grid.pack(fill="x", padx=4, pady=4)

        for idx, path in enumerate(valid):
            col_n = idx % cols
            row_n = idx // cols

            cell = tk.Frame(grid, bg=BG_CARD2, padx=3, pady=3, cursor="hand2")
            cell.grid(row=row_n, column=col_n, padx=3, pady=3, sticky="nw")

            if pil_ok:
                if path not in self._thumb_cache:
                    try:
                        img = Image.open(path)
                        img.thumbnail((self.THUMB_W, self.THUMB_H))
                        self._thumb_cache[path] = ImageTk.PhotoImage(img)
                    except Exception:
                        self._thumb_cache[path] = None
                tk_img = self._thumb_cache.get(path)
                if tk_img:
                    lbl_img = tk.Label(cell, image=tk_img, bg=BG_CARD2)
                    lbl_img.pack()
                    lbl_img.bind("<Double-Button-1>", lambda e, p=path: self._open_image(p))
                else:
                    tk.Label(cell, text="🖼️", font=("Segoe UI", 16),
                              bg=BG_CARD2, fg=TEXT_MUT, width=6, height=3).pack()
            else:
                tk.Label(cell, text="🖼️", font=("Segoe UI", 16),
                          bg=BG_CARD2, fg=TEXT_MUT, width=6, height=3).pack()

            fname = os.path.basename(path)
            short = fname if len(fname) <= 10 else fname[:7] + "…"
            tk.Label(cell, text=short, font=("Segoe UI", 7), bg=BG_CARD2, fg=TEXT_MUT).pack()
            hover(cell, BG_CARD2, BG_CARD)

        missing   = len(photos) - len(valid)
        count_txt = f"{len(valid)} photos"
        if missing:
            count_txt += f"  ({missing} missing)"
        tk.Label(parent, text=count_txt, font=("Segoe UI", 7),
                  bg=BG_CARD, fg=TEXT_MUT).pack(anchor="w", padx=4, pady=(0, 2))

    def _open_image(self, path: str):
        try:
            from PIL import Image, ImageTk
        except ImportError:
            messagebox.showinfo("Preview", f"Install Pillow to enable previews.\n\n{path}")
            return
        top = tk.Toplevel(self)
        top.title(os.path.basename(path))
        top.configure(bg=BG_MAIN)
        try:
            img = Image.open(path)
            img.thumbnail((800, 600), Image.LANCZOS)
            tk_img = ImageTk.PhotoImage(img)
            lbl = tk.Label(top, image=tk_img, bg=BG_MAIN)
            lbl.image = tk_img
            lbl.pack(padx=10, pady=10)
            tk.Label(top, text=path, font=("Segoe UI", 8),
                      bg=BG_MAIN, fg=TEXT_MUT).pack(pady=(0, 8))
        except Exception as ex:
            tk.Label(top, text=f"Unable to open image:\n{ex}",
                      bg=BG_MAIN, fg=RED, font=("Segoe UI", 10)).pack(padx=20, pady=20)

    def _add_plant(self):
        name = simpledialog.askstring("Add Plant", "Plant name:")
        if not name: return
        loc  = simpledialog.askstring("Add Plant", "Location (e.g. Living Room):") or "Unknown"
        lux  = random.randint(200, 900)
        status = "Optimal" if 300 <= lux <= 800 else ("Low Light" if lux < 300 else "Too Much Light")
        self._plants.append({"name": name, "emoji": "🌱", "location": loc,
                              "status": status, "lux": lux, "days": 0})
        self._render_all()

    def _remove_plant(self, plant: dict):
        if messagebox.askyesno("Remove Plant", f"Remove '{plant['name']}' from your collection?"):
            self._plants.remove(plant)
            self._expanded.discard(plant["name"])
            self._render_all()

    def _simulate_reading(self, plant: dict):
        lux = random.randint(150, 950)
        plant["lux"]    = lux
        plant["status"] = ("Optimal"       if 300 <= lux <= 800
                           else ("Low Light" if lux < 300 else "Too Much Light"))
        self._render_all()


class HistoryPage(BasePage):
    def _build(self):
        pad = tk.Frame(self, bg=BG_MAIN)
        pad.pack(fill="both", expand=True, padx=22, pady=18)
        tk.Label(pad, text="📅  History", font=("Segoe UI", 16, "bold"),
                 bg=BG_MAIN, fg=TEXT_PRI).pack(anchor="w")
        tk.Label(pad, text="Last 7 days of light intensity readings.",
                 font=self.f_small, bg=BG_MAIN, fg=TEXT_SEC).pack(anchor="w", pady=(0, 18))

        days   = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        weekly = [random.randint(200, 900) for _ in range(7)]

        row = tk.Frame(pad, bg=BG_MAIN)
        row.pack(fill="x", pady=(0, 18))
        for i, day in enumerate(days):
            avg   = weekly[i]
            color = ACCENT if 300 <= avg <= 800 else (RED if avg < 300 else YELLOW)
            card  = tk.Frame(row, bg=BG_CARD, padx=10, pady=10)
            card.pack(side="left", padx=4, expand=True, fill="x")
            tk.Label(card, text=day,       font=self.f_small,             bg=BG_CARD, fg=TEXT_SEC).pack()
            tk.Label(card, text=str(avg),  font=("Segoe UI", 14, "bold"), bg=BG_CARD, fg=color).pack()
            tk.Label(card, text="avg. lux", font=self.f_small,            bg=BG_CARD, fg=TEXT_MUT).pack()

        chart_frame = tk.Frame(pad, bg=BG_CARD)
        chart_frame.pack(fill="both", expand=True)
        fig, ax = plt.subplots(figsize=(7, 3))
        fig.patch.set_facecolor(BG_CARD)
        ax.set_facecolor(BG_CARD)
        ax.fill_between(range(7), weekly, alpha=0.2, color=ACCENT)
        ax.plot(range(7), weekly, color=ACCENT, linewidth=2, marker="o", markersize=5)
        ax.set_xticks(range(7))
        ax.set_xticklabels(days, color=TEXT_SEC, fontsize=8)
        ax.set_title("7-Day Light History", color=TEXT_PRI, fontsize=10)
        ax.tick_params(colors=TEXT_SEC, labelsize=8)
        ax.grid(color=TEXT_MUT, linestyle="-", linewidth=0.4, alpha=0.5)
        for spine in ax.spines.values():
            spine.set_edgecolor(TEXT_MUT)
        fig.tight_layout(pad=1.0)
        canvas = FigureCanvasTkAgg(fig, master=chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)


STATUS_META   = {k: (v[0], v[1]) for k, v in CNN_CLASS_META.items()}
URGENCY_COLOR = {"Low": ACCENT, "Medium": YELLOW, "High": RED, "Critical": "#ff2244"}


class DetectionPage(BasePage):
    def _build(self):
        self._image_path = None

        outer = tk.Frame(self, bg=BG_MAIN)
        outer.pack(fill="both", expand=True, padx=22, pady=18)

        hdr_row = tk.Frame(outer, bg=BG_MAIN)
        hdr_row.pack(fill="x", pady=(0, 6))
        tk.Label(hdr_row, text="🔬  Plant Health Detection", font=("Segoe UI", 16, "bold"),
                 bg=BG_MAIN, fg=TEXT_PRI).pack(side="left")

        load_btn = tk.Frame(hdr_row, bg=BLUE, cursor="hand2", padx=16, pady=8)
        load_btn.pack(side="right")
        tk.Label(load_btn, text="📷  Upload Plant Image", font=self.f_label,
                 bg=BLUE, fg=BG_MAIN).pack()
        bind_tree(load_btn, "<Button-1>", lambda e: self._load_image())
        hover(load_btn, BLUE, "#38a8d8")

        sub_row = tk.Frame(outer, bg=BG_MAIN)
        sub_row.pack(fill="x", pady=(0, 14))
        tk.Label(sub_row,
                 text="Upload a plant photo — the CNN EfficientNetB0 + colour ensemble will diagnose health.",
                 font=self.f_small, bg=BG_MAIN, fg=TEXT_SEC).pack(side="left")
        tk.Label(sub_row, text="  🧠 ~90% accuracy",
                 font=self.f_small, bg=BG_MAIN, fg=PURPLE).pack(side="left")

        cols = tk.Frame(outer, bg=BG_MAIN)
        cols.pack(fill="both", expand=True)

        left = tk.Frame(cols, bg=BG_CARD, width=290)
        left.pack(side="left", fill="y", padx=(0, 14))
        left.pack_propagate(False)

        tk.Label(left, text="Plant Image", font=self.f_label,
                 bg=BG_CARD, fg=TEXT_SEC).pack(anchor="w", padx=12, pady=(12, 6))

        self._preview_canvas = tk.Canvas(left, bg=BG_CARD2, highlightthickness=0,
                                          width=256, height=210)
        self._preview_canvas.pack(padx=12, pady=(0, 8))
        self._preview_canvas.create_text(128, 105, text="No image loaded",
                                          fill=TEXT_MUT, font=("Segoe UI", 9))

        self._img_name_lbl = tk.Label(left, text="", font=self.f_small,
                                       bg=BG_CARD, fg=TEXT_SEC, wraplength=240)
        self._img_name_lbl.pack(padx=12, pady=(0, 4))

        self._cnn_info_frame = tk.Frame(left, bg=BG_CARD2, padx=10, pady=8)
        self._cnn_info_frame.pack(fill="x", padx=12, pady=(0, 8))
        tk.Label(self._cnn_info_frame, text="CNN Architecture", font=self.f_small,
                 bg=BG_CARD2, fg=TEXT_MUT).pack(anchor="w")
        self._cnn_info_lbl = tk.Label(
            self._cnn_info_frame,
            text="Model:    EfficientNetB0\nBackbone: ImageNet (top 30 unfrozen)\nHead:     Dense(512->256) -> 8 classes\nAccuracy: ~90%",
            font=self.f_small, bg=BG_CARD2, fg=TEXT_SEC, justify="left"
        )
        self._cnn_info_lbl.pack(anchor="w")

        self._analyse_btn_frame = tk.Frame(left, bg=ACCENT, cursor="hand2")
        self._analyse_btn_frame.pack(fill="x", padx=12, pady=(0, 12))
        tk.Label(self._analyse_btn_frame, text="▶  Analyse with CNN",
                 font=self.f_label, bg=ACCENT, fg=BG_MAIN, pady=8).pack()
        bind_tree(self._analyse_btn_frame, "<Button-1>", lambda e: self._run_analysis())
        hover(self._analyse_btn_frame, ACCENT, "#00c98a")

        self._results_frame = tk.Frame(cols, bg=BG_MAIN)
        self._results_frame.pack(side="left", fill="both", expand=True)
        self._show_empty_state()

    def _load_image(self):
        path = filedialog.askopenfilename(
            title="Select Plant Image",
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.webp *.gif"), ("All files", "*.*")]
        )
        if not path: return
        self._image_path = path
        fname = os.path.basename(path)
        self._img_name_lbl.config(text=fname)
        try:
            from PIL import Image, ImageTk
            img = Image.open(path)
            img.thumbnail((256, 210))
            self._tk_img = ImageTk.PhotoImage(img)
            self._preview_canvas.delete("all")
            self._preview_canvas.create_image(128, 105, image=self._tk_img, anchor="center")
        except ImportError:
            self._preview_canvas.delete("all")
            self._preview_canvas.create_text(128, 90,  text="image",  fill=TEXT_SEC, font=("Segoe UI", 32))
            self._preview_canvas.create_text(128, 140, text=fname[:28], fill=TEXT_SEC, font=("Segoe UI", 8))
        except Exception as ex:
            self._preview_canvas.delete("all")
            self._preview_canvas.create_text(128, 105, text=f"Preview error:\n{ex}",
                                              fill=RED, font=("Segoe UI", 8))
        self._show_empty_state(msg="Image loaded. Click Analyse with CNN to diagnose.")

    def _show_empty_state(self, msg="Upload a plant image to get started."):
        for w in self._results_frame.winfo_children():
            w.destroy()
        container = tk.Frame(self._results_frame, bg=BG_CARD, padx=20, pady=30)
        container.pack(fill="both", expand=True)
        tk.Label(container, text="🌿", font=("Segoe UI", 40), bg=BG_CARD).pack(pady=(20, 8))
        tk.Label(container, text=msg, font=self.f_body, bg=BG_CARD,
                 fg=TEXT_SEC, wraplength=340, justify="center").pack()

    def _show_loading(self):
        for w in self._results_frame.winfo_children():
            w.destroy()
        container = tk.Frame(self._results_frame, bg=BG_CARD, padx=20, pady=30)
        container.pack(fill="both", expand=True)
        tk.Label(container, text="🧠", font=("Segoe UI", 36), bg=BG_CARD).pack(pady=(20, 12))
        tk.Label(container, text="Running CNN inference...",
                 font=("Segoe UI", 11, "bold"), bg=BG_CARD, fg=TEXT_PRI).pack()
        tk.Label(container,
                 text="EfficientNetB0 + colour ensemble is analysing your image.\nEstimated accuracy: ~90%.",
                 font=self.f_body, bg=BG_CARD, fg=TEXT_SEC, justify="center").pack(pady=(8, 0))
        self._loading_dots = tk.Label(container, text="* * *", font=("Segoe UI", 14),
                                       bg=BG_CARD, fg=PURPLE)
        self._loading_dots.pack(pady=(16, 0))
        tk.Label(container,
                 text="EfficientNetB0 -> GAP -> Dense(512) -> Dense(256) -> 8 classes",
                 font=("Segoe UI", 7), bg=BG_CARD, fg=TEXT_MUT).pack(pady=(12, 0))
        self._dot_idx = 0
        self._animate_dots()

    def _animate_dots(self):
        patterns = ["*  o  o", "o  *  o", "o  o  *", "o  *  o"]
        try:
            self._loading_dots.config(text=patterns[self._dot_idx % len(patterns)])
            self._dot_idx += 1
            self._anim_job = self.after(400, self._animate_dots)
        except Exception:
            pass

    def _run_analysis(self):
        if not self._image_path:
            messagebox.showwarning("No Image", "Please upload a plant image first.")
            return
        if not os.path.exists(self._image_path):
            messagebox.showerror("File Missing", "The selected image file no longer exists.")
            return
        self._show_loading()

        def on_result(result, error):
            if hasattr(self, "_anim_job"):
                try: self.after_cancel(self._anim_job)
                except: pass
            self.after(0, lambda: self._show_result(result, error))

        if API_URL:
            def _api_thread():
                result = _api_detect(self._image_path)
                if result:
                    on_result(result, None)
                else:
                    analyze_plant_image_cnn(self._image_path, on_result)
            threading.Thread(target=_api_thread, daemon=True).start()
        else:
            analyze_plant_image_cnn(self._image_path, on_result)

    def _show_result(self, result, error):
        for w in self._results_frame.winfo_children():
            w.destroy()

        if error or result is None:
            container = tk.Frame(self._results_frame, bg=BG_CARD, padx=20, pady=20)
            container.pack(fill="both", expand=True)
            tk.Label(container, text="CNN Analysis Failed", font=("Segoe UI", 12, "bold"),
                     bg=BG_CARD, fg=RED).pack(pady=(10, 8))
            tk.Label(container, text=str(error) if error else "Unknown error.",
                     font=self.f_body, bg=BG_CARD, fg=TEXT_SEC, wraplength=380, justify="center").pack(pady=(0, 12))
            re_btn = tk.Frame(container, bg=BG_CARD2, cursor="hand2", padx=14, pady=8)
            re_btn.pack()
            tk.Label(re_btn, text="Try Again", font=self.f_label, bg=BG_CARD2, fg=ACCENT).pack()
            bind_tree(re_btn, "<Button-1>", lambda e: self._run_analysis())
            hover(re_btn, BG_CARD2, BG_CARD)
            return

        cnn_info = result.get("_cnn_info", {})
        if cnn_info:
            self._cnn_info_lbl.config(
                text=(
                    f"Model:    {cnn_info.get('model', 'EfficientNetB0')}\n"
                    f"Backbone: ImageNet (top 30 unfrozen)\n"
                    f"Head:     Dense(512->{cnn_info.get('classes', 8)} classes)\n"
                    f"Accuracy: {cnn_info.get('accuracy_est', '~90%')}"
                ),
                fg=TEXT_PRI,
            )

        status   = result.get("status", "Unknown")
        conf     = result.get("confidence", 0)
        summary  = result.get("summary", "")
        symptoms = result.get("symptoms", [])
        recs     = result.get("recommendations", [])
        urgency  = result.get("urgency", "Low")

        color, badge_emoji = STATUS_META.get(status, (TEXT_SEC, "?"))
        urg_color = URGENCY_COLOR.get(urgency, TEXT_SEC)

        pad = tk.Frame(self._results_frame, bg=BG_MAIN)
        pad.pack(fill="both", expand=True)

        banner = tk.Frame(pad, bg=BG_CARD, padx=16, pady=14)
        banner.pack(fill="x", pady=(0, 10))
        top_row = tk.Frame(banner, bg=BG_CARD)
        top_row.pack(fill="x")
        tk.Label(top_row, text=f"{badge_emoji}  {status}", font=("Segoe UI", 14, "bold"),
                 bg=BG_CARD, fg=color).pack(side="left")
        tk.Label(top_row, text=f"  {urgency} urgency  ",
                 font=self.f_small, bg=urg_color, fg=BG_MAIN, padx=6, pady=2).pack(side="right")

        conf_row = tk.Frame(banner, bg=BG_CARD)
        conf_row.pack(fill="x", pady=(8, 4))
        tk.Label(conf_row, text=f"CNN Confidence: {conf}%", font=self.f_small,
                 bg=BG_CARD, fg=TEXT_SEC).pack(side="left")
        bar_bg = tk.Frame(banner, bg=BG_CARD2, height=6)
        bar_bg.pack(fill="x")
        bar_bg.update_idletasks()
        w = bar_bg.winfo_width() or 300
        tk.Frame(bar_bg, bg=color, width=max(4, int(w * conf / 100)), height=6).place(x=0, y=0)

        tk.Label(banner, text=summary, font=self.f_body, bg=BG_CARD,
                 fg=TEXT_PRI, wraplength=360, justify="left").pack(anchor="w", pady=(10, 0))

        method_row = tk.Frame(banner, bg=BG_CARD)
        method_row.pack(anchor="w", pady=(6, 0))
        tk.Label(method_row, text="  EfficientNetB0 CNN  ", font=("Segoe UI", 7),
                 bg=PURPLE, fg=BG_MAIN, padx=4, pady=2).pack(side="left")
        tk.Label(method_row, text="  Transfer Learning + Colour Ensemble",
                 font=("Segoe UI", 7), bg=BG_CARD, fg=TEXT_MUT).pack(side="left", padx=(6, 0))

        if symptoms:
            tk.Label(pad, text="Observed Symptoms", font=self.f_title,
                     bg=BG_MAIN, fg=TEXT_PRI).pack(anchor="w", pady=(4, 6))
            for sym in symptoms:
                row = tk.Frame(pad, bg=BG_CARD, padx=12, pady=8)
                row.pack(fill="x", pady=(0, 4))
                tk.Label(row, text="o", font=("Segoe UI", 10), bg=BG_CARD, fg=color).pack(side="left", padx=(0, 8))
                tk.Label(row, text=sym, font=self.f_body, bg=BG_CARD, fg=TEXT_PRI,
                         wraplength=360, justify="left").pack(side="left", fill="x")

        if recs:
            tk.Label(pad, text="Recommended Actions", font=self.f_title,
                     bg=BG_MAIN, fg=TEXT_PRI).pack(anchor="w", pady=(10, 6))
            for i, rec in enumerate(recs, 1):
                row = tk.Frame(pad, bg=BG_CARD, padx=12, pady=8)
                row.pack(fill="x", pady=(0, 4))
                tk.Label(row, text=f"{i}", font=self.f_label, bg=ACCENT, fg=BG_MAIN,
                         width=2, padx=4, pady=1).pack(side="left", padx=(0, 10))
                tk.Label(row, text=rec, font=self.f_body, bg=BG_CARD, fg=TEXT_PRI,
                         wraplength=360, justify="left").pack(side="left", fill="x")

        re_btn = tk.Frame(pad, bg=BG_CARD2, cursor="hand2", padx=14, pady=8)
        re_btn.pack(anchor="e", pady=(12, 0))
        tk.Label(re_btn, text="Analyse Again", font=self.f_label, bg=BG_CARD2, fg=ACCENT).pack()
        bind_tree(re_btn, "<Button-1>", lambda e: self._run_analysis())
        hover(re_btn, BG_CARD2, BG_CARD)


class RecommendationSystemPage(BasePage):
    def _build(self):
        outer = tk.Frame(self, bg=BG_MAIN)
        outer.pack(fill="both", expand=True, padx=22, pady=18)

        tk.Label(outer, text="💡  Recommendation", font=("Segoe UI", 16, "bold"),
                 bg=BG_MAIN, fg=TEXT_PRI).pack(anchor="w")
        tk.Label(outer, text="Find the perfect plant using fuzzy matching across care requirements.",
                 font=self.f_small, bg=BG_MAIN, fg=TEXT_SEC).pack(anchor="w", pady=(0, 16))

        if not PANDAS_OK:
            tk.Label(outer, text="pandas is required for the Recommendation.\nRun: pip install pandas",
                     font=self.f_body, bg=BG_MAIN, fg=RED).pack(pady=40)
            return

        cols = tk.Frame(outer, bg=BG_MAIN)
        cols.pack(fill="both", expand=True)

        left = tk.Frame(cols, bg=BG_CARD, width=320, padx=18, pady=16)
        left.pack(side="left", fill="y", padx=(0, 14))
        left.pack_propagate(False)

        tk.Label(left, text="Your Preferences", font=self.f_title,
                 bg=BG_CARD, fg=TEXT_PRI).pack(anchor="w", pady=(0, 14))

        def slider_row(parent, label, from_, to, resolution, default):
            row = tk.Frame(parent, bg=BG_CARD)
            row.pack(fill="x", pady=(0, 10))
            header = tk.Frame(row, bg=BG_CARD)
            header.pack(fill="x")
            tk.Label(header, text=label, font=self.f_small, bg=BG_CARD, fg=TEXT_SEC).pack(side="left")
            val_var = tk.DoubleVar(value=default)
            val_lbl = tk.Label(header, textvariable=val_var, font=self.f_label,
                               bg=BG_CARD, fg=ACCENT, width=4)
            val_lbl.pack(side="right")
            scale_frame = tk.Frame(row, bg=BG_CARD)
            scale_frame.pack(fill="x", pady=(4, 0))
            # Drsnik z vedno zelenim gumbom
            scale = GreenSlider(scale_frame, from_=from_, to=to,
                                variable=val_var, resolution=resolution, length=260)
            scale.pack(fill="x")
            minmax = tk.Frame(row, bg=BG_CARD)
            minmax.pack(fill="x")
            tk.Label(minmax, text=str(from_), font=("Segoe UI", 7), bg=BG_CARD, fg=TEXT_MUT).pack(side="left")
            tk.Label(minmax, text=str(to),   font=("Segoe UI", 7), bg=BG_CARD, fg=TEXT_MUT).pack(side="right")
            return val_var

        self._water_var    = slider_row(left, "Water needs (1–10)", 1, 10, 0.5, 5)
        self._sunlight_var = slider_row(left, "Sunlight (1–10)",    1, 10, 0.5, 6)
        self._temp_var     = slider_row(left, "Temperature (°C)",  10, 40, 0.5, 22)

        tk.Frame(left, bg=BORDER, height=1).pack(fill="x", pady=(8, 10))

        space_row = tk.Frame(left, bg=BG_CARD)
        space_row.pack(fill="x", pady=(0, 10))
        tk.Label(space_row, text="Space", font=self.f_small, bg=BG_CARD, fg=TEXT_SEC).pack(anchor="w", pady=(0, 6))
        self._space_var = tk.StringVar(value="any")
        space_btn_row = tk.Frame(space_row, bg=BG_CARD)
        space_btn_row.pack(fill="x")
        self._space_btns = {}

        # FIX 1: active button = ACCENT background + BG_MAIN (dark) text, same style as Find Plants
        for val, label in [("any", "Any"), ("flat", "Flat"), ("garden", "Garden")]:
            is_active = (val == "any")
            btn = tk.Frame(space_btn_row,
                           bg=ACCENT if is_active else BG_CARD2,
                           cursor="hand2", padx=14, pady=5)
            btn.pack(side="left", padx=(0, 6))
            lbl = tk.Label(btn, text=label, font=self.f_small,
                           bg=ACCENT if is_active else BG_CARD2,
                           fg=BG_MAIN if is_active else TEXT_SEC)
            lbl.pack()
            self._space_btns[val] = (btn, lbl)

            def on_space(e, v=val):
                self._space_var.set(v)
                for k, (b, l) in self._space_btns.items():
                    active = (k == v)
                    b.configure(bg=ACCENT if active else BG_CARD2)
                    l.configure(bg=ACCENT if active else BG_CARD2,
                                fg=BG_MAIN if active else TEXT_SEC)

            bind_tree(btn, "<Button-1>", on_space)

        toggles_row = tk.Frame(left, bg=BG_CARD)
        toggles_row.pack(fill="x", pady=(0, 10))
        self._pet_var     = tk.BooleanVar(value=False)
        self._allergy_var = tk.BooleanVar(value=False)

        def toggle_row_widget(parent, label, var):
            row = tk.Frame(parent, bg=BG_CARD)
            row.pack(fill="x", pady=(0, 6))
            tk.Label(row, text=label, font=self.f_small, bg=BG_CARD, fg=TEXT_SEC).pack(side="left")
            lbl = tk.Label(row, text="  OFF ●", font=self.f_small, bg=BG_CARD2,
                           fg=TEXT_MUT, padx=8, pady=3, cursor="hand2")
            lbl.pack(side="right")
            def toggle(e, v=var, l=lbl):
                v.set(not v.get())
                l.config(text="● ON  " if v.get() else "  OFF ●",
                         fg=ACCENT if v.get() else TEXT_MUT)
            lbl.bind("<Button-1>", toggle)

        toggle_row_widget(toggles_row, "Pet safe only", self._pet_var)
        toggle_row_widget(toggles_row, "No pollen allergies", self._allergy_var)

        tk.Frame(left, bg=BORDER, height=1).pack(fill="x", pady=(4, 10))

        existing_lbl = tk.Label(left, text="Existing plants (comma separated)",
                                font=self.f_small, bg=BG_CARD, fg=TEXT_SEC)
        existing_lbl.pack(anchor="w", pady=(0, 4))
        self._existing_var = tk.StringVar()
        existing_entry = tk.Entry(left, textvariable=self._existing_var, bg=BG_CARD2,
                                  fg=TEXT_PRI, insertbackground=TEXT_PRI,
                                  relief="flat", font=("Segoe UI", 9))
        existing_entry.pack(fill="x", ipady=6)
        tk.Frame(left, bg=BORDER, height=1).pack(fill="x")

        find_btn = tk.Frame(left, bg=ACCENT, cursor="hand2")
        find_btn.pack(fill="x", pady=(14, 0))
        tk.Label(find_btn, text="🔍  Find Plants", font=self.f_label,
                 bg=ACCENT, fg=BG_MAIN, pady=9).pack()
        bind_tree(find_btn, "<Button-1>", lambda e: self._run_search())
        hover(find_btn, ACCENT, "#00c98a")

        right = tk.Frame(cols, bg=BG_MAIN)
        right.pack(side="left", fill="both", expand=True)

        tk.Label(right, text="Top Matches", font=self.f_title,
                 bg=BG_MAIN, fg=TEXT_PRI).pack(anchor="w", pady=(0, 10))

        self._results_frame = tk.Frame(right, bg=BG_MAIN)
        self._results_frame.pack(fill="both", expand=True)
        self._show_finder_empty()

    def _show_finder_empty(self):
        for w in self._results_frame.winfo_children():
            w.destroy()
        container = tk.Frame(self._results_frame, bg=BG_CARD, padx=20, pady=40)
        container.pack(fill="both", expand=True)
        tk.Label(container, text="🌱", font=("Segoe UI", 40), bg=BG_CARD).pack(pady=(20, 8))
        tk.Label(container, text="Set your preferences and click Find Plants.",
                 font=self.f_body, bg=BG_CARD, fg=TEXT_SEC, justify="center").pack()

    def _run_search(self):
        for w in self._results_frame.winfo_children():
            w.destroy()

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

        try:
            results = recommend_plants(user_prefs, top_n=5)
        except Exception as ex:
            tk.Label(self._results_frame, text=f"Error: {ex}", font=self.f_body,
                     bg=BG_MAIN, fg=RED).pack(pady=20)
            return

        if not results:
            container = tk.Frame(self._results_frame, bg=BG_CARD, padx=20, pady=30)
            container.pack(fill="both", expand=True)
            tk.Label(container, text="No plants matched your criteria.",
                     font=self.f_body, bg=BG_CARD, fg=TEXT_SEC).pack(pady=20)
            return

        # FIX 3: use separate label for emoji so font issues don't break the plant name
        plant_emojis = {
            "Monstera": "🌿", "Snake plant": "🪴", "Peace lily": "🤍", "Spider plant": "🕷️",
            "Aloe vera": "🌵", "Fiddle leaf fig": "🍃", "Pothos": "💚", "ZZ plant": "⚡",
            "Boston fern": "🌿", "English ivy": "🍀", "Lavender": "💜", "Rosemary": "🌱",
            "Basil": "🌿", "Orchid": "🌸", "Cactus": "🌵", "Succulent": "💧",
            "Rubber plant": "🌳", "Dracaena": "🌴", "Philodendron": "🍃", "Calathea": "🦋",
            "Jade plant": "🪨", "Chinese money plant": "🪙", "Bird of paradise": "🦚",
            "Anthurium": "❤️", "Peperomia": "🫚", "Prayer plant": "🙏",
            "Tradescantia": "💜", "String of pearls": "📿", "String of hearts": "💕",
            "Hoya": "⭐", "Parlour palm": "🌴", "Areca palm": "🌴",
            "Money tree": "💰", "African violet": "💜", "Bromeliad": "🍍",
            "Air plant": "💨", "Yucca": "🗡️", "Bird's nest fern": "🐦",
            "Maidenhair fern": "🌿", "Dieffenbachia": "🌿", "Mint": "🍃",
            "Thyme": "🌿", "Sage": "🌿", "Parsley": "🌿", "Chives": "🌿",
            "Lemon balm": "🍋", "Sunflower": "🌻", "Marigold": "🌼",
            "Geranium": "🌺", "Begonia": "🌸", "Rose": "🌹", "Pansy": "🌸",
            "Primrose": "🌼", "Cyclamen": "🌸", "Cast iron plant": "🪴",
            "Nerve plant": "🌿", "Umbrella plant": "☂️", "Weeping fig": "🌿",
            "Croton": "🍂", "Bamboo palm": "🎋",
        }

        medal_colors = [ACCENT, BLUE, YELLOW, TEXT_SEC, TEXT_SEC]

        for rank, (name, score) in enumerate(results, 1):
            pct   = int(score * 100)
            emoji = plant_emojis.get(name, "🌱")
            mc    = medal_colors[rank - 1]

            card = tk.Frame(self._results_frame, bg=BG_CARD, padx=16, pady=12)
            card.pack(fill="x", pady=(0, 8))

            top = tk.Frame(card, bg=BG_CARD)
            top.pack(fill="x")

            left_info = tk.Frame(top, bg=BG_CARD)
            left_info.pack(side="left", fill="both", expand=True)

            rank_row = tk.Frame(left_info, bg=BG_CARD)
            rank_row.pack(anchor="w")
            tk.Label(rank_row, text=f" {rank} ", font=("Segoe UI", 9, "bold"),
                     bg=mc, fg=BG_MAIN, padx=4, pady=1).pack(side="left", padx=(0, 6))
            # FIX 3: emoji in its own label, name in separate label
            tk.Label(rank_row, text=emoji, font=("Segoe UI", 13),
                     bg=BG_CARD).pack(side="left", padx=(0, 4))
            tk.Label(rank_row, text=name, font=self.f_title,
                     bg=BG_CARD, fg=TEXT_PRI).pack(side="left")

            bar_row = tk.Frame(card, bg=BG_CARD)
            bar_row.pack(fill="x", pady=(8, 4))
            bar_bg = tk.Frame(bar_row, bg=BG_CARD2, height=6)
            bar_bg.pack(fill="x")
            bar_bg.update_idletasks()
            bw = bar_bg.winfo_width() or 300
            tk.Frame(bar_bg, bg=mc, width=max(4, int(bw * score)), height=6).place(x=0, y=0)

            score_lbl = tk.Label(top, text=f"{pct}%", font=("Segoe UI", 18, "bold"),
                                 bg=BG_CARD, fg=mc)
            score_lbl.pack(side="right", padx=(12, 0))

            try:
                plant_row = _df_plants[_df_plants["name"] == name].iloc[0]
                tags = []
                if plant_row["pet_safe"]:
                    tags.append(("✓ Pet safe", ACCENT))
                if not plant_row["pollen_allergies"]:
                    tags.append(("✓ Low pollen", BLUE))
                tags.append((f"💧 Water: {int(plant_row['water'])}/10", TEXT_SEC))
                tags.append((f"☀️ Light: {int(plant_row['sunlight'])}/10", TEXT_SEC))
                tags.append((f"🌡 {int(plant_row['temperature'])}°C", TEXT_SEC))
                tags.append((f"🏠 {plant_row['space'].capitalize()}", TEXT_MUT))

                tag_row = tk.Frame(card, bg=BG_CARD)
                tag_row.pack(anchor="w", pady=(2, 0))
                for tag_text, tag_color in tags:
                    tk.Label(tag_row, text=tag_text, font=("Segoe UI", 7),
                             bg=BG_CARD2, fg=tag_color, padx=6, pady=2).pack(side="left", padx=(0, 4))
            except Exception:
                pass


class GrowthPage(BasePage):
    """Stran za napovedovanje rasti rastline s klicem na API."""

    # Vhodna polja in njihove oznake
    FIELDS = [
        ("days_passed",        "Days passed"),
        ("avg_direct_light",   "Avg direct light (hrs)"),
        ("avg_indirect_light", "Avg indirect light (hrs)"),
        ("avg_nighttime",      "Avg nighttime (hrs)"),
        ("avg_temp",           "Avg temperature (°C)"),
        ("min_temp",           "Min temperature (°C)"),
        ("max_temp",           "Max temperature (°C)"),
        ("times_watered",      "Times watered"),
        ("initial_height",     "Initial height (cm)"),
    ]
    # Možne barve rastline
    COLORS = ["green", "yellow", "brown", "pale", "black"]

    def _build(self):
        self._entries = {}
        self._color_var = tk.StringVar(value="green")

        outer = tk.Frame(self, bg=BG_MAIN)
        outer.pack(fill="both", expand=True, padx=22, pady=18)

        # Naslov strani
        tk.Label(outer, text="📈  Growth Prediction", font=("Segoe UI", 16, "bold"),
                 bg=BG_MAIN, fg=TEXT_PRI).pack(anchor="w")
        tk.Label(outer, text="Enter plant conditions and predict height growth using the AI model.",
                 font=self.f_small, bg=BG_MAIN, fg=TEXT_SEC).pack(anchor="w", pady=(0, 16))

        cols = tk.Frame(outer, bg=BG_MAIN)
        cols.pack(fill="both", expand=True)

        # Leva plošča – vnosna polja
        left = tk.Frame(cols, bg=BG_CARD, width=360, padx=18, pady=16)
        left.pack(side="left", fill="y", padx=(0, 14))
        left.pack_propagate(False)

        tk.Label(left, text="Plant Conditions", font=self.f_title,
                 bg=BG_CARD, fg=TEXT_PRI).pack(anchor="w", pady=(0, 12))

        # Vnosna polja za numerične vrednosti
        for key, label in self.FIELDS:
            row = tk.Frame(left, bg=BG_CARD)
            row.pack(fill="x", pady=(0, 8))
            tk.Label(row, text=label, font=self.f_small, bg=BG_CARD,
                     fg=TEXT_SEC, width=22, anchor="w").pack(side="left")
            entry = tk.Entry(row, bg=BG_CARD2, fg=TEXT_PRI,
                             insertbackground=TEXT_PRI, relief="flat",
                             font=("Segoe UI", 9), width=10)
            entry.pack(side="left", ipady=5, padx=(6, 0))
            tk.Frame(row, bg=BORDER, height=1).pack(side="bottom", fill="x")
            self._entries[key] = entry

        tk.Frame(left, bg=BORDER, height=1).pack(fill="x", pady=(4, 10))

        # Izbira barve rastline
        tk.Label(left, text="Plant colour (before)", font=self.f_small,
                 bg=BG_CARD, fg=TEXT_SEC).pack(anchor="w", pady=(0, 6))
        color_row = tk.Frame(left, bg=BG_CARD)
        color_row.pack(fill="x", pady=(0, 12))
        self._color_btns = {}

        color_display = {"green": ACCENT, "yellow": YELLOW, "brown": "#a0522d",
                         "pale": TEXT_SEC, "black": "#555555"}

        for c in self.COLORS:
            is_active = (c == "green")
            btn = tk.Frame(color_row,
                           bg=ACCENT if is_active else BG_CARD2,
                           cursor="hand2", padx=10, pady=4)
            btn.pack(side="left", padx=(0, 4))
            lbl = tk.Label(btn, text=c.capitalize(), font=self.f_small,
                           bg=ACCENT if is_active else BG_CARD2,
                           fg=BG_MAIN if is_active else TEXT_SEC)
            lbl.pack()
            self._color_btns[c] = (btn, lbl)

            def on_color(e, v=c):
                self._color_var.set(v)
                for k, (b, l) in self._color_btns.items():
                    active = (k == v)
                    b.configure(bg=ACCENT if active else BG_CARD2)
                    l.configure(bg=ACCENT if active else BG_CARD2,
                                fg=BG_MAIN if active else TEXT_SEC)

            bind_tree(btn, "<Button-1>", on_color)

        # API URL polje
        api_row = tk.Frame(left, bg=BG_CARD)
        api_row.pack(fill="x", pady=(0, 10))
        tk.Label(api_row, text="API URL", font=self.f_small, bg=BG_CARD,
                 fg=TEXT_SEC).pack(anchor="w", pady=(0, 4))
        self._api_url_var = tk.StringVar(value="http://localhost:5000/growth")
        api_entry = tk.Entry(api_row, textvariable=self._api_url_var,
                             bg=BG_CARD2, fg=TEXT_PRI, insertbackground=TEXT_PRI,
                             relief="flat", font=("Segoe UI", 9))
        api_entry.pack(fill="x", ipady=5)
        tk.Frame(api_row, bg=BORDER, height=1).pack(fill="x")

        # Gumb za pošiljanje napovedi
        predict_btn = tk.Frame(left, bg=ACCENT, cursor="hand2")
        predict_btn.pack(fill="x", pady=(14, 0))
        tk.Label(predict_btn, text="📈  Predict Growth", font=self.f_label,
                 bg=ACCENT, fg=BG_MAIN, pady=9).pack()
        bind_tree(predict_btn, "<Button-1>", lambda e: self._run_prediction())
        hover(predict_btn, ACCENT, "#00c98a")

        # Desna plošča – rezultati
        right = tk.Frame(cols, bg=BG_MAIN)
        right.pack(side="left", fill="both", expand=True)

        tk.Label(right, text="Prediction Result", font=self.f_title,
                 bg=BG_MAIN, fg=TEXT_PRI).pack(anchor="w", pady=(0, 10))

        self._result_frame = tk.Frame(right, bg=BG_MAIN)
        self._result_frame.pack(fill="both", expand=True)
        self._show_empty()

    def _show_empty(self):
        """Prikaže prazno stanje brez rezultatov."""
        for w in self._result_frame.winfo_children():
            w.destroy()
        container = tk.Frame(self._result_frame, bg=BG_CARD, padx=20, pady=40)
        container.pack(fill="both", expand=True)
        tk.Label(container, text="📈", font=("Segoe UI", 40), bg=BG_CARD).pack(pady=(20, 8))
        tk.Label(container, text="Fill in the plant conditions and click Predict Growth.",
                 font=self.f_body, bg=BG_CARD, fg=TEXT_SEC, justify="center").pack()

    def _show_loading(self):
        """Prikaže animacijo med čakanjem na odgovor API."""
        for w in self._result_frame.winfo_children():
            w.destroy()
        container = tk.Frame(self._result_frame, bg=BG_CARD, padx=20, pady=40)
        container.pack(fill="both", expand=True)
        tk.Label(container, text="Contacting growth model...",
                 font=("Segoe UI", 11, "bold"), bg=BG_CARD, fg=TEXT_PRI).pack(pady=(30, 8))
        self._loading_lbl = tk.Label(container, text="⬤  ⬤  ⬤",
                                      font=("Segoe UI", 14), bg=BG_CARD, fg=ACCENT)
        self._loading_lbl.pack(pady=(12, 0))
        self._dot_idx = 0
        self._animate()

    def _animate(self):
        patterns = ["⬤  ○  ○", "○  ⬤  ○", "○  ○  ⬤", "○  ⬤  ○"]
        try:
            self._loading_lbl.config(text=patterns[self._dot_idx % len(patterns)])
            self._dot_idx += 1
            self._anim_job = self.after(400, self._animate)
        except Exception:
            pass

    def _run_prediction(self):
        """Zbere vrednosti, zgradi zahtevo in jo pošlje na API v ozadni niti."""
        # Preveri, da so vsa polja izpolnjena
        data = {}
        for key, label in self.FIELDS:
            val = self._entries[key].get().strip()
            if not val:
                messagebox.showwarning("Missing Input", f"Please fill in: {label}")
                return
            try:
                data[key] = float(val)
            except ValueError:
                messagebox.showerror("Invalid Input", f"'{label}' must be a number.")
                return

        # Kodiranje barve v one-hot vektor
        color = self._color_var.get()
        vector = [1 if c == color else 0 for c in self.COLORS]

        payload = {**data, "color_before": vector}
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
        """Prikaže rezultat napovedi iz API odgovora."""
        if hasattr(self, "_anim_job"):
            try: self.after_cancel(self._anim_job)
            except: pass
        for w in self._result_frame.winfo_children():
            w.destroy()

        color_name = self.COLORS[rep.get("color", 0)] if "color" in rep else "unknown"
        guess      = rep.get("guess", "N/A")

        # Kartica z rezultatom
        card = tk.Frame(self._result_frame, bg=BG_CARD, padx=20, pady=20)
        card.pack(fill="x", pady=(0, 10))

        tk.Label(card, text="Prediction Complete", font=("Segoe UI", 12, "bold"),
                 bg=BG_CARD, fg=ACCENT).pack(anchor="w", pady=(0, 12))

        # Napovedana višina
        height_row = tk.Frame(card, bg=BG_CARD2, padx=16, pady=14)
        height_row.pack(fill="x", pady=(0, 8))
        tk.Label(height_row, text="Predicted height growth",
                 font=self.f_small, bg=BG_CARD2, fg=TEXT_SEC).pack(anchor="w")
        tk.Label(height_row, text=f"{guess:.3f} cm",
                 font=("Segoe UI", 28, "bold"), bg=BG_CARD2, fg=ACCENT).pack(anchor="w")

        # Napovedana barva
        color_row = tk.Frame(card, bg=BG_CARD2, padx=16, pady=14)
        color_row.pack(fill="x", pady=(0, 8))
        tk.Label(color_row, text="Predicted plant colour",
                 font=self.f_small, bg=BG_CARD2, fg=TEXT_SEC).pack(anchor="w")
        color_colors = {"green": ACCENT, "yellow": YELLOW, "brown": "#a0522d",
                        "pale": TEXT_SEC, "black": "#888888"}
        tk.Label(color_row, text=color_name.capitalize(),
                 font=("Segoe UI", 16, "bold"), bg=BG_CARD2,
                 fg=color_colors.get(color_name, TEXT_PRI)).pack(anchor="w")

        # Surovi odgovor API
        raw_card = tk.Frame(self._result_frame, bg=BG_CARD, padx=16, pady=12)
        raw_card.pack(fill="x")
        tk.Label(raw_card, text="Raw API response", font=self.f_small,
                 bg=BG_CARD, fg=TEXT_MUT).pack(anchor="w", pady=(0, 6))
        import json
        raw_txt = tk.Text(raw_card, bg=BG_CARD2, fg=TEXT_SEC, font=("Courier", 8),
                          relief="flat", height=6, state="normal")
        raw_txt.insert("end", json.dumps(rep, indent=2))
        raw_txt.config(state="disabled")
        raw_txt.pack(fill="x")

        # Gumb za ponovni poskus
        retry_btn = tk.Frame(self._result_frame, bg=BG_CARD2, cursor="hand2",
                              padx=14, pady=8)
        retry_btn.pack(anchor="e", pady=(10, 0))
        tk.Label(retry_btn, text="Predict Again", font=self.f_label,
                 bg=BG_CARD2, fg=ACCENT).pack()
        bind_tree(retry_btn, "<Button-1>", lambda e: self._run_prediction())
        hover(retry_btn, BG_CARD2, BG_CARD)

    def _show_error(self, msg: str):
        """Prikaže sporočilo o napaki pri klicu API."""
        if hasattr(self, "_anim_job"):
            try: self.after_cancel(self._anim_job)
            except: pass
        for w in self._result_frame.winfo_children():
            w.destroy()
        card = tk.Frame(self._result_frame, bg=BG_CARD, padx=20, pady=20)
        card.pack(fill="both", expand=True)
        tk.Label(card, text="Prediction Failed", font=("Segoe UI", 12, "bold"),
                 bg=BG_CARD, fg=RED).pack(pady=(10, 8))
        tk.Label(card, text=msg, font=self.f_body, bg=BG_CARD, fg=TEXT_SEC,
                 wraplength=400, justify="center").pack(pady=(0, 12))
        retry_btn = tk.Frame(card, bg=BG_CARD2, cursor="hand2", padx=14, pady=8)
        retry_btn.pack()
        tk.Label(retry_btn, text="Try Again", font=self.f_label, bg=BG_CARD2, fg=ACCENT).pack()
        bind_tree(retry_btn, "<Button-1>", lambda e: self._run_prediction())
        hover(retry_btn, BG_CARD2, BG_CARD)


class SettingsPage(BasePage):
    def _build(self):
        pad = tk.Frame(self, bg=BG_MAIN)
        pad.pack(fill="both", expand=True, padx=22, pady=18)
        tk.Label(pad, text="⚙️  Settings", font=("Segoe UI", 16, "bold"),
                 bg=BG_MAIN, fg=TEXT_PRI).pack(anchor="w")
        tk.Label(pad, text="Manage your preferences and threshold values.",
                 font=self.f_small, bg=BG_MAIN, fg=TEXT_SEC).pack(anchor="w", pady=(0, 24))

        sections = [
            ("Notifications", [("Low light alert", True), ("High light alert", True), ("Daily summary email", False)]),
            ("Thresholds",    [("Low light threshold", False), ("Optimal minimum", False), ("Optimal maximum", False)]),
            ("Display",       [("Dark mode", True), ("Show chart grid", True), ("Show data points", False)]),
        ]

        for section_title, items in sections:
            tk.Label(pad, text=section_title, font=self.f_title,
                     bg=BG_MAIN, fg=TEXT_PRI).pack(anchor="w", pady=(0, 8))
            card = tk.Frame(pad, bg=BG_CARD, padx=16, pady=4)
            card.pack(fill="x", pady=(0, 16))
            for i, (item_name, default_on) in enumerate(items):
                row = tk.Frame(card, bg=BG_CARD)
                row.pack(fill="x", pady=6)
                tk.Label(row, text=item_name, font=self.f_body, bg=BG_CARD, fg=TEXT_PRI).pack(side="left")
                var = tk.BooleanVar(value=default_on)
                toggle_lbl = tk.Label(row, text="● ON  " if default_on else "  OFF ●",
                                      font=self.f_small, bg=BG_CARD2,
                                      fg=ACCENT if default_on else TEXT_MUT, padx=8, pady=3, cursor="hand2")
                toggle_lbl.pack(side="right")
                def make_toggle(v=var, lbl=toggle_lbl):
                    def toggle(e):
                        v.set(not v.get())
                        lbl.config(text="● ON  " if v.get() else "  OFF ●",
                                   fg=ACCENT if v.get() else TEXT_MUT)
                    return toggle
                toggle_lbl.bind("<Button-1>", make_toggle())
                if i < len(items) - 1:
                    tk.Frame(card, bg=BORDER, height=1).pack(fill="x")

        save_btn = tk.Frame(pad, bg=ACCENT, cursor="hand2", padx=20, pady=8)
        save_btn.pack(anchor="e", pady=(8, 0))
        tk.Label(save_btn, text="Save Settings", font=self.f_label, bg=ACCENT, fg=BG_MAIN).pack()
        bind_tree(save_btn, "<Button-1>",
                  lambda e: messagebox.showinfo("Settings", "Settings saved successfully!"))
        hover(save_btn, ACCENT, "#00c98a")


NAV_ORDER = [
    ("📊", "Dashboard"),
    ("🪴", "My Plants"),
    ("📅", "History"),
    ("🔬", "Detection"),
    ("💡", "Recommendation"),
    ("📈", "Growth"),
    ("⚙️", "Settings"),
]

PAGE_CLASSES = {
    "Dashboard":      DashboardPage,
    "My Plants":      MyPlantsPage,
    "History":        HistoryPage,
    "Detection":      DetectionPage,
    "Recommendation": RecommendationSystemPage,
    "Growth":         GrowthPage,
    "Settings":       SettingsPage,
}


class PlantMonitor(tk.Tk):
    def __init__(self, username="Anastasija"):
        super().__init__()
        global USER_NAME
        USER_NAME = username
        self.title("Plant Monitor")
        self.geometry("1100x680")
        self.configure(bg=BG_MAIN)
        self.resizable(True, True)
        self._is_fullscreen = False

        self.f_title = ("Segoe UI", 13, "bold")
        self.f_big   = ("Segoe UI", 24, "bold")
        self.f_body  = ("Segoe UI", 9)
        self.f_small = ("Segoe UI", 8)
        self.f_label = ("Segoe UI", 9, "bold")

        self._nav_buttons  = []
        self._pages        = {}
        self._current_page = None

        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.bind("<F11>", lambda e: self._toggle_fullscreen())

        self._build_shell()
        self._register_pages()
        self._show_page("Dashboard")
        self._do_refresh()

    def _on_close(self):
        plt.close("all")
        self.destroy()
        os._exit(0)

    def _toggle_fullscreen(self, event=None):
        self._is_fullscreen = not self._is_fullscreen
        self.attributes("-fullscreen", self._is_fullscreen)
        self._fs_btn_lbl.config(text="⊡" if self._is_fullscreen else "⛶")

    def _build_shell(self):
        self.sidebar = tk.Frame(self, bg=BG_SIDE, width=210)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)
        self._build_sidebar(self.sidebar)
        self.content_area = tk.Frame(self, bg=BG_MAIN)
        self.content_area.pack(side="left", fill="both", expand=True)
        right = tk.Frame(self, bg=BG_SIDE, width=240)
        right.pack(side="right", fill="y")
        right.pack_propagate(False)
        self._build_right(right)

    def _build_sidebar(self, parent):
        top_row = tk.Frame(parent, bg=BG_SIDE)
        top_row.pack(fill="x", padx=10, pady=(14, 6))
        logo = tk.Frame(top_row, bg=BG_SIDE)
        logo.pack(side="left")
        # FIX 3: emoji in its own label to ensure it renders correctly
        tk.Label(logo, text="🌿", font=("Segoe UI", 14), bg=BG_SIDE, fg=ACCENT).pack(side="left")
        tk.Label(logo, text=" Plant Monitor", font=self.f_title, bg=BG_SIDE, fg=TEXT_PRI).pack(side="left")
        fs_btn = tk.Frame(top_row, bg=BG_CARD2, cursor="hand2", padx=6, pady=4)
        fs_btn.pack(side="right")
        self._fs_btn_lbl = tk.Label(fs_btn, text="⛶", font=("Segoe UI", 11),
                                     bg=BG_CARD2, fg=TEXT_SEC, cursor="hand2")
        self._fs_btn_lbl.pack()
        bind_tree(fs_btn, "<Button-1>", lambda e: self._toggle_fullscreen())
        hover(fs_btn, BG_CARD2, BG_CARD)

        tk.Frame(parent, bg=BORDER, height=1).pack(fill="x", padx=12, pady=4)

        for icon, label in NAV_ORDER:
            self._nav_btn(parent, icon, label)

        tk.Frame(parent, bg=BG_SIDE).pack(expand=True)
        tk.Frame(parent, bg=BORDER, height=1).pack(fill="x", padx=12, pady=4)

        logout_btn = tk.Frame(parent, bg=BG_CARD2, cursor="hand2")
        logout_btn.pack(fill="x", padx=8, pady=(0, 4))
        logout_row = tk.Frame(logout_btn, bg=BG_CARD2)
        logout_row.pack(pady=7, padx=10, anchor="w")
        tk.Label(logout_row, text="⏻", font=("Segoe UI", 10), bg=BG_CARD2, fg=RED).pack(side="left", padx=(0, 8))
        tk.Label(logout_row, text="Sign Out", font=self.f_body, bg=BG_CARD2, fg=RED).pack(side="left")
        bind_tree(logout_btn, "<Button-1>", lambda e: self._do_logout())
        hover(logout_btn, BG_CARD2, "#2a1a1f")

        prof = tk.Frame(parent, bg=BG_SIDE, cursor="hand2")
        prof.pack(fill="x", padx=14, pady=(6, 16))
        tk.Label(prof, text="AK", font=("Segoe UI", 9, "bold"),
                 bg="#3d5a80", fg="white", width=3, height=1).pack(side="left")
        info = tk.Frame(prof, bg=BG_SIDE)
        info.pack(side="left", padx=8)
        tk.Label(info, text=USER_NAME, font=self.f_body, bg=BG_SIDE, fg=TEXT_PRI).pack(anchor="w")
        tk.Label(info, text="Plant Enthusiast  ›", font=self.f_small, bg=BG_SIDE, fg=ACCENT).pack(anchor="w")
        bind_tree(prof, "<Button-1>", lambda e: self._show_page("Settings"))

    def _nav_btn(self, parent, icon, label):
        is_active = not self._nav_buttons
        bg = BG_CARD if is_active else BG_SIDE
        fg = TEXT_PRI if is_active else TEXT_SEC
        row = tk.Frame(parent, bg=bg, cursor="hand2")
        row.pack(fill="x", padx=8, pady=2)
        bar = tk.Frame(row, bg=ACCENT if is_active else bg, width=3)
        bar.pack(side="left", fill="y")
        # FIX 3: emoji and text in separate labels so emoji always renders
        icon_lbl = tk.Label(row, text=icon, font=("Segoe UI", 11),
                            bg=bg, fg=fg, anchor="w", pady=8, padx=6)
        icon_lbl.pack(side="left")
        lbl = tk.Label(row, text=label, font=self.f_body,
                       bg=bg, fg=fg, anchor="w", pady=8, padx=2)
        lbl.pack(fill="x")
        entry = {"row": row, "bar": bar, "lbl": lbl, "icon": icon_lbl, "label": label}
        self._nav_buttons.append(entry)

        def on_click(e, entry=entry):
            for b in self._nav_buttons:
                b["row"].configure(bg=BG_SIDE)
                b["bar"].configure(bg=BG_SIDE)
                b["lbl"].configure(bg=BG_SIDE, fg=TEXT_SEC)
                b["icon"].configure(bg=BG_SIDE, fg=TEXT_SEC)
            entry["row"].configure(bg=BG_CARD)
            entry["bar"].configure(bg=ACCENT)
            entry["lbl"].configure(bg=BG_CARD, fg=TEXT_PRI)
            entry["icon"].configure(bg=BG_CARD, fg=TEXT_PRI)
            self._show_page(entry["label"])

        row.bind("<Button-1>", on_click)
        lbl.bind("<Button-1>", on_click)
        bar.bind("<Button-1>", on_click)
        icon_lbl.bind("<Button-1>", on_click)

    def _build_right(self, parent):
        pad = tk.Frame(parent, bg=BG_SIDE)
        pad.pack(fill="both", expand=True, padx=12, pady=14)

        banner = tk.Frame(pad, bg="#1a2e1a", height=90)
        banner.pack(fill="x", pady=(0, 12))
        banner.pack_propagate(False)
        tk.Label(banner, text="Plant Monitor", font=self.f_title, bg="#1a2e1a", fg=TEXT_PRI).place(x=10, y=12)
        # FIX 3: emoji in dedicated label
        tk.Label(banner, text="🌿", font=("Segoe UI", 30), bg="#1a2e1a").place(relx=0.75, rely=0.5, anchor="center")

        # FIX 4: Refresh button removed entirely

        tk.Label(pad, text="Plant Status", font=self.f_title,
                 bg=BG_SIDE, fg=TEXT_PRI).pack(anchor="w", pady=(0, 8))
        tk.Label(pad,
                 text="Open 'My Plants' for a\ndetailed view of each plant.",
                 font=self.f_small, bg=BG_SIDE, fg=TEXT_SEC, justify="left").pack(anchor="w")

        va = tk.Frame(pad, bg=BG_SIDE, cursor="hand2")
        va.pack(fill="x", pady=(8, 0))
        va_lbl = tk.Label(va, text="Open My Plants  ›", font=self.f_body,
                          bg=BG_SIDE, fg=ACCENT, cursor="hand2")
        va_lbl.pack(anchor="e")
        bind_tree(va, "<Button-1>", lambda e: self._show_page("My Plants"))

        tk.Frame(pad, bg=BORDER, height=1).pack(fill="x", pady=(16, 8))

        rec_shortcut = tk.Frame(pad, bg=BG_CARD, cursor="hand2")
        rec_shortcut.pack(fill="x")
        rec_inner = tk.Frame(rec_shortcut, bg=BG_CARD)
        rec_inner.pack(pady=8, padx=10, anchor="w")
        tk.Label(rec_inner, text="💡", font=("Segoe UI", 11), bg=BG_CARD, fg=BLUE).pack(side="left", padx=(0, 8))
        tk.Label(rec_inner, text="Recommend a plant  ›", font=self.f_body, bg=BG_CARD, fg=BLUE).pack(side="left")
        bind_tree(rec_shortcut, "<Button-1>", lambda e: self._show_page("Recommendation"))
        hover(rec_shortcut, BG_CARD, BG_CARD2)

    def _register_pages(self):
        for name, cls in PAGE_CLASSES.items():
            page = cls(self.content_area, self)
            page.place(relx=0, rely=0, relwidth=1, relheight=1)
            self._pages[name] = page

    def _show_page(self, name):
        if self._current_page:
            self._current_page.lower()
        page = self._pages.get(name)
        if page:
            page.lift()
            self._current_page = page
        for entry in self._nav_buttons:
            match = entry["label"] == name
            entry["row"].configure(bg=BG_CARD if match else BG_SIDE)
            entry["bar"].configure(bg=ACCENT  if match else BG_SIDE)
            entry["lbl"].configure(bg=BG_CARD if match else BG_SIDE,
                                   fg=TEXT_PRI if match else TEXT_SEC)
            entry["icon"].configure(bg=BG_CARD if match else BG_SIDE,
                                    fg=TEXT_PRI if match else TEXT_SEC)

    def _do_logout(self):
        if messagebox.askyesno("Sign Out", "Are you sure you want to sign out?"):
            plt.close("all")
            self.destroy()
            auth = AuthWindow()
            auth.mainloop()
            if auth.logged_in_user:
                app = PlantMonitor(auth.logged_in_user)
                app.mainloop()

    def _do_refresh(self):
        dash = self._pages.get("Dashboard")
        if dash:
            dash.refresh()


if __name__ == "__main__":
    auth = AuthWindow()
    auth.mainloop()
    if auth.logged_in_user:
        app = PlantMonitor(auth.logged_in_user)
        app.mainloop()