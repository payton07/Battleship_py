# -*- coding: utf-8 -*-
import sys
import os

# Ajout du chemin pour trouver les modules du projet
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from classes.grid import Grid

def main():
    print("\n" + "="*30)
    print("      GRILLE VIERGE")
    print("="*30 + "\n")
    
    # Création d'une grille vide (initialisée par défaut avec CASE_DEFAULT '~')
    empty_grid = Grid()
    
    # Affichage de la grille
    print(empty_grid)
    
    print("="*30)

if __name__ == "__main__":
    main()
