from typing import Tuple

import numpy as np

#Tile graphic structure compatible with Console.tiles_rgb
#dtype creates a new data structure
graphic_dt = np.dtype(
    [
        ('ch', np.int32),   #Unicode codepoint
        ('fg', '3B'),   #3 unsugned bites for rgb, foreground
        ('bg', '3B')    #3 unsugned bites for rgb, background
    ]
)

#Tile struct for statically defined tile data
#dark is holder for FOV colour manipulation
tile_dt = np.dtype(
    [
        ('walkable', np.bool),  #True if we can walk over the tile
        ('transparent', np.bool),   #True if it doesn't block FOV
        ('dark', graphic_dt)    #Graphic for when not in FOV
        
    ]
)

#Creates Numpy array of one tile_dt element and return it
def new_tile(
    *,  #Enforce keywords, parameter order doesn't matter
    walkable: int,
    transparent: int,
    dark: Tuple[int, Tuple[int, int, int], Tuple[int, int, int]]
) -> np.ndarray:
    """Helper function for defining individual tile types"""
    return np.array((walkable, transparent, dark), dtype= tile_dt)

#Can use ' ' or '#' for space character, foreground white (wont matter)
#and background colours slightly different so we can differentiate at this point
floor = new_tile(
    walkable= True, transparent= True, dark=(ord(' '), (255, 255, 255), (50, 50, 150))
)

wall = new_tile(
    walkable= False, transparent= False, dark=(ord('#'), (255, 255, 255), (0, 0, 100))
)
