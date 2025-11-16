from __future__ import annotations

from typing import Any, Mapping

from rich.console import Console
from rich.theme import Theme

from utils.logging_interfaces import ConsoleRendererProtocol


DEFAULT_THEME = Theme(
    {
        "log.time": "dim cyan",
        "log.message": "white",
        "log.path": "dim blue",
        "logging.level.debug": "dim blue",
        "logging.level.info": "green",
        "logging.level.warning": "yellow",
        "logging.level.error": "bold red",
        "logging.level.critical": "bold white on red",
        "log.level": "bold",
    }
)


class RichConsoleRenderer(ConsoleRendererProtocol):
    """
    A class for rendering outputs using the Rich library, providing tools for formatted,
    interactive, and elegant console outputs. This renderer is useful for creating
    structured and visually appealing console interfaces by supporting features like
    sections, tables, panels, JSON views, hierarchical tree views, and status messages.

    It integrates with Loguru configuration through a `write` function and provides
    other utilities to organize and display data in custom styles.

    :ivar console: Rich Console instance used for rendering outputs. It is initialized
        with a default Rich theme if none is provided.
    :type console: Console
    """

    def __init__(self, console: Console | None = None):
        self.console = console or Console(theme=DEFAULT_THEME)

    # Punto de integración con la configuración de Loguru: una función write
    def write(self, message: str) -> None:
        """
        Writes a formatted message to the console using Rich console output.

        The method processes the input message by removing trailing whitespace
        and checks if it is non-empty before printing it to the console. The
        message is assumed to already include necessary Rich formatting markup.
        The output will not have syntax highlighting applied.

        :param message: The message to be printed to the console.
        :type message: str
        :return: This method does not return a value.
        :rtype: None
        """
        message = message.rstrip()
        if message:
            # El mensaje ya viene con marcas Rich desde el formatter
            self.console.print(message, markup=True, highlight=False)

    def section(self, title: str, style: str = "bold cyan") -> None:
        """
        Outputs a visual section rule to the console using the specified title and style.

        This method provides a convenient way to create a section break with a custom
        title and style for console-based outputs. It utilizes the `console.rule`
        functionality of the Rich library.

        :param title: The title text for the section rule.
        :type title: str
        :param style: The color and style of the section rule in Rich markup. Defaults to "bold cyan".
        :type style: str
        :return: None
        """
        self.console.rule(f"[{style}]{title}[/{style}]")

    def table(self, title: str, data: Mapping[str, Any], style: str = "cyan") -> None:
        """
        Generate and display a styled table using the given title, data, and style.

        :param title: The title of the table.
        :param data: A dictionary containing the data to populate the table. The keys
            will serve as the names for the first column ("Campo"), while the values
            will be displayed in the second column ("Valor").
        :param style: The style to apply to the title of the table. Defaults to "cyan".
        :return: None. This method does not return any value; it prints the generated
            table using the console.
        """
        from rich.table import Table

        table = Table(title=title, style=style)
        table.add_column("Campo", style="cyan", no_wrap=True)
        table.add_column("Valor", style="white")
        for key, value in data.items():
            table.add_row(str(key), str(value))
        self.console.print(table)

    def json(self, data: Mapping[str, Any], title: str = "JSON Data") -> None:
        """
        Prints formatted JSON data to the console with a specified title.

        This function utilizes the `rich` library to format and display JSON
        data in a human-readable way. It includes a bold cyan title for
        contextualization, followed by the formatted JSON content.

        :param data: The JSON-compatible mapping to be displayed.
        :type data: Mapping[str, Any]
        :param title: The title to display above the JSON content. Defaults to "JSON Data".
        :type title: str, optional
        :return: None
        """
        from rich.json import JSON

        self.console.print(f"[bold cyan]{title}:[/bold cyan]")
        self.console.print(JSON.from_data(data))

    def panel(self, message: str, title: str | None = None, style: str = "cyan") -> None:
        """
        Displays a styled panel in the console using the Rich library.

        This method utilizes the `Panel` class from the Rich library to render
        a visually styled panel containing a message. Optional parameters allow
        customization of the panel's title and style. The formatted panel is then
        printed to the console.

        :param message: The primary content to be displayed within the panel.
        :type message: str
        :param title: An optional title for the panel to be displayed at the top.
        :type title: str | None
        :param style: The style of the panel, defining its color and textual aesthetics.
        :type style: str
        :return: None
        """
        from rich.panel import Panel

        self.console.print(Panel(message, title=title, style=style))

    def tree(self, data: Any, title: str = "Tree View") -> None:
        """
        Generate and display a hierarchical tree representation of the given data structure.

        This function utilizes the `rich.tree.Tree` class to create a visually
        appealing representation of a nested structure, which can include dictionaries
        and lists, rendered as a tree in the console. The tree's title can be customized
        via the `title` parameter. Colors are applied to differentiate keys and nested
        items for better readability.

        :param data: The data to be represented in the tree structure. It can be a
            dictionary, list, or a combination of both as nested elements.
        :type data: Any
        :param title: The title or header displayed at the root of the tree.
            Defaults to "Tree View".
        :type title: str
        :return: None
        """
        from rich.tree import Tree

        def add_to_tree(tree, node):
            if isinstance(node, dict):
                for k, v in node.items():
                    if isinstance(v, (dict, list)):
                        branch = tree.add(f"[cyan]{k}[/cyan]")
                        add_to_tree(branch, v)
                    else:
                        tree.add(f"[cyan]{k}[/cyan]: [white]{v}[/white]")
            elif isinstance(node, list):
                for i, item in enumerate(node):
                    if isinstance(item, (dict, list)):
                        branch = tree.add(f"[yellow][{i}][/yellow]")
                        add_to_tree(branch, item)
                    else:
                        tree.add(f"[yellow][{i}][/yellow]: [white]{item}[/white]")

        tree = Tree(f"[bold]{title}[/bold]")
        add_to_tree(tree, data)
        self.console.print(tree)

    def status(self, message: str, spinner: str = "dots") -> Any:
        """
        Displays a status message on the console with an optional spinner animation.

        The method allows for displaying a temporary status message to the user,
        optionally accompanied by a spinner to indicate ongoing activity. This
        method is typically used when performing actions that may take some time
        to complete, providing feedback about the process to the user.

        :param message: The message to be displayed on the console.
        :type message: str
        :param spinner: The type of spinner animation to display alongside the message.
                       Defaults to "dots".
        :type spinner: str
        :return: The result of the status context, depending on the console's implementation.
        :rtype: Any
        """
        return self.console.status(message, spinner=spinner)


__all__ = ["RichConsoleRenderer", "DEFAULT_THEME"]
