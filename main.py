#!/usr/bin/env python3
import tcod

from engine import Engine
from entity import Entity
from game_map import GameMap
from input_handlers import EventHandler


def main() -> None:
    
    #Defining screen variables
    #TODO: move to json to clean up
    screen_width = 80
    screen_height = 50
    
    map_width = 80
    map_height = 45
    
    #What font to use (the one saved in the repo)
    tileset = tcod.tileset.load_tilesheet(
        'dejavu10x10_gs_tc.png', 32, 8, tcod.tileset.CHARMAP_TCOD
    )

    #Create an instance of our class, to receive and process events
    event_handler = EventHandler()
    
    #Call entity class and define
    player = Entity(int(screen_width / 2), int(screen_height / 2), '@', (255, 255, 255))
    npc = Entity(int(screen_width / 2 - 5), int(screen_height / 2), '@', (255, 255, 0))
    
    #set will eventually hold all our entities
    entities = {player, npc}
    
    #Call game map
    game_map = GameMap(map_width, map_height)
    
    engine = Engine(entities= entities, event_handler= event_handler, game_map= game_map, player= player)
    
    #Create the screen
    #Definisng vsync is slightly redundant but all the best
    #games have it!!
    with tcod.context.new_terminal(
        screen_width,
        screen_height,
        tileset= tileset,
        title= 'Roguelike v1',
        vsync= True,
    ) as context:
        
        #Creates the console we are drawing to
        #n.p order= 'F' reverses numpys unintuitive [y,x] notation
        root_console = tcod.console.Console(screen_width, screen_height, order= 'F')
        
        #Game loop
        while True:
            
            #Where to print
            engine.render(console= root_console, context= context)
            
            #Update the screen with what we told it to display
            events = tcod.event.wait()
            
            engine.handle_events(events)

if __name__ == '__main__':
    main()