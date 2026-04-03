from tkinter import *

# https://python.doctor/page-tkinter-interface-graphique-python-tutoriel

class Interface:
    def __init__(self):
        # Paramètres de la grille
        self.nb_cases = 10
        self.taille_case = 50
        self.canvas = None
        self.fenetre = Tk()
        self.create_fenetre()
        self.fenetre.mainloop()

    def create_canvas(self):
        cote = self.nb_cases * self.taille_case  # 500 pixels

        self.canvas = Canvas(self.fenetre, width=cote, height=cote, bg="white", highlightthickness=0)
        self.canvas.pack(padx=10, pady=10)

        self.canvas.bind("<Button-1>", self.recuperer_case)

        # Tracé de la grille
        for i in range(self.nb_cases + 1):
            pos = i * self.taille_case
            # Lignes horizontales
            self.canvas.create_line(0, pos, cote, pos, fill="lightgray")
            # Lignes verticales
            self.canvas.create_line(pos, 0, pos, cote, fill="lightgray")

    def recuperer_case(self, event):
        # Calculer l'index de la case cliquée (de 0 à 9)
        colonne = event.x // self.taille_case
        ligne = event.y // self.taille_case

        print(f"Clic sur la case : [Ligne {ligne}, Colonne {colonne}]")

        # Colorier la case cliquée pour confirmation
        x1, y1 = colonne * self.taille_case, ligne * self.taille_case
        x2, y2 = x1 + self.taille_case, y1 + self.taille_case
        self.canvas.create_rectangle(x1, y1, x2, y2, fill="lightblue", outline="gray")
    
    def create_fenetre(self):
        # bouton de sortie
        bouton = Button(self.fenetre, text="Fermer", command=self.fenetre.quit)
        bouton.pack()

        self.create_canvas()