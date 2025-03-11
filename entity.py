from __future__ import annotations

import copy
from typing import TYPE_CHECKING, Tuple, TypeVar, Optional, Type

if TYPE_CHECKING:
    from components.ai import BaseAI
    from components.fighter import Fighter
    from game_map import GameMap


# // TODO: block_movement always True for actor. Ghost enemies???
# // TODO: maybe when certain ghosts die they turn into ghosts

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
        blocks_movement: bool = False,
    ):
        self.x = x
        self.y = y
        self.char = char
        self.colour = colour
        self.name = name
        self.blocks_movement = blocks_movement
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

    # Actor class init


class Actor(Entity):
    # Actor class init
    def __init__(
        self,
        *,
        x: int = 0,
        y: int = 0,
        char: str = "?",
        colour: Tuple[int, int, int] = (255, 255, 255),
        name: str = "<Unnamed>",
        ai_cls: Type[BaseAI],
        fighter: Fighter,
    ):
        super().__init__(
            x=x,
            y=y,
            char=char,
            colour=colour,
            name=name,
            blocks_movement=True,
        )
        self.ai: Optional[BaseAI] = ai_cls(self)
        self.fighter = fighter
        self.fighter.entity = self

    @property
    def is_alive(self) -> bool:
        """Returns true as long as this actor is alove and can perform"""
        return bool(self.ai)
