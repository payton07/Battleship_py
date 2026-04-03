import random
from classes.variable import Variable
from classes.position import Position
from classes.orientation import Orientation
from classes.ship import Ship
from classes.response import Response
from players.cheat_bot import CheatBot


class Game:
    def __init__(self):
        self.players = []
        self.turn = 0
        self.ship_sizes = Variable.get_ship_sizes()

    def add_player(self, player):
        self.players.append(player)

    def play(self, player):
        """
        Effectue UN TIR pour le joueur donné, s'il a le droit de jouer.
        Ne passe pas au tour suivant automatiquement.
        """
        if not self.players:
            return Variable.MESSAGE_PAS_DE_JOUEUR
        
        try:
            player_index = self.players.index(player)
        except ValueError:
            return Variable.MESSAGE_JOUEUR_NON_TROUVE

        if player_index == self.turn:
            # Le joueur tire
            message = player.shoot().get_message()
            
            # On retourne le message du tir
            return message

        return Variable.MESSAGE_TOUR_ERR.format(player_name=player.get_name())

    def next_turn(self):
        """Passe manuellement au joueur suivant."""
        if self.players:
            self.turn = (self.turn + 1) % len(self.players)

    def place_ships(self, player, ships_to_place):
        grid = player.get_my_grid()
        for ship in ships_to_place:
            grid.place_ship(ship)

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
