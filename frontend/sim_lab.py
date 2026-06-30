"""
HESTIA Simulation Lab
=====================
Ventana independiente para correr simulaciones aceleradas contra el motor real C++.
Conecta los 8 arquetipos de Monte Carlo al bridge Python → C++ sin clicks manuales.

Ejecutar:  python -m frontend.sim_lab  (desde raíz del proyecto)
"""

import os
import sys
import csv
import random
import sqlite3
import threading
import traceback
import time
import shutil
from pathlib import Path
from typing import Optional

import tkinter as tk
from tkinter import ttk

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "src"))

try:
    from frontend.bridge.hestia_bridge import METHOD
    import hestia_core  # type: ignore
    BRIDGE_AVAILABLE = True
except ImportError as e:
    BRIDGE_AVAILABLE = False
    BRIDGE_ERROR = str(e)

try:
    import matplotlib
    matplotlib.use("TkAgg")
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    HAS_MPL = True
except ImportError:
    HAS_MPL = False

# ─── Paleta ───────────────────────────────────────────────────────────────────
BG_DARK    = "#111622"
BG_WHITE   = "#ffffff"
BG_LIGHT   = "#f8f9fa"
ACCENT     = "#3498db"
TEXT_MAIN  = "#2c3e50"
TEXT_DIM   = "#7f8c8d"
GREEN_MINT = "#00FF9D"

METHOD_NAMES = ["Visual", "Auditivo", "Kinestésico", "Fonético", "Global"]
METHOD_COLORS_BAR = ["#a0c4ff", "#b9fbc0", "#ffd6a5", "#ffadad", "#d0d0ff"]

PROFILE_COLORS = [
    "#e74c3c", "#3498db", "#2ecc71", "#f39c12",
    "#9b59b6", "#1abc9c", "#e67e22", "#e91e63",
]

# ─── 8 Arquetipos (alineados con monte_carlo.cpp) ────────────────────────────
ARCHETYPES = [
    {"name": "Fast Learner",        "emoji": "🚀",
     "p_transition": 0.30, "p_slip": 0.10, "p_guess": 0.25, "p_forget": 0.02,
     "method_success_probs": [0.9, 0.8, 0.7, 0.6, 0.8], "color": PROFILE_COLORS[0]},
    {"name": "Average Learner",     "emoji": "📚",
     "p_transition": 0.15, "p_slip": 0.10, "p_guess": 0.25, "p_forget": 0.05,
     "method_success_probs": [0.6, 0.7, 0.6, 0.5, 0.6], "color": PROFILE_COLORS[1]},
    {"name": "Slow & Consistent",   "emoji": "🐢",
     "p_transition": 0.05, "p_slip": 0.10, "p_guess": 0.25, "p_forget": 0.01,
     "method_success_probs": [0.4, 0.4, 0.8, 0.4, 0.4], "color": PROFILE_COLORS[2]},
    {"name": "Forgetful Learner",   "emoji": "🧠",
     "p_transition": 0.20, "p_slip": 0.10, "p_guess": 0.25, "p_forget": 0.40,
     "method_success_probs": [0.5, 0.5, 0.5, 0.5, 0.5], "color": PROFILE_COLORS[3]},
    {"name": "Struggling Learner",  "emoji": "😓",
     "p_transition": 0.02, "p_slip": 0.15, "p_guess": 0.25, "p_forget": 0.15,
     "method_success_probs": [0.3, 0.3, 0.3, 0.4, 0.3], "color": PROFILE_COLORS[4]},
    {"name": "The Crammer",         "emoji": "⚡",
     "p_transition": 0.35, "p_slip": 0.10, "p_guess": 0.25, "p_forget": 0.35,
     "method_success_probs": [0.8, 0.6, 0.6, 0.6, 0.6], "color": PROFILE_COLORS[5]},
    {"name": "Inconsistent Genius", "emoji": "🎲",
     "p_transition": 0.35, "p_slip": 0.30, "p_guess": 0.25, "p_forget": 0.05,
     "method_success_probs": [0.7, 0.7, 0.7, 0.7, 0.7], "color": PROFILE_COLORS[6]},
    {"name": "Guessing Gamer",      "emoji": "🎮",
     "p_transition": 0.05, "p_slip": 0.10, "p_guess": 0.40, "p_forget": 0.10,
     "method_success_probs": [0.4, 0.4, 0.4, 0.4, 0.4], "color": PROFILE_COLORS[7]},
]

# ─── SyntheticAgent ───────────────────────────────────────────────────────────
class SyntheticAgent:
    def __init__(self, arch: dict, seed: int = 42):
        self.arch = arch
        self.rng = random.Random(seed)
        self.p_known = arch["p_guess"]

    def respond(self, method_int: int) -> bool:
        arch = self.arch
        known = self.rng.random() < self.p_known
        prefs = arch["method_success_probs"]
        mp = prefs[method_int] if method_int < len(prefs) else 0.5
        if known:
            p_correct = mp * (1.0 - arch["p_slip"])
        else:
            p_correct = (1.0 - mp) * arch["p_guess"]
        correct = self.rng.random() < p_correct
        if correct:
            self.p_known = min(0.99, self.p_known + arch["p_transition"] * (1 - self.p_known))
        else:
            self.p_known = max(0.01, self.p_known - arch["p_forget"] * self.p_known)
        return correct

    def response_time_ms(self, correct: bool) -> int:
        base = 2500 if correct else 5500
        return max(300, int(self.rng.gauss(base, 900)))


# ─── SimulationRunner ─────────────────────────────────────────────────────────
class SimulationRunner:
    METHOD_INT_TO_ENUM = {
        0: METHOD.VISUAL, 1: METHOD.AUDITORY, 2: METHOD.KINESTHETIC,
        3: METHOD.PHONETIC, 4: METHOD.GLOBAL,
    } if BRIDGE_AVAILABLE else {}
    METHOD_ENUM_TO_INT = {v: k for k, v in METHOD_INT_TO_ENUM.items()} if BRIDGE_AVAILABLE else {}

    def __init__(self, archetypes, n_attempts, seed, on_progress, on_done, on_log):
        self.archetypes = archetypes
        self.n = n_attempts
        self.seed = seed
        self.on_progress = on_progress
        self.on_done = on_done
        self.on_log = on_log
        self._stop = threading.Event()
        self.results = {}

    def stop(self): self._stop.set()

    def run(self):
        db_path = str(BASE_DIR / f"hestia_simlab_{int(time.time())}.db")
        source_db = str(BASE_DIR / "hestia.db")
        try:
            if os.path.exists(source_db):
                shutil.copy2(source_db, db_path)
            self._run_all(db_path)
        except Exception:
            self.on_log(f"[SimLab ERROR]\n{traceback.format_exc()}")
        finally:
            try:
                Path(db_path).unlink(missing_ok=True)
            except Exception:
                pass

    def _run_all(self, db_path):
        total = len(self.archetypes) * self.n
        done = 0
        self.on_log(f"[SIM] {len(self.archetypes)} arquetipos x {self.n} intentos — seed={self.seed}")
        for arch in self.archetypes:
            if self._stop.is_set():
                break
            self._run_archetype(arch, db_path)
            done += self.n
            self.on_progress(done, total)
        self.on_log("[SIM] ✓ Completo")
        self.on_done(self.results)

    def _run_archetype(self, arch, db_path):
        name = arch["name"]
        self.on_log(f"  [{arch['emoji']} {name}] iniciando ...")
        from frontend.bridge.hestia_bridge import HestiaBridge
        # Fresh bridge instance (anula singleton para DB temporal)
        HestiaBridge._instance = None
        bridge = HestiaBridge(db_path=db_path)
        agent = SyntheticAgent(arch, seed=self.seed)
        # Registra usuario sintético
        with sqlite3.connect(db_path) as conn:
            cur = conn.cursor()
            cur.execute("CREATE TABLE IF NOT EXISTS user_profile "
                        "(id INTEGER PRIMARY KEY, name TEXT, profile_type TEXT)")
            cur.execute("INSERT INTO user_profile (name, profile_type) VALUES (?,?)",
                        (name, "synthetic"))
            conn.commit()
            uid = cur.lastrowid
        skill_id = 0
        bridge.start_session(uid, skill_id)
        trace = []
        curr_mi = 0
        for attempt in range(1, self.n + 1):
            if self._stop.is_set():
                break
            method_enum = self.METHOD_INT_TO_ENUM.get(curr_mi, METHOD.VISUAL)
            correct = agent.respond(curr_mi)
            rt = agent.response_time_ms(correct)
            try:
                result, latency, logs = bridge.process_response_timed(uid, skill_id, method_enum, correct, rt)
                pl_op = result.current_pL
                pl_th = result.current_pL_theorical
                next_mi = self.METHOD_ENUM_TO_INT.get(result.next_method, 0)
            except Exception:
                self.on_log(f"    bridge err attempt {attempt}:\n{traceback.format_exc()}")
                pl_op = pl_th = 0.0
                next_mi = curr_mi
            try:
                sm = bridge.get_method_states_for_ui(uid, skill_id)
                q_vals = [sm.get(m, {}).get("q_value", 0.5)
                          for m in ("VISUAL","AUDITORY","KINESTHETIC","PHONETIC","GLOBAL")]
            except Exception:
                q_vals = [0.5]*5
            trace.append({"attempt": attempt, "method_int": curr_mi,
                          "correct": correct, "pl_op": pl_op, "pl_th": pl_th, "q_vals": q_vals})
            curr_mi = next_mi
        self.results[name] = trace
        acc = sum(1 for t in trace if t["correct"]) / max(len(trace), 1)
        self.on_log(f"    P(L)={trace[-1]['pl_op']:.3f}  Acc={acc*100:.1f}%")
        HestiaBridge._instance = None


# ─── SimLabApp ────────────────────────────────────────────────────────────────
class SimLabApp:
    def __init__(self, root):
        self.root = root
        self.root.title("HESTIA — Simulation Lab 🔬")
        self.root.geometry("1400x820")
        self.root.minsize(1200, 720)
        self.root.configure(bg=BG_WHITE)
        self._runner = None
        self._thread = None
        self._results = {}
        self._build_ui()

    # ── Layout ────────────────────────────────────────────────────────────────
    def _build_ui(self):
        hdr = tk.Frame(self.root, bg=BG_DARK, pady=12)
        hdr.pack(fill="x")
        tk.Label(hdr, text="HESTIA  ·  Simulation Lab",
                 font=("Courier New", 18, "bold"), fg=GREEN_MINT, bg=BG_DARK).pack(side="left", padx=20)
        tk.Label(hdr, text="Motor real C++  ·  8 arquetipos Monte Carlo",
                 font=("Courier New", 10), fg="#34495e", bg=BG_DARK).pack(side="left")

        body = tk.Frame(self.root, bg=BG_WHITE)
        body.pack(fill="both", expand=True)
        body.columnconfigure(0, weight=0, minsize=290)
        body.columnconfigure(1, weight=1)
        body.rowconfigure(0, weight=1)
        self._build_sidebar(body)
        self._build_right_panel(body)

    # ── Sidebar ───────────────────────────────────────────────────────────────
    def _build_sidebar(self, parent):
        side = tk.Frame(parent, bg=BG_LIGHT, padx=16, pady=16, width=290)
        side.grid(row=0, column=0, sticky="nsew")
        side.pack_propagate(False)

        tk.Label(side, text="CONFIGURACIÓN", font=("Courier New", 10, "bold"),
                 fg=TEXT_DIM, bg=BG_LIGHT).pack(anchor="w", pady=(0, 12))

        # Intentos
        tk.Label(side, text="Intentos por arquetipo", font=("Arial", 11, "bold"),
                 fg=TEXT_MAIN, bg=BG_LIGHT).pack(anchor="w")
        self.attempts_var = tk.IntVar(value=80)
        frm_sl = tk.Frame(side, bg=BG_LIGHT)
        frm_sl.pack(fill="x", pady=(4, 12))
        self.attempts_lbl = tk.Label(frm_sl, text="80", font=("Courier New", 13, "bold"),
                                     fg=ACCENT, bg=BG_LIGHT, width=4)
        self.attempts_lbl.pack(side="right")
        tk.Scale(frm_sl, from_=20, to=200, orient="horizontal", variable=self.attempts_var,
                 bg=BG_LIGHT, highlightthickness=0, troughcolor="#dfe4ea",
                 command=lambda v: self.attempts_lbl.config(text=str(self.attempts_var.get())),
                 showvalue=False).pack(side="left", fill="x", expand=True)

        # Semilla
        tk.Label(side, text="Semilla aleatoria", font=("Arial", 11, "bold"),
                 fg=TEXT_MAIN, bg=BG_LIGHT).pack(anchor="w")
        self.seed_var = tk.IntVar(value=42)
        tk.Entry(side, textvariable=self.seed_var, font=("Courier New", 11),
                 width=8, relief="flat", bg="#ecf0f1").pack(anchor="w", pady=(4, 12))

        # Checkboxes de arquetipos
        tk.Label(side, text="Arquetipos a simular", font=("Arial", 11, "bold"),
                 fg=TEXT_MAIN, bg=BG_LIGHT).pack(anchor="w", pady=(4, 6))
        self.arch_vars = {}
        for arch in ARCHETYPES:
            v = tk.BooleanVar(value=True)
            self.arch_vars[arch["name"]] = v
            frm = tk.Frame(side, bg=BG_LIGHT)
            frm.pack(fill="x", pady=1)
            dot = tk.Canvas(frm, width=12, height=12, bg=BG_LIGHT, highlightthickness=0)
            dot.create_oval(1, 1, 11, 11, fill=arch["color"], outline="")
            dot.pack(side="left", padx=(0, 5))
            tk.Checkbutton(frm, text=f"{arch['emoji']} {arch['name']}",
                           variable=v, font=("Arial", 9), fg=TEXT_MAIN, bg=BG_LIGHT,
                           activebackground=BG_LIGHT, selectcolor=BG_LIGHT).pack(side="left")

        # Botones
        self.btn_run = tk.Button(side, text="▶  EJECUTAR SIMULACIÓN",
                                 font=("Arial", 13, "bold"), bg=ACCENT, fg="white",
                                 activebackground="#2980b9", relief="flat", cursor="hand2",
                                 pady=12, command=self._start)
        self.btn_run.pack(fill="x", pady=(18, 6))
        self.btn_stop = tk.Button(side, text="⏹  Detener",
                                  font=("Arial", 10), bg="#ecf0f1", fg=TEXT_MAIN,
                                  relief="flat", cursor="hand2", command=self._stop,
                                  state="disabled")
        self.btn_stop.pack(fill="x", pady=(0, 4))
        self.btn_export = tk.Button(side, text="💾  Exportar CSV",
                                    font=("Arial", 10), bg="#ecf0f1", fg=TEXT_MAIN,
                                    relief="flat", cursor="hand2", command=self._export,
                                    state="disabled")
        self.btn_export.pack(fill="x", pady=(0, 12))

        # Progreso
        tk.Label(side, text="PROGRESO", font=("Courier New", 8, "bold"),
                 fg=TEXT_DIM, bg=BG_LIGHT).pack(anchor="w", pady=(6, 2))
        self.prog_canvas = tk.Canvas(side, height=8, bg="#dfe4ea", highlightthickness=0)
        self.prog_canvas.pack(fill="x")
        self.prog_bar = self.prog_canvas.create_rectangle(0, 0, 0, 8, fill=ACCENT, outline="")
        self.prog_label = tk.Label(side, text="Esperando...", font=("Courier New", 9),
                                   fg=TEXT_DIM, bg=BG_LIGHT)
        self.prog_label.pack(anchor="w", pady=(2, 0))

    # ── Panel derecho ─────────────────────────────────────────────────────────
    def _build_right_panel(self, parent):
        right = tk.Frame(parent, bg=BG_WHITE)
        right.grid(row=0, column=1, sticky="nsew")
        right.rowconfigure(0, weight=1)
        right.rowconfigure(1, weight=0, minsize=180)
        right.columnconfigure(0, weight=1)

        self.notebook = ttk.Notebook(right)
        self.notebook.grid(row=0, column=0, sticky="nsew", padx=10, pady=(10, 5))
        self.tab_pl   = tk.Frame(self.notebook, bg=BG_WHITE)
        self.tab_mab  = tk.Frame(self.notebook, bg=BG_WHITE)
        self.tab_dist = tk.Frame(self.notebook, bg=BG_WHITE)
        self.notebook.add(self.tab_pl,   text="📈  Convergencia P(L)")
        self.notebook.add(self.tab_mab,  text="🎰  Q-Values MAB")
        self.notebook.add(self.tab_dist, text="📊  Distribución métodos")
        self._init_charts()

        log_frame = tk.Frame(right, bg=BG_DARK, padx=10, pady=6)
        log_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        tk.Label(log_frame, text=">_  ENGINE LOG",
                 font=("Courier New", 9, "bold"), fg="#34495e", bg=BG_DARK).pack(anchor="w")
        self.log_text = tk.Text(log_frame, bg=BG_DARK, fg=GREEN_MINT,
                                font=("Courier New", 9), height=8, relief="flat",
                                wrap="word", highlightthickness=0)
        self.log_text.pack(fill="both", expand=True)

    # ── Charts ────────────────────────────────────────────────────────────────
    def _init_charts(self):
        if not HAS_MPL:
            for t in (self.tab_pl, self.tab_mab, self.tab_dist):
                tk.Label(t, text="⚠  matplotlib no encontrado\npip install matplotlib",
                         font=("Arial", 14), fg="#e74c3c", bg=BG_WHITE).pack(expand=True)
            return
        # P(L) chart
        fig1 = Figure(figsize=(8, 4), dpi=96, facecolor=BG_WHITE)
        self.ax_pl = fig1.add_subplot(111)
        self._style_ax(self.ax_pl, "Convergencia P(L) Operativo por arquetipo", "Intento", "P(L) op")
        self.cv_pl = FigureCanvasTkAgg(fig1, master=self.tab_pl)
        self.cv_pl.get_tk_widget().pack(fill="both", expand=True)
        # MAB chart
        fig2 = Figure(figsize=(8, 4), dpi=96, facecolor=BG_WHITE)
        self.ax_mab = fig2.add_subplot(111)
        self._style_ax(self.ax_mab, "Q-Values MAB (estado final, por método y arquetipo)", "Arquetipo", "Q-Value EWMA")
        self.cv_mab = FigureCanvasTkAgg(fig2, master=self.tab_mab)
        self.cv_mab.get_tk_widget().pack(fill="both", expand=True)
        # Distribution chart
        fig3 = Figure(figsize=(8, 4), dpi=96, facecolor=BG_WHITE)
        self.ax_dist = fig3.add_subplot(111)
        self._style_ax(self.ax_dist, "Método dominante: 1ª vs 2ª mitad (evidencia de convergencia)", "Arquetipo", "% uso brazo dominante")
        self.cv_dist = FigureCanvasTkAgg(fig3, master=self.tab_dist)
        self.cv_dist.get_tk_widget().pack(fill="both", expand=True)

    def _style_ax(self, ax, title, xl, yl):
        ax.set_facecolor(BG_WHITE)
        ax.set_title(title, fontsize=9, fontweight="bold", color=TEXT_MAIN, pad=6)
        ax.set_xlabel(xl, fontsize=8, color=TEXT_DIM)
        ax.set_ylabel(yl, fontsize=8, color=TEXT_DIM)
        ax.tick_params(colors=TEXT_DIM, labelsize=7)
        for s in ax.spines.values():
            s.set_color("#ecf0f1")

    # ── Eventos ───────────────────────────────────────────────────────────────
    def _log(self, line):
        self.root.after(0, lambda: (
            self.log_text.insert("end", line + "\n"),
            self.log_text.see("end")
        ))

    def _set_progress(self, done, total):
        self.prog_canvas.update_idletasks()
        w = self.prog_canvas.winfo_width()
        frac = min(done / max(total, 1), 1.0)
        self.prog_canvas.coords(self.prog_bar, 0, 0, int(w * frac), 8)
        self.prog_label.config(text=f"{int(frac*100)}%  ({done}/{total})")

    def _on_progress(self, done, total):
        if done is not None:
            self.root.after(0, lambda: self._set_progress(done, total))

    def _start(self):
        if not BRIDGE_AVAILABLE:
            self._log(f"[ERROR] Bridge no disponible: {BRIDGE_ERROR}")
            return
        selected = [a for a in ARCHETYPES if self.arch_vars[a["name"]].get()]
        if not selected:
            self._log("[UI] Selecciona al menos un arquetipo.")
            return
        n, seed = self.attempts_var.get(), self.seed_var.get()
        self._results = {}
        self._set_progress(0, len(selected) * n)
        self.btn_run.config(state="disabled")
        self.btn_stop.config(state="normal")
        self.btn_export.config(state="disabled")
        self._runner = SimulationRunner(
            archetypes=selected, n_attempts=n, seed=seed,
            on_progress=self._on_progress,
            on_done=lambda r: self.root.after(0, lambda: self._done(r)),
            on_log=self._log,
        )
        self._thread = threading.Thread(target=self._runner.run, daemon=True)
        self._thread.start()

    def _stop(self):
        if self._runner: self._runner.stop()
        self.btn_stop.config(state="disabled")
        self.btn_run.config(state="normal")

    def _done(self, results):
        self._results = results
        self.btn_run.config(state="normal")
        self.btn_stop.config(state="disabled")
        self.btn_export.config(state="normal")
        self._render_charts()

    # ── Render ────────────────────────────────────────────────────────────────
    def _render_charts(self):
        if not HAS_MPL or not self._results: return
        self._render_pl()
        self._render_mab()
        self._render_dist()

    def _render_pl(self):
        ax = self.ax_pl; ax.cla()
        self._style_ax(ax, "Convergencia P(L) Operativo", "Intento", "P(L) op")
        ax.axhline(y=0.85, color="#e74c3c", lw=1, ls="--", alpha=0.5, label="Dominio (0.85)")
        for arch in ARCHETYPES:
            name = arch["name"]
            if name not in self._results: continue
            tr = self._results[name]
            ax.plot([t["attempt"] for t in tr], [t["pl_op"] for t in tr],
                    color=arch["color"], lw=1.5, label=name, alpha=0.85)
        ax.set_ylim(0, 1.05)
        ax.legend(loc="lower right", fontsize=6, framealpha=0.7, ncol=2)
        self.cv_pl.draw()

    def _render_mab(self):
        ax = self.ax_mab; ax.cla()
        self._style_ax(ax, "Q-Values MAB al finalizar", "Arquetipo", "Q-Value EWMA")
        names = [a["name"] for a in ARCHETYPES if a["name"] in self._results]
        x = list(range(len(names)))
        bw = 0.14
        for mi in range(5):
            offs = [i + (mi - 2) * bw for i in x]
            vals = [self._results[n][-1]["q_vals"][mi] for n in names]
            ax.bar(offs, vals, width=bw, color=METHOD_COLORS_BAR[mi],
                   label=METHOD_NAMES[mi], alpha=0.85)
        ax.set_xticks(x)
        ax.set_xticklabels([n.split()[0] for n in names], rotation=22, ha="right", fontsize=7)
        ax.set_ylim(0, 1.05)
        ax.axhline(0.5, color="#bdc3c7", lw=0.8, ls="--")
        ax.legend(fontsize=7, framealpha=0.7)
        self.cv_mab.draw()

    def _render_dist(self):
        ax = self.ax_dist; ax.cla()
        self._style_ax(ax, "Método dominante: 1ª vs 2ª mitad", "Arquetipo", "% brazo dominante")
        names = [a["name"] for a in ARCHETYPES if a["name"] in self._results]
        first_vals, second_vals = [], []
        for name in names:
            tr = self._results[name]
            mid = len(tr) // 2
            def dom(half):
                if not half: return 0
                c = [0]*5
                for t in half: c[t["method_int"]] += 1
                return max(c) / len(half) * 100
            first_vals.append(dom(tr[:mid]))
            second_vals.append(dom(tr[mid:]))
        x = list(range(len(names)))
        bw = 0.35
        ax.bar([i - bw/2 for i in x], first_vals, width=bw, color="#a0c4ff", label="1ª mitad", alpha=0.85)
        ax.bar([i + bw/2 for i in x], second_vals, width=bw, color="#2ecc71", label="2ª mitad", alpha=0.85)
        ax.set_xticks(x)
        ax.set_xticklabels([n.split()[0] for n in names], rotation=22, ha="right", fontsize=7)
        ax.set_ylim(0, 108)
        ax.legend(fontsize=8, framealpha=0.7)
        for i, (f, s) in enumerate(zip(first_vals, second_vals)):
            arrow = "↑" if s > f+5 else ("↓" if f > s+5 else "≈")
            color = "#27ae60" if arrow=="↑" else ("#e74c3c" if arrow=="↓" else TEXT_DIM)
            ax.text(i, max(f, s)+2, arrow, ha="center", fontsize=11, color=color)
        self.cv_dist.draw()

    # ── Exportar ──────────────────────────────────────────────────────────────
    def _export(self):
        if not self._results: return
        out = BASE_DIR / "results" / f"simlab_{int(time.time())}.csv"
        out.parent.mkdir(exist_ok=True)
        rows = []
        for name, trace in self._results.items():
            for t in trace:
                rows.append({
                    "archetype": name, "attempt": t["attempt"],
                    "method_int": t["method_int"],
                    "method_name": METHOD_NAMES[t["method_int"]],
                    "correct": int(t["correct"]),
                    "pl_op": round(t["pl_op"], 4), "pl_th": round(t["pl_th"], 4),
                    **{f"q_{METHOD_NAMES[i].lower().split('/')[0]}": round(t["q_vals"][i], 4) for i in range(5)},
                })
        with out.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader(); w.writerows(rows)
        self._log(f"[EXPORT] {out}")


def open_sim_lab(parent_root=None):
    if parent_root is not None:
        win = tk.Toplevel(parent_root)
        win.title("HESTIA — Simulation Lab 🔬")
        win.geometry("1400x820")
        SimLabApp(win)
    else:
        root = tk.Tk()
        SimLabApp(root)
        root.mainloop()


if __name__ == "__main__":
    open_sim_lab()
