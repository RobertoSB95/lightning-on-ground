# services/lightning_service.py
import logging
from data_processing import extraer_datos_respuesta, calculate_distance
from send_request import (
    consultar_posiciones_moviles_UYU,
    consultar_posiciones_moviles_ARG,
    xWeather_request
)
from firebase_service import FirebaseService
from slack_service import send_alert_to_slack_channel

logger = logging.getLogger(__name__)

class LightningService:
    """Detecta rayos cerca de vehículos detenidos y envía alertas."""

    def __init__(self, firebase: FirebaseService) -> None:
        self._firebase = firebase

    def procesar(self) -> tuple[str, int]:
        """
        Punto de entrada principal del proceso de rayos.
        Obtiene vehículos, consulta posiciones y evalúa peligro.
        """
        logger.info("Iniciando proceso de detección de rayos")

        vehiculos = self._firebase.get_data()
        if not vehiculos:
            logger.warning("No se encontraron vehículos en Firebase")
            return "No data found", 400

        vehiculos_UY  = [v for v in vehiculos if v.get("country") == "UY"]
        vehiculos_ARG = [v for v in vehiculos if v.get("country") == "ARG"]

        posiciones = self._obtener_posiciones(vehiculos_UY, vehiculos_ARG)
        if posiciones is None:
            return "No data found", 400

        return self._evaluar_posiciones(posiciones, vehiculos)

    # ── privados ──────────────────────────────────────────────────

    def _obtener_posiciones(self, vehiculos_UY, vehiculos_ARG):
        """Consulta posiciones de ambos países y las combina."""
        response_UYU = consultar_posiciones_moviles_UYU(vehiculos_UY)
        response_ARG = consultar_posiciones_moviles_ARG(vehiculos_ARG)

        if response_UYU is None or response_ARG is None:
            logger.error("Error al obtener posiciones de uno o ambos países")
            return None

        return extraer_datos_respuesta(response_UYU.text) + response_ARG

    def _evaluar_posiciones(self, posiciones: list, vehiculos: list) -> tuple[str, int]:
        """Evalúa cada vehículo y dispara alerta si hay peligro."""
        for vehiculo in posiciones:
            logger.info("Procesando vehículo %s", vehiculo["movilId"])

            if not calculate_distance(vehiculo["latitud"], vehiculo["longitud"], vehiculo["country"]):
                logger.info("Vehículo %s en base, sin riesgo", vehiculo["movilId"])
                continue

            if float(vehiculo["velocidad"]) != 0:
                logger.info("Vehículo %s en movimiento, sin riesgo", vehiculo["movilId"])
                continue

            # Vehículo detenido fuera de base — evalúa rayos
            resultado = self._evaluar_rayos(vehiculo, vehiculos)
            if resultado:
                return resultado

        return "Lightning processing done", 200

    def _evaluar_rayos(self, vehiculo: dict, vehiculos: list):
        """Consulta la API de rayos para un vehículo específico."""
        meta = next(
            (v for v in vehiculos if v["movilId"] == vehiculo["movilId"]),
            None
        )
        if not meta:
            logger.warning("No se encontró metadata para vehículo %s", vehiculo["movilId"])
            return None

        response = xWeather_request(vehiculo["latitud"], vehiculo["longitud"])
        data = response.json()

        if response.status_code != 200 or data.get("error"):
            error_code = (data.get("error") or {}).get("code", "")
            if error_code == "warn_no_data":
                logger.info("Sin rayos detectados para %s", vehiculo["movilId"])
            else:
                logger.error("Error API rayos para %s: %s", vehiculo["movilId"], data)
                return f"Error en la solicitud", 400
            return None

        if not data.get("response"):
            logger.info("Sin rayos detectados para %s", vehiculo["movilId"])
            return None

        logger.warning("PELIGRO detectado para vehículo %s", vehiculo["movilId"])
        self._enviar_alerta(vehiculo, meta)
        return None

    def _enviar_alerta(self, vehiculo: dict, meta: dict) -> None:
        """Envía alerta a Slack y guarda registro en Firebase."""
        response = send_alert_to_slack_channel(
            meta["vehicle_plate"],
            vehiculo["latitud"],
            vehiculo["longitud"],
            meta["time_zone"]
        )
        self._firebase.save_data("slack_notifications", {
            "timestamp":      response["ts"],
            "source":         "rayos",
            "latitud":        vehiculo["latitud"],
            "longitud":       vehiculo["longitud"],
            "vehicle_plate":  meta["vehicle_plate"],
            "user_confirm":   "pending"
        }, response["ts"])