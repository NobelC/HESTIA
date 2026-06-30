from dataclasses import dataclass

@dataclass
class BKTState:
    p_l_operativo: float = 0.25
    p_l_teorico: float = 0.25
    p_t: float = 0.12
    p_g: float = 0.20
    p_s: float = 0.10
    avg_time_ms: float = 0.0

class ExtendedBKT:
    """
    Implementación demo de Bayesian Knowledge Tracing extendido.

    - p_l_operativo: dominio usado por la interfaz, con techo para mantener sensibilidad.
    - p_l_teorico: dominio acumulado sin techo operativo.
    - p_t: probabilidad de aprendizaje después de un intento.
    - p_g: probabilidad de acertar sin dominar.
    - p_s: probabilidad de fallar aunque se domine.
    """

    def __init__(self, cap=0.98):
        self.cap = cap

    def from_db(self, row):
        if not row:
            return BKTState()
        return BKTState(
            p_l_operativo=float(row.get("p_l_operativo", 0.25)),
            p_l_teorico=float(row.get("p_l_teorico", 0.25)),
            p_t=float(row.get("p_t", 0.12)),
            p_g=float(row.get("p_g", 0.20)),
            p_s=float(row.get("p_s", 0.10)),
            avg_time_ms=float(row.get("avg_time_ms", 0.0)),
        )

    def update(self, state, is_correct, response_time_ms):
        prior = max(0.001, min(0.999, state.p_l_operativo))
        p_t = self._dynamic_transition(state.p_t, response_time_ms)
        p_g = self._dynamic_guess(state.p_g, is_correct, response_time_ms)
        p_s = self._dynamic_slip(state.p_s, is_correct, response_time_ms)

        if is_correct:
            numerator = prior * (1.0 - p_s)
            denominator = numerator + (1.0 - prior) * p_g
        else:
            numerator = prior * p_s
            denominator = numerator + (1.0 - prior) * (1.0 - p_g)

        posterior = numerator / max(denominator, 1e-9)

        # BKT clásico: posterior + aprendizaje posterior al intento.
        learned = posterior + (1.0 - posterior) * p_t

        # Teórico acumula sin techo operativo.
        p_l_teorico = max(state.p_l_teorico, min(1.0, learned))

        # Operativo queda capado para evitar que el sistema deje de reaccionar.
        p_l_operativo = min(self.cap, learned)

        if state.avg_time_ms <= 0:
            avg_time = float(response_time_ms)
        else:
            avg_time = 0.75 * state.avg_time_ms + 0.25 * float(response_time_ms)

        return BKTState(
            p_l_operativo=p_l_operativo,
            p_l_teorico=p_l_teorico,
            p_t=p_t,
            p_g=p_g,
            p_s=p_s,
            avg_time_ms=avg_time,
        )

    def _dynamic_transition(self, base_p_t, response_time_ms):
        # Si la sesión se vuelve lenta, baja levemente la probabilidad de aprender por fatiga.
        if response_time_ms > 12000:
            return max(0.05, base_p_t * 0.90)
        if response_time_ms < 2500:
            return min(0.20, base_p_t * 1.05)
        return base_p_t

    def _dynamic_guess(self, base_p_g, is_correct, response_time_ms):
        # Acierto muy rápido: puede ser dominio, pero también suerte; se mantiene sensibilidad.
        if is_correct and response_time_ms < 1800:
            return min(0.35, base_p_g + 0.03)
        return base_p_g

    def _dynamic_slip(self, base_p_s, is_correct, response_time_ms):
        # Error muy rápido: posible impulsividad. Error muy lento: posible laguna conceptual.
        if (not is_correct) and response_time_ms < 2000:
            return min(0.25, base_p_s + 0.04)
        if (not is_correct) and response_time_ms > 12000:
            return min(0.22, base_p_s + 0.02)
        return base_p_s
