"""
Overall approcah is filling the room with walls and then carving out
a path and room for us to navigate

Most generation will occur in procgen.py as we may want multiple alternate
generators for different room types

//TODO: Thinking like Boss rooms every 5 floors or something with unique outlines?
//TODO: Maybe easter egg rooms as well, every x rooms or use an rng string
//TODO: Relates to the generator as well to initialise these alternate rooms

"""

from __future__ import annotations

from typing import TYPE_CHECKING, Iterable, Iterator, Optional

import numpy as np
from tcod.console import Console

import tile_types
from entity import Actor, Item

if TYPE_CHECKING:
    from engine import Engine
    from entity import Entity


class GameMap:
    def __init__(
        self,
        engine: Engine,
        width: int,
        height: int,
        entities: Iterable[Entity] = (),
    ):
        self.engine = engine
        self.width, self.height = width, height
        self.entities = set(entities)

        # Create a 2D array filled with same values from tile_types.floor
        # fills self.tiles with floor tiles
        self.tiles = np.full((width, height), fill_value=tile_types.wall, order='F')

        # Add new np frames for currently visible and previously seen
        self.visible = np.full((width, height), fill_value=False, order='F')
        self.explored = np.full((width, height), fill_value=False, order='F')

    @property
    def gamemap(self) -> GameMap:
        return self

    @property
    def actors(self) -> Iterator[Actor]:
        """Iterate over this maps living actors."""
        yield from (entity for entity in self.entities if isinstance(entity, Actor) and entity.is_alive)

    # Find itrems on same tile as player
    @property
    def items(self) -> Iterator[Item]:
        yield from (entity for entity in self.entities if isinstance(entity, Item))

    def get_blocking_entity_at_location(self, location_x: int, location_y: int) -> Optional[Entity]:
        for entity in self.entities:
            if entity.blocks_movement and entity.x == location_x and entity.y == location_y:
                return entity
        return None

    def get_actor_at_location(self, x: int, y: int) -> Optional[Actor]:
        for actor in self.actors:
            if actor.x == x and actor.y == y:
                return actor
        return None

    # Restricts player to avoid void
    def in_bounds(self, x: int, y: int) -> bool:
        """Returns True if x and y are inside bounds of map"""
        return 0 <= x < self.width and 0 <= y < self.height

    # Render map using Console tiles_rgb method
    def render(self, console: Console) -> None:
        """
        Render the map based on passable and iterable parameters

        Visible:
            Drawn with light colours

        Non visible but explored:
            Draw in dark colours to show where we've seen

        Non visible and not explored:
            Default to the SHROUD type
        """

        # Set the console to be conditionally drawn (np.select) based on
        # condlist
        console.tiles_rgb[0 : self.width, 0 : self.height] = np.select(
            # Check if tile is visibile or explored then uses corresponding
            # value
            condlist=[self.visible, self.explored],
            choicelist=[self.tiles['light'], self.tiles['dark']],
            # If neither true in condlist sets default
            default=tile_types.SHROUD,
        )

        entities_sorted_for_rendering = sorted(self.entities, key=lambda x: x.render_order.value)

        for entity in entities_sorted_for_rendering:
            # Only print entities that are in the FOV
            if self.visible[entity.x, entity.y]:
                console.print(
                    x=entity.x,
                    y=entity.y,
                    string=entity.char,
                    fg=entity.colour,
                )
