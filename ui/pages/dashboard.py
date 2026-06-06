import os
import datetime
import threading
import tkinter as tk
from tkinter import messagebox, filedialog

import numpy as np
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from .theme import (
    BG_MAIN, BG_CARD, BG_CARD2, BG_GLASS, ACCENT, ACCENT2, BLUE, BLUE2, RED, PURPLE, TEAL,
    ORANGE, TEXT_PRI, TEXT_SEC, TEXT_MUT, BORDER, ON_ACCENT, bind_tree, hover, BasePage,
    _load_history_db, _save_history_db, _prune_old_entries
)
from models.plant_height import measure_plant_height_color, measure_plant_height_edge

class DashboardPage(BasePage):
    def _build(self):
        self._chart_canvas = None
        self._data = []
        self._file_label_var = tk.StringVar(value="")
        self.avg_var = tk.StringVar(value="—")
        self.max_var = tk.StringVar(value="—")
        self.min_var = tk.StringVar(value="—")

        # Plant-height estimator state
        self._ph_image_path = None
        self._ph_file_var   = tk.StringVar(value="No image selected")
        self._ph_result_var = tk.StringVar(value="")
        self._ph_pot_var    = tk.StringVar(value="9.0")

        # Scrollable main area
        outer_canvas = tk.Canvas(self, bg=BG_MAIN, highlightthickness=0)
        scrollbar = tk.Scrollbar(self, orient="vertical", command=outer_canvas.yview)
        outer_canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        outer_canvas.pack(side="left", fill="both", expand=True)
        pad = tk.Frame(outer_canvas, bg=BG_MAIN)
        win_id = outer_canvas.create_window((0,0), window=pad, anchor="nw")
        pad.bind("<Configure>", lambda e: outer_canvas.configure(scrollregion=outer_canvas.bbox("all")))
        outer_canvas.bind("<Configure>", lambda e: outer_canvas.itemconfig(win_id, width=e.width))
        outer_canvas.bind("<MouseWheel>", lambda e: outer_canvas.yview_scroll(-1*(e.delta//120),"units"))
        pad.bind("<MouseWheel>", lambda e: outer_canvas.yview_scroll(-1*(e.delta//120),"units"))

        # Hero header
        hero = tk.Frame(pad, bg=BG_GLASS, padx=24, pady=20)
        hero.pack(fill="x", padx=22, pady=(18,0))
        tk.Frame(hero, bg=ACCENT, width=4).pack(side="left", fill="y", padx=(0,16))
        hero_text = tk.Frame(hero, bg=BG_GLASS)
        hero_text.pack(side="left", fill="both", expand=True)
        tk.Label(hero_text, text=f"Good day, {self.app.username}",
                 font=("Segoe UI", 18, "bold"), bg=BG_GLASS, fg=TEXT_PRI).pack(anchor="w")
        tk.Label(hero_text, text="Upload a light data file (.bin or .npz) to visualise your plant's readings.",
                 font=self.f_small, bg=BG_GLASS, fg=TEXT_SEC).pack(anchor="w", pady=(2,0))
        # File button
        file_btn = tk.Frame(hero, bg=ACCENT, cursor="hand2", padx=16, pady=0)
        file_btn.pack(side="right", fill="y")
        icon_lbl = tk.Label(file_btn, text="📂", font=("Segoe UI",12), bg=ACCENT, fg=ON_ACCENT)
        icon_lbl.pack()
        tk.Label(file_btn, text="ADD FILE", font=("Segoe UI",8,"bold"), bg=ACCENT, fg=ON_ACCENT).pack()
        bind_tree(file_btn, "<Button-1>", lambda e: self._load_file())
        hover(file_btn, ACCENT, ACCENT2)

        self._file_name_lbl = tk.Label(pad, textvariable=self._file_label_var,
                                        font=self.f_small, bg=BG_MAIN, fg=ACCENT)
        self._file_name_lbl.pack(anchor="e", padx=22, pady=(4,0))

        # Stat cards row
        stats_row = tk.Frame(pad, bg=BG_MAIN)
        stats_row.pack(fill="x", padx=22, pady=(14,0))
        configs = [
            ("AVG",  self.avg_var, BLUE,   "lx", "Average intensity"),
            ("MAX",  self.max_var, ACCENT, "lx", "Peak reading"),
            ("MIN",  self.min_var, ORANGE, "lx", "Lowest reading"),
        ]
        for idx, (tag, var, color, unit, desc) in enumerate(configs):
            sc = tk.Frame(stats_row, bg=BG_CARD, padx=0, pady=0)
            sc.pack(side="left", padx=(0,10), fill="x", expand=True)
            tk.Frame(sc, bg=color, height=3).pack(fill="x")
            inner = tk.Frame(sc, bg=BG_CARD, padx=16, pady=12)
            inner.pack(fill="both")
            tk.Label(inner, text=tag, font=("Segoe UI",7,"bold"),
                     bg=BG_CARD, fg=color).pack(anchor="w")
            val_row = tk.Frame(inner, bg=BG_CARD)
            val_row.pack(anchor="w", pady=(2,0))
            tk.Label(val_row, textvariable=var, font=("Segoe UI",26,"bold"),
                     bg=BG_CARD, fg=TEXT_PRI).pack(side="left")
            tk.Label(val_row, text=unit, font=("Segoe UI",9), bg=BG_CARD,
                     fg=TEXT_SEC).pack(side="left", padx=(4,0), pady=(8,0))
            tk.Label(inner, text=desc, font=("Segoe UI",7), bg=BG_CARD, fg=TEXT_MUT).pack(anchor="w")

        # Chart area
        chart_outer = tk.Frame(pad, bg=BG_CARD, padx=0, pady=0)
        chart_outer.pack(fill="x", padx=22, pady=(14,0))
        tk.Frame(chart_outer, bg=BLUE, height=3).pack(fill="x")
        chart_header = tk.Frame(chart_outer, bg=BG_CARD, padx=16, pady=10)
        chart_header.pack(fill="x")
        tk.Label(chart_header, text="Light Intensity Over Time", font=self.f_title,
                 bg=BG_CARD, fg=TEXT_PRI).pack(side="left")
        tk.Label(chart_header, text="lux", font=("Segoe UI",8),
                 bg=BG_GLASS, fg=BLUE, padx=8, pady=3).pack(side="right")

        # Placeholder
        self._placeholder_frame = tk.Frame(chart_outer, bg=BG_CARD, height=220)
        self._placeholder_frame.pack(fill="x")
        self._placeholder_frame.pack_propagate(False)
        tk.Label(self._placeholder_frame,
                 text="No data loaded\n\nClick  ADD FILE  above to load a .bin or .npz file",
                 font=self.f_body, bg=BG_CARD, fg=TEXT_MUT, justify="center").place(relx=0.5, rely=0.5, anchor="center")

        self.chart_frame = tk.Frame(chart_outer, bg=BG_CARD)
        self.chart_frame.pack(fill="both", expand=True)

        # Plant height estimator
        self._build_plant_height(pad)

        # Add plant teaser
        add_card = tk.Frame(pad, bg=BG_GLASS, cursor="hand2", padx=24, pady=18)
        add_card.pack(fill="x", padx=22, pady=(14,22))
        tk.Frame(add_card, bg=ACCENT, width=4).pack(side="left", fill="y", padx=(0,16))
        txt = tk.Frame(add_card, bg=BG_GLASS)
        txt.pack(side="left", fill="both", expand=True)
        tk.Label(txt, text="Expand your collection", font=("Segoe UI",11,"bold"),
                 bg=BG_GLASS, fg=TEXT_PRI).pack(anchor="w")
        tk.Label(txt, text="Navigate to My Plants to add and monitor new plants.",
                 font=self.f_small, bg=BG_GLASS, fg=TEXT_SEC).pack(anchor="w")
        arrow = tk.Label(add_card, text="→", font=("Segoe UI",20), bg=BG_GLASS, fg=ACCENT)
        arrow.pack(side="right")
        bind_tree(add_card, "<Button-1>", lambda e: self.app._show_page("My Plants"))
        hover(add_card, BG_GLASS, BG_CARD2)

    # Plant height section
    def _build_plant_height(self, parent):
        ph_outer = tk.Frame(parent, bg=BG_CARD, padx=0, pady=0)
        ph_outer.pack(fill="x", padx=22, pady=(14,0))
        tk.Frame(ph_outer, bg=TEAL, height=3).pack(fill="x")

        head = tk.Frame(ph_outer, bg=BG_CARD, padx=16, pady=10)
        head.pack(fill="x")
        tk.Label(head, text="Plant Height", font=self.f_title, bg=BG_CARD, fg=TEXT_PRI).pack(side="left")
        tk.Label(head, text="📏", font=("Segoe UI",12), bg=BG_CARD).pack(side="left", padx=(6,0))
        tk.Label(head, text="cm", font=("Segoe UI",8), bg=BG_GLASS, fg=TEAL, padx=8, pady=3).pack(side="right")

        body = tk.Frame(ph_outer, bg=BG_CARD, padx=16, pady=0)
        body.pack(fill="x", pady=(0,14))
        tk.Label(body, text="Upload a plant photo, then estimate its height with one of the two models.",
                 font=self.f_small, bg=BG_CARD, fg=TEXT_SEC).pack(anchor="w", pady=(0,10))

        # Row 1: upload + filename + pot height
        row1 = tk.Frame(body, bg=BG_CARD); row1.pack(fill="x")
        up_btn = tk.Frame(row1, bg=BLUE, cursor="hand2", padx=14, pady=7)
        up_btn.pack(side="left")
        tk.Label(up_btn, text="📷  Upload Photo", font=self.f_label, bg=BLUE, fg=ON_ACCENT).pack()
        bind_tree(up_btn, "<Button-1>", lambda e: self._ph_upload())
        hover(up_btn, BLUE, BLUE2)

        tk.Label(row1, textvariable=self._ph_file_var, font=self.f_small,
                 bg=BG_CARD, fg=TEXT_SEC).pack(side="left", padx=(12,0))

        pot_frame = tk.Frame(row1, bg=BG_CARD); pot_frame.pack(side="right")
        tk.Label(pot_frame, text="Pot height (cm):", font=self.f_small,
                 bg=BG_CARD, fg=TEXT_SEC).pack(side="left", padx=(0,6))
        pot_box = tk.Frame(pot_frame, bg=BG_GLASS); pot_box.pack(side="left")
        tk.Frame(pot_box, bg=TEAL, width=3).pack(side="left", fill="y")
        tk.Entry(pot_box, textvariable=self._ph_pot_var, width=6, bg=BG_GLASS, fg=TEXT_PRI,
                 insertbackground=TEAL, relief="flat", font=("Segoe UI",9)).pack(side="left", ipady=5, padx=(6,6))

        # Row 2: model choice buttons
        row2 = tk.Frame(body, bg=BG_CARD); row2.pack(fill="x", pady=(10,0))
        tk.Label(row2, text="Choose a model:", font=self.f_small, bg=BG_CARD, fg=TEXT_SEC).pack(side="left", padx=(0,8))

        m1 = tk.Frame(row2, bg=TEAL, cursor="hand2", padx=14, pady=6); m1.pack(side="left", padx=(0,8))
        tk.Label(m1, text="Model 1 · Colour", font=self.f_label, bg=TEAL, fg=ON_ACCENT).pack()
        bind_tree(m1, "<Button-1>", lambda e: self._ph_measure("color"))
        hover(m1, TEAL, "#1fb3a0")

        m2 = tk.Frame(row2, bg=PURPLE, cursor="hand2", padx=14, pady=6); m2.pack(side="left")
        tk.Label(m2, text="Model 2 · Edge", font=self.f_label, bg=PURPLE, fg=ON_ACCENT).pack()
        bind_tree(m2, "<Button-1>", lambda e: self._ph_measure("edge"))
        hover(m2, PURPLE, "#8b6ee8")

        # Result
        self._ph_result_lbl = tk.Label(body, textvariable=self._ph_result_var,
                                        font=("Segoe UI",13,"bold"), bg=BG_CARD, fg=TEAL,
                                        wraplength=720, justify="left")
        self._ph_result_lbl.pack(anchor="w", pady=(12,0))

    def _ph_upload(self):
        path = filedialog.askopenfilename(
            title="Select Plant Photo",
            filetypes=[("Image files","*.jpg *.jpeg *.png *.webp *.bmp"),("All files","*.*")])
        if not path: return
        self._ph_image_path = path
        self._ph_file_var.set(f"  {os.path.basename(path)}")
        self._ph_result_var.set("")

    def _ph_measure(self, method):
        if not self._ph_image_path:
            messagebox.showwarning("No Photo", "Please upload a plant photo first."); return
        if not os.path.exists(self._ph_image_path):
            messagebox.showerror("File Missing", "The selected photo no longer exists."); return
        try:
            pot_cm = float(self._ph_pot_var.get())
            if pot_cm <= 0: raise ValueError
        except ValueError:
            messagebox.showerror("Invalid Pot Height", "Pot height must be a positive number."); return

        label = "Colour model" if method == "color" else "Edge model"
        self._ph_result_lbl.config(fg=TEAL)
        self._ph_result_var.set(f"Measuring with the {label}…")

        def _run():
            try:
                if method == "color":
                    h = measure_plant_height_color(self._ph_image_path, pot_height_cm=pot_cm)
                else:
                    h = measure_plant_height_edge(self._ph_image_path, pot_height_cm=pot_cm)
                self.after(0, lambda: self._ph_show(h, label))
            except Exception as ex:
                self.after(0, lambda e=ex: self._ph_error(str(e)))
        threading.Thread(target=_run, daemon=True).start()

    def _ph_show(self, height_cm, label):
        self._ph_result_lbl.config(fg=ACCENT)
        self._ph_result_var.set(f"🌱  Estimated height: {height_cm:.2f} cm    ({label})")

    def _ph_error(self, msg):
        self._ph_result_lbl.config(fg=RED)
        self._ph_result_var.set(f"⚠  {msg}")

    # Light-data file handling 
    def _load_file(self):
        path = filedialog.askopenfilename(
            title="Open Light Data File",
            filetypes=[("Binary/NumPy files", "*.bin *.npz"), ("All files", "*.*")]
        )
        if not path: return
        data = []
        ext = os.path.splitext(path)[1].lower()
        try:
            if ext == ".npz":
                loaded = np.load(path, allow_pickle=True)
                for key in loaded.files:
                    arr = loaded[key].flatten()
                    data.extend([float(v) for v in arr if np.isfinite(v)])
            elif ext == ".bin":
                raw = np.fromfile(path, dtype=np.float32)
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
        self._file_label_var.set(f"  Loaded: {fname}  ({len(data):,} values)")

        # Save to history
        entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "filename":  fname,
            "path":      path,
            "values":    data[:2000],  # cap stored values
        }
        history = _load_history_db()
        history.append(entry)
        history = _prune_old_entries(history, days=10)
        _save_history_db(history)

        self._update_stats()
        self._draw_chart()
        # Refresh history page if it exists
        if hasattr(self.app, "_pages") and "History" in self.app._pages:
            self.app._pages["History"].refresh()

    def _update_stats(self):
        d = self._data
        if not d: return
        self.avg_var.set(f"{sum(d)/len(d):.0f}")
        self.max_var.set(f"{max(d):.0f}")
        self.min_var.set(f"{min(d):.0f}")

    def refresh(self):
        if not self._data:
            self.avg_var.set("—"); self.max_var.set("—"); self.min_var.set("—")

    def _draw_chart(self):
        if self._chart_canvas:
            self._chart_canvas.get_tk_widget().destroy()
            plt.close("all")
        self._placeholder_frame.pack_forget()

        data = self._data
        x    = list(range(len(data)))

        fig, axes = plt.subplots(2, 1, figsize=(7, 4.4),
                                  gridspec_kw={"height_ratios":[3,1],"hspace":0.05})
        fig.patch.set_facecolor(BG_CARD)

        ax = axes[0]
        ax.set_facecolor(BG_CARD)
        ax.fill_between(x, data, alpha=0.18, color=BLUE)
        ax.fill_between(x, data, alpha=0.06, color=ACCENT)
        ax.plot(x, data, color=BLUE, linewidth=1.8, zorder=3)
        if len(data) <= 200:
            ax.scatter(x, data, color=BLUE, s=18, zorder=4, alpha=0.7)
        ax.axhline(y=300, color=RED,    linestyle="--", linewidth=1, alpha=0.7)
        ax.axhline(y=800, color=ACCENT, linestyle="--", linewidth=1, alpha=0.7)
        ax.text(len(data)*0.98, 310, "LOW",     color=RED,    fontsize=7, ha="right")
        ax.text(len(data)*0.98, 810, "OPTIMAL", color=ACCENT, fontsize=7, ha="right")
        ax.set_xlim(0, max(len(data)-1,1)); ax.set_ylim(0, max(max(data)*1.1, 1100))
        ax.tick_params(colors=TEXT_SEC, labelsize=7, labelbottom=False)
        ax.grid(color=TEXT_MUT, linestyle="-", linewidth=0.3, alpha=0.4)
        for spine in ax.spines.values(): spine.set_edgecolor(BORDER)
        ax.set_title("Light Intensity", color=TEXT_PRI, fontsize=10, pad=8, loc="left")

        ax2 = axes[1]
        ax2.set_facecolor(BG_CARD)
        bins = min(80, len(data))
        bin_size = max(1, len(data)//bins)
        bin_x=[]; bin_y=[]
        for i in range(0, len(data), bin_size):
            chunk = data[i:i+bin_size]
            bin_x.append(i); bin_y.append(sum(chunk)/len(chunk))
        colors_bar = [ACCENT if v >= 300 else RED for v in bin_y]
        ax2.bar(bin_x, bin_y, width=bin_size*0.8, color=colors_bar, alpha=0.7, zorder=2)
        ax2.set_xlim(0, max(len(data)-1,1))
        ax2.set_ylim(0, max(max(data)*1.1,1100))
        ax2.tick_params(colors=TEXT_SEC, labelsize=6)
        ax2.set_xlabel("Sample index", color=TEXT_SEC, fontsize=7)
        ax2.grid(color=TEXT_MUT, linestyle="-", linewidth=0.3, alpha=0.3)
        for spine in ax2.spines.values(): spine.set_edgecolor(BORDER)

        fig.tight_layout(pad=1.0)
        self._chart_canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
        self._chart_canvas.draw()
        self._chart_canvas.get_tk_widget().pack(fill="both", expand=True)