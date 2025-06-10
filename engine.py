from __future__ import annotations

from typing import TYPE_CHECKING

from tcod.console import Console
from tcod.map import compute_fov

from input_handlers import MainGameEventHandler
from message_log import MessageLog
from render_functions import render_bar, render_names_at_mouse_location

if TYPE_CHECKING:
    from entity import Actor
    from game_map import GameMap
    from input_handlers import EventHandler


class Engine:
    game_map: GameMap

    # Seperate player reference for ease
    def __init__(
        self,
        player: Actor,
    ):
        self.event_handler: EventHandler = MainGameEventHandler(self)
        self.message_log = MessageLog()
        self.mouse_location = (0, 0)
        self.player = player

    def handle_enemy_turns(self) -> None:
        for entity in set(self.game_map.actors) - {self.player}:
            if entity.ai:
                entity.ai.perform()

    def update_fov(self) -> None:
        """
        Recompute the visible area based on the players POV

        compute_fov takes arguments (transparency, pov, radius)

        //TODO: investigate the function more to consider more complex
        FOV algorithms
        """
        self.game_map.visible[:] = compute_fov(
            self.game_map.tiles["transparent"],
            (self.player.x, self.player.y),
            radius=8,
        )

        # If it is now visible then we add it to explored
        self.game_map.explored |= self.game_map.visible

    # Draw screen and iterate through entities to print to screen
    def render(self, console: Console) -> None:
        self.game_map.render(console)

        self.message_log.render(console=console, x=21, y=45, width=40, height=5)

        render_bar(
            console=console,
            current_value=self.player.fighter.hp,
            max_value=self.player.fighter.max_hp,
            total_width=20,
        )

        render_names_at_mouse_location(console=console, x=21, y=44, engine=self)
