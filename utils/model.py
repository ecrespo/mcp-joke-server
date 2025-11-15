from dataclasses import dataclass

@dataclass
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

@dataclass
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
