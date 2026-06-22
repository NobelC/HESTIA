import tkinter as tk
from tkinter import messagebox
import time

from ContentLoader import ContentLoader
from PersistenceLayer import PersistenceLayer
from SRSQueue import SRSQueue


class VocalesApp:
    def __init__(self, root):
        self.root = root
        self.root.title("HESTIA - Vocales")
        self.root.geometry("750x550")
        self.root.resizable(False, False)

        self.loader = ContentLoader()
        self.db = PersistenceLayer("hestia.db")
        self.srs = SRSQueue("hestia.db")

        self.contenido = self.loader.cargar_json("exercises/vocales.json")
        self.ejercicios = self.contenido["exercises"]

        self.id_user = None
        self.indice_actual = 0
        self.aciertos = 0
        self.inicio_tiempo = None

        self.mostrar_bienvenida()

    def limpiar_pantalla(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    def mostrar_bienvenida(self):
        self.limpiar_pantalla()

        titulo = tk.Label(
            self.root,
            text="HESTIA",
            font=("Arial", 36, "bold")
        )
        titulo.pack(pady=40)

        subtitulo = tk.Label(
            self.root,
            text="Motor de Aprendizaje Adaptativo",
            font=("Arial", 18)
        )
        subtitulo.pack(pady=10)

        descripcion = tk.Label(
            self.root,
            text="Módulo inicial de vocales\nEjercicios visuales y fonéticos",
            font=("Arial", 14),
            justify="center"
        )
        descripcion.pack(pady=30)

        boton_iniciar = tk.Button(
            self.root,
            text="Iniciar módulo de vocales",
            font=("Arial", 16, "bold"),
            width=25,
            height=2,
            command=self.iniciar_modulo
        )
        boton_iniciar.pack(pady=30)

        nota = tk.Label(
            self.root,
            text="Los resultados serán registrados localmente en SQLite.",
            font=("Arial", 11)
        )
        nota.pack(pady=10)

    def iniciar_modulo(self):
        self.id_user = self.db.crear_usuario(
            "Estudiante Tkinter",
            "Alta variabilidad"
        )

        self.indice_actual = 0
        self.aciertos = 0

        self.crear_interfaz_ejercicios()
        self.mostrar_ejercicio()

    def crear_interfaz_ejercicios(self):
        self.limpiar_pantalla()

        self.titulo = tk.Label(
            self.root,
            text="HESTIA - Módulo de Vocales",
            font=("Arial", 22, "bold")
        )
        self.titulo.pack(pady=20)

        self.info = tk.Label(
            self.root,
            text="",
            font=("Arial", 12)
        )
        self.info.pack(pady=5)

        self.pregunta = tk.Label(
            self.root,
            text="",
            font=("Arial", 20),
            wraplength=650,
            justify="center"
        )
        self.pregunta.pack(pady=30)

        self.frame_opciones = tk.Frame(self.root)
        self.frame_opciones.pack(pady=10)

        self.botones = []

        for i in range(4):
            boton = tk.Button(
                self.frame_opciones,
                text="",
                font=("Arial", 18),
                width=12,
                height=2,
                command=lambda i=i: self.validar_respuesta(i)
            )
            boton.grid(row=i // 2, column=i % 2, padx=15, pady=10)
            self.botones.append(boton)

        self.feedback = tk.Label(
            self.root,
            text="",
            font=("Arial", 14, "bold")
        )
        self.feedback.pack(pady=20)

        self.progreso = tk.Label(
            self.root,
            text="",
            font=("Arial", 11)
        )
        self.progreso.pack(pady=5)

    def mostrar_ejercicio(self):
        if self.indice_actual >= len(self.ejercicios):
            self.mostrar_resultado_final()
            return

        ejercicio = self.ejercicios[self.indice_actual]

        self.info.config(
            text=f"Usuario ID: {self.id_user} | Tema: {self.contenido['topic']} | Método: {ejercicio['method_id']}"
        )

        self.pregunta.config(text=ejercicio["question"])

        for i, opcion in enumerate(ejercicio["options"]):
            self.botones[i].config(
                text=opcion,
                state="normal"
            )

        self.feedback.config(text="")
        self.progreso.config(
            text=f"Ejercicio {self.indice_actual + 1} de {len(self.ejercicios)}"
        )

        self.inicio_tiempo = time.time()

    def validar_respuesta(self, indice_opcion):
        ejercicio = self.ejercicios[self.indice_actual]

        fin_tiempo = time.time()
        tiempo_ms = int((fin_tiempo - self.inicio_tiempo) * 1000)

        respuesta_usuario = ejercicio["options"][indice_opcion]

        if respuesta_usuario == ejercicio["correct_answer"]:
            correcto = 1
            self.aciertos += 1
            self.feedback.config(
                text=ejercicio["feedback_correct"],
                fg="green"
            )
        else:
            correcto = 0
            self.feedback.config(
                text=ejercicio["feedback_incorrect"],
                fg="red"
            )

        self.guardar_resultado(ejercicio, correcto, tiempo_ms)

        for boton in self.botones:
            boton.config(state="disabled")

        self.root.after(1200, self.siguiente_ejercicio)

    def guardar_resultado(self, ejercicio, correcto, tiempo_ms):
        self.db.log_response(
            self.id_user,
            ejercicio["id"],
            ejercicio["skill_id"],
            ejercicio["method_id"],
            correcto,
            tiempo_ms
        )

        self.db.save_skill_state(
            self.id_user,
            ejercicio["skill_id"],
            0.50 if correcto else 0.30,
            0.55 if correcto else 0.35,
            0.12,
            0.20,
            0.10,
            tiempo_ms
        )

        self.db.save_method_state(
            self.id_user,
            ejercicio["method_id"],
            0.75 if correcto else 0.25,
            1
        )

        self.srs.mark_reviewed(
            self.id_user,
            ejercicio["skill_id"],
            correcto == 1
        )

    def siguiente_ejercicio(self):
        self.indice_actual += 1
        self.mostrar_ejercicio()

    def mostrar_resultado_final(self):
        self.limpiar_pantalla()

        porcentaje = round((self.aciertos / len(self.ejercicios)) * 100, 2)

        titulo = tk.Label(
            self.root,
            text="Módulo finalizado",
            font=("Arial", 28, "bold")
        )
        titulo.pack(pady=40)

        resultado = tk.Label(
            self.root,
            text=f"Aciertos: {self.aciertos}/{len(self.ejercicios)}",
            font=("Arial", 20)
        )
        resultado.pack(pady=10)

        porcentaje_label = tk.Label(
            self.root,
            text=f"Porcentaje: {porcentaje}%",
            font=("Arial", 20)
        )
        porcentaje_label.pack(pady=10)

        guardado = tk.Label(
            self.root,
            text="Los datos fueron guardados correctamente en SQLite.",
            font=("Arial", 13)
        )
        guardado.pack(pady=20)

        boton_reiniciar = tk.Button(
            self.root,
            text="Volver al inicio",
            font=("Arial", 14),
            width=20,
            height=2,
            command=self.mostrar_bienvenida
        )
        boton_reiniciar.pack(pady=20)

        messagebox.showinfo(
            "Resultado final",
            f"Terminaste el módulo de vocales.\n\nAciertos: {self.aciertos}/{len(self.ejercicios)}\nPorcentaje: {porcentaje}%"
        )


if __name__ == "__main__":
    root = tk.Tk()
    app = VocalesApp(root)
    root.mainloop()