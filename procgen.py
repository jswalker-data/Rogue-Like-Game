from __future__ import annotations

import random
from typing import TYPE_CHECKING, Dict, Iterator, List, Tuple

import tcod

import entity_factories
import tile_types
from game_map import GameMap

if TYPE_CHECKING:
    from engine import Engine
    from entity import Entity


max_items_per_floor = [(1, 1), (4, 2)]

max_monsters_per_floor = [(1, 2), (4, 3), (6, 5)]


item_chances: Dict[int, List[Tuple[Entity, int]]] = {
    0: [(entity_factories.health_potion, 35)],
    2: [(entity_factories.confusion_scroll, 10)],
    4: [(entity_factories.lightning_scroll, 25)],
    6: [(entity_factories.fireball_scroll, 25)],
}

enemy_chances: Dict[int, List[Tuple[Entity, int]]] = {
    0: [(entity_factories.orc, 80)],
    3: [(entity_factories.troll, 15)],
    5: [(entity_factories.troll, 30)],
    7: [(entity_factories.troll, 60)],
}


def get_max_value_for_floor(weighted_chance_by_floor: List[Tuple[int, int]], floor: int) -> int:
    current_value = 0

    for floor_min, value in weighted_chance_by_floor:
        if floor_min > floor:
            break
        else:
            current_value = value

    return current_value


def get_entities_at_random(
    weighted_chances_by_floor: Dict[int, List[Tuple[Entity, int]]],
    number_of_entities: int,
    floor: int,
) -> List[Entity]:
    entity_weighted_chances = {}

    for key, values in weighted_chances_by_floor.items():
        if key > floor:
            break
        else:
            for value in values:
                entity = value[0]
                weighted_chance = value[1]

                entity_weighted_chances[entity] = weighted_chance

    entities = list(entity_weighted_chances.keys())
    entity_weighted_chances_values = list(entity_weighted_chances.values())

    chosen_entities = random.choices(entities, weights=entity_weighted_chances_values, k=number_of_entities)

    return chosen_entities


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
        return self.x1 <= other.x2 and self.x2 >= other.x1 and self.y1 <= other.y2 and self.y2 >= other.y1


def place_entities(
    room: RectangularRoom,
    dungeon: GameMap,
    floor_number: int,
) -> None:
    num_Monsters = random.randint(0, get_max_value_for_floor(max_monsters_per_floor, floor_number))  # noqa: S311
    num_items = random.randint(0, get_max_value_for_floor(max_items_per_floor, floor_number))  # noqa: S311

    monsters: List[Entity] = get_entities_at_random(
        enemy_chances,
        num_Monsters,
        floor_number,
    )

    items: List[Entity] = get_entities_at_random(
        item_chances,
        num_items,
        floor_number,
    )

    for entity in monsters + items:
        x = random.randint(room.x1 + 1, room.x2 - 1)
        y = random.randint(room.y1 + 1, room.y2 - 1)

        if not any(entity.x == x and entity.y == y for entity in dungeon.entities):
            entity.spawn(dungeon, x, y)


# Take 2 sets of x, y and return iterator of 2 tuples of ints
def tunnel_between(start: Tuple[int, int], end: Tuple[int, int]) -> Iterator[Tuple[int, int]]:
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
    engine: Engine,
) -> GameMap:
    """Generate new dungeon map"""

    player = engine.player
    dungeon = GameMap(engine, map_width, map_height, entities=[player])

    rooms: List[RectangularRoom] = []

    center_of_last_room = (0, 0)

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

            center_of_last_room = new_room.center

        # Place entities in the room
        place_entities(new_room, dungeon, engine.game_world.current_floor)

        # Add the down stairs to the last room
        dungeon.tiles[center_of_last_room] = tile_types.down_stairs
        dungeon.downstairs_location = center_of_last_room

        # Append to list of rooms
        rooms.append(new_room)

    return dungeon
