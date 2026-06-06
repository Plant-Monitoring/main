import os
import tkinter as tk
from tkinter import messagebox

from .theme import *

class AuthWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Plant Monitor — Login")
        self.geometry("480x600")
        self.configure(bg=BG_MAIN)
        self.resizable(False, False)
        self.logged_in_user = None
        self.protocol("WM_DELETE_WINDOW", lambda: os._exit(0))
        self._frame = tk.Frame(self, bg=BG_MAIN)
        self._frame.place(relx=0.5, rely=0.5, anchor="center", width=360)
        self._render_login()

    def _clear(self):
        for w in self._frame.winfo_children(): w.destroy()

    def _accent_line(self, parent):
        line_frame = tk.Frame(parent, bg=BG_MAIN, height=3)
        line_frame.pack(fill="x", pady=(0,14))
        tk.Frame(line_frame, bg=ACCENT, height=3, width=40).pack(side="left")
        tk.Frame(line_frame, bg=ACCENT2, height=3, width=20).pack(side="left")
        tk.Frame(line_frame, bg=BG_GLASS, height=3).pack(side="left", expand=True, fill="x")

    def _field(self, parent, label, show=None):
        tk.Label(parent, text=label, font=("Segoe UI", 8, "bold"), bg=BG_MAIN,
                 fg=ACCENT).pack(anchor="w", pady=(10,2))
        container = tk.Frame(parent, bg=BG_GLASS, pady=0)
        container.pack(fill="x")
        left_bar = tk.Frame(container, bg=ACCENT, width=3)
        left_bar.pack(side="left", fill="y")
        e = tk.Entry(container, bg=BG_GLASS, fg=TEXT_PRI, insertbackground=ACCENT,
                     relief="flat", font=("Segoe UI", 10), show=show, bd=0)
        e.pack(side="left", fill="x", expand=True, ipady=9, padx=(8,8))
        return e

    def _action_btn(self, parent, text, command):
        btn = tk.Frame(parent, bg=ACCENT, cursor="hand2")
        btn.pack(fill="x", pady=(20,0))
        inner = tk.Frame(btn, bg=ACCENT)
        inner.pack(fill="x")
        tk.Label(inner, text=text, font=("Segoe UI", 10, "bold"),
                 bg=ACCENT, fg=BG_MAIN, pady=11).pack()
        bind_tree(btn, "<Button-1>", lambda e: command())
        hover(btn, ACCENT, ACCENT2)

    def _link_btn(self, parent, text, command):
        lbl = tk.Label(parent, text=text, font=("Segoe UI", 8),
                       bg=BG_MAIN, fg=ACCENT, cursor="hand2")
        lbl.pack(pady=(12,0))
        lbl.bind("<Button-1>", lambda e: command())

    def _render_login(self):
        self._clear(); f = self._frame
        # Header
        hdr = tk.Frame(f, bg=BG_MAIN)
        hdr.pack(fill="x", pady=(0,6))
        icon_frame = tk.Frame(hdr, bg=BG_GLASS, padx=10, pady=8)
        icon_frame.pack(anchor="center")
        tk.Label(icon_frame, text="🌿", font=("Segoe UI", 26), bg=BG_GLASS).pack()
        tk.Label(f, text="PLANT MONITOR", font=("Segoe UI", 16, "bold"),
                 bg=BG_MAIN, fg=TEXT_PRI).pack()
        tk.Label(f, text="Sign in to continue", font=("Segoe UI", 8),
                 bg=BG_MAIN, fg=TEXT_SEC).pack(pady=(2,8))
        self._accent_line(f)
        self._login_user = self._field(f, "USERNAME")
        self._login_pass = self._field(f, "PASSWORD", show="*")
        self._err_lbl = tk.Label(f, text="", font=("Segoe UI", 8), bg=BG_MAIN, fg=RED)
        self._err_lbl.pack(pady=(8,0))
        self._action_btn(f, "SIGN IN", self._do_login)
        self._link_btn(f, "No account yet?  Register here", self._render_signup)
        self.bind("<Return>", lambda e: self._do_login())

    def _do_login(self):
        u=self._login_user.get().strip(); p=self._login_pass.get().strip()
        if not u or not p: self._err_lbl.config(text="Please fill in all fields."); return
        if USERS.get(u) == p: self.logged_in_user = u; self.destroy()
        else: self._err_lbl.config(text="Incorrect username or password.")

    def _render_signup(self):
        self._clear(); f = self._frame
        icon_frame = tk.Frame(f, bg=BG_GLASS, padx=10, pady=8)
        icon_frame.pack(anchor="center")
        tk.Label(icon_frame, text="🌿", font=("Segoe UI", 26), bg=BG_GLASS).pack()
        tk.Label(f, text="CREATE ACCOUNT", font=("Segoe UI", 16, "bold"), bg=BG_MAIN, fg=TEXT_PRI).pack()
        tk.Label(f, text="Join the Plant Monitor community", font=("Segoe UI", 8),
                 bg=BG_MAIN, fg=TEXT_SEC).pack(pady=(2,8))
        self._accent_line(f)
        self._su_user  = self._field(f, "USERNAME")
        self._su_pass  = self._field(f, "PASSWORD", show="*")
        self._su_pass2 = self._field(f, "CONFIRM PASSWORD", show="*")
        self._su_err = tk.Label(f, text="", font=("Segoe UI", 8), bg=BG_MAIN, fg=RED)
        self._su_err.pack(pady=(8,0))
        self._action_btn(f, "CREATE ACCOUNT", self._do_signup)
        self._link_btn(f, "Already have an account?  Sign In", self._render_login)
        self.bind("<Return>", lambda e: self._do_signup())

    def _do_signup(self):
        u=self._su_user.get().strip(); p=self._su_pass.get().strip(); p2=self._su_pass2.get().strip()
        if not u or not p or not p2: self._su_err.config(text="Please fill in all fields."); return
        if u in USERS:     self._su_err.config(text="Username is already taken."); return
        if len(p) < 4:     self._su_err.config(text="Password must be at least 4 characters."); return
        if p != p2:        self._su_err.config(text="Passwords do not match."); return
        USERS[u] = p
        messagebox.showinfo("Account Created", f"Welcome, {u}!\nYou can now sign in.")
        self._render_login()