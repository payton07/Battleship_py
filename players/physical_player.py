# -*- coding: utf-8 -*-
from players.player import Player
from classes.variable import Variable
from classes.position import Position
from classes.response import Response

class PhysicalPlayer(Player):
    """
    Joueur physique (humain jouant sur papier).
    Il n'a pas de grille digitale 'my_grid' gérée par le programme.
    Les résultats de ses tirs et des tirs de l'adversaire sont gérés manuellement.
    """
    def __init__(self, name):
        super(PhysicalPlayer, self).__init__(name)
        # La grille personnelle est ignorée (joueur papier)
        self.my_grid = None

    def get_case_played(self):
        """Demande la case jouée à l'utilisateur via la console."""
        try:
            prompt = Variable.PROMPT_TIR.format(player_name=self.name)
            # Compatibilité Python 2.7 (raw_input)
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
        """
        Appelé quand l'adversaire tire sur ce joueur physique.
        On demande à l'humain le résultat réel sur sa grille papier.
        """
        print("\nL'adversaire tire en {}{} !".format(Variable.get_alphabet(x), y))
        print("Quel est le résultat sur votre grille papier ?")
        print("0. Raté")
        print("1. Touché")
        print("2. Coulé")
        
        while True:
            try:
                # Compatibilité Python 2.7
                try:
                    choice = raw_input("Votre réponse (0, 1 ou 2) : ").strip()
                except NameError:
                    choice = input("Votre réponse (0, 1 ou 2) : ").strip()
                
                if choice == "0":
                    return Response(0, Variable.MESSAGE_RATE)
                elif choice == "1":
                    return Response(1, Variable.MESSAGE_TOUCHE)
                elif choice == "2":
                    return Response(2, Variable.MESSAGE_COULE)
                else:
                    print("Choix invalide. Veuillez entrer 0, 1 ou 2.")
            except (ValueError, EOFError):
                print("Erreur de saisie. Réessayez.")

    def all_ships_sunk(self):
        """
        Pour un joueur physique, on demande si tous ses bateaux sont coulés.
        """
        print("\nEst-ce que tous vos bateaux sont coulés ? (O/N)")
        try:
            try:
                ans = raw_input("> ").strip().upper()
            except NameError:
                ans = input("> ").strip().upper()
            return ans == "O"
        except EOFError:
            return False
