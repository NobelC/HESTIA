"""
HESTIA — Frontend Principal
Diseño: Minimalismo refinado de alta gama
Paleta: Fondos oscuros profundos + acentos ámbar cálidos
"""

import tkinter as tk
from tkinter import font as tkfont
import sys
import os
import time
import threading

# Asegurar que el bridge sea importable
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Pre-importar el enum METHOD para usarlo en ExercisesView sin imports dinámicos
try:
    from bridge.hestia_bridge import METHOD as _HESTIA_METHOD
except Exception:
    _HESTIA_METHOD = None

# ─────────────────────────────────────────────
# SISTEMA DE DISEÑO
# ─────────────────────────────────────────────

COLORS = {
    "bg":           "#0D0F1A",   # Fondo principal — negro azulado profundo
    "surface":      "#141627",   # Superficies elevadas — azul medianoche
    "surface_2":    "#1C1F38",   # Tarjetas y paneles
    "surface_3":    "#242848",   # Hover / estados activos
    "border":       "#2A2E52",   # Bordes sutiles
    "border_light": "#363B68",   # Bordes visibles
    "accent":       "#E8A84A",   # Ámbar cálido — acción principal
    "accent_dim":   "#A87530",   # Ámbar apagado
    "accent_glow":  "#F0C070",   # Ámbar brillante (hover)
    "blue":         "#5B8EF0",   # Azul para información
    "blue_dim":     "#3A6ACE",
    "success":      "#52C97A",   # Verde menta
    "success_dim":  "#2A7A4A",
    "error":        "#E8526A",   # Rojo suave
    "error_dim":    "#8A2A38",
    "text":         "#EEF0F8",   # Blanco cálido
    "text_2":       "#9398B8",   # Texto secundario
    "text_3":       "#5C6080",   # Texto deshabilitado
    "sidebar_bg":   "#0A0C16",   # Sidebar más oscuro
}

RADII = 12  # radio de bordes redondeados


# ─────────────────────────────────────────────
# HELPERS DE DIBUJO
# ─────────────────────────────────────────────

def rounded_rect(canvas, x1, y1, x2, y2, r=RADII, **kwargs):
    """Dibuja un rectángulo redondeado en un Canvas."""
    pts = [
        x1 + r, y1,
        x2 - r, y1,
        x2, y1,
        x2, y1 + r,
        x2, y2 - r,
        x2, y2,
        x2 - r, y2,
        x1 + r, y2,
        x1, y2,
        x1, y2 - r,
        x1, y1 + r,
        x1, y1,
        x1 + r, y1,
    ]
    return canvas.create_polygon(pts, smooth=True, **kwargs)


class RoundedFrame(tk.Canvas):
    """Frame con bordes redondeados usando Canvas."""

    def __init__(self, parent, bg_color=COLORS["surface_2"],
                 border_color=COLORS["border"], radius=RADII,
                 border_width=1, **kwargs):
        w = kwargs.pop("width", 300)
        h = kwargs.pop("height", 100)
        super().__init__(
            parent,
            width=w, height=h,
            bg=COLORS["bg"],
            highlightthickness=0,
            **kwargs,
        )
        self._bg = bg_color
        self._border = border_color
        self._r = radius
        self._bw = border_width
        self._rect = None
        self._border_rect = None
        self.bind("<Configure>", self._redraw)
        self._draw(w, h)

    def _draw(self, w, h):
        self.delete("bg")
        bw = self._bw
        if bw:
            rounded_rect(self, 0, 0, w, h, self._r,
                         fill=self._border, outline="", tags="bg")
            rounded_rect(self, bw, bw, w - bw, h - bw, self._r - bw,
                         fill=self._bg, outline="", tags="bg")
        else:
            rounded_rect(self, 0, 0, w, h, self._r,
                         fill=self._bg, outline="", tags="bg")
        self.tag_lower("bg")

    def _redraw(self, event):
        self._draw(event.width, event.height)


# ─────────────────────────────────────────────
# BARRA LATERAL
# ─────────────────────────────────────────────

class Sidebar(tk.Frame):
    def __init__(self, parent, navigate_callback):
        super().__init__(parent, bg=COLORS["sidebar_bg"], width=220)
        self.pack_propagate(False)
        self._nav = navigate_callback
        self._active = "dashboard"
        self._buttons = {}
        self.demo_mode_var = tk.BooleanVar(value=False)
        self._build()

    def _build(self):
        # Logo / marca
        logo_frame = tk.Frame(self, bg=COLORS["sidebar_bg"])
        logo_frame.pack(fill="x", padx=24, pady=(32, 8))

        tk.Label(
            logo_frame, text="HESTIA",
            font=("Helvetica", 22, "bold"),
            bg=COLORS["sidebar_bg"], fg=COLORS["accent"],
            anchor="w",
        ).pack(fill="x")
        tk.Label(
            logo_frame, text="Motor de Tutoría Adaptativa",
            font=("Helvetica", 9),
            bg=COLORS["sidebar_bg"], fg=COLORS["text_3"],
            anchor="w", wraplength=170,
        ).pack(fill="x")

        # Separador
        tk.Frame(self, bg=COLORS["border"], height=1).pack(
            fill="x", padx=24, pady=(16, 20))

        # Sección Estudiante
        tk.Label(
            self, text="ESTUDIANTE",
            font=("Helvetica", 8, "bold"),
            bg=COLORS["sidebar_bg"], fg=COLORS["text_3"],
            anchor="w",
        ).pack(fill="x", padx=28, pady=(0, 8))

        nav_items = [
            ("dashboard",  "●  Panel Principal"),
            ("exercises",  "◆  Ejercicios"),
            ("progress",   "▲  Progreso"),
        ]

        for key, label in nav_items:
            self._make_nav_btn(key, label)

        # Sección Sistema
        tk.Frame(self, bg=COLORS["border"], height=1).pack(
            fill="x", padx=24, pady=(20, 16))
        tk.Label(
            self, text="SISTEMA",
            font=("Helvetica", 8, "bold"),
            bg=COLORS["sidebar_bg"], fg=COLORS["text_3"],
            anchor="w",
        ).pack(fill="x", padx=28, pady=(0, 8))

        self._make_nav_btn("settings",   "⚙  Configuración")
        self._make_nav_btn("diagnostics", "🔬  Diagnóstico Motor")

        # Footer
        footer = tk.Frame(self, bg=COLORS["sidebar_bg"])
        footer.pack(side="bottom", fill="x", padx=24, pady=20)
        
        # Toggle Demo Técnica
        tk.Checkbutton(footer, text="Modo Demo Técnica", variable=self.demo_mode_var, bg=COLORS["sidebar_bg"], fg=COLORS["accent"], selectcolor=COLORS["sidebar_bg"], activebackground=COLORS["sidebar_bg"], activeforeground=COLORS["accent"], command=lambda: self.event_generate("<<ToggleDemo>>")).pack(pady=5)

        tk.Frame(footer, bg=COLORS["border"], height=1).pack(fill="x", pady=(0, 12))
        tk.Label(
            footer, text="v1.0  ·  JIC 2026",
            font=("Helvetica", 9),
            bg=COLORS["sidebar_bg"], fg=COLORS["text_3"],
        ).pack()

    def _make_nav_btn(self, key, text):
        btn = tk.Label(
            self, text=text,
            font=("Helvetica", 11),
            bg=COLORS["sidebar_bg"], fg=COLORS["text_2"],
            anchor="w", padx=20, pady=9, cursor="hand2",
        )
        btn.pack(fill="x", padx=12, pady=1)
        btn.bind("<Button-1>", lambda e, k=key: self._on_click(k))
        btn.bind("<Enter>",    lambda e, b=btn: self._hover(b, True))
        btn.bind("<Leave>",    lambda e, b=btn, k=key: self._hover(b, False, k))
        self._buttons[key] = btn

    def _hover(self, btn, entering, key=None):
        if key and key == self._active:
            return
        if entering:
            btn.config(bg=COLORS["surface_3"], fg=COLORS["text"])
        else:
            btn.config(bg=COLORS["sidebar_bg"], fg=COLORS["text_2"])

    def _on_click(self, key):
        self.set_active(key)
        self._nav(key)

    def set_active(self, key):
        # Resetear anterior
        if self._active in self._buttons:
            self._buttons[self._active].config(
                bg=COLORS["sidebar_bg"], fg=COLORS["text_2"])
        self._active = key
        if key in self._buttons:
            self._buttons[key].config(
                bg=COLORS["surface_3"], fg=COLORS["accent"])


# ─────────────────────────────────────────────
# COMPONENTES REUTILIZABLES
# ─────────────────────────────────────────────

class StatCard(tk.Frame):
    """Tarjeta de estadística con valor grande y etiqueta."""

    def __init__(self, parent, value, label, accent=COLORS["accent"], **kwargs):
        super().__init__(parent, bg=COLORS["surface_2"],
                         padx=24, pady=20, **kwargs)
        tk.Label(
            self, text=value,
            font=("Helvetica", 32, "bold"),
            bg=COLORS["surface_2"], fg=accent,
        ).pack(anchor="w")
        tk.Label(
            self, text=label,
            font=("Helvetica", 10),
            bg=COLORS["surface_2"], fg=COLORS["text_2"],
        ).pack(anchor="w")


class SectionHeader(tk.Frame):
    def __init__(self, parent, title, subtitle="", **kwargs):
        super().__init__(parent, bg=COLORS["bg"], **kwargs)
        tk.Label(
            self, text=title,
            font=("Helvetica", 26, "bold"),
            bg=COLORS["bg"], fg=COLORS["text"],
            anchor="w",
        ).pack(fill="x")
        if subtitle:
            tk.Label(
                self, text=subtitle,
                font=("Helvetica", 12),
                bg=COLORS["bg"], fg=COLORS["text_2"],
                anchor="w",
            ).pack(fill="x", pady=(4, 0))


class HestiaButton(tk.Label):
    """Botón estilizado con estados hover y presionado."""

    def __init__(self, parent, text, command=None,
                 style="primary", width_px=None, **kwargs):
        styles = {
            "primary":   (COLORS["accent"],   COLORS["bg"],       COLORS["accent_glow"]),
            "secondary": (COLORS["surface_3"], COLORS["text"],     COLORS["border_light"]),
            "danger":    (COLORS["error_dim"], COLORS["error"],    COLORS["error"]),
            "success":   (COLORS["success_dim"], COLORS["success"], COLORS["success"]),
        }
        bg, fg, hover = styles.get(style, styles["primary"])

        super().__init__(
            parent, text=text,
            font=("Helvetica", 12, "bold"),
            bg=bg, fg=fg,
            padx=24, pady=12,
            cursor="hand2",
            relief="flat",
            borderwidth=2,
            **kwargs,
        )
        self._bg = bg
        self._hover_bg = hover if style != "primary" else COLORS["accent_glow"]
        self._fg = fg
        self._hover_fg = COLORS["bg"] if style == "primary" else fg
        self._cmd = command

        self.bind("<Button-1>", self._on_press)
        self.bind("<ButtonRelease-1>", self._on_release)
        self.bind("<Enter>",    self._on_hover)
        self.bind("<Leave>",    self._on_leave)

    def _on_hover(self, e):
        self.config(bg=self._hover_bg, fg=self._hover_fg)

    def _on_leave(self, e):
        self.config(bg=self._bg, fg=self._fg)

    def _on_press(self, e):
        self.config(relief="sunken")

    def _on_release(self, e):
        self.config(relief="flat")
        if self._cmd:
            self._cmd()


class ProgressBar(tk.Canvas):
    """Barra de progreso elegante con animación."""

    def __init__(self, parent, width=300, height=6,
                 color=COLORS["accent"], bg=COLORS["surface_3"], **kwargs):
        super().__init__(parent, width=width, height=height,
                         bg=COLORS["bg"], highlightthickness=0, **kwargs)
        self._width_val = width
        self._height_val = height
        self._color = color
        self._track_color = bg
        self._value = 0
        self._draw()

    def _draw(self):
        self.delete("all")
        r = self._height_val // 2
        # Track
        rounded_rect(self, 0, 0, self._width_val, self._height_val, r,
                     fill=self._track_color, outline="")
        # Fill
        fill_w = max(self._height_val, int(self._width_val * self._value))
        if fill_w > 0:
            rounded_rect(self, 0, 0, fill_w, self._height_val, r,
                         fill=self._color, outline="")

    def set_value(self, v):
        """v entre 0.0 y 1.0"""
        self._value = max(0.0, min(1.0, v))
        self._draw()

    def animate_to(self, target, steps=20, delay=16):
        start = self._value
        def step(i=0):
            if i > steps:
                return
            self._value = start + (target - start) * (i / steps)
            self._draw()
            self.after(delay, lambda: step(i + 1))
        step()


# ─────────────────────────────────────────────
# VISTAS
# ─────────────────────────────────────────────

class DashboardView(tk.Frame):
    def __init__(self, parent, bridge=None, student_id=1):
        super().__init__(parent, bg=COLORS["bg"])
        self._bridge = bridge
        self._sid = student_id
        self._build()

    def _build(self):
        # Cabecera
        header = tk.Frame(self, bg=COLORS["bg"])
        header.pack(fill="x", pady=(0, 32))

        tk.Label(
            header, text="Bienvenido de vuelta",
            font=("Helvetica", 13),
            bg=COLORS["bg"], fg=COLORS["text_2"],
        ).pack(anchor="w")
        tk.Label(
            header, text="Panel Principal",
            font=("Helvetica", 30, "bold"),
            bg=COLORS["bg"], fg=COLORS["text"],
        ).pack(anchor="w")

        # Separador decorativo
        sep = tk.Frame(self, bg=COLORS["accent"], height=2, width=48)
        sep.pack(anchor="w", pady=(0, 28))

        # Tarjetas de estadísticas
        cards_frame = tk.Frame(self, bg=COLORS["bg"])
        cards_frame.pack(fill="x", pady=(0, 28))

        # --- NUEVO: Data Real ---
        mastered_count = 0
        total_time_h = 0.0
        pending_count = 0
        hit_rate = 0.0
        logs = []
        domains = []
        
        if self._bridge:
            try:
                progress = self._bridge.get_student_progress(self._sid)
                mastered_count = sum(1 for p in progress if p.is_mastered)
                if progress:
                    hit_rate = self._bridge.get_session_hit_rate()
                    pending_count = len(self._bridge.get_due_skills())
                
                # Mock domains from progress for demo purposes
                domains = [
                    ("Alfabetización", 0.65, COLORS["accent"]),
                    ("Numeración",     0.40, COLORS["blue"]),
                ]
                
                real_logs = self._bridge.get_session_logs(self._sid, 0)
                for l in list(real_logs)[-3:]: # last 3
                    logs.append(("●", f"Skill {l.skill_id}", f"P(L): {l.p_learn:.2f}", COLORS["blue"]))
            except Exception as e:
                print("Error loading dashboard data:", e)

        if not logs:
            logs = [
                ("●", "Vocal A dominada",         "+P(L) 0.20 → 0.91", COLORS["success"]),
                ("◆", "Número 3 en práctica",      "P(L) actual: 0.54",  COLORS["blue"]),
                ("▲", "Número 2 requiere repaso",  "Inactiva 52h",       COLORS["accent"]),
            ]

        stat_data = [
            (str(mastered_count), "Habilidades dominadas",  COLORS["accent"]),
            (f"{int(hit_rate * 100)}%", "Precisión de hoy", COLORS["success"]),
            (f"{total_time_h:.1f}h",  "Tiempo total de estudio", COLORS["blue"]),
            (str(pending_count), "Habilidades pendientes",  COLORS["text_2"]),
        ]

        for val, lbl, color in stat_data:
            card = StatCard(cards_frame, val, lbl, accent=color)
            card.pack(side="left", padx=(0, 12), expand=True, fill="both")

        # Sección progreso por dominio
        tk.Label(
            self, text="Progreso por dominio",
            font=("Helvetica", 14, "bold"),
            bg=COLORS["bg"], fg=COLORS["text"],
            anchor="w",
        ).pack(fill="x", pady=(0, 14))

        for name, val, color in domains:
            row = tk.Frame(self, bg=COLORS["bg"])
            row.pack(fill="x", pady=6)

            top = tk.Frame(row, bg=COLORS["bg"])
            top.pack(fill="x", pady=(0, 6))
            tk.Label(top, text=name, font=("Helvetica", 11),
                     bg=COLORS["bg"], fg=COLORS["text"]).pack(side="left")
            tk.Label(top, text=f"{int(val * 100)}%",
                     font=("Helvetica", 11, "bold"),
                     bg=COLORS["bg"], fg=color).pack(side="right")

            bar = ProgressBar(row, width=580, height=8, color=color)
            bar.pack(anchor="w")
            bar.after(200, lambda b=bar, v=val: b.animate_to(v))

        # Actividad reciente
        tk.Label(
            self, text="Actividad reciente",
            font=("Helvetica", 14, "bold"),
            bg=COLORS["bg"], fg=COLORS["text"],
            anchor="w",
        ).pack(fill="x", pady=(28, 14))
        for icon, title, detail, color in logs:
            row = tk.Frame(self, bg=COLORS["surface_2"], padx=16, pady=12)
            row.pack(fill="x", pady=3)

            tk.Label(row, text=icon, font=("Helvetica", 10),
                     bg=COLORS["surface_2"], fg=color, width=2).pack(side="left")
            tk.Label(row, text=title, font=("Helvetica", 11, "bold"),
                     bg=COLORS["surface_2"], fg=COLORS["text"]).pack(side="left", padx=(8, 4))
            tk.Label(row, text=f"  {detail}", font=("Helvetica", 10),
                     bg=COLORS["surface_2"], fg=COLORS["text_2"]).pack(side="left")


class ExercisesView(tk.Frame):
    def __init__(self, parent, bridge=None, student_id=1):
        super().__init__(parent, bg=COLORS["bg"])
        self._bridge = bridge
        self._sid = student_id
        self._streak = 0
        self._correct_total = 0
        self._attempts = 0
        self._pL = 0.20
        self._feedback_job = None

        from content_loader import ContentLoader
        self._loader = ContentLoader()
        from audio_player import AudioPlayer
        self._audio = AudioPlayer(os.path.dirname(os.path.abspath(__file__)) + "/../")

        self.exercises = []
        try:
            base_dir = os.path.dirname(os.path.abspath(__file__)) + "/../"
            for mod in ["vocales.json", "numeros.json", "limites.json"]:
                data = self._loader.cargar_modulo(base_dir, mod)
                self.exercises.extend(data.get("exercises", []))
        except Exception as e:
            print("Error cargando ejercicios:", e)

        self._current_ex = None
        self._target_skill = 1 # Map string to int appropriately in load_question
        self._current_zone = "LOW"
        
        if _HESTIA_METHOD:
            self._target_method = _HESTIA_METHOD.VISUAL
        else:
            self._target_method = 0
            
        if self._bridge:
            try:
                state = self._bridge.storage.load_skill_state(self._sid, self._target_skill)
                if state:
                    self._pL = state.pLearn_operative
            except Exception:
                pass

        self._build()

    # ── construcción inicial ──────────────────

    def _build(self):
        # Cabecera
        hdr = tk.Frame(self, bg=COLORS["bg"])
        hdr.pack(fill="x", pady=(0, 24))

        tk.Label(hdr, text="Sesión de práctica",
                 font=("Helvetica", 13), bg=COLORS["bg"],
                 fg=COLORS["text_2"]).pack(anchor="w")
        tk.Label(hdr, text="Ejercicios Adaptativos",
                 font=("Helvetica", 30, "bold"),
                 bg=COLORS["bg"], fg=COLORS["text"]).pack(anchor="w")
        tk.Frame(self, bg=COLORS["accent"], height=2, width=48).pack(
            anchor="w", pady=(0, 24))

        # ── Barra de sesión ─────────────────
        session_bar = tk.Frame(self, bg=COLORS["surface_2"], padx=20, pady=14)
        session_bar.pack(fill="x", pady=(0, 20))

        self._skill_lbl = tk.Label(
            session_bar, text="",
            font=("Helvetica", 11, "bold"),
            bg=COLORS["surface_2"], fg=COLORS["accent"])
        self._skill_lbl.pack(side="left")
        
        self._method_lbl = tk.Label(
            session_bar, text="",
            font=("Helvetica", 10),
            bg=COLORS["surface_2"], fg=COLORS["text_2"])
        self._method_lbl.pack(side="left", padx=20)
        
        self._zone_lbl = tk.Label(
            session_bar, text="LOW",
            font=("Helvetica", 9, "bold"),
            bg=COLORS["surface_3"], fg=COLORS["text"], padx=8, pady=2)
        self._zone_lbl.pack(side="left", padx=10)

        right_info = tk.Frame(session_bar, bg=COLORS["surface_2"])
        right_info.pack(side="right")

        tk.Label(right_info, text="Racha ",
                 font=("Helvetica", 10),
                 bg=COLORS["surface_2"], fg=COLORS["text_2"]).pack(side="left")
        self._streak_lbl = tk.Label(
            right_info, text="0",
            font=("Helvetica", 11, "bold"),
            bg=COLORS["surface_2"], fg=COLORS["text"])
        self._streak_lbl.pack(side="left")

        tk.Label(right_info, text="   P(L) ",
                 font=("Helvetica", 10),
                 bg=COLORS["surface_2"], fg=COLORS["text_2"]).pack(side="left")
        self._pl_lbl = tk.Label(
            right_info, text="0.20",
            font=("Helvetica", 11, "bold"),
            bg=COLORS["surface_2"], fg=COLORS["blue"])
        self._pl_lbl.pack(side="left")

        # ── Tarjeta principal de ejercicio ──
        self._card = tk.Frame(self, bg=COLORS["surface_2"], padx=48, pady=40)
        self._card.pack(fill="both", expand=True)

        # Etiqueta de dominio
        self._domain_lbl = tk.Label(
            self._card, text="",
            font=("Helvetica", 9, "bold"),
            bg=COLORS["surface_2"], fg=COLORS["text_3"])
        self._domain_lbl.pack(anchor="w", pady=(0, 20))

        # Pregunta
        self._question_lbl = tk.Label(
            self._card, text="",
            font=("Helvetica", 16),
            bg=COLORS["surface_2"], fg=COLORS["text_2"],
            wraplength=700, justify="left")
        self._question_lbl.pack(anchor="w")

        # Audio
        self._audio_btn = HestiaButton(
            self._card, text="🔊 Reproducir audio",
            command=self._play_audio, style="secondary")

        # Símbolo grande (letra o número)
        self._symbol_lbl = tk.Label(
            self._card, text="",
            font=("Helvetica", 80, "bold"),
            bg=COLORS["surface_2"], fg=COLORS["text"])
        self._symbol_lbl.pack(pady=20)

        # Feedback (oculto inicialmente)
        self._feedback_lbl = tk.Label(
            self._card, text="",
            font=("Helvetica", 13, "bold"),
            bg=COLORS["surface_2"], fg=COLORS["success"])
        self._feedback_lbl.pack(pady=(0, 12))

        # Opciones
        self._opts_frame = tk.Frame(self._card, bg=COLORS["surface_2"])
        self._opts_frame.pack(pady=8)

        self._opt_btns = []
        for i in range(4):
            btn = HestiaButton(
                self._opts_frame, text="",
                command=None, style="secondary")
            btn.grid(row=0, column=i, padx=8)
            self._opt_btns.append(btn)

        # Siguiente / continuar
        bottom = tk.Frame(self._card, bg=COLORS["surface_2"])
        bottom.pack(fill="x", pady=(24, 0))

        self._next_btn = HestiaButton(
            bottom, text="Siguiente  →",
            command=self._next_question,
            style="primary")
        self._next_btn.pack(side="right")

        # Cargar primer ejercicio
        self._load_question()

    # ── lógica ───────────────────────────────

    def _play_audio(self):
        if self._current_ex and "audio_path" in self._current_ex:
            self._audio.play(self._current_ex["audio_path"])

    def _load_question(self):
        method_int = self._target_method.value if hasattr(self._target_method, "value") else self._target_method
        
        candidates = [e for e in self.exercises if e.get("skill_id") == self._target_skill and e.get("method_id") == method_int]
        if not candidates:
            # Fallback
            candidates = [e for e in self.exercises if e.get("skill_id") == self._target_skill]
            
        if not candidates:
            self._skill_lbl.config(text=f"Habilidad ID: {self._target_skill}")
            self._domain_lbl.config(text="")
            self._question_lbl.config(text="Felicidades, has completado los ejercicios o no hay más disponibles.")
            for btn in self._opt_btns: btn.config(state="disabled", text="")
            self._audio_btn.pack_forget()
            self._symbol_lbl.config(text="🎉")
            self._feedback_lbl.config(text="")
            return

        import random
        self._current_ex = random.choice(candidates)

        m_map = {0: "👁 Visual", 1: "🔊 Auditivo", 2: "✋ Kinestésico", 3: "🗣 Fonético", 4: "🌐 Global"}
        m_text = m_map.get(method_int, str(method_int))
        self._method_lbl.config(text=f"{m_text}")

        self._skill_lbl.config(text=f"Habilidad ID: {self._target_skill}")
        self._domain_lbl.config(text="EJERCICIO")
        self._question_lbl.config(text=self._current_ex.get("question", "¿Cuál es la respuesta?"))
        
        if "audio_path" in self._current_ex:
            self._audio_btn.pack(pady=(15, 0))
        else:
            self._audio_btn.pack_forget()

        sym = self._current_ex.get("correct_answer", "")
        if "audio_text" in self._current_ex or "audio_path" in self._current_ex:
            self._symbol_lbl.config(text="🔊", fg=COLORS["text_2"], font=("Helvetica", 64))
        else:
            self._symbol_lbl.config(text=sym, fg=COLORS["text"], font=("Helvetica", 80, "bold"))

        self._feedback_lbl.config(text="")
        self._next_btn.config(state="disabled")

        options = self._current_ex.get("options", [])
        for i in range(4):
            btn = self._opt_btns[i]
            if i < len(options):
                opt = options[i]
                btn.config(text=opt, bg=COLORS["surface_3"], fg=COLORS["text"], state="normal")
                btn._bg = COLORS["surface_3"]
                btn._fg = COLORS["text"]
                btn._cmd = lambda o=opt: self._check(o)
                btn.bind("<Button-1>",       lambda e, o=opt: self._check(o))
                btn.bind("<ButtonRelease-1>", lambda e, o=opt: None)
            else:
                btn.config(text="", state="disabled")

    def _check(self, chosen):
        if not self._current_ex: return
        correct = (chosen == self._current_ex.get("correct_answer"))
        self._attempts += 1

        if correct:
            self._correct_total += 1
            self._streak += 1
            fb_text  = f"✓  {self._current_ex.get('feedback_correct', '¡Correcto!')}"
            fb_color = COLORS["success"]
            sym_col  = COLORS["success"]
        else:
            self._streak = 0
            fb_text  = f"✗  {self._current_ex.get('feedback_incorrect', 'Incorrecto.')}"
            fb_color = COLORS["error"]
            sym_col  = COLORS["error"]

        # Guardado toast
        toast = tk.Label(self._card, text="Guardado ✓", font=("Helvetica", 9), bg=COLORS["surface_2"], fg=COLORS["text_3"])
        toast.place(relx=0.9, rely=0.1)
        self.after(1500, toast.destroy)

        self._feedback_lbl.config(text=fb_text, fg=fb_color)
        self._symbol_lbl.config(fg=sym_col)

        if self._bridge and _HESTIA_METHOD:
            try:
                # Need to map self._target_skill from int to int, already an int
                result = self._bridge.process_response(
                    self._sid, self._target_skill,
                    self._target_method, correct, 1500.0)
                self._pL = result.current_pL
                self._target_skill = result.next_skill_id
                self._target_method = result.next_method
                self._current_zone = result.next_zone.name if hasattr(result.next_zone, "name") else str(result.next_zone)
                self._zone_lbl.config(text=self._current_zone)
                
                # Event to update diagnostic view
                self.event_generate("<<ResponseProcessed>>")
            except Exception as ex:
                print(ex)
                delta = 0.04 if correct else -0.02
                self._pL = max(0.01, min(0.98, self._pL + delta))
        else:
            delta = 0.04 if correct else -0.02
            self._pL = max(0.01, min(0.98, self._pL + delta))

        self._pl_lbl.config(text=f"{self._pL:.2f}")
        self._streak_lbl.config(text=str(self._streak))

        # Colorear opciones
        for btn in self._opt_btns:
            if btn.cget("text") == self._current_ex.get("correct_answer"):
                btn.config(bg=COLORS["success_dim"], fg=COLORS["success"], state="disabled")
                btn._bg = COLORS["success_dim"]
            elif btn.cget("text") == chosen and not correct:
                btn.config(bg=COLORS["error_dim"], fg=COLORS["error"], state="disabled")
                btn._bg = COLORS["error_dim"]
            else:
                btn.config(state="disabled")

        self._next_btn.config(state="normal")

    def _next_question(self):
        self._load_question()


class ProgressView(tk.Frame):
    def __init__(self, parent, bridge=None, student_id=1):
        super().__init__(parent, bg=COLORS["bg"])
        self._bridge = bridge
        self._sid = student_id
        self._build()

    def _build(self):
        tk.Label(self, text="Progreso del estudiante",
                 font=("Helvetica", 13), bg=COLORS["bg"],
                 fg=COLORS["text_2"]).pack(anchor="w")
        tk.Label(self, text="Progreso",
                 font=("Helvetica", 30, "bold"),
                 bg=COLORS["bg"], fg=COLORS["text"]).pack(anchor="w")
        tk.Frame(self, bg=COLORS["accent"], height=2, width=48).pack(
            anchor="w", pady=(0, 28))

        # Skills
        skills = []
        if self._bridge:
            try:
                progress = self._bridge.get_student_progress(self._sid)
                for p in progress:
                    status = "Dominada" if p.is_mastered else ("En progreso" if p.pL_current > 0.2 else "Iniciando")
                    color = COLORS["success"] if p.is_mastered else (COLORS["accent"] if p.pL_current > 0.2 else COLORS["blue"])
                    skills.append((f"Skill {p.skill_id}", p.pL_current, status, color))
            except Exception as e:
                print("Error loading progress:", e)

        if not skills:
            skills = [
                ("Vocal A",   0.91, "Dominada",      COLORS["success"]),
                ("Vocal E",   0.68, "En progreso",    COLORS["accent"]),
                ("Vocal I",   0.30, "Iniciando",      COLORS["blue"]),
                ("Número 1",  0.85, "Dominada",       COLORS["success"]),
                ("Número 2",  0.54, "En progreso",    COLORS["accent"]),
                ("Número 3",  0.40, "En progreso",    COLORS["accent"]),
                ("Número 4",  0.12, "Bloqueada",      COLORS["text_3"]),
            ]

        for name, val, status, color in skills:
            row = tk.Frame(self, bg=COLORS["surface_2"], padx=20, pady=14)
            row.pack(fill="x", pady=3)

            left = tk.Frame(row, bg=COLORS["surface_2"])
            left.pack(side="left", fill="x", expand=True)

            info = tk.Frame(left, bg=COLORS["surface_2"])
            info.pack(fill="x", pady=(0, 8))

            tk.Label(info, text=name,
                     font=("Helvetica", 12, "bold"),
                     bg=COLORS["surface_2"], fg=COLORS["text"]).pack(side="left")
            tk.Label(info, text=f"  {status}",
                     font=("Helvetica", 10),
                     bg=COLORS["surface_2"], fg=color).pack(side="left")
            tk.Label(info, text=f"{int(val * 100)}%",
                     font=("Helvetica", 11, "bold"),
                     bg=COLORS["surface_2"], fg=color).pack(side="right")

            bar = ProgressBar(left, width=500, height=6, color=color)
            bar.pack(anchor="w")
            bar.after(300 + skills.index((name, val, status, color)) * 80,
                      lambda b=bar, v=val: b.animate_to(v))


class SettingsView(tk.Frame):
    def __init__(self, parent, bridge=None, student_id=1):
        super().__init__(parent, bg=COLORS["bg"])
        self._bridge = bridge
        self._sid = student_id
        self._build()

    def _build(self):
        tk.Label(self, text="Sistema adaptativo",
                 font=("Helvetica", 13), bg=COLORS["bg"],
                 fg=COLORS["text_2"]).pack(anchor="w")
        tk.Label(self, text="Configuración",
                 font=("Helvetica", 30, "bold"),
                 bg=COLORS["bg"], fg=COLORS["text"]).pack(anchor="w")
        tk.Frame(self, bg=COLORS["accent"], height=2, width=48).pack(
            anchor="w", pady=(0, 28))

        sections = []
        if self._bridge:
            try:
                c = self._bridge.get_bkt_constants()
                sections = [
                    ("Motor BKT", [
                        ("P(Transición) por defecto", str(c["DEFAULT_P_TRANSITION"])),
                        ("Umbral de olvido (horas)",  str(c["FORGET_THRESHOLD_HOURS"])),
                        ("P(Learn) por defecto",      str(c["DEFAULT_P_LEARN"])),
                        ("P(Slip) por defecto",       str(c["DEFAULT_P_SLIP"])),
                    ]),
                    ("Motor MAB / UCB", [
                        ("Constante de exploración C", "1.0"),
                        ("Métodos disponibles",         "5 activos"),
                    ]),
                    ("Sistema SRS", [
                        ("Intervalos de repaso",  "1 · 3 · 7 · 14 · 30 días"),
                        ("Retención de logs",     "6 meses"),
                    ]),
                ]
            except Exception as e:
                print("Error loading settings:", e)
        if not sections:
            sections = [
                ("Motor BKT", [
                    ("P(Transición) por defecto", "0.10"),
                    ("Umbral de olvido (horas)",  "48"),
                    ("Umbral anti-stall",          "3 intentos"),
                ]),
                ("Motor MAB / UCB", [
                    ("Constante de exploración C", "1.0"),
                    ("Métodos disponibles",         "5 activos"),
                ]),
                ("Sistema SRS", [
                    ("Intervalos de repaso",  "1 · 3 · 7 · 14 · 30 días"),
                    ("Retención de logs",     "6 meses"),
                ]),
            ]

        for sec_name, params in sections:
            tk.Label(self, text=sec_name,
                     font=("Helvetica", 13, "bold"),
                     bg=COLORS["bg"], fg=COLORS["text"],
                     anchor="w").pack(fill="x", pady=(16, 8))

            for param, val in params:
                row = tk.Frame(self, bg=COLORS["surface_2"],
                               padx=20, pady=14)
                row.pack(fill="x", pady=2)
                tk.Label(row, text=param,
                         font=("Helvetica", 11),
                         bg=COLORS["surface_2"],
                         fg=COLORS["text_2"]).pack(side="left")
                tk.Label(row, text=val,
                         font=("Helvetica", 11, "bold"),
                         bg=COLORS["surface_2"],
                         fg=COLORS["text"]).pack(side="right")

        # Botón de acción
        tk.Frame(self, bg=COLORS["bg"], height=8).pack()
        HestiaButton(self, text="Restablecer base de datos",
                     style="danger",
                     command=lambda: None).pack(anchor="w")


class MotorDiagnosticsView(tk.Frame):
    """Panel técnico de diagnóstico del motor — para demostración ante el jurado."""

    MASTERY_THRESHOLD = 0.90
    CEIL_THRESHOLD    = 0.98
    MAX_HISTORY       = 50
    METHOD_NAMES      = ["VISUAL", "AUDITORY", "KINESTHETIC", "PHONETIC", "GLOBAL"]

    def __init__(self, parent, bridge=None, student_id=1):
        super().__init__(parent, bg=COLORS["sidebar_bg"], width=360)
        self.pack_propagate(False)
        self._bridge = bridge
        self._sid = student_id
        self._sim_job = None

        # Live state
        self.pl_op   = 0.20
        self.pl_th   = 0.20
        self.gap     = 0.0
        self.mastered = False
        self.streak  = 0
        self.avg_rt  = 0.0
        self.bkt = {"pT": 0.10, "pG": 0.25, "pS": 0.10, "pF": 0.50,
                    "pT_prev": 0.10, "pG_prev": 0.25}
        self.method_q = {m: (None, 0) for m in self.METHOD_NAMES}
        self.history = []

        self._build()
        self.update_data()

    # ── Construction ─────────────────────────

    def _build(self):
        C = COLORS
        sbg = C["sidebar_bg"]

        # Title bar
        title_bar = tk.Frame(self, bg=sbg)
        title_bar.pack(fill="x", padx=16, pady=(18, 4))
        tk.Label(title_bar, text="🔬", font=("Helvetica", 14),
                 bg=sbg, fg=C["accent"]).pack(side="left")
        tk.Label(title_bar, text=" Diagnóstico Motor",
                 font=("Helvetica", 13, "bold"),
                 bg=sbg, fg=C["accent"]).pack(side="left")
        tk.Frame(self, bg=C["accent"], height=1).pack(fill="x", padx=16, pady=(0, 10))

        self._build_section_a()
        tk.Frame(self, bg=C["border"], height=1).pack(fill="x", padx=16, pady=8)
        self._build_section_b()
        tk.Frame(self, bg=C["border"], height=1).pack(fill="x", padx=16, pady=8)
        self._build_section_c()
        tk.Frame(self, bg=C["border"], height=1).pack(fill="x", padx=16, pady=8)
        self._build_section_d()
        tk.Frame(self, bg=C["border"], height=1).pack(fill="x", padx=16, pady=8)
        self._build_section_e()

    def _build_section_a(self):
        C = COLORS
        sbg = C["sidebar_bg"]
        tk.Label(self, text="MÉTRICAS DUALES",
                 font=("Helvetica", 8, "bold"), bg=sbg, fg=C["text_3"],
                 anchor="w").pack(fill="x", padx=16)

        grid = tk.Frame(self, bg=sbg)
        grid.pack(fill="x", padx=12, pady=(4, 0))

        def metric_card(parent, row, col, label_text, var_name):
            f = tk.Frame(parent, bg=C["surface_2"], padx=8, pady=6)
            f.grid(row=row, column=col, padx=3, pady=3, sticky="nsew")
            parent.columnconfigure(col, weight=1)
            lbl_val = tk.Label(f, text="—", font=("Helvetica", 18, "bold"),
                               bg=C["surface_2"], fg=C["text"])
            lbl_val.pack()
            tk.Label(f, text=label_text, font=("Helvetica", 7),
                     bg=C["surface_2"], fg=C["text_3"]).pack()
            setattr(self, var_name, lbl_val)

        metric_card(grid, 0, 0, "P(L) Operativo", "_lbl_pl_op")
        metric_card(grid, 0, 1, "P(L) Teórico",   "_lbl_pl_th")
        metric_card(grid, 1, 0, "Brecha",           "_lbl_gap")
        metric_card(grid, 1, 1, "Dominado",         "_lbl_mast")

    def _build_section_b(self):
        C = COLORS
        sbg = C["sidebar_bg"]
        tk.Label(self, text="PARÁMETROS BKT",
                 font=("Helvetica", 8, "bold"), bg=sbg, fg=C["text_3"],
                 anchor="w").pack(fill="x", padx=16)

        f = tk.Frame(self, bg=C["surface"], padx=12, pady=8)
        f.pack(fill="x", padx=12, pady=(4, 0))

        self._bkt_lbls = {}
        params = [
            ("pT",  "P(Transición)"),
            ("pG",  "P(Guess)    "),
            ("pS",  "P(Slip)     "),
            ("pF",  "P(Forget)   "),
            ("rt",  "T.resp prom "),
            ("str", "Racha actual"),
        ]
        for key, label in params:
            row = tk.Frame(f, bg=C["surface"])
            row.pack(fill="x", pady=1)
            tk.Label(row, text=label, font=("Courier", 9),
                     bg=C["surface"], fg=C["text_3"], width=14,
                     anchor="w").pack(side="left")
            lbl = tk.Label(row, text="——", font=("Courier", 9, "bold"),
                           bg=C["surface"], fg=C["text"], anchor="w")
            lbl.pack(side="left")
            self._bkt_lbls[key] = lbl

    def _build_section_c(self):
        C = COLORS
        sbg = C["sidebar_bg"]
        tk.Label(self, text="SELECCIÓN DE MÉTODO (UCB)",
                 font=("Helvetica", 8, "bold"), bg=sbg, fg=C["text_3"],
                 anchor="w").pack(fill="x", padx=16)

        self._method_canvas = tk.Canvas(self, bg=sbg, highlightthickness=0,
                                        height=120)
        self._method_canvas.pack(fill="x", padx=12, pady=(4, 0))
        self._draw_method_bars()

    def _build_section_d(self):
        C = COLORS
        sbg = C["sidebar_bg"]
        tk.Label(self, text="SIMULACIÓN ACELERADA",
                 font=("Helvetica", 8, "bold"), bg=sbg, fg=C["text_3"],
                 anchor="w").pack(fill="x", padx=16)

        btns = tk.Frame(self, bg=sbg)
        btns.pack(fill="x", padx=12, pady=(4, 0))

        sim_style = dict(font=("Helvetica", 9, "bold"),
                         bg=C["surface_3"], fg=C["text"],
                         activebackground=C["border_light"],
                         relief="flat", padx=6, pady=4, cursor="hand2")
        tk.Button(btns, text="▶ Random",
                  command=lambda: self._start_sim("random"),
                  **sim_style).pack(side="left", padx=(0, 3))
        tk.Button(btns, text="▶ Perfecto",
                  command=lambda: self._start_sim("perfect"),
                  **sim_style).pack(side="left", padx=3)
        tk.Button(btns, text="▶ Oscilante",
                  command=lambda: self._start_sim("oscil"),
                  **sim_style).pack(side="left", padx=3)
        tk.Button(btns, text="■ Stop",
                  command=self._stop_sim,
                  font=("Helvetica", 9, "bold"),
                  bg=C["error_dim"], fg=C["error"],
                  activebackground=C["error_dim"],
                  relief="flat", padx=6, pady=4,
                  cursor="hand2").pack(side="left", padx=3)

    def _build_section_e(self):
        C = COLORS
        sbg = C["sidebar_bg"]
        tk.Label(self, text="CURVA P(L) EN VIVO",
                 font=("Helvetica", 8, "bold"), bg=sbg, fg=C["text_3"],
                 anchor="w").pack(fill="x", padx=16)

        self._graph = tk.Canvas(self, height=130, bg=C["surface"],
                                highlightthickness=0)
        self._graph.pack(fill="x", padx=12, pady=(4, 12))

        leg = tk.Frame(self, bg=sbg)
        leg.pack(padx=16, pady=(0, 12), anchor="w")
        for color, label in [
            (C["blue"],    "— P(L) Op."),
            (C["error"],   "⋯ P(L) Teo."),
            (C["success"], "--- 0.90"),
            ("#666",       "--- 0.98"),
        ]:
            tk.Label(leg, text=label, font=("Helvetica", 7),
                     bg=sbg, fg=color).pack(side="left", padx=3)

        self._draw_graph()

    # ── Drawing helpers ──────────────────────

    def _draw_method_bars(self):
        mc = self._method_canvas
        mc.delete("all")
        W = 336
        ROW_H = 22
        mc.config(height=ROW_H * len(self.METHOD_NAMES) + 4)
        BAR_W = 130

        qs = [self.method_q[m][0] for m in self.METHOD_NAMES
              if self.method_q[m][0] is not None]
        max_q = max(qs) if qs else 1.0
        selected_method = max(
            self.METHOD_NAMES,
            key=lambda m: self.method_q[m][0] if self.method_q[m][0] is not None else -1
        )

        for i, mname in enumerate(self.METHOD_NAMES):
            q_val, n_att = self.method_q[mname]
            y = i * ROW_H + 4
            is_sel = (mname == selected_method and q_val is not None)

            mc.create_text(2, y + ROW_H // 2,
                           text=mname[:8], anchor="w",
                           font=("Courier", 8),
                           fill=COLORS["accent"] if is_sel else COLORS["text_3"])

            mc.create_rectangle(72, y + 4, 72 + BAR_W, y + ROW_H - 4,
                                 fill=COLORS["surface_3"], outline="")

            if q_val is None:
                mc.create_text(72 + BAR_W // 2, y + ROW_H // 2,
                               text="sin probar", font=("Courier", 7),
                               fill=COLORS["text_3"])
            else:
                fill_w = int(BAR_W * (q_val / max_q))
                fill_c = COLORS["accent"] if is_sel else COLORS["blue_dim"]
                mc.create_rectangle(72, y + 4, 72 + fill_w, y + ROW_H - 4,
                                     fill=fill_c, outline="")
                mc.create_text(72 + BAR_W + 4, y + ROW_H // 2,
                               text=f"Q={q_val:.2f}  n={n_att}",
                               anchor="w", font=("Courier", 7),
                               fill=COLORS["text_2"])
            if is_sel:
                mc.create_text(W - 2, y + ROW_H // 2,
                               text="◀", anchor="e",
                               font=("Helvetica", 9),
                               fill=COLORS["accent"])

    def _draw_graph(self):
        g = self._graph
        g.delete("all")
        W = g.winfo_width() or 330
        H = 130
        PAD = 6
        inner_h = H - PAD * 2

        def y_px(val):
            return PAD + inner_h - int(inner_h * max(0.0, min(1.0, val)))

        g.create_line(0, y_px(0.90), W, y_px(0.90),
                      fill=COLORS["success"], dash=(6, 3))
        g.create_line(0, y_px(0.98), W, y_px(0.98),
                      fill="#555", dash=(4, 2))

        if len(self.history) < 2:
            return

        dx = (W - PAD * 2) / max(1, len(self.history) - 1)
        pts_op, pts_th = [], []
        for i, (op, th) in enumerate(self.history):
            x = PAD + i * dx
            pts_op.extend([x, y_px(op)])
            pts_th.extend([x, y_px(th)])

        if len(pts_op) >= 4:
            g.create_line(pts_op, fill=COLORS["blue"], width=2, smooth=True)
        if len(pts_th) >= 4:
            g.create_line(pts_th, fill=COLORS["error"], width=1,
                          dash=(3, 2), smooth=True)

        op_x = PAD + (len(self.history) - 1) * dx
        g.create_oval(op_x - 4, y_px(self.pl_op) - 4,
                      op_x + 4, y_px(self.pl_op) + 4,
                      fill=COLORS["blue"], outline="")
        g.create_oval(op_x - 3, y_px(self.pl_th) - 3,
                      op_x + 3, y_px(self.pl_th) + 3,
                      fill=COLORS["error"], outline="")

    # ── Data refresh ─────────────────────────

    def update_data(self, skill_id=1):
        """Pull live state from bridge and refresh all widgets."""
        if self._bridge:
            try:
                state = self._bridge.storage.load_skill_state(self._sid, skill_id)
                if state:
                    old_pT = self.bkt["pT"]
                    old_pG = self.bkt["pG"]
                    self.pl_op   = state.pLearn_operative
                    self.pl_th   = state.pLearn_theorical
                    self.gap     = self.pl_op - self.pl_th
                    self.mastered = self.pl_th >= self.MASTERY_THRESHOLD
                    self.streak  = state.consecutive_correct
                    self.avg_rt  = state.avg_response_time_ms
                    self.bkt.update({
                        "pT": state.pTransition,
                        "pG": state.pGuess,
                        "pS": state.pSlip,
                        "pF": state.pForget,
                        "pT_prev": old_pT,
                        "pG_prev": old_pG,
                    })
                    try:
                        method_states = self._bridge.storage.load_method_states(
                            self._sid, skill_id)
                        m_names = ["VISUAL", "AUDITORY", "KINESTHETIC", "PHONETIC", "GLOBAL"]
                        for i, m in enumerate(m_names):
                            ms = method_states[i]
                            if ms.n_attempts > 0:
                                self.method_q[m] = (ms.q_value, ms.n_attempts)
                            else:
                                self.method_q[m] = (None, 0)
                    except Exception:
                        pass
            except Exception as e:
                print(f"[Diag] {e}")

        self.history.append((self.pl_op, self.pl_th))
        if len(self.history) > self.MAX_HISTORY:
            self.history.pop(0)

        self._refresh_widgets()

    def _refresh_widgets(self):
        C = COLORS
        gap_col  = C["accent"] if self.gap > 0.1 else C["text"]
        mast_col = C["success"] if self.mastered else C["text_2"]

        self._lbl_pl_op.config(text=f"{self.pl_op:.3f}", fg=C["blue"])
        self._lbl_pl_th.config(text=f"{self.pl_th:.3f}", fg=C["error"])
        self._lbl_gap.config(text=f"{self.gap:+.3f}", fg=gap_col)
        self._lbl_mast.config(text="SI ✓" if self.mastered else "NO",
                              fg=mast_col)

        def arrow(new, old):
            if new > old + 0.001: return "↑"
            if new < old - 0.001: return "↓"
            return "→"

        pT_prev = self.bkt.get("pT_prev", self.bkt["pT"])
        pG_prev = self.bkt.get("pG_prev", self.bkt["pG"])

        self._bkt_lbls["pT"].config(
            text=f"{pT_prev:.2f} → {self.bkt['pT']:.2f}  {arrow(self.bkt['pT'], pT_prev)}")
        self._bkt_lbls["pG"].config(
            text=f"{pG_prev:.2f} → {self.bkt['pG']:.2f}  {arrow(self.bkt['pG'], pG_prev)}")
        self._bkt_lbls["pS"].config(text=f"{self.bkt['pS']:.2f}")
        self._bkt_lbls["pF"].config(text=f"{self.bkt['pF']:.2f}")
        self._bkt_lbls["rt"].config(text=f"{self.avg_rt:.0f}ms")
        streak_col = C["success"] if self.streak >= 3 else C["text"]
        self._bkt_lbls["str"].config(
            text=f"{self.streak} correctas", fg=streak_col)

        self._draw_method_bars()
        self._draw_graph()

    # ── Simulation engine ────────────────────

    def _start_sim(self, mode):
        self._stop_sim()
        self._sim_iter = 0
        self._sim_mode = mode
        self._run_sim_step()

    def _stop_sim(self):
        if self._sim_job:
            self.after_cancel(self._sim_job)
            self._sim_job = None

    def _run_sim_step(self):
        import random
        if self._sim_iter >= 50:
            return

        mode = self._sim_mode
        if mode == "random":
            correct = random.random() > 0.5
        elif mode == "perfect":
            correct = True
        else:  # oscil
            correct = (self._sim_iter % 4) < 3

        pL  = self.pl_op
        pT  = self.bkt["pT"]
        pG  = self.bkt["pG"]
        pS  = self.bkt["pS"]
        pF  = self.bkt["pF"]

        if correct:
            pL_post = (pL * (1 - pS)) / (pL * (1 - pS) + (1 - pL) * pG)
        else:
            pL_post = (pL * pS) / (pL * pS + (1 - pL) * (1 - pG))

        new_pL = pL_post + (1 - pL_post) * pT - pL_post * pF * 0.01
        new_pL = max(0.01, min(0.98, new_pL))
        new_th = min(0.98, self.pl_th + pT * 0.7) if correct else max(0.01, self.pl_th - 0.005)

        self.pl_op  = new_pL
        self.pl_th  = new_th
        self.gap    = self.pl_op - self.pl_th
        self.mastered = self.pl_th >= self.MASTERY_THRESHOLD
        self.streak = (self.streak + 1) if correct else 0

        self.history.append((self.pl_op, self.pl_th))
        if len(self.history) > self.MAX_HISTORY:
            self.history.pop(0)

        self._refresh_widgets()
        self._sim_iter += 1
        self._sim_job = self.after(80, self._run_sim_step)


class HestiaApp:
    VIEWS = {
        "dashboard":   DashboardView,
        "exercises":   ExercisesView,
        "progress":    ProgressView,
        "settings":    SettingsView,
        "diagnostics": MotorDiagnosticsView,
    }


    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("HESTIA — Sistema de Tutoría Inteligente")
        self.root.geometry("1100x700")
        self.root.minsize(900, 600)
        self.root.configure(bg=COLORS["bg"])

        self._bridge = None
        self._student_id = 1
        self._init_bridge()

        self._build_layout()
        self._navigate("dashboard")

    # ── Bridge ────────────────────────────────

    def _init_bridge(self):
        try:
            from bridge.hestia_bridge import get_bridge
            self._bridge = get_bridge()
        except Exception:
            self._bridge = None

    # ── Layout ────────────────────────────────

    def _build_layout(self):
        # Contenedor raíz
        self._root_frame = tk.Frame(self.root, bg=COLORS["bg"])
        self._root_frame.pack(fill="both", expand=True)

        # Línea divisora vertical entre sidebar y contenido
        self._sidebar = Sidebar(self._root_frame, self._navigate)
        self._sidebar.pack(side="left", fill="y")

        tk.Frame(self._root_frame, bg=COLORS["border"],
                 width=1).pack(side="left", fill="y")

        # Área de contenido principal
        self._content_wrapper = tk.Frame(
            self._root_frame, bg=COLORS["bg"])
        self._content_wrapper.pack(
            side="left", fill="both", expand=True)
            
        self._diag_view = MotorDiagnosticsView(self._root_frame, bridge=self._bridge, student_id=self._student_id)
        # Not packed initially
        
        self.root.bind("<<ToggleDemo>>", self._on_toggle_demo)
        self.root.bind("<<ResponseProcessed>>", lambda e: self._diag_view.update_data())

        # Scrollable container
        self._canvas = tk.Canvas(
            self._content_wrapper,
            bg=COLORS["bg"],
            highlightthickness=0)
        self._canvas.pack(side="left", fill="both", expand=True)

        self._scrollbar = tk.Scrollbar(
            self._content_wrapper,
            orient="vertical",
            command=self._canvas.yview)
        self._scrollbar.pack(side="right", fill="y")

        self._canvas.configure(yscrollcommand=self._scrollbar.set)
        self._canvas.bind("<Configure>", self._on_canvas_resize)
        self._canvas.bind_all("<MouseWheel>", self._on_mousewheel)

        self._content_frame = tk.Frame(self._canvas, bg=COLORS["bg"])
        self._canvas_window = self._canvas.create_window(
            (0, 0), window=self._content_frame, anchor="nw")

        self._content_frame.bind("<Configure>", self._on_frame_resize)

    def _on_canvas_resize(self, event):
        self._canvas.itemconfig(
            self._canvas_window, width=event.width)

    def _on_frame_resize(self, event):
        self._canvas.configure(
            scrollregion=self._canvas.bbox("all"))

    def _on_mousewheel(self, event):
        self._canvas.yview_scroll(
            int(-1 * (event.delta / 120)), "units")

    def _on_toggle_demo(self, event):
        if self._sidebar.demo_mode_var.get():
            self._diag_view.pack(side="right", fill="y")
        else:
            self._diag_view.pack_forget()

    # ── Navegación ────────────────────────────

    def _navigate(self, key):
        self._sidebar.set_active(key)

        # Limpiar contenido actual
        for w in self._content_frame.winfo_children():
            w.destroy()

        # Instanciar nueva vista
        view_cls = self.VIEWS.get(key, DashboardView)
        view = view_cls(
            self._content_frame,
            bridge=self._bridge,
            student_id=self._student_id)
        view.pack(fill="both", expand=True, padx=48, pady=40)

        # Resetear scroll al tope
        self._canvas.yview_moveto(0)


# ─────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────

if __name__ == "__main__":
    # DPI awareness en Windows (Debe llamarse antes de crear la ventana)
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass

    root = tk.Tk()

    # Icono y configuración de ventana
    try:
        root.iconbitmap("")
    except Exception:
        pass

    app = HestiaApp(root)
    root.mainloop()