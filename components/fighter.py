from __future__ import annotations

from typing import TYPE_CHECKING

import colour
from components.base_component import BaseComponent
from input_handlers import GameOverEventHandler
from render_order import RenderOrder

if TYPE_CHECKING:
    from entity import Actor


# Inherit base component to allow access to entity and engine
class Fighter(BaseComponent):
    parent: Actor

    def __init__(self, hp: int, defense: int, power: int):
        # Getter and setter of hp, allows access of hp as normal var
        self.max_hp = hp
        self._hp = hp
        self.defense = defense
        self.power = power

    # Getter: returns the hp
    @property
    def hp(self) -> int:
        return self._hp

    # Setter: always between 0 and max
    @hp.setter
    def hp(self, value: int) -> None:
        self._hp = max(0, min(value, self.max_hp))
        if self._hp == 0 and self.parent.ai:
            self.die()

    def die(self) -> None:
        if self.engine.player is self.parent:
            death_message = "You died!"
            death_message_colour = colour.player_die
            self.engine.event_handler = GameOverEventHandler(self.engine)
        else:
            death_message = f"{self.parent.name} is dead!"
            death_message_colour = colour.enemy_die

        self.parent.char = "%"
        self.parent.colour = (191, 0, 0)
        self.parent.blocks_movement = False
        self.parent.ai = None
        self.parent.name = f"remains of {self.parent.name}"
        self.parent.render_order = RenderOrder.CORPSE
        self.engine.message_log.add_message(death_message, death_message_colour)
