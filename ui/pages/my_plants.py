import os
import json
import random
import tkinter as tk
from tkinter import simpledialog, messagebox, filedialog

from .theme import *

_IMG_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp", ".tiff"}
SAMPLE_PLANTS = [
    {"name": "Calibrachoa", "emoji": "🌸", "location": "Garden", "status": "Optimal", "lux": 720, "days": 1},
]
STATUS_COLOR = {"Optimal": ACCENT, "Low Light": RED, "Too Much Light": YELLOW}
CALIBRACHOA_FOLDER = "/home/anastasija/Desktop/FERI/2 semester/pp/projekt/main/Calibrachoa"

PLANTS_DB_PATH = os.path.join(APP_DIR, "plants_data.json")

def _load_plants_db():
    if os.path.exists(PLANTS_DB_PATH):
        try:
            with open(PLANTS_DB_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except: pass
    return {}

def _save_plants_db(data):
    try:
        with open(PLANTS_DB_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as ex:
        print(f"[Plant DB] Save error: {ex}")

def _init_calibrachoa_images(db):
    if "Calibrachoa" in db: return db
    folder = CALIBRACHOA_FOLDER
    if not os.path.isdir(folder): return db
    images = sorted([os.path.join(folder, f) for f in os.listdir(folder)
                     if os.path.splitext(f)[1].lower() in _IMG_EXTS])
    if images:
        db["Calibrachoa"] = images
        _save_plants_db(db)
    return db

class MyPlantsPage(BasePage):
    THUMB_W = 88
    THUMB_H = 72

    def _build(self):
        self._plants    = [dict(p) for p in SAMPLE_PLANTS]
        self._plants_db = _init_calibrachoa_images(_load_plants_db())
        self._thumb_cache: dict[str,object] = {}
        self._expanded: set[str] = {"Calibrachoa"}

        self._outer = tk.Frame(self, bg=BG_MAIN)
        self._outer.pack(fill="both", expand=True, padx=22, pady=18)

        hdr_row = tk.Frame(self._outer, bg=BG_MAIN)
        hdr_row.pack(fill="x", pady=(0,4))
        tk.Label(hdr_row, text="My Plants", font=("Segoe UI",16,"bold"),
                 bg=BG_MAIN, fg=TEXT_PRI).pack(side="left")
        icon_lbl = tk.Label(hdr_row, text="🪴", font=("Segoe UI",16), bg=BG_MAIN)
        icon_lbl.pack(side="left", padx=(6,0))

        add_btn = tk.Frame(hdr_row, bg=ACCENT, cursor="hand2", padx=14, pady=6)
        add_btn.pack(side="right")
        tk.Label(add_btn, text="+ Add Plant", font=self.f_label, bg=ACCENT, fg=BG_MAIN).pack()
        bind_tree(add_btn, "<Button-1>", lambda e: self._add_plant())
        hover(add_btn, ACCENT, ACCENT2)

        tk.Label(self._outer, text="Manage your plants. Click the photo section to expand the gallery.",
                 font=self.f_small, bg=BG_MAIN, fg=TEXT_SEC).pack(anchor="w", pady=(0,12))

        self._stats_frame = tk.Frame(self._outer, bg=BG_MAIN)
        self._stats_frame.pack(fill="x", pady=(0,14))

        list_outer = tk.Frame(self._outer, bg=BG_MAIN)
        list_outer.pack(fill="both", expand=True)
        self._list_canvas = tk.Canvas(list_outer, bg=BG_MAIN, highlightthickness=0)
        scrollbar = tk.Scrollbar(list_outer, orient="vertical", command=self._list_canvas.yview)
        self._list_canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self._list_canvas.pack(side="left", fill="both", expand=True)
        self._list_frame = tk.Frame(self._list_canvas, bg=BG_MAIN)
        self._list_canvas_window = self._list_canvas.create_window((0,0), window=self._list_frame, anchor="nw")
        self._list_frame.bind("<Configure>",
            lambda e: self._list_canvas.configure(scrollregion=self._list_canvas.bbox("all")))
        self._list_canvas.bind("<Configure>",
            lambda e: self._list_canvas.itemconfig(self._list_canvas_window, width=e.width))
        self._list_canvas.bind("<MouseWheel>",
            lambda e: self._list_canvas.yview_scroll(-1*(e.delta//120),"units"))
        self._render_all()

    def _render_all(self):
        self._render_stats()
        self._render_plant_list()

    def _render_stats(self):
        for w in self._stats_frame.winfo_children(): w.destroy()
        total   = len(self._plants)
        optimal = sum(1 for p in self._plants if p["status"] == "Optimal")
        alerts  = total - optimal
        for label, val, color, icon in [
            ("Total Plants", total, BLUE,  "🪴"),
            ("Optimal",      optimal, ACCENT, "✓"),
            ("Needs Attention", alerts, RED, "!")
        ]:
            sc = tk.Frame(self._stats_frame, bg=BG_CARD, padx=0, pady=0)
            sc.pack(side="left", padx=(0,10))
            tk.Frame(sc, bg=color, height=3).pack(fill="x")
            inner = tk.Frame(sc, bg=BG_CARD, padx=18, pady=10)
            inner.pack()
            val_row = tk.Frame(inner, bg=BG_CARD)
            val_row.pack()
            tk.Label(val_row, text=str(val), font=("Segoe UI",22,"bold"), bg=BG_CARD, fg=color).pack(side="left")
            tk.Label(inner, text=label, font=self.f_small, bg=BG_CARD, fg=TEXT_SEC).pack()

    def _render_plant_list(self):
        for w in self._list_frame.winfo_children(): w.destroy()
        if not self._plants:
            tk.Label(self._list_frame, text="No plants yet. Click '+ Add Plant' above.",
                     font=self.f_body, bg=BG_MAIN, fg=TEXT_SEC).pack(pady=30)
            return
        for plant in self._plants:
            self._render_plant_card(plant)

    def _render_plant_card(self, plant):
        name = plant["name"]
        sc   = STATUS_COLOR.get(plant["status"], TEXT_SEC)

        card = tk.Frame(self._list_frame, bg=BG_CARD, padx=0, pady=0)
        card.pack(fill="x", pady=(0,10))
        status_bar = tk.Frame(card, bg=sc, width=4)
        status_bar.pack(side="left", fill="y")

        inner = tk.Frame(card, bg=BG_CARD, padx=14, pady=12)
        inner.pack(side="left", fill="both", expand=True)

        top = tk.Frame(inner, bg=BG_CARD)
        top.pack(fill="x")

        left = tk.Frame(top, bg=BG_CARD)
        left.pack(side="left", fill="y")
        tk.Label(left, text=plant["emoji"], font=("Segoe UI",22), bg=BG_CARD).pack(side="left", padx=(0,12))
        info = tk.Frame(left, bg=BG_CARD)
        info.pack(side="left")
        tk.Label(info, text=name, font=self.f_label, bg=BG_CARD, fg=TEXT_PRI).pack(anchor="w")
        tk.Label(info, text=f"📍 {plant['location']}", font=self.f_small, bg=BG_CARD, fg=TEXT_SEC).pack(anchor="w")
        tk.Label(info, text=f"Added {plant['days']} day(s) ago",
                 font=self.f_small, bg=BG_CARD, fg=TEXT_MUT).pack(anchor="w")

        right = tk.Frame(top, bg=BG_CARD)
        right.pack(side="right", fill="y")
        tk.Label(right, text=f"{plant['lux']} lux",
                 font=("Segoe UI",14,"bold"), bg=BG_CARD, fg=sc).pack(anchor="e")
        tk.Label(right, text=plant["status"], font=("Segoe UI",7,"bold"),
                 bg=BG_GLASS, fg=sc, padx=8, pady=3).pack(anchor="e", pady=(2,8))
        btn_row = tk.Frame(right, bg=BG_CARD)
        btn_row.pack(anchor="e")
        sim_btn = tk.Label(btn_row, text="↻ New Reading", font=self.f_small,
                           bg=BG_GLASS, fg=BLUE, padx=8, pady=3, cursor="hand2")
        sim_btn.pack(side="left", padx=(0,6))
        sim_btn.bind("<Button-1>", lambda e, p=plant: self._simulate_reading(p))
        rm_btn = tk.Label(btn_row, text="✕ Remove", font=self.f_small,
                          bg=BG_GLASS, fg=RED, padx=8, pady=3, cursor="hand2")
        rm_btn.pack(side="left")
        rm_btn.bind("<Button-1>", lambda e, p=plant: self._remove_plant(p))

        photos   = self._plants_db.get(name, [])
        n_photos = len([p for p in photos if os.path.isfile(p)])
        gallery_label = f"Photos  ({n_photos})" if n_photos else "Add Photos"
        is_expanded   = name in self._expanded

        toggle_row = tk.Frame(inner, bg=BG_CARD)
        toggle_row.pack(fill="x", pady=(10,0))
        tk.Frame(toggle_row, bg=BORDER, height=1).pack(fill="x", pady=(0,8))

        tgl_container = tk.Frame(toggle_row, bg=BG_GLASS)
        tgl_container.pack(fill="x")
        toggle_btn = tk.Label(tgl_container,
                              text=f"{'▼' if is_expanded else '▶'}  📷  {gallery_label}",
                              font=self.f_small, bg=BG_GLASS, fg=ACCENT, padx=10, pady=5, cursor="hand2")
        toggle_btn.pack(side="left")
        add_folder_btn = tk.Label(tgl_container, text="  + Folder",
                                  font=self.f_small, bg=BG_GLASS, fg=BLUE, padx=8, pady=5, cursor="hand2")
        add_folder_btn.pack(side="left", padx=(4,0))
        add_folder_btn.bind("<Button-1>", lambda e, n=name: self._add_photo_folder(n))

        gallery_frame = tk.Frame(inner, bg=BG_CARD)
        if is_expanded:
            gallery_frame.pack(fill="x", pady=(6,0))
            self._render_plant_gallery(gallery_frame, name)

        def on_toggle(e, n=name, gf=gallery_frame):
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
        self._expanded.add(plant_name)
        self._render_all()

    def _render_plant_gallery(self, parent, plant_name):
        photos = self._plants_db.get(plant_name, [])
        valid  = [p for p in photos if os.path.isfile(p)]
        if not valid:
            tk.Label(parent, text="No photos yet. Click '+ Folder' to add images.",
                     font=self.f_small, bg=BG_CARD, fg=TEXT_MUT).pack(anchor="w", padx=4, pady=4)
            return
        parent.update_idletasks()
        avail_w = max(parent.winfo_width(), 500)
        cell_w  = self.THUMB_W + 14
        cols    = max(1, avail_w // cell_w)
        try:
            from PIL import Image, ImageTk; pil_ok = True
        except ImportError:
            pil_ok = False
        grid = tk.Frame(parent, bg=BG_CARD)
        grid.pack(fill="x", padx=4, pady=4)
        for idx, path in enumerate(valid):
            col_n = idx % cols; row_n = idx // cols
            cell = tk.Frame(grid, bg=BG_GLASS, padx=3, pady=3, cursor="hand2")
            cell.grid(row=row_n, column=col_n, padx=4, pady=4, sticky="nw")
            if pil_ok:
                if path not in self._thumb_cache:
                    try:
                        img = Image.open(path); img.thumbnail((self.THUMB_W, self.THUMB_H))
                        self._thumb_cache[path] = ImageTk.PhotoImage(img)
                    except: self._thumb_cache[path] = None
                tk_img = self._thumb_cache.get(path)
                if tk_img:
                    lbl_img = tk.Label(cell, image=tk_img, bg=BG_GLASS)
                    lbl_img.pack()
                    lbl_img.bind("<Double-Button-1>", lambda e, p=path: self._open_image(p))
                else:
                    tk.Label(cell, text="?", font=("Segoe UI",16), bg=BG_GLASS, fg=TEXT_MUT, width=6, height=3).pack()
            else:
                tk.Label(cell, text="?", font=("Segoe UI",16), bg=BG_GLASS, fg=TEXT_MUT, width=6, height=3).pack()
            fname = os.path.basename(path)
            short = fname if len(fname) <= 10 else fname[:7]+"..."
            tk.Label(cell, text=short, font=("Segoe UI",7), bg=BG_GLASS, fg=TEXT_MUT).pack()
            hover(cell, BG_GLASS, BG_CARD2)
        missing = len(photos)-len(valid)
        count_txt = f"{len(valid)} photo(s)"
        if missing: count_txt += f"  ({missing} missing)"
        tk.Label(parent, text=count_txt, font=("Segoe UI",7), bg=BG_CARD, fg=TEXT_MUT).pack(anchor="w", padx=4, pady=(0,2))

    def _open_image(self, path):
        try: from PIL import Image, ImageTk
        except ImportError:
            messagebox.showinfo("Preview", f"Install Pillow to enable previews.\n\n{path}"); return
        top = tk.Toplevel(self); top.title(os.path.basename(path)); top.configure(bg=BG_MAIN)
        try:
            img = Image.open(path); img.thumbnail((800,600), Image.LANCZOS)
            tk_img = ImageTk.PhotoImage(img)
            lbl = tk.Label(top, image=tk_img, bg=BG_MAIN); lbl.image = tk_img; lbl.pack(padx=10, pady=10)
            tk.Label(top, text=path, font=("Segoe UI",8), bg=BG_MAIN, fg=TEXT_MUT).pack(pady=(0,8))
        except Exception as ex:
            tk.Label(top, text=f"Unable to open image:\n{ex}", bg=BG_MAIN, fg=RED, font=("Segoe UI",10)).pack(padx=20, pady=20)

    def _add_plant(self):
        name = simpledialog.askstring("Add Plant", "Plant name:")
        if not name: return
        loc  = simpledialog.askstring("Add Plant", "Location (e.g. Living Room):") or "Unknown"
        lux  = random.randint(200, 900)
        status = "Optimal" if 300 <= lux <= 800 else ("Low Light" if lux < 300 else "Too Much Light")
        self._plants.append({"name": name, "emoji": "🌱", "location": loc,
                              "status": status, "lux": lux, "days": 0})
        self._render_all()

    def _remove_plant(self, plant):
        if messagebox.askyesno("Remove Plant", f"Remove '{plant['name']}' from your collection?"):
            self._plants.remove(plant)
            self._expanded.discard(plant["name"])
            self._render_all()

    def _simulate_reading(self, plant):
        lux = random.randint(150, 950)
        plant["lux"]    = lux
        plant["status"] = ("Optimal" if 300 <= lux <= 800 else ("Low Light" if lux < 300 else "Too Much Light"))
        self._render_all()