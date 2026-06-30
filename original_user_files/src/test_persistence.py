from PersistenceLayer import PersistenceLayer

db = PersistenceLayer("hestia.db")

id_user = db.crear_usuario("Héctor", "Alta variabilidad")

print("Usuario creado con ID:", id_user)

usuario = db.load_user(id_user)

print("Usuario cargado:")
print(usuario)