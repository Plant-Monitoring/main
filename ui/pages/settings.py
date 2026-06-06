import tkinter as tk
from tkinter import messagebox

from .theme import (
    BG_MAIN, BG_CARD, BG_GLASS, ACCENT, ACCENT2, BLUE, RED, PURPLE, TEAL, ORANGE, TEXT_PRI,
    TEXT_SEC, TEXT_MUT, BORDER, BORDER2, ON_ACCENT, USERS, bind_tree, hover, GreenSlider,
    BasePage
)

class SettingsPage(BasePage):
    def _build(self):
        # Scrollable outer
        outer_canvas = tk.Canvas(self, bg=BG_MAIN, highlightthickness=0)
        scrollbar = tk.Scrollbar(self, orient="vertical", command=outer_canvas.yview)
        outer_canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        outer_canvas.pack(side="left", fill="both", expand=True)
        pad = tk.Frame(outer_canvas, bg=BG_MAIN)
        win_id = outer_canvas.create_window((0,0), window=pad, anchor="nw")
        pad.bind("<Configure>", lambda e: outer_canvas.configure(scrollregion=outer_canvas.bbox("all")))
        outer_canvas.bind("<Configure>", lambda e: outer_canvas.itemconfig(win_id, width=e.width))

        # Header
        hdr = tk.Frame(pad, bg=BG_GLASS, padx=24, pady=20)
        hdr.pack(fill="x", padx=22, pady=(18,0))
        tk.Frame(hdr, bg=PURPLE, width=4).pack(side="left", fill="y", padx=(0,16))
        hdr_txt = tk.Frame(hdr, bg=BG_GLASS); hdr_txt.pack(side="left")
        tk.Label(hdr_txt, text="Settings", font=("Segoe UI",18,"bold"), bg=BG_GLASS, fg=TEXT_PRI).pack(anchor="w")
        tk.Label(hdr_txt, text="Manage display preferences and application behaviour.",
                 font=self.f_small, bg=BG_GLASS, fg=TEXT_SEC).pack(anchor="w")
        settings_icon = tk.Label(hdr, text="⚙", font=("Segoe UI",28), bg=BG_GLASS, fg=PURPLE)
        settings_icon.pack(side="right", padx=(0,8))

        content = tk.Frame(pad, bg=BG_MAIN)
        content.pack(fill="both", expand=True, padx=22, pady=(16,22))

        def section(parent, title, color=PURPLE):
            hdr_row = tk.Frame(parent, bg=BG_MAIN); hdr_row.pack(fill="x", pady=(18,8))
            tk.Frame(hdr_row, bg=color, width=4, height=16).pack(side="left")
            tk.Label(hdr_row, text=f"  {title}", font=self.f_title, bg=BG_MAIN, fg=TEXT_PRI).pack(side="left")
            tk.Frame(hdr_row, bg=BORDER, height=1).pack(side="left", fill="x", expand=True, pady=8)
            card = tk.Frame(parent, bg=BG_CARD, padx=0, pady=0)
            card.pack(fill="x")
            tk.Frame(card, bg=color, height=3).pack(fill="x")
            return tk.Frame(card, bg=BG_CARD, padx=20, pady=8)

        def toggle_item(parent, label, desc, default_on, is_last=False):
            row = tk.Frame(parent, bg=BG_CARD); row.pack(fill="x", pady=(8,0))
            txt = tk.Frame(row, bg=BG_CARD); txt.pack(side="left", fill="both", expand=True)
            tk.Label(txt, text=label, font=self.f_body, bg=BG_CARD, fg=TEXT_PRI).pack(anchor="w")
            if desc:
                tk.Label(txt, text=desc, font=("Segoe UI",7), bg=BG_CARD, fg=TEXT_MUT).pack(anchor="w")
            var = tk.BooleanVar(value=default_on)
            toggle_container = tk.Frame(row, bg=BG_GLASS, width=58, height=26)
            toggle_container.pack(side="right", padx=(12,0))
            toggle_container.pack_propagate(False)
            toggle_canvas = tk.Canvas(toggle_container, bg=BG_GLASS, width=58, height=26,
                                      highlightthickness=0)
            toggle_canvas.pack()

            def draw_toggle(on):
                toggle_canvas.delete("all")
                track_color = ACCENT2 if on else BORDER2
                toggle_canvas.create_rectangle(0, 4, 56, 22, fill=track_color, outline="", tags="track")
                kx = 36 if on else 8
                kcolor = ACCENT if on else TEXT_MUT
                toggle_canvas.create_oval(kx-8, 2, kx+8, 24, fill=kcolor, outline=BG_GLASS, width=2)

            draw_toggle(default_on)

            def toggle(e):
                var.set(not var.get()); draw_toggle(var.get())

            toggle_canvas.bind("<Button-1>", toggle)

            if not is_last:
                tk.Frame(parent, bg=BORDER, height=1).pack(fill="x", pady=(8,0))
            return var

        # Display section 
        display_inner = section(content, "Display", PURPLE)
        display_inner.pack(fill="x")
        self._dark_var    = toggle_item(display_inner, "Dark mode",             "Keep dark theme active",        True)
        self._grid_var    = toggle_item(display_inner, "Show chart grid",       "Gridlines on all charts",       True)
        self._points_var  = toggle_item(display_inner, "Show data points",      "Scatter markers on line charts",False)
        self._compact_var = toggle_item(display_inner, "Compact sidebar",       "Collapse labels in navigation", False, is_last=True)

        # Data section 
        data_inner = section(content, "Data & History", BLUE)
        data_inner.pack(fill="x")
        ret_row = tk.Frame(data_inner, bg=BG_CARD); ret_row.pack(fill="x", pady=(8,0))
        tk.Label(ret_row, text="History retention", font=self.f_body, bg=BG_CARD, fg=TEXT_PRI).pack(anchor="w")
        tk.Label(ret_row, text="Number of days to keep loaded file records", font=("Segoe UI",7), bg=BG_CARD, fg=TEXT_MUT).pack(anchor="w")
        self._retention_var = tk.DoubleVar(value=10)
        ret_slider_row = tk.Frame(data_inner, bg=BG_CARD); ret_slider_row.pack(fill="x", pady=(4,0))
        ret_header = tk.Frame(ret_slider_row, bg=BG_CARD); ret_header.pack(fill="x")
        tk.Label(ret_header, text="Days", font=("Segoe UI",7), bg=BG_CARD, fg=TEXT_SEC).pack(side="left")
        tk.Label(ret_header, textvariable=self._retention_var, font=("Segoe UI",9,"bold"),
                 bg=BG_CARD, fg=BLUE, width=4).pack(side="right")
        GreenSlider(ret_slider_row, from_=1, to=30, variable=self._retention_var,
                    resolution=1, length=260).pack(fill="x")
        tk.Frame(data_inner, bg=BORDER, height=1).pack(fill="x", pady=(8,0))

        self._autosave_var = toggle_item(data_inner, "Auto-save history on file load",
                                         "Automatically append each loaded file to history", True, is_last=True)

        # CNN / Model section 
        cnn_inner = section(content, "CNN Model", TEAL)
        cnn_inner.pack(fill="x")
        self._gpu_var     = toggle_item(cnn_inner, "Use GPU if available", "TensorFlow will use CUDA if detected", False)
        self._fp16_var    = toggle_item(cnn_inner, "FP16 inference",       "Faster inference with reduced precision", False)
        self._verbose_var = toggle_item(cnn_inner, "Verbose CNN output",   "Show model logs in terminal", False, is_last=True)

        # Growth API section 
        api_inner = section(content, "Growth API", ORANGE)
        api_inner.pack(fill="x")
        url_row = tk.Frame(api_inner, bg=BG_CARD); url_row.pack(fill="x", pady=(8,0))
        tk.Label(url_row, text="Default API endpoint", font=self.f_body, bg=BG_CARD, fg=TEXT_PRI).pack(anchor="w")
        tk.Label(url_row, text="Used by the Growth Prediction page", font=("Segoe UI",7), bg=BG_CARD, fg=TEXT_MUT).pack(anchor="w")
        self._api_url_var = tk.StringVar(value="http://localhost:8000/fwd")
        url_frame = tk.Frame(api_inner, bg=BG_GLASS); url_frame.pack(fill="x", pady=(6,0))
        tk.Frame(url_frame, bg=ORANGE, width=3).pack(side="left", fill="y")
        api_entry = tk.Entry(url_frame, textvariable=self._api_url_var,
                             bg=BG_GLASS, fg=TEXT_PRI, insertbackground=ORANGE,
                             relief="flat", font=("Segoe UI",9))
        api_entry.pack(side="left", fill="x", expand=True, ipady=7, padx=(8,8))
        tk.Frame(api_inner, bg=BORDER, height=1).pack(fill="x", pady=(8,0))
        self._timeout_var = toggle_item(api_inner, "Strict API timeout", "Fail fast after 10 seconds", True, is_last=True)

        # Account section
        acc_inner = section(content, "Account", RED)
        acc_inner.pack(fill="x")
        acc_row = tk.Frame(acc_inner, bg=BG_CARD); acc_row.pack(fill="x", pady=(8,14))
        username = self.app.username
        avatar = tk.Label(acc_row, text=username[:2].upper(),
                          font=("Segoe UI",12,"bold"), bg="#3d5a80", fg="white",
                          width=3, padx=6, pady=6)
        avatar.pack(side="left", padx=(0,14))
        acc_info = tk.Frame(acc_row, bg=BG_CARD); acc_info.pack(side="left", fill="both", expand=True)
        tk.Label(acc_info, text=username, font=("Segoe UI",11,"bold"), bg=BG_CARD, fg=TEXT_PRI).pack(anchor="w")
        tk.Label(acc_info, text="Plant Enthusiast", font=("Segoe UI",8), bg=BG_CARD, fg=ACCENT).pack(anchor="w")
        tk.Label(acc_info, text=f"{len(USERS)} account(s) registered in this session",
                 font=("Segoe UI",7), bg=BG_CARD, fg=TEXT_MUT).pack(anchor="w")

        # Save button 
        save_row = tk.Frame(content, bg=BG_MAIN); save_row.pack(anchor="e", pady=(20,0))
        save_btn = tk.Frame(save_row, bg=PURPLE, cursor="hand2", padx=24, pady=10)
        save_btn.pack(side="right")
        tk.Label(save_btn, text="Save Settings", font=("Segoe UI",10,"bold"),
                 bg=PURPLE, fg=ON_ACCENT).pack()
        bind_tree(save_btn, "<Button-1>",
                  lambda e: messagebox.showinfo("Settings", "Settings saved successfully!"))
        hover(save_btn, PURPLE, "#8b6ee8")