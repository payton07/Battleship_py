# -*- coding: utf-8 -*-
try:
    from tkinter import *
    from tkinter import messagebox
    from tkinter import simpledialog
except ImportError:
    from Tkinter import *
    import tkMessageBox as messagebox
    import tkSimpleDialog as simpledialog
import random
from game_logic.game_master import GameMaster
from classes.variable import Variable
from classes.position import Position

class BattleshipGUI(object):
    def __init__(self, root):
        self.root = root
        self.root.title("Pepper Battleship - Digital vs Physical")
        self.root.resizable(False, False)

        # Initialisation du moteur de jeu
        self.gm = GameMaster()
        # Par défaut en mode Digital pour l'UI
        self.gm.setup_players(hybrid=False)
        
        # État de l'interface
        self.current_grid_index = 0
        self.is_playing = False
        self.can_shoot = False
        self.shots_left = Variable.SHOTS_PER_TURN
        self.bot_shots_history = [] # Historique des tirs du bot pour le tour actuel
        
        # Paramètres graphiques
        self.cell_size = 35
        self.offset = 25 # Marge pour les numéros de ligne/colonne
        self.grid_size = Variable.get_size_grid()
        self.canvas_dim = (self.cell_size * self.grid_size) + self.offset

        self._setup_ui()
        self._show_preview()

    def _setup_ui(self):
        """Crée les widgets de l'interface."""
        self.top_frame = Frame(self.root, pady=10)
        self.top_frame.pack()

        self.label_status = Label(self.top_frame, text="Choisissez votre configuration", font=("Arial", 14, "bold"))
        self.label_status.pack()

        self.label_quota = Label(self.top_frame, text="Quota : -", font=("Arial", 12), fg="#7f8c8d")
        self.label_quota.pack()

        self.btn_next = Button(self.top_frame, text="Grille Suivante (N)", command=self._next_grid, fg="black", bg="white", highlightbackground="white", activeforeground="black")
        self.btn_next.pack(side=LEFT, padx=5)

        self.btn_validate = Button(self.top_frame, text="Valider (V)", command=self._validate_grid, fg="black", bg="white", highlightbackground="white", activeforeground="black")
        self.btn_validate.pack(side=LEFT, padx=5)

        self.btn_repeat_bot = Button(self.top_frame, text="Répéter", command=self._repeat_bot_shot, state=DISABLED, fg="black", bg="white", highlightbackground="white", activeforeground="black")
        self.btn_repeat_bot.pack(side=LEFT, padx=5)

        self.grid_frame = Frame(self.root, padx=20, pady=20)
        self.grid_frame.pack()

        # Grille Joueur
        self.player_frame = Frame(self.grid_frame)
        self.player_frame.pack(side=LEFT, padx=20)
        Label(self.player_frame, text="MA GRILLE", font=("Arial", 10, "bold")).pack()
        self.canvas_player = Canvas(self.player_frame, width=self.canvas_dim, height=self.canvas_dim, bg="white", borderwidth=1, relief="solid")
        self.canvas_player.pack()
        self.canvas_player.bind("<Button-1>", self._on_player_click)

        # Grille Ennemie
        self.enemy_frame = Frame(self.grid_frame)
        self.enemy_frame.pack(side=LEFT, padx=20)
        Label(self.enemy_frame, text="GRILLE ENNEMIE", font=("Arial", 10, "bold")).pack()
        self.canvas_enemy = Canvas(self.enemy_frame, width=self.canvas_dim, height=self.canvas_dim, bg="white", borderwidth=1, relief="solid", cursor="crosshair")
        self.canvas_enemy.pack()
        self.canvas_enemy.bind("<Button-1>", self._on_enemy_click)

        self.status_bar = Label(self.root, text="Prêt", bd=1, relief=SUNKEN, anchor=W)
        self.status_bar.pack(side=BOTTOM, fill=X)

    def _draw_grid_base(self, canvas):
        canvas.delete("all")
        # Dessiner les lettres (Colonnes)
        for i in range(self.grid_size):
            char = chr(ord('A') + i)
            x = self.offset + (i * self.cell_size) + (self.cell_size // 2)
            canvas.create_text(x, self.offset // 2, text=char, font=("Arial", 10, "bold"), fill="black")
        
        # Dessiner les chiffres (Lignes)
        for i in range(self.grid_size):
            y = self.offset + (i * self.cell_size) + (self.cell_size // 2)
            canvas.create_text(self.offset // 2, y, text=str(i), font=("Arial", 10, "bold"), fill="black")

        # Dessiner les lignes de la grille (décalées par l'offset)
        for i in range(self.grid_size + 1):
            pos = self.offset + (i * self.cell_size)
            # Lignes horizontales
            canvas.create_line(self.offset, pos, self.canvas_dim, pos, fill="#ecf0f1")
            # Lignes verticales
            canvas.create_line(pos, self.offset, pos, self.canvas_dim, fill="#ecf0f1")

    def _draw_content(self, canvas, grid, hide_ships=False):
        self._draw_grid_base(canvas)
        if not grid: return
        
        for x in range(self.grid_size):
            for y in range(self.grid_size):
                case = grid.cases[x][y]
                color = None
                if case == Variable.CASE_BATEAU and not hide_ships:
                    color = "#95a5a6"
                elif case == Variable.CASE_TOUCHE:
                    color = "#e74c3c"
                elif case == Variable.CASE_RATE:
                    color = "#3498db"
                elif case == Variable.CASE_COULE:
                    color = "#FFFF00"
                
                if color:
                    x1 = self.offset + (x * self.cell_size)
                    y1 = self.offset + (y * self.cell_size)
                    x2, y2 = x1 + self.cell_size, y1 + self.cell_size
                    canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="#7f8c8d")

    def _show_preview(self):
        from classes.grid import Grid
        from classes.predefined_grids import PredefinedGrids
        from classes.ship import Ship
        from classes.orientation import Orientation
        temp_grid = Grid()
        config = PredefinedGrids.get_grid(self.current_grid_index)
        for size, x, y, orient_val in config:
            ship = Ship(size, Position(x, y), Orientation(orient_val))
            temp_grid.place_ship(ship)
        self._draw_content(self.canvas_player, temp_grid)
        self.label_status.config(text=u"Configuration {}".format(self.current_grid_index))

    def _next_grid(self):
        if not self.is_playing:
            self.current_grid_index = (self.current_grid_index + 1) % 10
            self._show_preview()

    def _validate_grid(self):
        if not self.is_playing:
            self.gm.apply_grid_choice(self.gm.human_player, self.current_grid_index)
            self.gm.game.place_all_ships(self.gm.bot_player)
            self.is_playing = True
            self.can_shoot = True
            self.btn_next.config(state=DISABLED)
            self.btn_validate.config(state=DISABLED)
            self._set_turn_message("player")
            self._refresh_ui()

    def _set_turn_message(self, turn_owner):
        if turn_owner == "player":
            msg = u"À VOUS DE TIRER ! ({} restants)".format(self.shots_left)
            self.label_status.config(text=msg, fg="#2ecc71")
            self.label_quota.config(text="Quota : (Votre tour)", fg="#7f8c8d")
        else:
            quota = self.gm.bot_player.success_quota
            msg = u"TOUR DU BOT : {} tirs restants".format(self.shots_left)
            self.label_status.config(text=msg, fg="#e67e22")
            self.label_quota.config(text=u"QUOTA À ATTEINDRE : {} touchés".format(quota), fg="#d35400", font=("Arial", 14, "bold"))

    def _refresh_ui(self):
        self._draw_content(self.canvas_player, self.gm.human_player.my_grid)
        self._draw_content(self.canvas_enemy, self.gm.bot_player.my_grid, hide_ships=False)

    def _on_enemy_click(self, event):
        if not self.is_playing or not self.can_shoot:
            return
        
        # Soustraire l'offset avant de diviser par cell_size
        x = (event.x - self.offset) // self.cell_size
        y = (event.y - self.offset) // self.cell_size
        
        if not Variable.is_inside(x, y): return

        res = self.gm.play_shot(self.gm.human_player, x, y)
        if res == Variable.MESSAGE_DEJA_JOUE:
            self.status_bar.config(text="Case déjà jouée !")
            return

        self.shots_left -= 1
        self.status_bar.config(text=u"Résultat : {}".format(res))
        self._refresh_ui()

        if self.gm.is_game_over():
            self._end_game()
            return

        if self.shots_left == 0:
            self.gm.game.next_turn()
            self.can_shoot = False
            self.btn_repeat_bot.config(state=NORMAL)
            self.shots_left = Variable.SHOTS_PER_TURN
            self.bot_shots_history = [] 
            
            # Récupérer le quota pour le tour du bot qui commence
            next_quota = self.gm.quotas_manager.get_next_quota()
            self.gm.bot_player.set_success_quota(next_quota)
            
            self._set_turn_message("bot")
        else:
            self._set_turn_message("player")

    def _on_player_click(self, event):
        """Permet de déclencher un tir du bot en cliquant sur sa propre grille (CheatBot)."""
        if not self.is_playing or self.can_shoot:
            # On ne peut cliquer que si c'est le tour du Bot
            return
        
        x = (event.x - self.offset) // self.cell_size
        y = (event.y - self.offset) // self.cell_size
        
        if not Variable.is_inside(x, y): return

        # On force le prochain tir du bot à cette position
        self.gm.bot_player.set_next_shot(x, y)
        self._next_bot_shot()

    def _next_bot_shot(self):
        """Exécute un tir du bot manuellement."""
        if not self.is_playing or self.can_shoot:
            return

        res = self.gm.play_shot(self.gm.bot_player)
        if res == Variable.MESSAGE_DEJA_JOUE:
            self.status_bar.config(text="Bot : Case déjà jouée !")
            return

        # Enregistrement du tir du bot
        pos = self.gm.bot_player.last_played_pos
        self.bot_shots_history.append({
            'x': pos.get_x(),
            'y': pos.get_y(),
            'result': res
        })

        self.status_bar.config(text=u"Le Bot tire : {}".format(res))
        self._refresh_ui()

        if self.gm.is_game_over():
            self._end_game()
            return

        self.shots_left -= 1
        if self.shots_left == 0:
            self.gm.game.next_turn()
            self.shots_left = Variable.SHOTS_PER_TURN
            
            # Demander si l'utilisateur pense que le bot a triché (OUI/NON)
            has_cheated = messagebox.askyesno(
                "Évaluation de la triche", 
                "Pensez-vous que le robot a triché durant ce tour ?"
            )
            trust_value = 1 if has_cheated else 0
            
            # Enregistre le tour avec le résultat (0 ou 1)
            self.gm.save_bot_turn(trust_value, self.bot_shots_history)
            
            self.can_shoot = True
            self.btn_repeat_bot.config(state=DISABLED)
            self._set_turn_message("player")
        else:
            self._set_turn_message("bot")

    def _repeat_bot_shot(self):
        """Demande au bot de répéter son dernier tir."""
        if self.gm.repeat_bot_shot():
            self.status_bar.config(text=u"Bot : Dernier tir répété.")
        else:
            self.status_bar.config(text=u"Erreur : Impossible de répéter.")

    def _end_game(self):
        self.gm.finalize_game() # Enregistre le gagnant en BDD
        
        self.is_playing = False
        self.can_shoot = False
        winner_msg = self.gm.get_winner_message()
        self.label_status.config(text=u"PARTIE TERMINÉE", fg="#c0392b")
        messagebox.showinfo("Fin de partie", winner_msg)
        self.root.quit()

if __name__ == "__main__":
    root = Tk()
    gui = BattleshipGUI(root)
    root.mainloop()
