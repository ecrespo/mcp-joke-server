from enum import Enum

from utils.config import Settings

URL = Settings.API_BASE_URL


class JokeType(Enum):
    GENERAL = "general"
    KNOCK_KNOCK = "knock-knock"
    PROGRAMMING = "programming"
    DAD = "dad"


# Mantener el nombre público para anotaciones existentes
JOKE_TYPES = JokeType


def joke_type_value(joke_type: "JokeType | str") -> str:
    """
    Devuelve el valor de cadena para un tipo de chiste, aceptando tanto Enum como str.

    :param joke_type: Tipo de chiste como Enum JokeType o cadena.
    :return: Representación de cadena del tipo.
    """
    return joke_type.value if isinstance(joke_type, JokeType) else str(joke_type)


CONSISTENT_JOKE = "What's brown and sticky?\nA stick! Ha ha ha ha"
