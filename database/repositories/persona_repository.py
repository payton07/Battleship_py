import psycopg2.extras


class PersonaRepository:
    def __init__(self, db):
        self.db = db

    def find_all_active(self):
        with self.db.get_connection() as conn:
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cur.execute(
                "SELECT id, name, emoji, description FROM BotPersona WHERE active = TRUE ORDER BY id"
            )
            return [dict(r) for r in cur.fetchall()]

    def find_all(self):
        with self.db.get_connection() as conn:
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cur.execute(
                "SELECT id, name, emoji, description, active FROM BotPersona ORDER BY id"
            )
            return [dict(r) for r in cur.fetchall()]

    def find_by_id(self, persona_id):
        with self.db.get_connection() as conn:
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cur.execute(
                "SELECT id, name, emoji, description, active FROM BotPersona WHERE id = %s",
                (persona_id,)
            )
            row = cur.fetchone()
            return dict(row) if row else None

    def create(self, name, emoji, description):
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO BotPersona (name, emoji, description) VALUES (%s, %s, %s) RETURNING id",
                (name, emoji, description)
            )
            return cur.fetchone()[0]

    def toggle_active(self, persona_id, active):
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "UPDATE BotPersona SET active = %s WHERE id = %s",
                (active, persona_id)
            )

    def delete(self, persona_id):
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM BotPersona WHERE id = %s", (persona_id,))
