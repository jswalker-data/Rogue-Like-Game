from __future__ import annotations

from typing import Optional, Tuple, TYPE_CHECKING

import colour
import exceptions

if TYPE_CHECKING:
    from engine import Engine
    from entity import Actor, Entity


class Action:
    def __init__(self, entity: Actor) -> None:
        super().__init__()
        self.entity = entity

    @property
    def engine(self) -> Engine:
        """Return which engine the action belongs to"""
        return self.entity.gamemap.engine

    def perform(self) -> None:
        """Perform this action with the objects needed to determine
        its scope.

        `self.engine` is the scope this action is being performed in.

        `self.entity` is the object performing the action.

        This method must be overridden by Action subclasses.
        """
        raise NotImplementedError()


# Esc key for quitting game
# TODO: Make a menu option maybe?
class EscapeAction(Action):
    def perform(self) -> None:
        raise SystemExit()


class WaitAction(Action):
    def perform(self) -> None:
        pass


class ActionWithDirection(Action):
    def __init__(self, entity: Actor, dx: int, dy: int):
        super().__init__(entity)

        self.dx = dx
        self.dy = dy

    @property
    def dest_xy(self) -> Tuple[int, int]:
        """Returns the destination of the action"""
        return self.entity.x + self.dx, self.entity.y + self.dy

    @property
    def blocking_entity(self) -> Optional[Entity]:
        """Return the blocking entity at this actions destination"""
        return self.engine.game_map.get_blocking_entity_at_location(*self.dest_xy)

    # Return the actor where we are moving to, so we know what we are attacking!!
    @property
    def target_actor(self) -> Optional[Actor]:
        """Return the actor at this actions location"""
        return self.engine.game_map.get_actor_at_location(*self.dest_xy)

    # This method would be ovberidden by subclasses
    def perform(self) -> None:
        raise NotImplementedError


class MeleeAction(ActionWithDirection):
    def perform(self) -> None:
        target = self.target_actor
        if not target:
            raise exceptions.Impossible("Nothing to attack!")  # No entity to attack.

        # How much damage taken
        damage = self.entity.fighter.power - target.fighter.defense

        attack_desc = f"{self.entity.name.capitalize()} attacks {target.name}"
        if self.entity is self.engine.player:
            attack_colour = colour.player_atk
        else:
            attack_colour = colour.enemy_atk

        if damage > 0:
            self.engine.message_log.add_message(
                f"{attack_desc} for {damage} hit points", attack_colour
            )
            target.fighter.hp -= damage
        else:
            self.engine.message_log.add_message(
                f"{attack_desc} but does no damage.", attack_colour
            )


# Move player
class MovementAction(ActionWithDirection):
    def perform(self) -> None:
        dest_x, dest_y = self.dest_xy

        # Double check walkable and in bounds
        if not self.engine.game_map.in_bounds(dest_x, dest_y):
            # Destination is out of bounds
            raise exceptions.Impossible("This way is blocked!")

        if not self.engine.game_map.tiles["walkable"][dest_x, dest_y]:
            # Destination is blocked by a tile
            raise exceptions.Impossible("This way is blocked!")

        # Safeguard, should never be triggered due to other criteria
        if self.engine.game_map.get_blocking_entity_at_location(dest_x, dest_y):
            # Destination is blocked by an enemy
            raise exceptions.Impossible("This way is blocked!")

        self.entity.move(self.dx, self.dy)


# Are we moving or attacking: which class does the work
class BumpAction(ActionWithDirection):
    def perform(self) -> None:
        if self.target_actor:
            return MeleeAction(self.entity, self.dx, self.dy).perform()

        else:
            return MovementAction(self.entity, self.dx, self.dy).perform()
