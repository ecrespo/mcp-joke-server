import httpx
from typing import  Annotated
from pydantic import Field

from utils.model import Joke, Jokes
from utils.logger import log
from utils.constants import URL, JOKE_TYPES




def get_joke()-> Joke:
    """
    Fetches a random joke from a designated jokes service.

    This function utilizes an HTTP GET request to retrieve a random joke in JSON
    format from the configured jokes service endpoint. It processes the received
    data and returns it as an instance of the Joke class. If there are any
    connection issues or the service returns an error, the function manages the
    exceptions appropriately.

    :raises TimeoutError: If the request to the jokes service exceeds the allowed
                          time limit.
    :raises ConnectionError: If there is a failure to connect to the jokes service.
    :raises BaseException: If the jokes service responds with a non-success status
                           code (not 200).
    :returns: An instance of the Joke class containing the retrieved joke data.
    :rtype: Joke
    """
    url_joke = URL + "/random_joke"
    try:
        response = httpx.get(url_joke)
    except httpx.ReadTimeout:
        raise TimeoutError(detail="Tiempo de espera excedido")
    except httpx.ConnectError:
        raise ConnectionError(detail="Error de conexión con el servicio de Jokes")

    if response.status_code != 200:
        log.error(response.text)
        raise BaseException(detail="Error al obtener la información del Jokes")

    resp = response.json()

    joke = Joke(**resp)
    return joke


def get_ten_jokes()-> Jokes:
    """
    Fetches a list containing ten jokes from an external service.

    This function retrieves ten random jokes by making a GET request to an external
    joke service. It raises appropriate errors in case of issues like timeout or connection
    failures. If the response is successful, it parses the response JSON into a `Jokes`
    object and returns it. In case of a non-200 response status code, it logs the error and
    raises a generic exception.

    :raises TimeoutError: If the request to the service exceeds the time limit.
    :raises ConnectionError: If there is an issue connecting to the joke service.
    :raises BaseException: If the returned status code is not 200, signaling a failure
        to retrieve the jokes.
    :return: A `Jokes` object containing ten random jokes.
    :rtype: Jokes
    """
    url_joke = URL + "/random_ten"
    try:
        response = httpx.get(url_joke)
    except httpx.ReadTimeout:
        raise TimeoutError(detail="Tiempo de espera excedido")
    except httpx.ConnectError:
        raise ConnectionError(detail="Error de conexión con el servicio de Jokes")

    if response.status_code != 200:
        log.error(response.text)
        raise BaseException(detail="Error al obtener la información del Jokes")

    resp = response.json()

    jokes = Jokes(*resp)
    return jokes



def get_joke_by_id(joke_id: Annotated[int, Field(ge=1, le=451)])-> Joke:
    """
    Fetches a joke from the Jokes service using the specified joke ID.

    The function communicates with an external API to fetch a joke resource
    based on the provided joke ID. It validates the ID input and handles
    possible errors that may occur during the request process, returning
    a Joke object if the operation is successful.

    :param joke_id: The ID of the joke to be fetched. Should be an integer between 1 and 451 inclusive.
    :type joke_id: int
    :return: An instance of the Joke data class containing the joke's details.
    :rtype: Joke
    :raises TimeoutError: If the request to the Jokes service exceeds the allowed response time.
    :raises ConnectionError: If there is a connection issue when attempting to reach the Jokes service.
    :raises BaseException: If the API response is not successful or contains an error.
    """
    url_joke = URL + f"/jokes/{joke_id}"
    try:
        response = httpx.get(url_joke)
    except httpx.ReadTimeout:
        raise TimeoutError(detail="Tiempo de espera excedido")
    except httpx.ConnectError:
        raise ConnectionError(detail="Error de conexión con el servicio de Jokes")

    if response.status_code != 200:
        log.error(response.text)
        raise BaseException(detail="Error al obtener la información del Jokes")

    resp = response.json()

    joke = Joke(**resp)
    return joke



def get_jokes_by_type(joke_type:JOKE_TYPES)-> Jokes:
    """
    Fetches a random joke of the specified type from the joke service.

    This function sends a GET request to retrieve a random joke based on the provided
    joke type. If the joke service is unavailable or there are network issues, appropriate
    errors are raised. If the service responds with an unsuccessful status code, a general
    exception is raised.

    :param joke_type: The type of joke to fetch (e.g., general, programming, etc.)
    :type joke_type: JOKE_TYPES
    :return: A `Jokes` object containing the joke data.
    :rtype: Jokes
    :raises TimeoutError: If the request to the joke service times out.
    :raises ConnectionError: If unable to connect to the joke service.
    :raises BaseException: If the joke service responds with any error status.
    """
    url_joke = URL + f"/jokes/{joke_type}/random"
    try:
        response = httpx.get(url_joke)
    except httpx.ReadTimeout:
        raise TimeoutError(detail="Tiempo de espera excedido")
    except httpx.ConnectError:
        raise ConnectionError(detail="Error de conexión con el servicio de Jokes")

    if response.status_code != 200:
        log.error(response.text)
        raise BaseException(detail="Error al obtener la información del Jokes")

    resp = response.json()

    jokes = Jokes(*resp)
    return jokes
