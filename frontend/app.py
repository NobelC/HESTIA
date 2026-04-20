import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os
# Asegurar que el bridge sea importable
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bridge.hestia_bridge import get_bridge, METHOD

class HestiaApp:
    def __init__(self, root):
        self.root = root
        self.root.title("HESTIA — Sistema de Tutoría Inteligente")
        self.root.geometry("900x600")
        self.root.configure(bg="#1e1e2e")
        
        # Inicializar Bridge
        self.bridge = get_bridge()
        self.student_id = 1
        self.current_skill_id = 0 # 'Vocal A' según skill_graph.json

        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure("TFrame", background="#1e1e2e")
        self.style.configure("TLabel", background="#1e1e2e", foreground="#cdd6f4", font=("Inter", 11))
        self.style.configure("Header.TLabel", font=("Inter", 18, "bold"), foreground="#89b4fa")
        self.style.configure("TButton", font=("Inter", 10, "bold"), padding=10)

        self.setup_ui()

    def setup_ui(self):
        # Sidebar
        sidebar = tk.Frame(self.root, bg="#181825", width=200)
        sidebar.pack(side="left", fill="y")

        tk.Label(sidebar, text="HESTIA", font=("Inter", 16, "bold"), bg="#181825", fg="#89b4fa", pady=20).pack()
        
        btn_style = {"bg": "#181825", "fg": "#cdd6f4", "activebackground": "#313244", "relief": "flat", "padx": 20, "pady": 10, "anchor": "w"}
        tk.Button(sidebar, text="Dashboard", **btn_style, command=self.show_dashboard).pack(fill="x")
        tk.Button(sidebar, text="Ejercicios", **btn_style, command=self.show_exercises).pack(fill="x")
        tk.Button(sidebar, text="Progreso", **btn_style, command=self.show_progress).pack(fill="x")
        tk.Button(sidebar, text="Configuración", **btn_style, command=self.show_settings).pack(fill="x")

        # Main Content
        self.main_container = tk.Frame(self.root, bg="#1e1e2e")
        self.main_container.pack(side="right", expand=True, fill="both", padx=40, pady=40)

        self.show_dashboard()

    def clear_main(self):
        for widget in self.main_container.winfo_children():
            widget.destroy()

    def show_dashboard(self):
        self.clear_main()
        ttk.Label(self.main_container, text="Panel de Control", style="Header.TLabel").pack(anchor="w")
        ttk.Label(self.main_container, text="Bienvenido al motor HESTIA. Seleccione una habilidad para comenzar.").pack(anchor="w", pady=(10, 30))
        
        # Stats summary (Mock)
        stats_frame = tk.Frame(self.main_container, bg="#1e1e2e")
        stats_frame.pack(fill="x", pady=20)
        
        self.create_stat_card(stats_frame, "Habilidades Dominadas", "12")
        self.create_stat_card(stats_frame, "Tiempo de Estudio", "4.5h")
        self.create_stat_card(stats_frame, "Precisión Media", "88%")

    def create_stat_card(self, parent, label, value):
        card = tk.Frame(parent, bg="#313244", padx=20, pady=20, highlightthickness=1, highlightbackground="#45475a")
        card.pack(side="left", padx=10, expand=True, fill="both")
        tk.Label(card, text=value, font=("Inter", 24, "bold"), bg="#313244", fg="#f5e0dc").pack()
        tk.Label(card, text=label, font=("Inter", 10), bg="#313244", fg="#9399b2").pack()

    def show_exercises(self):
        self.clear_main()
        ttk.Label(self.main_container, text="Sesión de Práctica", style="Header.TLabel").pack(anchor="w")
        
        exercise_card = tk.Frame(self.main_container, bg="#313244", padx=40, pady=40)
        exercise_card.pack(fill="both", expand=True, pady=20)
        
        tk.Label(exercise_card, text="¿Cuál es el resultado de 5 + 3?", font=("Inter", 20), bg="#313244", fg="white").pack(pady=40)
        
        options_frame = tk.Frame(exercise_card, bg="#313244")
        options_frame.pack()
        
        for opt in ["7", "8", "9", "10"]:
            tk.Button(options_frame, text=opt, width=10, bg="#45475a", fg="white", font=("Inter", 12, "bold"), 
                      command=lambda o=opt: self.check_answer(o)).pack(side="left", padx=10)

    def check_answer(self, opt):
        is_correct = (opt == "8")
        
        # Procesar con el motor real vía Bridge
        result = self.bridge.process_response(
            self.student_id, 
            self.current_skill_id, 
            METHOD.VISUAL, 
            is_correct, 
            1500.0 # Tiempo mock
        )

        if is_correct:
            messagebox.showinfo("¡Correcto!", 
                f"¡Muy bien! P(L) actualizado a {result.current_pL:.2f}")
        else:
            messagebox.showerror("Oops", 
                f"Casi. El motor HESTIA ajustará la dificultad. P(L): {result.current_pL:.2f}")

    def show_progress(self):
        self.clear_main()
        ttk.Label(self.main_container, text="Progreso del Estudiante", style="Header.TLabel").pack(anchor="w")
        ttk.Label(self.main_container, text="Gráficos de dominio y curvas de aprendizaje (BKT)").pack(anchor="w", pady=10)

    def show_settings(self):
        self.clear_main()
        ttk.Label(self.main_container, text="Configuración del Motor", style="Header.TLabel").pack(anchor="w")
        
if __name__ == "__main__":
    root = tk.Tk()
    app = HestiaApp(root)
    root.mainloop()
