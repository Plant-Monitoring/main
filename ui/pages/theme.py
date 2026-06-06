import os
import json
import datetime
import tkinter as tk

# Colour palette
BG_MAIN   = "#080b12"
BG_SIDE   = "#0d1117"
BG_CARD   = "#111520"
BG_CARD2  = "#161b2a"
BG_GLASS  = "#1a2035"
ACCENT    = "#00e5a0"
ACCENT2   = "#00b37e"
BLUE      = "#38bdf8"
BLUE2     = "#0ea5e9"
RED       = "#f43f5e"
YELLOW    = "#fbbf24"
PURPLE    = "#a78bfa"
TEAL      = "#2dd4bf"
ORANGE    = "#fb923c"
TEXT_PRI  = "#f0f4ff"
TEXT_SEC  = "#8b95a8"
TEXT_MUT  = "#3a4259"
BORDER    = "#1e2638"
BORDER2   = "#253047"
GLOW      = "#0d2b22"

# Users (in-memory accounts for this session)
USERS = {
    "Anastasija": "plant123",
    "David":      "plant123",
    "Damjan":     "plant123",
}

# Data location (the ui/ folder, parent of this pages/ package)
_PKG_DIR   = os.path.dirname(os.path.abspath(__file__))   
APP_DIR    = os.path.dirname(_PKG_DIR)                    
GALLERY_DB = os.path.join(APP_DIR, "gallery_data.json")
HISTORY_DB = os.path.join(APP_DIR, "history_data.json")

# History DB
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

# Gallery DB
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

# UI helpers
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

# GreenSlider 
class GreenSlider(tk.Frame):
    def __init__(self, parent, from_, to, variable, resolution=0.5, length=260, **kw):
        super().__init__(parent, bg=BG_CARD, height=24)
        self._from=from_; self._to=to; self._var=variable; self._res=resolution; self._len=length; self._drag=False
        self._canvas = tk.Canvas(self, bg=BG_CARD, height=24, width=length, highlightthickness=0)
        self._canvas.pack(fill="x", expand=True)
        self._canvas.bind("<Configure>",       self._redraw)
        self._canvas.bind("<ButtonPress-1>",   self._on_press)
        self._canvas.bind("<B1-Motion>",       self._on_drag)
        self._canvas.bind("<ButtonRelease-1>", self._on_release)
        self._var.trace_add("write", lambda *a: self._redraw())
        self._redraw()

    def _x_for_val(self, val, w):
        ratio = (val-self._from)/(self._to-self._from)
        return int(10 + ratio*(w-20))

    def _val_for_x(self, x, w):
        ratio = (x-10)/(w-20)
        ratio = max(0.0, min(1.0, ratio))
        raw   = self._from + ratio*(self._to-self._from)
        snapped = round(raw/self._res)*self._res
        return max(self._from, min(self._to, snapped))

    def _redraw(self, *_):
        c=self._canvas; w=c.winfo_width() or self._len
        c.delete("all")
        # Track
        c.create_rectangle(10, 10, w-10, 14, fill=BG_GLASS, outline=BORDER2)
        val=self._var.get(); tx=self._x_for_val(val, w)
        # Fill
        c.create_rectangle(10, 10, tx, 14, fill=ACCENT, outline="")
        # Glow dots on track
        steps=8
        for i in range(1, steps):
            sx = int(10 + i*(tx-10)/steps)
            c.create_oval(sx-1, 11, sx+1, 13, fill=ACCENT2, outline="")
        # Thumb with glow
        c.create_oval(tx-10, 2, tx+10, 22, fill=ACCENT, outline=ACCENT2, width=2)
        c.create_oval(tx-5,  7, tx+5,  17, fill=BG_MAIN, outline="")

    def _on_press(self, event):  self._drag=True;  self._update(event.x)
    def _on_drag(self, event):
        if self._drag: self._update(event.x)
    def _on_release(self, event): self._drag=False; self._update(event.x)
    def _update(self, x):
        w=self._canvas.winfo_width() or self._len
        self._var.set(round(self._val_for_x(x,w), 2))

# BasePage
class BasePage(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=BG_MAIN)
        self.app = app
        self.f_title = ("Segoe UI", 12, "bold")
        self.f_big   = ("Segoe UI", 22, "bold")
        self.f_body  = ("Segoe UI", 9)
        self.f_small = ("Segoe UI", 8)
        self.f_label = ("Segoe UI", 9, "bold")
        self._build()

    def _section_header(self, parent, text, color=ACCENT):
        row = tk.Frame(parent, bg=BG_MAIN)
        row.pack(fill="x", pady=(0,10))
        tk.Frame(row, bg=color, width=4, height=18).pack(side="left")
        tk.Label(row, text=text, font=self.f_title, bg=BG_MAIN, fg=TEXT_PRI, padx=8).pack(side="left")
        tk.Frame(row, bg=BORDER, height=1).pack(side="left", fill="x", expand=True, pady=9)

    def _card(self, parent, padx=16, pady=12, **kw):
        f = tk.Frame(parent, bg=BG_CARD, padx=padx, pady=pady, **kw)
        # subtle top accent line
        tk.Frame(f, bg=BORDER2, height=1).pack(fill="x", pady=(0,8))
        return f

    def _build(self): pass

__all__ = [
    "BG_MAIN", "BG_SIDE", "BG_CARD", "BG_CARD2", "BG_GLASS", "ACCENT", "ACCENT2",
    "BLUE", "BLUE2", "RED", "YELLOW", "PURPLE", "TEAL", "ORANGE",
    "TEXT_PRI", "TEXT_SEC", "TEXT_MUT", "BORDER", "BORDER2", "GLOW",
    "USERS", "APP_DIR", "GALLERY_DB", "HISTORY_DB",
    "bind_tree", "hover", "GreenSlider", "BasePage",
    "_load_history_db", "_save_history_db", "_prune_old_entries",
    "_load_gallery_db", "_save_gallery_db",
]