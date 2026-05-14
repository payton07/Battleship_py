# PBattleship

Jeu de Bataille Navale développé dans le cadre d'un TER (Travail d'Étude et de Recherche) en Master 1 Génie Logiciel. Le projet explore la **détection de triche** par un joueur humain face à un bot adversaire qui triche de façon contrôlée, avec un robot Pepper comme interface physique.

---

## Concept

Le bot adverse (**CheatBot**) a accès à la grille du joueur et peut viser directement ses bateaux. Cependant, pour paraître naturel, il respecte un **quota de succès** aléatoire par tour (0 à 3 touches sur 4 tirs). En fin de partie, le joueur évalue sur une échelle de 0 à 5 s'il a perçu la triche. Ces données sont enregistrées pour analyse.

---

## Fonctionnalités

- **Deux modes de jeu** : Console (texte) et Graphique (Tkinter)
- **Deux modes adversaire** :
  - *Digital* : le joueur joue sur PC, le CheatBot voit sa grille et triche
  - *Hybride* : le joueur joue sur une grille papier et déclare manuellement les résultats
- **CheatBot** avec quota de succès variable pour simuler un comportement humain
- **Communication socket** avec un robot Pepper (envoi des tirs en temps réel)
- **Persistance SQLite** : historique des parties, tours, tirs du bot et scores de confiance
- **10 configurations de grille** prédéfinies + générateur aléatoire
- **4 tirs par tour** par joueur

---

## Prérequis

- Python 3.x
- `tkinter` (inclus dans la plupart des distributions Python)
- `sqlite3` (inclus dans Python)
- Accès réseau au robot Pepper sur `10.161.177.181:5000` (optionnel — la connexion échoue silencieusement)

---

## Lancement

```bash
python main.py
```

Choisissez ensuite le mode :
- `1` — Mode Console
- `2` — Mode Graphique (Tkinter)

---

## Structure du projet

```
PBattleship/
├── main.py                      # Point d'entrée
├── classes/
│   ├── variable.py              # Constantes globales (taille, symboles, messages)
│   ├── grid.py                  # Grille de jeu (placement, tirs, état)
│   ├── ship.py                  # Bateau (positions, gestion des touches)
│   ├── position.py              # Coordonnée (x, y)
│   ├── orientation.py           # HORIZONTAL / VERTICAL
│   ├── response.py              # Résultat d'un tir (code + message)
│   ├── predefined_grids.py      # 10 configurations de grilles prédéfinies
│   └── grid_generator.py        # Génération aléatoire de configurations
├── players/
│   ├── player.py                # Joueur de base (saisie console)
│   ├── bot.py                   # Bot aléatoire pur
│   ├── smart_bot.py             # Bot avec stratégie chasse/ciblage
│   ├── cheat_bot.py             # Bot tricheur (accès grille + quota de succès)
│   └── physical_player.py       # Joueur papier (déclare les résultats manuellement)
├── game_logic/
│   ├── game.py                  # Arbitre (tours, tirs, détection de fin)
│   └── game_master.py           # Orchestrateur (setup, boucle de jeu, BDD)
├── interface/
│   └── interface_tk.py          # Interface graphique Tkinter
├── client/
│   └── client.py                # Client socket TCP vers le robot Pepper
├── database/
│   └── db_manager.py            # Gestionnaire SQLite
├── tests/
│   ├── test_game.py
│   ├── test_grid.py
│   └── test_ship.py
└── battleship_stats.db          # Base de données générée au premier lancement
```

---

## Fonctionnement du CheatBot

Le `CheatBot` implémente une triche discrète en trois étapes à chaque tour :

1. **Analyse** de la grille ennemie — il identifie toutes les cases de bateau non encore touchées et toutes les cases d'eau intactes
2. **Quota** — il sélectionne aléatoirement N touches (0 ≤ N ≤ 3) et complète à 4 tirs avec de l'eau
3. **Mélange** — les tirs sont mélangés aléatoirement pour masquer la stratégie

Chaque tir est également transmis au robot Pepper via socket TCP au format `P<colonne><ligne>` (ex: `PA3`).

---

## Base de données

La base SQLite `battleship_stats.db` contient trois tables :

| Table | Contenu |
|-------|---------|
| `Game` | Nom du joueur, type (Digital/Papier), date, gagnant, score de confiance final |
| `Turn` | Numéro du tour, quota du bot, score de confiance |
| `BotShot` | Coordonnées et résultat de chaque tir du bot |

---

## Paramètres configurables

Tous les paramètres globaux sont centralisés dans `classes/variable.py` :

| Paramètre | Valeur par défaut | Description |
|-----------|-------------------|-------------|
| `SIZE_GRID` | `10` | Taille de la grille |
| `SHIP_SIZES` | `[5, 4, 3, 3, 2]` | Tailles des bateaux |
| `SHOTS_PER_TURN` | `4` | Nombre de tirs par tour |

---

## Tests

```bash
python -m pytest tests/
```

---

## Interface Web (Site/)

Le projet inclut une **interface web complète** permettant de jouer depuis un navigateur, conçue pour la collecte de données à grande échelle.

### Lancement

```bash
cd Site
pip install flask
python app.py
# → http://localhost:5001
```

### Fonctionnalités du site

- **Page d'accueil** attractive avec animation de particules et compteur de parties en temps réel
- **Sélection de grille** interactive (navigation clavier/souris, aperçu live)
- **Jeu complet** dans le navigateur : tirs cliquables, animation séquentielle des tirs du bot, journal de bord
- **Évaluation finale** : slider de confiance 0–5, données envoyées en base SQLite
- Design inspiré des jeux mobiles/web (thème dark navy, effets neon, animations CSS)

### Structure du site

```
Site/
├── app.py                  # Backend Flask (API REST + serveur de pages)
├── requirements.txt        # flask>=2.3
├── templates/
│   ├── index.html          # Page d'accueil
│   └── game.html           # Page de jeu (3 écrans : setup → grille → combat)
└── static/
    ├── css/style.css       # Feuille de styles complète
    └── js/game.js          # Logique client (state machine, appels API, animations)
```

### API REST

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| `POST` | `/api/game/new` | Crée une nouvelle partie |
| `GET` | `/api/game/<id>/preview/<n>` | Aperçu de la configuration n |
| `POST` | `/api/game/<id>/select-grid` | Valide la configuration choisie |
| `POST` | `/api/game/<id>/shoot` | Effectue un tir joueur (x, y) |
| `POST` | `/api/game/<id>/bot-turn` | Exécute le tour complet du bot (4 tirs) |
| `POST` | `/api/game/<id>/trust` | Enregistre le score de confiance |
| `GET` | `/api/stats` | Statistiques globales (parties, score moyen) |

> Documentation complète : voir [`Site/SITE.md`](Site/SITE.md)
