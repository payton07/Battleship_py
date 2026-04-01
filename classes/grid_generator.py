import random
from classes.grid import Grid
from classes.ship import Ship
from classes.position import Position
from classes.orientation import Orientation
from classes.variable import Variable

class GridGenerator:
    @staticmethod
    def generate_one_configuration():
        """Génère une seule configuration valide en respectant la taille dynamique."""
        grid = Grid()
        ship_configs = []
        sizes = Variable.get_ship_sizes()
        size_grid = Variable.get_size_grid() # Récupération de la taille (ex: 10)
        
        for size in sizes:
            placed = False
            attempts = 0
            while not placed and attempts < 200: # Plus d'essais si la grille est serrée
                x = random.randint(0, size_grid - 1)
                y = random.randint(0, size_grid - 1)
                orient = random.choice([Orientation.HORIZONTAL, Orientation.VERTICAL])
                
                ship = Ship(size, Position(x, y), orient)
                # On utilise la validation de Grid qui vérifie les collisions et les bords
                if grid.place_ship(ship):
                    ship_configs.append((size, x, y, orient.value))
                    placed = True
                attempts += 1
        
        # Sécurité : Si après 200 essais un bateau manque, on recommence tout
        if len(ship_configs) < len(sizes):
            return GridGenerator.generate_one_configuration()
            
        return ship_configs

    @classmethod
    def generate_multiple_configurations(cls, count=10):
        return [cls.generate_one_configuration() for _ in range(count)]

    @classmethod
    def print_as_python_code(cls, count=10):
        configs = cls.generate_multiple_configurations(count)
        print("    GRIDS = [")
        for i, config in enumerate(configs):
            print(f"        # Grille {i}")
            print(f"        {config},")
        print("    ]")
