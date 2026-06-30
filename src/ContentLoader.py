import json
from pathlib import Path

class ContentLoader:
    def cargar_json(self, ruta):
        ruta = Path(ruta)
        with ruta.open("r", encoding="utf-8") as archivo:
            return json.load(archivo)

    def cargar_modulo(self, base_dir, nombre_archivo):
        return self.cargar_json(Path(base_dir) / "exercises" / nombre_archivo)
