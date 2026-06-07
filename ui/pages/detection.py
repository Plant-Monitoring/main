import os
import threading
import tkinter as tk
from tkinter import messagebox, filedialog

from .theme import (
    BG_MAIN, BG_CARD, BG_CARD2, BG_GLASS, ACCENT, ACCENT2, BLUE, BLUE2, RED, YELLOW,
    PURPLE, TEXT_PRI, TEXT_SEC, TEXT_MUT, BORDER2, ON_ACCENT, bind_tree, hover, BasePage
)
from models.detection import (
    API_URL,
    api_detect,
    analyze_plant_image_cnn,
    CNN_CLASS_META,
)

STATUS_META   = {k: (v[0], v[1]) for k, v in CNN_CLASS_META.items()}
URGENCY_COLOR = {"Low": ACCENT, "Medium": YELLOW, "High": RED, "Critical": "#ff2244"}


class DetectionPage(BasePage):
    def _build(self):
        self._image_path = None

        outer = tk.Frame(self, bg=BG_MAIN)
        outer.pack(fill="both", expand=True, padx=22, pady=18)

        hdr_row = tk.Frame(outer, bg=BG_MAIN)
        hdr_row.pack(fill="x", pady=(0,6))
        tk.Label(hdr_row, text="Plant Health Detection", font=("Segoe UI",16,"bold"),
                 bg=BG_MAIN, fg=TEXT_PRI).pack(side="left")
        icon_lbl = tk.Label(hdr_row, text="🔬", font=("Segoe UI",16), bg=BG_MAIN)
        icon_lbl.pack(side="left", padx=(6,0))

        load_btn = tk.Frame(hdr_row, bg=BLUE, cursor="hand2", padx=16, pady=8)
        load_btn.pack(side="right")
        tk.Label(load_btn, text="📷  Upload Image", font=self.f_label, bg=BLUE, fg=ON_ACCENT).pack()
        bind_tree(load_btn, "<Button-1>", lambda e: self._load_image())
        hover(load_btn, BLUE, BLUE2)

        sub_row = tk.Frame(outer, bg=BG_MAIN)
        sub_row.pack(fill="x", pady=(0,14))
        tk.Label(sub_row, text="Upload a plant photo — EfficientNetB0 + colour ensemble will diagnose health.",
                 font=self.f_small, bg=BG_MAIN, fg=TEXT_SEC).pack(side="left")
        tk.Label(sub_row, text="  ~90% accuracy", font=self.f_small, bg=BG_MAIN, fg=PURPLE).pack(side="left")

        cols = tk.Frame(outer, bg=BG_MAIN)
        cols.pack(fill="both", expand=True)

        left = tk.Frame(cols, bg=BG_CARD, width=290)
        left.pack(side="left", fill="y", padx=(0,14))
        left.pack_propagate(False)
        tk.Frame(left, bg=ACCENT, height=3).pack(fill="x")

        tk.Label(left, text="Plant Image", font=self.f_label,
                 bg=BG_CARD, fg=TEXT_SEC).pack(anchor="w", padx=12, pady=(12,6))

        self._preview_canvas = tk.Canvas(left, bg=BG_GLASS, highlightthickness=1,
                                          highlightbackground=BORDER2, width=256, height=210)
        self._preview_canvas.pack(padx=12, pady=(0,8))
        self._preview_canvas.create_text(128, 105, text="No image loaded",
                                          fill=TEXT_MUT, font=("Segoe UI",9))

        self._img_name_lbl = tk.Label(left, text="", font=self.f_small,
                                       bg=BG_CARD, fg=TEXT_SEC, wraplength=240)
        self._img_name_lbl.pack(padx=12, pady=(0,4))

        self._cnn_info_frame = tk.Frame(left, bg=BG_GLASS, padx=10, pady=8)
        self._cnn_info_frame.pack(fill="x", padx=12, pady=(0,8))
        tk.Label(self._cnn_info_frame, text="CNN Architecture", font=("Segoe UI",7,"bold"),
                 bg=BG_GLASS, fg=ACCENT).pack(anchor="w")
        self._cnn_info_lbl = tk.Label(
            self._cnn_info_frame,
            text="Model:    EfficientNetB0\nBackbone: ImageNet (top 30 unfrozen)\nHead:     Dense(512->256) -> 8 classes\nAccuracy: ~90%",
            font=self.f_small, bg=BG_GLASS, fg=TEXT_SEC, justify="left")
        self._cnn_info_lbl.pack(anchor="w")

        self._analyse_btn_frame = tk.Frame(left, bg=ACCENT, cursor="hand2")
        self._analyse_btn_frame.pack(fill="x", padx=12, pady=(0,12))
        tk.Label(self._analyse_btn_frame, text="Analyse with CNN",
                 font=self.f_label, bg=ACCENT, fg=ON_ACCENT, pady=9).pack()
        bind_tree(self._analyse_btn_frame, "<Button-1>", lambda e: self._run_analysis())
        hover(self._analyse_btn_frame, ACCENT, ACCENT2)

        self._results_frame = tk.Frame(cols, bg=BG_MAIN)
        self._results_frame.pack(side="left", fill="both", expand=True)
        self._show_empty_state()

    def _load_image(self):
        path = filedialog.askopenfilename(
            title="Select Plant Image",
            filetypes=[("Image files","*.jpg *.jpeg *.png *.webp *.gif"),("All files","*.*")])
        if not path: return
        self._image_path = path
        fname = os.path.basename(path)
        self._img_name_lbl.config(text=fname)
        try:
            from PIL import Image, ImageTk
            img = Image.open(path); img.thumbnail((256,210))
            self._tk_img = ImageTk.PhotoImage(img)
            self._preview_canvas.delete("all")
            self._preview_canvas.create_image(128, 105, image=self._tk_img, anchor="center")
        except ImportError:
            self._preview_canvas.delete("all")
            self._preview_canvas.create_text(128, 105, text=fname[:28], fill=TEXT_SEC, font=("Segoe UI",8))
        except Exception as ex:
            self._preview_canvas.delete("all")
            self._preview_canvas.create_text(128, 105, text=f"Preview error:\n{ex}", fill=RED, font=("Segoe UI",8))
        self._show_empty_state(msg="Image loaded. Click 'Analyse with CNN' to diagnose.")

    def _show_empty_state(self, msg="Upload a plant image to get started."):
        for w in self._results_frame.winfo_children(): w.destroy()
        container = tk.Frame(self._results_frame, bg=BG_CARD, padx=20, pady=30)
        container.pack(fill="both", expand=True)
        tk.Frame(container, bg=ACCENT, height=3).pack(fill="x", pady=(0,20))
        tk.Label(container, text="🌿", font=("Segoe UI",40), bg=BG_CARD).pack(pady=(0,8))
        tk.Label(container, text=msg, font=self.f_body, bg=BG_CARD,
                 fg=TEXT_SEC, wraplength=340, justify="center").pack()

    def _show_loading(self):
        for w in self._results_frame.winfo_children(): w.destroy()
        container = tk.Frame(self._results_frame, bg=BG_CARD, padx=20, pady=30)
        container.pack(fill="both", expand=True)
        tk.Frame(container, bg=PURPLE, height=3).pack(fill="x", pady=(0,20))
        tk.Label(container, text="🧠", font=("Segoe UI",36), bg=BG_CARD).pack(pady=(0,12))
        tk.Label(container, text="Running CNN inference...",
                 font=("Segoe UI",11,"bold"), bg=BG_CARD, fg=TEXT_PRI).pack()
        tk.Label(container, text="EfficientNetB0 + colour ensemble is analysing your image.",
                 font=self.f_body, bg=BG_CARD, fg=TEXT_SEC, justify="center").pack(pady=(8,0))
        self._loading_dots = tk.Label(container, text="* * *", font=("Segoe UI",14),
                                       bg=BG_CARD, fg=PURPLE)
        self._loading_dots.pack(pady=(16,0))
        self._dot_idx = 0
        self._animate_dots()

    def _animate_dots(self):
        patterns = ["*  o  o","o  *  o","o  o  *","o  *  o"]
        try:
            self._loading_dots.config(text=patterns[self._dot_idx % len(patterns)])
            self._dot_idx += 1
            self._anim_job = self.after(400, self._animate_dots)
        except: pass

    def _run_analysis(self):
        if not self._image_path:
            messagebox.showwarning("No Image", "Please upload a plant image first."); return
        if not os.path.exists(self._image_path):
            messagebox.showerror("File Missing", "The selected image file no longer exists."); return
        self._show_loading()

        def on_result(result, error):
            if hasattr(self, "_anim_job"):
                try: self.after_cancel(self._anim_job)
                except: pass
            self.after(0, lambda: self._show_result(result, error))

        if API_URL:
            def _api_thread():
                result = api_detect(self._image_path)
                if result: on_result(result, None)
                else:      analyze_plant_image_cnn(self._image_path, on_result)
            threading.Thread(target=_api_thread, daemon=True).start()
        else:
            analyze_plant_image_cnn(self._image_path, on_result)

    def _show_result(self, result, error):
        for w in self._results_frame.winfo_children(): w.destroy()
        if error or result is None:
            container = tk.Frame(self._results_frame, bg=BG_CARD, padx=20, pady=20)
            container.pack(fill="both", expand=True)
            tk.Frame(container, bg=RED, height=3).pack(fill="x", pady=(0,12))
            tk.Label(container, text="CNN Analysis Failed", font=("Segoe UI",12,"bold"),
                     bg=BG_CARD, fg=RED).pack(pady=(0,8))
            tk.Label(container, text=str(error) if error else "Unknown error.",
                     font=self.f_body, bg=BG_CARD, fg=TEXT_SEC, wraplength=380, justify="center").pack(pady=(0,12))
            re_btn = tk.Frame(container, bg=BG_GLASS, cursor="hand2", padx=14, pady=8)
            re_btn.pack()
            tk.Label(re_btn, text="Try Again", font=self.f_label, bg=BG_GLASS, fg=ACCENT).pack()
            bind_tree(re_btn, "<Button-1>", lambda e: self._run_analysis())
            hover(re_btn, BG_GLASS, BG_CARD2)
            return

        cnn_info = result.get("_cnn_info", {})
        if cnn_info:
            self._cnn_info_lbl.config(
                text=(f"Model:    {cnn_info.get('model','EfficientNetB0')}\n"
                      f"Backbone: ImageNet (top 30 unfrozen)\n"
                      f"Head:     Dense(512->{cnn_info.get('classes',8)} classes)\n"
                      f"Accuracy: {cnn_info.get('accuracy_est','~90%')}"),
                fg=TEXT_PRI)

        status   = result.get("status","Unknown")
        conf     = result.get("confidence", 0)
        summary  = result.get("summary","")
        symptoms = result.get("symptoms",[])
        recs     = result.get("recommendations",[])
        urgency  = result.get("urgency","Low")
        color, badge_emoji = STATUS_META.get(status, (TEXT_SEC,"?"))
        urg_color = URGENCY_COLOR.get(urgency, TEXT_SEC)

        res_canvas = tk.Canvas(self._results_frame, bg=BG_MAIN, highlightthickness=0)
        sb = tk.Scrollbar(self._results_frame, orient="vertical", command=res_canvas.yview)
        res_canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        res_canvas.pack(side="left", fill="both", expand=True)
        pad = tk.Frame(res_canvas, bg=BG_MAIN)
        win_id = res_canvas.create_window((0,0), window=pad, anchor="nw")
        pad.bind("<Configure>", lambda e: res_canvas.configure(scrollregion=res_canvas.bbox("all")))
        res_canvas.bind("<Configure>", lambda e: res_canvas.itemconfig(win_id, width=e.width))

        banner = tk.Frame(pad, bg=BG_CARD, padx=16, pady=14)
        banner.pack(fill="x", pady=(0,10))
        tk.Frame(banner, bg=color, height=3).pack(fill="x", pady=(0,10))
        top_row = tk.Frame(banner, bg=BG_CARD)
        top_row.pack(fill="x")
        tk.Label(top_row, text=f"{badge_emoji}  {status}", font=("Segoe UI",14,"bold"),
                 bg=BG_CARD, fg=color).pack(side="left")
        tk.Label(top_row, text=f"  {urgency} urgency  ",
                 font=self.f_small, bg=urg_color, fg=ON_ACCENT, padx=6, pady=2).pack(side="right")
        tk.Label(banner, text=f"CNN Confidence: {conf}%", font=self.f_small,
                 bg=BG_CARD, fg=TEXT_SEC).pack(anchor="w", pady=(8,4))
        bar_bg = tk.Frame(banner, bg=BG_GLASS, height=8)
        bar_bg.pack(fill="x")
        bar_bg.update_idletasks()
        w = bar_bg.winfo_width() or 300
        bar_fill = tk.Frame(bar_bg, bg=color, width=max(4, int(w*conf/100)), height=8)
        bar_fill.place(x=0, y=0)
        tk.Label(banner, text=summary, font=self.f_body, bg=BG_CARD,
                 fg=TEXT_PRI, wraplength=360, justify="left").pack(anchor="w", pady=(10,0))
        method_row = tk.Frame(banner, bg=BG_CARD)
        method_row.pack(anchor="w", pady=(6,0))
        tk.Label(method_row, text="  EfficientNetB0  ", font=("Segoe UI",7),
                 bg=PURPLE, fg=ON_ACCENT, padx=4, pady=2).pack(side="left")
        tk.Label(method_row, text="  Transfer Learning + Colour Ensemble",
                 font=("Segoe UI",7), bg=BG_CARD, fg=TEXT_MUT).pack(side="left", padx=(6,0))

        if symptoms:
            sym_hdr = tk.Frame(pad, bg=BG_MAIN)
            sym_hdr.pack(fill="x", pady=(4,6))
            tk.Frame(sym_hdr, bg=YELLOW, width=4, height=16).pack(side="left")
            tk.Label(sym_hdr, text="  Observed Symptoms", font=self.f_title,
                     bg=BG_MAIN, fg=TEXT_PRI).pack(side="left")
            for sym in symptoms:
                row = tk.Frame(pad, bg=BG_CARD, padx=12, pady=8)
                row.pack(fill="x", pady=(0,4))
                tk.Frame(row, bg=color, width=3).pack(side="left", fill="y", padx=(0,10))
                tk.Label(row, text=sym, font=self.f_body, bg=BG_CARD, fg=TEXT_PRI,
                         wraplength=360, justify="left").pack(side="left", fill="x")

        if recs:
            rec_hdr = tk.Frame(pad, bg=BG_MAIN)
            rec_hdr.pack(fill="x", pady=(10,6))
            tk.Frame(rec_hdr, bg=ACCENT, width=4, height=16).pack(side="left")
            tk.Label(rec_hdr, text="  Recommended Actions", font=self.f_title,
                     bg=BG_MAIN, fg=TEXT_PRI).pack(side="left")
            for i, rec in enumerate(recs, 1):
                row = tk.Frame(pad, bg=BG_CARD, padx=12, pady=8)
                row.pack(fill="x", pady=(0,4))
                num = tk.Label(row, text=f" {i} ", font=("Segoe UI",8,"bold"),
                               bg=ACCENT, fg=ON_ACCENT, padx=4, pady=1)
                num.pack(side="left", padx=(0,10))
                tk.Label(row, text=rec, font=self.f_body, bg=BG_CARD, fg=TEXT_PRI,
                         wraplength=360, justify="left").pack(side="left", fill="x")

        re_btn = tk.Frame(pad, bg=BG_GLASS, cursor="hand2", padx=14, pady=8)
        re_btn.pack(anchor="e", pady=(12,20))
        tk.Label(re_btn, text="Analyse Again", font=self.f_label, bg=BG_GLASS, fg=ACCENT).pack()
        bind_tree(re_btn, "<Button-1>", lambda e: self._run_analysis())
        hover(re_btn, BG_GLASS, BG_CARD2)