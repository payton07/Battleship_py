from classes.orientation import Orientation

class PredefinedGrids:
    # Format: (size, x, y, orientation)
    # Orientation: 1 = HORIZONTAL (X change), 2 = VERTICAL (Y change)
    GRIDS = [
        # Grille 0
        [(5, 2, 6, 1), (4, 6, 7, 1), (3, 5, 5, 1), (3, 0, 2, 1), (2, 6, 8, 2)],
        # Grille 1
        [(5, 4, 4, 2), (4, 6, 5, 1), (3, 2, 9, 1), (3, 7, 6, 2), (2, 6, 2, 2)],
        # Grille 2
        [(5, 3, 4, 1), (4, 1, 1, 1), (3, 0, 5, 1), (3, 7, 6, 1), (2, 0, 0, 1)],
        # Grille 3
        [(5, 0, 8, 1), (4, 6, 2, 2), (3, 7, 4, 1), (3, 0, 1, 2), (2, 7, 7, 2)],
        # Grille 4
        [(5, 8, 1, 2), (4, 6, 5, 2), (3, 2, 1, 2), (3, 4, 2, 2), (2, 9, 4, 2)],
        # Grille 5
        [(5, 6, 5, 2), (4, 1, 6, 1), (3, 9, 1, 2), (3, 1, 4, 1), (2, 4, 2, 2)],
        # Grille 6
        [(5, 5, 8, 1), (4, 9, 1, 2), (3, 6, 3, 2), (3, 0, 6, 2), (2, 1, 2, 1)],
        # Grille 7
        [(5, 2, 9, 1), (4, 3, 3, 1), (3, 5, 5, 1), (3, 3, 6, 2), (2, 1, 4, 1)],
        # Grille 8
        [(5, 8, 3, 2), (4, 4, 5, 1), (3, 4, 6, 2), (3, 7, 2, 2), (2, 5, 2, 1)],
        # Grille 9
        [(5, 2, 1, 2), (4, 6, 6, 2), (3, 5, 1, 2), (3, 4, 0, 1), (2, 3, 1, 2)],
    ]

    @classmethod
    def get_grid(cls, index):
        if 0 <= index < len(cls.GRIDS):
            return cls.GRIDS[index]
        return cls.GRIDS[0]
