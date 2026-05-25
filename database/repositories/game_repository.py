# -*- coding: utf-8 -*-
import psycopg2.extras


class GameRepository:
    def __init__(self, db):
        self.db = db

    def create(self, player_name, player_type):
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO Game (player_name, player_type) VALUES (%s, %s) RETURNING id",
                (player_name, player_type)
            )
            return cur.fetchone()[0]

    def update_winner(self, game_id, winner):
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("UPDATE Game SET winner = %s WHERE id = %s", (winner, game_id))

    def update_trust(self, game_id, trust_score):
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("UPDATE Game SET trust_score = %s WHERE id = %s", (trust_score, game_id))

    def update_trust_final(self, game_id, detected):
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "UPDATE Game SET trust_final = %s WHERE id = %s",
                (1 if detected else 0, game_id)
            )

    def find_all(self, limit=200):
        with self.db.get_connection() as conn:
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cur.execute("""
                SELECT g.id, g.player_name, g.player_type, g.date_played, g.winner,
                       g.trust_final,
                       COUNT(DISTINCT t.id)             AS turn_count,
                       ROUND(AVG(t.trust_score)::numeric, 1) AS avg_trust
                FROM Game g
                LEFT JOIN Turn t ON t.game_id = g.id
                GROUP BY g.id
                ORDER BY g.date_played DESC
                LIMIT %s
            """, (limit,))
            return [dict(r) for r in cur.fetchall()]

    def find_by_id(self, game_id):
        with self.db.get_connection() as conn:
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cur.execute("SELECT * FROM Game WHERE id = %s", (game_id,))
            row = cur.fetchone()
            return dict(row) if row else None

    def find_all_players(self):
        with self.db.get_connection() as conn:
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cur.execute("""
                SELECT
                    g.player_name,
                    COUNT(DISTINCT g.id)                          AS game_count,
                    MIN(g.date_played)                            AS first_seen,
                    MAX(g.date_played)                            AS last_seen,
                    ROUND(AVG(t.trust_score)::numeric, 1)         AS avg_trust,
                    COUNT(DISTINCT CASE WHEN g.trust_final = 1 THEN g.id END) AS detected_count,
                    COUNT(DISTINCT CASE WHEN g.trust_final IS NOT NULL THEN g.id END) AS answered_count,
                    COUNT(DISTINCT CASE WHEN g.winner != 'Pepper Bot' AND g.winner IS NOT NULL THEN g.id END) AS player_wins
                FROM Game g
                LEFT JOIN Turn t ON t.game_id = g.id
                GROUP BY g.player_name
                ORDER BY last_seen DESC
            """)
            return [dict(r) for r in cur.fetchall()]

    def delete_by_player(self, player_name):
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                DELETE FROM BotShot WHERE turn_id IN (
                    SELECT t.id FROM Turn t
                    JOIN Game g ON t.game_id = g.id
                    WHERE g.player_name = %s
                )
            """, (player_name,))
            cur.execute("""
                DELETE FROM Turn WHERE game_id IN (
                    SELECT id FROM Game WHERE player_name = %s
                )
            """, (player_name,))
            cur.execute("DELETE FROM Game WHERE player_name = %s", (player_name,))

    def delete_by_id(self, game_id):
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                DELETE FROM BotShot WHERE turn_id IN (
                    SELECT id FROM Turn WHERE game_id = %s
                )
            """, (game_id,))
            cur.execute("DELETE FROM Turn WHERE game_id = %s", (game_id,))
            cur.execute("DELETE FROM Game WHERE id = %s", (game_id,))

    def delete_all(self):
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("TRUNCATE TABLE BotShot, Turn, Game RESTART IDENTITY")

    def get_overview_stats(self):
        with self.db.get_connection() as conn:
            cur = conn.cursor()

            cur.execute("SELECT COUNT(*) FROM Game")
            total_games = cur.fetchone()[0]

            cur.execute("SELECT COUNT(DISTINCT player_name) FROM Game")
            unique_players = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM Game WHERE winner = 'Pepper Bot'")
            bot_wins = cur.fetchone()[0]

            cur.execute(
                "SELECT COUNT(*) FROM Game WHERE winner IS NOT NULL AND winner != 'Pepper Bot'"
            )
            player_wins = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM Game WHERE trust_final = 1")
            detected_count = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM Game WHERE trust_final IS NOT NULL")
            answered_count = cur.fetchone()[0]

        return {
            'total_games':    total_games,
            'unique_players': unique_players,
            'bot_wins':       bot_wins,
            'player_wins':    player_wins,
            'detected_count': detected_count,
            'answered_count': answered_count,
        }
