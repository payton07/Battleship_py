from classes.grid import Grid
from classes.position import Position
from classes.variable import Variable

class Player:
    def __init__(self, name, my_grid=None):
        self.name = name
        self.my_grid = my_grid if my_grid else Grid()
        # La tracking_grid ne contient que des symboles, pas les bateaux réels
        self.tracking_grid = [[Variable.CASE_DEFAULT for _ in range(Variable.SIZE_GRID)] for _ in range(Variable.SIZE_GRID)]
        self.history = set()
        self.next_shot = None
        self.last_played_pos = None
        self.last_shot_response = None

    def set_next_shot(self, x, y):
        self.next_shot = Position(x, y)

    def get_last_shot_response(self):
        return self.last_shot_response

    def get_case_played(self):
        """Demande ou retourne la position du prochain tir."""
        if self.next_shot:
            p = self.next_shot
            self.next_shot = None
            return p
        
        try:
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

    def receive_shot(self, x, y):
        """Reçoit un tir de l'adversaire et retourne le résultat (Touché/Coulé/Raté)."""
        return self.my_grid.shoot(x, y)

    def handle_response(self, x, y, response):
        """Enregistre le résultat d'un tir effectué par le joueur sur sa grille de suivi."""
        self.last_played_pos = Position(x, y)
        self.history.add(self.last_played_pos)
        self.last_shot_response = response
        
        success = response.get_success()
        if success >= 1: # Touché ou Coulé
            self.tracking_grid[x][y] = Variable.CASE_TOUCHE
        elif success == 0: # Raté
            self.tracking_grid[x][y] = Variable.CASE_RATE

    def get_my_grid(self):
        return self.my_grid

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
