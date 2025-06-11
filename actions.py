from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Tuple

import colour
import exceptions

if TYPE_CHECKING:
    from engine import Engine
    from entity import Actor, Entity, Item


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


class PickupAction(Action):
    """Pickup an item and add it to the inventory, only if space"""

    def __init__(self, entity: Actor):
        super().__init__(entity)

    def perform(self) -> None:
        actor_location_x = self.entity.x
        actor_location_y = self.entity.y
        inventory = self.entity.inventory

        for item in self.engine.game_map.items:
            if actor_location_x == item.x and actor_location_y == item.y:
                if len(inventory.items) >= inventory.capacity:
                    raise exceptions.Impossible('Your inventory is full!')

                self.engine.game_map.entities.remove(item)
                item.parent = self.entity.parent
                inventory.items.append(item)

                self.engine.message_log.add_message(f'You picked up the {item.name}!')
                return

        raise exceptions.Impossible('There is no item here to pickup.')


class ItemAction(Action):
    def __init__(self, entity: Actor, item: Item, target_xy: Optional[Tuple[int, int]] = None):
        super().__init__(entity)
        self.item = item
        if not target_xy:
            target_xy = entity.x, entity.y
        self.target_xy = target_xy

    @property
    def target_actor(self) -> Optional[Actor]:
        """RFeturn the actor at this actions destination"""
        return self.engine.game_map.get_actor_at_location(*self.target_xy)

    def perform(self) -> None:
        """Invoke the abiility of the item, action given to provide context"""
        self.item.consumable.activate(self)


class DropItem(ItemAction):
    def perform(self) -> None:
        self.entity.inventory.drop(self.item)


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
            raise exceptions.Impossible('Nothing to attack!')  # No entity to attack.

        # How much damage taken
        damage = self.entity.fighter.power - target.fighter.defense

        attack_desc = f'{self.entity.name.capitalize()} attacks {target.name}'
        attack_colour = colour.player_atk if self.entity is self.engine.player else colour.enemy_atk

        if damage > 0:
            self.engine.message_log.add_message(f'{attack_desc} for {damage} hit points', attack_colour)
            target.fighter.hp -= damage
        else:
            self.engine.message_log.add_message(f'{attack_desc} but does no damage.', attack_colour)


# Move player
class MovementAction(ActionWithDirection):
    def perform(self) -> None:
        dest_x, dest_y = self.dest_xy

        # Double check walkable and in bounds
        if not self.engine.game_map.in_bounds(dest_x, dest_y):
            # Destination is out of bounds
            raise exceptions.Impossible('This way is blocked!')

        if not self.engine.game_map.tiles['walkable'][dest_x, dest_y]:
            # Destination is blocked by a tile
            raise exceptions.Impossible('This way is blocked!')

        # Safeguard, should never be triggered due to other criteria
        if self.engine.game_map.get_blocking_entity_at_location(dest_x, dest_y):
            # Destination is blocked by an enemy
            raise exceptions.Impossible('This way is blocked!')

        self.entity.move(self.dx, self.dy)


# Are we moving or attacking: which class does the work
class BumpAction(ActionWithDirection):
    def perform(self) -> None:
        if self.target_actor:
            return MeleeAction(self.entity, self.dx, self.dy).perform()

        else:
            return MovementAction(self.entity, self.dx, self.dy).perform()
