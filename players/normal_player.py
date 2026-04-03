from interface.interface_tk import Interface
from players.player import Player
from classes.position import Position

class NormalPlayer(Player):
    def __init__(self, name):
        super(NormalPlayer, self).__init__(name)
        self.interface = Interface()
        self.interface.start()
    
    def get_case_played(self):
        """Récupère la case jouée via l'interface graphique"""
        if self.next_shot:
            p = self.next_shot
            self.next_shot = None
            return p
        
        # Afficher un message pour indiquer qu'on attend un clic
        self.interface.afficher_message(f"{self.name} - Cliquez sur une case pour tirer")
        print(f"\n{self.name}, cliquez sur la grille pour choisir votre cible...")
        
        # Attendre un clic sur l'interface
        click = self.interface.wait_for_click(timeout=600)  # 60 secondes de timeout
        
        if click:
            colonne, ligne = click
            print(f"Position sélectionnée : ({chr(65 + colonne)}{ligne})")
            return Position(colonne, ligne)
        else:
            print("Timeout - aucun clic détecté")
            return Position(-1, -1)
    
    def shoot(self):
        """Tire sur la grille ennemie et met à jour l'affichage"""
        pos = self.get_case_played()
        self.last_played_pos = pos
        self.history.add(pos)
        self.last_shot_response = self.enemy_grid.shoot(pos.get_x(), pos.get_y())
        
        # Colorier la case selon le résultat
        if self.last_shot_response.get_success() == 1:  # Touché
            self.interface.colorier_case(pos.get_x(), pos.get_y(), "red")
        elif self.last_shot_response.get_success() == 0:  # Raté
            self.interface.colorier_case(pos.get_x(), pos.get_y(), "lightblue")
        
        return self.last_shot_response

