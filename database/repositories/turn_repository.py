# -*- coding: utf-8 -*-
import psycopg2.extras


class TurnRepository:
    def __init__(self, db):
        self.db = db

    def save(self, game_id, turn_number, bot_quota, trust_score, bot_shots):
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """INSERT INTO Turn (game_id, turn_number, bot_quota, trust_score)
                   VALUES (%s, %s, %s, %s) RETURNING id""",
                (game_id, turn_number, bot_quota, trust_score)
            )
            turn_id = cur.fetchone()[0]
            for i, shot in enumerate(bot_shots):
                cur.execute(
                    """INSERT INTO BotShot (turn_id, shot_number, pos_x, pos_y, result)
                       VALUES (%s, %s, %s, %s, %s)""",
                    (turn_id, i + 1, shot['x'], shot['y'], shot['result'])
                )
            return turn_id

    def update_trust(self, turn_id, trust_score):
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "UPDATE Turn SET trust_score = %s WHERE id = %s",
                (trust_score, turn_id)
            )

    def find_by_game(self, game_id):
        with self.db.get_connection() as conn:
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cur.execute(
                "SELECT * FROM Turn WHERE game_id = %s ORDER BY turn_number",
                (game_id,)
            )
            turns = [dict(r) for r in cur.fetchall()]

            cur.execute("""
                SELECT bs.turn_id, bs.pos_x, bs.pos_y, bs.result
                FROM BotShot bs
                JOIN Turn t ON bs.turn_id = t.id
                WHERE t.game_id = %s
                ORDER BY t.turn_number, bs.shot_number
            """, (game_id,))
            shots = [dict(r) for r in cur.fetchall()]

        shots_by_turn = {}
        for s in shots:
            shots_by_turn.setdefault(s['turn_id'], []).append(s)
        for t in turns:
            t['shots'] = shots_by_turn.get(t['id'], [])

        return turns

    def get_overview_stats(self):
        with self.db.get_connection() as conn:
            cur = conn.cursor()

            cur.execute("SELECT COUNT(*) FROM Turn")
            total_turns = cur.fetchone()[0]

            cur.execute("SELECT AVG(trust_score) FROM Turn WHERE trust_score IS NOT NULL")
            avg_trust = cur.fetchone()[0]

            cur.execute("""
                SELECT trust_score, COUNT(*) FROM Turn
                WHERE trust_score IS NOT NULL
                GROUP BY trust_score ORDER BY trust_score
            """)
            dist_rows = cur.fetchall()

            cur.execute("""
                SELECT bot_quota, ROUND(AVG(trust_score)::numeric, 2), COUNT(*)
                FROM Turn
                WHERE trust_score IS NOT NULL AND bot_quota IS NOT NULL
                GROUP BY bot_quota ORDER BY bot_quota
            """)
            quota_rows = cur.fetchall()

            cur.execute("""
                SELECT AVG(h) FROM (
                    SELECT SUM(CASE WHEN result IN ('Touché','Coulé') THEN 1 ELSE 0 END) AS h
                    FROM BotShot GROUP BY turn_id
                ) AS sub
            """)
            avg_hits = cur.fetchone()[0]

            cur.execute("""
                SELECT t.bot_quota,
                       COUNT(DISTINCT t.game_id)                                        AS total,
                       COUNT(DISTINCT CASE WHEN g.trust_final = 1 THEN t.game_id END)   AS detected
                FROM Turn t
                JOIN Game g ON g.id = t.game_id
                WHERE g.trust_final IS NOT NULL AND t.bot_quota IS NOT NULL
                GROUP BY t.bot_quota ORDER BY t.bot_quota
            """)
            quota_detection_rows = cur.fetchall()

        return {
            'total_turns':       total_turns,
            'avg_trust':         round(float(avg_trust), 2) if avg_trust else 0,
            'trust_distribution': {str(r[0]): r[1] for r in dist_rows},
            'quota_trust':        [
                {'quota': r[0], 'avg_trust': float(r[1]) if r[1] else 0, 'count': r[2]}
                for r in quota_rows
            ],
            'avg_hits_per_turn': round(float(avg_hits), 1) if avg_hits else 0,
            'quota_detection':    [
                {'quota': r[0], 'total': r[1], 'detected': r[2],
                 'rate': round(100 * r[2] / r[1], 1) if r[1] else 0}
                for r in quota_detection_rows
            ],
        }
