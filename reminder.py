import os
import sys
import json
from datetime import datetime, timedelta, timezone


# Required variables in .env file
# CANVAS_URL url of your canvas 
# CANVAS_API_KEY Canvas API access token
# NTFY_TOPIC ntfy topic for notifications

CANVAS_URL = os.environ["CANVAS_URL"].rstrip("/")
CANVAS_TOKEN = os.environ["CANVAS_TOKEN"]
NTFY_TOPIC = os.environ["NTFY_TOPIC"]
NTFY_SERVER = os.environ.get("NTFY_SERVER", "https://ntfy.sh").rstrip("/")
FREQUENCY = float(os.environ.get("LOOKAHEAD_HOURS", "24"))
 
STATE_FILE = os.path.join(os.path.dirname(__file__), "notified_state.json")

HEADERS = {"Authorization": f"Bearer {CANVAS_TOKEN}"}

