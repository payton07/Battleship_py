from flask import Flask, request, jsonify, render_template
import sys, os, uuid, random, sqlite3

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from classes.grid import Grid
from classes.ship import Ship
from classes.position import Position
from classes.orientation import Orientation
from classes.variable import Variable
from classes.predefined_grids import PredefinedGrids
from players.player import Player
from players.cheat_bot import CheatBot
from game_logic.game import Game
from database.db_manager import DatabaseManager

app = Flask(__name__)
games = {}

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'battleship_stats.db')


class WebGame:
    def __init__(self, player_name):
        self.player_name = player_name
        self.phase = 'setup'
        self.current_turn = 'player'
        self.player_shots_left = Variable.SHOTS_PER_TURN
        self.turn_number = 1
        self.bot_shots_this_turn = []
        self.action_log = []
        self.last_turn_id = None

        self.player = Player(player_name)
        self.bot = CheatBot('Pepper Bot')

        self.game = Game()
        self.game.add_player(self.player)
        self.game.add_player(self.bot)

        try:
            self.db = DatabaseManager(DB_PATH)
            self.game_id = self.db.create_game(player_name, 'Digital-Web')
        except Exception:
            self.db = None
            self.game_id = None

    def get_grid_preview(self, index):
        config = PredefinedGrids.get_grid(index)
        temp = Grid()
        for size, x, y, ov in config:
            temp.place_ship(Ship(size, Position(x, y), Orientation(ov)))
        return self._serialize(temp)

    def select_grid(self, index):
        config = PredefinedGrids.get_grid(index)
        self.game.place_predefined_ships(self.player, config)
        self.game.place_all_ships(self.bot)
        if isinstance(self.bot, CheatBot):
            self.bot.set_target_grid(self.player.get_my_grid())
        self.phase = 'playing'

    def _serialize(self, grid, hide_ships=False):
        size = Variable.get_size_grid()
        return [
            [
                Variable.CASE_DEFAULT if (hide_ships and grid.cases[x][y] == Variable.CASE_BATEAU) else grid.cases[x][y]
                for x in range(size)
            ]
            for y in range(size)
        ]

    def _is_over(self):
        r = self.game.is_game_over()
        if r.get_success() == 1:
            self.phase = 'game_over'
            msg = r.get_message()
            winner = 'player' if self.player_name in msg else 'bot'
            return True, winner, msg
        return False, None, None

    def _grids(self, reveal_bot=False):
        return {
            'player_grid': self._serialize(self.player.get_my_grid()),
            'enemy_grid': self._serialize(self.bot.get_my_grid(), hide_ships=not reveal_bot),
        }

    def player_shoot(self, x, y):
        if self.current_turn != 'player' or self.phase != 'playing':
            return {'error': 'Not your turn'}

        self.player.set_next_shot(x, y)
        result = self.game.play(self.player)

        if result in (Variable.MESSAGE_DEJA_JOUE, Variable.MESSAGE_HORS_GRILLE):
            return {'result': result, 'invalid': True, 'shots_left': self.player_shots_left}

        self.player_shots_left -= 1
        col = chr(65 + x)
        self.action_log.insert(0, {
            'actor': self.player_name, 'coord': f"{col}{y}",
            'result': result, 'type': 'player'
        })

        over, winner, msg = self._is_over()
        if over:
            self._save_winner(winner)
            return {**self._grids(reveal_bot=True), 'result': result,
                    'game_over': True, 'winner': winner, 'message': msg,
                    'shots_left': self.player_shots_left}

        turn_ended = False
        if self.player_shots_left <= 0:
            self.game.next_turn()
            self.current_turn = 'bot'
            self.bot_shots_this_turn = []
            if isinstance(self.bot, CheatBot):
                self.bot.set_success_quota(random.randint(0, 3))
            turn_ended = True

        return {
            **self._grids(),
            'result': result,
            'shots_left': self.player_shots_left,
            'game_over': False,
            'turn_ended': turn_ended,
            'x': x, 'y': y,
        }

    def execute_bot_turn(self):
        if self.current_turn != 'bot' or self.phase != 'playing':
            return {'error': 'Not bot turn'}

        shots = []
        for _ in range(Variable.SHOTS_PER_TURN):
            result = self.game.play(self.bot)
            pos = self.bot.last_played_pos
            sx = pos.get_x() if pos else -1
            sy = pos.get_y() if pos else -1
            col = chr(65 + sx) if sx >= 0 else '?'

            shot = {'x': sx, 'y': sy, 'coord': f"{col}{sy}", 'result': result}
            shots.append(shot)
            self.bot_shots_this_turn.append({'x': sx, 'y': sy, 'result': result})
            self.action_log.insert(0, {'actor': 'Pepper Bot', **shot, 'type': 'bot'})

            over, winner, msg = self._is_over()
            if over:
                self._save_winner(winner)
                return {**self._grids(reveal_bot=True),
                        'shots': shots, 'game_over': True, 'winner': winner, 'message': msg}

        self.game.next_turn()
        self.current_turn = 'player'
        self.player_shots_left = Variable.SHOTS_PER_TURN
        self.turn_number += 1

        if self.db and self.game_id:
            try:
                quota = self.bot.success_quota if isinstance(self.bot, CheatBot) else 0
                self.last_turn_id = self.db.save_full_turn(
                    self.game_id, self.turn_number, quota, None, self.bot_shots_this_turn
                )
            except Exception:
                pass

        return {
            **self._grids(),
            'shots': shots,
            'game_over': False,
            'shots_left': self.player_shots_left,
            'turn_number': self.turn_number,
        }

    def _save_winner(self, winner_key):
        if self.db and self.game_id:
            name = self.player_name if winner_key == 'player' else 'Pepper Bot'
            try:
                self.db.update_game_winner(self.game_id, name)
            except Exception:
                pass

    def submit_turn_trust(self, score):
        """Enregistre le score de confiance du dernier tour du bot."""
        if self.db and self.last_turn_id:
            try:
                self.db.update_turn_trust(self.last_turn_id, score)
            except Exception:
                pass

    def submit_trust(self, score):
        if self.db and self.game_id:
            try:
                self.db.update_game_trust(self.game_id, score)
            except Exception:
                pass

    def get_state(self):
        return {
            'phase': self.phase,
            'current_turn': self.current_turn,
            'shots_left': self.player_shots_left,
            'turn_number': self.turn_number,
            **self._grids(),
            'action_log': self.action_log[:10],
        }


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/game')
def game_page():
    return render_template('game.html')

@app.route('/api/game/new', methods=['POST'])
def new_game():
    data = request.json or {}
    name = (data.get('player_name') or 'Joueur').strip() or 'Joueur'
    gid = str(uuid.uuid4())
    games[gid] = WebGame(name)
    return jsonify({'game_id': gid})

@app.route('/api/game/<gid>/preview/<int:idx>')
def preview(gid, idx):
    wg = games.get(gid)
    if not wg:
        return jsonify({'error': 'not found'}), 404
    return jsonify({'cells': wg.get_grid_preview(idx)})

@app.route('/api/game/<gid>/select-grid', methods=['POST'])
def select_grid(gid):
    wg = games.get(gid)
    if not wg:
        return jsonify({'error': 'not found'}), 404
    idx = (request.json or {}).get('index', 0)
    wg.select_grid(idx)
    return jsonify(wg.get_state())

@app.route('/api/game/<gid>/shoot', methods=['POST'])
def shoot(gid):
    wg = games.get(gid)
    if not wg:
        return jsonify({'error': 'not found'}), 404
    data = request.json or {}
    return jsonify(wg.player_shoot(data.get('x', 0), data.get('y', 0)))

@app.route('/api/game/<gid>/bot-turn', methods=['POST'])
def bot_turn(gid):
    wg = games.get(gid)
    if not wg:
        return jsonify({'error': 'not found'}), 404
    return jsonify(wg.execute_bot_turn())

@app.route('/api/game/<gid>/turn-trust', methods=['POST'])
def turn_trust(gid):
    wg = games.get(gid)
    if not wg:
        return jsonify({'error': 'not found'}), 404
    score = (request.json or {}).get('score', 0)
    wg.submit_turn_trust(score)
    return jsonify({'ok': True})

@app.route('/api/game/<gid>/trust', methods=['POST'])
def trust(gid):
    wg = games.get(gid)
    if not wg:
        return jsonify({'error': 'not found'}), 404
    score = (request.json or {}).get('score', 3)
    wg.submit_trust(score)
    return jsonify({'ok': True})

@app.route('/api/stats')
def api_stats():
    try:
        with sqlite3.connect(DB_PATH) as conn:
            total = conn.execute("SELECT COUNT(*) FROM Game").fetchone()[0]
            avg = conn.execute(
                "SELECT AVG(trust_score) FROM Game WHERE trust_score IS NOT NULL"
            ).fetchone()[0]
        return jsonify({'total_games': total, 'avg_trust': round(float(avg), 1) if avg else None})
    except Exception:
        return jsonify({'total_games': 0, 'avg_trust': None})

@app.route('/admin')
def admin_page():
    return render_template('admin.html')

@app.route('/api/admin/overview')
def admin_overview():
    try:
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            total_games    = c.execute("SELECT COUNT(*) FROM Game").fetchone()[0]
            unique_players = c.execute("SELECT COUNT(DISTINCT player_name) FROM Game").fetchone()[0]
            avg_trust      = c.execute("SELECT AVG(trust_score) FROM Turn WHERE trust_score IS NOT NULL").fetchone()[0]
            bot_wins       = c.execute("SELECT COUNT(*) FROM Game WHERE winner = 'Pepper Bot'").fetchone()[0]
            player_wins    = c.execute("SELECT COUNT(*) FROM Game WHERE winner IS NOT NULL AND winner != 'Pepper Bot'").fetchone()[0]
            total_turns    = c.execute("SELECT COUNT(*) FROM Turn").fetchone()[0]

            dist_rows = c.execute("""
                SELECT trust_score, COUNT(*) FROM Turn
                WHERE trust_score IS NOT NULL
                GROUP BY trust_score ORDER BY trust_score
            """).fetchall()

            quota_rows = c.execute("""
                SELECT bot_quota, ROUND(AVG(trust_score), 2), COUNT(*)
                FROM Turn WHERE trust_score IS NOT NULL AND bot_quota IS NOT NULL
                GROUP BY bot_quota ORDER BY bot_quota
            """).fetchall()

            avg_hits = c.execute("""
                SELECT AVG(h) FROM (
                    SELECT SUM(CASE WHEN result IN ('Touché','Coulé') THEN 1 ELSE 0 END) as h
                    FROM BotShot GROUP BY turn_id
                )
            """).fetchone()[0]

        return jsonify({
            'total_games':       total_games,
            'unique_players':    unique_players,
            'avg_trust':         round(float(avg_trust), 2) if avg_trust else 0,
            'bot_wins':          bot_wins,
            'player_wins':       player_wins,
            'total_turns':       total_turns,
            'avg_hits_per_turn': round(float(avg_hits), 1) if avg_hits else 0,
            'trust_distribution': {str(r[0]): r[1] for r in dist_rows},
            'quota_trust':        [{'quota': r[0], 'avg_trust': r[1], 'count': r[2]} for r in quota_rows],
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/games')
def admin_games_list():
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("""
                SELECT g.id, g.player_name, g.player_type, g.date_played, g.winner,
                       COUNT(DISTINCT t.id) as turn_count,
                       ROUND(AVG(t.trust_score), 1) as avg_trust
                FROM Game g
                LEFT JOIN Turn t ON t.game_id = g.id
                GROUP BY g.id
                ORDER BY g.date_played DESC
                LIMIT 200
            """).fetchall()
        return jsonify([dict(r) for r in rows])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/game/<int:gid>')
def admin_game_detail(gid):
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            game  = dict(conn.execute("SELECT * FROM Game WHERE id = ?", (gid,)).fetchone() or {})
            turns = [dict(r) for r in conn.execute(
                "SELECT * FROM Turn WHERE game_id = ? ORDER BY turn_number", (gid,)
            ).fetchall()]
            shots = [dict(r) for r in conn.execute("""
                SELECT bs.turn_id, bs.pos_x, bs.pos_y, bs.result
                FROM BotShot bs JOIN Turn t ON bs.turn_id = t.id
                WHERE t.game_id = ? ORDER BY t.turn_number, bs.shot_number
            """, (gid,)).fetchall()]

        shots_by_turn = {}
        for s in shots:
            shots_by_turn.setdefault(s['turn_id'], []).append(s)
        for t in turns:
            t['shots'] = shots_by_turn.get(t['id'], [])

        return jsonify({'game': game, 'turns': turns})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5001)
