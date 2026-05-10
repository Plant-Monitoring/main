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
import base64
import threading
import urllib.request
import urllib.error
import json

os.environ["GOOGLE_API_KEY"] = "AIzaSyBKuN-shGF5gbD2RTsHV_U9OU3uXq6UZv8"

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

def generate_data():
    base = 400
    return [max(150, min(950, base + random.randint(-200, 400))) for _ in range(24)]

ALERTS_DATA = [
    ("●", RED,    "Low Light!",        "10 mins ago", "Current intensity dropped\nbelow the low threshold.",  "280"),
    ("✔", ACCENT, "Optimal Range!",    "1 hour ago",  "Current intensity is now back\nin the optimal range.", "780"),
    ("▲", YELLOW, "High Light Level!", "3 hours ago", "Intensity exceeded the\noptimal threshold.",           "920"),
]

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

def analyze_plant_image(image_path, callback):
    def _run():
        try:
            api_key = os.environ.get("GOOGLE_API_KEY", "").strip()
            if not api_key:
                callback(None, "No Google API key found.")
                return

            with open(image_path, "rb") as f:
                raw = f.read()
            b64 = base64.standard_b64encode(raw).decode("utf-8")

            ext = os.path.splitext(image_path)[1].lower()
            media_map = {".jpg": "image/jpeg", ".jpeg": "image/jpeg",
                         ".png": "image/png", ".gif": "image/gif", ".webp": "image/webp"}
            media_type = media_map.get(ext, "image/jpeg")

            prompt = (
                "You are an expert botanist and plant health specialist. "
                "Carefully examine this plant image and provide a precise diagnosis.\n\n"
                "Respond ONLY with a valid JSON object — no markdown, no code fences, no extra text. "
                "Use exactly these keys:\n"
                "{\n"
                '  "status": one of exactly: "Healthy", "Needs Water", "Overwatered", '
                '"Disease Detected", "Pest Infestation", "Nutrient Deficiency", "Root Rot", "Dead", "Unknown",\n'
                '  "confidence": integer 0-100,\n'
                '  "summary": one concise sentence describing the plant condition,\n'
                '  "symptoms": array of up to 4 strings describing visible symptoms,\n'
                '  "recommendations": array of up to 4 actionable strings,\n'
                '  "urgency": one of exactly: "Low", "Medium", "High", "Critical"\n'
                "}"
            )

            payload = {
                "contents": [{
                    "parts": [
                        {"inline_data": {"mime_type": media_type, "data": b64}},
                        {"text": prompt}
                    ]
                }],
                "generationConfig": {"temperature": 0.1, "maxOutputTokens": 1024}
            }

            url = (
                "https://generativelanguage.googleapis.com/v1beta/models/"
                f"gemini-2.0-flash-lite:generateContent?key={api_key}"
            )
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(url, data=data,
                                          headers={"Content-Type": "application/json"},
                                          method="POST")

            try:
                with urllib.request.urlopen(req, timeout=40) as resp:
                    body = json.loads(resp.read().decode("utf-8"))
            except urllib.error.HTTPError as http_err:
                err_body = http_err.read().decode("utf-8")
                try:
                    msg = json.loads(err_body).get("error", {}).get("message", err_body)
                except Exception:
                    msg = err_body
                callback(None, f"HTTP {http_err.code}: {msg}")
                return

            text = (body.get("candidates", [{}])[0]
                        .get("content", {})
                        .get("parts", [{}])[0]
                        .get("text", ""))

            text = text.strip()
            for fence in ["```json", "```"]:
                if text.startswith(fence):
                    text = text[len(fence):]
                    break
            if text.endswith("```"):
                text = text[:-3]

            result = json.loads(text.strip())
            callback(result, None)

        except json.JSONDecodeError as je:
            callback(None, f"Could not parse response as JSON:\n{je}")
        except Exception as ex:
            callback(None, str(ex))

    threading.Thread(target=_run, daemon=True).start()


class AuthWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Plant Monitor — Sign In")
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
        self._link_btn(f, "Don't have an account? Sign Up", self._render_signup)
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
        tk.Label(f, text="Create Account", font=("Segoe UI", 18, "bold"),
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
            self._su_err.config(text="Username already taken."); return
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

        tk.Label(pad, text=f"Welcome Back, {USER_NAME}!", font=("Segoe UI", 16, "bold"),
                 bg=BG_MAIN, fg=TEXT_PRI).pack(anchor="w")
        tk.Label(pad, text="Hello, check the latest light readings for your plants.",
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
        tk.Label(inner, text="Growing your collection?", font=self.f_label,
                 bg=BG_CARD, fg=TEXT_PRI).pack(pady=(6, 0))
        tk.Label(inner, text="Add a new plant to track its needs and keep thriving",
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
            title="Open light data file",
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
            messagebox.showerror("File Error", f"Could not read file:\n{ex}"); return
        if not data:
            messagebox.showwarning("No Data", "No numeric values found in the file."); return
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
        ax.text(len(data)-0.7, 308, "Low",     color=RED,    fontsize=7, va="bottom")
        ax.text(len(data)-0.7, 808, "Optimal", color=ACCENT, fontsize=7, va="bottom")
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


ALL_ALERTS_EXTENDED = [
    ("●", RED,    "Low Light!",        "10 mins ago", "Current intensity dropped\nbelow the low threshold.",  "280", "critical"),
    ("✔", ACCENT, "Optimal Range!",    "1 hour ago",  "Current intensity is now back\nin the optimal range.", "780", "info"),
    ("▲", YELLOW, "High Light Level!", "3 hours ago", "Intensity exceeded the\noptimal threshold.",           "920", "warning"),
    ("●", RED,    "Low Light!",        "5 hours ago", "Current intensity dropped\nbelow the low threshold.",  "195", "critical"),
    ("✔", ACCENT, "Optimal Range!",    "Yesterday",   "Current intensity is now back\nin the optimal range.", "650", "info"),
    ("▲", YELLOW, "High Light Level!", "2 days ago",  "Intensity exceeded the\noptimal threshold.",           "845", "warning"),
    ("●", RED,    "Low Light!",        "2 days ago",  "Current intensity dropped\nbelow the low threshold.",  "220", "critical"),
    ("✔", ACCENT, "Optimal Range!",    "3 days ago",  "Current intensity is now back\nin the optimal range.", "710", "info"),
    ("▲", YELLOW, "High Light Level!", "4 days ago",  "Intensity exceeded the\noptimal threshold.",           "890", "warning"),
]

class AlertsPage(BasePage):
    def _build(self):
        self._active_filter = "all"
        pad = tk.Frame(self, bg=BG_MAIN)
        pad.pack(fill="both", expand=True, padx=22, pady=18)
        tk.Label(pad, text="🔔  Alerts", font=("Segoe UI", 16, "bold"),
                 bg=BG_MAIN, fg=TEXT_PRI).pack(anchor="w")
        tk.Label(pad, text="All notifications about your plant's light conditions.",
                 font=self.f_small, bg=BG_MAIN, fg=TEXT_SEC).pack(anchor="w", pady=(0, 12))
        filter_row = tk.Frame(pad, bg=BG_MAIN)
        filter_row.pack(fill="x", pady=(0, 12))
        self._filter_btns = {}
        for label, key, color in [("All","all",ACCENT),("Critical","critical",RED),
                                   ("Warnings","warning",YELLOW),("Info","info",BLUE)]:
            btn = tk.Frame(filter_row, bg=BG_CARD, cursor="hand2", padx=12, pady=6)
            btn.pack(side="left", padx=(0, 8))
            lbl = tk.Label(btn, text=label, font=self.f_small, bg=BG_CARD, fg=color)
            lbl.pack()
            self._filter_btns[key] = (btn, lbl, color)
            def on_filter(e, k=key):
                self._active_filter = k
                self._apply_filter()
            bind_tree(btn, "<Button-1>", on_filter)
            hover(btn, BG_CARD, BG_CARD2)
        self._list_frame = tk.Frame(pad, bg=BG_MAIN)
        self._list_frame.pack(fill="both", expand=True)
        self._apply_filter()

    def _apply_filter(self):
        for key, (btn, lbl, color) in self._filter_btns.items():
            active = (key == self._active_filter)
            btn.configure(bg=ACCENT if active else BG_CARD)
            lbl.configure(bg=ACCENT if active else BG_CARD, fg=BG_MAIN if active else color)
        for w in self._list_frame.winfo_children():
            w.destroy()
        shown = [a for a in ALL_ALERTS_EXTENDED
                 if self._active_filter == "all" or a[6] == self._active_filter]
        if not shown:
            tk.Label(self._list_frame, text="No alerts in this category.",
                     font=self.f_body, bg=BG_MAIN, fg=TEXT_SEC).pack(pady=30)
            return
        for icon, color, title, time_str, desc, val, _ in shown:
            card = tk.Frame(self._list_frame, bg=BG_CARD, padx=14, pady=10)
            card.pack(fill="x", pady=(0, 6))
            tk.Label(card, text=icon, font=("Segoe UI", 12), bg=BG_CARD, fg=color
                     ).grid(row=0, column=0, rowspan=2, sticky="n", padx=(0, 12), pady=(2, 0))
            hdr = tk.Frame(card, bg=BG_CARD)
            hdr.grid(row=0, column=1, sticky="ew")
            tk.Label(hdr, text=title,    font=self.f_label, bg=BG_CARD, fg=TEXT_PRI).pack(side="left")
            tk.Label(hdr, text=time_str, font=self.f_small, bg=BG_CARD, fg=TEXT_SEC).pack(side="right")
            tk.Label(card, text=desc, font=self.f_small, bg=BG_CARD, fg=TEXT_SEC, justify="left"
                     ).grid(row=1, column=1, sticky="w")
            tk.Label(card, text=f"▐ {val}", font=self.f_small, bg=BG_CARD, fg=color
                     ).grid(row=2, column=1, sticky="e")
            card.grid_columnconfigure(1, weight=1)


SAMPLE_PLANTS = [
    {"name": "Monstera",    "emoji": "🌿", "location": "Living Room", "status": "Optimal",   "lux": 620, "days": 14},
    {"name": "Snake Plant", "emoji": "🪴", "location": "Bedroom",     "status": "Low Light", "lux": 210, "days": 32},
    {"name": "Fiddle Leaf", "emoji": "🌳", "location": "Study",       "status": "Optimal",   "lux": 740, "days": 7},
    {"name": "Peace Lily",  "emoji": "🌸", "location": "Bathroom",    "status": "High",      "lux": 870, "days": 21},
    {"name": "Cactus Mix",  "emoji": "🌵", "location": "Windowsill",  "status": "Optimal",   "lux": 910, "days": 60},
]
STATUS_COLOR = {"Optimal": ACCENT, "Low Light": RED, "High": YELLOW}

class MyPlantsPage(BasePage):
    def _build(self):
        self._plants = [dict(p) for p in SAMPLE_PLANTS]
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
        tk.Label(self._outer, text="Monitor and manage all your plants in one place.",
                 font=self.f_small, bg=BG_MAIN, fg=TEXT_SEC).pack(anchor="w", pady=(0, 12))
        self._stats_frame = tk.Frame(self._outer, bg=BG_MAIN)
        self._stats_frame.pack(fill="x", pady=(0, 14))
        self._list_frame = tk.Frame(self._outer, bg=BG_MAIN)
        self._list_frame.pack(fill="both", expand=True)
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
        for label, val, color in [("Total Plants", total, BLUE),
                                   ("Optimal",      optimal, ACCENT),
                                   ("Need Attention", alerts, RED)]:
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
            sc = STATUS_COLOR.get(plant["status"], TEXT_SEC)
            card = tk.Frame(self._list_frame, bg=BG_CARD, padx=14, pady=12)
            card.pack(fill="x", pady=(0, 8))
            left = tk.Frame(card, bg=BG_CARD)
            left.pack(side="left", fill="y")
            tk.Label(left, text=plant["emoji"], font=("Segoe UI", 22), bg=BG_CARD).pack(side="left", padx=(0, 12))
            info = tk.Frame(left, bg=BG_CARD)
            info.pack(side="left")
            tk.Label(info, text=plant["name"],              font=self.f_label, bg=BG_CARD, fg=TEXT_PRI).pack(anchor="w")
            tk.Label(info, text=f"📍 {plant['location']}", font=self.f_small, bg=BG_CARD, fg=TEXT_SEC).pack(anchor="w")
            tk.Label(info, text=f"Added {plant['days']} days ago", font=self.f_small, bg=BG_CARD, fg=TEXT_MUT).pack(anchor="w")
            right = tk.Frame(card, bg=BG_CARD)
            right.pack(side="right", fill="y")
            tk.Label(right, text=f"{plant['lux']} lux", font=("Segoe UI", 13, "bold"),
                     bg=BG_CARD, fg=sc).pack(anchor="e")
            tk.Label(right, text=plant["status"], font=self.f_small, bg=BG_CARD2,
                     fg=sc, padx=8, pady=2).pack(anchor="e", pady=(2, 6))
            sim_btn = tk.Label(right, text="↻ New Reading", font=self.f_small,
                               bg=BG_CARD, fg=BLUE, cursor="hand2")
            sim_btn.pack(anchor="e", pady=(0, 4))
            sim_btn.bind("<Button-1>", lambda e, p=plant: self._simulate_reading(p))
            rm_btn = tk.Label(right, text="✕ Remove", font=self.f_small,
                              bg=BG_CARD, fg=TEXT_MUT, cursor="hand2")
            rm_btn.pack(anchor="e")
            rm_btn.bind("<Button-1>", lambda e, p=plant: self._remove_plant(p))

    def _add_plant(self):
        name = simpledialog.askstring("Add Plant", "Plant name:")
        if not name: return
        loc = simpledialog.askstring("Add Plant", "Location (e.g. Living Room):") or "Unknown"
        lux = random.randint(200, 900)
        status = "Optimal" if 300 <= lux <= 800 else ("Low Light" if lux < 300 else "High")
        self._plants.append({"name": name, "emoji": "🌱", "location": loc,
                              "status": status, "lux": lux, "days": 0})
        self._render_all()

    def _remove_plant(self, plant):
        if messagebox.askyesno("Remove Plant", f"Remove '{plant['name']}' from your collection?"):
            self._plants.remove(plant)
            self._render_all()

    def _simulate_reading(self, plant):
        lux = random.randint(150, 950)
        plant["lux"] = lux
        plant["status"] = "Optimal" if 300 <= lux <= 800 else ("Low Light" if lux < 300 else "High")
        self._render_all()


class HistoryPage(BasePage):
    def _build(self):
        pad = tk.Frame(self, bg=BG_MAIN)
        pad.pack(fill="both", expand=True, padx=22, pady=18)
        tk.Label(pad, text="📅  History", font=("Segoe UI", 16, "bold"),
                 bg=BG_MAIN, fg=TEXT_PRI).pack(anchor="w")
        tk.Label(pad, text="Past 7 days of light intensity readings.",
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
            tk.Label(card, text="avg lux", font=self.f_small,             bg=BG_CARD, fg=TEXT_MUT).pack()
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


STATUS_META = {
    "Healthy":             (ACCENT,  "✅"),
    "Needs Water":         (BLUE,    "💧"),
    "Overwatered":         (PURPLE,  "🌊"),
    "Disease Detected":    (RED,     "🦠"),
    "Pest Infestation":    (YELLOW,  "🐛"),
    "Nutrient Deficiency": (YELLOW,  "🟡"),
    "Root Rot":            (RED,     "🪱"),
    "Dead":                ("#888",  "💀"),
    "Unknown":             (TEXT_SEC,"❓"),
}
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
        tk.Label(load_btn, text="📷  Load Plant Image", font=self.f_label,
                 bg=BLUE, fg=BG_MAIN).pack()
        bind_tree(load_btn, "<Button-1>", lambda e: self._load_image())
        hover(load_btn, BLUE, "#38a8d8")

        tk.Label(outer, text="Upload a photo of your plant — Gemini AI will diagnose its health status.",
                 font=self.f_small, bg=BG_MAIN, fg=TEXT_SEC).pack(anchor="w", pady=(0, 14))

        cols = tk.Frame(outer, bg=BG_MAIN)
        cols.pack(fill="both", expand=True)

        left = tk.Frame(cols, bg=BG_CARD, width=280)
        left.pack(side="left", fill="y", padx=(0, 14))
        left.pack_propagate(False)

        tk.Label(left, text="Plant Image", font=self.f_label,
                 bg=BG_CARD, fg=TEXT_SEC).pack(anchor="w", padx=12, pady=(12, 6))

        self._preview_canvas = tk.Canvas(left, bg=BG_CARD2, highlightthickness=0, width=256, height=210)
        self._preview_canvas.pack(padx=12, pady=(0, 8))
        self._preview_canvas.create_text(128, 105, text="No image loaded",
                                          fill=TEXT_MUT, font=("Segoe UI", 9))

        self._img_name_lbl = tk.Label(left, text="", font=self.f_small,
                                       bg=BG_CARD, fg=TEXT_SEC, wraplength=240)
        self._img_name_lbl.pack(padx=12, pady=(0, 8))

        self._analyse_btn_frame = tk.Frame(left, bg=ACCENT, cursor="hand2")
        self._analyse_btn_frame.pack(fill="x", padx=12, pady=(0, 12))
        tk.Label(self._analyse_btn_frame, text="▶  Analyse Plant",
                 font=self.f_label, bg=ACCENT, fg=BG_MAIN, pady=8).pack()
        bind_tree(self._analyse_btn_frame, "<Button-1>", lambda e: self._run_analysis())
        hover(self._analyse_btn_frame, ACCENT, "#00c98a")

        self._results_frame = tk.Frame(cols, bg=BG_MAIN)
        self._results_frame.pack(side="left", fill="both", expand=True)
        self._show_empty_state()

    def _load_image(self):
        path = filedialog.askopenfilename(
            title="Select plant image",
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
            self._preview_canvas.create_text(128, 90,  text="🖼️",       fill=TEXT_SEC, font=("Segoe UI", 32))
            self._preview_canvas.create_text(128, 140, text=fname[:28], fill=TEXT_SEC, font=("Segoe UI", 8))
        except Exception as ex:
            self._preview_canvas.delete("all")
            self._preview_canvas.create_text(128, 105, text=f"Preview error:\n{ex}",
                                              fill=RED, font=("Segoe UI", 8))
        self._show_empty_state(msg="Image loaded. Click ▶ Analyse Plant to diagnose.")

    def _show_empty_state(self, msg="Load a plant image to get started."):
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
        tk.Label(container, text="🔬", font=("Segoe UI", 36), bg=BG_CARD).pack(pady=(20, 12))
        tk.Label(container, text="Analysing plant health…",
                 font=("Segoe UI", 11, "bold"), bg=BG_CARD, fg=TEXT_PRI).pack()
        tk.Label(container, text="Gemini AI is examining your plant image.\nThis may take a few seconds.",
                 font=self.f_body, bg=BG_CARD, fg=TEXT_SEC, justify="center").pack(pady=(8, 0))
        self._loading_dots = tk.Label(container, text="● ● ●", font=("Segoe UI", 14),
                                       bg=BG_CARD, fg=ACCENT)
        self._loading_dots.pack(pady=(16, 0))
        self._dot_idx = 0
        self._animate_dots()

    def _animate_dots(self):
        patterns = ["●  ○  ○", "○  ●  ○", "○  ○  ●", "○  ●  ○"]
        try:
            self._loading_dots.config(text=patterns[self._dot_idx % len(patterns)])
            self._dot_idx += 1
            self._anim_job = self.after(400, self._animate_dots)
        except Exception:
            pass

    def _run_analysis(self):
        if not self._image_path:
            messagebox.showwarning("No Image", "Please load a plant image first.")
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

        analyze_plant_image(self._image_path, on_result)

    def _show_result(self, result, error):
        for w in self._results_frame.winfo_children():
            w.destroy()

        if error or result is None:
            container = tk.Frame(self._results_frame, bg=BG_CARD, padx=20, pady=20)
            container.pack(fill="both", expand=True)
            tk.Label(container, text="⚠️  Analysis Failed", font=("Segoe UI", 12, "bold"),
                     bg=BG_CARD, fg=RED).pack(pady=(10, 8))
            tk.Label(container, text=str(error) if error else "Unknown error.",
                     font=self.f_body, bg=BG_CARD, fg=TEXT_SEC, wraplength=380, justify="center").pack(pady=(0, 12))
            re_btn = tk.Frame(container, bg=BG_CARD2, cursor="hand2", padx=14, pady=8)
            re_btn.pack()
            tk.Label(re_btn, text="↻  Try Again", font=self.f_label, bg=BG_CARD2, fg=ACCENT).pack()
            bind_tree(re_btn, "<Button-1>", lambda e: self._run_analysis())
            hover(re_btn, BG_CARD2, BG_CARD)
            return

        status   = result.get("status", "Unknown")
        conf     = result.get("confidence", 0)
        summary  = result.get("summary", "")
        symptoms = result.get("symptoms", [])
        recs     = result.get("recommendations", [])
        urgency  = result.get("urgency", "Low")

        color, badge_emoji = STATUS_META.get(status, (TEXT_SEC, "❓"))
        urg_color = URGENCY_COLOR.get(urgency, TEXT_SEC)

        pad = tk.Frame(self._results_frame, bg=BG_MAIN)
        pad.pack(fill="both", expand=True)

        banner = tk.Frame(pad, bg=BG_CARD, padx=16, pady=14)
        banner.pack(fill="x", pady=(0, 10))
        top_row = tk.Frame(banner, bg=BG_CARD)
        top_row.pack(fill="x")
        tk.Label(top_row, text=f"{badge_emoji}  {status}", font=("Segoe UI", 14, "bold"),
                 bg=BG_CARD, fg=color).pack(side="left")
        tk.Label(top_row, text=f"  {urgency} Urgency  ",
                 font=self.f_small, bg=urg_color, fg=BG_MAIN, padx=6, pady=2).pack(side="right")

        conf_row = tk.Frame(banner, bg=BG_CARD)
        conf_row.pack(fill="x", pady=(8, 4))
        tk.Label(conf_row, text=f"Confidence: {conf}%", font=self.f_small,
                 bg=BG_CARD, fg=TEXT_SEC).pack(side="left")
        bar_bg = tk.Frame(banner, bg=BG_CARD2, height=6)
        bar_bg.pack(fill="x")
        bar_bg.update_idletasks()
        w = bar_bg.winfo_width() or 300
        tk.Frame(bar_bg, bg=color, width=max(4, int(w * conf / 100)), height=6).place(x=0, y=0)

        tk.Label(banner, text=summary, font=self.f_body, bg=BG_CARD,
                 fg=TEXT_PRI, wraplength=360, justify="left").pack(anchor="w", pady=(10, 0))

        if symptoms:
            tk.Label(pad, text="Observed Symptoms", font=self.f_title,
                     bg=BG_MAIN, fg=TEXT_PRI).pack(anchor="w", pady=(4, 6))
            for sym in symptoms:
                row = tk.Frame(pad, bg=BG_CARD, padx=12, pady=8)
                row.pack(fill="x", pady=(0, 4))
                tk.Label(row, text="⚬", font=("Segoe UI", 10), bg=BG_CARD, fg=color).pack(side="left", padx=(0, 8))
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
        tk.Label(re_btn, text="↻  Re-Analyse", font=self.f_label, bg=BG_CARD2, fg=ACCENT).pack()
        bind_tree(re_btn, "<Button-1>", lambda e: self._run_analysis())
        hover(re_btn, BG_CARD2, BG_CARD)


PLANT_TIPS = {
    "Optimal": [
        ("🌟", ACCENT, "Keep it up!", "Your plant is receiving ideal light. Maintain the current placement for best growth."),
        ("💧", BLUE,   "Watering reminder", "With optimal light, ensure consistent watering every 5–7 days."),
        ("🌡️", YELLOW, "Temperature check", "Plants in optimal light do best between 18–24°C. Avoid cold drafts near windows."),
    ],
    "Low Light": [
        ("⚠️", RED,    "Move to brighter spot", "Current lux is below 300. Try moving the plant closer to a south or east-facing window."),
        ("💡", YELLOW, "Consider grow lights", "If natural light is limited, a full-spectrum LED grow light can supplement effectively."),
        ("🌿", ACCENT, "Choose shade-tolerant species", "If relocation isn't possible, consider a snake plant, pothos, or ZZ plant."),
    ],
    "High": [
        ("🔆", YELLOW, "Reduce direct sunlight", "Readings above 800 lux can cause leaf burn. Use a sheer curtain to diffuse the light."),
        ("💧", BLUE,   "Increase watering frequency", "High light increases evaporation. Check soil moisture daily and water more frequently."),
        ("🌵", ACCENT, "Consider sun-loving species", "If you can't reduce light, consider cacti or succulents that thrive in intense light."),
    ],
}

class RecommendationsPage(BasePage):
    def _build(self):
        outer = tk.Frame(self, bg=BG_MAIN)
        outer.pack(fill="both", expand=True, padx=22, pady=18)
        tk.Label(outer, text="💡  Recommendations", font=("Segoe UI", 16, "bold"),
                 bg=BG_MAIN, fg=TEXT_PRI).pack(anchor="w")
        tk.Label(outer, text="Personalised tips based on your current light readings.",
                 font=self.f_small, bg=BG_MAIN, fg=TEXT_SEC).pack(anchor="w", pady=(0, 16))

        sel_row = tk.Frame(outer, bg=BG_MAIN)
        sel_row.pack(fill="x", pady=(0, 16))
        tk.Label(sel_row, text="Current status:", font=self.f_body,
                 bg=BG_MAIN, fg=TEXT_SEC).pack(side="left", padx=(0, 10))
        self._status_var = tk.StringVar(value="Optimal")
        self._sel_btns   = {}
        for status, color in [("Optimal", ACCENT), ("Low Light", RED), ("High", YELLOW)]:
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

        gauge_frame = tk.Frame(outer, bg=BG_CARD, padx=16, pady=12)
        gauge_frame.pack(fill="x", pady=(0, 16))
        gauge_top = tk.Frame(gauge_frame, bg=BG_CARD)
        gauge_top.pack(fill="x")
        tk.Label(gauge_top, text="Light Level Scale", font=self.f_label,
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

        tk.Frame(outer, bg=BORDER, height=1).pack(fill="x", pady=(12, 8))
        tk.Label(outer, text="General Best Practices", font=self.f_title,
                 bg=BG_MAIN, fg=TEXT_PRI).pack(anchor="w", pady=(0, 8))
        for icon, tip in [
            ("🔄", "Rotate your plants every 2 weeks for even light exposure on all sides."),
            ("📅", "Keep a watering schedule and adjust based on light levels and season."),
            ("🧹", "Wipe leaves monthly — dust blocks light absorption by up to 30%."),
            ("📊", "Use Plant Monitor's History page to spot weekly trends and adjust placement."),
        ]:
            row = tk.Frame(outer, bg=BG_CARD, padx=14, pady=10)
            row.pack(fill="x", pady=(0, 6))
            tk.Label(row, text=icon, font=("Segoe UI", 13), bg=BG_CARD).pack(side="left", padx=(0, 12))
            tk.Label(row, text=tip, font=self.f_body, bg=BG_CARD, fg=TEXT_PRI,
                     wraplength=560, justify="left").pack(side="left", fill="x")

        self._render_tips()

    def _render_tips(self):
        status = self._status_var.get()
        for s, (btn, lbl, color) in self._sel_btns.items():
            active = (s == status)
            btn.configure(bg=color if active else BG_CARD)
            lbl.configure(bg=color if active else BG_CARD, fg=BG_MAIN if active else color)
        lux_map = {"Optimal": 550, "Low Light": 180, "High": 880}
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
        for w_ in self._tips_frame.winfo_children():
            w_.destroy()
        color_map = {"Optimal": ACCENT, "Low Light": RED, "High": YELLOW}
        badge_color = color_map[status]
        badge_row = tk.Frame(self._tips_frame, bg=BG_MAIN)
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


class SettingsPage(BasePage):
    def _build(self):
        pad = tk.Frame(self, bg=BG_MAIN)
        pad.pack(fill="both", expand=True, padx=22, pady=18)
        tk.Label(pad, text="⚙️  Settings", font=("Segoe UI", 16, "bold"),
                 bg=BG_MAIN, fg=TEXT_PRI).pack(anchor="w")
        tk.Label(pad, text="Manage your preferences and thresholds.",
                 font=self.f_small, bg=BG_MAIN, fg=TEXT_SEC).pack(anchor="w", pady=(0, 24))
        sections = [
            ("Notifications", [("Alert on Low Light", True), ("Alert on High Light", True), ("Daily Summary Email", False)]),
            ("Thresholds",    [("Low Light Threshold", False), ("Optimal Min", False), ("Optimal Max", False)]),
            ("Display",       [("Dark Mode", True), ("Show Grid on Chart", True), ("Show Data Points", False)]),
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
                toggle_lbl = tk.Label(row, text="● ON " if default_on else " OFF ●",
                                      font=self.f_small, bg=BG_CARD2,
                                      fg=ACCENT if default_on else TEXT_MUT, padx=8, pady=3, cursor="hand2")
                toggle_lbl.pack(side="right")
                def make_toggle(v=var, lbl=toggle_lbl):
                    def toggle(e):
                        v.set(not v.get())
                        lbl.config(text="● ON " if v.get() else " OFF ●",
                                   fg=ACCENT if v.get() else TEXT_MUT)
                    return toggle
                toggle_lbl.bind("<Button-1>", make_toggle())
                if i < len(items) - 1:
                    tk.Frame(card, bg=BORDER, height=1).pack(fill="x")
        save_btn = tk.Frame(pad, bg=ACCENT, cursor="hand2", padx=20, pady=8)
        save_btn.pack(anchor="e", pady=(8, 0))
        tk.Label(save_btn, text="Save Settings", font=self.f_label, bg=ACCENT, fg=BG_MAIN).pack()
        bind_tree(save_btn, "<Button-1>", lambda e: messagebox.showinfo("Settings", "Settings saved successfully!"))
        hover(save_btn, ACCENT, "#00c98a")


NAV_ORDER = [
    ("📊", "Dashboard"),
    ("🔔", "Alerts"),
    ("🪴", "My Plants"),
    ("📅", "History"),
    ("🔬", "Detection"),
    ("💡", "Recommendations"),
    ("⚙️", "Settings"),
]
PAGE_CLASSES = {
    "Dashboard":       DashboardPage,
    "Alerts":          AlertsPage,
    "My Plants":       MyPlantsPage,
    "History":         HistoryPage,
    "Detection":       DetectionPage,
    "Recommendations": RecommendationsPage,
    "Settings":        SettingsPage,
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
        tk.Label(logout_row, text="Log Out", font=self.f_body, bg=BG_CARD2, fg=RED).pack(side="left")
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
        pad = tk.Frame(parent, bg=BG_SIDE)
        pad.pack(fill="both", expand=True, padx=12, pady=14)
        banner = tk.Frame(pad, bg="#1a2e1a", height=90)
        banner.pack(fill="x", pady=(0, 12))
        banner.pack_propagate(False)
        tk.Label(banner, text="Recent Alerts", font=self.f_title, bg="#1a2e1a", fg=TEXT_PRI).place(x=10, y=12)
        tk.Label(banner, text="🌿", font=("Segoe UI", 30), bg="#1a2e1a").place(relx=0.75, rely=0.5, anchor="center")
        ref_btn = tk.Frame(pad, bg=BG_CARD, cursor="hand2")
        ref_btn.pack(fill="x", pady=(0, 14))
        ref_inner = tk.Frame(ref_btn, bg=BG_CARD)
        ref_inner.pack(pady=8)
        tk.Label(ref_inner, text="↻  Refresh Data", font=self.f_body,
                 bg=BG_CARD, fg=TEXT_PRI, cursor="hand2").pack(side="left")
        bind_tree(ref_btn, "<Button-1>", lambda e: self._do_refresh())
        hover(ref_btn, BG_CARD, BG_CARD2)
        hdr = tk.Frame(pad, bg=BG_SIDE, cursor="hand2")
        hdr.pack(fill="x", pady=(0, 8))
        tk.Label(hdr, text="Recent Alerts", font=self.f_title, bg=BG_SIDE, fg=TEXT_PRI).pack(side="left")
        tk.Label(hdr, text="≡", font=("Segoe UI", 14), bg=BG_SIDE, fg=TEXT_SEC).pack(side="right")
        bind_tree(hdr, "<Button-1>", lambda e: self._show_page("Alerts"))
        for icon, color, title, time_str, desc, val in ALERTS_DATA:
            self._alert_card(pad, icon, color, title, time_str, desc, val)
        va = tk.Frame(pad, bg=BG_SIDE, cursor="hand2")
        va.pack(fill="x", pady=(8, 0))
        va_lbl = tk.Label(va, text="View All  ›", font=self.f_body, bg=BG_SIDE, fg=ACCENT, cursor="hand2")
        va_lbl.pack(anchor="e")
        bind_tree(va, "<Button-1>", lambda e: self._show_page("Alerts"))

    def _alert_card(self, parent, icon, color, title, time_str, desc, val):
        card = tk.Frame(parent, bg=BG_CARD, padx=12, pady=10, cursor="hand2")
        card.pack(fill="x", pady=(0, 6))
        tk.Label(card, text=icon, font=("Segoe UI", 10), bg=BG_CARD, fg=color
                 ).grid(row=0, column=0, sticky="n", padx=(0, 8))
        hdr = tk.Frame(card, bg=BG_CARD)
        hdr.grid(row=0, column=1, sticky="ew")
        tk.Label(hdr, text=title,    font=self.f_label, bg=BG_CARD, fg=TEXT_PRI).pack(side="left")
        tk.Label(hdr, text=time_str, font=self.f_small, bg=BG_CARD, fg=TEXT_SEC).pack(side="right")
        tk.Label(card, text=desc, font=self.f_small, bg=BG_CARD, fg=TEXT_SEC, justify="left"
                 ).grid(row=1, column=1, sticky="w")
        val_row = tk.Frame(card, bg=BG_CARD)
        val_row.grid(row=2, column=1, sticky="e")
        tk.Label(val_row, text=f"▐ {val}", font=self.f_small, bg=BG_CARD, fg=color).pack(side="right")
        card.grid_columnconfigure(1, weight=1)
        bind_tree(card, "<Button-1>", lambda e: self._show_page("Alerts"))
        hover(card, BG_CARD, BG_CARD2)

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

    def _do_logout(self):
        if messagebox.askyesno("Log Out", "Are you sure you want to log out?"):
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
