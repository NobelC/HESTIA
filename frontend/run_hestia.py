import os
import sys
import time
import random
import sqlite3
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

METHOD_LABELS = {
    "M1_visual": "Visual",
    "M2_auditivo": "Auditivo",
    "M3_kinestesico": "Kinestésico",
    "M4_fonetico": "Fonético",
    "M5_global": "Global/contextual",
}

METHOD_STR_TO_ENUM = {
    "M1_visual": METHOD.VISUAL,
    "M2_auditivo": METHOD.AUDITORY,
    "M3_kinestesico": METHOD.KINESTHETIC,
    "M4_fonetico": METHOD.PHONETIC,
    "M5_global": METHOD.GLOBAL,
}

METHOD_ENUM_TO_STR = {
    METHOD.VISUAL: "M1_visual",
    METHOD.AUDITORY: "M2_auditivo",
    METHOD.KINESTHETIC: "M3_kinestesico",
    METHOD.PHONETIC: "M4_fonetico",
    METHOD.GLOBAL: "M5_global",
}

METHOD_LABELS_FROM_CPP = {
    "VISUAL": "Visual",
    "AUDITORY": "Auditivo",
    "KINESTHETIC": "Kinestésico",
    "PHONETIC": "Fonético",
    "GLOBAL": "Global/contextual"
}

SKILL_STR_TO_INT = {
    "vocal_a": 0,
    "vocal_e": 1,
    "vocal_i": 2,
    "vocal_o": 3,
    "vocal_u": 4,
    "numero_1": 5,
    "numero_2": 6,
    "numero_3": 7,
    "numero_4": 8,
    "limites_concepto": 9,
    "limites_sustitucion_directa": 10,
    "limites_indeterminacion": 11,
    "limites_factorizacion": 12
}

SKILL_INT_TO_STR = {v: k for k, v in SKILL_STR_TO_INT.items()}

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
        self.root.geometry("1080x700")
        self.root.minsize(1000, 640)

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

        self.last_decision = {"phase": "inicio", "recommended_method": None}
        self.last_logs = []

        self.selected_module = tk.StringVar(value="Vocales")
        self.selected_profile = tk.StringVar(value=PROFILES[0])
        self.feedback_var = tk.StringVar(value="")
        self.metrics_var = tk.StringVar(value="")
        self.recommendation_var = tk.StringVar(value="")
        self.study_hint_var = tk.StringVar(value="")

        self.show_start()

    def clear(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    def show_start(self):
        self.clear()
        frame = ttk.Frame(self.root, padding=30)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text="HESTIA", font=("Arial", 38, "bold")).pack(pady=10)
        ttk.Label(
            frame,
            text="Demo técnica adaptativa: BKT estima dominio y MAB/UCB cambia el método de estudio",
            font=("Arial", 15)
        ).pack(pady=5)

        box = ttk.LabelFrame(frame, text="Configuración de la sesión", padding=20)
        box.pack(pady=25)

        ttk.Label(box, text="Módulo educativo:").grid(row=0, column=0, sticky="w", padx=10, pady=10)
        ttk.Combobox(box, textvariable=self.selected_module, values=list(MODULES.keys()), state="readonly", width=24).grid(row=0, column=1, padx=10, pady=10)

        ttk.Label(box, text="Perfil sintético:").grid(row=1, column=0, sticky="w", padx=10, pady=10)
        ttk.Combobox(box, textvariable=self.selected_profile, values=PROFILES, state="readonly", width=24).grid(row=1, column=1, padx=10, pady=10)

        ttk.Button(frame, text="Iniciar demo", command=self.start_session).pack(pady=20)

        info = (
            "Ahora la demo no solo muestra porcentajes:\n"
            "• Primero explora métodos.\n"
            "• Luego recomienda el método que mejor le funciona al perfil.\n"
            "• Después prioriza ese método en los siguientes ejercicios."
        )
        ttk.Label(frame, text=info, justify="center", font=("Arial", 12)).pack(pady=15)

    def start_session(self):
        module_file = MODULES[self.selected_module.get()]
        self.content = self.loader.cargar_modulo(BASE_DIR, module_file)
        
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute("CREATE TABLE IF NOT EXISTS user_profile (id INTEGER PRIMARY KEY, name TEXT, profile_type TEXT)")
            cur.execute(
                "INSERT INTO user_profile (name, profile_type) VALUES (?, ?)",
                ("Estudiante Demo", self.selected_profile.get())
            )
            conn.commit()
            self.id_user = cur.lastrowid
            
        self.exercises = self.content.get("exercises", [])
        self.current_exercise = random.choice(self.exercises)
        self.current_method_enum = METHOD_STR_TO_ENUM[self.current_exercise["method_id"]]
        
        skill_id_int = SKILL_STR_TO_INT.get(self.current_exercise["skill_id"], 0)
        self.bridge.start_session(self.id_user, skill_id_int)

        self.show_exercise_screen()
        self.load_next_exercise()

    def show_exercise_screen(self):
        self.clear()

        top = ttk.Frame(self.root, padding=10)
        top.pack(fill="x")

        ttk.Label(top, text="HESTIA - Demo adaptativa", font=("Arial", 22, "bold")).pack(side="left")
        ttk.Button(top, text="Finalizar sesión", command=self.show_final).pack(side="right", padx=10)

        main = ttk.Frame(self.root, padding=15)
        main.pack(fill="both", expand=True)

        left = ttk.Frame(main)
        left.pack(side="left", fill="both", expand=True, padx=(0, 15))

        right = ttk.Frame(main, width=340)
        right.pack(side="right", fill="y")

        self.module_label = ttk.Label(left, text="", font=("Arial", 12))
        self.module_label.pack(anchor="w", pady=5)

        rec_box = ttk.LabelFrame(left, text="Personalización activa", padding=10)
        rec_box.pack(fill="x", pady=8)
        ttk.Label(rec_box, textvariable=self.recommendation_var, font=("Arial", 12, "bold"), wraplength=650).pack(anchor="w")
        ttk.Label(rec_box, textvariable=self.study_hint_var, font=("Arial", 12), wraplength=650).pack(anchor="w", pady=(5, 0))
        self.audio_button = ttk.Button(rec_box, text="🔊 Reproducir audio", command=self.play_current_audio)
        self.audio_button.pack(anchor="w", pady=(8, 0))

        self.question_label = ttk.Label(left, text="", font=("Arial", 20, "bold"), wraplength=650, justify="center")
        self.question_label.pack(pady=25)

        self.options_frame = ttk.Frame(left)
        self.options_frame.pack(pady=10)

        self.option_buttons = []
        for i in range(4):
            btn = ttk.Button(self.options_frame, text="", command=lambda i=i: self.answer(i), width=28)
            btn.grid(row=i//2, column=i%2, padx=12, pady=12, ipady=12)
            self.option_buttons.append(btn)

        ttk.Label(left, textvariable=self.feedback_var, font=("Arial", 14, "bold")).pack(pady=20)

        metrics_box = ttk.LabelFrame(right, text="Métricas en vivo", padding=12)
        metrics_box.pack(fill="x", pady=8)
        ttk.Label(metrics_box, textvariable=self.metrics_var, justify="left", font=("Consolas", 10)).pack(anchor="w")

        log_box = ttk.LabelFrame(right, text="Log del motor", padding=12)
        log_box.pack(fill="both", expand=True, pady=8)
        self.log_text = tk.Text(log_box, height=18, width=42, wrap="word")
        self.log_text.pack(fill="both", expand=True)

    def load_next_exercise(self):
        ex = self.current_exercise

        method_name = METHOD_LABELS.get(ex["method_id"], ex["method_id"])
        recommended = self.last_decision.get("recommended_method")
        recommended_label = METHOD_LABELS.get(recommended, "Aún sin método recomendado")

        self.module_label.config(
            text=f"Usuario #{self.id_user} | Módulo: {self.content.get('topic')} | Habilidad: {ex['skill_id']}"
        )

        self.recommendation_var.set(
            f"Fase: {self.last_decision['phase']} | Método aplicado ahora: {method_name} | Método recomendado: {recommended_label}"
        )
        self.study_hint_var.set("Estrategia de estudio aplicada: Usa el método sugerido.")

        prefix = f"[Método {method_name}] "
        self.question_label.config(text=prefix + ex["question"])

        for i, option in enumerate(ex["options"]):
            self.option_buttons[i].config(text=option, state="normal")

        self.feedback_var.set("")
        audio_path = ex.get("audio_path", "")
        if audio_path:
            self.audio_button.config(state="normal")
        else:
            self.audio_button.config(state="disabled")

        self.start_time = time.time()
        self.update_metrics()
        self.write_log(self.last_logs)

        # En los métodos fonético/auditivo el audio es parte del estímulo.
        if ex.get("method_id") in ("M4_fonetico", "M2_auditivo") and audio_path:
            self.root.after(350, self.play_current_audio)


    def play_current_audio(self):
        if not self.current_exercise:
            return
        audio_path = self.current_exercise.get("audio_path", "")
        ok, msg = self.audio_player.play(audio_path)
        if not ok:
            self.feedback_var.set("⚠️ " + msg)
        else:
            self.feedback_var.set("🔊 " + msg)

    def answer(self, index):
        ex = self.current_exercise
        elapsed_ms = int((time.time() - self.start_time) * 1000)
        selected = ex["options"][index]
        is_correct = selected == ex["correct_answer"]

        # 1. Process response using HestiaBridge (C++ engine)
        skill_id_int = SKILL_STR_TO_INT.get(ex["skill_id"], 0)
        result, latency, logs = self.bridge.process_response_timed(
            self.id_user, skill_id_int, self.current_method_enum, is_correct, elapsed_ms
        )
        
        self.last_logs = logs
        self.last_decision = {
            "phase": "adaptación" if result.current_pL > 0.0 else "exploración",
            "recommended_method": METHOD_ENUM_TO_STR.get(result.next_method, None)
        }

        if is_correct:
            self.feedback_var.set("✅ " + ex.get("feedback_correct", "Correcto."))
        else:
            self.feedback_var.set("🟡 " + ex.get("feedback_incorrect", "Inténtalo de nuevo."))

        for btn in self.option_buttons:
            btn.config(state="disabled")

        self.update_metrics()
        self.write_log(self.last_logs)
        
        # 2. Select next exercise based on C++ recommendation
        next_skill_id_str = SKILL_INT_TO_STR.get(result.next_skill_id, "vocal_a")
        next_method_str = METHOD_ENUM_TO_STR.get(result.next_method, "M1_visual")
        
        matching = [e for e in self.exercises if e["skill_id"] == next_skill_id_str and e["method_id"] == next_method_str]
        if not matching:
            matching = [e for e in self.exercises if e["method_id"] == next_method_str]
        if not matching:
            matching = self.exercises
            
        self.current_exercise = random.choice(matching)
        self.current_method_enum = METHOD_STR_TO_ENUM[self.current_exercise["method_id"]]

        self.root.after(1200, self.load_next_exercise)

    def update_metrics(self):
        skill_id_int = SKILL_STR_TO_INT.get(self.current_exercise["skill_id"], 0)
        states = self.bridge.get_method_states_for_ui(self.id_user, skill_id_int)
        
        text = "Métricas en vivo (C++ Backend):\n"
        for m, s in states.items():
            method_label = METHOD_LABELS_FROM_CPP.get(m, m)
            text += f"- {method_label}: Q={s['q_value']:.2f}, n={s['attempts']}\n"
        
        try:
            hr = self.bridge.get_session_hit_rate()
            text += f"\nHit Rate de la Sesión: {hr*100:.1f}%\n"
        except:
            pass
            
        self.metrics_var.set(text)

    def write_log(self, lines):
        if not lines:
            return
        self.log_text.insert("end", "\n".join(lines) + "\n" + "-"*42 + "\n")
        self.log_text.see("end")

    def show_final(self):
        message = (
            f"Sesión finalizada.\n\n"
            f"Los datos quedaron guardados en hestia.db y procesados por el backend C++."
        )
        messagebox.showinfo("HESTIA", message)
        self.show_start()

if __name__ == "__main__":
    root = tk.Tk()
    app = HestiaDemoApp(root)
    root.mainloop()
