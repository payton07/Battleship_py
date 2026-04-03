class Position:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def get_x(self):
        return self.x

    def get_y(self):
        return self.y

    def __eq__(self, other):
        if not isinstance(other, Position):
            return False
        return self.x == other.x and self.y == other.y

    def __hash__(self):
        return hash((self.x, self.y))

    def get_neighbors(self):
        """Retourne les 4 positions adjacentes (Haut, Bas, Gauche, Droite)."""
        return [
            Position(self.x - 1, self.y),
            Position(self.x + 1, self.y),
            Position(self.x, self.y - 1),
            Position(self.x, self.y + 1)
        ]

    def __repr__(self):
        return "Position({}, {})".format(self.x, self.y)
