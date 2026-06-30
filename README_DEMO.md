# HESTIA DEMO ADAPTATIVA

Esta versión corrige el punto clave de la demo: no solo muestra porcentajes, sino que **cambia la forma de estudiar** según el método que más favorece al estudiante.

## Qué hace

- Primero explora distintos métodos pedagógicos.
- Calcula el rendimiento de cada método con Multi-Armed Bandit/UCB.
- Recomienda el método con mejor desempeño acumulado.
- Prioriza ese método en los siguientes ejercicios.
- Mantiene exploración controlada para evitar quedarse fija en una sola opción.
- Actualiza el dominio de habilidades con Bayesian Knowledge Tracing.

## Cómo ejecutar la demo visual

```bash
python run_hestia.py
```

En la pantalla debe verse:

- Fase: exploración / personalización / exploración controlada.
- Método aplicado ahora.
- Método recomendado.
- Estrategia de estudio aplicada.
- Log del motor BKT + MAB.

## Cómo generar resultados para el artículo

```bash
python run_simulation.py
```

Genera:

- `results/simulation_detail.csv`
- `results/simulation_summary.csv`
- `results/adaptation_evidence.csv`
- `results/article_results_table.txt`

El archivo más importante para el artículo es:

`results/article_results_table.txt`

## Cómo explicar esta demo

HESTIA no solo calcula métricas. La demo observa qué método produce mejores respuestas en el perfil simulado y luego empieza a priorizar ese método. Por ejemplo, si un perfil responde mejor con recursos visuales, el MAB favorece ejercicios visuales; si responde mejor con recursos fonéticos, favorece ejercicios fonéticos.

## Qué no se debe afirmar

No se debe afirmar que HESTIA ya mejora las notas de estudiantes reales. Los resultados corresponden a una validación funcional/simulada del motor adaptativo.


## Cómo colocar audios en el método fonético

1. Entra a la carpeta:

```text
assets/audio/
```

2. Coloca tus audios en formato WAV con estos nombres sugeridos:

```text
a.wav
e.wav
i.wav
o.wav
u.wav
```

3. Para números, usa:

```text
uno.wav
dos.wav
tres.wav
cuatro.wav
cinco.wav
seis.wav
siete.wav
ocho.wav
nueve.wav
diez.wav
```

4. Los ejercicios fonéticos ya tienen el campo `audio_path`, por ejemplo:

```json
"audio_path": "assets/audio/a.wav"
```

5. Ejecuta:

```bash
python run_hestia.py
```

Cuando el método activo sea fonético o auditivo, la demo reproduce el audio automáticamente y también muestra un botón `Reproducir audio`.

### Si tus audios son MP3

Puedes usar MP3, pero instala pygame:

```bash
pip install pygame
```

Luego cambia en el JSON:

```json
"audio_path": "assets/audio/a.mp3"
```
