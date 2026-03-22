# slack_service.py
import logging
from typing import Optional
import pytz
from datetime import datetime
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from config import TOKEN_SLACK, CHANNEL_SLACK, USERS_SLACK, RADIUS

logger = logging.getLogger(__name__)

MAX_RETRIES = 2


def send_alert_to_slack_channel(
    vehicle_id: str,
    latitud: float,
    longitud: float,
    time_zone: str
) -> dict:
    """
    Envía alerta de rayos a canal Slack.

    Args:
        vehicle_id: Patente del vehículo.
        latitud:    Latitud del vehículo.
        longitud:   Longitud del vehículo.
        time_zone:  Zona horaria para mostrar la hora.

    Returns:
        Diccionario con los datos de la respuesta de Slack — siempre incluye 'ts'.

    Raises:
        RuntimeError: Si no se pudo enviar después de los reintentos.
    """
    latitud_str  = f"{latitud:.4f}"
    longitud_str = f"{longitud:.4f}"

    timezone  = pytz.timezone(time_zone)
    now_str   = datetime.now(timezone).strftime("%d-%m-%Y %H:%M")
    if time_zone == "America/Montevideo":
        now_str += " (UYU)"

    client = WebClient(token=TOKEN_SLACK)
    blocks = _construir_bloques_alerta(vehicle_id, latitud_str, longitud_str, now_str, time_zone)

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = client.chat_postMessage(
                channel=CHANNEL_SLACK,
                blocks=blocks,
            )
            logger.info("Alerta enviada a Slack para vehículo %s — ts: %s", vehicle_id, response["ts"])
            return dict(response.data) #type: ignore

        except SlackApiError as e:
            logger.warning(
                "Intento %d/%d fallido enviando alerta [%s]: %s",
                attempt, MAX_RETRIES, vehicle_id, e.response["error"]
            )
            if attempt == MAX_RETRIES:
                _enviar_warning(f"No se logró notificar a {vehicle_id}")
                raise RuntimeError(f"Error enviando alerta Slack para {vehicle_id}") from e

    raise RuntimeError("send_alert_to_slack_channel no pudo ejecutarse")


def update_message_slack(answer_form: dict, time_zone: str) -> str:
    """
    Actualiza el mensaje de alerta con la confirmación del usuario.

    Args:
        answer_form: Payload del formulario de Slack.
        time_zone:   Zona horaria para mostrar la hora de confirmación.

    Returns:
        Nombre real del usuario que confirmó.

    Raises:
        RuntimeError: Si no se pudo actualizar después de los reintentos.
    """
    client  = WebClient(token=TOKEN_SLACK)
    user_id = answer_form["user"]["id"]

    timezone = pytz.timezone(time_zone)
    now_str  = datetime.now(timezone).strftime("%d-%m-%Y %H:%M")
    if time_zone == "America/Montevideo":
        now_str += " (UYU)"
            
    user_info = client.users_info(user=user_id)["user"]
    if user_info is None:
        raise RuntimeError(f"No se encontró información del usuario {user_id}")
    user_name = user_info["real_name"]

    blocks = list(answer_form["message"]["blocks"])
    blocks[-3] = {
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": f":large_green_circle: *{user_name}* confirmó a las {now_str}."
        }
    }

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            client.chat_update(
                channel=CHANNEL_SLACK,
                ts=answer_form["container"]["message_ts"],
                blocks=blocks,
            )
            logger.info("Mensaje actualizado por %s", user_name)
            return user_name

        except SlackApiError as e:
            logger.warning(
                "Intento %d/%d fallido actualizando mensaje [%s]: %s",
                attempt, MAX_RETRIES, user_name, e.response["error"]
            )
            if attempt == MAX_RETRIES:
                _enviar_warning(f"No se logró actualizar mensaje de {user_name}")
                raise RuntimeError(f"Error actualizando mensaje Slack de {user_name}") from e

    raise RuntimeError("update_message_slack no pudo ejecutarse")


def _enviar_warning(mensaje: str) -> None:
    """
    Notifica a los usuarios de la lista USERS_SLACK sobre un fallo.

    Args:
        mensaje: Descripción del fallo.
    """
    client = WebClient(token=TOKEN_SLACK)
    for user_id in USERS_SLACK:
        try:
            client.chat_postMessage(channel=user_id, text=mensaje)
            logger.info("Warning enviado a %s", user_id)
        except SlackApiError as e:
            logger.error("No se pudo enviar warning a %s: %s", user_id, e.response["error"])


def _construir_bloques_alerta(
    vehicle_id: str,
    latitud: str,
    longitud: str,
    now_str: str,
    time_zone: str
) -> list:
    """
    Construye los bloques del mensaje de alerta Slack.

    Args:
        vehicle_id: Patente del vehículo.
        latitud:    Latitud formateada.
        longitud:   Longitud formateada.
        now_str:    Fecha y hora formateada.
        time_zone:  Zona horaria del vehículo.

    Returns:
        Lista de bloques para la API de Slack.
    """
    return [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": ":rotating_light: Nueva amenaza de rayos :lightning_cloud:"}
        },
        {
            "type": "context",
            "elements": [{"type": "mrkdwn", "text": "_Alerta de seguridad en terreno_"}]
        },
        {"type": "divider"},
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f":pickup_truck: *vehículo:*\n{vehicle_id}"},
                {"type": "mrkdwn", "text": f":clock2: *fecha - hora:*\n{now_str}"},
            ]
        },
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f":straight_ruler: *radio alerta:*\n{RADIUS}"},
                {"type": "mrkdwn", "text": f":round_pushpin: *coordenadas (lat, lon):*\n{latitud}, {longitud}"},
            ]
        },
        {"type": "divider"},
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": "*_Pasos a seguir:_*\n"}
        },
        {
            "type": "rich_text",
            "elements": [{
                "type": "rich_text_list",
                "style": "ordered",
                "indent": 0,
                "border": 0,
                "elements": [
                    {"type": "rich_text_section", "elements": [{"type": "text", "text": "Notifica a tus compañeros en terreno del peligro de rayos."}]},
                    {"type": "rich_text_section", "elements": [{"type": "text", "text": "Aléjate de objetos metálicos o estructuras altas."}]},
                    {"type": "rich_text_section", "elements": [{"type": "text", "text": "Ingrese al vehículo inmediatamente."}]},
                    {"type": "rich_text_section", "elements": [{"type": "text", "text": "No salgas del vehículo durante al menos 30 minutos."}]},
                ]
            }]
        },
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": ":warning: Si vuelve a recibir este mensaje, *permanece dentro del vehículo* por 30 minutos más."}
        },
        {"type": "divider"},
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": "*_Confirma que el equipo se encuentra dentro del vehículo:_*\n"}
        },
        {
            "type": "actions",
            "elements": [{
                "type": "button",
                "text": {"type": "plain_text", "text": "Confirmar", "emoji": True},
                "style": "primary",
                "value": time_zone,
                "action_id": "CONFIRM"
            }]
        },
        {
            "type": "context",
            "elements": [{"type": "mrkdwn", "text": "_Nota_: Seguimiento continuo de rayos para proteger al equipo en terreno."}]
        },
        {"type": "divider"},
    ]