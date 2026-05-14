# -*- coding: utf-8 -*-
from contextlib import contextmanager
import psycopg2
import psycopg2.extras


class Database:
    def __init__(self, url):
        self.url = url

    @contextmanager
    def get_connection(self):
        conn = psycopg2.connect(self.url)
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def init(self):
        with self.get_connection() as conn:
            cur = conn.cursor()

            cur.execute("""
                CREATE TABLE IF NOT EXISTS Game (
                    id          SERIAL PRIMARY KEY,
                    player_name TEXT,
                    player_type TEXT,
                    date_played TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    winner      TEXT,
                    trust_score INTEGER,
                    trust_final INTEGER
                )
            """)

            cur.execute("""
                CREATE TABLE IF NOT EXISTS Turn (
                    id          SERIAL PRIMARY KEY,
                    game_id     INTEGER REFERENCES Game(id),
                    turn_number INTEGER,
                    bot_quota   INTEGER,
                    trust_score INTEGER
                )
            """)

            cur.execute("""
                CREATE TABLE IF NOT EXISTS BotShot (
                    id          SERIAL PRIMARY KEY,
                    turn_id     INTEGER REFERENCES Turn(id),
                    shot_number INTEGER,
                    pos_x       INTEGER,
                    pos_y       INTEGER,
                    result      TEXT
                )
            """)

            cur.execute("""
                ALTER TABLE Game ADD COLUMN IF NOT EXISTS trust_final INTEGER
            """)
