from classes.position import Position
from classes.orientation import Orientation

class Ship:
    def __init__(self, size, start, orientation):
        self.size = size
        self.start = start
        self.orientation = orientation
        self.hits = set()

    def get_positions(self):
        positions = []
        for i in range(self.size):
            if self.orientation == Orientation.HORIZONTAL:
                positions.append(Position(self.start.get_x() + i, self.start.get_y()))
            else:
                positions.append(Position(self.start.get_x(), self.start.get_y() + i))
        return positions

    def get_size(self):
        return self.size

    def hit(self, x, y):
        self.hits.add(Position(x, y))

    def is_sunk(self):
        return len(self.hits) == self.size
