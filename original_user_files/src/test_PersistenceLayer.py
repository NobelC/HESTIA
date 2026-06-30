from PersistenceLayer import PersistenceLayer

db = PersistenceLayer("hestia.db")

id_user = db.crear_usuario("Héctor", "Alta variabilidad")

print("Usuario creado con ID:", id_user)

usuario = db.load_user(id_user)
print("Usuario cargado:", usuario)

db.save_skill_state(
    id_user,
    "vocal_a",
    0.45,
    0.50,
    0.12,
    0.20,
    0.10,
    1500
)

estado = db.load_skill_state(id_user, "vocal_a")
print("Estado de habilidad:", estado)

db.save_method_state(
    id_user,
    "M1_visual",
    0.75,
    4
)

db.log_response(
    id_user,
    "ex_vocal_a_001",
    "vocal_a",
    "M1_visual",
    1,
    1200
)

print("Prueba de PersistenceLayer completada.")