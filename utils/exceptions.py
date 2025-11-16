"""
Custom exceptions for the Joke API client.

This module defines a hierarchy of custom exceptions used throughout the
joke service integration, providing clear error handling and meaningful
error messages.
"""


class JokeAPIError(Exception):
    """
    Base exception for all Joke API related errors.

    This serves as the parent class for all custom exceptions in the
    joke service integration, allowing for broad exception handling when needed.
    """

    def __init__(self, message: str, status_code: int | None = None):
        """
        Initialize the JokeAPIError.

        :param message: Human-readable error message
        :param status_code: Optional HTTP status code associated with the error
        """
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class JokeAPITimeoutError(JokeAPIError):
    """
    Raised when a request to the Joke API times out.

    This exception indicates that the joke service did not respond
    within the expected time frame.
    """

    def __init__(
        self, message: str = "Tiempo de espera excedido al conectar con el servicio de Jokes"
    ):
        super().__init__(message)


class JokeAPIConnectionError(JokeAPIError):
    """
    Raised when there's a connection failure to the Joke API.

    This exception indicates network-level issues preventing
    communication with the joke service.
    """

    def __init__(self, message: str = "Error de conexión con el servicio de Jokes"):
        super().__init__(message)


class JokeAPIHTTPError(JokeAPIError):
    """
    Raised when the Joke API returns a non-200 HTTP status code.

    This exception indicates that the joke service responded with an
    error status, such as 404 (Not Found) or 500 (Internal Server Error).
    """

    def __init__(self, message: str, status_code: int, response_text: str = ""):
        """
        Initialize the JokeAPIHTTPError.

        :param message: Human-readable error message
        :param status_code: HTTP status code returned by the API
        :param response_text: Optional response body text for debugging
        """
        super().__init__(message, status_code)
        self.response_text = response_text


class JokeAPIParseError(JokeAPIError):
    """
    Raised when the API response cannot be parsed correctly.

    This exception indicates that the joke service returned data
    in an unexpected format or structure.
    """

    def __init__(self, message: str = "Error al parsear la respuesta del servicio de Jokes"):
        super().__init__(message)
