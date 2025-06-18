from __future__ import annotations

from typing import TYPE_CHECKING, List, Tuple

import random
import numpy as np
import tcod

from actions import Action, BumpAction, MeleeAction, MovementAction, WaitAction

if TYPE_CHECKING:
    from entity import Actor

# //TODO: Different pathing for different entities?
# //TODO: Target could be food or treasure instead of player?? Race to the treasure??
# //TODO: Terrain could take longer to pass? Water?


class BaseAI(Action):
    entity: Actor

    def perform(self) -> None:
        # return
        raise NotImplementedError()

    def get_path_to(self, dest_x: int, dest_y: int) -> List[Tuple[int, int]]:
        """
        Compute the path to a target, using a cost based system on how far
        and where to travel

        Args:
            dest_x (int): Where in the x posiiton entity are going
            dest_y (int): Where in the y position entity is going

        Returns:
            List[Tuple[int,int]]: returns the path through list of coord,
            empty if no path
        """
        # use walkable array from entity and make array of 1 if walkable
        cost = np.array(self.entity.gamemap.tiles['walkable'], dtype=np.int8)

        for entity in self.entity.gamemap.entities:
            # Check entity blocking and cost not equal zero (walkable)
            if entity.blocks_movement and cost[entity.x, entity.y]:
                # Add to the cost of a blocked position.
                # A lower number means more enemies will crowd behind each other in
                # hallways.  A higher number means enemies will take longer paths in
                # order to surround the player.
                # The paths will avoid other entities as now a costly 10 space
                cost[entity.x, entity.y] += 10

        # Creates a graph from cost array and pass graph to new pathfinder
        graph = tcod.path.SimpleGraph(cost=cost, cardinal=2, diagonal=3)
        pathfinder = tcod.path.Pathfinder(graph)

        # Start position
        pathfinder.add_root((self.entity.x, self.entity.y))

        # Compute path and remove start as its already there
        path: List[List[int]] = pathfinder.path_to((dest_x, dest_y))[1:].tolist()

        # Convert to expected typing
        return [(index[0], index[1]) for index in path]


class HostileEnemy(BaseAI):
    def __init__(self, entity: Actor):
        super().__init__(entity)
        self.path: List[Tuple[int, int]] = []

    def perform(self) -> None:
        target = self.engine.player
        dx = target.x - self.entity.x
        dy = target.y - self.entity.y
        distance = max(abs(dx), abs(dy))

        if self.engine.game_map.visible[self.entity.x, self.entity.y]:
            if distance <= 1:
                return MeleeAction(self.entity, dx, dy).perform()

            self.path = self.get_path_to(target.x, target.y)

        if self.path:
            dest_x, dest_y = self.path.pop(0)
            return MovementAction(self.entity, dest_x - self.entity.x, dest_y - self.entity.y).perform()

        return WaitAction(self.entity).perform()


class ConfusedEnemy(BaseAI):
    """
    A confused enemy will stumble around aimlessly for a given numer of turns, then return back to previous AI.
    If an actor occupies a tile it is randomly moving into, it will attack.
    """

    def __init__(self, entity: Actor, previous_ai: BaseAI | None, turns_remaining: int):
        super().__init__(entity)

        self.previous_ai = previous_ai
        self.turns_remaining = turns_remaining

    def preform(self) -> None:
        # Revert the AI back to the original state if the effect has finished.
        if self.turns_remaining <= 0:
            self.engine.message_log.add_message(f'The {self.entity.name} is no longer confused.')
            self.entity.ai = self.previous_ai
        else:
            # Pick random direction
            direction_x, direction_y = random.choice(
                [
                    (-1, -1),
                    (0, -1),
                    (1, -1),
                    (-1, 0),
                    (1, 0),
                    (-1, 1),
                    (0, 1),
                    (1, 1),
                ]
            )

            self.turns_remaining -= 1

            # The actor will either try to move or attack in the choosen random direction.
            # Its possible the actor will just bump into the wall wasting a turn
            # I am not going to add in logic that prevents this
            return BumpAction(
                self.entity,
                direction_x,
                direction_y,
            ).perform()
