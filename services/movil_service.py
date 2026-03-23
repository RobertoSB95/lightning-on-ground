# services/movil_service.py
import asyncio
import logging
from send_request import consultar_moviles_UYU, consultar_moviles_ARG
from data_processing import extract_movilIDs_UYU
from firebase_service import FirebaseService

logger = logging.getLogger(__name__)


class MovilService:
    """Sincroniza la flota de vehículos desde las APIs GPS hacia Firebase."""

    def __init__(self, firebase: FirebaseService) -> None:
        self._firebase = firebase

    async def sincronizar(self) -> tuple[str, int]:
        """
        Obtiene vehículos de UY y ARG en paralelo y los guarda en Firebase.
        Antes: secuencial — ahora: ambas consultas simultáneas.
        """
        logger.info("Sincronizando flota de vehículos")

        # consultar ambos países en paralelo
        response_UYU, moviles_ARG = await asyncio.gather(
            consultar_moviles_UYU(),
            consultar_moviles_ARG(),
        )

        moviles_UY = extract_movilIDs_UYU(response_UYU)
        todos      = moviles_UY + moviles_ARG

        for movil in todos:
            self._firebase.save_data("target_vehicles", movil, movil["movilId"])

        logger.info("Sincronización completa: %d vehículos", len(todos))
        return "Movil processing done", 200