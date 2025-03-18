from __future__ import annotations

import random
from typing import TYPE_CHECKING, Iterator, List, Tuple

import tcod

import entity_factories
import tile_types
from game_map import GameMap

if TYPE_CHECKING:
    from engine import Engine


class RectangularRoom:
    # take coord of top left and compute bottom right based on height/width
    def __init__(self, x: int, y: int, width: int, height: int):
        self.x1 = x
        self.y1 = y
        self.x2 = x + width
        self.y2 = y + height

    # Property is a read only variable of the class, defining the center
    @property
    def center(self) -> Tuple[int, int]:
        center_x = int((self.x1 + self.x2) / 2)
        center_y = int((self.y1 + self.y2) / 2)

        return center_x, center_y

    # Slices represent our inner portion of the room, what we dig out
    @property
    def inner(self) -> Tuple[slice, slice]:
        """
        Returns the inner area of the room as 2D array index
        Use this to fix "usable" area within a room
        """
        # Remember count from 0 so +1 for area so we have at least a 1 gap
        # between rooms
        return slice(self.x1 + 1, self.x2), slice(self.y1 + 1, self.y2)

    # want rooms to be independant with tunnels without overlap
    def intersects(self, other: RectangularRoom) -> bool:
        """
        Return Tru if this room overlaps with another RectangularRoom
        We need to keep this condition happy for a good dungeon!
        Other in the argument is this 'other' room we might intersect with
        """
        return (
            self.x1 <= other.x2
            and self.x2 >= other.x1
            and self.y1 <= other.y2
            and self.y2 >= other.y1
        )


def place_entities(
    room: RectangularRoom,
    dungeon: GameMap,
    max_monsters: int,
    max_items: int,
) -> None:
    num_Monsters = random.randint(0, max_monsters)
    num_Items = random.randint(0, max_items)

    for i in range(num_Monsters):
        # +-1 So not placed in the walls
        x = random.randint(room.x1 + 1, room.x2 - 1)
        y = random.randint(room.y1 + 1, room.y2 - 1)

        # Check no other entities at that location, stops  stacking
        if not any(entity.x == x and entity.y == y for entity in dungeon.entities):
            if random.random() < 0.8:
                entity_factories.orc.spawn(dungeon, x, y)
            else:
                entity_factories.troll.spawn(dungeon, x, y)

    for i in range(num_Items):
        x = random.randint(room.x1 + 1, room.x2 - 1)
        y = random.randint(room.y1 + 1, room.y2 - 1)

        if not any(entity.x == x and entity.y == y for entity in dungeon.entities):
            entity_factories.health_potion.spawn(dungeon, x, y)


# Take 2 sets of x, y and return iterator of 2 tuples of ints
def tunnel_between(
    start: Tuple[int, int], end: Tuple[int, int]
) -> Iterator[Tuple[int, int]]:
    """Return an L-shaped tunnel between two points"""
    x1, y1 = start
    x2, y2 = end

    # randomly pick if we do hor then vert or other way round
    if random.random() < 0.5:  # 50% chance
        # move horizonal then vertical
        corner_x, corner_y = x2, y1
    else:
        corner_x, corner_y = x1, y2

    # Generate this tunnel, use line of sight algorithm (Bresenhams lines)
    # get line from one set to another
    # Yield returns the values but keeps the state rather then closing it
    # off, picks up where we left off when called again
    for x, y in tcod.los.bresenham((x1, y1), (corner_x, corner_y)).tolist():
        yield x, y
    for x, y in tcod.los.bresenham((corner_x, corner_y), (x2, y2)).tolist():
        yield x, y


# //TODO: We currently toss coliding rooms, more elegant to augment?
def generate_dungeon(
    max_rooms: int,
    room_min_size: int,
    room_max_size: int,
    map_width: int,
    map_height: int,
    max_monsters_per_room: int,
    max_items_per_room: int,
    engine: Engine,
) -> GameMap:
    """Generate new dungeon map"""

    player = engine.player
    dungeon = GameMap(engine, map_width, map_height, entities=[player])

    rooms: List[RectangularRoom] = []

    for r in range(max_rooms):
        room_width = random.randint(room_min_size, room_max_size)
        room_height = random.randint(room_min_size, room_max_size)

        x = random.randint(0, dungeon.width - room_width - 1)
        y = random.randint(0, dungeon.height - room_height - 1)

        # Easier using 'RectangularRoom' class to make rooms
        # TODO: add more options in the future
        new_room = RectangularRoom(x, y, room_width, room_height)

        # Check if it intersets any current rooms
        if any(new_room.intersects(other_room) for other_room in rooms):
            continue  # This rom intersects so next attempt

        # No intersetions means valid room
        # Dig it out
        dungeon.tiles[new_room.inner] = tile_types.floor

        # First room generated, so player start
        if len(rooms) == 0:
            player.place(*new_room.center, dungeon)

        # All other rooms except first
        else:
            # Dig between this and previous room
            for x, y in tunnel_between(rooms[-1].center, new_room.center):
                dungeon.tiles[x, y] = tile_types.floor

        # Place entities in the room
        place_entities(new_room, dungeon, max_monsters_per_room, max_items_per_room)

        # Appppend to list of rooms
        rooms.append(new_room)

    return dungeon
