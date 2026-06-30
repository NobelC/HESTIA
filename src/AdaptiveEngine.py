import random
from collections import defaultdict

from BKT import ExtendedBKT
from MAB import UCBMultiArmedBandit, MethodState

METHOD_LABELS = {
    "M1_visual": "Visual",
    "M2_auditivo": "Auditivo",
    "M3_kinestesico": "Kinestésico",
    "M4_fonetico": "Fonético",
    "M5_global": "Global/contextual",
}

METHOD_HINTS = {
    "M1_visual": "Observa la forma, el tamaño y la posición del símbolo antes de responder.",
    "M2_auditivo": "Escucha o repite mentalmente el sonido antes de responder.",
    "M3_kinestesico": "Imagina que trazas o manipulas el símbolo antes de responder.",
    "M4_fonetico": "Pronuncia el sonido de la letra y relaciónalo con la opción correcta.",
    "M5_global": "Relaciona el símbolo con una palabra o situación real.",
}

class AdaptiveEngine:
    def __init__(self, db, content, id_user):
        self.db = db
        self.content = content
        self.id_user = id_user
        self.bkt = ExtendedBKT()
        self.mab = UCBMultiArmedBandit(exploration_c=1.20)
        self.history = set()
        self.last_selected_method = None
        self.last_selected_skill = None
        self.last_log = []
        self.last_decision = {
            "phase": "inicio",
            "recommended_method": None,
            "selected_method": None,
            "reason": "Aún no hay suficientes datos."
        }

        self.exercises = content.get("exercises", [])
        self.methods_supported = content.get("methods_supported") or sorted({e["method_id"] for e in self.exercises})
        self.by_method = defaultdict(list)
        self.by_skill = defaultdict(list)
        for ex in self.exercises:
            self.by_method[ex["method_id"]].append(ex)
            self.by_skill[ex["skill_id"]].append(ex)

    def _load_bkt_state(self, skill_id):
        return self.bkt.from_db(self.db.load_skill_state(self.id_user, skill_id))

    def _save_bkt_state(self, skill_id, state):
        self.db.save_skill_state(
            self.id_user,
            skill_id,
            state.p_l_operativo,
            state.p_l_teorico,
            state.p_t,
            state.p_g,
            state.p_s,
            state.avg_time_ms
        )

    def _load_method_states(self):
        states = {}
        for method_id in self.methods_supported:
            states[method_id] = self.mab.from_db(self.db.load_method_state(self.id_user, method_id))
        return states

    def _save_method_state(self, method_id, state):
        self.db.save_method_state(self.id_user, method_id, state.q_value, state.times_used)

    def _recommended_method(self, method_states):
        usable = {
            method_id: state
            for method_id, state in method_states.items()
            if state.times_used >= 3
        }
        if not usable:
            return None
        return max(usable, key=lambda m: usable[m].q_value)

    def _select_adaptive_method(self, available_methods, method_states):
        """
        MAB con adaptación visible:
        1) Primero explora métodos no usados o poco usados.
        2) Cuando ya existe evidencia mínima, recomienda el método con mayor Q.
        3) Prioriza ese método la mayor parte del tiempo, pero mantiene exploración.
        """
        total_uses = sum(method_states.get(m, MethodState()).times_used for m in available_methods)

        # Exploración inicial obligatoria: todos los métodos deben probarse al menos 3 veces.
        for method_id in available_methods:
            if method_states.get(method_id, MethodState()).times_used < 3:
                self.last_decision = {
                    "phase": "exploración",
                    "recommended_method": None,
                    "selected_method": method_id,
                    "reason": "HESTIA aún está probando métodos para reunir evidencia."
                }
                return method_id

        recommended = self._recommended_method(method_states)
        selected_by_ucb = self.mab.select_method(available_methods, method_states)

        # 80% prioriza el método que está funcionando mejor; 20% explora con UCB.
        if recommended and random.random() < 0.80:
            selected = recommended
            phase = "personalización"
            reason = "HESTIA priorizó el método con mejor desempeño acumulado para este perfil."
        else:
            selected = selected_by_ucb
            phase = "exploración controlada"
            reason = "HESTIA mantuvo exploración para no quedarse fija en un método."

        self.last_decision = {
            "phase": phase,
            "recommended_method": recommended,
            "selected_method": selected,
            "reason": reason
        }
        return selected

    def _select_skill_for_method(self, method_id):
        candidates = self.by_method.get(method_id, [])
        if not candidates:
            candidates = self.exercises[:]

        best_exercise = None
        best_mastery = 2.0

        unseen = [ex for ex in candidates if ex["id"] not in self.history]
        pool = unseen if unseen else candidates

        for ex in pool:
            state = self._load_bkt_state(ex["skill_id"])
            if state.p_l_operativo < best_mastery:
                best_mastery = state.p_l_operativo
                best_exercise = ex

        return best_exercise or random.choice(self.exercises)

    def next_exercise(self):
        method_states = self._load_method_states()
        available_methods = [m for m in self.methods_supported if self.by_method.get(m)]
        selected_method = self._select_adaptive_method(available_methods, method_states)
        exercise = self._select_skill_for_method(selected_method)

        self.last_selected_method = selected_method
        self.last_selected_skill = exercise["skill_id"]

        recommended = self.last_decision.get("recommended_method")
        recommended_label = METHOD_LABELS.get(recommended, "Aún sin recomendación")
        selected_label = METHOD_LABELS.get(selected_method, selected_method)

        self.last_log = [
            f"Fase MAB: {self.last_decision['phase']}",
            f"Método seleccionado: {selected_label}",
            f"Método recomendado: {recommended_label}",
            f"Motivo: {self.last_decision['reason']}",
            f"Habilidad objetivo: {exercise['skill_id']}"
        ]

        return exercise

    def process_answer(self, exercise, is_correct, response_time_ms):
        skill_id = exercise["skill_id"]
        method_id = exercise["method_id"]

        old_state = self._load_bkt_state(skill_id)
        new_state = self.bkt.update(old_state, bool(is_correct), int(response_time_ms))
        self._save_bkt_state(skill_id, new_state)

        speed_bonus = 0.15 if response_time_ms <= 6000 else 0.0
        reward = (1.0 if is_correct else 0.0) + speed_bonus
        reward = min(1.0, reward)

        method_state = self.mab.from_db(self.db.load_method_state(self.id_user, method_id))
        new_method_state = self.mab.update(method_state, reward)
        self._save_method_state(method_id, new_method_state)

        self.db.log_response(
            self.id_user,
            exercise["id"],
            skill_id,
            method_id,
            int(is_correct),
            int(response_time_ms),
            new_state.p_l_operativo,
            method_id
        )

        self.history.add(exercise["id"])

        self.last_log = [
            f"BKT actualizó {skill_id}: {old_state.p_l_operativo:.2f} → {new_state.p_l_operativo:.2f}",
            f"MAB actualizó {METHOD_LABELS.get(method_id, method_id)}: Q={new_method_state.q_value:.2f}, usos={new_method_state.times_used}",
            f"Respuesta={'correcta' if is_correct else 'incorrecta'}, tiempo={response_time_ms}ms"
        ]

        return new_state, new_method_state

    def get_study_hint(self, method_id=None):
        method_id = method_id or self.last_selected_method
        return METHOD_HINTS.get(method_id, "Responde con calma y observa la retroalimentación.")

    def get_metrics(self):
        skill_states = self.db.load_all_latest_skill_states(self.id_user)
        method_states_db = self.db.load_all_latest_method_states(self.id_user)
        summary = self.db.get_summary(self.id_user)

        if skill_states:
            avg_mastery = sum(s["p_l_operativo"] for s in skill_states.values()) / len(skill_states)
        else:
            avg_mastery = 0.0

        best_method = None
        best_q = -1
        for method_id, state in method_states_db.items():
            if state["q_value"] > best_q:
                best_q = state["q_value"]
                best_method = method_id

        return {
            "accuracy": summary["accuracy"],
            "total": summary["total"],
            "correct": summary["correct"],
            "avg_time": summary["avg_time"],
            "avg_mastery": avg_mastery,
            "best_method": best_method or "Sin datos",
            "method_states": method_states_db,
            "skill_states": skill_states,
            "last_decision": self.last_decision,
        }
