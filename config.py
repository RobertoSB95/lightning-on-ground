# config.py
import os
from dotenv import load_dotenv

load_dotenv()  # carga el .env automáticamente

# GPS Uruguay
GPS_SERVICE_ENDPOINT_UYU = os.environ["GPS_SERVICE_ENDPOINT_UYU"]
GPS_SERVICE_USERNAME_UYU = os.environ["GPS_SERVICE_USERNAME_UYU"]
GPS_SERVICE_PASSWORD_UYU = os.environ["GPS_SERVICE_PASSWORD_UYU"]

# GPS Argentina
GPS_SERVICE_ENDPOINT_ARG = os.environ["GPS_SERVICE_ENDPOINT_ARG"]
GPS_SERVICE_USERNAME_ARG = os.environ["GPS_SERVICE_USERNAME_ARG"]
GPS_SERVICE_PASSWORD_ARG = os.environ["GPS_SERVICE_PASSWORD_ARG"]

# XWeather
CLIENT_ID      = os.environ["XWEATHER_CLIENT_ID"]
CLIENT_SECRET  = os.environ["XWEATHER_CLIENT_SECRET"]
RADIUS         = os.environ.get("XWEATHER_RADIUS", "15km")
TYPE_FILTER    = os.environ.get("XWEATHER_TYPE_FILTER", "cg")
LIMIT          = os.environ.get("XWEATHER_LIMIT", "100")
LAST_TIME      = os.environ.get("XWEATHER_LAST_TIME", "-5minutes")

# Slack
TOKEN_SLACK   = os.environ["TOKEN_SLACK"]
CHANNEL_SLACK = os.environ["CHANNEL_SLACK"]
USERS_SLACK   = os.environ["USERS_SLACK"].split(",")