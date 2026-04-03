# -*- coding: utf-8 -*-
from classes.grid import Grid
from classes.position import Position
from classes.variable import Variable

class Player(object): # New-style class for Python 2.7
    def __init__(self, name, my_grid=None):
        self.name = name
        self.my_grid = my_grid if my_grid else Grid()
        self.tracking_grid = Grid() # Grille pour noter ses propres tirs
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
            prompt = Variable.PROMPT_TIR.format(player_name=self.name)
            # Compatibilité Python 2.7
            try:
                position_input = raw_input(prompt).strip()
            except NameError:
                position_input = input(prompt).strip()
                
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
        """Reçoit un tir de l'adversaire et retourne la réponse."""
        return self.my_grid.shoot(x, y)

    def get_my_grid(self):
        return self.my_grid

    def get_tracking_grid(self):
        return self.tracking_grid

    def get_name(self):
        return self.name

    def is_inside(self, x, y):
        return Variable.is_inside(x, y)

    def get_valid_neighbors(self, x, y):
        valid_neighbors = []
        for neighbor in Position(x, y).get_neighbors():
            if self.is_inside(neighbor.get_x(), neighbor.get_y()):
                valid_neighbors.append(neighbor)
        return valid_neighbors
