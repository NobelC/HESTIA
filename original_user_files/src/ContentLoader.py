import json


class ContentLoader:

    def cargar_json(self, ruta):
        with open(ruta, "r", encoding="utf-8") as archivo:
            datos = json.load(archivo)

        return datos