import tkinter as tk
from tkinter import ttk
import time
import json
import os
import random
import math
import sys

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from bridge.hestia_bridge import get_bridge

try:
    from bridge.hestia_bridge import METHOD as HESTIA_METHOD
except Exception:
    HESTIA_METHOD = None

COLORS = {
    "clinical_bg": "#F5F7FA",
    "clinical_text": "#2C3E50",
    "clinical_btn": "#3498DB",
    "clinical_btn_hover": "#2980B9",
    "eng_bg": "#111622",
    "eng_surface": "#1A2033",
    "eng_text": "#EEF0F8",
    "eng_text_dim": "#9398B8",
    "eng_accent": "#00A3E0",
    "eng_accent_gold": "#E8A84A",
    "success": "#52C97A",
    "error": "#E8526A",
    "warning": "#F39C12",
}

class TelemetryDashboard(tk.Frame):
    def __init__(self, parent, bridge=None, student_id=1):
        super().__init__(parent, bg=COLORS["eng_bg"])
        self.pack_propagate(False)
        
        self._bridge = bridge
        self._sid = student_id
        
        # Load content graph
        base_dir = os.path.dirname(os.path.abspath(__file__)) + "/../"
        cg_path = os.path.join(base_dir, "data", "content_graph.json")
        try:
            with open(cg_path, "r", encoding="utf-8") as f:
                self.content = json.load(f).get("skills", {})
        except Exception as e:
            print("Error loading content_graph:", e)
            self.content = {}

        self.skill_ids = list(self.content.keys())
        self.current_skill_id = int(self.skill_ids[0]) if self.skill_ids else 0
        
        if HESTIA_METHOD:
            self.current_method = HESTIA_METHOD.VISUAL
        else:
            self.current_method = 0
            
        self.method_names = ["VISUAL", "AUDITORY", "KINESTHETIC", "PHONETIC", "GLOBAL"]
        
        # State tracking
        self.pL_op = 0.20
        self.pT = 0.10
        self.pG = 0.25
        self.pS = 0.10
        self.pF = 0.50
        self.streak = 0
        self.fatigue = 1.0
        self.method_states = {m: {"q_value": 0.0, "attempts": 0} for m in self.method_names}
        self.total_attempts = 0
        
        self._build_layout()
        self._sync_state()
        self._load_next_question()

    def _build_layout(self):
        # Split-screen 40/60
        self.paned = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        self.paned.pack(fill="both", expand=True)

        self.clinical_panel = tk.Frame(self.paned, bg=COLORS["clinical_bg"])
        self.eng_panel = tk.Frame(self.paned, bg=COLORS["eng_bg"])

        self.paned.add(self.clinical_panel, weight=4) # 40%
        self.paned.add(self.eng_panel, weight=6) # 60%

        self._build_clinical_panel()
        self._build_eng_panel()

    def _build_clinical_panel(self):
        bg = COLORS["clinical_bg"]
        
        # Header: Progress bar
        self.prog_var = tk.DoubleVar(value=0)
        style = ttk.Style()
        style.theme_use('default')
        style.configure("Clinical.Horizontal.TProgressbar", thickness=12, background=COLORS["success"], troughcolor="#E2E8F0")
        
        self.prog_bar = ttk.Progressbar(self.clinical_panel, variable=self.prog_var, maximum=100, style="Clinical.Horizontal.TProgressbar")
        self.prog_bar.pack(fill="x", padx=40, pady=(40, 20))
        
        # Central Canvas: Stimulus
        self.stimulus_canvas = tk.Canvas(self.clinical_panel, bg=bg, highlightthickness=0)
        self.stimulus_canvas.pack(fill="both", expand=True, padx=40)
        
        self.stimulus_text = self.stimulus_canvas.create_text(
            400, 250, text="...", font=("Helvetica", 96, "bold"), fill=COLORS["clinical_text"], anchor="center", justify="center", width=700
        )
        
        # Footer: Interaction Buttons
        self.btn_frame = tk.Frame(self.clinical_panel, bg=bg)
        self.btn_frame.pack(fill="x", padx=40, pady=40)
        
        self.opt_btns = []
        for i in range(4):
            btn = tk.Button(
                self.btn_frame, text="", font=("Helvetica", 28, "bold"),
                bg=COLORS["clinical_btn"], fg="white", activebackground=COLORS["clinical_btn_hover"], activeforeground="white",
                relief="flat", cursor="hand2", padx=20, pady=10
            )
            btn.pack(side="left", fill="x", expand=True, padx=10)
            self.opt_btns.append(btn)

    def _build_eng_panel(self):
        bg = COLORS["eng_bg"]
        
        # Header BKT
        bkt_frame = tk.Frame(self.eng_panel, bg=bg)
        bkt_frame.pack(fill="x", padx=20, pady=(20, 10))
        
        self.pl_lbl = tk.Label(bkt_frame, text="P(L) = 0.200", font=("Courier", 48, "bold"), bg=bg, fg=COLORS["eng_accent"])
        self.pl_lbl.pack(side="left", padx=20)
        
        params_f = tk.Frame(bkt_frame, bg=bg)
        params_f.pack(side="left", padx=20)
        
        self.p_lbls = {}
        for row, param in enumerate([("P(T)", "pT"), ("P(G)", "pG"), ("P(S)", "pS"), ("P(F)", "pF"), ("Fatiga", "fatigue"), ("Racha", "streak")]):
            lbl = tk.Label(params_f, text=f"{param[0]}: 0.00", font=("Courier", 14), bg=bg, fg=COLORS["eng_text_dim"])
            lbl.grid(row=row//2, column=row%2, sticky="w", padx=15, pady=2)
            self.p_lbls[param[1]] = lbl

        # MAB Matplotlib Bar Chart
        mab_frame = tk.Frame(self.eng_panel, bg=COLORS["eng_surface"], bd=1, relief="solid")
        mab_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        tk.Label(mab_frame, text="MAB/UCB-1 Optimizer", font=("Helvetica", 12, "bold"), bg=COLORS["eng_surface"], fg=COLORS["eng_text"]).pack(anchor="w", padx=10, pady=5)
        
        self.fig = Figure(figsize=(6, 3), dpi=100, facecolor=COLORS["eng_surface"])
        self.ax = self.fig.add_subplot(111)
        self.ax.set_facecolor(COLORS["eng_surface"])
        self.ax.tick_params(colors=COLORS["eng_text_dim"])
        for spine in self.ax.spines.values():
            spine.set_color(COLORS["eng_surface"])
            
        self.canvas_agg = FigureCanvasTkAgg(self.fig, master=mab_frame)
        self.canvas_agg.get_tk_widget().pack(fill="both", expand=True)
        self._draw_mab_chart()

        # Flags & Logs
        bot_frame = tk.Frame(self.eng_panel, bg=bg)
        bot_frame.pack(fill="x", padx=20, pady=20)
        
        flags_f = tk.Frame(bot_frame, bg=bg)
        flags_f.pack(side="left")
        
        self.stall_led = tk.Canvas(flags_f, width=20, height=20, bg=bg, highlightthickness=0)
        self.stall_led.pack(side="left", padx=5)
        self.stall_circ = self.stall_led.create_oval(2, 2, 18, 18, fill="gray")
        tk.Label(flags_f, text="Anti-Stall", font=("Courier", 10), bg=bg, fg=COLORS["eng_text_dim"]).pack(side="left", padx=(0, 20))
        
        self.fatigue_led = tk.Canvas(flags_f, width=20, height=20, bg=bg, highlightthickness=0)
        self.fatigue_led.pack(side="left", padx=5)
        self.fatigue_circ = self.fatigue_led.create_oval(2, 2, 18, 18, fill="gray")
        tk.Label(flags_f, text="Fatiga", font=("Courier", 10), bg=bg, fg=COLORS["eng_text_dim"]).pack(side="left")

        # Terminal
        self.terminal = tk.Text(bot_frame, height=6, bg="#0A0C16", fg="#A8B0D3", font=("Courier", 10), bd=0, padx=10, pady=10)
        self.terminal.pack(side="right", fill="x", expand=True, padx=(20, 0))
        self.terminal.insert(tk.END, "[SYSTEM] HESTIA Demo Interface Started...\n")
        self.terminal.config(state="disabled")

    def _log(self, text, color="#A8B0D3"):
        self.terminal.config(state="normal")
        self.terminal.insert(tk.END, text + "\n")
        self.terminal.see(tk.END)
        self.terminal.config(state="disabled")

    def _sync_state(self):
        if not self._bridge:
            return
            
        try:
            state = self._bridge.storage.load_skill_state(self._sid, self.current_skill_id)
            if state:
                self.pL_op = state.pLearn_operative
                self.pT = state.pTransition
                self.pG = state.pGuess
                self.pS = state.pSlip
                self.pF = state.pForget
                self.streak = state.consecutive_correct
                
            session = self._bridge.processor.get_current_session()
            if session:
                # Mocking fatigue for demo based on attempts
                self.fatigue = 1.0 - (session.cumulative_total * 0.005)
                self.total_attempts = session.cumulative_total
                
            ms = self._bridge.get_method_states_for_ui(self._sid, self.current_skill_id)
            for m_name in self.method_names:
                if m_name in ms:
                    self.method_states[m_name] = ms[m_name]
                    
        except Exception as e:
            pass
            
        self._update_eng_ui()

    def _update_eng_ui(self):
        self.pl_lbl.config(text=f"P(L) = {self.pL_op:.3f}")
        self.prog_var.set(self.pL_op * 100)
        
        self.p_lbls["pT"].config(text=f"P(T): {self.pT:.2f}")
        self.p_lbls["pG"].config(text=f"P(G): {self.pG:.2f}")
        self.p_lbls["pS"].config(text=f"P(S): {self.pS:.2f}")
        self.p_lbls["pF"].config(text=f"P(F): {self.pF:.2f}")
        self.p_lbls["fatigue"].config(text=f"Fatiga: {self.fatigue:.2f}")
        self.p_lbls["streak"].config(text=f"Racha: {self.streak}")
        
        # LEDs
        if self.streak == 0 and self.total_attempts > 5:
            self.stall_led.itemconfig(self.stall_circ, fill=COLORS["error"])
        else:
            self.stall_led.itemconfig(self.stall_circ, fill="gray")
            
        if self.fatigue < 0.8:
            self.fatigue_led.itemconfig(self.fatigue_circ, fill=COLORS["warning"])
        else:
            self.fatigue_led.itemconfig(self.fatigue_circ, fill="gray")
            
        self._draw_mab_chart()

    def _draw_mab_chart(self):
        self.ax.clear()
        
        methods = self.method_names
        q_vals = [self.method_states[m]["q_value"] for m in methods]
        attempts = [self.method_states[m]["attempts"] for m in methods]
        
        # Calculate UCB bounds
        ucb_vals = []
        total_n = max(1, sum(attempts))
        for i in range(5):
            if attempts[i] == 0:
                ucb_vals.append(0.5) # Exploration bonus
            else:
                c = 1.0
                ucb = c * math.sqrt(math.log(total_n) / attempts[i])
                ucb_vals.append(ucb)
                
        y_pos = range(len(methods))
        colors = [COLORS["eng_accent_gold"] if i == (self.current_method.value if hasattr(self.current_method, 'value') else self.current_method) else COLORS["eng_accent"] for i in range(5)]
        
        self.ax.barh(y_pos, q_vals, xerr=ucb_vals, align='center', color=colors, ecolor=COLORS["eng_text"], capsize=5, alpha=0.8)
        self.ax.set_yticks(y_pos)
        self.ax.set_yticklabels(methods, color=COLORS["eng_text"])
        self.ax.invert_yaxis()  # labels read top-to-bottom
        self.ax.set_xlim(0, 1.5)
        
        self.fig.tight_layout()
        self.canvas_agg.draw()

    def _load_next_question(self):
        m_str = str(self.current_skill_id)
        skill_data = self.content.get(m_str)
        if not skill_data:
            self.stimulus_canvas.itemconfig(self.stimulus_text, text="Fin de Demo")
            for btn in self.opt_btns:
                btn.pack_forget()
            return
            
        m_name = self.method_names[self.current_method.value if hasattr(self.current_method, 'value') else self.current_method]
        arm_data = skill_data.get("arms", {}).get(m_name, {})
        
        stimulus = arm_data.get("stimulus", skill_data.get("name", "???"))
        
        w = self.stimulus_canvas.winfo_width()
        h = self.stimulus_canvas.winfo_height()
        self.stimulus_canvas.coords(self.stimulus_text, w/2 if w>10 else 400, h/2 if h>10 else 250)
        self.stimulus_canvas.itemconfig(self.stimulus_text, text=stimulus)
        
        options = arm_data.get("options", ["A", "B", "C", "D"])
        random.shuffle(options)
        
        self.correct_ans = skill_data.get("correct", options[0])
        self.t0 = time.time()
        
        for i, btn in enumerate(self.opt_btns):
            if i < len(options):
                opt = options[i]
                btn.config(text=opt, state="normal")
                btn.bind("<Button-1>", lambda e, o=opt: self._on_answer(o))
            else:
                btn.config(text="", state="disabled")
                
    def _on_answer(self, chosen):
        if not self._bridge:
            return
            
        correct = (chosen == self.correct_ans)
        t1 = time.time()
        resp_ms = (t1 - self.t0) * 1000.0
        
        # Disable buttons
        for btn in self.opt_btns:
            btn.config(state="disabled")
            
        # Process in bridge
        try:
            if hasattr(self._bridge, "process_response_timed"):
                result, lat_ms, logs = self._bridge.process_response_timed(
                    self._sid, self.current_skill_id, self.current_method, correct, resp_ms
                )
                for log in logs:
                    self._log(log)
            else:
                result = self._bridge.process_response(
                    self._sid, self.current_skill_id, self.current_method, correct, resp_ms
                )
                self._log(f"[C++] Respuesta procesada. P(L) -> {result.current_pL:.3f}")
                
            self.current_skill_id = result.next_skill_id
            self.current_method = result.next_method
            
        except Exception as e:
            self._log(f"[ERROR] {e}", color=COLORS["error"])
            
        self._sync_state()
        self.after(500, self._load_next_question)
