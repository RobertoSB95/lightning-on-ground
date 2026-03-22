# services/movil_service.py
import logging
from send_request import consultar_moviles_UYU, consultar_moviles_ARG
from data_processing import extract_movilIDs_UYU
from firebase_service import FirebaseService

logger = logging.getLogger(__name__)

class MovilService:
    """Sincroniza la flota de vehículos desde las APIs GPS hacia Firebase."""

    def __init__(self, firebase: FirebaseService) -> None:
        self._firebase = firebase

    def sincronizar(self) -> tuple[str, int]:
        """Obtiene vehículos de UY y ARG y los guarda en Firebase."""
        logger.info("Sincronizando flota de vehículos")

        moviles_UY  = extract_movilIDs_UYU(consultar_moviles_UYU())
        moviles_ARG = consultar_moviles_ARG()
        todos       = moviles_UY + moviles_ARG

        for movil in todos:
            self._firebase.save_data("target_vehicles", movil, movil["movilId"])

        logger.info("Sincronización completa: %d vehículos", len(todos))
        return "Movil processing done", 200