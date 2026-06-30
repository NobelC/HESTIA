## HESTIA — Adaptive Intelligent Tutoring System

> **Version:** 1.0

HESTIA is an intelligent tutoring engine designed to teach basic literacy and elementary mathematics to children with intellectual disabilities secondary to neurological conditions. 

**It does not replace the teacher — it is their intelligent ally.**

---

## Unique Value Proposition

HESTIA operates on **two simultaneous dimensions of adaptation**, a capability unmatched by existing educational tools for this population:

| Dimension | Question It Answers | Engine Responsible |
|-----------|---------------------|--------------------|
| **Domain** | How well does the child master this skill? | Extended BKT (5 parameters) |
| **Methodology** | How does this child learn best? | Multi-Armed Bandit (UCB) |

---

## Prototype Scope

### IN Scope
- Extended BKT engine with 5 extensions (forgetting, ceiling, fatigue, response time, anti-stall)
- MAB/UCB engine for pedagogical method selection (Visual, Auditory, Kinesthetic, Phonetic, Global)
- Local persistence with SQLite (serverless, zero leakage risk)
- Functional desktop interface using Python + Tkinter
- Basic literacy and elementary math/logic
- Monte Carlo simulator + Stress bot for theoretical validation
- Session report generation for the teacher

### OUT of Scope
- Speech or handwriting recognition
- Mobile or web application
- Networked multi-user dashboard
- Full elementary school curriculum
- Automated clinical diagnosis
- External server communication

---

## Technological Stack

| Layer | Technology | Justification |
|------|-----------|--------------|
| **AI Engine** | C++20 | O(1) per update, SIMD vectorization, scalability |
| **Persistence** | SQLite (C++) | Serverless, local file, exclusive access from C++ |
| **Bridge** | pybind11 | Exposes C++ to Python as a native module, zero overhead |
| **Frontend** | Python + Tkinter | Well-known stack, desktop-first, no external dependencies |
| **Data** | JSON | Exercises and graph structure editable without modifying code |
| **Build** | CMake + Catch2 | Reproducible across all 3 development machines |
| **Simulation** | Python (external scripts) | Monte Carlo and stress bot kept outside the main system |

## Instalación y Ejecución

HESTIA incluye scripts automáticos para preparar el entorno (compilación C++, entorno virtual de Python y dependencias).

### En Linux / macOS
```bash
./setup.sh
```

### En Windows
```cmd
setup.bat
```

### Ejecutar la Aplicación
Una vez finalizado el setup, activa el entorno virtual y ejecuta el archivo principal:
```bash
# Linux / macOS
source venv/bin/activate
python frontend/run_hestia.py

# Windows
call venv\Scripts\activate.bat
python frontend\run_hestia.py
```

### Simulation Lab
HESTIA incluye un laboratorio de simulación que prueba el motor estadístico mediante Arquetipos de Monte Carlo:
```bash
python -m frontend.sim_lab
```

---

## License
**GNU Affero General Public License v3.0 (AGPL-3.0)**.
