from players.player import Player
from classes.position import Position
from classes.variable import Variable
import random

class Bot(Player):
    def __init__(self, name):
        super(Bot, self).__init__(name)

    def get_case_played(self):
        size = Variable.get_size_grid()
        while True:
            x = random.randint(0, size - 1)
            y = random.randint(0, size - 1)
            pos = Position(x, y)
            if pos not in self.history:
                return pos
