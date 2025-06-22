from __future__ import annotations

import copy
import math
from typing import TYPE_CHECKING, Optional, Tuple, Type, TypeVar, Union

from render_order import RenderOrder

if TYPE_CHECKING:
    from components.ai import BaseAI
    from components.consumable import Consumable
    from components.fighter import Fighter
    from components.inventory import Inventory
    from game_map import GameMap


# // TODO: block_movement always True for actor. Ghost enemies???
# // TODO: maybe when certain ghosts die they turn into ghosts

T = TypeVar('T', bound='Entity')


class Entity:
    """
    A generic object that will store representations of players,
    enemies, items and anyting else
    """

    parent: Union[GameMap, Inventory]

    # char is display character, colour is rgb
    def __init__(
        self,
        parent: GameMap | None = None,
        x: int = 0,
        y: int = 0,
        char: str = '?',
        colour: Tuple[int, int, int] = (255, 255, 255),
        name: str = '<Unamed>',
        blocks_movement: bool = False,
        render_order: RenderOrder = RenderOrder.CORPSE,
    ):
        self.x = x
        self.y = y
        self.char = char
        self.colour = colour
        self.name = name
        self.blocks_movement = blocks_movement
        self.render_order = render_order
        if parent:
            # If parent isnt here now it will be later set
            self.parent = parent
            parent.entities.add(self)

    @property
    def gamemap(self) -> GameMap:
        return self.parent.gamemap

    def spawn(self: T, gamemap: GameMap, x: int, y: int) -> T:
        """Spawn a copy of this instance at the location"""
        clone = copy.deepcopy(self)
        clone.x = x
        clone.y = y
        clone.parent = gamemap
        gamemap.entities.add(clone)
        return clone

    # //TODO: This needed??
    def move(self, dx: int, dy: int) -> None:
        # Move by amount
        self.x += dx
        self.y += dy

    def place(self, x: int, y: int, gamemap: GameMap | None = None) -> None:
        """Place at new location. Handles moving across the map"""
        self.x = x
        self.y = y
        if gamemap:
            # We could be uninitialised
            if hasattr(self, 'parent') and self.parent is self.gamemap:
                self.gamemap.entities.remove(self)
            self.parent = gamemap
            gamemap.entities.add(self)

    def distance(self, x: int, y: int) -> float:
        """
        Return the distance between the current entity and a given coordinate
        """
        return math.sqrt((x - self.x) ** 2 + (y - self.y) ** 2)


class Actor(Entity):
    # Actor class init
    def __init__(
        self,
        *,
        x: int = 0,
        y: int = 0,
        char: str = '?',
        colour: Tuple[int, int, int] = (255, 255, 255),
        name: str = '<Unnamed>',
        ai_cls: Type[BaseAI],
        fighter: Fighter,
        inventory: Inventory,
    ):
        super().__init__(
            x=x,
            y=y,
            char=char,
            colour=colour,
            name=name,
            blocks_movement=True,
            render_order=RenderOrder.ACTOR,
        )
        self.ai: BaseAI | None = ai_cls(self)
        self.fighter = fighter
        self.fighter.parent = self

        self.inventory = inventory
        self.inventory.parent = self

    @property
    def is_alive(self) -> bool:
        """Returns true as long as this actor is alive and can perform"""
        return bool(self.ai)


class Item(Entity):
    def __init__(
        self,
        *,
        x: int = 0,
        y: int = 0,
        char: str = '?',
        colour: Tuple[int, int, int] = (255, 255, 255),
        name: str = '<Unnamed>',
        consumable: Consumable,
    ):
        super().__init__(
            x=x,
            y=y,
            char=char,
            colour=colour,
            name=name,
            blocks_movement=False,
            render_order=RenderOrder.ITEM,
        )

        self.consumable = consumable
        self.consumable.parent = self
