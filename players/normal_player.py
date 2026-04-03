from interface.interface_tk import Interface
from players.player import Player

class NormalPlayer(Player):
    def __init__(self, name):
        super(NormalPlayer, self).__init__(name)
        self.interface = Interface()
