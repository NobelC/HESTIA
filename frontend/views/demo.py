from ContentLoader import ContentLoader
from PersistenceLayer import PersistenceLayer
from SRSQueue import SRSQueue
import time


loader = ContentLoader()
db = PersistenceLayer("hestia.db")
srs = SRSQueue("hestia.db")

contenido = loader.cargar_json("exercises/vocales.json")
ejercicios = contenido["exercises"][:5]


print("HESTIA DEMO")


id_user = db.crear_usuario("Estudiante Demo", "Alta variabilidad")

print("Usuario creado con ID:", id_user)
print("Tema:", contenido["topic"])
print()

aciertos = 0

for numero, ejercicio in enumerate(ejercicios, start=1):
    print("--------------------------------")
    print(f"Ejercicio {numero} de {len(ejercicios)}")
    print("Pregunta:", ejercicio["question"])
    print()

    for i, opcion in enumerate(ejercicio["options"], start=1):
        print(f"{i}. {opcion}")

    inicio = time.time()
    respuesta = input("\nElige una opción: ")
    fin = time.time()

    tiempo_ms = int((fin - inicio) * 1000)

    try:
        indice = int(respuesta) - 1
        respuesta_usuario = ejercicio["options"][indice]
    except:
        respuesta_usuario = ""

    if respuesta_usuario == ejercicio["correct_answer"]:
        correcto = 1
        aciertos += 1
        print("\n", ejercicio["feedback_correct"])
    else:
        correcto = 0
        print("\n", ejercicio["feedback_incorrect"])

    db.log_response(
        id_user,
        ejercicio["id"],
        ejercicio["skill_id"],
        ejercicio["method_id"],
        correcto,
        tiempo_ms
    )

    db.save_skill_state(
        id_user,
        ejercicio["skill_id"],
        0.50 if correcto else 0.30,
        0.55 if correcto else 0.35,
        0.12,
        0.20,
        0.10,
        tiempo_ms
    )

    db.save_method_state(
        id_user,
        ejercicio["method_id"],
        0.75 if correcto else 0.25,
        1
    )

    srs.mark_reviewed(
        id_user,
        ejercicio["skill_id"],
        correcto == 1
    )

    print("Respuesta guardada.")
    print()

print("       RESULTADO FINAL")
print("Aciertos:", aciertos, "/", len(ejercicios))
print("Porcentaje:", round((aciertos / len(ejercicios)) * 100, 2), "%")
print("Demo múltiple finalizada correctamente.")