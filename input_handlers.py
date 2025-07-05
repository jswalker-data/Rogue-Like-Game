# Type hinting that something can be set to None
from __future__ import annotations

import os
from typing import TYPE_CHECKING, Callable, Tuple, Union

import tcod

import actions
import colour
import exceptions
from actions import Action, BumpAction, PickupAction, WaitAction

if TYPE_CHECKING:
    from engine import Engine
    from entity import Item


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

CONFIRM_KEYS = {
    tcod.event.K_RETURN,
    tcod.event.K_KP_ENTER,
}


ActionOrHandler = Union[Action, 'BaseEventHandler']
"""An event handler return value which can trigger an action or switch active handlers.

If a handler is returned then it will become the active handler for future events
If an action is returned it will be attempted and if it's valid then
MainGameEventHandler will become the active handler.
"""


class BaseEventHandler(tcod.event.EventDispatch[ActionOrHandler]):
    def handle_events(self, event: tcod.event.Event) -> BaseEventHandler:
        """Handle an event and return the next active handler."""
        state = self.dispatch(event)
        if isinstance(state, BaseEventHandler):
            return state
        assert not isinstance(state, Action), f'{self!r} can not handle actions.'
        return self

    def on_render(self, console: tcod.Console) -> None:
        raise NotImplementedError()

    def ev_quit(self, event: tcod.event.Quit) -> Action | None:
        raise SystemExit()


class PopupMessage(BaseEventHandler):
    """Display a popup ext window."""

    def __init__(self, parent_handler: BaseEventHandler, text: str):
        self.parent = parent_handler
        self.text = text

    def on_render(self, console: tcod.Console) -> None:
        """Render the parent and dim the result, then print the message on top."""
        self.parent.on_render(console)
        console.tiles_rgb['fg'] //= 8
        console.tiles_rgb['bg'] //= 8

        console.print(
            console.width // 2,
            console.height // 2,
            self.text,
            fg=colour.white,
            bg=colour.black,
            alignment=tcod.CENTER,
        )

    def ev_keydown(self, event: tcod.event.KeyDown) -> BaseEventHandler | None:
        """Any key returns to the parent handler."""
        return self.parent


class EventHandler(BaseEventHandler):
    def __init__(self, engine: Engine):
        self.engine = engine

    def handle_events(self, event: tcod.event.Event) -> BaseEventHandler:
        """Handle events for input handlers with an engine."""
        action_or_state = self.dispatch(event)
        if isinstance(action_or_state, BaseEventHandler):
            return action_or_state
        if self.handle_action(action_or_state):
            # A valid action was performed.
            if not self.engine.player.is_alive:
                # The player was killed sometime during or after the action.
                return GameOverEventHandler(self.engine)
            elif self.engine.player.level.requires_level_up:
                # Player needs to level up
                return LevelUpEventHandler(self.engine)
            return MainGameEventHandler(self.engine)  # Return to the main handler.
        return self

    def handle_action(self, action: Action | None) -> bool:
        """Handle actions returned from event methods.

        Returns True if the action will advance a turn.
        """
        if action is None:
            return False

        try:
            action.perform()
        except exceptions.Impossible as exc:
            self.engine.message_log.add_message(exc.args[0], colour.impossible)
            return False  # Skip enemy turn on exceptions.

        self.engine.handle_enemy_turns()

        self.engine.update_fov()
        return True

    def ev_mousemotion(self, event: tcod.event.MouseMotion) -> None:
        if self.engine.game_map.in_bounds(event.tile.x, event.tile.y):
            self.engine.mouse_location = event.tile.x, event.tile.y

    def on_render(self, console: tcod.Console) -> None:
        self.engine.render(console)


# Not super useful itsel but we will create special subclasses that do specific actions
class AskUserEventHandler(EventHandler):
    """Handles user input for actions that require special input."""

    def ev_keydown(self, event: tcod.event.KeyDown) -> ActionOrHandler | None:
        """By default any key exits this input handler."""
        # Ignore modifier keys
        if event.sym in {
            tcod.event.K_LSHIFT,
            tcod.event.K_RSHIFT,
            tcod.event.K_LCTRL,
            tcod.event.K_RCTRL,
            tcod.event.K_LALT,
            tcod.event.K_RALT,
        }:
            return None
        return self.on_exit()

    def ev_mousebuttondown(self, event: tcod.event.MouseButtonDown) -> ActionOrHandler | None:
        """By default any mouse clicks exits this input handler."""
        return self.on_exit()

    def on_exit(self) -> ActionOrHandler | None:
        """Called when the user is trying to exit or cancel an action.

        By default return to the main handler
        """

        return MainGameEventHandler(self.engine)


class CharacterScreenEventHandler(AskUserEventHandler):
    TITLE = 'Character Information'

    def on_render(self, console: tcod.Console) -> None:
        """Render the character screen."""
        super().on_render(console)

        x = 40 if self.engine.player.x <= 30 else 0

        y = 0

        width = len(self.TITLE) + 4

        console.draw_frame(
            x=x,
            y=y,
            width=width,
            height=7,
            title=self.TITLE,
            clear=True,
            fg=(255, 255, 255),
            bg=(0, 0, 0),
        )

        console.print(x=x + 1, y=y + 1, string=f'Level: {self.engine.player.level.current_level}')
        console.print(x=x + 1, y=y + 2, string=f'XP: {self.engine.player.level.current_xp}')
        console.print(
            x=x + 1,
            y=y + 3,
            string=f'XP for next Level: {self.engine.player.level.experience_to_next_level}',
        )

        console.print(x=x + 1, y=y + 4, string=f'Attack: {self.engine.player.fighter.power}')
        console.print(x=x + 1, y=y + 5, string=f'Defense: {self.engine.player.fighter.defense}')


class LevelUpEventHandler(AskUserEventHandler):
    TITLE = 'Level Up'

    def on_render(self, console: tcod.Console) -> None:
        super().on_render(console)

        x = 40 if self.engine.player.x <= 30 else 0

        console.draw_frame(
            x=x,
            y=0,
            width=35,
            height=8,
            title=self.TITLE,
            clear=True,
            fg=(255, 255, 255),
            bg=(0, 0, 0),
        )

        console.print(x=x + 1, y=1, string="Congratulations! You don't suck!")
        console.print(x=x + 1, y=2, string='Select an attribute to increase.')

        console.print(x=x + 1, y=4, string=f'a) Constitution (+20 HP, from {self.engine.player.fighter.max_hp})')

        console.print(x=x + 1, y=5, string=f'b) Strength (+1 attack, from {self.engine.player.fighter.power})')

        console.print(x=x + 1, y=6, string=f'c) Agility (+1 defense, from {self.engine.player.fighter.defense})')

    def ev_keydown(self, event: tcod.event.KeyDown) -> ActionOrHandler | None:
        player = self.engine.player
        key = event.sym
        index = key - tcod.event.K_a

        if 0 <= index <= 2:
            if index == 0:
                player.level.increase_max_hp()
            elif index == 1:
                player.level.increase_power()
            else:
                player.level.increase_defense()
        else:
            self.engine.message_log.add_message('Invalid entry.', colour.invalid)

            return None

        return super().ev_keydown(event)

    def ev_mousebuttondown(self, event: tcod.event.MouseButtonDown) -> ActionOrHandler | None:
        """
        Don't allow the user to click to exit the menu, like normal
        """
        return None


class InventoryEventHandler(AskUserEventHandler):
    """This handler lets the user select an item.

    What happens then depends on the subclass
    """

    TITLE = '<missing title>'

    def on_render(self, console: tcod.Console) -> None:
        """Render an inventory menu, which displays the items in the inventory, and letter to access  it.
        Will move to a different position based on where the player is located so player can see
        where they are.
        """
        super().on_render(console)
        number_of_items_in_inventory = len(self.engine.player.inventory.items)

        # Make a minimum height of 3
        height = number_of_items_in_inventory + 2

        if height <= 3:
            height = 3

        x = 40 if self.engine.player.x <= 30 else 0

        y = 0

        width = len(self.TITLE) + 4

        console.draw_frame(
            x=x, y=y, width=width, height=height, title=self.TITLE, clear=True, fg=(255, 255, 255), bg=(0, 0, 0)
        )

        if number_of_items_in_inventory > 0:
            for i, item in enumerate(self.engine.player.inventory.items):
                item_key = chr(ord('a') + i)

                is_equipped = self.engine.player.equipment.item_is_equipped(item)

                item_string = f'({item_key}) {item.name}'

                if is_equipped:
                    item_string = f'{item_string} (E)'

                console.print(x + 1, y + i + 1, item_string)

        else:
            console.print(x + 1, y + 1, '(Empty)')

    def ev_keydown(self, event: tcod.event.KeyDown) -> ActionOrHandler | None:
        player = self.engine.player
        key = event.sym
        index = key - tcod.event.K_a

        if 0 <= index <= 26:
            try:
                selected_item = player.inventory.items[index]
            except IndexError:
                self.engine.message_log.add_message('Invalid entry.', colour.invalid)
                return None
            return self.on_item_selected(selected_item)
        return super().ev_keydown(event)

    def on_item_selected(self, item: Item) -> ActionOrHandler | None:
        """Called when the user selected a valid item."""
        raise NotImplementedError()


class InventoryActivateHandler(InventoryEventHandler):
    """Handle using an inventory item."""

    TITLE = 'Select and item to use'

    def on_item_selected(self, item: Item) -> ActionOrHandler | None:
        if item.consumable:
            # Return the action for the selected item.
            return item.consumable.get_action(self.engine.player)
        elif item.equippable:
            return actions.EquipAction(self.engine.player, item)
        else:
            return None


class InventoryDropHandler(InventoryEventHandler):
    """Handle dropping an inventory item."""

    TITLE = 'Select an item to drop'

    def on_item_selected(self, item: Item) -> ActionOrHandler | None:
        """Drop this item."""
        return actions.DropItem(self.engine.player, item)


class SelectIndexHandler(AskUserEventHandler):
    """Handle asking the user for an index on the map."""

    def __init__(self, engine: Engine):
        """Sets the cursor to the player when this handler is constructed."""
        super().__init__(engine)
        player = self.engine.player
        engine.mouse_location = player.x, player.y

    def on_render(self, console: tcod.console) -> None:
        """Highlight the tile under cursor."""
        super().on_render(console)
        x, y = self.engine.mouse_location
        console.tiles_rgb['bg'][x, y] = colour.white
        console.tiles_rgb['fg'][x, y] = colour.black

    def ev_keydown(self, event: tcod.event.KeyDown) -> ActionOrHandler | None:
        """Check for key movemenets and confirmation keys"""
        key = event.sym
        if key in MOVE_KEYS:
            # Holding modifyer key will speed up movement
            modifier = 1
            if event.mod & (tcod.event.KMOD_LSHIFT | tcod.event.KMOD_RSHIFT):
                modifier *= 5
            if event.mod & (tcod.event.KMOD_LCTRL | tcod.event.KMOD_RCTRL):
                modifier *= 10
            if event.mod & (tcod.event.KMOD_LALT | tcod.event.KMOD_RALT):
                modifier *= 20

            x, y = self.engine.mouse_location
            dx, dy = MOVE_KEYS[key]
            x += dx * modifier
            y += dy * modifier
            # Clamp cursor index to map size
            x = max(0, min(x, self.engine.game_map.width - 1))
            y = max(0, min(y, self.engine.game_map.height - 1))
            self.engine.mouse_location = x, y
            return None
        elif key in CONFIRM_KEYS:
            return self.on_index_selected(*self.engine.mouse_location)
        return super().ev_mousebuttondown(event)

    def ev_mousebuttondown(self, event: tcod.event.MouseButtonDown) -> ActionOrHandler | None:
        """Left click confirms a selection."""
        if self.engine.game_map.in_bounds(*event.tile) and event.button == 1:
            return self.on_index_selected(*event.tile)
        return super().ev_mousebuttondown(event)

    def on_index_selected(self, x: int, y: int) -> ActionOrHandler | None:
        """Call when an index is selected."""
        raise NotImplementedError


class LookHandler(SelectIndexHandler):
    """Look the player around using the kayboard"""

    def on_index_selected(self, x: int, y: int) -> MainGameEventHandler:
        """Return back to main handler."""
        return MainGameEventHandler(self.engine)


class SingleRangedAttackHandler(SelectIndexHandler):
    """Handles targeting a single enemy. Only the enemy selected will be affected."""

    def __init__(self, engine: Engine, callback: Callable[[Tuple[int, int]], Action | None]):
        super().__init__(engine)

        self.callback = callback

    def on_index_selected(self, x: int, y: int) -> Action | None:
        return self.callback((x, y))


class AreaRangedAttackHandler(SelectIndexHandler):
    """Handles targeting an area within a given radius. Any entity within will be affected."""

    def __init__(self, engine: Engine, radius: int, callback: Callable[[Tuple[int, int]], Action | None]):
        super().__init__(engine)

        self.radius = radius
        self.callback = callback

    def on_render(self, console: tcod.Console) -> None:
        """Highlight the tile under the cursor,"""
        super().on_render(console)

        x, y = self.engine.mouse_location

        # Draw a rectangle around the targeteted area, so player can see what will be affected.
        console.draw_frame(
            x=x - self.radius - 1,
            y=y - self.radius - 1,
            width=self.radius**2,
            height=self.radius**2,
            fg=colour.red,
            clear=False,
        )

    def on_index_selected(self, x: int, y: int) -> Action | None:
        return self.callback((x, y))


class MainGameEventHandler(EventHandler):
    def ev_keydown(self, event: tcod.event.KeyDown) -> ActionOrHandler | None:
        action: Action | None = None

        key = event.sym
        modifier = event.mod

        player = self.engine.player

        # Take the stairs
        if key == tcod.event.K_PERIOD and modifier & (tcod.event.KMOD_LSHIFT | tcod.event.KMOD_RSHIFT):
            return actions.TakeStairsAction(player)

        if key in MOVE_KEYS:
            dx, dy = MOVE_KEYS[key]
            action = BumpAction(player, dx, dy)

        elif key in WAIT_KEYS:
            action = WaitAction(player)

        elif key == tcod.event.K_ESCAPE:
            raise SystemExit()

        elif key == tcod.event.K_v:
            return HistoryViewer(self.engine)

        elif key == tcod.event.K_g:
            action = PickupAction(player)

        elif key == tcod.event.K_i:
            return InventoryActivateHandler(self.engine)

        elif key == tcod.event.K_d:
            return InventoryDropHandler(self.engine)

        elif key == tcod.event.K_c:
            return CharacterScreenEventHandler(self.engine)

        elif key == tcod.event.K_SLASH:
            return LookHandler(self.engine)

        # No valid key was pressed
        return action


class GameOverEventHandler(EventHandler):
    def on_quit(self) -> None:
        """Handle exiting out of a finished game"""
        if os.path.exists('savegame.sav'):
            os.remove('savegame.sav')  # Deletes the active save file
        raise exceptions.QuitWithoutSaving()  # Avoid saving the game

    def ev_quit(self, event: tcod.event.Quit) -> None:
        self.on_quit()

    def ev_keydown(self, event: tcod.event.KeyDown) -> None:
        if event.sym == tcod.event.K_ESCAPE:
            self.on_quit()


CURSOR_Y_KEYS = {
    tcod.event.K_UP: -1,
    tcod.event.K_DOWN: 1,
    tcod.event.K_PAGEUP: -10,
    tcod.event.K_PAGEDOWN: 10,
}


class HistoryViewer(EventHandler):
    """Print the history on a larger window which can be navigated."""

    def __init__(self, engine: Engine):
        super().__init__(engine)
        self.log_length = len(engine.message_log.messages)
        self.cursor = self.log_length - 1

    def on_render(self, console: tcod.Console) -> None:
        super().on_render(console)  # Draw the main state as the background.

        log_console = tcod.Console(console.width - 6, console.height - 6)

        # Draw a frame with a custom banner title.
        log_console.draw_frame(0, 0, log_console.width, log_console.height)
        log_console.print_box(0, 0, log_console.width, 1, '┤Message history├', alignment=tcod.CENTER)

        # Render the message log using the cursor parameter.
        self.engine.message_log.render_messages(
            log_console,
            1,
            1,
            log_console.width - 2,
            log_console.height - 2,
            self.engine.message_log.messages[: self.cursor + 1],
        )
        log_console.blit(console, 3, 3)

    def ev_keydown(self, event: tcod.event.KeyDown) -> MainGameEventHandler | None:
        # Fancy conditional movement to make it feel right.
        if event.sym in CURSOR_Y_KEYS:
            adjust = CURSOR_Y_KEYS[event.sym]
            if adjust < 0 and self.cursor == 0:
                # Only move from the top to the bottom when you're on the edge.
                self.cursor = self.log_length - 1
            elif adjust > 0 and self.cursor == self.log_length - 1:
                # Same with bottom to top movement.
                self.cursor = 0
            else:
                # Otherwise move while staying clamped to the bounds of the history log.
                self.cursor = max(0, min(self.cursor + adjust, self.log_length - 1))
        elif event.sym == tcod.event.K_HOME:
            self.cursor = 0  # Move directly to the top message.
        elif event.sym == tcod.event.K_END:
            self.cursor = self.log_length - 1  # Move directly to the last message.
        else:  # Any other key moves back to the main game state.
            return MainGameEventHandler(self.engine)
        return None
