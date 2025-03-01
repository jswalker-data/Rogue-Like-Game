from entity import Entity

player = Entity(
    char="@", colour=(255, 255, 255), name="Player", block_movements=True
)

orc = Entity(
    char="o", colour=(63, 127, 63), name="Orc", block_movements=True
)
troll = Entity(
    char="T", colour=(0, 127, 0), name="Troll", block_movements=True
)
