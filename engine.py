from typing import Set, Iterable, Any

from tcod.context import Context
from tcod.console import Console
from tcod.map import compute_fov

from entity import Entity
from game_map import GameMap
from input_handlers import EventHandler

class Engine:
    
    #Seperate player reference for ease
    def __init__(self, entities: Set[Entity], event_handler: EventHandler, game_map: GameMap, player: Entity):
        self.entities = entities
        self.event_handler = event_handler
        self.game_map = game_map
        self.player = player
        self.update_fov()
        
    #Pass events and uterate through
    def handle_events(self, events: Iterable[Any]) -> None:
        for event in events:
            action = self.event_handler.dispatch(event)
            
            if action is None:
                continue
            
            action.perform(self, self.player)
            
            #Update fov before players next action and after each one
            self.update_fov()

    def update_fov(self) -> None:
        """
        Recompute the visible area based on the players POV
        
        compute_fov takes arguments (transparency, pov, radius)
        
        //TODO: investigate the function more to consider more complex
        FOV algorithms
        """
        self.game_map.visible[:]= compute_fov(
            self.game_map.tiles['transparent'],
            (self.player.x, self.player.y),
            radius= 8,
        )
        
        #If it is now visible then we add it to explored
        self.game_map.explored|= self.game_map.visible

    #Draw screen and iterate through entities to print to screen
    def render(self, console: Console, context: Context) -> None:
        
        self.game_map.render(console)
        
        for entity in self.entities:
            #Only print entities in FOV
            if self.game_map.visible[entity.x, entity.y]:
                console.print(entity.x, entity.y, entity.char, fg= entity.colour)
        
        context.present(console)
        
        console.clear()






