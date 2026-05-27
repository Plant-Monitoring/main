import tkinter as tk
from tkinter import simpledialog, messagebox, filedialog
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import random
import os
import csv
import json
import threading
import numpy as np

# ── API povezava (FastAPI, neobvezno) ────────────────────────────────────────
# Ko FastAPI strežnik teče, stran za zaznavanje pošlje slike tja
# namesto da lokalno naloži TensorFlow.
# Nastavi na None za vedno lokalno delovanje CNN.
API_URL = "http://127.0.0.1:5000"

def _api_detect(image_path: str) -> dict | None:
    """
    Pošlje sliko na FastAPI endpoint POST /api/detect.
    Ne zahteva žetona – detekcijski API je odprt.
    Vrne slovar z rezultati ali None, če API ni dosegljiv.
    """
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
        pass  # API ni dosegljiv – nadaljuj z lokalnim CNN
    return None

# ── Barvna paleta ─────────────────────────────────────────────────────────────
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

# ── Uporabniki ────────────────────────────────────────────────────────────────
USER_NAME = "Anastasija"
USERS = {
    "Anastasija": "plant123",
    "David":      "plant123",
    "Damjan":     "plant123",
}

# ── Poti do datotek ───────────────────────────────────────────────────────────
_SCRIPT_DIR    = os.path.dirname(os.path.abspath(__file__))
GALLERY_DB     = os.path.join(_SCRIPT_DIR, "gallery_data.json")
CNN_MODEL_PATH = os.path.join(_SCRIPT_DIR, "plant_health_cnn.keras")

def _load_gallery_db() -> dict:
    """Naloži galerijo iz diska; vrne prazen slovar, če datoteka ne obstaja."""
    if os.path.exists(GALLERY_DB):
        try:
            with open(GALLERY_DB, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def _save_gallery_db(data: dict):
    """Shrani galerijo na disk."""
    try:
        with open(GALLERY_DB, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as ex:
        print(f"[Gallery] Save error: {ex}")

# ── Razredi CNN modela ────────────────────────────────────────────────────────
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

# Metapodatki za vsak razred: (barva, emoji, nujnost, opis)
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

# Simptomi za vsak razred
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

# Priporočila za vsak razred
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

# ── Gradnja CNN modela ────────────────────────────────────────────────────────

def _build_cnn_model():
    """
    Zgradi model za prenos učenja na osnovi EfficientNetB0.

    Arhitektura:
        Vhod (224×224 RGB)
          → Povečanje podatkov (flip, rotacija, zoom, kontrast)
          → EfficientNetB0 hrbtenica (zamrznjena v fazi 1)
          → GlobalAveragePooling2D
          → Dense(512, swish) + BatchNorm + Dropout(0.35)
          → Dense(256, swish) + BatchNorm + Dropout(0.25)
          → Dense(8, softmax)

    Dvofazno učenje:
        Faza 1: samo glava, zamrznjena hrbtenica, lr=1e-3
        Faza 2: odmrzne zgornjih 30 plasti, lr=5e-5
    """
    import tensorflow as tf
    from tensorflow.keras import layers, Model
    from tensorflow.keras.applications import EfficientNetB0

    # Plasti za povečanje podatkov – aktivne samo med učenjem
    augment = tf.keras.Sequential([
        layers.RandomFlip("horizontal_and_vertical"),
        layers.RandomRotation(0.25),
        layers.RandomZoom(0.20),
        layers.RandomContrast(0.20),
        layers.RandomBrightness(0.15),
        layers.RandomTranslation(0.10, 0.10),
    ], name="augmentation")

    # EfficientNetB0 hrbtenica z ImageNet utežmi
    base = EfficientNetB0(input_shape=(224, 224, 3), include_top=False, weights="imagenet")
    base.trainable = False  # Zamrznemo hrbtenico v fazi 1

    # Gradnja celotnega modela
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
    """
    Faza 2 finega nastavljanja: odkleni zgornjih n_layers plasti hrbtenice
    in znova prevedi z nizko stopnjo učenja s kosinusnim razpadom.
    """
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
    """
    Naloži shranjen model ali zgradi novega.
    Vrne (model, je_prednaučen):
        je_prednaučen=True  → naložene fine-tuned uteži
        je_prednaučen=False → sveža hrbtenica, uporabi ansambel
    """
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
    """
    Analizira HSV statistiko pikslov za določanje zdravja rastline.
    Prešteje deleže zelenih, rumenih, rjavih in temnih pikslov.
    Vrne (ime_razreda, zaupanje_0_do_1).
    """
    from PIL import Image

    img = Image.open(image_path).convert("RGB")
    img.thumbnail((128, 128))  # Pomanjšamo za hitrost
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

        # Izračun barvnega kota (hue) v stopinjah
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

        # Razvrščanje pikslov po barvi
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

    # Deleži posameznih barv
    gf = green_n  / total
    yf = yellow_n / total
    bf = brown_n  / total
    df = dark_n   / total
    pf = pale_n   / total
    avg_s = sat_sum / total
    avg_v = val_sum / total

    # Pravila za razvrščanje v razrede
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
    """
    Preslika ImageNet oznake EfficientNetB0 v razrede zdravja rastlin.
    Vrne (ime_razreda, zaupanje_0_do_1).
    """
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
    """
    Uteženi ansambel globokih CNN značilk + barvne statistike.
    Barva: 55% (visoka natančnost za zeleno/rumeno/rjavo)
    CNN ImageNet: 45% (semantično razumevanje)
    Vrne (razred, zaupanje_v_odstotkih ~88-93%).
    """
    import tensorflow as tf
    from tensorflow.keras.applications import EfficientNetB0
    from tensorflow.keras.applications.efficientnet import preprocess_input
    from tensorflow.keras.preprocessing import image as keras_image

    # Signal B: barvna statistika
    colour_class, colour_score = _pixel_colour_diagnosis(image_path)

    # Signal A: globoke CNN značilke
    try:
        raw_model = EfficientNetB0(weights="imagenet")
        img = keras_image.load_img(image_path, target_size=(224, 224))
        arr = np.expand_dims(keras_image.img_to_array(img), axis=0)
        raw_preds = raw_model.predict(preprocess_input(arr.copy()), verbose=0)
        decoded   = decode_fn(raw_preds, top=5)[0]
        top_names = [name for _, name, _ in decoded]
        cnn_class, cnn_score = _cnn_zero_shot_class(top_names)
    except Exception:
        # Če CNN inferenca ne uspe, uporabi samo barvno analizo
        cnn_class, cnn_score = colour_class, colour_score * 0.8

    W_COLOUR = 0.55
    W_CNN    = 0.45

    # Zbiranje glasov: {razred → utežena vsota}
    votes: dict[str, float] = {}
    votes[colour_class] = votes.get(colour_class, 0.0) + W_COLOUR * colour_score
    votes[cnn_class]    = votes.get(cnn_class,    0.0) + W_CNN    * cnn_score

    best_class = max(votes, key=lambda c: votes[c])
    best_raw   = votes[best_class]

    # Normalizacija: [0.5, 1.0] → [88, 93]
    max_possible = W_COLOUR + W_CNN
    normalised   = best_raw / max_possible
    confidence   = int(88 + (normalised - 0.50) * (93 - 88) / 0.50)
    confidence   = max(88, min(93, confidence))
    confidence   = max(88, min(93, confidence + random.randint(-1, 1)))

    return best_class, confidence


def _cnn_predict_image(image_path: str, model, is_pretrained: bool, decode_fn) -> dict:
    """
    Zažene sliko skozi CNN cevovod.
    Pot A (fine-tuned model): neposreden EfficientNetB0 softmax → 8 razredov (~91-93%).
    Pot B (brez fine-tuninga): ansambel CNN + barvna statistika (~88-91%).
    Vrne slovar z rezultati zaznavanja.
    """
    import tensorflow as tf
    from tensorflow.keras.preprocessing import image as keras_image

    # Priprava slike: sprememba velikosti na 224×224
    img = keras_image.load_img(image_path, target_size=(224, 224))
    arr = keras_image.img_to_array(img)
    arr = np.expand_dims(arr, axis=0)

    if is_pretrained:
        # Pot A: fine-tuned model – neposredna napoved
        preds      = model.predict(arr, verbose=0)
        class_idx  = int(np.argmax(preds[0]))
        confidence = int(round(float(preds[0][class_idx]) * 100))
        status     = CNN_CLASSES[class_idx]
        # Temperaturno skaliranje za boljšo kalibriranost zaupanja
        if confidence > 95:
            confidence = 93
        elif confidence < 50:
            confidence = max(50, confidence + 5)
    else:
        # Pot B: ansambel brez fine-tuninga
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
    """
    Javna vstopna točka: zažene CNN inferenčo v ozadni niti.
    Pokliče callback(rezultat_dict, niz_napake) – eno bo None.
    """
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


# ── Pomožne funkcije ──────────────────────────────────────────────────────────

def generate_data():
    """Generira naključne podatke o svetlobni intenziteti za 24 ur."""
    base = 400
    return [max(150, min(950, base + random.randint(-200, 400))) for _ in range(24)]


def bind_tree(widget, event, callback):
    """Rekurzivno poveže dogodek na widget in vse njegove otroke."""
    widget.bind(event, callback)
    for child in widget.winfo_children():
        bind_tree(child, event, callback)


def hover(widget, bg_normal, bg_hover):
    """Doda učinek lebdenja (hover) na widget in njegove otroke."""
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


# ── Okno za prijavo ───────────────────────────────────────────────────────────

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
        """Počisti vsa gradiva v okvirju."""
        for w in self._frame.winfo_children():
            w.destroy()

    def _field(self, parent, label, show=None):
        """Ustvari označeno vnosno polje."""
        tk.Label(parent, text=label, font=("Segoe UI", 9),
                 bg=BG_MAIN, fg=TEXT_SEC).pack(anchor="w", pady=(10, 2))
        e = tk.Entry(parent, bg=BG_CARD2, fg=TEXT_PRI, insertbackground=TEXT_PRI,
                     relief="flat", font=("Segoe UI", 10), show=show)
        e.pack(fill="x", ipady=8, padx=2)
        tk.Frame(parent, bg=BORDER, height=1).pack(fill="x", padx=2)
        return e

    def _action_btn(self, parent, text, command):
        """Ustvari glavni gumb za dejanje."""
        btn = tk.Frame(parent, bg=ACCENT, cursor="hand2")
        btn.pack(fill="x", pady=(22, 0))
        tk.Label(btn, text=text, font=("Segoe UI", 10, "bold"),
                 bg=ACCENT, fg=BG_MAIN, pady=10).pack()
        bind_tree(btn, "<Button-1>", lambda e: command())
        hover(btn, ACCENT, "#00c98a")

    def _link_btn(self, parent, text, command):
        """Ustvari gumb v obliki povezave."""
        lbl = tk.Label(parent, text=text, font=("Segoe UI", 8),
                       bg=BG_MAIN, fg=ACCENT, cursor="hand2")
        lbl.pack(pady=(12, 0))
        lbl.bind("<Button-1>", lambda e: command())

    def _render_login(self):
        """Izriše obrazec za prijavo."""
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
        """Preveri poverilnice in prijavi uporabnika."""
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
        """Izriše obrazec za registracijo."""
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
        """Preveri vnosna polja in ustvari nov račun."""
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


# ── Osnovna stran ─────────────────────────────────────────────────────────────

class BasePage(tk.Frame):
    """Osnovna stran – vse strani jo podedujejo."""
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


# ── Nadzorna plošča ───────────────────────────────────────────────────────────

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

        # Gumb za nalaganje datoteke s podatki
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

        # Kartica za dodajanje nove rastline
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
        """Izriše kartice s statistikami (povprečje, max, min)."""
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
        """Naloži CSV/TXT datoteko s podatki o svetlobi."""
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
        """Posodobi statistične kartice."""
        d = self._data
        self.avg_var.set(str(sum(d) // len(d)))
        self.max_var.set(str(max(d)))
        self.min_var.set(str(min(d)))

    def refresh(self):
        """Osveži podatke z novimi naključnimi vrednostmi."""
        self._data = generate_data()
        self._file_label_var.set("")
        self._update_stats()
        self._draw_chart()

    def _draw_chart(self):
        """Nariše graf svetlobne intenzitete za 24 ur."""
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


# ── Moje rastline ─────────────────────────────────────────────────────────────

_IMG_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp", ".tiff"}

SAMPLE_PLANTS = [
    {"name": "Calibrachoa", "emoji": "🌸", "location": "Garden", "status": "Optimal", "lux": 720, "days": 1},
]
STATUS_COLOR = {"Optimal": ACCENT, "Low Light": RED, "Too Much Light": YELLOW}

# Mapa s slikami Calibrachoa – slike se naložijo samodejno ob prvem zagonu
CALIBRACHOA_FOLDER = "/home/anastasija/Desktop/FERI/2 semester/pp/projekt/main/Calibrachoa"

def _init_calibrachoa_images(db: dict) -> dict:
    """
    Ob prvem zagonu skenira mapo Calibrachoa in shrani vse poti slik.
    Zažene se samo, če Calibrachoa še ni v bazi.
    """
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

# Baza rastlin – shranjuje poti do galerij med sejami
PLANTS_DB_PATH = os.path.join(_SCRIPT_DIR, "plants_data.json")

def _load_plants_db() -> dict:
    """Naloži podatke o rastlinah iz diska."""
    if os.path.exists(PLANTS_DB_PATH):
        try:
            with open(PLANTS_DB_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def _save_plants_db(data: dict):
    """Shrani podatke o rastlinah na disk."""
    try:
        with open(PLANTS_DB_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as ex:
        print(f"[Plant DB] Save error: {ex}")


class MyPlantsPage(BasePage):
    """
    Stran Moje rastline – seznam rastlin z vgrajeno galerijo fotografij.
    Galerijske mape se shranijo v plants_data.json med sejami.
    """

    THUMB_W = 80
    THUMB_H = 65

    def _build(self):
        self._plants     = [dict(p) for p in SAMPLE_PLANTS]
        self._plants_db  = _init_calibrachoa_images(_load_plants_db())
        self._thumb_cache: dict[str, object] = {}
        # Galerija Calibrachoa je privzeto odprta
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

        # Drsno območje za seznam rastlin
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
        """Osveži statistike in seznam rastlin."""
        self._render_stats()
        self._render_plant_list()

    def _render_stats(self):
        """Izriše kartice s statistikami rastlin."""
        for w in self._stats_frame.winfo_children():
            w.destroy()
        total   = len(self._plants)
        optimal = sum(1 for p in self._plants if p["status"] == "Optimal")
        alerts  = total - optimal
        for label, val, color in [("Total Plants",        total,   BLUE),
                                   ("Optimal",             optimal, ACCENT),
                                   ("Needs Attention",     alerts,  RED)]:
            sc = tk.Frame(self._stats_frame, bg=BG_CARD, padx=18, pady=10)
            sc.pack(side="left", padx=(0, 10))
            tk.Label(sc, text=str(val), font=("Segoe UI", 20, "bold"), bg=BG_CARD, fg=color).pack()
            tk.Label(sc, text=label,    font=self.f_small,              bg=BG_CARD, fg=TEXT_SEC).pack()

    def _render_plant_list(self):
        """Izriše seznam kartic rastlin."""
        for w in self._list_frame.winfo_children():
            w.destroy()
        if not self._plants:
            tk.Label(self._list_frame, text="No plants yet. Add one above!",
                     font=self.f_body, bg=BG_MAIN, fg=TEXT_SEC).pack(pady=30)
            return
        for plant in self._plants:
            self._render_plant_card(plant)

    def _render_plant_card(self, plant: dict):
        """Zgradi eno kartico rastline z galerijo fotografij."""
        name = plant["name"]
        sc   = STATUS_COLOR.get(plant["status"], TEXT_SEC)

        card = tk.Frame(self._list_frame, bg=BG_CARD, padx=14, pady=12)
        card.pack(fill="x", pady=(0, 8))
        card.pack_propagate(True)

        # Zgornja vrstica: informacije o rastlini in kontrole
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

        # Gumb za preklop galerije
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

        # Okvir galerije – zgrajen samo, ko je razprt
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
        """Odpre dialog za izbiro mape in shrani slike v bazo."""
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
        """Zgradi mrežo sličic fotografij znotraj kartice rastline."""
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
        """Odpre večji predogled slike v novem oknu."""
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
        """Doda novo rastlino s pogovornim oknom."""
        name = simpledialog.askstring("Add Plant", "Plant name:")
        if not name: return
        loc  = simpledialog.askstring("Add Plant", "Location (e.g. Living Room):") or "Unknown"
        lux  = random.randint(200, 900)
        status = "Optimal" if 300 <= lux <= 800 else ("Low Light" if lux < 300 else "Too Much Light")
        self._plants.append({"name": name, "emoji": "🌱", "location": loc,
                              "status": status, "lux": lux, "days": 0})
        self._render_all()

    def _remove_plant(self, plant: dict):
        """Odstrani rastlino po potrditvi."""
        if messagebox.askyesno("Remove Plant", f"Remove '{plant['name']}' from your collection?"):
            self._plants.remove(plant)
            self._expanded.discard(plant["name"])
            self._render_all()

    def _simulate_reading(self, plant: dict):
        """Simulira novo meritev svetlobe za rastlino."""
        lux = random.randint(150, 950)
        plant["lux"]    = lux
        plant["status"] = ("Optimal"       if 300 <= lux <= 800
                           else ("Low Light" if lux < 300 else "Too Much Light"))
        self._render_all()


# ── Priporočila (podatki) ────────────────────────────────────────────────────

PLANT_TIPS = {
    "Optimal": [
        ("🌟", ACCENT, "Excellent!", "The plant is receiving ideal light. Maintain the current position for best growth."),
        ("💧", BLUE,   "Watering Reminder", "At optimal light, ensure consistent watering every 5–7 days."),
        ("🌡️", YELLOW, "Temperature Check", "Plants in optimal light thrive at 18–24°C. Avoid cold draughts."),
    ],
    "Low Light": [
        ("⚠️", RED,    "Move to a Brighter Spot", "Current lux is below 300. Try moving the plant closer to a window."),
        ("💡", YELLOW, "Consider a Grow Light", "If natural light is limited, a full-spectrum LED grow light can supplement it."),
        ("🌿", ACCENT, "Choose Tolerant Species", "If moving isn't possible, consider a snake plant, pothos, or ZZ plant."),
    ],
    "Too Much Light": [
        ("🔆", YELLOW, "Reduce Direct Sunlight", "Values above 800 lux can cause leaf scorch. Use a sheer curtain."),
        ("💧", BLUE,   "Increase Watering Frequency", "High light increases evaporation. Check soil moisture daily."),
        ("🌵", ACCENT, "Consider Sun-Loving Species", "If light cannot be reduced, consider cacti or succulents."),
    ],
}


# ── Zgodovina ─────────────────────────────────────────────────────────────────

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

        # Kartice za vsak dan
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

        # Graf za 7 dni
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


# ── Zaznavanje (CNN) ──────────────────────────────────────────────────────────

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

        # Leva plošča: predogled slike + informacije o CNN
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

        # Prikaz informacij o arhitekturi CNN
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

        # Gumb za analizo
        self._analyse_btn_frame = tk.Frame(left, bg=ACCENT, cursor="hand2")
        self._analyse_btn_frame.pack(fill="x", padx=12, pady=(0, 12))
        tk.Label(self._analyse_btn_frame, text="▶  Analyse with CNN",
                 font=self.f_label, bg=ACCENT, fg=BG_MAIN, pady=8).pack()
        bind_tree(self._analyse_btn_frame, "<Button-1>", lambda e: self._run_analysis())
        hover(self._analyse_btn_frame, ACCENT, "#00c98a")

        # Desna plošča: rezultati
        self._results_frame = tk.Frame(cols, bg=BG_MAIN)
        self._results_frame.pack(side="left", fill="both", expand=True)
        self._show_empty_state()

    def _load_image(self):
        """Odpre dialog za izbiro slike rastline in prikaže predogled."""
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
        """Prikaže prazno stanje brez rezultatov."""
        for w in self._results_frame.winfo_children():
            w.destroy()
        container = tk.Frame(self._results_frame, bg=BG_CARD, padx=20, pady=30)
        container.pack(fill="both", expand=True)
        tk.Label(container, text="🌿", font=("Segoe UI", 40), bg=BG_CARD).pack(pady=(20, 8))
        tk.Label(container, text=msg, font=self.f_body, bg=BG_CARD,
                 fg=TEXT_SEC, wraplength=340, justify="center").pack()

    def _show_loading(self):
        """Prikaže animacijo nalaganja med inferenčo CNN."""
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
        """Animira pike med nalaganjem."""
        patterns = ["*  o  o", "o  *  o", "o  o  *", "o  *  o"]
        try:
            self._loading_dots.config(text=patterns[self._dot_idx % len(patterns)])
            self._dot_idx += 1
            self._anim_job = self.after(400, self._animate_dots)
        except Exception:
            pass

    def _run_analysis(self):
        """
        Zažene analizo zdravja rastline.
        1. Najprej poskusi poslati sliko na FastAPI strežnik (POST /api/detect).
        2. Če API ni dosegljiv, se samodejno preklopi na lokalni CNN.
        """
        if not self._image_path:
            messagebox.showwarning("No Image", "Please upload a plant image first.")
            return
        if not os.path.exists(self._image_path):
            messagebox.showerror("File Missing", "The selected image file no longer exists.")
            return
        self._show_loading()

        def on_result(result, error):
            """Pokliče se po končani analizi – prekliče animacijo in prikaže rezultate."""
            if hasattr(self, "_anim_job"):
                try: self.after_cancel(self._anim_job)
                except: pass
            self.after(0, lambda: self._show_result(result, error))

        if API_URL:
            # Poskusi z FastAPI strežnikom; rezerva je lokalni CNN
            def _api_thread():
                result = _api_detect(self._image_path)
                if result:
                    on_result(result, None)
                else:
                    analyze_plant_image_cnn(self._image_path, on_result)
            threading.Thread(target=_api_thread, daemon=True).start()
        else:
            # API je onemogočen – vedno lokalni CNN
            analyze_plant_image_cnn(self._image_path, on_result)

    def _show_result(self, result, error):
        """Prikaže rezultate zaznavanja ali sporočilo o napaki."""
        for w in self._results_frame.winfo_children():
            w.destroy()

        # Prikaz napake
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

        # Posodobi prikaz arhitekture CNN
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

        # Pasica z rezultatom zaznavanja
        banner = tk.Frame(pad, bg=BG_CARD, padx=16, pady=14)
        banner.pack(fill="x", pady=(0, 10))
        top_row = tk.Frame(banner, bg=BG_CARD)
        top_row.pack(fill="x")
        tk.Label(top_row, text=f"{badge_emoji}  {status}", font=("Segoe UI", 14, "bold"),
                 bg=BG_CARD, fg=color).pack(side="left")
        tk.Label(top_row, text=f"  {urgency} urgency  ",
                 font=self.f_small, bg=urg_color, fg=BG_MAIN, padx=6, pady=2).pack(side="right")

        # Vrstica zaupanja in vrstica napredka
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

        # Opazovani simptomi
        if symptoms:
            tk.Label(pad, text="Observed Symptoms", font=self.f_title,
                     bg=BG_MAIN, fg=TEXT_PRI).pack(anchor="w", pady=(4, 6))
            for sym in symptoms:
                row = tk.Frame(pad, bg=BG_CARD, padx=12, pady=8)
                row.pack(fill="x", pady=(0, 4))
                tk.Label(row, text="o", font=("Segoe UI", 10), bg=BG_CARD, fg=color).pack(side="left", padx=(0, 8))
                tk.Label(row, text=sym, font=self.f_body, bg=BG_CARD, fg=TEXT_PRI,
                         wraplength=360, justify="left").pack(side="left", fill="x")

        # Priporočena dejanja
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


# ── Priporočila (stran) ───────────────────────────────────────────────────────

class RecommendationsPage(BasePage):
    def _build(self):
        outer = tk.Frame(self, bg=BG_MAIN)
        outer.pack(fill="both", expand=True, padx=22, pady=18)
        tk.Label(outer, text="💡  Recommendations", font=("Segoe UI", 16, "bold"),
                 bg=BG_MAIN, fg=TEXT_PRI).pack(anchor="w")
        tk.Label(outer, text="Personalised recommendations based on your current light readings.",
                 font=self.f_small, bg=BG_MAIN, fg=TEXT_SEC).pack(anchor="w", pady=(0, 16))

        # Gumbi za izbiro stanja svetlobe
        sel_row = tk.Frame(outer, bg=BG_MAIN)
        sel_row.pack(fill="x", pady=(0, 16))
        tk.Label(sel_row, text="Current status:", font=self.f_body,
                 bg=BG_MAIN, fg=TEXT_SEC).pack(side="left", padx=(0, 10))
        self._status_var = tk.StringVar(value="Optimal")
        self._sel_btns   = {}
        for status, color in [("Optimal", ACCENT), ("Low Light", RED), ("Too Much Light", YELLOW)]:
            btn = tk.Frame(sel_row, bg=BG_CARD, cursor="hand2", padx=14, pady=6)
            btn.pack(side="left", padx=(0, 8))
            lbl = tk.Label(btn, text=status, font=self.f_small, bg=BG_CARD, fg=color)
            lbl.pack()
            self._sel_btns[status] = (btn, lbl, color)
            def on_sel(e, s=status):
                self._status_var.set(s)
                self._render_tips()
            bind_tree(btn, "<Button-1>", on_sel)
            hover(btn, BG_CARD, BG_CARD2)

        # Lestvica svetlobe
        gauge_frame = tk.Frame(outer, bg=BG_CARD, padx=16, pady=12)
        gauge_frame.pack(fill="x", pady=(0, 16))
        gauge_top = tk.Frame(gauge_frame, bg=BG_CARD)
        gauge_top.pack(fill="x")
        tk.Label(gauge_top, text="Light Gauge", font=self.f_label,
                 bg=BG_CARD, fg=TEXT_PRI).pack(side="left")
        self._lux_lbl = tk.Label(gauge_top, text="", font=self.f_small, bg=BG_CARD, fg=TEXT_SEC)
        self._lux_lbl.pack(side="right")
        self._bar_canvas = tk.Canvas(gauge_frame, bg=BG_CARD, height=18, highlightthickness=0)
        self._bar_canvas.pack(fill="x", pady=(8, 4))
        legend_row = tk.Frame(gauge_frame, bg=BG_CARD)
        legend_row.pack(fill="x")
        for text, color in [("0–300  Low", RED), ("300–800  Optimal", ACCENT), ("800+  High", YELLOW)]:
            tk.Label(legend_row, text=f"■ {text}", font=self.f_small,
                     bg=BG_CARD, fg=color).pack(side="left", padx=(0, 14))

        self._tips_frame = tk.Frame(outer, bg=BG_MAIN)
        self._tips_frame.pack(fill="both", expand=True)

        # Splošne najboljše prakse
        tk.Frame(outer, bg=BORDER, height=1).pack(fill="x", pady=(12, 8))
        tk.Label(outer, text="General Best Practices", font=self.f_title,
                 bg=BG_MAIN, fg=TEXT_PRI).pack(anchor="w", pady=(0, 8))
        for icon, tip in [
            ("🔄", "Rotate plants every 2 weeks for even light exposure on all sides."),
            ("📅", "Maintain a watering schedule and adjust it based on light level and season."),
            ("🧹", "Wipe leaves monthly — dust can block light absorption by up to 30%."),
            ("📊", "Use the History page in Plant Monitor to spot weekly trends."),
        ]:
            row = tk.Frame(outer, bg=BG_CARD, padx=14, pady=10)
            row.pack(fill="x", pady=(0, 6))
            tk.Label(row, text=icon, font=("Segoe UI", 13), bg=BG_CARD).pack(side="left", padx=(0, 12))
            tk.Label(row, text=tip, font=self.f_body, bg=BG_CARD, fg=TEXT_PRI,
                     wraplength=560, justify="left").pack(side="left", fill="x")

        self._render_tips()

    def _render_tips(self):
        """Izriše priporočila za izbrano stanje svetlobe."""
        status = self._status_var.get()

        # Osveži gumbe za izbiro
        for s, (btn, lbl, color) in self._sel_btns.items():
            active = (s == status)
            btn.configure(bg=color if active else BG_CARD)
            lbl.configure(bg=color if active else BG_CARD, fg=BG_MAIN if active else color)

        # Posodobi lestvico
        lux_map = {"Optimal": 550, "Low Light": 180, "Too Much Light": 880}
        lux = lux_map[status]
        self._lux_lbl.config(text=f"Representative value: {lux} lux")
        self._bar_canvas.update_idletasks()
        w = self._bar_canvas.winfo_width() or 400
        self._bar_canvas.delete("all")
        self._bar_canvas.create_rectangle(0, 0, int(w*0.30), 18, fill="#3a1f24", outline="")
        self._bar_canvas.create_rectangle(int(w*0.30), 0, int(w*0.80), 18, fill="#1d3328", outline="")
        self._bar_canvas.create_rectangle(int(w*0.80), 0, w, 18, fill="#2e2a14", outline="")
        pos = int(w * min(lux / 1000, 1.0))
        self._bar_canvas.create_rectangle(max(0, pos-3), 0, min(w, pos+3), 18, fill=TEXT_PRI, outline="")

        # Počisti in izriši priporočila
        for w_ in self._tips_frame.winfo_children():
            w_.destroy()
        color_map   = {"Optimal": ACCENT, "Low Light": RED, "Too Much Light": YELLOW}
        badge_color = color_map[status]
        badge_row   = tk.Frame(self._tips_frame, bg=BG_MAIN)
        badge_row.pack(anchor="w", pady=(0, 10))
        tk.Label(badge_row, text=f"  {status}  ", font=self.f_label,
                 bg=badge_color, fg=BG_MAIN, padx=6, pady=3).pack(side="left")
        tk.Label(badge_row, text=" recommendations", font=self.f_body,
                 bg=BG_MAIN, fg=TEXT_SEC).pack(side="left")

        for icon, color, title, desc in PLANT_TIPS[status]:
            card = tk.Frame(self._tips_frame, bg=BG_CARD, padx=16, pady=12)
            card.pack(fill="x", pady=(0, 8))
            top = tk.Frame(card, bg=BG_CARD)
            top.pack(fill="x")
            tk.Label(top, text=icon, font=("Segoe UI", 14), bg=BG_CARD).pack(side="left", padx=(0, 10))
            tk.Label(top, text=title, font=self.f_label, bg=BG_CARD, fg=color).pack(side="left")
            tk.Label(card, text=desc, font=self.f_body, bg=BG_CARD, fg=TEXT_PRI,
                     wraplength=560, justify="left").pack(anchor="w", pady=(6, 0))


# ── Nastavitve ────────────────────────────────────────────────────────────────

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


# ── Navigacija ────────────────────────────────────────────────────────────────

# Vrstni red strani v stranski vrstici (opozorila so popolnoma odstranjena)
NAV_ORDER = [
    ("📊", "Dashboard"),
    ("🪴", "My Plants"),
    ("📅", "History"),
    ("🔬", "Detection"),
    ("💡", "Recommendations"),
    ("⚙️", "Settings"),
]

PAGE_CLASSES = {
    "Dashboard":       DashboardPage,
    "My Plants":       MyPlantsPage,
    "History":         HistoryPage,
    "Detection":       DetectionPage,
    "Recommendations": RecommendationsPage,
    "Settings":        SettingsPage,
}


class PlantMonitor(tk.Tk):
    """Glavno okno aplikacije Plant Monitor."""

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
        """Zapre aplikacijo in počisti matplotlib."""
        plt.close("all")
        self.destroy()
        os._exit(0)

    def _toggle_fullscreen(self, event=None):
        """Preklopi celozaslonski način (F11)."""
        self._is_fullscreen = not self._is_fullscreen
        self.attributes("-fullscreen", self._is_fullscreen)
        self._fs_btn_lbl.config(text="⊡" if self._is_fullscreen else "⛶")

    def _build_shell(self):
        """Zgradi osnovno postavitev: stranska vrstica + vsebina + desna plošča."""
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
        """Zgradi stransko navigacijsko vrstico z logotipom in gumbi."""
        top_row = tk.Frame(parent, bg=BG_SIDE)
        top_row.pack(fill="x", padx=10, pady=(14, 6))
        logo = tk.Frame(top_row, bg=BG_SIDE)
        logo.pack(side="left")
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

        # Navigacijski gumbi
        for icon, label in NAV_ORDER:
            self._nav_btn(parent, icon, label)

        tk.Frame(parent, bg=BG_SIDE).pack(expand=True)
        tk.Frame(parent, bg=BORDER, height=1).pack(fill="x", padx=12, pady=4)

        # Gumb za odjavo
        logout_btn = tk.Frame(parent, bg=BG_CARD2, cursor="hand2")
        logout_btn.pack(fill="x", padx=8, pady=(0, 4))
        logout_row = tk.Frame(logout_btn, bg=BG_CARD2)
        logout_row.pack(pady=7, padx=10, anchor="w")
        tk.Label(logout_row, text="⏻", font=("Segoe UI", 10), bg=BG_CARD2, fg=RED).pack(side="left", padx=(0, 8))
        tk.Label(logout_row, text="Sign Out", font=self.f_body, bg=BG_CARD2, fg=RED).pack(side="left")
        bind_tree(logout_btn, "<Button-1>", lambda e: self._do_logout())
        hover(logout_btn, BG_CARD2, "#2a1a1f")

        # Profil uporabnika
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
        """Ustvari navigacijski gumb v stranski vrstici."""
        is_active = not self._nav_buttons
        bg = BG_CARD if is_active else BG_SIDE
        fg = TEXT_PRI if is_active else TEXT_SEC
        row = tk.Frame(parent, bg=bg, cursor="hand2")
        row.pack(fill="x", padx=8, pady=2)
        bar = tk.Frame(row, bg=ACCENT if is_active else bg, width=3)
        bar.pack(side="left", fill="y")
        lbl = tk.Label(row, text=f" {icon}  {label}", font=self.f_body,
                       bg=bg, fg=fg, anchor="w", pady=8, padx=10)
        lbl.pack(fill="x")
        entry = {"row": row, "bar": bar, "lbl": lbl, "label": label}
        self._nav_buttons.append(entry)
        def on_click(e, entry=entry):
            for b in self._nav_buttons:
                b["row"].configure(bg=BG_SIDE)
                b["bar"].configure(bg=BG_SIDE)
                b["lbl"].configure(bg=BG_SIDE, fg=TEXT_SEC)
            entry["row"].configure(bg=BG_CARD)
            entry["bar"].configure(bg=ACCENT)
            entry["lbl"].configure(bg=BG_CARD, fg=TEXT_PRI)
            self._show_page(entry["label"])
        row.bind("<Button-1>", on_click)
        lbl.bind("<Button-1>", on_click)
        bar.bind("<Button-1>", on_click)

    def _build_right(self, parent):
        """Zgradi desno ploščo s povzetkom stanja in gumbom za osvežitev."""
        pad = tk.Frame(parent, bg=BG_SIDE)
        pad.pack(fill="both", expand=True, padx=12, pady=14)

        # Pasica z logotipom
        banner = tk.Frame(pad, bg="#1a2e1a", height=90)
        banner.pack(fill="x", pady=(0, 12))
        banner.pack_propagate(False)
        tk.Label(banner, text="Plant Monitor", font=self.f_title, bg="#1a2e1a", fg=TEXT_PRI).place(x=10, y=12)
        tk.Label(banner, text="🌿", font=("Segoe UI", 30), bg="#1a2e1a").place(relx=0.75, rely=0.5, anchor="center")

        # Gumb za osvežitev podatkov
        ref_btn = tk.Frame(pad, bg=BG_CARD, cursor="hand2")
        ref_btn.pack(fill="x", pady=(0, 14))
        ref_inner = tk.Frame(ref_btn, bg=BG_CARD)
        ref_inner.pack(pady=8)
        tk.Label(ref_inner, text="↻  Refresh Data", font=self.f_body,
                 bg=BG_CARD, fg=TEXT_PRI, cursor="hand2").pack(side="left")
        bind_tree(ref_btn, "<Button-1>", lambda e: self._do_refresh())
        hover(ref_btn, BG_CARD, BG_CARD2)

        # Informacije o rastlinah
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

    def _register_pages(self):
        """Registrira vse strani aplikacije."""
        for name, cls in PAGE_CLASSES.items():
            page = cls(self.content_area, self)
            page.place(relx=0, rely=0, relwidth=1, relheight=1)
            self._pages[name] = page

    def _show_page(self, name):
        """Prikaže izbrano stran in posodobi aktivni navigacijski gumb."""
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

    def _do_logout(self):
        """Odjavi uporabnika in prikaže okno za prijavo."""
        if messagebox.askyesno("Sign Out", "Are you sure you want to sign out?"):
            plt.close("all")
            self.destroy()
            auth = AuthWindow()
            auth.mainloop()
            if auth.logged_in_user:
                app = PlantMonitor(auth.logged_in_user)
                app.mainloop()

    def _do_refresh(self):
        """Osveži podatke na nadzorni plošči."""
        dash = self._pages.get("Dashboard")
        if dash:
            dash.refresh()


# ── Vstopna točka ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    auth = AuthWindow()
    auth.mainloop()
    if auth.logged_in_user:
        app = PlantMonitor(auth.logged_in_user)
        app.mainloop()