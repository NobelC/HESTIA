import os
import sys
import time
import random
import sqlite3
import threading
import traceback
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path

# Fix paths to find src and bridge
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "src"))

from src.ContentLoader import ContentLoader
from src.AudioPlayer import AudioPlayer
from frontend.bridge.hestia_bridge import get_bridge, METHOD
from frontend.sim_lab import open_sim_lab

# BUG FIX: Some JSON files use int method_ids (0, 3) and some use strings ("M1_visual").
# We normalize everything to INT internally but provide maps for both.
METHOD_INT_TO_ENUM = {
    0: METHOD.VISUAL, 1: METHOD.AUDITORY, 2: METHOD.KINESTHETIC, 3: METHOD.PHONETIC, 4: METHOD.GLOBAL,
    "M1_visual": METHOD.VISUAL, "M2_auditivo": METHOD.AUDITORY,
    "M3_kinestesico": METHOD.KINESTHETIC, "M4_fonetico": METHOD.PHONETIC, "M5_global": METHOD.GLOBAL,
}

METHOD_INT_TO_LABEL = {
    0: "Visual", 1: "Auditivo", 2: "Kinestésico", 3: "Fonético", 4: "Global/contextual",
    "M1_visual": "Visual", "M2_auditivo": "Auditivo",
    "M3_kinestesico": "Kinestésico", "M4_fonetico": "Fonético", "M5_global": "Global/contextual",
}

METHOD_INT_TO_ICON = {
    0: "👁️", 1: "👂", 2: "✋", 3: "🗣️", 4: "🧩",
    "M1_visual": "👁️", "M2_auditivo": "👂",
    "M3_kinestesico": "✋", "M4_fonetico": "🗣️", "M5_global": "🧩",
}

METHOD_STR_TO_INT = {
    "M1_visual": 0, "M2_auditivo": 1, "M3_kinestesico": 2, "M4_fonetico": 3, "M5_global": 4,
    0: 0, 1: 1, 2: 2, 3: 3, 4: 4
}

METHOD_ENUM_TO_INT = {
    METHOD.VISUAL: 0,
    METHOD.AUDITORY: 1,
    METHOD.KINESTHETIC: 2,
    METHOD.PHONETIC: 3,
    METHOD.GLOBAL: 4,
}

METHOD_CPP_NAME_TO_INT = {
    "VISUAL": 0,
    "AUDITORY": 1,
    "KINESTHETIC": 2,
    "PHONETIC": 3,
    "GLOBAL": 4,
}

SKILL_STR_TO_INT = {
    "vocal_a": 0, "vocal_e": 1, "vocal_i": 2, "vocal_o": 3, "vocal_u": 4,
    "numero_1": 5, "numero_2": 6, "numero_3": 7, "numero_4": 8,
    "limites_concepto": 9, "limites_sustitucion_directa": 10,
    "limites_indeterminacion": 11, "limites_factorizacion": 12
}
# If JSON exercises already use ints, this safely returns the int
def get_skill_int(skill_val):
    if isinstance(skill_val, int):
        return skill_val
    return SKILL_STR_TO_INT.get(skill_val, 0)

MODULES = {
    "Vocales": "vocales.json",
    "Números": "numeros.json",
    "Límites": "limites.json",
}

PROFILES = [
    "Visual fuerte",
    "Fonético fuerte",
    "Lento y consistente",
    "Alta variabilidad",
    "Balanceado",
]

class HestiaDemoApp:
    def __init__(self, root):
        self.root = root
        self.root.title("HESTIA - Demo adaptativa BKT + MAB")
        self.root.geometry("1200x720")
        self.root.minsize(1100, 660)
        self.root.configure(bg="#f5f7fa")

        self.loader = ContentLoader()
        self.db_path = str(BASE_DIR / "hestia.db")
        self.bridge = get_bridge(self.db_path)
        self.audio_player = AudioPlayer(BASE_DIR)

        self.id_user = None
        self.content = None
        self.current_exercise = None
        self.current_method_enum = None
        self.start_time = None
        self.exercises = []
        # BUG FIX: track methods supported by active module (int ids)
        self.supported_method_ids = set()

        self.last_decision = {"phase": "Exploración", "led_color": "#3498db"}
        self.last_logs = []
        self.current_pl = 0.0
        self.current_pl_theorical = 0.0

        self.selected_module = tk.StringVar(value="Vocales")
        self.selected_profile = tk.StringVar(value=PROFILES[0])

        self.show_start()

    def clear(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    def show_start(self):
        self.clear()
        
        main_frame = tk.Frame(self.root, bg="#ffffff")
        main_frame.pack(fill="both", expand=True)

        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(0, weight=1)

        # Left side - Guide
        left_frame = tk.Frame(main_frame, bg="#f8f9fa", padx=50, pady=50)
        left_frame.grid(row=0, column=0, sticky="nsew")

        tk.Label(left_frame, text="HESTIA", font=("Arial", 48, "bold"), fg="#2c3e50", bg="#f8f9fa").pack(anchor="w", pady=(0, 20))
        tk.Label(left_frame, text="Guía Rápida", font=("Arial", 20, "bold"), fg="#34495e", bg="#f8f9fa").pack(anchor="w", pady=(0, 20))

        guide_steps = [
            ("01", "Selecciona un módulo de estudio."),
            ("02", "Elige un perfil de estudiante sintético."),
            ("03", "Observa cómo MAB optimiza el aprendizaje.")
        ]

        for num, text in guide_steps:
            step_frame = tk.Frame(left_frame, bg="#f8f9fa")
            step_frame.pack(fill="x", pady=15)
            tk.Label(step_frame, text=num, font=("Courier New", 24, "bold"), fg="#3498db", bg="#f8f9fa", width=3, anchor="w").pack(side="left")
            tk.Label(step_frame, text=text, font=("Arial", 14), fg="#7f8c8d", bg="#f8f9fa", wraplength=350, justify="left").pack(side="left", fill="x", expand=True)

        # Right side - Config
        right_frame = tk.Frame(main_frame, bg="#ffffff", padx=50, pady=50)
        right_frame.grid(row=0, column=1, sticky="nsew")

        config_container = tk.Frame(right_frame, bg="#ffffff")
        config_container.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(config_container, text="Configuración", font=("Arial", 24, "bold"), fg="#2c3e50", bg="#ffffff").pack(anchor="w", pady=(0, 30))

        tk.Label(config_container, text="Módulo educativo", font=("Arial", 12, "bold"), fg="#7f8c8d", bg="#ffffff").pack(anchor="w", pady=(0, 5))
        combo_module = ttk.Combobox(config_container, textvariable=self.selected_module, values=list(MODULES.keys()), state="readonly", font=("Arial", 14), width=24)
        combo_module.pack(fill="x", pady=(0, 20), ipady=5)

        tk.Label(config_container, text="Perfil sintético", font=("Arial", 12, "bold"), fg="#7f8c8d", bg="#ffffff").pack(anchor="w", pady=(0, 5))
        combo_profile = ttk.Combobox(config_container, textvariable=self.selected_profile, values=PROFILES, state="readonly", font=("Arial", 14), width=24)
        combo_profile.pack(fill="x", pady=(0, 40), ipady=5)
        
        btn_start = tk.Button(
            config_container, text="INICIAR DEMO", font=("Arial", 16, "bold"),
            bg="#3498db", fg="white", activebackground="#2980b9", activeforeground="white",
            relief="flat", cursor="hand2", command=self.start_session, pady=15
        )
        btn_start.pack(fill="x")

        btn_sim = tk.Button(
            config_container, text="🔬 SIM LAB", font=("Arial", 12, "bold"),
            bg="#ecf0f1", fg="#2c3e50", activebackground="#bdc3c7", activeforeground="#2c3e50",
            relief="flat", cursor="hand2", command=self.open_sim_lab_window, pady=10
        )
        btn_sim.pack(fill="x", pady=(15, 0))

    def open_sim_lab_window(self):
        open_sim_lab(self.root)

    def start_session(self):
        module_file = MODULES[self.selected_module.get()]
        self.content = self.loader.cargar_modulo(BASE_DIR, module_file)

        # BUG FIX: collect supported method int ids from the actual exercise data
        self.exercises = self.content.get("exercises", [])
        self.supported_method_ids = {METHOD_STR_TO_INT.get(e["method_id"], 0) for e in self.exercises}

        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute("CREATE TABLE IF NOT EXISTS user_profile (id INTEGER PRIMARY KEY, name TEXT, profile_type TEXT)")
            cur.execute(
                "INSERT INTO user_profile (name, profile_type) VALUES (?, ?)",
                ("Estudiante Demo", self.selected_profile.get())
            )
            conn.commit()
            self.id_user = cur.lastrowid

        self.current_pl = 0.0
        self.current_pl_theorical = 0.0
        self.last_decision = {"phase": "Exploración", "led_color": "#3498db"}
        self.last_logs = []

        self.current_exercise = random.choice(self.exercises)
        # BUG FIX: method_id in JSON is int — use int map directly
        self.current_method_enum = METHOD_INT_TO_ENUM[self.current_exercise["method_id"]]

        skill_id_int = get_skill_int(self.current_exercise["skill_id"])
        self.bridge.start_session(self.id_user, skill_id_int)

        self.show_exercise_screen()
        self.load_next_exercise()

    def show_exercise_screen(self):
        self.clear()

        main_frame = tk.Frame(self.root, bg="#f5f7fa")
        main_frame.pack(fill="both", expand=True)
        main_frame.columnconfigure(0, weight=6)
        main_frame.columnconfigure(1, weight=4)
        main_frame.rowconfigure(0, weight=1)

        # Left Panel (Student)
        self.left_panel = tk.Frame(main_frame, bg="#ffffff", padx=30, pady=20)
        self.left_panel.grid(row=0, column=0, sticky="nsew")

        header_frame = tk.Frame(self.left_panel, bg="#ffffff")
        header_frame.pack(fill="x", pady=(0, 20))
        
        tk.Button(header_frame, text="Salir", command=self.show_final, relief="flat", bg="#ecf0f1", padx=10).pack(side="right")
        tk.Button(header_frame, text="🔄 Nuevo Estudiante", command=self.start_session, relief="flat", bg="#fef9e7", fg="#f39c12", padx=10).pack(side="right", padx=(0, 10))
        self.module_label = tk.Label(header_frame, text="Módulo", font=("Arial", 12, "bold"), fg="#95a5a6", bg="#ffffff")
        self.module_label.pack(side="left")

        # Mastery Bar Canvas
        mastery_frame = tk.Frame(self.left_panel, bg="#ffffff")
        mastery_frame.pack(fill="x", pady=(0, 30))
        tk.Label(mastery_frame, text="Progreso de Maestría P(L)", font=("Arial", 10, "bold"), fg="#7f8c8d", bg="#ffffff").pack(anchor="w", pady=(0, 5))
        self.mastery_canvas = tk.Canvas(mastery_frame, height=12, bg="#ecf0f1", highlightthickness=0)
        self.mastery_canvas.pack(fill="x")
        self.mastery_rect = self.mastery_canvas.create_rectangle(0, 0, 0, 12, fill="#a0c4ff", outline="")

        # Stimulus Area
        self.stimulus_frame = tk.Frame(self.left_panel, bg="#f8f9fa", padx=20, pady=40)
        self.stimulus_frame.pack(fill="both", expand=True, pady=(0, 20))
        
        self.method_icon_label = tk.Label(self.stimulus_frame, text="👁️", font=("Arial", 24), bg="#f8f9fa")
        self.method_icon_label.place(relx=1.0, rely=0.0, anchor="ne")

        self.question_label = tk.Label(self.stimulus_frame, text="", font=("Arial", 28, "bold"), fg="#2c3e50", bg="#f8f9fa", wraplength=550, justify="center")
        self.question_label.pack(expand=True)

        self.audio_button = tk.Button(
            self.stimulus_frame, text="🔊 Reproducir Audio", font=("Arial", 12),
            bg="#ecf0f1", fg="#2c3e50", relief="flat", cursor="hand2", command=self.play_current_audio, padx=10, pady=5
        )

        # Response Buttons
        self.options_frame = tk.Frame(self.left_panel, bg="#ffffff")
        self.options_frame.pack(fill="x", pady=10)
        self.options_frame.columnconfigure((0, 1), weight=1)

        self.option_buttons = []
        for i in range(4):
            btn = tk.Button(
                self.options_frame, text="", font=("Arial", 16),
                bg="#f1f2f6", fg="#2f3542", activebackground="#dfe4ea", activeforeground="#2f3542",
                relief="flat", cursor="hand2", command=lambda i=i: self.answer(i), pady=15
            )
            btn.grid(row=i//2, column=i%2, padx=10, pady=10, sticky="nsew")
            self.option_buttons.append(btn)

        # 1px Divider
        divider = tk.Frame(main_frame, bg="#dcdde1", width=1)
        divider.grid(row=0, column=0, sticky="ne", rowspan=2)

        # Right Panel (Engineering)
        self.right_panel = tk.Frame(main_frame, bg="#ffffff", padx=20, pady=15)
        self.right_panel.grid(row=0, column=1, sticky="nsew")

        # — Dual-channel P(L) display —
        status_frame = tk.Frame(self.right_panel, bg="#ffffff")
        status_frame.pack(fill="x", pady=(0, 10))

        tk.Label(status_frame, text="DOMINIO COMPUTADO", font=("Courier New", 9, "bold"), fg="#7f8c8d", bg="#ffffff").pack(anchor="center")
        self.pl_value_label = tk.Label(status_frame, text="0.00", font=("Courier New", 44, "bold"), fg="#2c3e50", bg="#ffffff")
        self.pl_value_label.pack(anchor="center")

        # Dual-channel row: operativo vs teórico
        dual_frame = tk.Frame(status_frame, bg="#ffffff")
        dual_frame.pack(anchor="center", pady=(2, 0))
        tk.Label(dual_frame, text="Op:", font=("Courier New", 9), fg="#7f8c8d", bg="#ffffff").pack(side="left")
        self.pl_op_label = tk.Label(dual_frame, text="0.000", font=("Courier New", 9, "bold"), fg="#3498db", bg="#ffffff")
        self.pl_op_label.pack(side="left", padx=(2, 10))
        tk.Label(dual_frame, text="Teórico:", font=("Courier New", 9), fg="#7f8c8d", bg="#ffffff").pack(side="left")
        self.pl_th_label = tk.Label(dual_frame, text="0.000", font=("Courier New", 9, "bold"), fg="#9b59b6", bg="#ffffff")
        self.pl_th_label.pack(side="left", padx=(2, 0))

        # Status LED + phase
        led_frame = tk.Frame(status_frame, bg="#ffffff")
        led_frame.pack(anchor="center", pady=(5, 0))
        self.status_led_canvas = tk.Canvas(led_frame, width=16, height=16, bg="#ffffff", highlightthickness=0)
        self.status_led_canvas.pack(side="left", padx=(0, 5))
        self.status_led = self.status_led_canvas.create_oval(2, 2, 14, 14, fill="#3498db", outline="")
        self.status_label = tk.Label(led_frame, text="Fase: Exploración", font=("Courier New", 11), fg="#7f8c8d", bg="#ffffff")
        self.status_label.pack(side="left")

        # Anti-stall / anomaly badges
        badge_frame = tk.Frame(status_frame, bg="#ffffff")
        badge_frame.pack(anchor="center", pady=(4, 0))
        self.badge_stall = tk.Label(badge_frame, text="⚡ Anti-Stall", font=("Courier New", 8, "bold"),
                                    fg="#e74c3c", bg="#fdecea", padx=4, pady=2, relief="flat")
        self.badge_anomaly = tk.Label(badge_frame, text="⚠ Tiempo filtrado", font=("Courier New", 8, "bold"),
                                      fg="#e67e22", bg="#fef5e7", padx=4, pady=2, relief="flat")
        self.badge_mastered = tk.Label(badge_frame, text="✓ Dominado", font=("Courier New", 8, "bold"),
                                       fg="#27ae60", bg="#eafaf1", padx=4, pady=2, relief="flat")

        # MAB bars
        mab_frame = tk.Frame(self.right_panel, bg="#ffffff")
        mab_frame.pack(fill="x", pady=(10, 5))
        tk.Label(mab_frame, text="Q-VALUES  MAB (brazos activos)", font=("Courier New", 9, "bold"), fg="#7f8c8d", bg="#ffffff").pack(anchor="w", pady=(0, 6))
        self.mab_canvas = tk.Canvas(mab_frame, height=145, bg="#ffffff", highlightthickness=0)
        self.mab_canvas.pack(fill="x")

        log_frame = tk.Frame(self.right_panel, bg="#111622", padx=10, pady=10)
        log_frame.pack(fill="both", expand=True)
        tk.Label(log_frame, text=">_ ENGINE LOG", font=("Courier New", 10, "bold"), fg="#34495e", bg="#111622").pack(anchor="w", pady=(0, 5))
        
        self.log_text = tk.Text(log_frame, bg="#111622", fg="#00FF9D", font=("Courier New", 9), relief="flat", wrap="word", highlightthickness=0)
        self.log_text.pack(fill="both", expand=True)

    def get_method_icon(self, method_id_int):
        return METHOD_INT_TO_ICON.get(method_id_int, "💡")

    def load_next_exercise(self):
        ex = self.current_exercise
        method_id_raw = ex["method_id"]
        method_id_int = METHOD_STR_TO_INT.get(method_id_raw, 0)
        skill_id_int = get_skill_int(ex["skill_id"])    # int

        topic = self.content.get("topic", "")
        method_label = METHOD_INT_TO_LABEL.get(method_id_int, str(method_id_int))
        self.module_label.config(text=f"{topic}  |  Skill {skill_id_int}  |  {method_label}")

        self.method_icon_label.config(text=self.get_method_icon(method_id_int))
        self.question_label.config(text=ex["question"])

        audio_path = ex.get("audio_path", "")
        if audio_path:
            self.audio_button.pack(pady=(20, 0))
        else:
            self.audio_button.pack_forget()

        for i, option in enumerate(ex["options"]):
            self.option_buttons[i].config(text=option, state="normal", bg="#f1f2f6", fg="#2f3542")

        self.start_time = time.time()
        self.update_engineering_panel()
        self.write_log(self.last_logs)

        # Auto-play only for truly auditory/phonetic exercises (int ids 1 and 3)
        if method_id_int in (1, 3) and audio_path:
            self.root.after(350, self.play_current_audio)

    def play_current_audio(self):
        if not self.current_exercise:
            return
        audio_path = self.current_exercise.get("audio_path", "")
        ok, msg = self.audio_player.play(audio_path)
        if not ok:
            self.write_log([f"⚠️ [WARN] Audio resource '{os.path.basename(audio_path)}' no disponible."])

    def answer(self, index):
        ex = self.current_exercise
        elapsed_ms = int((time.time() - self.start_time) * 1000)
        selected = ex["options"][index]
        is_correct = selected == ex["correct_answer"]

        for i, btn in enumerate(self.option_buttons):
            btn.config(state="disabled")
            if i == index:
                if is_correct:
                    btn.config(bg="#e8f8f5", fg="#1abc9c")
                else:
                    btn.config(bg="#fdedec", fg="#e74c3c")
            elif ex["options"][i] == ex["correct_answer"] and not is_correct:
                btn.config(bg="#fef9e7", fg="#f1c40f")

        # BUG FIX: skill_id is now directly an int in the JSON
        skill_id_int = get_skill_int(ex["skill_id"])
        result, latency, logs = self.bridge.process_response_timed(
            self.id_user, skill_id_int, self.current_method_enum, is_correct, elapsed_ms
        )

        self.last_logs = logs
        self.current_pl = result.current_pL
        self.current_pl_theorical = result.current_pL_theorical

        # Phase logic: use attempt count & result flags
        is_anomalous = result.was_anomalous
        is_newly_mastered = result.newly_mastered

        # LED phase derived from BKT channel gap (anti-stall = op much lower than theorical)
        gap = self.current_pl_theorical - self.current_pl
        if is_newly_mastered:
            phase, led_color = "Dominado", "#27ae60"
        elif gap > 0.25 and self.current_pl > 0.0:
            phase, led_color = "Anti-Stall", "#e74c3c"
        elif self.current_pl > 0.4:
            phase, led_color = "Explotación", "#2ecc71"
        else:
            phase, led_color = "Exploración", "#3498db"

        self.last_decision = {
            "phase": phase,
            "led_color": led_color,
            "is_anomalous": is_anomalous,
            "is_newly_mastered": is_newly_mastered,
            "next_method_int": METHOD_ENUM_TO_INT.get(result.next_method, 0),
        }

        self.update_engineering_panel()
        self.write_log(self.last_logs)

        # BUG FIX: match by int skill_id and int method_id
        next_skill_id_int = result.next_skill_id
        next_method_int = METHOD_ENUM_TO_INT.get(result.next_method, 0)

        # BUG FIX: filter to only supported methods (ghost exploration fix)
        if next_method_int not in self.supported_method_ids and self.supported_method_ids:
            next_method_int = random.choice(list(self.supported_method_ids))

        matching = [e for e in self.exercises
                    if e["skill_id"] == next_skill_id_int and METHOD_STR_TO_INT.get(e["method_id"], 0) == next_method_int]
        if not matching:
            matching = [e for e in self.exercises if METHOD_STR_TO_INT.get(e["method_id"], 0) == next_method_int]
        if not matching:
            matching = self.exercises

        self.current_exercise = random.choice(matching)
        self.current_method_enum = METHOD_INT_TO_ENUM[self.current_exercise["method_id"]]

        self.root.after(1000, self.load_next_exercise)

    def update_engineering_panel(self):
        # Mastery bar (operative channel only)
        self.mastery_canvas.update_idletasks()
        max_width = self.mastery_canvas.winfo_width()
        bar_width = max(0, min(max_width, int(self.current_pl * max_width)))
        self.mastery_canvas.coords(self.mastery_rect, 0, 0, bar_width, 12)

        # Dual-channel labels
        self.pl_value_label.config(text=f"{self.current_pl:.2f}")
        self.pl_op_label.config(text=f"{self.current_pl:.3f}")
        self.pl_th_label.config(text=f"{self.current_pl_theorical:.3f}")

        # LED phase
        phase = self.last_decision.get("phase", "Exploración")
        self.status_led_canvas.itemconfig(self.status_led, fill=self.last_decision.get("led_color", "#3498db"))
        self.status_label.config(text=f"Fase: {phase}")

        # Badges (show/hide conditionally)
        for badge in (self.badge_stall, self.badge_anomaly, self.badge_mastered):
            badge.pack_forget()
        if phase == "Anti-Stall":
            self.badge_stall.pack(side="left", padx=3)
        if self.last_decision.get("is_anomalous"):
            self.badge_anomaly.pack(side="left", padx=3)
        if self.last_decision.get("is_newly_mastered"):
            self.badge_mastered.pack(side="left", padx=3)

        # BUG FIX: expose real traceback in log instead of silently returning defaults
        skill_id_int = get_skill_int(self.current_exercise["skill_id"])
        try:
            states = self.bridge.get_method_states_for_ui(self.id_user, skill_id_int)
        except Exception:
            tb = traceback.format_exc()
            self.write_log([f"[ERROR] get_method_states_for_ui falló:", tb])
            states = {}

        self.mab_canvas.delete("all")
        self.mab_canvas.update_idletasks()
        cw = max(self.mab_canvas.winfo_width(), 200)

        y = 8
        bar_h = 18
        gap = 8
        METHOD_COLORS = {
            "VISUAL": "#a0c4ff", "AUDITORY": "#b9fbc0",
            "KINESTHETIC": "#ffd6a5", "PHONETIC": "#ffadad", "GLOBAL": "#d0d0ff"
        }
        GHOST_COLOR = "#ecf0f1"  # methods not in module — shown dimmed

        for cpp_name, s in states.items():
            method_int = METHOD_CPP_NAME_TO_INT.get(cpp_name, -1)
            label = METHOD_INT_TO_LABEL.get(method_int, cpp_name)
            q_val = s["q_value"]
            is_ghost = method_int not in self.supported_method_ids

            # Label text — ghost methods in gray
            txt_color = "#bdc3c7" if is_ghost else "#2c3e50"
            self.mab_canvas.create_text(5, y + bar_h / 2, text=label,
                                        font=("Courier New", 9), anchor="w", fill=txt_color)

            bar_max_w = cw - 140
            bar_w = max(2, int(q_val * bar_max_w))
            fill_color = GHOST_COLOR if is_ghost else METHOD_COLORS.get(cpp_name, "#bdc3c7")
            self.mab_canvas.create_rectangle(115, y, 115 + bar_w, y + bar_h,
                                             fill=fill_color, outline="")
            q_txt = f"{q_val:.3f}" + (" [ghost]" if is_ghost else "")
            self.mab_canvas.create_text(120 + bar_w, y + bar_h / 2, text=q_txt,
                                        font=("Courier New", 8), anchor="w",
                                        fill="#bdc3c7" if is_ghost else "#2c3e50")
            y += bar_h + gap

    def write_log(self, lines):
        if not lines:
            return
        self.log_text.insert("end", "\n".join(lines) + "\n\n")
        self.log_text.see("end")

    def show_final(self):
        self.show_start()


if __name__ == "__main__":
    root = tk.Tk()
    app = HestiaDemoApp(root)
    root.mainloop()
