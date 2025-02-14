#Type hinting that something can be set to None
from typing import Optional

import tcod.event

from actions import Action, EscapeAction, MovementAction

#EventHandler is a subclass of EventDispatch. Allows event sending
#to proper methods
class EventHandler(tcod.event.EventDispatch[Action]):
    
    #Method of EventDispatch, when 'X' is hit (a quit event) we quit
    def ev_quit(self, event: tcod.event.Quit) -> Optional[Action]:
        raise SystemExit()
    
    #Method will receive key presses and return Action class or None
    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[Action]:
        
        #action holds whatever subclass of Action we choose or None
        action: Optional[Action] = None
        
        #Holds the actual key pressed
        #TODO: expand to modifiers e.g shift and alt
        key = event.sym
        
        #e.g. uo arrw creates a MovementAction amd which direction to move
        if key == tcod.event.KeySym.UP:
            action = MovementAction(dx= 0, dy= -1)
        elif key == tcod.event.KeySym.DOWN:
            action = MovementAction(dx= 0, dy= 1)
        elif key == tcod.event.KeySym.LEFT:
            action = MovementAction(dx= -1, dy= 0)
        elif key == tcod.event.KeySym.RIGHT:
            action = MovementAction(dx= 1, dy= 0)
        
        #Esc key returns EscapeAction
        #TODO: make this a menu maybe?
        elif key == tcod.event.K_ESCAPE:
            action = EscapeAction()
            
        return action