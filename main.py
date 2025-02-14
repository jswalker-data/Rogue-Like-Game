#!/usr/bin/env python3
import tcod

from actions import EscapeAction, MovementAction
from input_handlers import EventHandler


def main() -> None:
    
    #Defining screen variables
    #TODO: move to json to clean up
    screen_width = 80
    screen_height = 50
    
    #Track player posiiton (TCOD needs int, floats error)
    player_x = int(screen_width/2)
    player_y = int(screen_height/2)
    
    #What font to use (the one saved in the repo)
    tileset = tcod.tileset.load_tilesheet(
        'dejavu10x10_gs_tc.png', 32, 8, tcod.tileset.CHARMAP_TCOD
    )

    #Create an instance of our class, to receive and process events
    event_handler = EventHandler()
    
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
            root_console.print(x= player_x, y= player_y , string= '@')
            
            #Update the screen with what we told it to display
            context.present(root_console)
            
            #Clear console after each event (avoids snake!)
            root_console.clear()
            
            #Wait for an input from user and exit when 'x' is pressed
            for event in tcod.event.wait():
                
                #Sends an event to it's place, pressng 'X' to ev_quit and 
                #a keyboard stroke to ev_keydown
                action = event_handler.dispatch(event)
                
                #No key or a non recognised key
                if action is None:
                    continue
                
                #If action is an instance of MovementAction then return the
                #values to move the character
                if isinstance(action, MovementAction):
                    player_x += action.dx
                    player_y += action.dy
                    
                #Quit with esc
                elif isinstance(action, EscapeAction):
                    raise SystemExit()

if __name__ == '__main__':
    main()