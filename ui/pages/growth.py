import tkinter as tk

from .theme import *

class GrowthPage(BasePage):
    def _build(self):
        outer = tk.Frame(self, bg=BG_MAIN)
        outer.pack(fill="both", expand=True, padx=22, pady=18)

        tk.Label(outer, text="Growth Prediction", font=("Segoe UI",16,"bold"),
                 bg=BG_MAIN, fg=TEXT_PRI).pack(anchor="w")
        tk.Label(outer, text="📈", font=("Segoe UI",16), bg=BG_MAIN).pack(anchor="w")
        tk.Label(outer, text="Predict plant height growth from its conditions.",
                 font=self.f_small, bg=BG_MAIN, fg=TEXT_SEC).pack(anchor="w", pady=(0,16))

        card = tk.Frame(outer, bg=BG_CARD, padx=20, pady=40)
        card.pack(fill="both", expand=True)
        tk.Frame(card, bg=TEAL, height=3).pack(fill="x", pady=(0,20))
        tk.Label(card, text="🚧", font=("Segoe UI",40), bg=BG_CARD).pack(pady=(0,8))
        tk.Label(card, text="The growth prediction model is not implemented yet.\nComing soon.",
                 font=self.f_body, bg=BG_CARD, fg=TEXT_SEC, justify="center").pack()