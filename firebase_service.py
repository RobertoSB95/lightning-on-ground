# firebase_service.py
import logging
from datetime import datetime
from google.cloud import firestore
from typing import Optional

logger = logging.getLogger(__name__)


class FirebaseService:
    """Gestiona el acceso a Firestore para el sistema de alertas."""

    MAIN_COLLECTION = "thunderstorm_tracking"

    def __init__(self) -> None:
        self._db = firestore.Client()

    def save_data(self, collection: str, data: dict, id: Optional[str] = None) -> None:
        """
        Guarda un documento en Firestore.

        Args:
            collection: Nombre de la subcolección.
            data: Datos a guardar.
            id: ID del documento. Si es None se usa el timestamp actual.
        """
        doc_id = id if id else str(datetime.now().timestamp())

        try:
            self._db \
                .collection(self.MAIN_COLLECTION) \
                .document("data") \
                .collection(collection) \
                .document(doc_id) \
                .set(data)
            logger.info("Documento guardado en %s/%s", collection, doc_id)

        except Exception as e:
            logger.error("Error guardando en Firestore [%s/%s]: %s", collection, doc_id, e)
            raise

    def get_data(self) -> list:
        """
        Obtiene los vehículos objetivo desde Firestore.

        Returns:
            Lista de vehículos. Lista vacía si no hay datos.

        Raises:
            RuntimeError: Si Firestore no está disponible.
        """
        try:
            docs = self._db \
                .collection(self.MAIN_COLLECTION) \
                .document("data") \
                .collection("target_vehicles") \
                .get()

            data = [doc.to_dict() for doc in docs]
            logger.info("Vehículos obtenidos desde Firestore: %d", len(data))
            return data

        except Exception as e:
            logger.error("Error obteniendo vehículos desde Firestore: %s", e)
            raise RuntimeError("No se pudo conectar a Firestore") from e

    def update_data(self, answer_form: dict, user: str) -> None:
        """
        Registra la confirmación del usuario en la notificación de Slack.

        Args:
            answer_form: Payload del formulario de Slack.
            user: Nombre del usuario que confirmó.
        """
        doc_id = answer_form["container"]["message_ts"]

        try:
            self._db \
                .collection(self.MAIN_COLLECTION) \
                .document("data") \
                .collection("slack_notifications") \
                .document(doc_id) \
                .update({"user_confirm": user})
            logger.info("Confirmación registrada por %s en documento %s", user, doc_id)

        except Exception as e:
            logger.error("Error actualizando confirmación [%s]: %s", doc_id, e)
            raise