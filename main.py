# -*- coding: utf-8 -*-
from __future__ import print_function
import sys
import os
try:
    from tkinter import Tk
except ImportError:
    from Tkinter import Tk

# Garantir que les modules locaux sont trouvables
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from game_logic.game_master import GameMaster
from interface.interface_tk import BattleshipGUI

def main():
    print("#" + "="*40)
    print("### PEPPER BATTLESHIP ###")
    print("#" + "="*40 + "\n")
    
    print("Choisissez votre mode de jeu :")
    print("1. Mode Console (Texte)")
    print("2. Mode Graphique (Tkinter)")
    
    try:
        try:
            choice = raw_input("\nVotre choix (1 ou 2) : ").strip()
        except NameError:
            choice = input("\nVotre choix (1 ou 2) : ").strip()
        
        if choice == "1":
            print("\nLancement du mode Console...\n")
            game_master = GameMaster()
            game_master.run()
        elif choice == "2":
            print("\nLancement du mode Graphique...\n")
            root = Tk()
            gui = BattleshipGUI(root)
            root.mainloop()
        else:
            print("Choix invalide. Fermeture du programme.")
            
    except KeyboardInterrupt:
        print("\nPartie interrompue. À bientôt !")
    except Exception as e:
        import traceback
        traceback.print_exc()
        print("Une erreur inattendue est survenue : {}".format(e))

if __name__ == "__main__":
    main()
