import random
from classes.variable import Variable
from classes.position import Position
from classes.orientation import Orientation
from classes.ship import Ship
from classes.response import Response

class Game:
    def __init__(self):
        self.players = []
        self.turn = 0
        self.ship_sizes = Variable.get_ship_sizes()

    def add_player(self, player):
        self.players.append(player)

    def play(self, player):
        """
        Effectue UN TIR pour le joueur donné.
        Le moteur récupère les coordonnées de tir du joueur, 
        les transmet à l'adversaire et renvoie le résultat au tireur.
        """
        if not self.players:
            return Variable.MESSAGE_PAS_DE_JOUEUR
        
        try:
            player_index = self.players.index(player)
        except ValueError:
            return Variable.MESSAGE_JOUEUR_NON_TROUVE

        if player_index == self.turn:
            # 1. Obtenir la cible
            target_pos = player.get_case_played()
            x, y = target_pos.get_x(), target_pos.get_y()

            # 2. Identifier l'adversaire
            opponent_index = (player_index + 1) % len(self.players)
            opponent = self.players[opponent_index]

            # 3. Transmettre le tir et récupérer le résultat
            response = opponent.receive_shot(x, y)

            # 4. Informer le tireur pour qu'il mette à jour son suivi local
            player.handle_response(x, y, response)
            
            # 5. Retourner le message du tir
            return response.get_message()

        return Variable.MESSAGE_TOUR_ERR.format(player_name=player.get_name())

    def next_turn(self):
        if self.players:
            self.turn = (self.turn + 1) % len(self.players)

    def place_predefined_ships(self, player, configuration):
        grid = player.get_my_grid()
        for size, x, y, orientation_val in configuration:
            orient = Orientation(orientation_val)
            ship = Ship(size, Position(x, y), orient)
            grid.place_ship(ship)

    def place_all_ships(self, player):
        grid = player.get_my_grid()
        for size in self.ship_sizes:
            placed = False
            while not placed:
                x = random.randint(0, Variable.get_size_grid() - 1)
                y = random.randint(0, Variable.get_size_grid() - 1)
                pos = Position(x, y)
                orientation = Orientation.HORIZONTAL if random.random() < 0.5 else Orientation.VERTICAL
                ship = Ship(size, pos, orientation)
                placed = grid.place_ship(ship)

    def is_game_over(self):
        for i, player in enumerate(self.players):
            if player.get_my_grid().all_ships_sunk():
                winner_index = (i + 1) % len(self.players)
                winner_name = self.players[winner_index].get_name()
                return Response(1, Variable.MESSAGE_GAGNANT.format(player_name=winner_name))
        return Response(0, Variable.MESSAGE_AUCUN_GAGNANT)
