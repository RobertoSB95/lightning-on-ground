# main.py
import json
import asyncio
import logging
from firebase_service import FirebaseService
from services.lightning_service import LightningService
from services.movil_service import MovilService
from slack_service import update_message_slack

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main(request):
    '''Punto de entrada para la función Cloud.'''
    firebase = FirebaseService()

    if request.content_type == "application/json":
        return _handle_json(request.get_json(), firebase)

    if request.content_type == "application/x-www-form-urlencoded":
        return _handle_slack_form(request.form.to_dict(), firebase)

    logger.warning("Content-type no soportado: %s", request.content_type)
    return "No content type found", 400


def _handle_json(body: dict, firebase: FirebaseService) -> tuple:
    '''Maneja las solicitudes JSON para tareas de rayos y móviles.'''
    task = body.get("task")
    logger.info("Tarea recibida: %s", task)

    if task == "lightning":
        return asyncio.run(LightningService(firebase).procesar())

    if task == "movil":
        return asyncio.run(MovilService(firebase).sincronizar())

    logger.warning("Tarea desconocida: %s", task)
    return "No task found", 400


def _handle_slack_form(form: dict, firebase: FirebaseService) -> tuple:
    '''Maneja las solicitudes de formularios de Slack.'''
    if "payload" not in form:
        return "No payload found", 400

    answer = json.loads(form["payload"])
    action = (answer.get("actions") or [{}])[0].get("action_id")

    if action == "CONFIRM":
        time_zone = answer["actions"][0]["value"]
        user = update_message_slack(answer, time_zone)
        firebase.update_data(answer, user)
        logger.info("Confirmación recibida de %s", user)

    return "Data processing done", 200