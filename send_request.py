# send_request.py
import logging
import httpx
from urllib.parse import unquote
from config import (
    GPS_SERVICE_ENDPOINT_UYU,
    GPS_SERVICE_USERNAME_UYU,
    GPS_SERVICE_PASSWORD_UYU,
    GPS_SERVICE_ENDPOINT_ARG,
    GPS_SERVICE_USERNAME_ARG,
    GPS_SERVICE_PASSWORD_ARG,
    CLIENT_ID,
    CLIENT_SECRET,
    TYPE_FILTER,
    RADIUS,
    LIMIT,
    LAST_TIME,
)

logger = logging.getLogger(__name__)

MAX_RETRIES = 2


# ── Uruguay ───────────────────────────────────────────────────────

async def consultar_moviles_UYU() -> httpx.Response:
    """
    Consulta la flota completa de vehículos Uruguay.

    Returns:
        Respuesta SOAP con la flota de vehículos.

    Raises:
        RuntimeError: Si la consulta falla.
    """
    soap_body = f"""
        <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:ws="http://ws.wc.web.com.ar">
            <soapenv:Header/>
            <soapenv:Body>
                <ws:consultarMovilesFlota>
                    <ws:USER>{GPS_SERVICE_USERNAME_UYU}</ws:USER>
                    <ws:pass>{GPS_SERVICE_PASSWORD_UYU}</ws:pass>
                </ws:consultarMovilesFlota>
            </soapenv:Body>
        </soapenv:Envelope>
    """
    return await _enviar_solicitud_soap(
        soap_body,
        {"Content-Type": "text/xml", "SOAPAction": "urn:consultarMovilesFlota"}
    )


async def consultar_posiciones_moviles_UYU(movildata: list) -> httpx.Response:
    """
    Consulta posiciones de vehículos Uruguay.

    Args:
        movildata: Lista de vehículos con sus movilIds.

    Returns:
        Respuesta SOAP con las posiciones.
    """
    movilIds = ",".join(m["movilId"] for m in movildata)

    soap_body = f"""
    <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:ws="http://ws.wc.web.com.ar">
       <soapenv:Header/>
       <soapenv:Body>
          <ws:consultarPosicionesMovilesUsuario>
             <ws:USER>{GPS_SERVICE_USERNAME_UYU}</ws:USER>
             <ws:pass>{GPS_SERVICE_PASSWORD_UYU}</ws:pass>
             <ws:tipo>3</ws:tipo>
             <ws:movilIds>{movilIds}</ws:movilIds>
          </ws:consultarPosicionesMovilesUsuario>
       </soapenv:Body>
    </soapenv:Envelope>
    """
    return await _enviar_solicitud_soap(
        soap_body,
        {"Content-Type": "text/xml", "SOAPAction": "urn:consultarPosicionesMovilesUsuario"}
    )


async def _enviar_solicitud_soap(soap_body: str, headers: dict) -> httpx.Response:
    """
    Envía una solicitud SOAP al servicio GPS Uruguay.

    Raises:
        RuntimeError: Si la solicitud falla.
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                GPS_SERVICE_ENDPOINT_UYU,
                content=soap_body,
                headers=headers
            )
            response.raise_for_status()
            return response

    except httpx.HTTPError as e:
        logger.error("Error en solicitud SOAP a Uruguay: %s", e)
        raise RuntimeError("Error consultando GPS Uruguay") from e


# ── Argentina ─────────────────────────────────────────────────────

async def consultar_moviles_ARG() -> list:
    """
    Consulta la flota completa de vehículos Argentina.

    Returns:
        Lista de vehículos con sus datos básicos.
    """
    payload = {
        "user":   GPS_SERVICE_USERNAME_ARG,
        "pwd":    GPS_SERVICE_PASSWORD_ARG,
        "action": "DATOSACTUALES",
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                GPS_SERVICE_ENDPOINT_ARG,
                headers={"Content-Type": "application/json"},
                json=payload
            )
            response.raise_for_status()

        vehiculos = []
        for data in response.json():
            for key in data:
                if isinstance(data[key], str):
                    data[key] = unquote(data[key])
            vehiculos.append({
                "movilId":       data["id"],
                "vehicle_plate": data["patente"],
                "nombre":        data["nombre"],
                "time_zone":     "America/Buenos_Aires",
                "country":       "ARG",
            })

        logger.info("Vehículos ARG obtenidos: %d", len(vehiculos))
        return vehiculos

    except httpx.HTTPError as e:
        logger.error("Error consultando flota Argentina: %s", e)
        raise RuntimeError("Error consultando GPS Argentina") from e


async def consultar_posiciones_moviles_ARG(movildata: list) -> list:
    """
    Consulta posiciones de vehículos Argentina.

    Args:
        movildata: Lista de vehículos con sus movilIds.

    Returns:
        Lista de posiciones actuales.
    """
    movilIds = [m["movilId"] for m in movildata]

    payload = {
        "user":      GPS_SERVICE_USERNAME_ARG,
        "pwd":       GPS_SERVICE_PASSWORD_ARG,
        "action":    "DATOSACTUALES",
        "vehiculos": movilIds,
        "tipoID":    "id",
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                GPS_SERVICE_ENDPOINT_ARG,
                headers={"Content-Type": "application/json"},
                json=payload
            )
            response.raise_for_status()

        vehiculos = []
        for data in response.json():
            vehiculos.append({
                "movilId":           data.get("id"),
                "latitud":           float(data.get("latitud", 0)),
                "longitud":          float(data.get("longitud", 0)),
                "velocidad":         float(data.get("velocidad", 0)),
                "fecha":             unquote(data.get("fecha", "")),
                "nombre":            unquote(data.get("nombre", "")),
                "patente":           data.get("patente"),
                "evento":            data.get("evento"),
                "parking_activado":  unquote(data.get("parking_activado", "")),
                "parking_distancia": data.get("parking_distancia", ""),
                "time_zone":         "America/Buenos_Aires",
                "country":           "ARG",
            })

        logger.info("Posiciones ARG obtenidas: %d", len(vehiculos))
        return vehiculos

    except httpx.HTTPError as e:
        logger.error("Error consultando posiciones Argentina: %s", e)
        raise RuntimeError("Error consultando posiciones GPS Argentina") from e


# ── XWeather ──────────────────────────────────────────────────────

async def xWeather_request(latitud: float, longitud: float) -> httpx.Response:
    """
    Consulta la API de rayos para una ubicación.

    Args:
        latitud:  Latitud del punto a consultar.
        longitud: Longitud del punto a consultar.

    Returns:
        Respuesta HTTP de la API XWeather.

    Raises:
        RuntimeError: Si la consulta falla después de los reintentos.
    """
    url = (
        f"https://data.api.xweather.com/lightning/{latitud},{longitud}"
        f"?format=json&filter={TYPE_FILTER}&radius={RADIUS}"
        f"&from={LAST_TIME}&limit={LIMIT}"
        f"&fields=id,ob,loc,recISO"
        f"&client_id={CLIENT_ID}&client_secret={CLIENT_SECRET}"
    )

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url)
                response.raise_for_status()
                return response

        except httpx.HTTPError as e:
            logger.warning(
                "Intento %d/%d fallido para XWeather [%.4f, %.4f]: %s",
                attempt, MAX_RETRIES, latitud, longitud, e
            )
            if attempt == MAX_RETRIES:
                logger.error("XWeather falló después de %d intentos", MAX_RETRIES)
                raise RuntimeError("Error consultando API de rayos") from e

    raise RuntimeError("XWeather no pudo ejecutarse — MAX_RETRIES inválido")