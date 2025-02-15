from typing import Set, Iterable, Any

from tcod.context import Context
from tcod.console import Console
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
        
    #Pass events and uterate through
    def handle_events(self, events: Iterable[Any]) -> None:
        for event in events:
            action = self.event_handler.dispatch(event)
            
            if action is None:
                continue
            
            action.perform(self, self.player)
            
    #Draw screen and iterate through entities to print to screen
    def render(self, console: Console, context: Context) -> None:
        
        self.game_map.render(console)
        
        for entity in self.entities:
            console.print(entity.x, entity.y, entity.char, fg= entity.colour)
        
        context.present(console)
        
        console.clear()






