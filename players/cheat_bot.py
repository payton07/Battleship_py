# -*- coding: utf-8 -*-
import random

from classes.variable import Variable
from players.player import Player
from classes.position import Position


class CheatBot(Player):
    """
    CheatBot implémente une stratégie de triche discrète :
    - Connait la position de tous les bateaux ennemis
    - Simule un comportement humain en contrôlant le nombre de touches par tour
    - Tire 4 coups par tour avec un quota de succès défini
    """

    def __init__(self, name):
        super(CheatBot, self).__init__(name)
        self.planned_shots = []
        self.success_quota = 0


    def set_success_quota(self, success_quota):
        self.success_quota = success_quota

    def get_case_played(self):
        """
        Retourne le prochain coup planifié par le CheatBot.
        Si aucun coup n'est planifié, génère une série de 4 coups.
        
        Returns:
            Position: Les coordonnées du prochain tir
        """
        if not self.planned_shots:
            self._plan_next_shots()
        
        if self.planned_shots:
            x, y = self.planned_shots.pop(0)
            return Position(x, y)
        
        return Position(-1, -1)
    
    def _plan_next_shots(self):
        """
        Planifie les 4 prochains coups en utilisant la grille ennemie.
        Utilise un quota de succès par défaut de 2 touches sur 4 tirs.
        """
        if not self.enemy_grid:
            return
        
        grid = self.enemy_grid.cases
        enemy_ships = self.enemy_grid.ships

        self.planned_shots = self.execute_turn(grid, enemy_ships)

    def execute_turn(self, grid, enemy_ships):
        """
        Exécute un tour de jeu avec un quota de succès défini.

        Args:
            grid: Grille de jeu (cases avec ~, X, *, O)
            enemy_ships: Liste des bateaux ennemis

        Returns:
            Liste de 4 tuples (x, y) représentant les coordonnées des tirs
        """
        print(enemy_ships)
        if not 0 <= self.success_quota <= 4:
            raise ValueError("success_quota doit être entre 0 et 4")

        # Identification des cibles disponibles
        untouched_ship_cells = self._get_untouched_ship_cells(grid, enemy_ships)
        damaged_ships_cells = self._get_damaged_ships_cells(grid, enemy_ships)
        empty_cells = self._get_empty_cells(grid)

        # Vérifier si le quota est réalisable
        if self.success_quota > len(untouched_ship_cells):
            self.success_quota = untouched_ship_cells

        shots = []

        # Sélection des succès (N = success_quota)
        success_shots = self._select_success_shots(
            untouched_ship_cells,
            damaged_ships_cells,
            enemy_ships,
            self.success_quota
        )
        shots.extend(success_shots)

        # Sélection des échecs (4 - N tirs)
        miss_count = 4 - self.success_quota
        miss_shots = self._select_miss_shots(
            empty_cells,
            damaged_ships_cells,
            grid,
            miss_count,
            shots
        )
        shots.extend(miss_shots)

        # Mélanger pour plus de naturel
        random.shuffle(shots)

        return shots

    def _get_untouched_ship_cells(self, grid, enemy_ships):
        """Retourne les coordonnées des cases de bateaux non touchées (O)."""
        cells = []
        for ship in enemy_ships:
            if not ship.is_sunk():
                for pos in ship.get_positions():
                    x, y = pos.get_x(), pos.get_y()
                    if grid[x][y] == Variable.get_case_bateau():
                        cells.append((x, y))
        return cells

    def _get_damaged_ships_cells(self, grid, enemy_ships):
        """Retourne les coordonnées touchées (X) des bateaux non coulés."""
        cells = []
        for ship in enemy_ships:
            if not ship.is_sunk() and len(ship.hits) > 0:
                for pos in ship.get_positions():
                    x, y = pos.get_x(), pos.get_y()
                    if grid[x][y] == Variable.get_case_touche():
                        cells.append((x, y))
        return cells

    def _get_empty_cells(self, grid):
        """Retourne les coordonnées des cases vides (~)."""
        cells = []
        for x in range(Variable.get_size_grid()):
            for y in range(Variable.get_size_grid()):
                if grid[x][y] == Variable.get_case_default():
                    cells.append((x, y))
        return cells

    def _select_success_shots(self, untouched_cells, damaged_cells, enemy_ships, count):
        """Sélectionne les tirs qui doivent toucher (avec priorités)."""
        shots = []
        remaining_cells = list(untouched_cells)

        # Priorité 1 : Cases O des bateaux déjà endommagés
        damaged_ships = [ship for ship in enemy_ships if not ship.is_sunk() and len(ship.hits) > 0]
        for ship in damaged_ships:
            if len(shots) >= count:
                break
            for pos in ship.get_positions():
                if len(shots) >= count:
                    break
                cell = (pos.get_x(), pos.get_y())
                if cell in remaining_cells:
                    shots.append(cell)
                    remaining_cells.remove(cell)

        # Priorité 2 : Cases O des plus grands navires restants
        if len(shots) < count:
            undamaged_ships = [ship for ship in enemy_ships if not ship.is_sunk() and len(ship.hits) == 0]
            undamaged_ships.sort(key=lambda s: s.get_size(), reverse=True)

            for ship in undamaged_ships:
                if len(shots) >= count:
                    break
                for pos in ship.get_positions():
                    if len(shots) >= count:
                        break
                    cell = (pos.get_x(), pos.get_y())
                    if cell in remaining_cells:
                        shots.append(cell)
                        remaining_cells.remove(cell)

        return shots

    def _select_miss_shots(self, empty_cells, damaged_cells, grid, count, already_selected):
        """Sélectionne les tirs qui doivent rater (avec discrétion)."""
        shots = []
        available_empty = [cell for cell in empty_cells if cell not in already_selected]

        if count == 0:
            return shots

        # Priorité 1 : Cases adjacentes aux bateaux endommagés (discrétion)
        adjacent_to_damaged = []
        for dx, dy in damaged_cells:
            for adj_x, adj_y in self._get_adjacent_positions(dx, dy):
                cell = (adj_x, adj_y)
                if cell in available_empty and cell not in adjacent_to_damaged:
                    adjacent_to_damaged.append(cell)

        # Sélectionner parmi les cases adjacentes
        while len(shots) < count and adjacent_to_damaged:
            cell = random.choice(adjacent_to_damaged)
            shots.append(cell)
            adjacent_to_damaged.remove(cell)
            available_empty.remove(cell)

        # Priorité 2 : Cases aléatoires loin de tout bateau
        while len(shots) < count and available_empty:
            cell = random.choice(available_empty)
            shots.append(cell)
            available_empty.remove(cell)

        if len(shots) < count:
            raise ValueError("Pas assez de cases vides disponibles pour compléter les tirs")

        return shots

    def _get_adjacent_positions(self, x, y):
        """Retourne les positions adjacentes valides (haut, bas, gauche, droite)."""
        adjacent = []
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            new_x, new_y = x + dx, y + dy
            if 0 <= new_x < Variable.get_size_grid() and 0 <= new_y < Variable.get_size_grid():
                adjacent.append((new_x, new_y))
        return adjacent
