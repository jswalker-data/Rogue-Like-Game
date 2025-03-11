# Type hinting that something can be set to None
from __future__ import annotations


from typing import Optional, TYPE_CHECKING

import tcod.event

from actions import Action, BumpAction, EscapeAction

if TYPE_CHECKING:
    from engine import Engine


# EventHandler is a subclass of EventDispatch. Allows event sending
# to proper methods
class EventHandler(tcod.event.EventDispatch[Action]):
    def __init__(self, engine: Engine):
        self.engine = engine

    def handle_events(self) -> None:
        for event in tcod.event.wait():
            action = self.dispatch(event)

            if action is None:
                continue

            # Action -> Enemy action -> Update FOV
            action.perform()
            self.engine.handle_enemy_turns()
            self.engine.update_fov()

    # Method of EventDispatch, when 'X' is hit (a quit event) we quit
    def ev_quit(self, event: tcod.event.Quit) -> Optional[Action]:
        raise SystemExit()

    # Method will receive key presses and return Action class or None
    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[Action]:
        # action holds whatever subclass of Action we choose or None
        action: Optional[Action] = None

        # Holds the actual key pressed
        # TODO: expand to modifiers e.g shift and alt
        key = event.sym

        player = self.engine.player

        # e.g. uo arrw creates a MovementAction amd which direction to move
        if key == tcod.event.KeySym.UP:
            action = BumpAction(player, dx=0, dy=-1)
        elif key == tcod.event.KeySym.DOWN:
            action = BumpAction(player, dx=0, dy=1)
        elif key == tcod.event.KeySym.LEFT:
            action = BumpAction(player, dx=-1, dy=0)
        elif key == tcod.event.KeySym.RIGHT:
            action = BumpAction(player, dx=1, dy=0)

        # Esc key returns EscapeAction
        # TODO: make this a menu maybe?
        elif key == tcod.event.KeySym.ESCAPE:
            action = EscapeAction(player)

        return action
