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
        """Planifie les tirs selon un quota de succès et l'état des bateaux."""
        if not 0 <= self.success_quota <= Variable.SHOTS_PER_TURN:
            self.success_quota = 2
        size = Variable.get_size_grid()

        # Cases vides (eau intacte)
        water_cells = []
        for x in range(size):
            for y in range(size):
                if grid[x][y] == Variable.get_case_default():
                    water_cells.append((x, y))

        # Cases de bateaux encore intactes, regroupées par bateau
        ship_cells_by_ship = []
        for ship in enemy_ships:
            ship_cells = []
            for pos in ship.get_positions():
                x, y = pos.get_x(), pos.get_y()
                if grid[x][y] == Variable.get_case_bateau():
                    ship_cells.append((x, y))
            if ship_cells:
                ship_cells_by_ship.append((ship, ship_cells))

        total_ship_cells = sum(len(cells) for _, cells in ship_cells_by_ship)
        success_quota = min(self.success_quota, Variable.SHOTS_PER_TURN, total_ship_cells)

        shots = []
        selected = set()

        # Bateau touché = a des hits et n'est pas coulé
        touched_ships = [
            ship for ship, cells in ship_cells_by_ship
            if ship.hits and not ship.is_sunk()
        ]
        has_touched_ship = bool(touched_ships)

        # 1. Si aucun bateau n'est touché, commencer par des tirs ratés aléatoires
        if not has_touched_ship:
            misses_needed = Variable.SHOTS_PER_TURN - success_quota
            random.shuffle(water_cells)
            for cell in water_cells:
                if len(shots) >= misses_needed:
                    break
                shots.append(cell)
                selected.add(cell)

        # 2. Tirer les coups réussis, en commençant par un bateau touché si possible
        remaining_successes = success_quota
        if remaining_successes > 0 and ship_cells_by_ship:
            if has_touched_ship:
                primary_ship = touched_ships[0]
            else:
                ships_with_enough = [
                    ship for ship, cells in ship_cells_by_ship
                    if len(cells) >= remaining_successes
                ]
                if ships_with_enough:
                    primary_ship = random.choice(ships_with_enough)
                else:
                    primary_ship = max(
                        ship_cells_by_ship, key=lambda item: len(item[1])
                    )[0]

            ship_cells_map = {ship: list(cells) for ship, cells in ship_cells_by_ship}
            ship_order = [primary_ship] + [
                ship for ship, _ in ship_cells_by_ship if ship is not primary_ship
            ]

            for ship in ship_order:
                if remaining_successes <= 0:
                    break
                cells = ship_cells_map.get(ship, [])
                if not cells:
                    continue
                random.shuffle(cells)
                for cell in cells:
                    if remaining_successes <= 0:
                        break
                    if cell in selected:
                        continue
                    shots.append(cell)
                    selected.add(cell)
                    remaining_successes -= 1

        # 3. Compléter les tirs restants de façon aléatoire (priorité à l'eau)
        remaining = Variable.SHOTS_PER_TURN - len(shots)
        if remaining > 0:
            remaining_water = [cell for cell in water_cells if cell not in selected]
            random.shuffle(remaining_water)
            for cell in remaining_water:
                if len(shots) >= Variable.SHOTS_PER_TURN:
                    break
                shots.append(cell)
                selected.add(cell)

            remaining = Variable.SHOTS_PER_TURN - len(shots)
            if remaining > 0:
                remaining_ship_cells = []
                for _, cells in ship_cells_by_ship:
                    for cell in cells:
                        if cell not in selected:
                            remaining_ship_cells.append(cell)
                random.shuffle(remaining_ship_cells)
                for cell in remaining_ship_cells:
                    if len(shots) >= Variable.SHOTS_PER_TURN:
                        break
                    shots.append(cell)
                    selected.add(cell)

        return shots

    def receive_shot(self, x, y):
        return super().receive_shot(x, y)
