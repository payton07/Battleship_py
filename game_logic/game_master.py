# -*- coding: utf-8 -*-
from __future__ import print_function
import random

from game_logic.game import Game
from players.cheat_bot import CheatBot
from players.player import Player
from players.physical_player import PhysicalPlayer
from classes.variable import Variable
from classes.predefined_grids import PredefinedGrids
from classes.grid import Grid
from classes.ship import Ship
from classes.position import Position
from classes.orientation import Orientation

class GameMaster(object):
    def __init__(self):
        self.game = Game()
        self.players = []
        self.human_player = None
        self.bot_player = None
        self.is_hybrid = False

    def setup_players(self, hybrid=False):
        """Initialise les joueurs."""
        self.players = []
        self.is_hybrid = hybrid
        
        if self.is_hybrid:
            self.human_player = PhysicalPlayer(Variable.DEFAULT_PLAYER_HUMAN)
        else:
            self.human_player = Player(Variable.DEFAULT_PLAYER_HUMAN)
            
        # Par défaut, on joue contre le CheatBot
        self.bot_player = CheatBot(Variable.CHEAT_BOT_NAME)

        self.players.append(self.human_player)
        self.players.append(self.bot_player)

        for player in self.players:
            self.game.add_player(player)

        # SI LE BOT EST UN CHEATBOT ET QUE L'HUMAIN EST DIGITAL :
        # On lui donne accès à la grille pour qu'il puisse tricher
        if isinstance(self.bot_player, CheatBot) and not self.is_hybrid:
            self.bot_player.set_target_grid(self.human_player.get_my_grid())

    def apply_grid_choice(self, player, index):
        """Applique une grille prédéfinie à un joueur."""
        config = PredefinedGrids.get_grid(index)
        self.game.place_predefined_ships(player, config)

    def select_human_grid_console(self):
        """Gère la boucle de sélection de grille en mode console."""
        if self.is_hybrid:
            print("\nMode Hybride : Préparez votre grille sur papier.")
            return

        choice = 0
        validating = False
        while not validating:
            temp_grid = Grid()
            config = PredefinedGrids.get_grid(choice)
            for size, x, y, orient_val in config:
                ship = Ship(size, Position(x, y), Orientation(orient_val))
                temp_grid.place_ship(ship)
            
            print(Variable.MESSAGE_APERÇU_TITRE.format(index=choice))
            print(temp_grid)
            
            try:
                try:
                    user_input = raw_input(Variable.PROMPT_CHOIX_GRILLE).strip().upper()
                except NameError:
                    user_input = input(Variable.PROMPT_CHOIX_GRILLE).strip().upper()
            except EOFError:
                break
            
            if user_input == 'V':
                validating = True
                self.apply_grid_choice(self.human_player, choice)
            elif user_input == 'N':
                choice = (choice + 1) % 10
            else:
                try:
                    new_choice = int(user_input)
                    if 0 <= new_choice <= 9:
                        choice = new_choice
                except ValueError:
                    pass

    def play_shot(self, player, x=None, y=None):
        """Exécute un tir pour un joueur."""
        if x is not None and y is not None:
            player.set_next_shot(x, y)
        
        result = self.game.play(player)
        return result

    def execute_turn(self, player):
        """Exécute le tour complet d'un joueur."""
        # Si c'est le Bot qui triche, on définit son quota de succès pour ce tour
        if player == self.bot_player and isinstance(player, CheatBot):
            # Quota aléatoire entre 0 et 3 succès sur 4 tirs pour paraître naturel
            player.set_success_quota(random.randint(0, 3))

        results = []
        for _ in range(Variable.SHOTS_PER_TURN):
            res = self.play_shot(player)
            results.append(res)
            if self.is_game_over():
                break
        
        self.game.next_turn()
        return results

    def repeat_bot_shot(self):
        """Demande au bot de répéter son dernier tir."""
        if hasattr(self.bot_player, 'repeat_last_shot'):
            return self.bot_player.repeat_last_shot()
        return False

    def is_game_over(self):
        """Vérifie si la partie est terminée."""
        return self.game.is_game_over().get_success() == 1

    def get_winner_message(self):
        """Retourne le message du gagnant."""
        return self.game.is_game_over().get_message()

    def display_and_check_results(self, player, results):
        """Affiche les résultats d'un tour."""
        for res in results:
            print(Variable.MESSAGE_JOUEUR_ACTION.format(
                player_name=player.get_name(), 
                result=res
            ))
            if self.is_game_over():
                print(Variable.MESSAGE_FIN_PARTIE)
                print(self.get_winner_message())
                return True
        return False

    def run(self):
        """Boucle de jeu console."""
        print("\n--- Configuration ---")
        print("1. Mode Digital (Humain sur PC vs CheatBot)")
        print("2. Mode Hybride (Humain sur Papier vs Bot)")
        
        try:
            try:
                mode = raw_input("Votre choix : ").strip()
            except NameError:
                mode = input("Votre choix : ").strip()
            
            self.setup_players(hybrid=(mode == "2"))
            self.select_human_grid_console()
            
            # Placement des bateaux du bot
            self.game.place_all_ships(self.bot_player)
            
            print(Variable.MESSAGE_DEBUT_PARTIE)
            
            while not self.is_game_over():
                # Tour Humain
                print("\n--- C'est votre tour ({} tirs) ---".format(Variable.SHOTS_PER_TURN))
                if self.display_and_check_results(self.human_player, self.execute_turn(self.human_player)):
                    return

                # Tour Bot
                print("\n--- C'est le tour du Bot ---")
                if self.display_and_check_results(self.bot_player, self.execute_turn(self.bot_player)):
                    return
        except KeyboardInterrupt:
            print("\nPartie interrompue.")
