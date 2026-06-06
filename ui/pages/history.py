import datetime
import tkinter as tk

import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from .theme import (
    BG_MAIN, BG_SIDE, BG_CARD, BG_GLASS, ACCENT, BLUE, RED, TEAL, ORANGE, TEXT_PRI,
    TEXT_SEC, TEXT_MUT, BORDER, bind_tree, hover, BasePage, _load_history_db,
    _save_history_db, _prune_old_entries
)


class HistoryPage(BasePage):
    def _build(self):
        self._entries       = []
        self._chart_canvas  = None
        self._selected_idx  = None

        outer = tk.Frame(self, bg=BG_MAIN)
        outer.pack(fill="both", expand=True)

        self._left_pane = tk.Frame(outer, bg=BG_SIDE, width=260)
        self._left_pane.pack(side="left", fill="y", padx=0, pady=0)
        self._left_pane.pack_propagate(False)

        self._right_pane = tk.Frame(outer, bg=BG_MAIN)
        self._right_pane.pack(side="left", fill="both", expand=True, padx=0)

        self._build_left()
        self._build_right()
        self.refresh()

    def _build_left(self):
        pad = tk.Frame(self._left_pane, bg=BG_SIDE)
        pad.pack(fill="both", expand=True, padx=14, pady=18)

        hdr = tk.Frame(pad, bg=BG_SIDE)
        hdr.pack(fill="x", pady=(0,6))
        tk.Label(hdr, text="History", font=("Segoe UI",14,"bold"), bg=BG_SIDE, fg=TEXT_PRI).pack(side="left")
        calendar_lbl = tk.Label(hdr, text="📅", font=("Segoe UI",14), bg=BG_SIDE)
        calendar_lbl.pack(side="left", padx=(4,0))

        tk.Label(pad, text="Last 10 days of loaded files.",
                 font=self.f_small, bg=BG_SIDE, fg=TEXT_SEC).pack(anchor="w", pady=(0,12))

        tk.Frame(pad, bg=BORDER, height=1).pack(fill="x", pady=(0,10))

        list_outer = tk.Frame(pad, bg=BG_SIDE)
        list_outer.pack(fill="both", expand=True)
        self._hist_canvas = tk.Canvas(list_outer, bg=BG_SIDE, highlightthickness=0)
        sb = tk.Scrollbar(list_outer, orient="vertical", command=self._hist_canvas.yview)
        self._hist_canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self._hist_canvas.pack(side="left", fill="both", expand=True)
        self._hist_list = tk.Frame(self._hist_canvas, bg=BG_SIDE)
        self._hist_win  = self._hist_canvas.create_window((0,0), window=self._hist_list, anchor="nw")
        self._hist_list.bind("<Configure>",
            lambda e: self._hist_canvas.configure(scrollregion=self._hist_canvas.bbox("all")))
        self._hist_canvas.bind("<Configure>",
            lambda e: self._hist_canvas.itemconfig(self._hist_win, width=e.width))
        self._hist_canvas.bind("<MouseWheel>",
            lambda e: self._hist_canvas.yview_scroll(-1*(e.delta//120),"units"))

    def _build_right(self):
        self._right_content = tk.Frame(self._right_pane, bg=BG_MAIN)
        self._right_content.pack(fill="both", expand=True, padx=20, pady=18)

    def refresh(self):
        raw = _load_history_db()
        self._entries = _prune_old_entries(raw, days=10)
        _save_history_db(self._entries)
        self._render_list()
        if self._selected_idx is None and self._entries:
            self._select_entry(len(self._entries)-1)
        elif self._selected_idx is not None and self._entries:
            idx = min(self._selected_idx, len(self._entries)-1)
            self._select_entry(idx)
        else:
            self._show_empty_right()

    def _render_list(self):
        for w in self._hist_list.winfo_children(): w.destroy()
        if not self._entries:
            tk.Label(self._hist_list, text="No history yet.\nLoad a file from Dashboard.",
                     font=self.f_small, bg=BG_SIDE, fg=TEXT_MUT,
                     justify="center").pack(pady=30)
            return
        groups: dict[str, list] = {}
        for idx, entry in enumerate(self._entries):
            try:
                dt  = datetime.datetime.fromisoformat(entry["timestamp"])
                key = dt.strftime("%A, %d %b %Y")
            except:
                key = "Unknown date"
            groups.setdefault(key, []).append((idx, entry))

        for date_str, items in reversed(list(groups.items())):
            tk.Label(self._hist_list, text=date_str, font=("Segoe UI",7,"bold"),
                     bg=BG_SIDE, fg=ACCENT, pady=4).pack(anchor="w")
            for idx, entry in reversed(items):
                is_sel = (idx == self._selected_idx)
                bg_c   = BG_CARD if is_sel else BG_GLASS
                row    = tk.Frame(self._hist_list, bg=bg_c, cursor="hand2", padx=0, pady=0)
                row.pack(fill="x", pady=(0,3))
                sel_bar = tk.Frame(row, bg=ACCENT if is_sel else bg_c, width=3)
                sel_bar.pack(side="left", fill="y")
                inner = tk.Frame(row, bg=bg_c, padx=10, pady=8)
                inner.pack(side="left", fill="both", expand=True)
                try:
                    dt  = datetime.datetime.fromisoformat(entry["timestamp"])
                    time_str = dt.strftime("%H:%M")
                except:
                    time_str = ""
                fname = entry.get("filename", "unknown")
                short = fname if len(fname) <= 22 else fname[:19]+"..."
                name_row = tk.Frame(inner, bg=bg_c)
                name_row.pack(anchor="w", fill="x")
                tk.Label(name_row, text=short, font=self.f_small,
                         bg=bg_c, fg=TEXT_PRI if is_sel else TEXT_SEC).pack(side="left")
                tk.Label(name_row, text=time_str, font=("Segoe UI",7),
                         bg=bg_c, fg=ACCENT if is_sel else TEXT_MUT).pack(side="right")
                n_vals = len(entry.get("values",[]))
                tk.Label(inner, text=f"{n_vals:,} values", font=("Segoe UI",7),
                         bg=bg_c, fg=TEXT_MUT).pack(anchor="w")
                bind_tree(row, "<Button-1>", lambda e, i=idx: self._select_entry(i))
                hover(row, bg_c, BG_CARD)

    def _select_entry(self, idx):
        self._selected_idx = idx
        self._render_list()
        self._show_entry_chart(self._entries[idx])

    def _show_empty_right(self):
        for w in self._right_content.winfo_children(): w.destroy()
        container = tk.Frame(self._right_content, bg=BG_CARD, padx=20, pady=40)
        container.pack(fill="both", expand=True)
        tk.Label(container, text="📅", font=("Segoe UI",40), bg=BG_CARD).pack(pady=(20,8))
        tk.Label(container, text="Select a file from the list to view its chart.",
                 font=self.f_body, bg=BG_CARD, fg=TEXT_SEC, justify="center").pack()

    def _show_entry_chart(self, entry):
        for w in self._right_content.winfo_children(): w.destroy()
        if self._chart_canvas:
            try:
                self._chart_canvas.get_tk_widget().destroy()
                plt.close("all")
            except: pass
            self._chart_canvas = None

        data   = entry.get("values", [])
        fname  = entry.get("filename", "")
        try:
            dt  = datetime.datetime.fromisoformat(entry["timestamp"])
            dt_str = dt.strftime("%d %b %Y at %H:%M")
        except:
            dt_str = ""

        hdr = tk.Frame(self._right_content, bg=BG_GLASS, padx=16, pady=14)
        hdr.pack(fill="x", pady=(0,12))
        tk.Label(hdr, text=fname, font=("Segoe UI",12,"bold"), bg=BG_GLASS, fg=TEXT_PRI).pack(anchor="w")
        tk.Label(hdr, text=dt_str, font=self.f_small, bg=BG_GLASS, fg=ACCENT).pack(anchor="w")

        if not data:
            tk.Label(self._right_content, text="No data to display.", font=self.f_body,
                     bg=BG_MAIN, fg=TEXT_MUT).pack(pady=20); return

        stats_row = tk.Frame(self._right_content, bg=BG_MAIN)
        stats_row.pack(fill="x", pady=(0,10))
        avg_v = sum(data)/len(data)
        for label, val, color in [("AVG", f"{avg_v:.0f} lx", BLUE),
                                   ("MAX", f"{max(data):.0f} lx", ACCENT),
                                   ("MIN", f"{min(data):.0f} lx", ORANGE),
                                   ("SAMPLES", f"{len(data):,}", TEXT_SEC)]:
            sc = tk.Frame(stats_row, bg=BG_CARD, padx=0, pady=0)
            sc.pack(side="left", padx=(0,8), fill="x", expand=True)
            tk.Frame(sc, bg=color, height=3).pack(fill="x")
            inner = tk.Frame(sc, bg=BG_CARD, padx=12, pady=8)
            inner.pack(fill="both")
            tk.Label(inner, text=label, font=("Segoe UI",7,"bold"), bg=BG_CARD, fg=color).pack(anchor="w")
            tk.Label(inner, text=val,   font=("Segoe UI",14,"bold"), bg=BG_CARD, fg=TEXT_PRI).pack(anchor="w")

        chart_frame = tk.Frame(self._right_content, bg=BG_CARD)
        chart_frame.pack(fill="both", expand=True)

        x = list(range(len(data)))
        fig, ax = plt.subplots(figsize=(6.8, 3.4))
        fig.patch.set_facecolor(BG_CARD)
        ax.set_facecolor(BG_CARD)
        ax.fill_between(x, data, alpha=0.16, color=TEAL)
        ax.plot(x, data, color=TEAL, linewidth=1.8, zorder=3)
        if len(data) <= 200:
            ax.scatter(x, data, color=TEAL, s=16, zorder=4, alpha=0.7)
        ax.axhline(y=300, color=RED,    linestyle="--", linewidth=0.9, alpha=0.7)
        ax.axhline(y=800, color=ACCENT, linestyle="--", linewidth=0.9, alpha=0.7)
        ax.set_xlim(0, max(len(data)-1,1))
        ax.set_ylim(0, max(max(data)*1.1, 1100))
        ax.tick_params(colors=TEXT_SEC, labelsize=7)
        ax.grid(color=TEXT_MUT, linestyle="-", linewidth=0.3, alpha=0.4)
        for spine in ax.spines.values(): spine.set_edgecolor(BORDER)
        ax.set_title(fname, color=TEXT_PRI, fontsize=9, pad=8, loc="left")
        ax.set_xlabel("Sample index", color=TEXT_SEC, fontsize=7)
        ax.set_ylabel("lux",          color=TEXT_SEC, fontsize=7)
        fig.tight_layout(pad=1.0)
        self._chart_canvas = FigureCanvasTkAgg(fig, master=chart_frame)
        self._chart_canvas.draw()
        self._chart_canvas.get_tk_widget().pack(fill="both", expand=True)