#!/usr/bin/env python3
import copy

import tcod

import colour
from engine import Engine
import entity_factories
from procgen import generate_dungeon


def main() -> None:
    # Defining variables for screen, map, rooms etc.
    # TODO: move to json to clean up and fix size
    screen_width = 80
    screen_height = 50

    map_width = 80
    map_height = 43

    room_max_size = 10
    room_min_size = 6
    max_rooms = 30

    max_monsters_per_room = 2

    # What font to use (the one saved in the repo)
    tileset = tcod.tileset.load_tilesheet(
        "dejavu10x10_gs_tc.png",
        32,
        8,
        tcod.tileset.CHARMAP_TCOD,
    )

    # Call entity class and define
    # We can't use spawn as that passes the gamemap which isnt created yet
    player = copy.deepcopy(entity_factories.player)

    engine = Engine(player=player)

    # Call game map
    engine.game_map = generate_dungeon(
        max_rooms=max_rooms,
        room_min_size=room_min_size,
        room_max_size=room_max_size,
        map_width=map_width,
        map_height=map_height,
        max_monsters_per_room=max_monsters_per_room,
        engine=engine,
    )

    # Create our start fov
    engine.update_fov()

    engine.message_log.add_message(
        "Hello and welcome, adventurer, to yet another random dungeon! Who would have thought it!",
        colour.welcome_text,
    )

    # Create the screen
    # Definisng vsync is slightly redundant but all the best
    # games have it!!
    with tcod.context.new_terminal(
        screen_width,
        screen_height,
        tileset=tileset,
        title="Game",
        vsync=True,
    ) as context:
        # Creates the console we are drawing to
        # n.p order= 'F' reverses numpys unintuitive [y,x] notation
        root_console = tcod.console.Console(screen_width, screen_height, order="F")

        # Game loop
        while True:
            # Where to print
            root_console.clear()
            engine.event_handler.on_render(console=root_console)
            context.present(root_console)

            # Update the screen with what we told it to display
            engine.event_handler.handle_events(context)


if __name__ == "__main__":
    main()
