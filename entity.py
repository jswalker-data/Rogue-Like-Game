from __future__ import annotations

import copy
from typing import TYPE_CHECKING, Tuple, TypeVar, Optional

if TYPE_CHECKING:
    from game_map import GameMap

T = TypeVar("T", bound="Entity")


class Entity:
    """
    A generic object that will store representations of players,
    enemies, items and anyting else
    """

    gamemap: GameMap

    # char is display character, colour is rgb
    def __init__(
        self,
        gamemap: Optional[GameMap] = None,
        x: int = 0,
        y: int = 0,
        char: str = "?",
        colour: Tuple[int, int, int] = (255, 255, 255),
        name: str = "<Unamed>",
        block_movements: bool = False,
    ):
        self.x = x
        self.y = y
        self.char = char
        self.colour = colour
        self.name = name
        self.block_movements = block_movements
        if gamemap:
            # If the map isnt here now it will be later set
            self.gamemap = gamemap
            gamemap.entities.add(self)

    def spawn(self: T, gamemap: GameMap, x: int, y: int) -> T:
        """Spawn a copy of this instance at the location"""
        clone = copy.deepcopy(self)
        clone.x = x
        clone.y = y
        clone.gamemap = gamemap
        gamemap.entities.add(clone)
        return clone

    # //TODO: This needed??
    def move(self, dx: int, dy: int) -> None:
        # Move by amount
        self.x += dx
        self.y += dy

    def place(self, x: int, y: int, gamemap: Optional[GameMap] = None) -> None:
        """Place at new location. Handles moving across the map"""
        self.x = x
        self.y = y
        if gamemap:
            # We could be uninitialised
            if hasattr(self, "gamemap"):
                self.gamemap.entities.remove(self)
            self.gamemap = gamemap
            gamemap.entities.add(self)
