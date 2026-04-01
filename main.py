#import sys
#import os

# Ajouter le répertoire racine au sys.path pour garantir que les modules sont trouvés
# sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from game_logic.game_master import GameMaster

def main():
    try:
        game_master = GameMaster()
        game_master.run()
    except KeyboardInterrupt:
        print("\nPartie interrompue. À bientôt !")
    except Exception as e:
        print(f"Une erreur inattendue est survenue : {e}")

if __name__ == "__main__":
    main()
