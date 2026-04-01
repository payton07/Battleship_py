import unittest
from game_logic.game import Game
from players.normal_player import NormalPlayer
from classes.variable import Variable
from classes.ship import Ship
from classes.position import Position
from classes.orientation import Orientation

class TestGameFlow(unittest.TestCase):
    def setUp(self):
        self.game = Game()
        self.p1 = NormalPlayer("P1")
        self.p2 = NormalPlayer("P2")
        self.game.add_player(self.p1)
        self.game.add_player(self.p2)
        self.p1.set_enemy_grid(self.p2.get_my_grid())
        self.p2.set_enemy_grid(self.p1.get_my_grid())
        
        # On donne un bateau à P1 aussi pour qu'il ne soit pas considéré comme perdant par défaut
        ship1 = Ship(1, Position(9, 9), Orientation.HORIZONTAL)
        self.p1.get_my_grid().place_ship(ship1)

    def test_turn_management(self):
        """Vérifie que le tour ne change pas tout seul (pour les 4 tirs)."""
        self.assertEqual(self.game.turn, 0)
        self.p1.set_next_shot(0, 0)
        self.game.play(self.p1)
        self.assertEqual(self.game.turn, 0)
        
        self.game.next_turn()
        self.assertEqual(self.game.turn, 1)

    def test_game_over(self):
        """Vérifie la détection de fin de partie."""
        # On place un petit bateau pour P2 à une position différente
        ship2 = Ship(1, Position(0, 0), Orientation.HORIZONTAL)
        self.p2.get_my_grid().place_ship(ship2)
        
        # P1 tire et coule le seul bateau de P2
        self.p1.set_next_shot(0, 0)
        self.game.play(self.p1)
        
        res = self.game.is_game_over()
        self.assertEqual(res.get_success(), 1)
        # Si P2 n'a plus de bateaux, P1 est le gagnant
        self.assertIn("P1 a gagné", res.get_message())

if __name__ == '__main__':
    unittest.main()
