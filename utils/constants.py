from typing import Literal

from utils.config import Settings


URL = Settings.API_BASE_URL
JOKE_TYPES = Literal["general", "knock-knock", "programming", "dad"]
CONSISTENT_JOKE = "What's brown and sticky?\nA stick! Ha ha ha ha"
