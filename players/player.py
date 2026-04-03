from classes.grid import Grid
from classes.position import Position
from classes.variable import Variable

class Player:
    def __init__(self, name, my_grid=None, enemy_grid=None):
        self.name = name
        self.my_grid = my_grid if my_grid else Grid()
        self.enemy_grid = enemy_grid if enemy_grid else Grid()
        self.history = set()
        self.next_shot = None
        self.last_played_pos = None
        self.last_shot_response = None

    def set_next_shot(self, x, y):
        self.next_shot = Position(x, y)

    def get_last_shot_response(self):
        return self.last_shot_response

    def get_case_played(self):
        if self.next_shot:
            p = self.next_shot
            self.next_shot = None
            return p
        
        try:
            # Plus de chaines en dur : utilisation de Variable
            prompt = Variable.PROMPT_TIR.format(player_name=self.name)
            position_input = input(prompt)
            if not position_input or len(position_input) < 2:
                return Position(-1, -1)
            
            x = Variable.get_number(position_input[0])
            try:
                y = int(position_input[1:])
                return Position(x, y)
            except ValueError:
                return Position(x, -1)
        except EOFError:
            return Position(-1, -1)

    def shoot(self):
        pos = self.get_case_played()
        self.last_played_pos = pos
        self.history.add(pos)
        self.last_shot_response = self.enemy_grid.shoot(pos.get_x(), pos.get_y())
        return self.last_shot_response

    def get_my_grid(self):
        return self.my_grid

    def set_enemy_grid(self, enemy_grid):
        self.enemy_grid = enemy_grid

    def get_enemy_grid(self):
        return self.enemy_grid

    def get_name(self):
        return self.name

    def is_inside(self, x, y):
        """Vérifie si une coordonnée est dans la grille."""
        return Variable.is_inside(x, y)

    def get_valid_neighbors(self, x, y):
        """Retourne les positions adjacentes valides (dans la grille)."""
        valid_neighbors = []
        for neighbor in Position(x, y).get_neighbors():
            if self.is_inside(neighbor.get_x(), neighbor.get_y()):
                valid_neighbors.append(neighbor)
        return valid_neighbors
