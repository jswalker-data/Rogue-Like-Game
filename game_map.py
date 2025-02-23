"""
Overall approcah is filling the room with walls and then carving out
a path and room for us to navigate

Most generation will occur in procgen.py as we may want multiple alternate 
generators for different room types

//TODO: Thinking like Boss rooms every 5 or something with unique outlines?
//TODO: Maybe easter egg rooms as well, every x rooms or use an rng string


"""

import numpy as np
from tcod.console import Console

import tile_types




class GameMap:
    def __init__(self, width: int, height: int):
        self.width, self.height= width, height
        
        #Create a 2D array filled with same values from tile_types.floor
        #fills self.tiles with floor tiles
        self.tiles= np.full((width, height), fill_value= tile_types.wall, order= 'F')
        
        #Add new np frames for currently visible and previously seen
        self.visible=  np.full((width, height), fill_value= False, order= 'F')
        self.explored=  np.full((width, height), fill_value= False, order= 'F')
        

    #Restricts player to avoid void
    def in_bounds(self, x: int, y: int) -> bool:
        """Returns True if x and y are inside bounds of map"""
        return 0 <= x < self.width and 0 <= y < self.height
    
    #Render map using Console tiles_rgb method
    def render(self, console: Console) -> None:
        """
        Render the map based on passable and iterable parameters
        
        Visible:
            Drawn with light colours
        
        Non visible but explored:
            Draw in dark colours to show where we've seen
            
        Non visible and not explored:
            Default to the SHROUD type
        """

        #Set the console to be conditionally drawn (np.select) based on condlist
        console.rgb[0: self.width, 0: self.height]= np.select(
            
            #Check if tile is visibile or explored then uses corresponding value
            condlist= [self.visible, self.explored],
            choicelist= [self.tiles['light'], self.tiles['dark']],
            
            #If neither true in condlist sets default
            default= tile_types.SHROUD
        )





