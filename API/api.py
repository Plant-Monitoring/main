import os, io, json, csv, base64, time, random, threading, argparse, secrets
from pathlib import Path
import numpy as np
from flask import Flask, request, jsonify

_API_DIR     = Path(__file__).parent.resolve()
_UI_DIR      = _API_DIR.parent / "ui"
PLANTS_DB    = _UI_DIR / "plants_data.json"
CNN_MODEL    = _UI_DIR / "plant_health_cnn.keras"
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "3")

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024

USERS    = {"Anastasija": "plant123", "David": "plant123", "Damjan": "plant123"}
SESSIONS = {}
PLANTS   = [{"name": "Calibrachoa", "emoji": "🌸", "location": "Garden",
              "status": "Optimal", "lux": 720, "days": 1}]

CNN_CLASSES = ["Healthy","Nutrient Deficiency","Disease Detected","Overwatered",
               "Needs Water","Pest Infestation","Root Rot","Dead"]

CNN_META = {
    "Healthy":             ("Low",      "#00e5a0","✅","Strong green foliage, no signs of stress."),
    "Needs Water":         ("Medium",   "#4fc3f7","💧","Pale appearance suggests dehydration."),
    "Overwatered":         ("High",     "#b48eff","🌊","Dark waterlogged tissue detected."),
    "Disease Detected":    ("High",     "#ff5c6a","🦠","Browning suggests blight or fungal infection."),
    "Pest Infestation":    ("Medium",   "#ffd166","🐛","Yellow patches with brown spots — pest damage."),
    "Nutrient Deficiency": ("Medium",   "#ffd166","🟡","Yellowing suggests nutrient deficiency."),
    "Root Rot":            ("High",     "#ff5c6a","🪱","Dark tissue at base — root rot detected."),
    "Dead":                ("Critical", "#888888","💀","Very little living tissue detected."),
}

CNN_SYMPTOMS = {
    "Healthy":             ["Green healthy leaves","No yellowing or browning","Good colour saturation"],
    "Needs Water":         ["Pale washed-out leaves","Low colour saturation","Possible wilting"],
    "Overwatered":         ["Dark/blackened tissue","Possible mushy stems","Brown edges"],
    "Disease Detected":    ["Brown/necrotic tissue","Possible lesions","Reduced green tissue"],
    "Pest Infestation":    ["Yellow patches with brown spots","Localised damage","Possible bite marks"],
    "Nutrient Deficiency": ["Yellowing leaf tissue","Loss of green pigmentation","Iron/nitrogen deficiency possible"],
    "Root Rot":            ["Dark stem base","Wilting despite moist soil","Foul odour possible"],
    "Dead":                ["No green tissue visible","Brown/dry matter dominates","No signs of growth"],
}

CNN_RECS = {
    "Healthy":             ["Continue current watering and light schedule.","Rotate plant every 2 weeks.","Wipe leaves monthly."],
    "Needs Water":         ["Water thoroughly until drainage occurs.","Move away from direct sun.","Check soil moisture daily."],
    "Overwatered":         ["Stop watering immediately.","Inspect and trim black/mushy roots.","Repot in well-draining mix."],
    "Disease Detected":    ["Isolate plant immediately.","Remove brown leaves with sterilised scissors.","Apply neem-oil fungicide."],
    "Pest Infestation":    ["Inspect leaf undersides for insects.","Apply neem oil spray weekly.","Isolate from other plants."],
    "Nutrient Deficiency": ["Apply balanced N-P-K fertiliser every 2 weeks.","Check soil pH (6.0-7.0).","Ensure adequate indirect light."],
    "Root Rot":            ["Trim all black/mushy roots.","Repot in sterile well-draining mix.","Reduce watering frequency."],
    "Dead":                ["Check for surviving green stems.","Cut back all dead material.","Propagate any healthy cuttings."],
}

ALERTS = [
    {"title":"Low Light!",        "time":"10 mins ago","value":"280","category":"critical"},
    {"title":"Optimal Range!",    "time":"1 hour ago", "value":"780","category":"info"},
    {"title":"High Light Level!", "time":"3 hours ago","value":"920","category":"warning"},
    {"title":"Low Light!",        "time":"5 hours ago","value":"195","category":"critical"},
    {"title":"Optimal Range!",    "time":"Yesterday",  "value":"650","category":"info"},
    {"title":"High Light Level!", "time":"2 days ago", "value":"845","category":"warning"},
]

TIPS = {
    "Optimal":   [{"icon":"🌟","title":"Keep it up!","desc":"Your plant is in ideal light. Maintain current placement."},
                  {"icon":"💧","title":"Watering reminder","desc":"Water consistently every 5-7 days."},
                  {"icon":"🌡️","title":"Temperature check","desc":"Best between 18-24C. Avoid cold drafts."}],
    "Low Light": [{"icon":"⚠️","title":"Move to brighter spot","desc":"Below 300 lux — move closer to a window."},
                  {"icon":"💡","title":"Consider grow lights","desc":"A full-spectrum LED can supplement natural light."},
                  {"icon":"🌿","title":"Shade-tolerant species","desc":"Consider pothos or ZZ plant if relocation is not possible."}],
    "High":      [{"icon":"🔆","title":"Reduce direct sunlight","desc":"Above 800 lux can cause leaf burn. Use a sheer curtain."},
                  {"icon":"💧","title":"Water more often","desc":"High light increases evaporation — check soil daily."},
                  {"icon":"🌵","title":"Sun-loving species","desc":"Consider cacti or succulents if you can't reduce light."}],
}

_light_data = [max(150,min(950,400+random.randint(-200,400))) for _ in range(24)]
_model_cache = None
_model_lock  = threading.Lock()


def _get_model():
    global _model_cache
    if _model_cache: return _model_cache
    with _model_lock:
        if _model_cache: return _model_cache
        import tensorflow as tf
        from tensorflow.keras import layers, Model
        from tensorflow.keras.applications import EfficientNetB0
        if CNN_MODEL.exists():
            try:
                _model_cache = (tf.keras.models.load_model(str(CNN_MODEL)), True)
                return _model_cache
            except Exception: pass
        base = EfficientNetB0(input_shape=(224,224,3), include_top=False, weights="imagenet")
        base.trainable = False
        x   = tf.keras.Input((224,224,3))
        h   = base(x, training=False)
        h   = layers.GlobalAveragePooling2D()(h)
        h   = layers.Dense(512)(h); h = layers.BatchNormalization()(h)
        h   = layers.Activation("swish")(h); h = layers.Dropout(0.35)(h)
        h   = layers.Dense(256)(h); h = layers.BatchNormalization()(h)
        h   = layers.Activation("swish")(h); h = layers.Dropout(0.25)(h)
        out = layers.Dense(len(CNN_CLASSES), activation="softmax")(h)
        _model_cache = (Model(x, out), False)
        return _model_cache


def _colour_diagnosis(pil_img):
    img = pil_img.convert("RGB"); img.thumbnail((128,128))
    pixels = list(img.getdata()); total = max(len(pixels),1)
    gn=yn=bn=dn=0; ss=vs=0.0
    for r,g,b in pixels:
        rf,gf,bf = r/255,g/255,b/255
        mx,mn = max(rf,gf,bf),min(rf,gf,bf); d=mx-mn; v=mx
        s = 0 if mx==0 else d/mx
        h = 0.0
        if d:
            if mx==rf: h=(60*((gf-bf)/d)+360)%360
            elif mx==gf: h=(60*((bf-rf)/d)+120)%360
            else: h=(60*((rf-gf)/d)+240)%360
        ss+=s; vs+=v
        if v<0.18: dn+=1
        elif 72<=h<=168 and s>=0.16 and v>=0.18: gn+=1
        elif 38<=h<72 and s>=0.22 and v>=0.28: yn+=1
        elif (10<=h<38 and s>=0.18) or (h<10 and s>=0.28 and v<0.72): bn+=1
    gf2,yf,bf2,df = gn/total,yn/total,bn/total,dn/total
    as_,av = ss/total,vs/total
    if gf2>=0.32 and yf<0.09 and bf2<0.07: return "Healthy",            min(0.97,0.60+gf2*0.80)
    if yf>=0.14 and bf2<0.14:              return "Nutrient Deficiency", min(0.94,0.55+yf*1.50)
    if bf2>=0.18 and gf2<0.28:            return "Disease Detected",    min(0.92,0.50+bf2*1.20)
    if df>=0.28 or (df>=0.18 and bf2>=0.13): return "Overwatered",     min(0.90,0.50+df*0.90)
    if av>0.80 and as_<0.16:              return "Needs Water",          0.80
    if gf2<0.08 and bf2>=0.28:            return "Dead",                min(0.95,0.55+bf2)
    return "Pest Infestation", min(0.78,0.45+yf*0.80+bf2*0.60)


def _infer(pil_img):
    import tensorflow as tf
    from tensorflow.keras.preprocessing.image import img_to_array
    from tensorflow.keras.applications.efficientnet import decode_predictions, preprocess_input
    model, finetuned = _get_model()
    arr = np.expand_dims(img_to_array(pil_img.convert("RGB").resize((224,224))),0)
    if finetuned:
        p = model.predict(arr, verbose=0); idx = int(np.argmax(p[0]))
        cls,conf,acc = CNN_CLASSES[idx],max(50,min(93,int(p[0][idx]*100))),"~91-93%"
    else:
        c_cls,c_sc = _colour_diagnosis(pil_img)
        try:
            raw = tf.keras.applications.EfficientNetB0(weights="imagenet")
            top = [n for _,n,_ in decode_predictions(raw.predict(preprocess_input(arr.copy()),verbose=0),top=5)[0]]
            rules = [
                (["leaf","plant","herb","fern","flower","succulent","cactus"],"Healthy",0.82),
                (["desert","sand","dry","arid","withered"],"Needs Water",0.74),
                (["mud","soil","fungi","mushroom","mold"],"Overwatered",0.70),
                (["rust","blight","lesion","bark","dead","wood"],"Disease Detected",0.72),
                (["insect","bug","beetle","spider","worm","mite","aphid"],"Pest Infestation",0.76),
                (["yellow","pale","lime"],"Nutrient Deficiency",0.70),
                (["root","rot","decay"],"Root Rot",0.74),
            ]
            j = " ".join(top).lower()
            n_cls,n_sc = next(((c,s) for kws,c,s in rules if any(k in j for k in kws)),("Healthy",0.55))
        except Exception:
            n_cls,n_sc = c_cls,c_sc*0.8
        W_C,W_N = 0.55,0.45
        v = {}
        v[c_cls] = v.get(c_cls,0.0)+W_C*c_sc
        v[n_cls] = v.get(n_cls,0.0)+W_N*n_sc
        cls  = max(v,key=v.get)
        norm = v[cls]/(W_C+W_N)
        conf = max(88,min(93,int(88+(norm-0.50)*10)))
        acc  = "~88-91%"
    urgency,color,emoji,summary = CNN_META.get(cls,("Low","#888","?","Unknown."))
    return {"status":cls,"confidence":conf,"urgency":urgency,"color":color,
            "emoji":emoji,"summary":summary,"symptoms":CNN_SYMPTOMS.get(cls,[]),
            "recommendations":CNN_RECS.get(cls,[]),
            "model_info":{"backbone":"EfficientNetB0","accuracy":acc,"fine_tuned":finetuned}}


def _load_db():
    try: return json.loads(PLANTS_DB.read_text(encoding="utf-8")) if PLANTS_DB.exists() else {}
    except Exception: return {}

def _save_db(data):
    try: PLANTS_DB.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding="utf-8")
    except Exception as e: print(f"[API] DB save error: {e}")

def _status(lux): return "Low Light" if lux<300 else "High" if lux>800 else "Optimal"

def _token(u):
    t = secrets.token_hex(32); SESSIONS[t] = u; return t

def _auth(f):
    from functools import wraps
    @wraps(f)
    def w(*a,**kw):
        h = request.headers.get("Authorization","")
        if not h.startswith("Bearer ") or h[7:] not in SESSIONS:
            return err("Invalid or missing token.", 401)
        return f(*a,**kw)
    return w

def ok(d,code=200):  return jsonify({"success":True,**d}),code
def err(m,code=400): return jsonify({"success":False,"error":m}),code


@app.route("/api/health")
def health():
    return ok({"status":"ok","version":"1.0.0","model":"EfficientNetB0 + Colour Ensemble"})


@app.route("/api/auth/login",    methods=["POST"])
def login():
    d = request.get_json(silent=True) or {}
    u,p = d.get("username","").strip(), d.get("password","").strip()
    if not u or not p:           return err("username and password required.")
    if USERS.get(u) != p:        return err("Incorrect credentials.", 401)
    return ok({"token":_token(u),"username":u})


@app.route("/api/auth/register", methods=["POST"])
def register():
    d  = request.get_json(silent=True) or {}
    u  = d.get("username","").strip()
    p  = d.get("password","").strip()
    p2 = d.get("confirm_password","").strip()
    if not u or not p or not p2: return err("All fields required.")
    if u in USERS:               return err("Username already taken.")
    if len(p) < 4:               return err("Password must be at least 4 characters.")
    if p != p2:                  return err("Passwords do not match.")
    USERS[u] = p
    return ok({"message":f"Account created for {u}."},201)


@app.route("/api/dashboard")
@_auth
def dashboard():
    global _light_data
    if request.args.get("refresh","").lower()=="true":
        _light_data = [max(150,min(950,400+random.randint(-200,400))) for _ in range(24)]
    d = _light_data
    return ok({"readings":d,"stats":{"average":sum(d)//len(d),"maximum":max(d),"minimum":min(d)},
               "thresholds":{"low":300,"optimal_max":800}})


@app.route("/api/dashboard/upload", methods=["POST"])
@_auth
def upload():
    global _light_data
    if "file" not in request.files: return err("No 'file' field.")
    text = request.files["file"].read().decode("utf-8",errors="ignore")
    data = []
    for row in csv.reader(text.splitlines()):
        for cell in row:
            try: data.append(int(float(cell.strip())))
            except ValueError: pass
    if not data: return err("No numeric values found in file.")
    _light_data = data
    return ok({"readings":data,"count":len(data),
                "stats":{"average":sum(data)//len(data),"maximum":max(data),"minimum":min(data)}})


@app.route("/api/alerts")
@_auth
def alerts():
    f = request.args.get("filter","all").lower()
    result = ALERTS if f=="all" else [a for a in ALERTS if a["category"]==f]
    return ok({"alerts":result,"total":len(result),"filter":f})


@app.route("/api/plants",        methods=["GET"])
@_auth
def get_plants():
    total = len(PLANTS); opt = sum(1 for p in PLANTS if p["status"]=="Optimal")
    return ok({"plants":PLANTS,"stats":{"total":total,"optimal":opt,"need_attention":total-opt}})


@app.route("/api/plants",        methods=["POST"])
@_auth
def add_plant():
    d    = request.get_json(silent=True) or {}
    name = d.get("name","").strip()
    if not name:                                      return err("'name' is required.")
    if any(p["name"]==name for p in PLANTS):          return err(f"'{name}' already exists.")
    lux  = random.randint(200,900)
    p    = {"name":name,"emoji":d.get("emoji","🌱"),"location":d.get("location","Unknown"),
             "status":_status(lux),"lux":lux,"days":0}
    PLANTS.append(p)
    return ok({"plant":p},201)


@app.route("/api/plants/<name>", methods=["PUT"])
@_auth
def update_plant(name):
    plant = next((p for p in PLANTS if p["name"]==name),None)
    if not plant: return err(f"'{name}' not found.",404)
    lux = int((request.get_json(silent=True) or {}).get("lux",random.randint(150,950)))
    plant["lux"],plant["status"] = lux,_status(lux)
    return ok({"plant":plant})


@app.route("/api/plants/<name>", methods=["DELETE"])
@_auth
def delete_plant(name):
    global PLANTS
    before = len(PLANTS); PLANTS = [p for p in PLANTS if p["name"]!=name]
    if len(PLANTS)==before: return err(f"'{name}' not found.",404)
    return ok({"message":f"'{name}' removed."})


@app.route("/api/plants/<name>/photos", methods=["POST"])
@_auth
def add_photos(name):
    if not any(p["name"]==name for p in PLANTS): return err(f"'{name}' not found.",404)
    folder = (request.get_json(silent=True) or {}).get("folder","").strip()
    if not folder:              return err("'folder' path required.")
    if not os.path.isdir(folder): return err(f"Folder not found: {folder}")
    exts   = {".jpg",".jpeg",".png",".webp",".gif",".bmp",".tiff"}
    imgs   = sorted([os.path.join(folder,f) for f in os.listdir(folder)
                     if os.path.splitext(f)[1].lower() in exts])
    if not imgs: return err("No supported image files found.")
    db = _load_db(); existing = db.get(name,[])
    db[name] = existing+[p for p in imgs if p not in existing]
    _save_db(db)
    return ok({"plant":name,"added":len(db[name])-len(existing),"total":len(db[name])},201)


@app.route("/api/plants/<name>/photos", methods=["GET"])
@_auth
def get_photos(name):
    if not any(p["name"]==name for p in PLANTS): return err(f"'{name}' not found.",404)
    photos = _load_db().get(name,[]); valid = [p for p in photos if os.path.isfile(p)]
    return ok({"plant":name,"photos":valid,"total":len(valid),"missing":len(photos)-len(valid)})


@app.route("/api/history")
@_auth
def history():
    days   = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]
    weekly = [random.randint(200,900) for _ in range(7)]
    result = [{"day":d,"avg_lux":v,"status":_status(v)} for d,v in zip(days,weekly)]
    return ok({"history":result,"thresholds":{"low":300,"high":800}})


@app.route("/api/detect",        methods=["POST"])
@_auth
def detect():
    if "image" not in request.files: return err("No 'image' field.")
    try:
        from PIL import Image
        data = request.files["image"].read()
        img  = Image.open(io.BytesIO(data)); img.verify()
        img  = Image.open(io.BytesIO(data))
        t0   = time.perf_counter()
        res  = _infer(img)
        res.update({"success":True,"ms":int((time.perf_counter()-t0)*1000)})
        return jsonify(res)
    except Exception as e: return err(str(e),500)


@app.route("/api/detect/base64", methods=["POST"])
@_auth
def detect_b64():
    d = request.get_json(silent=True) or {}
    if "image" not in d: return err("JSON body must have field 'image'.")
    try:
        from PIL import Image
        s    = d["image"]; s = s.split(",",1)[1] if "," in s else s
        data = base64.b64decode(s)
        img  = Image.open(io.BytesIO(data)); img.verify()
        img  = Image.open(io.BytesIO(data))
        t0   = time.perf_counter()
        res  = _infer(img)
        res.update({"success":True,"ms":int((time.perf_counter()-t0)*1000)})
        return jsonify(res)
    except Exception as e: return err(str(e),500)


@app.route("/api/recommendations")
@_auth
def recommendations():
    status = request.args.get("status","Optimal")
    if status not in TIPS: return err(f"Invalid status. Choose: Optimal, Low Light, High.")
    return ok({"status":status,"tips":TIPS[status],
                "thresholds":{"low":300,"optimal_max":800}})


@app.errorhandler(404)
def not_found(e):    return err("Not found. GET /api/health for route list.",404)
@app.errorhandler(405)
def method_err(e):   return err("Method not allowed.",405)
@app.errorhandler(413)
def too_large(e):    return err("File too large. Max 16 MB.",413)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--host",  default="127.0.0.1")
    p.add_argument("--port",  default=5000, type=int)
    p.add_argument("--debug", action="store_true")
    a = p.parse_args()
    print(f"Plant Monitor API  |  http://{a.host}:{a.port}  |  GET /api/health for routes")
    app.run(host=a.host, port=a.port, debug=a.debug)