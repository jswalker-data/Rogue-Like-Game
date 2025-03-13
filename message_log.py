from typing import List, Reversible, Tuple
import textwrap

import tcod

import colour


class Message:
    def __init__(self, text: str, fg: Tuple[int, int, int]):
        self.plain_text = text
        self.fg = fg
        self.count = 1

    @property
    def full_text(self) -> str:
        """The full text of this message, including count if needed"""
        if self.count > 1:
            return f"{self.plain_text} (x{self.count})"
        return self.plain_text


class MessageLog:
    def __init__(self) -> None:
        self.messages: List[Message] = []

    def add_message(
        self,
        text: str,
        fg: Tuple[int, int, int] = colour.white,
        *,
        stack: bool = True,
    ) -> None:
        """
        Create the log of message that will be printed

        Args:
            text (str): Message text
            fg (Tuple[int, int, int], optional): Forground colour.
                Defaults to colour.white.
            stack (bool, optional): Stacking the text upon the previous
                message
        """

        if stack and self.messages and text == self.messages[-1].plain_text:
            self.messages[-1].count += 1
        else:
            self.messages.append(Message(text, fg))

    def render(
        self, console: tcod.console.Console, x: int, y: int, width: int, height: int
    ) -> None:
        """
        Render the log messages in given area

        Args:
            console (tcod.Console): To render within
            x (int): Poition in x
            y (int): Position in y
            width (int): Width of render
            height (int): Height of render
        """
        self.render_messages(console, x, y, width, height, self.messages)

    @staticmethod
    def render_messages(
        console: tcod.console.Console,
        x: int,
        y: int,
        width: int,
        height: int,
        messages: Reversible[Message],
    ) -> None:
        """
        Render the messages provided

        Args:
            messages (Reversible[Message]): Render starting at the
                last message and working back. As we want the last
                one to be the top shown
        """
        y_offset = height - 1

        for message in reversed(messages):
            for line in reversed(textwrap.wrap(message.full_text, width)):
                console.print(x=x, y=y + y_offset, string=line, fg=message.fg)
                y_offset -= 1
                # No more space for messages
                if y_offset < 0:
                    return
