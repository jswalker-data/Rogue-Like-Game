

from typing import Tuple



class Entity:
    """
    A generic object that will store representations of players,
    enemies, items and anyting else
    """
    
    #char is display character, colour is rgb 
    def __init__(self, x: int, y: int, char: str, colour: Tuple[int, int, int]):
        
    
        self.x = x
        self.y = y
        self.char = char
        self.colour = colour
    
    def move(self, dx: int, dy: int) -> None:
        
        #Move by amount
        self.x += dx
        self.y += dy
        