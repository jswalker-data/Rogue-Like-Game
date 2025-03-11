from __future__ import annotations

from components.base_component import BaseComponent


# Inherit base component to allow access to entity and engine
class Fighter(BaseComponent):
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
