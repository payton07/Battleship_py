from tkinter import *
import threading
import queue
import traceback

# https://python.doctor/page-tkinter-interface-graphique-python-tutoriel

class Interface:
    def __init__(self):
        # Paramètres de la grille
        self.nb_cases = 10
        self.taille_case = 50
        self.marge = 30  # Marge pour les labels
        self.canvas = None
        self.fenetre = None
        
        # File d'attente pour la communication thread-safe
        self.command_queue = queue.Queue()
        self.result_queue = queue.Queue()
        
        # File d'attente pour les clics de l'utilisateur
        self.click_queue = queue.Queue()
        
        # Thread pour l'interface
        self.thread = threading.Thread(target=self._run_tk, daemon=True)
        self.running = False
        self.error = None  # Stocke les erreurs du thread
        self.waiting_for_click = False  # Indique si on attend un clic
        
    def start(self):
        """Démarre l'interface dans un thread séparé"""
        self.running = True
        self.thread.start()
        # Attendre que l'interface soit initialisée (avec timeout)
        try:
            result = self.result_queue.get(timeout=5)
            if isinstance(result, Exception):
                raise result
        except queue.Empty:
            raise TimeoutError("L'interface n'a pas démarré dans les temps")
        
    def stop(self):
        """Arrête l'interface proprement"""
        self.running = False
        if self.fenetre:
            try:
                self.execute_command(lambda: self.fenetre.quit(), timeout=2)
            except queue.Empty:
                print("Avertissement : Timeout lors de la fermeture de l'interface")
            except Exception as e:
                print(f"Erreur lors de la fermeture : {e}")
    
    def _run_tk(self):
        """Fonction exécutée dans le thread Tkinter"""
        try:
            self.fenetre = Tk()
            self.fenetre.title("Battleship")
            
            # Gérer la fermeture de la fenêtre proprement
            self.fenetre.protocol("WM_DELETE_WINDOW", self._on_closing)
            
            self.create_fenetre()
            
            # Signaler que l'interface est prête
            self.result_queue.put(True)
            
            # Vérifier régulièrement la file de commandes
            self._process_commands()
            
            # Lancer la boucle principale
            self.fenetre.mainloop()
            
        except Exception as e:
            # Capturer et signaler les erreurs
            self.error = e
            self.result_queue.put(e)
            print(f"ERREUR dans le thread Tkinter : {e}")
            traceback.print_exc()
        finally:
            # Nettoyage
            self.running = False
            if self.fenetre:
                try:
                    self.fenetre.destroy()
                except:
                    pass
    
    def _on_closing(self):
        """Appelé quand l'utilisateur ferme la fenêtre"""
        self.running = False
        if self.fenetre:
            self.fenetre.quit()
    
    def _process_commands(self):
        """Traite les commandes de la file d'attente"""
        try:
            while True:
                command, args, kwargs = self.command_queue.get_nowait()
                try:
                    result = command(*args, **kwargs)
                    self.result_queue.put(result)
                except Exception as e:
                    # Capturer les erreurs dans les commandes
                    print(f"Erreur lors de l'exécution d'une commande : {e}")
                    traceback.print_exc()
                    self.result_queue.put(e)
        except queue.Empty:
            pass
        
        # Rappeler cette fonction après 100ms
        if self.running and self.fenetre:
            try:
                self.fenetre.after(100, self._process_commands)
            except:
                pass  # Fenêtre déjà détruite
    
    def execute_command(self, command, *args, timeout=None, **kwargs):
        """Exécute une commande dans le thread Tkinter de manière thread-safe
        
        Args:
            command: La fonction à exécuter
            timeout: Temps d'attente max en secondes (None = infini)
            *args, **kwargs: Arguments pour la commande
            
        Returns:
            Le résultat de la commande
            
        Raises:
            queue.Empty: Si timeout est dépassé
            Exception: Si la commande lève une exception
        """
        if not self.running:
            raise RuntimeError("L'interface n'est pas en cours d'exécution")
        
        self.command_queue.put((command, args, kwargs))
        result = self.result_queue.get(timeout=timeout)
        
        # Si le résultat est une exception, la relancer
        if isinstance(result, Exception):
            raise result
        
        return result

    def create_canvas(self):
        cote = self.nb_cases * self.taille_case  # 500 pixels
        
        # Ajouter des marges pour les labels
        marge = 30
        
        self.canvas = Canvas(
            self.fenetre, 
            width=cote + marge, 
            height=cote + marge, 
            bg="white", 
            highlightthickness=0
        )
        self.canvas.pack(padx=10, pady=10)

        self.canvas.bind("<Button-1>", self.recuperer_case)
        
        # Ajouter les labels des colonnes (A-J) en haut
        for i in range(self.nb_cases):
            x_pos = marge + i * self.taille_case + self.taille_case // 2
            self.canvas.create_text(x_pos, 15, text=chr(65 + i), font=("Arial", 10, "bold"))
        
        # Ajouter les labels des lignes (0-9) à gauche
        for i in range(self.nb_cases):
            y_pos = marge + i * self.taille_case + self.taille_case // 2
            self.canvas.create_text(15, y_pos, text=str(i), font=("Arial", 10, "bold"))

        # Tracé de la grille (décalée par la marge)
        for i in range(self.nb_cases + 1):
            pos = marge + i * self.taille_case
            # Lignes horizontales
            self.canvas.create_line(marge, pos, cote + marge, pos, fill="lightgray")
            # Lignes verticales
            self.canvas.create_line(pos, marge, pos, cote + marge, fill="lightgray")

    def recuperer_case(self, event):
        # Ajuster pour la marge des labels
        x_adjusted = event.x - self.marge
        y_adjusted = event.y - self.marge
        
        # Dans Tkinter : event.x = horizontal (colonne), event.y = vertical (ligne)
        # Dans le jeu : Position(x, y) où x = colonne (correspondant au CLI), y = ligne
        colonne = x_adjusted // self.taille_case
        ligne = y_adjusted // self.taille_case
        
        # Vérifier que les coordonnées sont valides
        if 0 <= ligne < self.nb_cases and 0 <= colonne < self.nb_cases:
            print(f"Clic sur la case : {chr(65 + colonne)}{ligne}")
            
            # Si on attend un clic, l'envoyer dans la queue (colonne, ligne pour correspondre au CLI)
            # Car le CLI utilise cases[colonne][ligne]
            if self.waiting_for_click:
                self.click_queue.put((colonne, ligne))
                self.waiting_for_click = False
                # Colorier en jaune pour indiquer la sélection
                self.colorier_case(colonne, ligne, "yellow")
            else:
                # Sinon, juste colorier pour confirmation
                x1 = self.marge + colonne * self.taille_case
                y1 = self.marge + ligne * self.taille_case
                x2 = x1 + self.taille_case
                y2 = y1 + self.taille_case
                self.canvas.create_rectangle(x1, y1, x2, y2, fill="lightblue", outline="gray")

    def wait_for_click(self, timeout=None):
        """Attend qu'un joueur clique sur une case
        
        Args:
            timeout: Temps d'attente max en secondes (None = infini)
            
        Returns:
            Tuple (ligne, colonne) ou None si timeout
        """
        self.waiting_for_click = True
        try:
            return self.click_queue.get(timeout=timeout)
        except queue.Empty:
            self.waiting_for_click = False
            return None
    
    def colorier_case(self, x, y, couleur="red"):
        """Colorie une case spécifique (thread-safe)
        
        Args:
            x: Colonne de la case (0-9) - correspond à x dans Position et cases[x][y]
            y: Ligne de la case (0-9) - correspond à y dans Position et cases[x][y]
            couleur: Couleur à appliquer
        """
        def _colorier():
            if not self.canvas:
                raise RuntimeError("Canvas non initialisé")
            # Dans le canvas Tkinter : event.x = horizontal (colonne), event.y = vertical (ligne)
            # x correspond à la colonne (horizontal), y correspond à la ligne (vertical)
            x1 = self.marge + x * self.taille_case
            y1 = self.marge + y * self.taille_case
            x2 = x1 + self.taille_case
            y2 = y1 + self.taille_case
            self.canvas.create_rectangle(x1, y1, x2, y2, fill=couleur, outline="gray")
        
        if threading.current_thread() == self.thread:
            _colorier()
        else:
            self.execute_command(_colorier, timeout=2)
    
    def afficher_message(self, message):
        """Affiche un message dans le titre de la fenêtre (thread-safe)"""
        def _afficher():
            if self.fenetre:
                self.fenetre.title(f"Battleship - {message}")
        
        if threading.current_thread() == self.thread:
            _afficher()
        else:
            try:
                self.execute_command(_afficher, timeout=1)
            except:
                pass
    
    def create_fenetre(self):
        # bouton de sortie
        bouton = Button(self.fenetre, text="Fermer", command=self._on_closing)
        bouton.pack()

        self.create_canvas()