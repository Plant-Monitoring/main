import tkinter as tk

from .theme import (
    BG_MAIN, BG_CARD, BG_CARD2, BG_GLASS, ACCENT, ACCENT2, BLUE, RED, YELLOW, TEXT_PRI,
    TEXT_SEC, TEXT_MUT, BORDER, ON_ACCENT, bind_tree, hover, GreenSlider, BasePage
)
from database.plants import df_plants as _df_plants, PANDAS_OK
from models.recommendation import recommend_plants


class RecommendationSystemPage(BasePage):
    def _build(self):
        outer = tk.Frame(self, bg=BG_MAIN)
        outer.pack(fill="both", expand=True, padx=22, pady=18)

        tk.Label(outer, text="Plant Recommendation", font=("Segoe UI",16,"bold"),
                 bg=BG_MAIN, fg=TEXT_PRI).pack(anchor="w")
        icon_lbl = tk.Label(outer, text="💡", font=("Segoe UI",16), bg=BG_MAIN)
        icon_lbl.pack(anchor="w")
        tk.Label(outer, text="Find the perfect plant using fuzzy matching across care requirements.",
                 font=self.f_small, bg=BG_MAIN, fg=TEXT_SEC).pack(anchor="w", pady=(0,16))

        if not PANDAS_OK:
            tk.Label(outer, text="pandas is required.\nRun: pip install pandas",
                     font=self.f_body, bg=BG_MAIN, fg=RED).pack(pady=40); return

        cols = tk.Frame(outer, bg=BG_MAIN)
        cols.pack(fill="both", expand=True)

        left = tk.Frame(cols, bg=BG_CARD, width=330, padx=0, pady=0)
        left.pack(side="left", fill="y", padx=(0,14))
        left.pack_propagate(False)
        tk.Frame(left, bg=ACCENT, height=3).pack(fill="x")
        left_inner = tk.Frame(left, bg=BG_CARD, padx=18, pady=16)
        left_inner.pack(fill="both", expand=True)

        tk.Label(left_inner, text="Your Preferences", font=self.f_title,
                 bg=BG_CARD, fg=TEXT_PRI).pack(anchor="w", pady=(0,14))

        def slider_row(parent, label, from_, to, resolution, default):
            row = tk.Frame(parent, bg=BG_CARD)
            row.pack(fill="x", pady=(0,12))
            header = tk.Frame(row, bg=BG_CARD); header.pack(fill="x")
            tk.Label(header, text=label, font=self.f_small, bg=BG_CARD, fg=TEXT_SEC).pack(side="left")
            val_var = tk.DoubleVar(value=default)
            val_lbl = tk.Label(header, textvariable=val_var, font=("Segoe UI",9,"bold"),
                               bg=BG_CARD, fg=ACCENT, width=5)
            val_lbl.pack(side="right")
            scale_frame = tk.Frame(row, bg=BG_CARD); scale_frame.pack(fill="x", pady=(4,0))
            scale = GreenSlider(scale_frame, from_=from_, to=to,
                                variable=val_var, resolution=resolution, length=260)
            scale.pack(fill="x")
            minmax = tk.Frame(row, bg=BG_CARD); minmax.pack(fill="x")
            tk.Label(minmax, text=str(from_), font=("Segoe UI",7), bg=BG_CARD, fg=TEXT_MUT).pack(side="left")
            tk.Label(minmax, text=str(to),   font=("Segoe UI",7), bg=BG_CARD, fg=TEXT_MUT).pack(side="right")
            return val_var

        self._water_var    = slider_row(left_inner, "Water needs (1–10)", 1, 10, 0.5, 5)
        self._sunlight_var = slider_row(left_inner, "Sunlight (1–10)",    1, 10, 0.5, 6)
        self._temp_var     = slider_row(left_inner, "Temperature (°C)",  10, 40, 0.5, 22)

        tk.Frame(left_inner, bg=BORDER, height=1).pack(fill="x", pady=(8,10))

        # Space selector
        space_row_outer = tk.Frame(left_inner, bg=BG_CARD)
        space_row_outer.pack(fill="x", pady=(0,10))
        tk.Label(space_row_outer, text="Space", font=self.f_small, bg=BG_CARD, fg=TEXT_SEC).pack(anchor="w", pady=(0,6))
        self._space_var = tk.StringVar(value="any")
        space_btn_row   = tk.Frame(space_row_outer, bg=BG_CARD)
        space_btn_row.pack(fill="x")
        self._space_btns = {}
        for val, label in [("any","Any"),("flat","Flat"),("garden","Garden")]:
            is_active = (val == "any")
            btn = tk.Frame(space_btn_row, bg=ACCENT if is_active else BG_GLASS,
                           cursor="hand2", padx=14, pady=5)
            btn.pack(side="left", padx=(0,6))
            lbl = tk.Label(btn, text=label, font=self.f_small,
                           bg=ACCENT if is_active else BG_GLASS,
                           fg=ON_ACCENT if is_active else TEXT_SEC)
            lbl.pack()
            self._space_btns[val] = (btn, lbl)
            def on_space(e, v=val):
                self._space_var.set(v)
                for k,(b,l) in self._space_btns.items():
                    active = (k==v)
                    b.configure(bg=ACCENT if active else BG_GLASS)
                    l.configure(bg=ACCENT if active else BG_GLASS,
                                fg=ON_ACCENT if active else TEXT_SEC)
            bind_tree(btn, "<Button-1>", on_space)

        # Toggles
        toggles_row = tk.Frame(left_inner, bg=BG_CARD)
        toggles_row.pack(fill="x", pady=(0,10))
        self._pet_var = tk.BooleanVar(value=False)
        self._allergy_var = tk.BooleanVar(value=False)

        def toggle_row_widget(parent, label, var):
            row = tk.Frame(parent, bg=BG_CARD); row.pack(fill="x", pady=(0,6))
            tk.Label(row, text=label, font=self.f_small, bg=BG_CARD, fg=TEXT_SEC).pack(side="left")
            lbl = tk.Label(row, text="  OFF", font=self.f_small, bg=BG_GLASS,
                           fg=TEXT_MUT, padx=10, pady=4, cursor="hand2")
            lbl.pack(side="right")
            def toggle(e, v=var, l=lbl):
                v.set(not v.get())
                l.config(text="ON  " if v.get() else "  OFF",
                         fg=ACCENT if v.get() else TEXT_MUT,
                         bg=BG_CARD2 if v.get() else BG_GLASS)
            lbl.bind("<Button-1>", toggle)

        toggle_row_widget(toggles_row, "Pet safe only",       self._pet_var)
        toggle_row_widget(toggles_row, "No pollen allergies", self._allergy_var)

        tk.Frame(left_inner, bg=BORDER, height=1).pack(fill="x", pady=(4,10))

        tk.Label(left_inner, text="Existing plants (comma separated)",
                 font=self.f_small, bg=BG_CARD, fg=TEXT_SEC).pack(anchor="w", pady=(0,4))
        self._existing_var = tk.StringVar()
        existing_frame = tk.Frame(left_inner, bg=BG_GLASS)
        existing_frame.pack(fill="x")
        tk.Frame(existing_frame, bg=ACCENT, width=3).pack(side="left", fill="y")
        existing_entry = tk.Entry(existing_frame, textvariable=self._existing_var,
                                  bg=BG_GLASS, fg=TEXT_PRI, insertbackground=ACCENT,
                                  relief="flat", font=("Segoe UI",9))
        existing_entry.pack(side="left", fill="x", expand=True, ipady=7, padx=(8,8))

        find_btn = tk.Frame(left_inner, bg=ACCENT, cursor="hand2")
        find_btn.pack(fill="x", pady=(14,0))
        tk.Label(find_btn, text="Find Plants", font=("Segoe UI",10,"bold"),
                 bg=ACCENT, fg=ON_ACCENT, pady=10).pack()
        bind_tree(find_btn, "<Button-1>", lambda e: self._run_search())
        hover(find_btn, ACCENT, ACCENT2)

        right = tk.Frame(cols, bg=BG_MAIN)
        right.pack(side="left", fill="both", expand=True)
        tk.Label(right, text="Top Matches", font=self.f_title,
                 bg=BG_MAIN, fg=TEXT_PRI).pack(anchor="w", pady=(0,10))
        self._results_frame = tk.Frame(right, bg=BG_MAIN)
        self._results_frame.pack(fill="both", expand=True)
        self._show_finder_empty()

    def _show_finder_empty(self):
        for w in self._results_frame.winfo_children(): w.destroy()
        container = tk.Frame(self._results_frame, bg=BG_CARD, padx=20, pady=40)
        container.pack(fill="both", expand=True)
        tk.Frame(container, bg=ACCENT, height=3).pack(fill="x", pady=(0,20))
        tk.Label(container, text="🌱", font=("Segoe UI",40), bg=BG_CARD).pack(pady=(0,8))
        tk.Label(container, text="Set your preferences and click Find Plants.",
                 font=self.f_body, bg=BG_CARD, fg=TEXT_SEC, justify="center").pack()

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

        try: results = recommend_plants(user_prefs, top_n=5)
        except Exception as ex:
            tk.Label(self._results_frame, text=f"Error: {ex}", font=self.f_body, bg=BG_MAIN, fg=RED).pack(pady=20); return

        if not results:
            container = tk.Frame(self._results_frame, bg=BG_CARD, padx=20, pady=30)
            container.pack(fill="both", expand=True)
            tk.Label(container, text="No plants matched your criteria.",
                     font=self.f_body, bg=BG_CARD, fg=TEXT_SEC).pack(pady=20)
            return

        plant_emojis = {
            "Monstera":"🌿","Snake plant":"🪴","Peace lily":"*","Spider plant":"*",
            "Aloe vera":"*","Fiddle leaf fig":"*","Pothos":"*","ZZ plant":"*",
            "Boston fern":"🌿","English ivy":"*","Lavender":"*","Rosemary":"🌱",
            "Basil":"🌿","Orchid":"*","Cactus":"*","Succulent":"*",
            "Rubber plant":"🌳","Dracaena":"*","Philodendron":"*","Calathea":"*",
            "Jade plant":"*","Chinese money plant":"*","Bird of paradise":"*",
            "Anthurium":"*","Peperomia":"*","Prayer plant":"*","Tradescantia":"*",
            "String of pearls":"*","String of hearts":"*","Hoya":"*",
            "Parlour palm":"*","Areca palm":"*","Money tree":"*","African violet":"*",
            "Bromeliad":"*","Air plant":"*","Yucca":"*","Bird's nest fern":"*",
            "Maidenhair fern":"🌿","Dieffenbachia":"🌿","Mint":"🍃","Thyme":"🌿",
            "Sage":"🌿","Parsley":"🌿","Chives":"🌿","Lemon balm":"*","Sunflower":"*",
            "Marigold":"*","Geranium":"*","Begonia":"*","Rose":"*","Pansy":"*",
            "Primrose":"*","Cyclamen":"*","Cast iron plant":"🪴","Nerve plant":"🌿",
            "Umbrella plant":"*","Weeping fig":"🌿","Croton":"*","Bamboo palm":"*",
        }
        medal_colors = [ACCENT, BLUE, YELLOW, TEXT_SEC, TEXT_SEC]

        res_canvas = tk.Canvas(self._results_frame, bg=BG_MAIN, highlightthickness=0)
        sb = tk.Scrollbar(self._results_frame, orient="vertical", command=res_canvas.yview)
        res_canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        res_canvas.pack(side="left", fill="both", expand=True)
        scroll_frame = tk.Frame(res_canvas, bg=BG_MAIN)
        win_id = res_canvas.create_window((0,0), window=scroll_frame, anchor="nw")
        scroll_frame.bind("<Configure>", lambda e: res_canvas.configure(scrollregion=res_canvas.bbox("all")))
        res_canvas.bind("<Configure>", lambda e: res_canvas.itemconfig(win_id, width=e.width))

        for rank, (name, score) in enumerate(results, 1):
            pct   = int(score*100)
            emoji = plant_emojis.get(name, "🌱")
            mc    = medal_colors[rank-1]

            card = tk.Frame(scroll_frame, bg=BG_CARD, padx=0, pady=0)
            card.pack(fill="x", pady=(0,10))
            tk.Frame(card, bg=mc, height=3).pack(fill="x")
            inner = tk.Frame(card, bg=BG_CARD, padx=16, pady=12)
            inner.pack(fill="both")

            top = tk.Frame(inner, bg=BG_CARD); top.pack(fill="x")
            left_info = tk.Frame(top, bg=BG_CARD); left_info.pack(side="left", fill="both", expand=True)

            rank_row = tk.Frame(left_info, bg=BG_CARD); rank_row.pack(anchor="w")
            tk.Label(rank_row, text=f" {rank} ", font=("Segoe UI",9,"bold"),
                     bg=mc, fg=ON_ACCENT, padx=4, pady=1).pack(side="left", padx=(0,6))
            tk.Label(rank_row, text=emoji, font=("Segoe UI",13), bg=BG_CARD).pack(side="left", padx=(0,4))
            tk.Label(rank_row, text=name, font=self.f_title, bg=BG_CARD, fg=TEXT_PRI).pack(side="left")

            score_lbl = tk.Label(top, text=f"{pct}%", font=("Segoe UI",20,"bold"),
                                 bg=BG_CARD, fg=mc)
            score_lbl.pack(side="right", padx=(12,0))

            bar_row = tk.Frame(inner, bg=BG_CARD); bar_row.pack(fill="x", pady=(8,4))
            bar_bg  = tk.Frame(bar_row, bg=BG_GLASS, height=6); bar_bg.pack(fill="x")
            bar_bg.update_idletasks()
            bw = bar_bg.winfo_width() or 300
            tk.Frame(bar_bg, bg=mc, width=max(4, int(bw*score)), height=6).place(x=0,y=0)

            try:
                plant_row = _df_plants[_df_plants["name"]==name].iloc[0]
                tags = []
                if plant_row["pet_safe"]:        tags.append(("Pet safe", ACCENT))
                if not plant_row["pollen_allergies"]: tags.append(("Low pollen", BLUE))
                tags.append((f"Water {int(plant_row['water'])}/10",    TEXT_SEC))
                tags.append((f"Light {int(plant_row['sunlight'])}/10", TEXT_SEC))
                tags.append((f"{int(plant_row['temperature'])}C",      TEXT_SEC))
                tags.append((plant_row["space"].capitalize(),          TEXT_MUT))
                tag_row = tk.Frame(inner, bg=BG_CARD); tag_row.pack(anchor="w", pady=(2,0))
                for tag_text, tag_color in tags:
                    tk.Label(tag_row, text=tag_text, font=("Segoe UI",7),
                             bg=BG_GLASS, fg=tag_color, padx=6, pady=2).pack(side="left", padx=(0,4))
            except: pass