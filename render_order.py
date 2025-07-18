"""
Sorting the entities to what is drawn first
So, for example, acotrs are always 'on top' of corpses
"""

from enum import Enum, auto


class RenderOrder(Enum):
    CORPSE = auto()
    ITEM = auto()
    ACTOR = auto()
