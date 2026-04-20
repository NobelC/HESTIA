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

    def start_session(self, student_id: int, skill_id: int) -> hestia_core.bkt.SkillState:
        """
        Carga el estado del estudiante y marca el inicio de una sesión.
        """
        state = self.storage.load_skill_state(student_id, skill_id)
        if state is None:
            state = hestia_core.bkt.SkillState()
            state.skill_id = skill_id
            
        self.processor.start_session(state)
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

# Instancia global para facilitar el acceso desde la UI
bridge = None

def get_bridge(db_path: str = "hestia.db") -> HestiaBridge:
    global bridge
    if bridge is None:
        bridge = HestiaBridge(db_path=db_path)
    return bridge
