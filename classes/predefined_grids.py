from classes.orientation import Orientation

class PredefinedGrids:
    # Format: (size, x, y, orientation)
    # Orientation: 1 = HORIZONTAL (Y change), 2 = VERTICAL (X change)
    GRIDS = [
        # Grille 0
        [(5, 4, 3, 2), (4, 1, 3, 1), (3, 7, 1, 2), (3, 2, 7, 1), (2, 8, 6, 2)],
        # Grille 1
        [(5, 2, 1, 2), (4, 4, 3, 1), (3, 0, 0, 2), (3, 7, 6, 2), (2, 4, 8, 1)],
        # Grille 2
        [(5, 1, 0, 2), (4, 3, 2, 1), (3, 5, 5, 2), (3, 0, 7, 1), (2, 7, 1, 2)],
        # Grille 3
        [(5, 0, 4, 1), (4, 2, 0, 2), (3, 6, 2, 1), (3, 4, 6, 2), (2, 8, 0, 2)],
        # Grille 4
        [(5, 3, 2, 1), (4, 0, 1, 2), (3, 5, 0, 2), (3, 1, 7, 1), (2, 8, 5, 2)],
        # Grille 5
        [(5, 4, 0, 2), (4, 1, 2, 1), (3, 7, 4, 2), (3, 2, 6, 1), (2, 0, 0, 1)],
        # Grille 6
        [(5, 2, 2, 1), (4, 5, 5, 2), (3, 0, 1, 2), (3, 7, 0, 1), (2, 0, 8, 1)],
        # Grille 7
        [(5, 1, 4, 2), (4, 3, 0, 1), (3, 6, 6, 2), (3, 0, 0, 1), (2, 8, 2, 2)],
        # Grille 8
        [(5, 0, 2, 2), (4, 2, 4, 1), (3, 5, 1, 2), (3, 1, 7, 1), (2, 7, 5, 2)],
        # Grille 9
        [(5, 3, 3, 1), (4, 0, 0, 2), (3, 5, 0, 2), (3, 7, 6, 1), (2, 1, 8, 2)]
    ]

    @classmethod
    def get_grid(cls, index):
        if 0 <= index < len(cls.GRIDS):
            return cls.GRIDS[index]
        return cls.GRIDS[0]
