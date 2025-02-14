

class Action:
    pass

#Move player
class MovementAction(Action):
    def __init__(self, dx: int, dy: int):
        super().__init__()
        
        self.dx= dx
        self.dy= dy

#Esc key for quitting game
#TODO: Make a menu option maybe?
class EscapeAction(Action):
    pass