class Variable:
    # --- Configuration du Jeu ---
    SIZE_GRID = 10
    SHIP_SIZES = [5, 4, 3, 3, 2]
    SHOTS_PER_TURN = 4
    
    # --- Symboles d'Affichage ---
    CASE_DEFAULT = "~"
    CASE_TOUCHE = "X"
    CASE_COULE = "C"
    CASE_RATE = "*"
    CASE_BATEAU = "O"

    # --- Messages de Retour de Tir ---
    MESSAGE_TOUCHE = "Touché"
    MESSAGE_COULE = "Coulé"
    MESSAGE_RATE = "Raté"
    MESSAGE_DEJA_JOUE = "Déjà joué"
    MESSAGE_HORS_GRILLE = "Hors Grille"
    
    # --- Prompts et Interface ---
    PROMPT_CHOIX_GRILLE = "Entrez 'N' pour la suivante, un numéro (0-9) pour un aperçu direct, ou 'V' pour valider : "
    MESSAGE_APERÇU_TITRE = "\n--- Aperçu de la Configuration {index} ---"
    MESSAGE_GRILLE_VALIDEE = "Grille {index} sélectionnée avec succès !"
    PROMPT_TIR = "Veuillez entrer la colonne de tir (ex: J4) pour {player_name}: "
    MESSAGE_TOUR_ERR = "Ce n'est pas le tour de {player_name}"
    MESSAGE_GAGNANT = "{player_name} a gagné ! "
    MESSAGE_AUCUN_GAGNANT = "Aucun gagnant"
    MESSAGE_FIN_PARTIE = "\n--- Fin de la partie ! ---"
    MESSAGE_DEBUT_PARTIE = "\n--- Début de la partie Battleship ---"
    MESSAGE_JOUEUR_ACTION = "{player_name} joue : {result}"
    MESSAGE_PAS_DE_JOUEUR = "Pas de joueurs configurés"
    MESSAGE_JOUEUR_NON_TROUVE = "Joueur non trouvé dans la partie"

    # --- Séquence de quota statique pour le CheatBot (Option B) ---
    # Générée une fois via random.choices([0,1,2,3,4], weights=[1,4,6,4,1], k=20).
    # Distribution cible : 0→6%, 1→25%, 2→38%, 3→25%, 4→6% (cloche centrée sur 2).
    # Chaque partie suit cette même séquence. Modifier manuellement si besoin.
    QUOTA_SEQUENCE = [1, 2, 2, 2, 2, 1, 0, 3, 1, 1, 4, 2, 3, 2, 2, 1, 2, 3, 2, 3]

    # --- Noms par défaut ---
    DEFAULT_PLAYER_1_NAME = "Joueur 1"
    DEFAULT_PLAYER_2_NAME = "Joueur 2"
    DEFAULT_PLAYER_HUMAN = "Joueur"
    DEFAULT_BOT_NAME = "Smart Bot"
    CHEAT_BOT_NAME = "Cheat Bot"

    @classmethod
    def get_case_default(cls):
        return cls.CASE_DEFAULT

    @classmethod
    def get_case_touche(cls):
        return cls.CASE_TOUCHE

    @classmethod
    def get_case_rate(cls):
        return cls.CASE_RATE

    @classmethod
    def get_case_bateau(cls):
        return cls.CASE_BATEAU

    @classmethod
    def get_message_touche(cls):
        return cls.MESSAGE_TOUCHE

    @classmethod
    def get_message_coule(cls):
        return cls.MESSAGE_COULE

    @classmethod
    def get_message_rate(cls):
        return cls.MESSAGE_RATE

    @classmethod
    def get_message_deja_joue(cls):
        return cls.MESSAGE_DEJA_JOUE

    @classmethod
    def get_message_hors_grille(cls):
        return cls.MESSAGE_HORS_GRILLE

    @classmethod
    def get_size_grid(cls):
        return cls.SIZE_GRID

    @classmethod
    def get_ship_sizes(cls):
        return cls.SHIP_SIZES

    @classmethod
    def get_number(cls, column):
        """Convertit une lettre (A, B, C...) en index numérique (0, 1, 2...)."""
        if not column:
            return -1
        col = column.upper()
        # Dynamique : On vérifie par rapport à SIZE_GRID
        index = ord(col) - ord('A')
        if 0 <= index < cls.SIZE_GRID:
            return index
        return -1

    @classmethod
    def get_alphabet(cls, number):
        """Convertit un index numérique (0, 1, 2...) en lettre (A, B, C...)."""
        if 0 <= number < cls.SIZE_GRID:
            return chr(ord('A') + number)
        return " "

    @classmethod
    def is_inside(cls, x, y):
        """Vérifie si une coordonnée (x, y) est dans les limites de la grille."""
        return 0 <= x < cls.SIZE_GRID and 0 <= y < cls.SIZE_GRID
