import math
from dataclasses import dataclass

@dataclass
class MethodState:
    q_value: float = 0.0
    times_used: int = 0

class UCBMultiArmedBandit:
    """
    Multi-Armed Bandit con regla UCB.
    Explora métodos no usados y luego favorece el método con mejor recompensa observada.
    """

    def __init__(self, exploration_c=1.20):
        self.exploration_c = exploration_c

    def from_db(self, row):
        if not row:
            return MethodState()
        return MethodState(
            q_value=float(row.get("q_value", 0.0)),
            times_used=int(row.get("times_used", 0))
        )

    def select_method(self, method_ids, method_states):
        if not method_ids:
            raise ValueError("No hay métodos disponibles para seleccionar.")

        # Explorar primero los métodos que no han sido usados.
        for method_id in method_ids:
            if method_states.get(method_id, MethodState()).times_used == 0:
                return method_id

        total_uses = sum(method_states.get(m, MethodState()).times_used for m in method_ids)
        total_uses = max(total_uses, 1)

        best_method = None
        best_score = -1e9

        for method_id in method_ids:
            state = method_states.get(method_id, MethodState())
            n = max(state.times_used, 1)
            exploration = self.exploration_c * math.sqrt(math.log(total_uses + 1) / n)
            score = state.q_value + exploration

            if score > best_score:
                best_score = score
                best_method = method_id

        return best_method

    def update(self, state, reward):
        reward = float(reward)
        new_n = state.times_used + 1
        new_q = state.q_value + (reward - state.q_value) / new_n
        return MethodState(q_value=new_q, times_used=new_n)
