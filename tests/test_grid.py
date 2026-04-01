import unittest
from classes.grid import Grid
from classes.ship import Ship
from classes.position import Position
from classes.orientation import Orientation
from classes.variable import Variable

class TestGrid(unittest.TestCase):
    def setUp(self):
        # On s'assure que la taille est 10 pour les tests
        Variable.SIZE_GRID = 10
        self.grid = Grid()

    def test_is_inside(self):
        """Vérifie si la grille détecte bien les bords."""
        self.assertTrue(self.grid.is_inside(0, 0))
        self.assertTrue(self.grid.is_inside(9, 9))
        self.assertFalse(self.grid.is_inside(-1, 0))
        self.assertFalse(self.grid.is_inside(10, 0))

    def test_place_ship_success(self):
        """Vérifie le placement d'un bateau valide."""
        ship = Ship(3, Position(0, 0), Orientation.HORIZONTAL)
        self.assertTrue(self.grid.place_ship(ship))
        # Vérifie si la case est occupée
        self.assertEqual(self.grid.cases[0][0], Variable.CASE_BATEAU)
        self.assertEqual(self.grid.cases[0][1], Variable.CASE_BATEAU)
        self.assertEqual(self.grid.cases[0][2], Variable.CASE_BATEAU)

    def test_place_ship_collision(self):
        """Vérifie que deux bateaux ne peuvent pas se superposer."""
        ship1 = Ship(3, Position(0, 0), Orientation.HORIZONTAL)
        ship2 = Ship(3, Position(0, 1), Orientation.VERTICAL)
        self.grid.place_ship(ship1)
        self.assertFalse(self.grid.place_ship(ship2))

    def test_shoot_miss(self):
        """Vérifie le tir raté."""
        res = self.grid.shoot(5, 5)
        self.assertEqual(res.get_success(), 0)
        self.assertEqual(self.grid.cases[5][5], Variable.CASE_RATE)

    def test_shoot_hit_and_sink(self):
        """Vérifie le tir réussi et le coulé."""
        ship = Ship(2, Position(0, 0), Orientation.HORIZONTAL)
        self.grid.place_ship(ship)
        
        res1 = self.grid.shoot(0, 0)
        self.assertEqual(res1.get_success(), 1) # Touché
        
        res2 = self.grid.shoot(0, 1)
        self.assertEqual(res2.get_success(), 2) # Coulé

if __name__ == '__main__':
    unittest.main()
