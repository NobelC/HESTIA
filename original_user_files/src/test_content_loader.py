from ContentLoader import ContentLoader

loader = ContentLoader()

vocales = loader.cargar_json("exercises/vocales.json")
numeros = loader.cargar_json("exercises/numeros.json")
limites = loader.cargar_json("exercises/limites.json")
skill_graph = loader.cargar_json("data/skill_graph.json")

print("Tema vocales:", vocales["topic"])
print("Cantidad ejercicios vocales:", len(vocales["exercises"]))

print("Tema números:", numeros["topic"])
print("Cantidad ejercicios números:", len(numeros["exercises"]))

print("Tema límites:", limites["topic"])
print("Cantidad ejercicios límites:", len(limites["exercises"]))

print("Cantidad habilidades:", len(skill_graph["skills"]))