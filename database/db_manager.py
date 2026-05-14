# -*- coding: utf-8 -*-
import sqlite3
import datetime
import os

class DatabaseManager(object):
    def __init__(self, db_path="battleship_stats.db"):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        """Initialise les tables si elles n'existent pas."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Table Game
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS Game (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    player_name TEXT,
                    player_type TEXT,
                    date_played DATETIME DEFAULT CURRENT_TIMESTAMP,
                    winner TEXT,
                    trust_score INTEGER
                )
            ''')
            
            # Table Turn
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS Turn (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    game_id INTEGER,
                    turn_number INTEGER,
                    bot_quota INTEGER,
                    trust_score INTEGER,
                    FOREIGN KEY (game_id) REFERENCES Game(id)
                )
            ''')
            
            # Table BotShot
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS BotShot (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    turn_id INTEGER,
                    shot_number INTEGER,
                    pos_x INTEGER,
                    pos_y INTEGER,
                    result TEXT,
                    FOREIGN KEY (turn_id) REFERENCES Turn(id)
                )
            ''')
            conn.commit()

    def create_game(self, player_name, player_type):
        """Crée une nouvelle partie et retourne son ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO Game (player_name, player_type) VALUES (?, ?)",
                (player_name, player_type)
            )
            return cursor.lastrowid

    def update_game_winner(self, game_id, winner):
        """Met à jour le gagnant à la fin de la partie."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE Game SET winner = ? WHERE id = ?",
                (winner, game_id)
            )
            conn.commit()

    def update_game_trust(self, game_id, trust_score):
        """Met à jour le score de confiance global de la partie."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE Game SET trust_score = ? WHERE id = ?",
                (trust_score, game_id)
            )
            conn.commit()

    def save_full_turn(self, game_id, turn_number, bot_quota, trust_score, bot_shots):
        """
        Enregistre un tour complet et ses tirs.
        bot_shots: liste de dictionnaires [{'x', 'y', 'result'}]
        Retourne le turn_id pour permettre une mise à jour ultérieure du trust_score.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO Turn (game_id, turn_number, bot_quota, trust_score) VALUES (?, ?, ?, ?)",
                (game_id, turn_number, bot_quota, trust_score)
            )
            turn_id = cursor.lastrowid

            for i, shot in enumerate(bot_shots):
                cursor.execute(
                    "INSERT INTO BotShot (turn_id, shot_number, pos_x, pos_y, result) VALUES (?, ?, ?, ?, ?)",
                    (turn_id, i + 1, shot['x'], shot['y'], shot['result'])
                )
            conn.commit()
            return turn_id

    def update_turn_trust(self, turn_id, trust_score):
        """Met à jour le score de confiance d'un tour spécifique."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE Turn SET trust_score = ? WHERE id = ?",
                (trust_score, turn_id)
            )
            conn.commit()
