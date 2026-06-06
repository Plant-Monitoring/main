import json
import threading
import tkinter as tk
from tkinter import messagebox

from .theme import (
    BG_MAIN, BG_CARD, BG_GLASS, ACCENT, RED, YELLOW, TEAL,
    TEXT_PRI, TEXT_SEC, TEXT_MUT, BORDER, ON_ACCENT,
    bind_tree, hover, BasePage,
)

# Colours the model can return (index -> name). Mirrors models/growth.COLORS.
# Used for the colour selector and for labelling the predicted colour.
COLORS = ["green", "yellow", "brown", "pale", "black"]


class GrowthPage(BasePage):
    FIELDS = [
        ("days_passed",        "Days passed"),
        ("avg_direct_light",   "Avg direct light (lux)"),
        ("avg_indirect_light", "Avg indirect light (lux)"),
        ("avg_nighttime",      "Avg nighttime (hrs)"),
        ("avg_temp",           "Avg temperature (C)"),
        ("min_temp",           "Min temperature (C)"),
        ("max_temp",           "Max temperature (C)"),
        ("times_watered",      "Times watered"),
        ("initial_height",     "Initial height (cm)"),
    ]
    COLORS = COLORS

    def _build(self):
        self._entries   = {}
        self._color_var = tk.StringVar(value="green")

        outer = tk.Frame(self, bg=BG_MAIN)
        outer.pack(fill="both", expand=True, padx=22, pady=18)

        tk.Label(outer, text="Growth Prediction", font=("Segoe UI",16,"bold"),
                 bg=BG_MAIN, fg=TEXT_PRI).pack(anchor="w")
        tk.Label(outer, text="📈", font=("Segoe UI",16), bg=BG_MAIN).pack(anchor="w")
        tk.Label(outer, text="Enter plant conditions and predict height growth using the AI model.",
                 font=self.f_small, bg=BG_MAIN, fg=TEXT_SEC).pack(anchor="w", pady=(0,16))

        cols = tk.Frame(outer, bg=BG_MAIN)
        cols.pack(fill="both", expand=True)

        left = tk.Frame(cols, bg=BG_CARD, width=370, padx=0, pady=0)
        left.pack(side="left", fill="y", padx=(0,14))
        left.pack_propagate(False)
        tk.Frame(left, bg=TEAL, height=3).pack(fill="x")
        left_inner = tk.Frame(left, bg=BG_CARD, padx=18, pady=16)
        left_inner.pack(fill="both", expand=True)

        tk.Label(left_inner, text="Plant Conditions", font=self.f_title,
                 bg=BG_CARD, fg=TEXT_PRI).pack(anchor="w", pady=(0,12))

        for key, label in self.FIELDS:
            row = tk.Frame(left_inner, bg=BG_CARD); row.pack(fill="x", pady=(0,8))
            tk.Label(row, text=label, font=self.f_small, bg=BG_CARD,
                     fg=TEXT_SEC, width=22, anchor="w").pack(side="left")
            ef = tk.Frame(row, bg=BG_GLASS)
            ef.pack(side="left", padx=(6,0), fill="x", expand=True)
            tk.Frame(ef, bg=TEAL, width=3).pack(side="left", fill="y")
            entry = tk.Entry(ef, bg=BG_GLASS, fg=TEXT_PRI, insertbackground=TEAL,
                             relief="flat", font=("Segoe UI",9), width=10)
            entry.pack(side="left", ipady=6, padx=(6,6))
            self._entries[key] = entry

        tk.Frame(left_inner, bg=BORDER, height=1).pack(fill="x", pady=(4,10))
        tk.Label(left_inner, text="Plant colour (before)", font=self.f_small,
                 bg=BG_CARD, fg=TEXT_SEC).pack(anchor="w", pady=(0,6))
        color_row = tk.Frame(left_inner, bg=BG_CARD); color_row.pack(fill="x", pady=(0,12))
        self._color_btns = {}
        for c in self.COLORS:
            is_active = (c == "green")
            btn = tk.Frame(color_row, bg=ACCENT if is_active else BG_GLASS, cursor="hand2", padx=10, pady=4)
            btn.pack(side="left", padx=(0,4))
            lbl = tk.Label(btn, text=c.capitalize(), font=self.f_small,
                           bg=ACCENT if is_active else BG_GLASS,
                           fg=ON_ACCENT if is_active else TEXT_SEC)
            lbl.pack()
            self._color_btns[c] = (btn, lbl)
            def on_color(e, v=c):
                self._color_var.set(v)
                for k,(b,l) in self._color_btns.items():
                    active = (k==v)
                    b.configure(bg=ACCENT if active else BG_GLASS)
                    l.configure(bg=ACCENT if active else BG_GLASS,
                                fg=ON_ACCENT if active else TEXT_SEC)
            bind_tree(btn, "<Button-1>", on_color)

        api_row = tk.Frame(left_inner, bg=BG_CARD); api_row.pack(fill="x", pady=(0,10))
        tk.Label(api_row, text="API URL", font=self.f_small, bg=BG_CARD, fg=TEXT_SEC).pack(anchor="w", pady=(0,4))
        self._api_url_var = tk.StringVar(value="http://localhost:8000/fwd")
        api_frame = tk.Frame(api_row, bg=BG_GLASS); api_frame.pack(fill="x")
        tk.Frame(api_frame, bg=TEAL, width=3).pack(side="left", fill="y")
        api_entry = tk.Entry(api_frame, textvariable=self._api_url_var,
                             bg=BG_GLASS, fg=TEXT_PRI, insertbackground=TEAL,
                             relief="flat", font=("Segoe UI",9))
        api_entry.pack(side="left", fill="x", expand=True, ipady=6, padx=(6,6))

        predict_btn = tk.Frame(left_inner, bg=TEAL, cursor="hand2")
        predict_btn.pack(fill="x", pady=(14,0))
        tk.Label(predict_btn, text="Predict Growth", font=("Segoe UI",10,"bold"),
                 bg=TEAL, fg=ON_ACCENT, pady=10).pack()
        bind_tree(predict_btn, "<Button-1>", lambda e: self._run_prediction())
        hover(predict_btn, TEAL, "#1fb3a0")

        right = tk.Frame(cols, bg=BG_MAIN)
        right.pack(side="left", fill="both", expand=True)
        tk.Label(right, text="Prediction Result", font=self.f_title,
                 bg=BG_MAIN, fg=TEXT_PRI).pack(anchor="w", pady=(0,10))
        self._result_frame = tk.Frame(right, bg=BG_MAIN)
        self._result_frame.pack(fill="both", expand=True)
        self._show_empty()

    def _show_empty(self):
        for w in self._result_frame.winfo_children(): w.destroy()
        container = tk.Frame(self._result_frame, bg=BG_CARD, padx=20, pady=40)
        container.pack(fill="both", expand=True)
        tk.Frame(container, bg=TEAL, height=3).pack(fill="x", pady=(0,20))
        tk.Label(container, text="📈", font=("Segoe UI",40), bg=BG_CARD).pack(pady=(0,8))
        tk.Label(container, text="Fill in the plant conditions and click Predict Growth.",
                 font=self.f_body, bg=BG_CARD, fg=TEXT_SEC, justify="center").pack()

    def _show_loading(self):
        for w in self._result_frame.winfo_children(): w.destroy()
        container = tk.Frame(self._result_frame, bg=BG_CARD, padx=20, pady=40)
        container.pack(fill="both", expand=True)
        tk.Frame(container, bg=TEAL, height=3).pack(fill="x", pady=(0,20))
        tk.Label(container, text="Contacting growth model...",
                 font=("Segoe UI",11,"bold"), bg=BG_CARD, fg=TEXT_PRI).pack(pady=(10,8))
        self._loading_lbl = tk.Label(container, text="--  --  --",
                                      font=("Segoe UI",14), bg=BG_CARD, fg=TEAL)
        self._loading_lbl.pack(pady=(12,0))
        self._dot_idx = 0; self._animate()

    def _animate(self):
        patterns = ["--  o  o","o  --  o","o  o  --","o  --  o"]
        try:
            self._loading_lbl.config(text=patterns[self._dot_idx % len(patterns)])
            self._dot_idx += 1
            self._anim_job = self.after(400, self._animate)
        except: pass

    def _run_prediction(self):
        # Import the model lazily so the GUI works even before models/growth.py exists.
        try:
            from models.growth import predict_growth
        except ModuleNotFoundError:
            messagebox.showinfo(
                "Model not available yet",
                "The growth model (models/growth.py) hasn't been added yet.\n"
                "The page will work as soon as it's in place.")
            return
        except Exception as ex:
            messagebox.showerror("Model Error", f"Could not load the growth model:\n{ex}")
            return

        data = {}
        for key, label in self.FIELDS:
            val = self._entries[key].get().strip()
            if not val:
                messagebox.showwarning("Missing Input", f"Please fill in: {label}"); return
            try: data[key] = float(val)
            except ValueError:
                messagebox.showerror("Invalid Input", f"'{label}' must be a number."); return
        color   = self._color_var.get()
        api_url = self._api_url_var.get().strip()
        if not api_url:
            messagebox.showwarning("Missing API URL", "Please enter the growth API URL."); return
        self._show_loading()
        def _call():
            try:
                rep = predict_growth(data, color, api_url, user_id=1, timeout=10)
                self.after(0, lambda: self._show_result(rep))
            except Exception as ex:
                self.after(0, lambda e=ex: self._show_error(str(e)))
        threading.Thread(target=_call, daemon=True).start()

    def _show_result(self, rep):
        if hasattr(self, "_anim_job"):
            try: self.after_cancel(self._anim_job)
            except: pass
        for w in self._result_frame.winfo_children(): w.destroy()
        try:
            color_name = self.COLORS[rep.get("color", 0)] if "color" in rep else "unknown"
        except (IndexError, TypeError):
            color_name = "unknown"
        guess = rep.get("guess", "N/A")

        card = tk.Frame(self._result_frame, bg=BG_CARD, padx=0, pady=0)
        card.pack(fill="x", pady=(0,10))
        tk.Frame(card, bg=TEAL, height=3).pack(fill="x")
        inner = tk.Frame(card, bg=BG_CARD, padx=20, pady=20)
        inner.pack(fill="both")

        tk.Label(inner, text="Prediction Complete", font=("Segoe UI",12,"bold"),
                 bg=BG_CARD, fg=TEAL).pack(anchor="w", pady=(0,12))

        height_row = tk.Frame(inner, bg=BG_GLASS, padx=16, pady=14)
        height_row.pack(fill="x", pady=(0,8))
        tk.Label(height_row, text="Predicted height growth", font=self.f_small, bg=BG_GLASS, fg=TEXT_SEC).pack(anchor="w")
        val_row = tk.Frame(height_row, bg=BG_GLASS); val_row.pack(anchor="w")
        tk.Label(val_row, text=f"{guess}", font=("Segoe UI",30,"bold"), bg=BG_GLASS, fg=TEAL).pack(side="left")
        tk.Label(val_row, text=" cm", font=("Segoe UI",12), bg=BG_GLASS, fg=TEXT_SEC).pack(side="left", pady=(10,0))

        color_row = tk.Frame(inner, bg=BG_GLASS, padx=16, pady=14)
        color_row.pack(fill="x", pady=(0,8))
        tk.Label(color_row, text="Predicted plant colour", font=self.f_small, bg=BG_GLASS, fg=TEXT_SEC).pack(anchor="w")
        color_colors = {"green":ACCENT,"yellow":YELLOW,"brown":"#a0522d","pale":TEXT_SEC,"black":"#888888"}
        tk.Label(color_row, text=color_name.capitalize(),
                 font=("Segoe UI",16,"bold"), bg=BG_GLASS,
                 fg=color_colors.get(color_name, TEXT_PRI)).pack(anchor="w")

        raw_card = tk.Frame(self._result_frame, bg=BG_CARD, padx=16, pady=12)
        raw_card.pack(fill="x")
        tk.Frame(raw_card, bg=BORDER, height=1).pack(fill="x", pady=(0,6))
        tk.Label(raw_card, text="Raw API response", font=("Segoe UI",7,"bold"),
                 bg=BG_CARD, fg=TEXT_MUT).pack(anchor="w", pady=(0,4))
        raw_txt = tk.Text(raw_card, bg=BG_GLASS, fg=TEXT_SEC, font=("Courier",8),
                          relief="flat", height=6, state="normal")
        raw_txt.insert("end", json.dumps(rep, indent=2))
        raw_txt.config(state="disabled")
        raw_txt.pack(fill="x")

        retry_btn = tk.Frame(self._result_frame, bg=BG_GLASS, cursor="hand2", padx=14, pady=8)
        retry_btn.pack(anchor="e", pady=(10,0))
        tk.Label(retry_btn, text="Predict Again", font=self.f_label, bg=BG_GLASS, fg=TEAL).pack()
        bind_tree(retry_btn, "<Button-1>", lambda e: self._run_prediction())
        hover(retry_btn, BG_GLASS, BG_CARD)

    def _show_error(self, msg):
        if hasattr(self, "_anim_job"):
            try: self.after_cancel(self._anim_job)
            except: pass
        for w in self._result_frame.winfo_children(): w.destroy()
        card = tk.Frame(self._result_frame, bg=BG_CARD, padx=0, pady=0)
        card.pack(fill="both", expand=True)
        tk.Frame(card, bg=RED, height=3).pack(fill="x")
        inner = tk.Frame(card, bg=BG_CARD, padx=20, pady=20)
        inner.pack(fill="both")
        tk.Label(inner, text="Prediction Failed", font=("Segoe UI",12,"bold"),
                 bg=BG_CARD, fg=RED).pack(pady=(0,8))
        tk.Label(inner, text=msg, font=self.f_body, bg=BG_CARD, fg=TEXT_SEC,
                 wraplength=400, justify="center").pack(pady=(0,12))
        retry_btn = tk.Frame(inner, bg=BG_GLASS, cursor="hand2", padx=14, pady=8)
        retry_btn.pack()
        tk.Label(retry_btn, text="Try Again", font=self.f_label, bg=BG_GLASS, fg=TEAL).pack()
        bind_tree(retry_btn, "<Button-1>", lambda e: self._run_prediction())
        hover(retry_btn, BG_GLASS, BG_CARD)