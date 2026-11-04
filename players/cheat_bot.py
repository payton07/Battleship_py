# -*- coding: utf-8 -*-
import random
from classes.variable import Variable
from players.player import Player
from classes.position import Position

class CheatBot(Player):
    """
    CheatBot implémente une stratégie de triche discrète :
    - Peut consulter la grille ennemie si elle est disponible (mode digital)
    - Simule un comportement humain en contrôlant le nombre de touches par tour
    """

    def __init__(self, name):
        super(CheatBot, self).__init__(name)
        self.planned_shots = []
        self.success_quota = 2
        self.target_grid = None

    def set_target_grid(self, grid):
        self.target_grid = grid

    def set_success_quota(self, quota):
        self.success_quota = quota

    def get_case_played(self):
        if self.target_grid and not self.planned_shots:
            self._plan_next_shots()

        if self.planned_shots:
            x, y = self.planned_shots.pop(0)
            self.last_played_pos = Position(x, y)
            return self.last_played_pos

        size = Variable.get_size_grid()
        while True:
            x = random.randint(0, size - 1)
            y = random.randint(0, size - 1)
            pos = Position(x, y)
            if pos not in self.history:
                self.last_played_pos = pos
                return pos

    def _plan_next_shots(self):
        if not self.target_grid:
            return
        self.planned_shots = self.execute_turn(
            self.target_grid.cases, self.target_grid.ships
        )

    def execute_turn(self, grid, enemy_ships):
        if not 0 <= self.success_quota <= 4:
            self.success_quota = 2

        untouched_ship_cells = []
        for ship in enemy_ships:
            if not ship.is_sunk():
                for pos in ship.get_positions():
                    if grid[pos.get_x()][pos.get_y()] == Variable.get_case_bateau():
                        untouched_ship_cells.append((pos.get_x(), pos.get_y()))

        empty_cells = []
        for x in range(Variable.get_size_grid()):
            for y in range(Variable.get_size_grid()):
                if grid[x][y] == Variable.get_case_default():
                    empty_cells.append((x, y))

        quota = min(self.success_quota, len(untouched_ship_cells))

        shots = []
        if untouched_ship_cells:
            random.shuffle(untouched_ship_cells)
            shots.extend(untouched_ship_cells[:quota])

        if empty_cells:
            random.shuffle(empty_cells)
            for cell in empty_cells:
                if len(shots) >= Variable.SHOTS_PER_TURN:
                    break
                if cell not in shots:
                    shots.append(cell)

        random.shuffle(shots)
        return shots

    def receive_shot(self, x, y):
        return super().receive_shot(x, y)
