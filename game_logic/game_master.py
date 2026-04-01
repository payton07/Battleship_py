from game_logic.game import Game
from players.normal_player import NormalPlayer
from players.smart_bot import SmartBot
from classes.variable import Variable
from classes.predefined_grids import PredefinedGrids
from classes.grid import Grid
from classes.ship import Ship
from classes.position import Position
from classes.orientation import Orientation

class GameMaster:
    def __init__(self):
        self.game = None
        self.players = []

    def init_game(self):
        """Initialise la partie en mode Humain vs Smart Bot."""
        self.players = []
        self.game = Game()

        # Création des joueurs
        self.players.append(NormalPlayer(Variable.DEFAULT_PLAYER_HUMAN))
        self.players.append(SmartBot(Variable.DEFAULT_BOT_NAME))

        for player in self.players:
            self.game.add_player(player)

        # Liaison des grilles pour l'adversité
        if len(self.players) >= 2:
            self.players[0].set_enemy_grid(self.players[1].get_my_grid())
            self.players[1].set_enemy_grid(self.players[0].get_my_grid())

        # Système de choix de grille pour l'humain
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
            user_input = input(Variable.PROMPT_CHOIX_GRILLE).strip().upper()
            
            if user_input == 'V':
                validating = True
                print(Variable.MESSAGE_GRILLE_VALIDEE.format(index=choice))
            elif user_input == 'N':
                choice = (choice + 1) % 10
            else:
                try:
                    new_choice = int(user_input)
                    if 0 <= new_choice <= 9:
                        choice = new_choice
                except ValueError:
                    pass
        
        self.game.place_predefined_ships(self.players[0], config)
        self.game.place_all_ships(self.players[1])

    def run(self):
        """Lance la boucle de jeu avec 4 tirs par tour."""
        self.init_game()
        print(Variable.MESSAGE_DEBUT_PARTIE)
        
        while self.game.is_game_over().get_success() == 0:
            for player in self.players:
                print(f"\n--- C'est le tour de {player.get_name()} ({Variable.SHOTS_PER_TURN} tirs) ---")
                
                for shot_num in range(1, Variable.SHOTS_PER_TURN + 1):
                    print(f"Tir n°{shot_num} :")
                    result = self.game.play(player)
                    
                    if result and not result.startswith(Variable.MESSAGE_TOUR_ERR[:5]):
                        print(Variable.MESSAGE_JOUEUR_ACTION.format(
                            player_name=player.get_name(), 
                            result=result
                        ))
                    
                    # Vérification immédiate de fin de partie
                    if self.game.is_game_over().get_success() == 1:
                        print(Variable.MESSAGE_FIN_PARTIE)
                        print(self.game.is_game_over().get_message())
                        return
                
                # Après ses 4 tirs, on passe au tour du joueur suivant
                self.game.next_turn()
