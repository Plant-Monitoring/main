import os
import sys

# Make the project root (parent of ui/) importable so `database` and `models` resolve.
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

import tkinter as tk
from tkinter import messagebox
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt

# Shared theme (colours + helpers)
from pages.theme import (
    BG_MAIN, BG_SIDE, BG_CARD, BG_CARD2, BG_GLASS,
    ACCENT, ACCENT2, BLUE, BLUE2, RED, YELLOW, PURPLE, TEAL, ORANGE,
    TEXT_PRI, TEXT_SEC, TEXT_MUT, BORDER, BORDER2, GLOW,
    bind_tree, hover,
)

# Pages
from pages.auth import AuthWindow
from pages.dashboard import DashboardPage
from pages.my_plants import MyPlantsPage
from pages.history import HistoryPage
from pages.detection import DetectionPage
from pages.recommendation import RecommendationSystemPage
from pages.growth import GrowthPage
from pages.settings import SettingsPage

# Navigation
NAV_ORDER = [
    ("📊", "Dashboard"),
    ("🪴", "My Plants"),
    ("📅", "History"),
    ("🔬", "Detection"),
    ("💡", "Recommendation"),
    ("📈", "Growth"),
    ("⚙", "Settings"),
]
PAGE_CLASSES = {
    "Dashboard":      DashboardPage,
    "My Plants":      MyPlantsPage,
    "History":        HistoryPage,
    "Detection":      DetectionPage,
    "Recommendation": RecommendationSystemPage,
    "Growth":         GrowthPage,
    "Settings":       SettingsPage,
}


# Main app window
class PlantMonitor(tk.Tk):
    def __init__(self, username="Anastasija"):
        super().__init__()
        self.username = username
        self.title("Plant Monitor")
        self.geometry("1150x700")
        self.configure(bg=BG_MAIN)
        self.resizable(True, True)
        self._is_fullscreen = False

        self.f_title = ("Segoe UI",13,"bold")
        self.f_big   = ("Segoe UI",24,"bold")
        self.f_body  = ("Segoe UI",9)
        self.f_small = ("Segoe UI",8)
        self.f_label = ("Segoe UI",9,"bold")

        self._nav_buttons  = []
        self._pages        = {}
        self._current_page = None

        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.bind("<F11>", lambda e: self._toggle_fullscreen())

        self._build_shell()
        self._register_pages()
        self._show_page("Dashboard")

    def _on_close(self):
        plt.close("all"); self.destroy(); os._exit(0)

    def _toggle_fullscreen(self, event=None):
        self._is_fullscreen = not self._is_fullscreen
        self.attributes("-fullscreen", self._is_fullscreen)
        self._fs_btn_lbl.config(text="⊡" if self._is_fullscreen else "⛶")

    def _build_shell(self):
        self.sidebar = tk.Frame(self, bg=BG_SIDE, width=220)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)
        self._build_sidebar(self.sidebar)
        self.content_area = tk.Frame(self, bg=BG_MAIN)
        self.content_area.pack(side="left", fill="both", expand=True)
        right = tk.Frame(self, bg=BG_SIDE, width=230)
        right.pack(side="right", fill="y")
        right.pack_propagate(False)
        self._build_right(right)

    def _build_sidebar(self, parent):
        # Logo row
        logo_row = tk.Frame(parent, bg=BG_SIDE)
        logo_row.pack(fill="x", padx=10, pady=(16,10))
        logo_inner = tk.Frame(logo_row, bg=BG_GLASS, padx=10, pady=8)
        logo_inner.pack(side="left", fill="x", expand=True)
        tk.Label(logo_inner, text="🌿", font=("Segoe UI",14), bg=BG_GLASS, fg=ACCENT).pack(side="left")
        tk.Label(logo_inner, text=" Plant Monitor", font=("Segoe UI",11,"bold"),
                 bg=BG_GLASS, fg=TEXT_PRI).pack(side="left")
        fs_btn = tk.Frame(logo_row, bg=BG_CARD2, cursor="hand2", padx=6, pady=6)
        fs_btn.pack(side="right", padx=(6,0))
        self._fs_btn_lbl = tk.Label(fs_btn, text="⛶", font=("Segoe UI",11),
                                     bg=BG_CARD2, fg=TEXT_SEC, cursor="hand2")
        self._fs_btn_lbl.pack()
        bind_tree(fs_btn, "<Button-1>", lambda e: self._toggle_fullscreen())
        hover(fs_btn, BG_CARD2, BG_CARD)

        # Section divider
        divider_row = tk.Frame(parent, bg=BG_SIDE)
        divider_row.pack(fill="x", padx=12, pady=(2,8))
        tk.Frame(divider_row, bg=BORDER, height=1).pack(fill="x")

        # Nav label
        tk.Label(parent, text="NAVIGATION", font=("Segoe UI",7,"bold"),
                 bg=BG_SIDE, fg=TEXT_MUT).pack(anchor="w", padx=16, pady=(0,4))

        for icon, label in NAV_ORDER:
            self._nav_btn(parent, icon, label)

        tk.Frame(parent, bg=BG_SIDE).pack(expand=True)

        # Divider
        tk.Frame(parent, bg=BORDER, height=1).pack(fill="x", padx=12, pady=4)

        # Sign out
        logout_btn = tk.Frame(parent, bg=BG_SIDE, cursor="hand2")
        logout_btn.pack(fill="x", padx=8, pady=(0,2))
        logout_inner = tk.Frame(logout_btn, bg=BG_SIDE)
        logout_inner.pack(pady=6, padx=12, anchor="w")
        tk.Label(logout_inner, text="⏻", font=("Segoe UI",10), bg=BG_SIDE, fg=RED).pack(side="left", padx=(0,8))
        tk.Label(logout_inner, text="Sign Out", font=self.f_body, bg=BG_SIDE, fg=RED).pack(side="left")
        bind_tree(logout_btn, "<Button-1>", lambda e: self._do_logout())
        hover(logout_btn, BG_SIDE, "#1e1a1a")

        # Profile
        prof = tk.Frame(parent, bg=BG_GLASS, cursor="hand2")
        prof.pack(fill="x", padx=8, pady=(4,14))
        prof_inner = tk.Frame(prof, bg=BG_GLASS)
        prof_inner.pack(padx=12, pady=10, anchor="w", fill="x")
        avatar = tk.Label(prof_inner, text=self.username[:2].upper(),
                          font=("Segoe UI",9,"bold"), bg="#3d5a80", fg="white",
                          width=3, padx=4, pady=4)
        avatar.pack(side="left")
        info = tk.Frame(prof_inner, bg=BG_GLASS); info.pack(side="left", padx=(8,0))
        tk.Label(info, text=self.username, font=self.f_body, bg=BG_GLASS, fg=TEXT_PRI).pack(anchor="w")
        tk.Label(info, text="Plant Enthusiast", font=("Segoe UI",7), bg=BG_GLASS, fg=ACCENT).pack(anchor="w")
        bind_tree(prof, "<Button-1>", lambda e: self._show_page("Settings"))
        hover(prof, BG_GLASS, BG_CARD)

    def _nav_btn(self, parent, icon, label):
        is_active = not self._nav_buttons
        bg_c = BG_CARD  if is_active else BG_SIDE
        fg_c = TEXT_PRI if is_active else TEXT_SEC

        row = tk.Frame(parent, bg=bg_c, cursor="hand2")
        row.pack(fill="x", padx=8, pady=1)

        bar = tk.Frame(row, bg=ACCENT if is_active else bg_c, width=3)
        bar.pack(side="left", fill="y")

        icon_lbl = tk.Label(row, text=icon, font=("Segoe UI",12),
                            bg=bg_c, fg=fg_c, anchor="w", pady=9, padx=8)
        icon_lbl.pack(side="left")
        lbl = tk.Label(row, text=label, font=self.f_body,
                       bg=bg_c, fg=fg_c, anchor="w", pady=9, padx=2)
        lbl.pack(fill="x")

        right_bar = tk.Frame(row, bg=GLOW if is_active else bg_c, width=3)
        right_bar.pack(side="right", fill="y")

        entry = {"row":row, "bar":bar, "lbl":lbl, "icon":icon_lbl, "right":right_bar, "label":label}
        self._nav_buttons.append(entry)

        def on_click(e, entry=entry):
            for b in self._nav_buttons:
                b["row"].configure(bg=BG_SIDE)
                b["bar"].configure(bg=BG_SIDE)
                b["right"].configure(bg=BG_SIDE)
                b["lbl"].configure(bg=BG_SIDE, fg=TEXT_SEC)
                b["icon"].configure(bg=BG_SIDE, fg=TEXT_SEC)
            entry["row"].configure(bg=BG_CARD)
            entry["bar"].configure(bg=ACCENT)
            entry["right"].configure(bg=GLOW)
            entry["lbl"].configure(bg=BG_CARD, fg=TEXT_PRI)
            entry["icon"].configure(bg=BG_CARD, fg=TEXT_PRI)
            self._show_page(entry["label"])

        row.bind("<Button-1>", on_click)
        lbl.bind("<Button-1>", on_click)
        bar.bind("<Button-1>", on_click)
        icon_lbl.bind("<Button-1>", on_click)
        right_bar.bind("<Button-1>", on_click)
        hover(row, bg_c, BG_CARD2)

    def _build_right(self, parent):
        pad = tk.Frame(parent, bg=BG_SIDE)
        pad.pack(fill="both", expand=True, padx=12, pady=14)

        # Top accent banner
        banner = tk.Frame(pad, bg=BG_GLASS, pady=0)
        banner.pack(fill="x", pady=(0,16))
        tk.Frame(banner, bg=ACCENT, height=3).pack(fill="x")
        banner_inner = tk.Frame(banner, bg=BG_GLASS, padx=14, pady=14)
        banner_inner.pack(fill="x")
        tk.Label(banner_inner, text="Plant Monitor", font=("Segoe UI",11,"bold"),
                 bg=BG_GLASS, fg=TEXT_PRI).pack(anchor="w")
        tk.Label(banner_inner, text="AI-powered care tracking", font=("Segoe UI",7),
                 bg=BG_GLASS, fg=ACCENT).pack(anchor="w")
        tk.Label(banner_inner, text="🌿", font=("Segoe UI",28), bg=BG_GLASS).pack(anchor="e")

        # Quick links
        tk.Label(pad, text="QUICK ACTIONS", font=("Segoe UI",7,"bold"),
                 bg=BG_SIDE, fg=TEXT_MUT).pack(anchor="w", pady=(0,6))

        for icon_text, label, page, color in [
            ("🪴", "My Plants",      "My Plants",      ACCENT),
            ("🔬", "Detect Health",  "Detection",      BLUE),
            ("💡", "Get Recommendation", "Recommendation", YELLOW),
            ("📅", "View History",   "History",        TEAL),
        ]:
            btn = tk.Frame(pad, bg=BG_GLASS, cursor="hand2")
            btn.pack(fill="x", pady=(0,4))
            tk.Frame(btn, bg=color, width=3).pack(side="left", fill="y")
            inner = tk.Frame(btn, bg=BG_GLASS, padx=10, pady=7)
            inner.pack(side="left", fill="x", expand=True)
            tk.Label(inner, text=icon_text, font=("Segoe UI",11), bg=BG_GLASS).pack(side="left", padx=(0,6))
            tk.Label(inner, text=label, font=self.f_small, bg=BG_GLASS, fg=TEXT_PRI).pack(side="left")
            tk.Label(inner, text="→", font=("Segoe UI",10), bg=BG_GLASS, fg=color).pack(side="right")
            bind_tree(btn, "<Button-1>", lambda e, p=page: self._show_page(p))
            hover(btn, BG_GLASS, BG_CARD)

        tk.Frame(pad, bg=BORDER, height=1).pack(fill="x", pady=(12,12))

        # System status card
        tk.Label(pad, text="SYSTEM", font=("Segoe UI",7,"bold"),
                 bg=BG_SIDE, fg=TEXT_MUT).pack(anchor="w", pady=(0,6))
        status_card = tk.Frame(pad, bg=BG_GLASS, padx=12, pady=10)
        status_card.pack(fill="x")
        for dot_color, label in [(ACCENT,"CNN Engine Ready"),(BLUE,"Data Layer Active"),(ORANGE,"Growth API Offline")]:
            row = tk.Frame(status_card, bg=BG_GLASS); row.pack(fill="x", pady=2)
            tk.Label(row, text="⬤", font=("Segoe UI",8), bg=BG_GLASS, fg=dot_color).pack(side="left")
            tk.Label(row, text=f"  {label}", font=("Segoe UI",7), bg=BG_GLASS, fg=TEXT_SEC).pack(side="left")

    def _register_pages(self):
        for name, cls in PAGE_CLASSES.items():
            page = cls(self.content_area, self)
            page.place(relx=0, rely=0, relwidth=1, relheight=1)
            self._pages[name] = page

    def _show_page(self, name):
        if self._current_page: self._current_page.lower()
        page = self._pages.get(name)
        if page:
            page.lift()
            self._current_page = page
        for entry in self._nav_buttons:
            match = entry["label"] == name
            entry["row"].configure(bg=BG_CARD if match else BG_SIDE)
            entry["bar"].configure(bg=ACCENT  if match else BG_SIDE)
            entry["right"].configure(bg=GLOW  if match else BG_SIDE)
            entry["lbl"].configure(bg=BG_CARD if match else BG_SIDE,
                                   fg=TEXT_PRI if match else TEXT_SEC)
            entry["icon"].configure(bg=BG_CARD if match else BG_SIDE,
                                    fg=TEXT_PRI if match else TEXT_SEC)

    def _do_logout(self):
        if messagebox.askyesno("Sign Out", "Are you sure you want to sign out?"):
            plt.close("all")
            self.destroy()
            auth = AuthWindow()
            auth.mainloop()
            if auth.logged_in_user:
                app = PlantMonitor(auth.logged_in_user)
                app.mainloop()

# Entry point 
if __name__ == "__main__":
    auth = AuthWindow()
    auth.mainloop()
    if auth.logged_in_user:
        app = PlantMonitor(auth.logged_in_user)
        app.mainloop()