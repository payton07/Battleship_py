# -*- coding: utf-8 -*-

class PredefinedGrids(object):
    """
    Classe contenant des configurations de grilles prédéfinies.
    Chaque grille est une liste de tuples : (taille, x, y, orientation)
    Orientation: 1 pour HORIZONTAL, 2 pour VERTICAL
    """
    
    GRIDS = [
        # Grille 0
        [(5, 4, 1, 1), (4, 2, 7, 1), (4, 4, 4, 1), (3, 1, 0, 2), (2, 9, 4, 2)],
        # Grille 1
        [(5, 2, 2, 1), (4, 6, 6, 1), (4, 1, 6, 1), (3, 2, 4, 1), (2, 6, 9, 1)],
        # Grille 2
        [(5, 8, 2, 2), (4, 0, 9, 1), (4, 6, 3, 2), (3, 6, 0, 1), (2, 3, 1, 2)],
        # Grille 3
        [(5, 5, 2, 2), (4, 1, 2, 2), (4, 7, 4, 2), (3, 1, 8, 1), (2, 8, 1, 1)],
        # Grille 4
        [(5, 8, 0, 2), (4, 1, 9, 1), (4, 0, 6, 1), (3, 3, 1, 1), (2, 4, 7, 1)],
        # Grille 5
        [(5, 1, 3, 1), (4, 2, 5, 1), (4, 9, 0, 2), (3, 1, 0, 1), (2, 5, 7, 2)],
        # Grille 6
        [(5, 0, 3, 1), (4, 2, 5, 2), (4, 5, 4, 2), (3, 0, 5, 2), (2, 9, 1, 2)],
        # Grille 7
        [(5, 5, 2, 1), (4, 4, 5, 2), (4, 8, 5, 2), (3, 2, 3, 2), (2, 2, 7, 2)],
        # Grille 8
        [(5, 9, 2, 2), (4, 5, 8, 1), (4, 2, 5, 2), (3, 6, 0, 2), (2, 6, 5, 1)],
        # Grille 9
        [(5, 3, 7, 1), (4, 4, 3, 1), (4, 0, 5, 2), (3, 5, 9, 1), (2, 4, 0, 2)],
    ]

    @classmethod
    def get_grid(cls, index):
        if 0 <= index < len(cls.GRIDS):
            return cls.GRIDS[index]
        return cls.GRIDS[0]
