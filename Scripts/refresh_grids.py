import sys
import os

# Garantir que les modules sont trouvables
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from classes.grid_generator import GridGenerator

def main():
    print("#" + "="*50)
    print("### GÉNÉRATEUR DE CONFIGURATIONS BATTLESHIP ###")
    print("#" + "="*50 + "\n")
    print("Copiez la liste ci-dessous dans classes/predefined_grids.py :\n")
    
    GridGenerator.print_as_python_code(10)

if __name__ == "__main__":
    main()
