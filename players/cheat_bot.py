# -*- coding: utf-8 -*-
import random
from classes.variable import Variable
from client.client import Client
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
        self.target_grid = None # La grille qu'on va "espionner"
        self.client_socket = Client("10.161.177.181", server_port=5000)
        self.client_socket.connect()
        # On ne connecte pas ici pour éviter de bloquer l'interface au démarrage

    def set_target_grid(self, grid):
        """Permet au GameMaster de donner l'accès à la grille adverse."""
        self.target_grid = grid

    def set_success_quota(self, quota):
        self.success_quota = quota

    def _send_safe_message(self, message):
        """Tente d'envoyer un message, en se connectant si nécessaire."""
        if not self.client_socket.connected:
            self.client_socket.connect()
        
        if self.client_socket.connected:
            return self.client_socket.send_message(message)
        return False

    def get_case_played(self):
        """
        Si on a une grille à espionner et qu'on n'a pas de coups planifiés, on triche.
        Sinon, on tire au hasard (comportement par défaut si pas de cible).
        """
        # 1. Si on peut tricher (grille digitale ennemie dispo)
        if self.target_grid and not self.planned_shots:
            self._plan_next_shots()
        
        # 2. Si on a des coups planifiés (via triche ou autre)
        if self.planned_shots:
            x, y = self.planned_shots.pop(0)
            self.last_played_pos = Position(x, y)
            self._send_safe_message(f"P{chr(65+x)}{y}")
            return self.last_played_pos
        
        # 3. Comportement de secours (ou mode Physique) : Aléatoire pur
        size = Variable.get_size_grid()
        while True:
            x = random.randint(0, size - 1)
            y = random.randint(0, size - 1)
            pos = Position(x, y)
            if pos not in self.history:
                self.last_played_pos = pos
                self._send_safe_message(f"P{chr(65+x)}{y}")
                return pos

    def repeat_last_shot(self):
        """Renvoie le message socket du dernier tir effectué."""
        if self.last_played_pos:
            x, y = self.last_played_pos.get_x(), self.last_played_pos.get_y()
            return self._send_safe_message(f"P{chr(65+x)}{y}")
        return False
    
    def _plan_next_shots(self):
        """Planifie les 4 prochains coups en analysant la grille cible."""
        if not self.target_grid:
            return
        
        grid_cases = self.target_grid.cases
        enemy_ships = self.target_grid.ships
        
        self.planned_shots = self.execute_turn(grid_cases, enemy_ships)

    def execute_turn(self, grid, enemy_ships):
        """Logique de triche avec quota de succès."""
        if not 0 <= self.success_quota <= 4:
            self.success_quota = 2

        # Cases de bateaux non touchées
        untouched_ship_cells = []
        for ship in enemy_ships:
            if not ship.is_sunk():
                for pos in ship.get_positions():
                    if grid[pos.get_x()][pos.get_y()] == Variable.get_case_bateau():
                        untouched_ship_cells.append((pos.get_x(), pos.get_y()))

        # Cases vides (eau)
        empty_cells = []
        for x in range(Variable.get_size_grid()):
            for y in range(Variable.get_size_grid()):
                if grid[x][y] == Variable.get_case_default():
                    empty_cells.append((x, y))

        # Ajuster le quota si plus assez de bateaux
        quota = min(self.success_quota, len(untouched_ship_cells))
        
        shots = []
        # 1. Sélectionner les succès
        if untouched_ship_cells:
            random.shuffle(untouched_ship_cells)
            shots.extend(untouched_ship_cells[:quota])

        # 2. Sélectionner les échecs pour compléter à 4
        needed = Variable.SHOTS_PER_TURN - len(shots)
        if empty_cells:
            random.shuffle(empty_cells)
            # Éviter de reprendre des cases déjà dans shots
            for cell in empty_cells:
                if len(shots) >= Variable.SHOTS_PER_TURN: break
                if cell not in shots:
                    shots.append(cell)

        random.shuffle(shots)
        return shots

    def receive_shot(self, x, y):
        msg = super().receive_shot(x, y)
        self.client_socket.send_message(msg.get_message()[0])
        return msg
