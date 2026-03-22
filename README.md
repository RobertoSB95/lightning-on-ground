 
# Lightning on Ground — Sistema de alertas de rayos

Sistema de detección de rayos para flotas de vehículos en Uruguay y Argentina.
Consulta APIs GPS en tiempo real, detecta tormentas eléctricas cercanas mediante
XWeather API y envía alertas automáticas a Slack cuando un vehículo está detenido
en zona de peligro.

## ¿Qué hace?

- Consulta posiciones de vehículos desde APIs GPS (Uruguay SOAP, Argentina REST)
- Detecta si el vehículo está fuera de su base y detenido
- Consulta la API XWeather para detectar rayos en un radio de 15km
- Envía alerta a canal Slack con instrucciones de seguridad
- Registra confirmaciones del equipo en terreno
- Persiste todo el historial en Firestore (GCP)

## Arquitectura
```
main.py                        # Entry point — Cloud Function GCP
├── services/
│   ├── lightning_service.py   # Lógica de detección y alertas
│   └── movil_service.py       # Sincronización de flota
├── firebase_service.py        # Acceso a Firestore
├── send_request.py            # Clientes GPS y XWeather
├── slack_service.py           # Notificaciones Slack
├── data_processing.py         # Procesamiento XML y cálculos
└── config.py                  # Configuración desde variables de entorno
```

El proyecto aplica arquitectura por capas con separación de responsabilidades —
cada módulo tiene una única función y las dependencias fluyen en una sola dirección.

## Stack técnico

- **Python 3.10**
- **Google Cloud Functions** — serverless deployment
- **Firestore** — persistencia NoSQL
- **Slack SDK** — notificaciones y confirmaciones interactivas
- **XWeather API** — detección de rayos
- **Pytest** — tests unitarios

## Configuración

1. Clona el repositorio
2. Crea el entorno virtual e instala dependencias:
```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
source .venv/bin/activate     # Linux/Mac
pip install -r requirements.txt
```

3. Copia `.env.example` como `.env` y completa las variables:
```bash
cp .env.example .env
```

4. Configura tus credenciales en `.env`:
```bash
GPS_SERVICE_ENDPOINT_UYU=...
GPS_SERVICE_USERNAME_UYU=...
GPS_SERVICE_PASSWORD_UYU=...

GPS_SERVICE_ENDPOINT_ARG=...
GPS_SERVICE_USERNAME_ARG=...
GPS_SERVICE_PASSWORD_ARG=...

XWEATHER_CLIENT_ID=...
XWEATHER_CLIENT_SECRET=...

TOKEN_SLACK=...
CHANNEL_SLACK=...
USERS_SLACK=...
```

## Tests
```bash
pytest tests/ -v
```

## Despliegue en GCP

El proyecto está diseñado para correr como Cloud Function en GCP.
La función `main` recibe requests HTTP y procesa dos tipos de tareas:

- `POST /` con `{"task": "lightning"}` — ejecuta detección de rayos
- `POST /` con `{"task": "movil"}` — sincroniza flota de vehículos
- `POST /` con form data — procesa confirmaciones desde Slack

## Autor

Roberto Sánchez Belmar — [linkedin.com/in/robertoasanchez95](https://linkedin.com/in/robertoasanchez95)