import unittest
from classes.ship import Ship
from classes.position import Position
from classes.orientation import Orientation

class TestShip(unittest.TestCase):
    def test_ship_positions_horizontal(self):
        """Vérifie les positions calculées pour un bateau horizontal."""
        ship = Ship(3, Position(2, 2), Orientation.HORIZONTAL)
        positions = ship.get_positions()
        expected = [Position(2, 2), Position(3, 2), Position(4, 2)]
        self.assertEqual(positions, expected)

    def test_ship_positions_vertical(self):
        """Vérifie les positions calculées pour un bateau vertical."""
        ship = Ship(2, Position(5, 5), Orientation.VERTICAL)
        positions = ship.get_positions()
        expected = [Position(5, 5), Position(5, 6)]
        self.assertEqual(positions, expected)

    def test_ship_sinking(self):
        """Vérifie si le bateau coule au bon nombre de coups."""
        ship = Ship(2, Position(0, 0), Orientation.HORIZONTAL)
        self.assertFalse(ship.is_sunk())
        ship.hit(0, 0)
        self.assertFalse(ship.is_sunk())
        ship.hit(1, 0)
        self.assertTrue(ship.is_sunk())

if __name__ == '__main__':
    unittest.main()
