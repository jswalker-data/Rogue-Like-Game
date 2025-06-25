"""Handle the loading and initialisation of game session."""

from __future__ import annotations

import copy

import tcod

import colour
import entity_factories
import input_handlers
from engine import Engine
from procgen import generate_dungeon

# Load the background image and remove alpha channel
background_image = tcod.image.load('menu_background.png')[:, :, :3]


def new_gane() -> Engine:
    """Return a brand new game session as an Engine instance."""
    map_width = 80
    map_height = 43

    room_max_size = 10
    room_min_size = 6
    max_rooms = 30

    max_monsters_per_room = 2
    max_items_per_room = 2

    player = copy.deepcopy(entity_factories.player)

    engine = Engine(player=player)

    engine.game_map = generate_dungeon(
        max_rooms=max_rooms,
        room_min_size=room_min_size,
        room_max_size=room_max_size,
        map_width=map_width,
        map_height=map_height,
        max_monsters_per_room=max_monsters_per_room,
        max_items_per_room=max_items_per_room,
        engine=engine,
    )
    engine.update_fov()

    engine.message_log.add_message('Hello and welcome, adventurer, to yet another dungeon!', colour.welcome_text)
    return engine


class MainMenu(input_handlers.BaseEventHandler):
    """Handle the main menu rendering and input."""

    def on_render(self, console: tcod.Console) -> None:
        """Render the main menu on a background image."""
        console.draw_semigraphics(background_image, 0, 0)

        console.print(
            console.width // 2,
            console.height // 2 - 4,
            'TOMBS OF SOME ANCIENT RICH GUY OR SOMETHING',
            fg=colour.menu_title,
            alignment=tcod.CENTER,
        )
        console.print(
            console.width // 2,
            console.height - 2,
            'By Josh Wallker',
            fg=colour.menu_title,
            alignment=tcod.CENTER,
        )

        menu_width = 24
        for i, text in enumerate(['[N] Play a new game', '[C] continue last game', '[Q] Quit']):
            console.print(
                console.width // 2,
                console.height // 2 - 2 + i,
                text.ljust(menu_width),
                fg=colour.menu_text,
                bg=colour.black,
                alignment=tcod.CENTER,
                bg_blend=tcod.BKGND_ALPHA(64),
            )

    def ev_keydown(self, event: tcod.event.KeyDown) -> input_handlers.BaseEventHandler | None:
        if event.sym in (tcod.event.K_q, tcod.event.K_ESCAPE):
            raise SystemExit()
        elif event.sym == tcod.event.K_c:
            # TODO: Load the gaame here
            pass
        elif event.sym == tcod.event.K_n:
            return input_handlers.MainGameEventHandler(new_gane())

        return None
