from dataclasses import dataclass


@dataclass(frozen=True)
class Joke:
    """
    Represents a Joke with its type, setup, punchline, and identifier.

    This class is used to encapsulate the details of a joke, including its type,
    setup, punchline, and a unique identifier. It helps in organizing jokes clearly
    and can be extended or used in applications where joke manipulation or structuring
    is required.

    :ivar type: The category or type of the joke.
    :type type: str
    :ivar setup: The setup or initial part of the joke.
    :type setup: str
    :ivar punchline: The concluding or humorous part of the joke.
    :type punchline: str
    :ivar id: A unique identifier for the joke.
    :type id: int
    """

    type: str
    setup: str
    punchline: str
    id: int

    # Getters y utilidades
    def get_type(self) -> str:
        """Devuelve el tipo de chiste."""
        return self.type

    def get_setup(self) -> str:
        """Devuelve el enunciado (setup) del chiste."""
        return self.setup

    def get_punchline(self) -> str:
        """Devuelve el remate (punchline) del chiste."""
        return self.punchline

    def get_id(self) -> int:
        """Devuelve el identificador del chiste."""
        return self.id

    def to_dict(self) -> dict:
        """
        Representación en diccionario del dataclass, evitando el uso de `__dict__`.

        :return: Diccionario con las claves `type`, `setup`, `punchline`, `id`.
        """
        return {
            "type": self.type,
            "setup": self.setup,
            "punchline": self.punchline,
            "id": self.id,
        }


@dataclass(frozen=True)
class Jokes:
    """
    Represents a collection of jokes.

    This class is used to store and manage a collection of Joke objects,
    allowing jokes to be organized and manipulated as a group. The jokes
    attribute contains a list of Joke instances.

    :ivar jokes: A list of Joke objects contained within this collection.
    :type jokes: list[Joke]
    """

    jokes: list[Joke]

    # Utilidad opcional para consistencia
    def get_jokes(self) -> list[Joke]:
        """Devuelve la lista de chistes."""
        return self.jokes
