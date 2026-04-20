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

        self._make_nav_btn("settings", "⚙  Configuración")

        # Footer
        footer = tk.Frame(self, bg=COLORS["sidebar_bg"])
        footer.pack(side="bottom", fill="x", padx=24, pady=20)
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

        stat_data = [
            ("12",    "Habilidades dominadas",  COLORS["accent"]),
            ("87%",   "Precisión de hoy",        COLORS["success"]),
            ("4.5h",  "Tiempo total de estudio", COLORS["blue"]),
            ("3",     "Habilidades pendientes",  COLORS["text_2"]),
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

        domains = [
            ("Alfabetización", 0.65, COLORS["accent"]),
            ("Numeración",     0.40, COLORS["blue"]),
        ]

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

        logs = [
            ("●", "Vocal A dominada",         "+P(L) 0.20 → 0.91", COLORS["success"]),
            ("◆", "Número 3 en práctica",      "P(L) actual: 0.54",  COLORS["blue"]),
            ("▲", "Número 2 requiere repaso",  "Inactiva 52h",       COLORS["accent"]),
        ]
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
    QUESTIONS = [
        {
            "id": 0,
            "skill": "Vocal A",
            "domain": "Alfabetización",
            "question": "¿Cuál es esta letra?",
            "symbol": "A",
            "options": ["A", "E", "O", "I"],
            "answer": "A",
        },
        {
            "id": 7,
            "skill": "Número 3",
            "domain": "Numeración",
            "question": "¿Cuántos elementos hay?",
            "symbol": "★ ★ ★",
            "options": ["2", "3", "4", "5"],
            "answer": "3",
        },
        {
            "id": 1,
            "skill": "Vocal E",
            "domain": "Alfabetización",
            "question": "¿Cuál es esta vocal?",
            "symbol": "E",
            "options": ["A", "E", "I", "U"],
            "answer": "E",
        },
    ]

    def __init__(self, parent, bridge=None, student_id=1):
        super().__init__(parent, bg=COLORS["bg"])
        self._bridge = bridge
        self._sid = student_id
        self._idx = 0
        self._streak = 0
        self._correct_total = 0
        self._attempts = 0
        self._pL = 0.20
        self._feedback_job = None
        self._build()

    # ── construcción inicial ──────────────────

    def _build(self):
        # Cabecera
        hdr = tk.Frame(self, bg=COLORS["bg"])
        hdr.pack(fill="x", pady=(0, 24))

        tk.Label(hdr, text="Sesión de práctica",
                 font=("Helvetica", 13), bg=COLORS["bg"],
                 fg=COLORS["text_2"]).pack(anchor="w")
        tk.Label(hdr, text="Ejercicios",
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
            bg=COLORS["surface_2"], fg=COLORS["text_2"])
        self._question_lbl.pack(anchor="w")

        # Símbolo grande (letra o número)
        self._symbol_lbl = tk.Label(
            self._card, text="",
            font=("Helvetica", 96, "bold"),
            bg=COLORS["surface_2"], fg=COLORS["text"])
        self._symbol_lbl.pack(pady=28)

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

    def _load_question(self):
        q = self.QUESTIONS[self._idx % len(self.QUESTIONS)]

        self._skill_lbl.config(text=f"Habilidad: {q['skill']}")
        self._domain_lbl.config(text=q["domain"].upper())
        self._question_lbl.config(text=q["question"])
        self._symbol_lbl.config(text=q["symbol"], fg=COLORS["text"])
        self._feedback_lbl.config(text="")
        self._next_btn.config(state="normal")

        for i, opt in enumerate(q["options"]):
            btn = self._opt_btns[i]
            btn.config(
                text=opt,
                bg=COLORS["surface_3"],
                fg=COLORS["text"],
                state="normal",
            )
            btn._bg = COLORS["surface_3"]
            btn._fg = COLORS["text"]
            btn._cmd = lambda o=opt: self._check(o)
            btn.bind("<Button-1>",       lambda e, o=opt: self._check(o))
            btn.bind("<ButtonRelease-1>", lambda e, o=opt: None)

    def _check(self, chosen):
        q = self.QUESTIONS[self._idx % len(self.QUESTIONS)]
        correct = (chosen == q["answer"])
        self._attempts += 1

        # Feedback visual
        if correct:
            self._correct_total += 1
            self._streak += 1
            fb_text  = f"✓  ¡Correcto!"
            fb_color = COLORS["success"]
            sym_col  = COLORS["success"]
        else:
            self._streak = 0
            fb_text  = f"✗  La respuesta es  \"{q['answer']}\""
            fb_color = COLORS["error"]
            sym_col  = COLORS["error"]

        self._feedback_lbl.config(text=fb_text, fg=fb_color)
        self._symbol_lbl.config(fg=sym_col)

        # Actualizar estadísticas con resultado del motor
        if self._bridge:
            try:
                from bridge.hestia_bridge import METHOD
                result = self._bridge.process_response(
                    self._sid, q["id"],
                    METHOD.VISUAL, correct, 1500.0)
                self._pL = result.current_pL
            except Exception:
                # Fallback mock si falla el bridge
                delta = 0.04 if correct else -0.02
                self._pL = max(0.01, min(0.98, self._pL + delta))
        else:
            delta = 0.04 if correct else -0.02
            self._pL = max(0.01, min(0.98, self._pL + delta))

        self._pl_lbl.config(text=f"{self._pL:.2f}")
        self._streak_lbl.config(text=str(self._streak))

        # Colorear opciones
        for btn in self._opt_btns:
            if btn.cget("text") == q["answer"]:
                btn.config(bg=COLORS["success_dim"], fg=COLORS["success"], state="disabled")
                btn._bg = COLORS["success_dim"]
            elif btn.cget("text") == chosen and not correct:
                btn.config(bg=COLORS["error_dim"], fg=COLORS["error"], state="disabled")
                btn._bg = COLORS["error_dim"]
            else:
                btn.config(state="disabled")

    def _next_question(self):
        self._idx += 1
        self._load_question()


class ProgressView(tk.Frame):
    def __init__(self, parent, bridge=None, student_id=1):
        super().__init__(parent, bg=COLORS["bg"])
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


# ─────────────────────────────────────────────
# APLICACIÓN PRINCIPAL
# ─────────────────────────────────────────────

class HestiaApp:
    VIEWS = {
        "dashboard": DashboardView,
        "exercises": ExercisesView,
        "progress":  ProgressView,
        "settings":  SettingsView,
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