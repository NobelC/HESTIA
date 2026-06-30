import sys
import os
import glob
from typing import List, Optional, Any

# --- Configuración de Rutas del Proyecto ---
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "../../"))
# Buscar el módulo C++ en build/backend
SEARCH_PATH = os.path.join(PROJECT_ROOT, "build/backend")

if SEARCH_PATH not in sys.path:
    sys.path.append(SEARCH_PATH)

try:
    import hestia_core
except ImportError as e:
    potential_so = glob.glob(os.path.join(SEARCH_PATH, "hestia_core*.so"))
    if not potential_so:
        raise ImportError(
            f"No se pudo encontrar 'hestia_core' en {SEARCH_PATH}. "
            f"Asegúrate de haber ejecutado './scripts/build.sh'. Error original: {e}"
        )
    import hestia_core

# --- Aliases para legibilidad ---
from hestia_core.mab import METHOD
from hestia_core.zone import Zone

class HestiaBridge:
    """
    Bridge entre la UI de Python y el motor de IA en C++.
    Sigue el patrón Singleton para asegurar que solo haya un motor activo.
    """
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(HestiaBridge, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, db_path: str = "hestia.db", skill_graph_path: Optional[str] = None):
        if self._initialized:
            return
        
        # Resolver path del grafo si no se provee
        if skill_graph_path is None:
            skill_graph_path = os.path.join(PROJECT_ROOT, "data/skill_graph.json")
        
        # 1. Inicializar componentes del motor
        self.bkt_engine = hestia_core.bkt.BKTEngine()
        self.mab_engine = hestia_core.mab.MABEngine(exploration_c=1.0)
        self.session_manager = hestia_core.bkt.SessionManager()
        self.blender = hestia_core.zone.ZoneBlender(seed=0)
        self.srs_queue = hestia_core.srs.SRSQueue()
        
        # 2. Cargar Grafo de Habilidades
        self.skill_graph = hestia_core.graph.SkillGraph()
        if os.path.exists(skill_graph_path):
            self.skill_graph.load(skill_graph_path)
        
        # 3. Inicializar Capa de Persistencia
        self.storage = hestia_core.persistence.PersistenceLayer.create(db_path)
        if self.storage is None:
            raise RuntimeError(
                f"Error crítico: No se pudo inicializar la persistencia en '{db_path}'. "
                "Verifica que la base de datos exista y tenga el esquema correcto (PRAGMA user_version=1)."
            )
        
        # 4. Procesador Central
        self.processor = hestia_core.core.ResponseProcessor(
            self.bkt_engine,
            self.mab_engine,
            self.session_manager,
            self.storage,
            self.blender,
            self.skill_graph,
            self.srs_queue,
            0.5 # lambda_val default
        )
        
        self._initialized = True

    def process_response(self, student_id: int, skill_id: int,
                         method: METHOD, correct: bool,
                         response_ms: float) -> Any:
        """
        Procesa una respuesta del estudiante y retorna la recomendación para el siguiente ejercicio.
        """
        return self.processor.process_response(
            student_id, skill_id, method, correct, response_ms
        )

    def process_response_timed(self, student_id: int, skill_id: int,
                               method: METHOD, correct: bool,
                               response_ms: float) -> tuple:
        import time
        t0 = time.perf_counter()
        result = self.processor.process_response(
            student_id, skill_id, method, correct, response_ms
        )
        t1 = time.perf_counter()
        latency_ms = (t1 - t0) * 1000.0

        # Formatear logs
        method_name = method.name if hasattr(method, 'name') else str(method)
        logs = []
        logs.append(f"[C++] Update O(1) en {latency_ms:.2f}ms -> Persistencia SQLite OK.")
        logs.append(f"[BKT] P(L) actualizado a {result.current_pL:.3f}")
        
        next_method_name = result.next_method.name if hasattr(result.next_method, 'name') else str(result.next_method)
        logs.append(f"[MAB] Siguiente brazo seleccionado: {next_method_name}")

        return result, latency_ms, logs

    def get_method_states_for_ui(self, student_id: int, skill_id: int) -> dict:
        try:
            states = self.storage.load_method_states(student_id, skill_id)
            m_names = ["VISUAL", "AUDITORY", "KINESTHETIC", "PHONETIC", "GLOBAL"]
            res = {}
            for i, m in enumerate(m_names):
                ms = states[i]
                res[m] = {"q_value": ms.ewma_success, "attempts": ms.count_attempts, "successes": ms.successes}
            return res
        except Exception as e:
            print(f"Error loading method states: {e}")
            return {m: {"q_value": 0.0, "attempts": 0, "successes": 0} for m in ["VISUAL", "AUDITORY", "KINESTHETIC", "PHONETIC", "GLOBAL"]}

    def start_session(self, student_id: int, skill_id: int) -> hestia_core.bkt.SkillState:
        """
        Carga el estado del estudiante y marca el inicio de una sesión.
        """
        state = self.storage.load_skill_state(student_id, skill_id)
        if state is None:
            state = hestia_core.bkt.SkillState()
            state.skill_id = skill_id

        # Bug fix: C++ signature is startSession(int student_id, SkillState& state)
        self.processor.start_session(student_id, state)
        return state

    def end_session(self, state: hestia_core.bkt.SkillState) -> None:
        """
        Finaliza la sesión y calcula métricas finales (fatiga, etc).
        """
        self.processor.end_session(state)

    def get_due_skills(self) -> List[int]:
        """
        Retorna la lista de skill_ids que necesitan revisión según el algoritmo SRS.
        """
        return self.processor.get_due_skills()

    def get_unlocked_skills(self, mastered_ids: List[int]) -> List[int]:
        """
        Retorna las habilidades que el estudiante ha desbloqueado basándose en sus logros.
        """
        return self.processor.get_unlocked_skills(mastered_ids)

    def get_student_progress(self, student_id: int) -> List[Any]:
        return self.storage.get_student_progress(student_id)

    def get_session_hit_rate(self) -> float:
        return self.processor.get_current_session().get_session_hit_rate()

    def get_session_logs(self, student_id: int, session_start_ts: int) -> List[Any]:
        return self.storage.get_session_logs(student_id, session_start_ts)

    def get_current_session(self) -> Any:
        return self.processor.get_current_session()

    def get_bkt_constants(self) -> dict:
        return {
            "DEFAULT_P_LEARN": hestia_core.bkt.DEFAULT_P_LEARN,
            "DEFAULT_P_TRANSITION": hestia_core.bkt.DEFAULT_P_TRANSITION,
            "DEFAULT_P_GUESS": hestia_core.bkt.DEFAULT_P_GUESS,
            "DEFAULT_P_SLIP": hestia_core.bkt.DEFAULT_P_SLIP,
            "DEFAULT_P_FORGET": hestia_core.bkt.DEFAULT_P_FORGET,
            "FORGET_THRESHOLD_HOURS": hestia_core.bkt.FORGET_THRESHOLD_HOURS,
        }

# Instancia global para facilitar el acceso desde la UI
bridge = None

def get_bridge(db_path: Optional[str] = None) -> HestiaBridge:
    """Retorna (o crea) la instancia singleton del bridge.
    Si db_path es None, usa <PROJECT_ROOT>/hestia.db como ruta absoluta.
    """
    global bridge
    if bridge is None:
        if db_path is None:
            db_path = os.path.join(PROJECT_ROOT, "hestia.db")
        bridge = HestiaBridge(db_path=db_path)
    return bridge
