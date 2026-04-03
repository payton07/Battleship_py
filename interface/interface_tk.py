from tkinter import *

fenetre = Tk()

# https://python.doctor/page-tkinter-interface-graphique-python-tutoriel

def recuperer_case(event):
    # Calculer l'index de la case cliquée (de 0 à 9)
    colonne = event.x // taille_case
    ligne = event.y // taille_case

    print(f"Clic sur la case : [Ligne {ligne}, Colonne {colonne}]")

    # Colorier la case cliquée pour confirmation
    x1, y1 = colonne * taille_case, ligne * taille_case
    x2, y2 = x1 + taille_case, y1 + taille_case
    Canvas1.create_rectangle(x1, y1, x2, y2, fill="lightblue", outline="gray")

# Paramètres de la grille
nb_cases = 10
taille_case = 50
cote = nb_cases * taille_case # 500 pixels

Canvas1 = Canvas(fenetre, width=cote, height=cote, bg="white", highlightthickness=0)
Canvas1.pack(padx=10, pady=10)

Canvas1.bind("<Button-1>", recuperer_case)

# Tracé de la grille
for i in range(nb_cases + 1):
    pos = i * taille_case
    # Lignes horizontales
    Canvas1.create_line(0, pos, cote, pos, fill="lightgray")
    # Lignes verticales
    Canvas1.create_line(pos, 0, pos, cote, fill="lightgray")

# bouton de sortie
bouton=Button(fenetre, text="Fermer", command=fenetre.quit)
bouton.pack()

fenetre.mainloop()
