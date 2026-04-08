# 🧠 HESTIA — Sistema de Tutoría Inteligente Adaptativa

> **Versión:** 1.0

HESTIA es un motor de tutoría inteligente diseñado para enseñar alfabetización básica y matemáticas elementales a niños con discapacidad intelectual secundaria a condiciones neurológicas. 

**No reemplaza al docente — es su aliado inteligente.**

---

## ✨ Propuesta de Valor Única

HESTIA opera en **dos dimensiones de adaptación simultáneas**, algo que ninguna herramienta educativa existente hace para esta población:

| Dimensión | Pregunta que responde | Motor responsable |
|-----------|----------------------|------------------|
| **Dominio** | ¿Cuánto domina el niño esta habilidad? | BKT Extendido (5 parámetros) |
| **Metodología** | ¿Cómo aprende mejor este niño? | Multi-Armed Bandit (UCB) |

---

## 🎯 Alcance del Prototipo

### ✅ DENTRO del scope
- Motor BKT Extendido con 5 extensiones (olvido, techo, fatiga, tiempo de respuesta, anti-stall)
- Motor MAB/UCB para selección de método pedagógico (Visual, Auditivo, Kinestésico, Fonético, Global)
- Persistencia local con SQLite (sin servidor, sin riesgo de filtración)
- Interfaz desktop funcional con Python + TKinter
- Vocales A–U y Números 1–10
- Simulador Monte Carlo + Bot de estrés para validación teórica
- Reporte de sesión al docente

### ❌ FUERA del scope
- Reconocimiento de voz o escritura a mano
- Aplicación móvil o web
- Panel multi-usuario en red
- Currículo completo de primaria
- Diagnóstico clínico automatizado
- Comunicación con servidores externos

---

## 🏗️ Arquitectura y Stack Tecnológico
hestia/
├── backend/                  # Motor IA en C++20
│   ├── include/              # Headers: BKTEngine, MABEngine, ZoneBlender...
│   ├── src/                  # Implementaciones
│   ├── tests/                # Tests unitarios con Catch2
│   └── CMakeLists.txt
├── frontend/                 # UI en Python + TKinter
│   ├── app.py
│   ├── views/                # Pantallas: AssentScreen, ExerciseScreen...
│   └── bridge/hestia_bridge.py  # Único punto de contacto con C++
├── data/                     # JSON editables
│   ├── skill_graph.json
│   └── exercises/
├── simulation/               # Validación teórica
│   ├── monte_carlo.py
│   └── stress_bot.py
├── docs/                     # Documentación técnica
├── scripts/
│   ├── build.sh
│   └── migrations/           # Scripts de migración de DB
├── .gitignore
└── README.md


| Capa | Tecnología | Justificación |
|------|-----------|--------------|
| **Motor IA** | C++20 | O(1) por update, vectorización SIMD, escalabilidad |
| **Persistencia** | SQLite (C++) | Sin servidor, archivo local, acceso exclusivo desde C++ |
| **Bridge** | pybind11 | Expone C++ a Python como módulo nativo, cero overhead |
| **Frontend** | Python + TKinter | Stack conocido, desktop-first, sin dependencias externas |
| **Datos** | JSON | Ejercicios y grafo editables sin tocar código |
| **Build** | CMake + Catch2 | Reproducible en las 3 máquinas del equipo |
| **Simulación** | Python (scripts externos) | Monte Carlo y bot de estrés fuera del sistema principal |

---
### Flujo de Decisión por Ejercicio
[Sesión inicia] → [MAB selecciona método] → [ZoneBlender define ejercicio según P(L)]
       ↓
[Niño responde: correcto, tiempo_ms]
       ↓
[BKT actualiza P(L)]  ←→  [MAB actualiza Q(método)]

