# -*- coding: utf-8 -*-
try:
    from tkinter import *
except ImportError:
    from Tkinter import *

from classes.variable import Variable

class EmptyGridGUI(object):
    def __init__(self, root):
        self.root = root
        self.root.title("Grille Battleship Vierge")
        self.root.resizable(False, False)

        # Paramètres identiques à l'interface du jeu
        self.cell_size = 35
        self.offset = 25
        self.grid_size = Variable.get_size_grid()
        self.canvas_dim = (self.cell_size * self.grid_size) + self.offset

        self._setup_ui()

    def _setup_ui(self):
        self.main_frame = Frame(self.root, padx=20, pady=20)
        self.main_frame.pack()

        Label(self.main_frame, text="GRILLE DE JEU", font=("Arial", 12, "bold"), pady=10).pack()

        self.canvas = Canvas(self.main_frame, width=self.canvas_dim, height=self.canvas_dim, bg="white", borderwidth=1, relief="solid")
        self.canvas.pack()

        self._draw_grid_base()

        # Bouton pour fermer
        Button(self.main_frame, text="Fermer", command=self.root.quit, pady=5).pack(pady=10)

    def _draw_grid_base(self):
        # Dessiner les lettres (Colonnes)
        for i in range(self.grid_size):
            char = chr(ord('A') + i)
            x = self.offset + (i * self.cell_size) + (self.cell_size // 2)
            self.canvas.create_text(x, self.offset // 2, text=char, font=("Arial", 10, "bold"), fill="black")
        
        # Dessiner les chiffres (Lignes)
        for i in range(self.grid_size):
            y = self.offset + (i * self.cell_size) + (self.cell_size // 2)
            self.canvas.create_text(self.offset // 2, y, text=str(i), font=("Arial", 10, "bold"), fill="black")

        # Dessiner les lignes de la grille
        for i in range(self.grid_size + 1):
            pos = self.offset + (i * self.cell_size)
            # Lignes horizontales
            self.canvas.create_line(self.offset, pos, self.canvas_dim, pos, fill="#bdc3c7")
            # Lignes verticales
            self.canvas.create_line(pos, self.offset, pos, self.canvas_dim, fill="#bdc3c7")

if __name__ == "__main__":
    root = Tk()
    gui = EmptyGridGUI(root)
    root.mainloop()
