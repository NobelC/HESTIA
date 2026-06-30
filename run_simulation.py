from pathlib import Path
import sys
import csv
import random
from collections import Counter

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR / "src"))

from ContentLoader import ContentLoader
from PersistenceLayer import PersistenceLayer
from AdaptiveEngine import AdaptiveEngine, METHOD_LABELS

PROFILES = {
    "visual_fuerte": {"M1_visual": 0.86, "M4_fonetico": 0.48},
    "fonetico_fuerte": {"M1_visual": 0.48, "M4_fonetico": 0.86},
    "balanceado": {"M1_visual": 0.68, "M4_fonetico": 0.68},
    "alta_variabilidad": {"M1_visual": 0.62, "M4_fonetico": 0.62},
}

def simulate_response(profile_name, method_id):
    base = PROFILES[profile_name].get(method_id, 0.55)
    if profile_name == "alta_variabilidad":
        base = max(0.20, min(0.92, random.gauss(base, 0.22)))
    correct = random.random() < base
    response_time = int(random.gauss(4200 if correct else 6900, 1100))
    return correct, max(800, response_time)

def count_methods(rows, profile, start, end):
    selected = [r for r in rows if r["profile"] == profile and start <= r["attempt"] <= end]
    c = Counter(r["method_label"] for r in selected)
    return dict(c)

def run_module(module_file="vocales.json", attempts=40, seed=17):
    random.seed(seed)
    loader = ContentLoader()
    content = loader.cargar_modulo(BASE_DIR, module_file)

    db_path = BASE_DIR / "hestia_simulation.db"
    if db_path.exists():
        db_path.unlink()
    db = PersistenceLayer(db_path)

    results_dir = BASE_DIR / "results"
    results_dir.mkdir(exist_ok=True)
    rows = []
    summary_rows = []
    adaptation_rows = []

    for profile_name in PROFILES:
        id_user = db.crear_usuario(f"Bot {profile_name}", profile_name)
        engine = AdaptiveEngine(db, content, id_user)

        for attempt in range(1, attempts + 1):
            ex = engine.next_exercise()
            decision_before = engine.last_decision.copy()
            correct, rt = simulate_response(profile_name, ex["method_id"])
            bkt_state, mab_state = engine.process_answer(ex, correct, rt)

            rows.append({
                "profile": profile_name,
                "attempt": attempt,
                "phase": decision_before["phase"],
                "recommended_method": decision_before.get("recommended_method") or "",
                "recommended_label": METHOD_LABELS.get(decision_before.get("recommended_method"), ""),
                "selected_method": ex["method_id"],
                "method_label": METHOD_LABELS.get(ex["method_id"], ex["method_id"]),
                "exercise_id": ex["id"],
                "skill_id": ex["skill_id"],
                "correct": int(correct),
                "response_time_ms": rt,
                "p_l_after": round(bkt_state.p_l_operativo, 4),
                "method_q": round(mab_state.q_value, 4),
                "method_uses": mab_state.times_used,
            })

        metrics = engine.get_metrics()
        method_states = metrics["method_states"]
        best_method = metrics["best_method"]

        first_half = [r for r in rows if r["profile"] == profile_name and r["attempt"] <= attempts//2]
        second_half = [r for r in rows if r["profile"] == profile_name and r["attempt"] > attempts//2]
        first_counts = Counter(r["method_label"] for r in first_half)
        second_counts = Counter(r["method_label"] for r in second_half)

        best_label = METHOD_LABELS.get(best_method, best_method)
        first_best_uses = first_counts.get(best_label, 0)
        second_best_uses = second_counts.get(best_label, 0)

        summary_rows.append({
            "profile": profile_name,
            "attempts": metrics["total"],
            "correct": metrics["correct"],
            "accuracy_percent": round(metrics["accuracy"] * 100, 2),
            "avg_mastery_percent": round(metrics["avg_mastery"] * 100, 2),
            "best_method": best_method,
            "best_method_label": best_label,
            "m1_q": round(method_states.get("M1_visual", {}).get("q_value", 0), 4),
            "m1_uses": method_states.get("M1_visual", {}).get("times_used", 0),
            "m4_q": round(method_states.get("M4_fonetico", {}).get("q_value", 0), 4),
            "m4_uses": method_states.get("M4_fonetico", {}).get("times_used", 0),
        })

        adaptation_rows.append({
            "profile": profile_name,
            "best_method_label": best_label,
            "first_half_best_method_uses": first_best_uses,
            "second_half_best_method_uses": second_best_uses,
            "first_half_distribution": "; ".join(f"{k}:{v}" for k, v in sorted(first_counts.items())),
            "second_half_distribution": "; ".join(f"{k}:{v}" for k, v in sorted(second_counts.items())),
            "adaptation_interpretation": (
                "Aumentó la prioridad del método favorecido"
                if second_best_uses > first_best_uses else
                "Mantuvo exploración por rendimiento similar o variable"
            )
        })

    detail_path = results_dir / "simulation_detail.csv"
    summary_path = results_dir / "simulation_summary.csv"
    adaptation_path = results_dir / "adaptation_evidence.csv"
    article_path = results_dir / "article_results_table.txt"

    with detail_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    with summary_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(summary_rows[0].keys()))
        writer.writeheader()
        writer.writerows(summary_rows)

    with adaptation_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(adaptation_rows[0].keys()))
        writer.writeheader()
        writer.writerows(adaptation_rows)

    with article_path.open("w", encoding="utf-8") as f:
        f.write("Tabla sugerida para el artículo: Evidencia de adaptación del método pedagógico\n\n")
        f.write("Perfil | Método favorecido | Uso 1ra mitad | Uso 2da mitad | Interpretación\n")
        f.write("--- | --- | ---: | ---: | ---\n")
        for r in adaptation_rows:
            f.write(
                f"{r['profile']} | {r['best_method_label']} | "
                f"{r['first_half_best_method_uses']} | {r['second_half_best_method_uses']} | "
                f"{r['adaptation_interpretation']}\n"
            )
        f.write("\nResumen funcional\n\n")
        f.write("Perfil | Intentos | Precisión | Dominio promedio | Método favorecido | Q Visual | Q Fonético\n")
        f.write("--- | ---: | ---: | ---: | --- | ---: | ---:\n")
        for r in summary_rows:
            f.write(
                f"{r['profile']} | {r['attempts']} | {r['accuracy_percent']}% | "
                f"{r['avg_mastery_percent']}% | {r['best_method_label']} | {r['m1_q']} | {r['m4_q']}\n"
            )

    print("Simulación adaptativa terminada.")
    print(f"Detalle: {detail_path}")
    print(f"Resumen: {summary_path}")
    print(f"Evidencia de adaptación: {adaptation_path}")
    print(f"Tabla para artículo: {article_path}")

if __name__ == "__main__":
    run_module("vocales.json", attempts=40, seed=17)
