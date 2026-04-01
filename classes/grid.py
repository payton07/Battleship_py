from classes.variable import Variable
from classes.position import Position
from classes.response import Response

class Grid:
    def __init__(self):
        # Récupération dynamique de la taille à l'initialisation
        self.size = Variable.get_size_grid()
        self.cases = [[Variable.CASE_DEFAULT for _ in range(self.size)] for _ in range(self.size)]
        self.ships = []

    def is_inside(self, x, y):
        """Vérification des limites de la grille (CONDITION 1)."""
        return 0 <= x < self.size and 0 <= y < self.size

    def can_place_ship(self, ship):
        """Vérifie si un bateau peut être placé (CONDITIONS 2 et 3)."""
        for pos in ship.get_positions():
            x, y = pos.get_x(), pos.get_y()
            # 1. Ne sort pas de la grille
            if not self.is_inside(x, y):
                return False
            # 2. Ne touche pas un autre bateau (Collision / Superposition)
            if self.cases[x][y] != Variable.CASE_DEFAULT:
                return False
        return True

    def place_ship(self, ship):
        """Place un bateau si c'est valide."""
        if not self.can_place_ship(ship):
            return False
        for pos in ship.get_positions():
            self.cases[pos.get_x()][pos.get_y()] = Variable.CASE_BATEAU
        self.ships.append(ship)
        return True

    def shoot(self, x, y):
        if not self.is_inside(x, y):
            return Response(-2, Variable.MESSAGE_HORS_GRILLE)

        if self.cases[x][y] in [Variable.CASE_TOUCHE, Variable.CASE_RATE]:
            return Response(-1, Variable.MESSAGE_DEJA_JOUE)

        if self.cases[x][y] == Variable.CASE_BATEAU:
            self.cases[x][y] = Variable.CASE_TOUCHE
            ship = self.get_ship_at(x, y)
            if ship:
                ship.hit(x, y)
                if ship.is_sunk():
                    return Response(2, Variable.MESSAGE_COULE)
            return Response(1, Variable.MESSAGE_TOUCHE)

        self.cases[x][y] = Variable.CASE_RATE
        return Response(0, Variable.MESSAGE_RATE)

    def get_ship_at(self, x, y):
        target = Position(x, y)
        for ship in self.ships:
            if target in ship.get_positions():
                return ship
        return None

    def all_ships_sunk(self):
        for ship in self.ships:
            if not ship.is_sunk():
                return False
        return True

    def __str__(self):
        sb = ["  "]
        for i in range(self.size):
            sb.append(Variable.get_alphabet(i) + " ")
        sb.append("\n")
        for i in range(self.size):
            sb.append(str(i).rjust(2) + " ") # rjust pour aligner les nombres > 10
            for j in range(self.size):
                sb.append(self.cases[j][i] + " ")
            sb.append("\n")
        return "".join(sb)
