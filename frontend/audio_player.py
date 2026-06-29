from pathlib import Path
import sys
import threading
import subprocess

class AudioPlayer:
    """
    Reproductor simple para la demo.
    - WAV en Windows: usa winsound, no requiere instalar nada.
    - MP3/WAV con pygame: opcional si instalas pygame.
    """

    def __init__(self, base_dir):
        self.base_dir = Path(base_dir)

    def play(self, audio_path):
        if not audio_path:
            return False, "Este ejercicio no tiene audio asignado."

        path = Path(audio_path)
        if not path.is_absolute():
            path = self.base_dir / path

        if not path.exists():
            return False, f"No encontré el audio: {path}"

        suffix = path.suffix.lower()

        def _play():
            try:
                if suffix == ".wav" and sys.platform.startswith("win"):
                    import winsound
                    winsound.PlaySound(str(path), winsound.SND_FILENAME)
                    return

                # Opción para MP3 o WAV si pygame está instalado
                try:
                    import pygame
                    pygame.mixer.init()
                    pygame.mixer.music.load(str(path))
                    pygame.mixer.music.play()
                    return
                except Exception:
                    pass

                # Fallback macOS
                if sys.platform == "darwin":
                    subprocess.run(["afplay", str(path)], check=False)
                    return

                # Fallback Linux
                subprocess.run(["xdg-open", str(path)], check=False)

            except Exception:
                pass

        threading.Thread(target=_play, daemon=True).start()
        return True, f"Reproduciendo: {path.name}"
