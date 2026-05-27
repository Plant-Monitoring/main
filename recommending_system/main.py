import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
import numpy as np
from io import StringIO
import threading

# FastAPI imports
from fastapi import FastAPI
from pydantic import BaseModel, Field
from typing import Optional, List
import uvicorn
from fastapi.responses import RedirectResponse

# -------------------------------
# 1. Load plant data
# -------------------------------
try:
    df_plants = pd.read_csv("plants.csv")
    df_plants["existing_plants"] = df_plants["existing_plants"].apply(
        lambda x: [p.strip() for p in x.split(",") if p.strip()] if isinstance(x, str) else []
    )
except FileNotFoundError:
    sample_data = """name,pet_safe,space,water,sunlight,temperature,pollen_allergies,existing_plants
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
Lavender,True,garden,3,10,22,False,"Rosemary"
Rosemary,True,garden,4,10,22,False,"Lavender"
Basil,True,garden,6,8,25,False,""
Orchid,True,flat,5,6,24,False,""
Cactus,True,flat,1,10,30,False,"Aloe vera,Succulent"
Succulent,True,flat,2,9,28,False,"Cactus,Aloe vera"
Rubber plant,False,flat,6,7,24,False,""
Dracaena,False,flat,5,6,23,False,""
Philodendron,False,flat,6,5,22,False,"Monstera,Pothos"
Calathea,True,flat,7,4,22,False,"Peace lily,Boston fern"
"""
    df_plants = pd.read_csv(StringIO(sample_data))
    df_plants["existing_plants"] = df_plants["existing_plants"].apply(
        lambda x: [p.strip() for p in x.split(",") if p.strip()] if isinstance(x, str) else []
    )

# -------------------------------
# 2. Fuzzy matching functions
# -------------------------------
def triangular_membership(x, center, spread):
    if spread <= 0:
        return 1.0 if x == center else 0.0
    return max(0.0, 1.0 - abs(x - center) / spread)

def fuzzy_match(user_val, plant_val, spread):
    return triangular_membership(plant_val, user_val, spread)

# -------------------------------
# 3. Recommendation engine
# -------------------------------
def recommend_plants(user_prefs, top_n=5):
    WATER_SPREAD = 2.0
    SUNLIGHT_SPREAD = 2.0
    TEMP_SPREAD = 4.0

    scores = []
    for _, plant in df_plants.iterrows():
        w_match = fuzzy_match(user_prefs["water"], plant["water"], WATER_SPREAD)
        s_match = fuzzy_match(user_prefs["sunlight"], plant["sunlight"], SUNLIGHT_SPREAD)
        t_match = fuzzy_match(user_prefs["temp"], plant["temperature"], TEMP_SPREAD)

        if user_prefs["pet_safe"] is not None:
            p_match = 1.0 if plant["pet_safe"] == user_prefs["pet_safe"] else 0.0
        else:
            p_match = None

        if user_prefs["space"] is not None:
            space_match = 1.0 if plant["space"] == user_prefs["space"] else 0.0
        else:
            space_match = None

        if user_prefs["allergy_concern"] is not None:
            if user_prefs["allergy_concern"]:
                a_match = 1.0 if not plant["pollen_allergies"] else 0.0
            else:
                a_match = 1.0
        else:
            a_match = None

        user_existing = user_prefs.get("existing_plants", [])
        if user_existing:
            plant_compat_list = plant["existing_plants"]
            if plant_compat_list:
                exist_match = sum(1 for up in user_existing if up in plant_compat_list) / len(user_existing)
            else:
                exist_match = 0.0
        else:
            exist_match = None

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
        active = {k: v for k, v in components.items() if v is not None}
        if not active:
            continue
        active_weight_sum = sum(weights[k] for k in active)
        score = sum(v * weights[k] / active_weight_sum for k, v in active.items())
        scores.append((plant["name"], score))

    scores.sort(key=lambda x: x[1], reverse=True)
    return scores[:top_n]

# -------------------------------
# 4. Pydantic models for FastAPI
# -------------------------------
class UserPreferences(BaseModel):
    water: float = Field(..., ge=1, le=10, description="Desired watering level (1-10)")
    sunlight: float = Field(..., ge=1, le=10, description="Desired sunlight level (1-10)")
    temp: float = Field(..., ge=10, le=40, description="Desired temperature in °C")
    pet_safe: Optional[bool] = Field(None, description="Filter for pet-safe plants (True/False)")
    space: Optional[str] = Field(None, description="Space type: 'flat' or 'garden'")
    allergy_concern: Optional[bool] = Field(None, description="Filter out plants with pollen allergies")
    existing_plants: List[str] = Field(default=[], description="List of existing plant names")

class PlantRecommendation(BaseModel):
    name: str
    pet_safe: bool
    space: str
    water: int
    sunlight: int
    temperature: int
    pollen_allergies: bool
    existing_plants: List[str]
    score: float

# -------------------------------
# 5. FastAPI application
# -------------------------------
app = FastAPI(title="Plant Recommendation System")

@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/docs")

@app.get("/recommend", include_in_schema=False)
def recommend_get_help():
    return {"message": "This endpoint requires a POST request with JSON body. Please use /docs or send a POST request."}

@app.post("/recommend", response_model=List[PlantRecommendation])
def get_recommendations(prefs: UserPreferences):
    user_dict = prefs.dict()
    results = recommend_plants(user_dict, top_n=5)

    output = []
    for plant_name, score in results:
        plant_row = df_plants[df_plants["name"] == plant_name].iloc[0]
        output.append(PlantRecommendation(
            name=plant_name,
            pet_safe=bool(plant_row["pet_safe"]),
            space=plant_row["space"],
            water=int(plant_row["water"]),
            sunlight=int(plant_row["sunlight"]),
            temperature=int(plant_row["temperature"]),
            pollen_allergies=bool(plant_row["pollen_allergies"]),
            existing_plants=plant_row["existing_plants"],
            score=round(score, 4)
        ))
    return output

# -------------------------------
# 6. GUI Application
# -------------------------------
class PlantRecommenderApp:
    def __init__(self, root):
        self.root = root
        root.title("Plant Recommendation System")
        root.geometry("550x600")
        root.resizable(False, False)

        pad_x = 10
        pad_y = 5

        # ----- Water Scale -----
        tk.Label(root, text="Desired Water (1-10)").grid(row=0, column=0, sticky="w", padx=pad_x, pady=pad_y)
        self.water_var = tk.DoubleVar(value=5)
        self.water_scale = tk.Scale(root, from_=1, to=10, resolution=0.5, orient=tk.HORIZONTAL,
                                    variable=self.water_var, length=200)
        self.water_scale.grid(row=0, column=1, sticky="we", padx=pad_x, pady=pad_y)

        # ----- Sunlight Scale -----
        tk.Label(root, text="Desired Sunlight (1-10)").grid(row=1, column=0, sticky="w", padx=pad_x, pady=pad_y)
        self.sunlight_var = tk.DoubleVar(value=6)
        self.sunlight_scale = tk.Scale(root, from_=1, to=10, resolution=0.5, orient=tk.HORIZONTAL,
                                       variable=self.sunlight_var, length=200)
        self.sunlight_scale.grid(row=1, column=1, sticky="we", padx=pad_x, pady=pad_y)

        # ----- Temperature Scale -----
        tk.Label(root, text="Desired Temperature (°C)").grid(row=2, column=0, sticky="w", padx=pad_x, pady=pad_y)
        self.temp_var = tk.DoubleVar(value=22)
        self.temp_scale = tk.Scale(root, from_=10, to=40, resolution=0.5, orient=tk.HORIZONTAL,
                                   variable=self.temp_var, length=200)
        self.temp_scale.grid(row=2, column=1, sticky="we", padx=pad_x, pady=pad_y)

        # ----- Space Type Radio -----
        tk.Label(root, text="Available Space").grid(row=3, column=0, sticky="w", padx=pad_x, pady=pad_y)
        self.space_var = tk.StringVar(value="any")
        space_frame = tk.Frame(root)
        space_frame.grid(row=3, column=1, sticky="w", padx=pad_x, pady=pad_y)
        tk.Radiobutton(space_frame, text="Garden", variable=self.space_var, value="garden").pack(side=tk.LEFT)
        tk.Radiobutton(space_frame, text="Flat", variable=self.space_var, value="flat").pack(side=tk.LEFT)
        tk.Radiobutton(space_frame, text="Any", variable=self.space_var, value="any").pack(side=tk.LEFT)

        # ----- Pet Safe Checkbox -----
        tk.Label(root, text="Pet Safety").grid(row=4, column=0, sticky="w", padx=pad_x, pady=pad_y)
        self.pet_var = tk.BooleanVar(value=False)
        tk.Checkbutton(root, text="Must be safe for pets", variable=self.pet_var).grid(row=4, column=1, sticky="w", padx=pad_x, pady=pad_y)

        # ----- Allergy Concern Checkbox -----
        tk.Label(root, text="Allergy Concern").grid(row=5, column=0, sticky="w", padx=pad_x, pady=pad_y)
        self.allergy_var = tk.BooleanVar(value=False)
        tk.Checkbutton(root, text="I have pollen allergies", variable=self.allergy_var).grid(row=5, column=1, sticky="w", padx=pad_x, pady=pad_y)

        # ----- Existing Plants Entry -----
        tk.Label(root, text="Existing Plants (comma separated)").grid(row=6, column=0, sticky="w", padx=pad_x, pady=pad_y)
        self.existing_var = tk.StringVar()
        tk.Entry(root, textvariable=self.existing_var, width=30).grid(row=6, column=1, sticky="we", padx=pad_x, pady=pad_y)

        # ----- Get Recommendations Button -----
        tk.Button(root, text="Get Recommendations", command=self.show_recommendations,
                  bg="#4CAF50", fg="white", font=("Arial", 10, "bold")).grid(
                      row=7, column=0, columnspan=2, pady=20)

        # ----- Results Listbox -----
        tk.Label(root, text="Top 5 Recommendations:").grid(row=8, column=0, sticky="w", padx=pad_x, pady=(10,0))
        self.results_listbox = tk.Listbox(root, width=50, height=6, font=("Courier", 10))
        self.results_listbox.grid(row=9, column=0, columnspan=2, padx=pad_x, pady=pad_y, sticky="nsew")

        scrollbar = tk.Scrollbar(root, orient=tk.VERTICAL, command=self.results_listbox.yview)
        scrollbar.grid(row=9, column=2, sticky="ns")
        self.results_listbox.config(yscrollcommand=scrollbar.set)

        root.grid_rowconfigure(9, weight=1)
        root.grid_columnconfigure(1, weight=1)

    def show_recommendations(self):
        user_prefs = {
            "water": self.water_var.get(),
            "sunlight": self.sunlight_var.get(),
            "temp": self.temp_var.get(),
            "pet_safe": True if self.pet_var.get() else None,
            "space": self.space_var.get() if self.space_var.get() != "any" else None,
            "allergy_concern": True if self.allergy_var.get() else None,
        }
        raw = self.existing_var.get().strip()
        existing = [p.strip() for p in raw.split(",") if p.strip()] if raw else []
        user_prefs["existing_plants"] = existing

        try:
            results = recommend_plants(user_prefs, top_n=5)
            self.results_listbox.delete(0, tk.END)
            if not results:
                self.results_listbox.insert(tk.END, "No plants match your criteria.")
            else:
                for rank, (name, score) in enumerate(results, 1):
                    self.results_listbox.insert(tk.END, f"{rank}. {name} ({score:.3f})")
        except Exception as e:
            messagebox.showerror("Error", str(e))

# -------------------------------
# 7. Launch both API and GUI
# -------------------------------
def start_api():
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")

def start_gui():
    try:
        root = tk.Tk()
        app_gui = PlantRecommenderApp(root)
        root.mainloop()
    except Exception as e:
        print(f"GUI failed to start: {e}")
        # Keep the process alive so the API still works
        import time
        while True:
            time.sleep(3600)

if __name__ == "__main__":
    # Start FastAPI in a NON‑daemon thread so it keeps the container running
    api_thread = threading.Thread(target=start_api)
    api_thread.start()

    # Start GUI in the main thread (or fallback if it fails)
    start_gui()