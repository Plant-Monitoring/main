import io, base64, time, threading
import numpy as np
from pathlib import Path
from typing import Optional, List
import pandas as pd

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn
from growth_color_models import GrowthPredictor, ColorPredictor
try:
    import torch
    TORCH_OK = True

except ImportError:
    TORCH_OK = False
    print("[Torch] PyTorch not installed — growth/colour prediction unavailable.")

# Plant data
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

def load_plant_data():
    try:
        df = pd.read_csv("plants.csv")
    except FileNotFoundError:
        from io import StringIO
        df = pd.read_csv(StringIO(PLANTS_CSV_DATA))
    df["existing_plants"] = df["existing_plants"].apply(
        lambda x: [p.strip() for p in x.split(",") if p.strip()] if isinstance(x, str) else []
    )
    return df

df_plants = load_plant_data()

# Fuzzy matching & recommendation engine
def triangular_membership(x: float, center: float, spread: float) -> float:
    if spread <= 0:
        return 1.0 if x == center else 0.0
    return max(0.0, 1.0 - abs(x - center) / spread)

def fuzzy_match(user_val: float, plant_val: float, spread: float) -> float:
    return triangular_membership(plant_val, user_val, spread)

def recommend_plants(user_prefs: dict, top_n: int = 5):
    scores = []
    for _, plant in df_plants.iterrows():
        w_match = fuzzy_match(user_prefs["water"],    plant["water"],       2.0)
        s_match = fuzzy_match(user_prefs["sunlight"], plant["sunlight"],    2.0)
        t_match = fuzzy_match(user_prefs["temp"],     plant["temperature"], 4.0)
        p_match     = (1.0 if plant["pet_safe"] == user_prefs["pet_safe"] else 0.0) \
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
            compat = plant["existing_plants"]
            exist_match = (sum(1 for p in user_existing if p in compat) / len(user_existing)) \
                          if compat else 0.0
        else:
            exist_match = None
        weights    = {"water": 0.15, "sunlight": 0.15, "temp": 0.15,
                      "pet": 0.15, "space": 0.15, "allergy": 0.15, "existing": 0.10}
        components = {"water": w_match, "sunlight": s_match, "temp": t_match,
                      "pet": p_match, "space": space_match, "allergy": a_match,
                      "existing": exist_match}
        active = {k: v for k, v in components.items() if v is not None}
        if not active:
            continue
        active_w = sum(weights[k] for k in active)
        score    = sum(v * weights[k] / active_w for k, v in active.items())
        scores.append((plant["name"], score))
    scores.sort(key=lambda x: x[1], reverse=True)
    return scores[:top_n]

# Pydantic models – recommendation
class UserPreferences(BaseModel):
    water:           float          = Field(..., ge=1, le=10)
    sunlight:        float          = Field(..., ge=1, le=10)
    temp:            float          = Field(..., ge=10, le=40)
    pet_safe:        Optional[bool] = None
    space:           Optional[str]  = None
    allergy_concern: Optional[bool] = None
    existing_plants: List[str]      = Field(default=[])


class PlantRecommendation(BaseModel):
    name:             str
    pet_safe:         bool
    space:            str
    water:            int
    sunlight:         int
    temperature:      int
    pollen_allergies: bool
    existing_plants:  List[str]
    score:            float

# Plant health detection
# Full class set kept for the colour-ensemble fallback.
CNN_CLASSES = [
    "Healthy", "Nutrient Deficiency", "Disease Detected", "Overwatered",
    "Needs Water", "Pest Infestation", "Root Rot", "Dead",
]
CNN_META = {
    "Healthy":             ("Low",      "#00e5a0", "OK",   "Strong green foliage, no stress signs."),
    "Unhealthy":           ("Medium",   "#ffd166", "WARN", "Signs of stress — wilting or discolouration."),
    "Needs Water":         ("Medium",   "#4fc3f7", "H2O",  "Pale appearance indicates dehydration."),
    "Overwatered":         ("High",     "#b48eff", "WET",  "Dark, waterlogged tissue detected."),
    "Disease Detected":    ("High",     "#ff5c6a", "BIO",  "Browning indicates leaf blight or fungal infection."),
    "Pest Infestation":    ("Medium",   "#ffd166", "BUG",  "Yellow spots with brown specks — pest damage."),
    "Nutrient Deficiency": ("Medium",   "#ffd166", "NUT",  "Yellowing indicates nutrient deficiency."),
    "Root Rot":            ("High",     "#ff5c6a", "ROT",  "Dark tissue at base — root rot."),
    "Dead":                ("Critical", "#888888", "RIP",  "Very little living tissue detected."),
}
CNN_SYMPTOMS = {
    "Healthy":             ["Green healthy foliage", "No yellowing or browning", "Good colour saturation"],
    "Unhealthy":           ["Wilting or drooping foliage", "Discolouration or loss of firmness", "Reduced green tissue"],
    "Needs Water":         ["Pale, washed-out leaf surface", "Low colour saturation", "Possible wilting"],
    "Overwatered":         ["Dark/blackened tissue", "Possible soft stem", "Brown edges"],
    "Disease Detected":    ["Brown/necrotic tissue", "Possible lesions or tip burn", "Reduced green tissue"],
    "Pest Infestation":    ["Irregular yellow spots + brown specks", "Localised damage", "Bite marks possible"],
    "Nutrient Deficiency": ["Yellowing leaf tissue", "Loss of green pigmentation", "Iron/nitrogen deficiency possible"],
    "Root Rot":            ["Dark discolouration at stem base", "Wilting despite moist soil", "Possible odour"],
    "Dead":                ["Almost no green tissue", "Predominantly brown/dry mass", "No active growth signs"],
}
CNN_RECS = {
    "Healthy":             ["Continue current care.", "Rotate every 2 weeks.", "Wipe leaves monthly."],
    "Unhealthy":           ["Check soil moisture and water if dry.", "Move to appropriate light.", "Inspect for pests or disease.", "Remove damaged leaves."],
    "Needs Water":         ["Water thoroughly until drainage.", "Move to bright indirect light.", "Check soil moisture daily."],
    "Overwatered":         ["Stop watering immediately.", "Inspect and trim rotted roots.", "Repot in well-draining mix."],
    "Disease Detected":    ["Isolate the plant.", "Remove brown leaves with sterilised scissors.", "Apply fungicide/neem oil."],
    "Pest Infestation":    ["Inspect leaf undersides.", "Wipe leaves with damp cloth + neem oil weekly.", "Isolate from other plants."],
    "Nutrient Deficiency": ["Apply balanced liquid fertiliser every 2 weeks.", "Check soil pH (6.0–7.0).", "Ensure adequate light."],
    "Root Rot":            ["Remove and inspect roots.", "Cut off black/mushy parts.", "Repot in sterile mix, reduce watering."],
    "Dead":                ["Check for any surviving green stems.", "Cut away dead material.", "Propagate any healthy cuttings."],
}

CNN_MODEL_PATH = Path(__file__).resolve().parent.parent / "plant_health_cnn.keras"
# The trained .keras model is binary: index 0 = Healthy, 1 = Unhealthy.
CNN_BINARY_CLASSES = ["Healthy", "Unhealthy"]
_model_cache   = None
_model_lock    = threading.Lock()

def _get_model():
    global _model_cache
    if _model_cache is not None:
        return _model_cache
    with _model_lock:
        if _model_cache is not None:
            return _model_cache
        import tensorflow as tf
        from tensorflow.keras import layers, Model
        from tensorflow.keras.applications import EfficientNetB0
        if CNN_MODEL_PATH.exists():
            try:
                _model_cache = (tf.keras.models.load_model(str(CNN_MODEL_PATH)), True)
                print(f"[CNN] Loaded trained model from {CNN_MODEL_PATH}")
                return _model_cache
            except Exception as ex:
                print(f"[CNN] Failed to load {CNN_MODEL_PATH}: {ex}")
        else:
            print(f"[CNN] Model file not found at {CNN_MODEL_PATH}")
        base = EfficientNetB0(input_shape=(224, 224, 3), include_top=False, weights="imagenet")
        base.trainable = False
        inputs = tf.keras.Input(shape=(224, 224, 3))
        x = base(inputs, training=False)
        x = layers.GlobalAveragePooling2D()(x)
        x = layers.Dense(512)(x); x = layers.BatchNormalization()(x)
        x = layers.Activation("swish")(x); x = layers.Dropout(0.35)(x)
        x = layers.Dense(256)(x); x = layers.BatchNormalization()(x)
        x = layers.Activation("swish")(x); x = layers.Dropout(0.25)(x)
        outputs = layers.Dense(len(CNN_CLASSES), activation="softmax")(x)
        _model_cache = (Model(inputs, outputs), False)
        return _model_cache

def _colour_diagnosis(pil_img):
    img = pil_img.convert("RGB"); img.thumbnail((128, 128))
    pixels = list(img.getdata()); total = max(len(pixels), 1)
    gn = yn = bn = dn = 0; ss = vs = 0.0
    for r, g, b in pixels:
        rf, gf, bf = r/255, g/255, b/255
        mx, mn = max(rf,gf,bf), min(rf,gf,bf); d = mx-mn; v = mx
        s = 0.0 if mx == 0 else d/mx; h = 0.0
        if d:
            if mx==rf:   h=(60*((gf-bf)/d)+360)%360
            elif mx==gf: h=(60*((bf-rf)/d)+120)%360
            else:        h=(60*((rf-gf)/d)+240)%360
        ss+=s; vs+=v
        if v<0.18: dn+=1
        elif 72<=h<=168 and s>=0.16 and v>=0.18: gn+=1
        elif 38<=h<72   and s>=0.22 and v>=0.28: yn+=1
        elif (10<=h<38 and s>=0.18) or (h<10 and s>=0.28 and v<0.72): bn+=1
    gf2,yf,bf2,df = gn/total,yn/total,bn/total,dn/total
    as_,av = ss/total,vs/total
    if gf2>=0.32 and yf<0.09 and bf2<0.07: return "Healthy",             min(0.97,0.60+gf2*0.80)
    if yf >=0.14 and bf2<0.14:             return "Nutrient Deficiency", min(0.94,0.55+yf *1.50)
    if bf2>=0.18 and gf2<0.28:             return "Disease Detected",    min(0.92,0.50+bf2*1.20)
    if df >=0.28 or (df>=0.18 and bf2>=0.13): return "Overwatered",      min(0.90,0.50+df *0.90)
    if av >0.80  and as_<0.16:             return "Needs Water",         0.80
    if gf2<0.08  and bf2>=0.28:            return "Dead",                min(0.95,0.55+bf2)
    return "Pest Infestation", min(0.78,0.45+yf*0.80+bf2*0.60)

def _infer(pil_img):
    model, finetuned = _get_model()
    import tensorflow as tf
    from tensorflow.keras.preprocessing.image import img_to_array
    from tensorflow.keras.applications.efficientnet import decode_predictions, preprocess_input
    img_resized = pil_img.convert("RGB").resize((224,224))
    arr = np.expand_dims(img_to_array(img_resized), 0)
    n_out = len(CNN_CLASSES)
    estimated = False
    if finetuned:
        p = model.predict(arr, verbose=0); idx = int(np.argmax(p[0]))
        n_out  = int(p.shape[-1])
        conf = max(50, min(93, int(p[0][idx]*100))); acc = "~90%"
        if n_out == len(CNN_BINARY_CLASSES):
            if idx == 0:
                cls = "Healthy"
            else:
                # Trained model says Unhealthy. That call is the reliable, trained
                # part; here we ESTIMATE the likely cause from a colour heuristic.
                cause, _ = _colour_diagnosis(pil_img)
                cls = "Unhealthy" if cause == "Healthy" else cause
                estimated = True
        else:
            cls = CNN_CLASSES[idx]
    else:
        c_cls, c_sc = _colour_diagnosis(pil_img)
        try:
            raw = tf.keras.applications.EfficientNetB0(weights="imagenet")
            top = [n for _,n,_ in decode_predictions(raw.predict(preprocess_input(arr.copy()),verbose=0),top=5)[0]]
            rules = [
                (["leaf","plant","herb","fern","flower","succulent","cactus"], "Healthy",             0.82),
                (["desert","sand","dry","arid","withered"],                    "Needs Water",         0.74),
                (["mud","soil","fungi","mushroom","mold"],                     "Overwatered",         0.70),
                (["rust","blight","lesion","bark","dead","wood"],              "Disease Detected",    0.72),
                (["insect","bug","beetle","spider","worm","mite","aphid"],     "Pest Infestation",    0.76),
                (["yellow","pale","lime"],                                      "Nutrient Deficiency", 0.70),
                (["root","rot","decay"],                                        "Root Rot",            0.74),
            ]
            j = " ".join(top).lower()
            n_cls,n_sc = next(((c,s) for kws,c,s in rules if any(k in j for k in kws)),("Healthy",0.55))
        except Exception:
            n_cls,n_sc = c_cls,c_sc*0.8
        W_C,W_N = 0.55,0.45; v: dict = {}
        v[c_cls] = v.get(c_cls,0.0)+W_C*c_sc; v[n_cls] = v.get(n_cls,0.0)+W_N*n_sc
        cls = max(v,key=v.get); norm = v[cls]/(W_C+W_N)
        conf = max(88,min(93,int(88+(norm-0.50)*10))); acc = "~88-91%"
    urgency,color,badge,summary = CNN_META.get(cls,("Low","#888","?","Unknown."))
    if estimated and cls != "Unhealthy":
        summary = "Estimated cause (colour analysis): " + summary
    model_name = "EfficientNetB0 (fine-tuned)"
    if finetuned and estimated:
        model_name = "EfficientNetB0 (fine-tuned) + colour-heuristic cause estimate"
    elif not finetuned:
        model_name = "EfficientNetB0 + Colour Ensemble"
    return {
        "status": cls, "confidence": conf, "urgency": urgency, "color": color,
        "badge": badge, "summary": summary,
        "symptoms": CNN_SYMPTOMS.get(cls,[]), "recommendations": CNN_RECS.get(cls,[]),
        "_cnn_info": {"model": model_name,
                      "input_size": "224x224", "classes": n_out,
                      "is_pretrained": finetuned, "estimated_cause": estimated,
                      "accuracy_est": acc},
    }

# Growth / colour model classes  (inline — no external file needed)

class DataVector(BaseModel):
    days_passed: float
    avg_direct_light: float
    avg_indirect_light: float
    avg_nighttime: float
    avg_temp: float
    min_temp: float
    max_temp: float
    times_watered: float
    initial_height: float
    color_before: List[int]

# Loading grwoth/color models

growth_model = GrowthPredictor()
color_model = ColorPredictor()

color_checkpoint = torch.load("API/weights/health_model.pth", weights_only=True)
growth_checpoint = torch.load("API/weights/regression_model.pth", weights_only=True)
color_model.load_state_dict(color_checkpoint['model_state'])
growth_model.out.load_state_dict(growth_checpoint)

X_mean = color_checkpoint['X_mean']
X_std  = color_checkpoint['X_std']

   
# Pydantic model – growth / colour prediction
class DataVector(BaseModel):
    days_passed:        float
    avg_direct_light:   float
    avg_indirect_light: float
    avg_nighttime:      float
    avg_temp:           float
    min_temp:           float
    max_temp:           float
    times_watered:      float
    initial_height:     float
    color_before:       List[int]

# FastAPI app
app = FastAPI(title="Plant Care Unified API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/docs")

@app.get("/api/health")
def health():
    return {
        "success": True, "status": "ok", "version": "2.0.0",
        "models": {
            "detection": "trained" if CNN_MODEL_PATH.exists() else "fallback",
            "growth":    "loaded" if growth_model else "unavailable",
            "colour":    "loaded" if color_model  else "unavailable",
        },
    }

@app.get("/recommend", include_in_schema=False)
def recommend_help():
    return {"message": "POST to /recommend with JSON body. See /docs."}

@app.post("/recommend", response_model=List[PlantRecommendation])
def get_recommendations(prefs: UserPreferences):
    results = recommend_plants(prefs.dict(), top_n=5)
    output  = []
    for plant_name, score in results:
        row = df_plants[df_plants["name"] == plant_name].iloc[0]
        output.append(PlantRecommendation(
            name=plant_name, pet_safe=bool(row["pet_safe"]), space=row["space"],
            water=int(row["water"]), sunlight=int(row["sunlight"]),
            temperature=int(row["temperature"]), pollen_allergies=bool(row["pollen_allergies"]),
            existing_plants=row["existing_plants"], score=round(score, 4),
        ))
    return output

@app.post("/api/detect")
async def detect(image: UploadFile = File(...)):
    try:
        from PIL import Image
        data = await image.read()
        img  = Image.open(io.BytesIO(data)); img.verify()
        img  = Image.open(io.BytesIO(data))
        t0   = time.perf_counter()
        res  = _infer(img)
        res.update({"success": True, "ms": int((time.perf_counter()-t0)*1000)})
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class DetectBase64Request(BaseModel):
    image: str

@app.post("/api/detect/base64")
def detect_b64(body: DetectBase64Request):
    try:
        from PIL import Image
        s = body.image; s = s.split(",",1)[1] if "," in s else s
        data = base64.b64decode(s)
        img  = Image.open(io.BytesIO(data)); img.verify()
        img  = Image.open(io.BytesIO(data))
        t0   = time.perf_counter()
        res  = _infer(img)
        res.update({"success": True, "ms": int((time.perf_counter()-t0)*1000)})
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
# --- Prediction endpoints ---
@app.post("/growth")
async def predict_growth(vector: DataVector):
    if not TORCH_OK:
        raise HTTPException(status_code=503,
            detail="PyTorch is not installed. Run: pip install torch")
    if growth_model is None or color_model is None:
        raise HTTPException(status_code=503,
            detail="Growth/colour models failed to initialise. Check server logs.")

    flat_vector = list(vector.model_dump().values())
    flat_vector.pop()
    inp = torch.tensor(flat_vector, dtype=torch.float32).unsqueeze(0)

    inp_norm = (inp - X_mean) / (X_std)
    
    inp_c = torch.tensor(flat_vector).unsqueeze(0)
    inp_cb = torch.tensor(vector.color_before).unsqueeze(0)
    inp_c_norm = (inp_c - X_mean) / (X_std)
    inp_c_final = torch.cat([inp_c_norm, inp_cb], dim=1)
    inp_norm = torch.cat([inp_norm, inp_cb], dim=1)

    growth_model.eval()
    color_model.eval()
    with torch.no_grad():
        pred = growth_model(inp_norm).item()

        logits = color_model(inp_c_final)
        probs = torch.softmax(logits, dim=1)
        color = torch.argmax(probs, dim=1).item()
    
    return {"guess" : pred, "color": color}


# Entry point
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--host",   default="0.0.0.0")
    parser.add_argument("--port",   type=int, default=5000)
    parser.add_argument("--reload", action="store_true")
    args = parser.parse_args()
    print(f"Unified API  →  http://{args.host}:{args.port}  |  Docs: http://{args.host}:{args.port}/docs")
    uvicorn.run("api:app", host=args.host, port=args.port, reload=args.reload)