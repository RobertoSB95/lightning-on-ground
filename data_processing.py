# data_processing.py
import logging
import xml.etree.ElementTree as ET
from math import sin, cos, sqrt, atan2, radians
from typing import Optional

logger = logging.getLogger(__name__)

# Coordenadas de las bases por país
BASE_COORDINATES = {
    "UY":  {"lat": -33.38056, "lon": -56.52361},
    "ARG": {"lat": -28.43817, "lon": -56.08829},
}

DISTANCIA_MINIMA_KM = 10.0
RADIO_TIERRA_KM     = 6371.0

NAMESPACES = {
    "soapenv": "http://schemas.xmlsoap.org/soap/envelope/",
    "ns":      "http://ws.wc.web.com.ar",
    "ax21":    "http://response.bean.ws.wc.web.com.ar/xsd",
}


def extract_movilIDs_UYU(response) -> list:
    """
    Extrae los movilIds y patentes de la respuesta de consulta de móviles Uruguay.

    Args:
        response: Respuesta HTTP de la consulta SOAP.

    Returns:
        Lista de diccionarios con datos de cada vehículo.
    """
    datos_vehiculos = []
    root = ET.fromstring(response.text)

    for movil in root.findall(".//ns:return", namespaces=NAMESPACES):
        movil_id = movil.find("ax21:movilId", namespaces=NAMESPACES)
        patente   = movil.find("ax21:patente", namespaces=NAMESPACES)

        if movil_id is not None and patente is not None:
            datos_vehiculos.append({
                "movilId":       movil_id.text,
                "vehicle_plate": patente.text,
                "time_zone":     "America/Montevideo",
                "country":       "UY",
            })

    if not datos_vehiculos:
        logger.warning("No se encontraron móviles en la respuesta UYU")

    logger.info("Móviles UYU extraídos: %d", len(datos_vehiculos))
    return datos_vehiculos


def extraer_datos_respuesta(xml_string: str) -> list:
    """
    Extrae posiciones de los móviles desde la respuesta XML Uruguay.

    Args:
        xml_string: Respuesta XML de la consulta de posiciones.

    Returns:
        Lista de diccionarios con posición y estado de cada vehículo.
    """
    root      = ET.fromstring(xml_string)
    respuestas = root.findall(".//ns:return", NAMESPACES)
    resultados = []

    for movil in respuestas:
        def campo(tag, tipo="str"):
            elemento = movil.find(f"ax21:{tag}", NAMESPACES)
            return normalizar_dato(elemento.text if elemento is not None else None, tipo)

        resultados.append({
            "movilId":          campo("movilId"),
            "latitud":          campo("latitud",          "float"),
            "longitud":         campo("longitud",         "float"),
            "fechaMensaje":     campo("fechaMensaje"),
            "velocidad":        campo("velocidad",        "int"),
            "bateriaPrincipal": campo("bateriaPrincipal", "float"),
            "bateriaSecundaria":campo("bateriaSecundaria","float"),
            "contacto":         campo("contacto"),
            "digitales":        campo("digitales",        "int"),
            "sentido":          campo("sentido",          "int"),
            "odometroTotal":    campo("odometroTotal",    "int"),
            "rpm":              campo("rpm",              "int"),
            "temperaturaMotor": campo("temperaturaMotor", "int"),
            "country":          "UY",
        })

    logger.info("Posiciones UYU extraídas: %d", len(resultados))
    return resultados


def normalizar_dato(dato: Optional[str], tipo: str = "str"):
    """
    Convierte un dato string al tipo especificado.

    Args:
        dato: Valor a convertir. Puede ser None o string vacío.
        tipo: Tipo destino — 'str', 'int' o 'float'.

    Returns:
        Valor convertido o None si el dato es vacío.
    """
    if dato is None or dato.strip() == "":
        return None
    if tipo == "int":
        return int(dato)
    if tipo == "float":
        return float(dato)
    return dato


def calculate_distance(lat1: float, lon1: float, country: str) -> bool:
    """
    Determina si un vehículo está lejos de su base.

    Args:
        lat1:    Latitud actual del vehículo.
        lon1:    Longitud actual del vehículo.
        country: Código de país para determinar la base ('UY' o 'ARG').

    Returns:
        True si el vehículo está a más de 10 km de la base.

    Raises:
        ValueError: Si el país no está configurado en BASE_COORDINATES.
    """
    if country not in BASE_COORDINATES:
        raise ValueError(f"País no soportado: {country}")

    base = BASE_COORDINATES[country]

    lat1_r = radians(lat1)
    lon1_r = radians(lon1)
    lat2_r = radians(base["lat"])
    lon2_r = radians(base["lon"])

    dlat = lat2_r - lat1_r
    dlon = lon2_r - lon1_r

    a        = sin(dlat / 2) ** 2 + cos(lat1_r) * cos(lat2_r) * sin(dlon / 2) ** 2
    distancia = RADIO_TIERRA_KM * 2 * atan2(sqrt(a), sqrt(1 - a))

    logger.debug("Distancia a base %s: %.2f km", country, distancia)
    return distancia >= DISTANCIA_MINIMA_KM