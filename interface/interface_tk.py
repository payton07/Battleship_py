# -*- coding: utf-8 -*-
from tkinter import *
from tkinter import messagebox
import random
from game_logic.game_master import GameMaster
from classes.variable import Variable
from classes.position import Position
from players.cheat_bot import CheatBot

class BattleshipGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Pepper Battleship - Digital vs Physical")
        self.root.resizable(False, False)

        # Initialisation du moteur de jeu
        self.gm = GameMaster()
        self.gm.setup_players()
        
        # État de l'interface
        self.current_grid_index = 0
        self.is_playing = False
        self.can_shoot = False
        self.shots_left = Variable.SHOTS_PER_TURN
        
        # Paramètres graphiques
        self.cell_size = 35
        self.grid_size = Variable.get_size_grid()
        self.canvas_dim = self.cell_size * self.grid_size

        self._setup_ui()
        self._show_preview()

    def _setup_ui(self):
        """Crée les widgets de l'interface."""
        self.top_frame = Frame(self.root, pady=10)
        self.top_frame.pack()

        self.label_status = Label(self.top_frame, text="Choisissez votre configuration", font=("Arial", 14, "bold"))
        self.label_status.pack()

        self.btn_next = Button(self.top_frame, text="Grille Suivante (N)", command=self._next_grid)
        self.btn_next.pack(side=LEFT, padx=5)

        self.btn_validate = Button(self.top_frame, text="Valider (V)", command=self._validate_grid, bg="#2ecc71", fg="black", highlightbackground="#2ecc71")
        self.btn_validate.pack(side=LEFT, padx=5)

        self.grid_frame = Frame(self.root, padx=20, pady=20)
        self.grid_frame.pack()

        # Grille Joueur
        self.player_frame = Frame(self.grid_frame)
        self.player_frame.pack(side=LEFT, padx=20)
        Label(self.player_frame, text="MA GRILLE", font=("Arial", 10, "bold")).pack()
        self.canvas_player = Canvas(self.player_frame, width=self.canvas_dim, height=self.canvas_dim, bg="white", borderwidth=1, relief="solid")
        self.canvas_player.pack()

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
        for i in range(self.grid_size + 1):
            pos = i * self.cell_size
            canvas.create_line(0, pos, self.canvas_dim, pos, fill="#ecf0f1")
            canvas.create_line(pos, 0, pos, self.canvas_dim, fill="#ecf0f1")

    def _draw_content(self, canvas, grid, hide_ships=False):
        self._draw_grid_base(canvas)
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
                
                if color:
                    x1, y1 = x * self.cell_size, y * self.cell_size
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
        self.label_status.config(text=f"Configuration {self.current_grid_index}")

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
            msg = "À VOUS DE TIRER ! ({} restants)".format(self.shots_left)
            self.label_status.config(text=msg, fg="#2ecc71")
        else:
            self.label_status.config(text="ATTENDEZ : Le Bot joue...", fg="#e67e22")

    def _refresh_ui(self):
        self._draw_content(self.canvas_player, self.gm.human_player.my_grid)
        self._draw_content(self.canvas_enemy, self.gm.bot_player.my_grid, hide_ships=True)

    def _on_enemy_click(self, event):
        if not self.is_playing or not self.can_shoot:
            return
        x, y = event.x // self.cell_size, event.y // self.cell_size
        if not Variable.is_inside(x, y): return

        res = self.gm.play_shot(self.gm.human_player, x, y)
        if res == Variable.MESSAGE_DEJA_JOUE:
            self.status_bar.config(text="Case déjà jouée !")
            return

        self.shots_left -= 1
        self.status_bar.config(text="Résultat : {}".format(res))
        self._refresh_ui()

        if self.gm.is_game_over():
            self._end_game()
            return

        if self.shots_left == 0:
            self.gm.game.next_turn()
            self.can_shoot = False
            self._set_turn_message("bot")
            if isinstance(self.gm.bot_player, CheatBot):
                sq = random.randint(0, 4)
                self.gm.bot_player.set_success_quota(sq)
            self.root.after(1000, lambda: self._bot_turn_step(0))
        else:
            self._set_turn_message("player")

    def _bot_turn_step(self, shot_num):
        """Exécute UN tir du bot, met à jour l'UI, et planifie le suivant."""
        if not self.is_playing: return

        res = self.gm.play_shot(self.gm.bot_player)
        self.status_bar.config(text="Le Bot tire : {}".format(res))
        self._refresh_ui()

        if self.gm.is_game_over():
            self._end_game()
            return

        if shot_num < Variable.SHOTS_PER_TURN - 1:
            self.root.after(600, lambda: self._bot_turn_step(shot_num + 1))
        else:
            self.gm.game.next_turn()
            self.shots_left = Variable.SHOTS_PER_TURN
            self.can_shoot = True
            self._set_turn_message("player")

    def _end_game(self):
        self.is_playing = False
        self.can_shoot = False
        winner_msg = self.gm.get_winner_message()
        self.label_status.config(text="PARTIE TERMINÉE", fg="#c0392b")
        messagebox.showinfo("Fin de partie", winner_msg)
        self.root.quit()

if __name__ == "__main__":
    root = Tk()
    gui = BattleshipGUI(root)
    root.mainloop()
