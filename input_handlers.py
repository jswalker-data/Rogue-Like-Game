# Type hinting that something can be set to None
from __future__ import annotations


from typing import Optional, TYPE_CHECKING

import tcod.event
from tcod import libtcodpy

from actions import Action, BumpAction, EscapeAction, WaitAction

import colour
import exceptions

if TYPE_CHECKING:
    from engine import Engine

MOVE_KEYS = {
    # Arrow keys.
    tcod.event.K_UP: (0, -1),
    tcod.event.K_DOWN: (0, 1),
    tcod.event.K_LEFT: (-1, 0),
    tcod.event.K_RIGHT: (1, 0),
    tcod.event.K_HOME: (-1, -1),
    tcod.event.K_END: (-1, 1),
    tcod.event.K_PAGEUP: (1, -1),
    tcod.event.K_PAGEDOWN: (1, 1),
    # Numpad keys.
    tcod.event.K_KP_1: (-1, 1),
    tcod.event.K_KP_2: (0, 1),
    tcod.event.K_KP_3: (1, 1),
    tcod.event.K_KP_4: (-1, 0),
    tcod.event.K_KP_6: (1, 0),
    tcod.event.K_KP_7: (-1, -1),
    tcod.event.K_KP_8: (0, -1),
    tcod.event.K_KP_9: (1, -1),
    # Vi keys.
    tcod.event.K_h: (-1, 0),
    tcod.event.K_j: (0, 1),
    tcod.event.K_k: (0, -1),
    tcod.event.K_l: (1, 0),
    tcod.event.K_y: (-1, -1),
    tcod.event.K_u: (1, -1),
    tcod.event.K_b: (-1, 1),
    tcod.event.K_n: (1, 1),
}

WAIT_KEYS = {
    tcod.event.K_PERIOD,
    tcod.event.K_KP_5,
    tcod.event.K_CLEAR,
}

CURSOR_Y_KEYS = {
    tcod.event.K_UP: -1,
    tcod.event.K_DOWN: 1,
    tcod.event.K_PAGEUP: -10,
    tcod.event.K_PAGEDOWN: 10,
}


# EventHandler is a subclass of EventDispatch. Allows event sending
# to proper methods
class EventHandler(tcod.event.EventDispatch[Action]):
    def __init__(self, engine: Engine):
        self.engine = engine

    def handle_events(self, event: tcod.event.Event) -> None:
        self.handle_events(self.dispatch(event))

    def handle_action(self, action: Optional[Action]) -> bool:
        """
        Handle actions returned from event methods

        Returns True if the action will advance a turn
        """
        if action is None:
            return False

        try:
            action.perform()
        except exceptions.Impossible as exc:
            self.engine.message_log.add_message(exc.args[0], colour.impossible)

            # skip enemy turn on exception
            return False

        self.engine.handle_enemy_turns()

        self.engine.update_fov()
        return True

    def ev_mousemotion(self, event: tcod.event.MouseMotion) -> None:
        if self.engine.game_map.in_bounds(event.tile.x, event.tile.y):
            self.engine.mouse_location = event.tile.x, event.tile.y

    # Method of EventDispatch, when 'X' is hit (a quit event) we quit
    def ev_quit(self, event: tcod.event.Quit) -> Optional[Action]:
        raise SystemExit()

    def on_render(self, console: tcod.Console) -> None:
        self.engine.render(console)


class MainGameEventHandler(EventHandler):
    # Method will receive key presses and return Action class or None
    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[Action]:
        # action holds whatever subclass of Action we choose or None
        action: Optional[Action] = None

        # Holds the actual key pressed
        # TODO: expand to modifiers e.g shift and alt
        key = event.sym

        player = self.engine.player

        if key in MOVE_KEYS:
            dx, dy = MOVE_KEYS[key]
            action = BumpAction(player, dx, dy)
        elif key in WAIT_KEYS:
            action = WaitAction(player)

        # Esc key returns EscapeAction
        # TODO: make this a menu maybe?
        elif key == tcod.event.KeySym.ESCAPE:
            action = EscapeAction(player)

        elif key == tcod.event.KeySym.v:
            self.engine.event_handler = HistoryViewer(self.engine)

        return action


class GameOverEventHandler(EventHandler):
    def ev_keydown(self, event: tcod.event.KeyDown) -> None:
        if event.sym == tcod.event.KeySym.ESCAPE:
            raise SystemExit()


class HistoryViewer(EventHandler):
    """Print log history on large window which can be navigated"""

    def __init__(self, engine: Engine):
        super().__init__(engine)
        self.log_length = len(engine.message_log.messages)
        self.cursor = self.log_length - 1

    def on_render(self, console: tcod.Console) -> None:
        # Draw the main state as the background
        super().on_render(console)

        log_console = tcod.console.Console(console.width - 6, console.height - 6)

        # Draw frame with custom banner
        log_console.draw_frame(0, 0, log_console.width, log_console.height)
        log_console.print_box(
            0,
            0,
            log_console.width,
            1,
            "┤Message history├",
            alignment=libtcodpy.CENTER,
        )

        # Render message log
        self.engine.message_log.render_messages(
            log_console,
            1,
            1,
            log_console.width - 2,
            log_console.height - 2,
            self.engine.message_log.messages[: self.cursor + 1],
        )
        log_console.blit(console, 3, 3)

    def ev_keydown(self, event: tcod.event.KeyDown) -> None:
        # Conditional movement
        if event.sym in CURSOR_Y_KEYS:
            adjust = CURSOR_Y_KEYS[event.sym]

            # Only move from top to bottom on the edge
            if adjust < 0 and self.cursor == 0:
                self.cursor = self.log_length - 1

            # Same but bottom to top
            elif adjust > 0 and self.cursor == self.log_length - 1:
                self.cursor = 0

                # Else move while being bound to the bounds of the history log
            else:
                self.cursor = max(0, min(self.cursor + adjust, self.log_length - 1))

        # Move directly to top message
        elif event.sym == tcod.event.KeySym.HOME:
            self.cursor = 0

        # Move to bottom message
        elif event.sym == tcod.event.KeySym.END:
            self.cursor = self.log_length - 1

        # Any other key not above moves back to main game state
        else:
            self.engine.event_handler = MainGameEventHandler(self.engine)
