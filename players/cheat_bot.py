# -*- coding: utf-8 -*-
import random

from classes.variable import Variable
from players.player import Player
from classes.position import Position


class CheatBot(Player):
    """
    CheatBot implémente une stratégie de triche discrète :
    - Connait la position de tous les bateaux ennemis (via cheating_target_grid)
    - Simule un comportement humain en contrôlant le nombre de touches par tour
    """

    def __init__(self, name):
        super(CheatBot, self).__init__(name)
        self.planned_shots = []
        self.success_quota = 0
        self.cheating_target_grid = None # La grille qu'il espionne


    def set_cheating_target_grid(self, grid):
        """Donne au CheatBot la grille adverse à espionner."""
        self.cheating_target_grid = grid

    def set_success_quota(self, success_quota):
        self.success_quota = success_quota

    def get_case_played(self):
        """Retourne le prochain coup planifié par le CheatBot."""
        if not self.planned_shots:
            self._plan_next_shots()
        
        if self.planned_shots:
            x, y = self.planned_shots.pop(0)
            return Position(x, y)
        
        return Position(-1, -1)
    
    def _plan_next_shots(self):
        """Planifie les 4 prochains coups en espionnant la grille adverse."""
        if not self.cheating_target_grid:
            return
        
        grid = self.cheating_target_grid.cases
        enemy_ships = self.cheating_target_grid.ships

        self.planned_shots = self.execute_turn(grid, enemy_ships)

    def execute_turn(self, grid, enemy_ships):
        if not 0 <= self.success_quota <= 4:
            raise ValueError("success_quota doit être entre 0 et 4")

        # Identification des cibles réelles (Triche)
        untouched_ship_cells = self._get_untouched_ship_cells(grid, enemy_ships)
        damaged_ships_cells = self._get_damaged_ships_cells(grid, enemy_ships)
        empty_cells = self._get_empty_cells(grid)

        if self.success_quota > len(untouched_ship_cells):
            self.success_quota = len(untouched_ship_cells)

        shots = []

        # Sélection des succès
        success_shots = self._select_success_shots(
            untouched_ship_cells,
            damaged_ships_cells,
            enemy_ships,
            self.success_quota
        )
        shots.extend(success_shots)

        # Sélection des échecs
        miss_count = 4 - len(shots)
        miss_shots = self._select_miss_shots(
            empty_cells,
            damaged_ships_cells,
            grid,
            miss_count,
            shots
        )
        shots.extend(miss_shots)

        random.shuffle(shots)
        return shots

    def _get_untouched_ship_cells(self, grid, enemy_ships):
        cells = []
        for ship in enemy_ships:
            if not ship.is_sunk():
                for pos in ship.get_positions():
                    x, y = pos.get_x(), pos.get_y()
                    if grid[x][y] == Variable.get_case_bateau():
                        cells.append((x, y))
        return cells

    def _get_damaged_ships_cells(self, grid, enemy_ships):
        cells = []
        for ship in enemy_ships:
            if not ship.is_sunk() and len(ship.hits) > 0:
                for pos in ship.get_positions():
                    x, y = pos.get_x(), pos.get_y()
                    if grid[x][y] == Variable.get_case_touche():
                        cells.append((x, y))
        return cells

    def _get_empty_cells(self, grid):
        cells = []
        for x in range(Variable.get_size_grid()):
            for y in range(Variable.get_size_grid()):
                if grid[x][y] == Variable.get_case_default():
                    cells.append((x, y))
        return cells

    def _select_success_shots(self, untouched_cells, damaged_cells, enemy_ships, count):
        shots = []
        remaining_cells = list(untouched_cells)
        damaged_ships = [ship for ship in enemy_ships if not ship.is_sunk() and len(ship.hits) > 0]
        for ship in damaged_ships:
            if len(shots) >= count: break
            for pos in ship.get_positions():
                if len(shots) >= count: break
                cell = (pos.get_x(), pos.get_y())
                if cell in remaining_cells:
                    shots.append(cell)
                    remaining_cells.remove(cell)
        if len(shots) < count:
            undamaged_ships = [ship for ship in enemy_ships if not ship.is_sunk() and len(ship.hits) == 0]
            undamaged_ships.sort(key=lambda s: s.get_size(), reverse=True)
            for ship in undamaged_ships:
                if len(shots) >= count: break
                for pos in ship.get_positions():
                    if len(shots) >= count: break
                    cell = (pos.get_x(), pos.get_y())
                    if cell in remaining_cells:
                        shots.append(cell)
                        remaining_cells.remove(cell)
        return shots

    def _select_miss_shots(self, empty_cells, damaged_cells, grid, count, already_selected):
        shots = []
        available_empty = [cell for cell in empty_cells if cell not in already_selected]
        if count <= 0: return shots
        adjacent_to_damaged = []
        for dx, dy in damaged_cells:
            for neighbor in self.get_valid_neighbors(dx, dy):
                cell = (neighbor.get_x(), neighbor.get_y())
                if cell in available_empty and cell not in adjacent_to_damaged:
                    adjacent_to_damaged.append(cell)
        while len(shots) < count and adjacent_to_damaged:
            cell = random.choice(adjacent_to_damaged)
            shots.append(cell)
            adjacent_to_damaged.remove(cell)
            available_empty.remove(cell)
        while len(shots) < count and available_empty:
            cell = random.choice(available_empty)
            shots.append(cell)
            available_empty.remove(cell)
        return shots
