from players.player import Player
from classes.position import Position
from classes.variable import Variable
import random

class SmartBot(Player):
    def __init__(self, name):
        super(SmartBot, self).__init__(name)
        self.potential_targets = []

    def get_case_played(self):
        # 1. Si le dernier tir était un succès, on ajoute des cibles adjacentes
        if self.last_shot_response and self.last_shot_response.get_success() >= 1:
            self.add_adjacent_targets(self.last_played_pos)

        # 2. Mode Ciblage : On teste les cibles potentielles
        while self.potential_targets:
            target = self.potential_targets.pop()
            if self.is_valid_and_not_played(target):
                return target

        # 3. Mode Chasse : Tir aléatoire si pas de cible
        size = Variable.get_size_grid()
        while True:
            x = random.randint(0, size - 1)
            y = random.randint(0, size - 1)
            pos = Position(x, y)
            if pos not in self.history:
                return pos

    def add_adjacent_targets(self, pos):
        """Ajoute les voisins valides aux cibles potentielles."""
        for neighbor in self.get_valid_neighbors(pos.get_x(), pos.get_y()):
            if neighbor not in self.history:
                self.potential_targets.append(neighbor)

    def is_valid_and_not_played(self, pos):
        """Vérifie si la position est valide et n'a pas encore été jouée."""
        return self.is_inside(pos.get_x(), pos.get_y()) and pos not in self.history
