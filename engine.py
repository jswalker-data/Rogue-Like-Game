from __future__ import annotations

from typing import TYPE_CHECKING

from tcod.context import Context
from tcod.console import Console
from tcod.map import compute_fov

from input_handlers import EventHandler

if TYPE_CHECKING:
    from entity import Entity
    from game_map import GameMap


class Engine:
    game_map: GameMap

    # Seperate player reference for ease
    def __init__(
        self,
        player: Entity,
    ):
        self.event_handler: EventHandler = EventHandler(self)
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
    def render(self, console: Console, context: Context) -> None:
        self.game_map.render(console)

        context.present(console)

        console.clear()
