import pyttsx3

engine = pyttsx3.init()
voices = engine.getProperty("voices")

for i, voice in enumerate(voices):
    print("Indice:", i)
    print("ID:", voice.id)
    print("Nombre:", voice.name)
    print("Idioma:", voice.languages)
    print("-----------------------")