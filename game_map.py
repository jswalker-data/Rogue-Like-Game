
import numpy as np
from tcod.console import Console

import tile_types




class GameMap:
    def __init__(self, width: int, height: int):
        self.width, self.height= width, height
        
        #Create a 2D array filled with same values from tile_types.floor
        #fills self.tiles with floor tiles
        self.tiles= np.full((width, height), fill_value= tile_types.floor, order= 'F')
        
        #overrides a small area with a wall
        #TODO: Remove as this is a POC
        self.tiles[30:33, 22]= tile_types.wall

    #Restricts player to avoid void
    def in_bounds(self, x: int, y: int) -> bool:
        """Returns True if x and y are inside bounds of map"""
        return 0 <= x < self.width and 0 <= y < self.height
    
    #Render map using Console tiles_rgb method
    def render(self, console: Console) -> None:
        console.rgb[0: self.width, 0: self.height]= self.tiles['dark']
        
        
        

