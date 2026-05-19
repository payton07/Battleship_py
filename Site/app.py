from flask import Flask, request, jsonify, render_template, Response
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from dotenv import load_dotenv
import sys, os, uuid, functools, time, logging

load_dotenv()

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
from database.connection import Database
from database.repositories.game_repository import GameRepository
from database.repositories.turn_repository import TurnRepository
from database.repositories.persona_repository import PersonaRepository

# ── Config depuis variables d'environnement ───────────────────────────────────
SECRET_KEY     = os.environ.get('SECRET_KEY')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD')
DATABASE_URL   = os.environ.get('DATABASE_URL')

if not SECRET_KEY:
    raise RuntimeError("Variable d'environnement SECRET_KEY manquante. Créer un fichier .env.")
if not ADMIN_PASSWORD:
    raise RuntimeError("Variable d'environnement ADMIN_PASSWORD manquante. Créer un fichier .env.")
if not DATABASE_URL:
    raise RuntimeError("Variable d'environnement DATABASE_URL manquante. Créer un fichier .env.")

# ── App ───────────────────────────────────────────────────────────────────────
app = Flask(__name__)
app.secret_key = SECRET_KEY

logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s %(levelname)s %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)

# ── Rate limiting ─────────────────────────────────────────────────────────────
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["500 per day", "100 per hour"],
    storage_uri="memory://",
)

# ── Repositories (partagés par toute l'app) ───────────────────────────────────
_db        = Database(DATABASE_URL)
_db.init()
game_repo    = GameRepository(_db)
turn_repo    = TurnRepository(_db)
persona_repo = PersonaRepository(_db)

# ── Sessions de jeu ───────────────────────────────────────────────────────────
games    = {}
GAME_TTL = 7200  # 2 heures

def cleanup_old_games():
    cutoff = time.time() - GAME_TTL
    stale = [gid for gid, wg in list(games.items()) if wg.created_at < cutoff]
    for gid in stale:
        del games[gid]

# ── Headers de sécurité ───────────────────────────────────────────────────────
@app.after_request
def add_security_headers(resp):
    resp.headers['X-Content-Type-Options']  = 'nosniff'
    resp.headers['X-Frame-Options']         = 'DENY'
    resp.headers['X-XSS-Protection']        = '1; mode=block'
    resp.headers['Referrer-Policy']         = 'strict-origin-when-cross-origin'
    resp.headers['Content-Security-Policy'] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; "
        "img-src 'self' data:; "
        "connect-src 'self';"
    )
    resp.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    return resp

# ── Validation des entrées ────────────────────────────────────────────────────
def validate_int(value, min_val, max_val):
    try:
        v = int(value)
        if min_val <= v <= max_val:
            return v
    except (TypeError, ValueError):
        pass
    return None

def validate_uuid(value):
    try:
        return str(uuid.UUID(str(value)))
    except (ValueError, AttributeError):
        return None

def sanitize_name(value):
    if not value:
        return 'Joueur'
    name = str(value).strip()[:24]
    return name or 'Joueur'

# ── Authentification admin ────────────────────────────────────────────────────
def require_admin(f):
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or auth.password != ADMIN_PASSWORD:
            ip = request.headers.get('X-Forwarded-For', request.remote_addr)
            logger.warning("Admin auth failed from IP %s on %s", ip, request.path)
            return Response(
                'Accès refusé.',
                401,
                {'WWW-Authenticate': 'Basic realm="Admin PBattleship"'}
            )
        return f(*args, **kwargs)
    return decorated


# ══════════════════════════════════════════════════════════════════════════════
#  WebGame
# ══════════════════════════════════════════════════════════════════════════════

class WebGame:
    def __init__(self, player_name, bot_name='Pepper Bot', bot_emoji='🤖'):
        self.player_name    = player_name
        self.bot_name       = bot_name
        self.bot_emoji      = bot_emoji
        self.phase          = 'setup'
        self.current_turn   = 'player'
        self.player_shots_left = Variable.SHOTS_PER_TURN
        self.turn_number    = 1
        self.bot_shots_this_turn = []
        self.action_log     = []
        self.last_turn_id   = None
        self.created_at     = time.time()

        self.player = Player(player_name)
        self.bot    = CheatBot(bot_name)

        self.game = Game()
        self.game.add_player(self.player)
        self.game.add_player(self.bot)

        self.quota_sequence = Variable.QUOTA_SEQUENCE
        self.quota_index    = 0

        try:
            self.game_id = game_repo.create(player_name, 'Digital-Web')
        except Exception as e:
            logger.error("create_game error: %s", e)
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
                Variable.CASE_DEFAULT if (hide_ships and grid.cases[x][y] == Variable.CASE_BATEAU)
                else grid.cases[x][y]
                for x in range(size)
            ]
            for y in range(size)
        ]

    def _is_over(self):
        r = self.game.is_game_over()
        if r.get_success() == 1:
            self.phase = 'game_over'
            msg    = r.get_message()
            winner = 'player' if self.player_name in msg else 'bot'
            return True, winner, msg
        return False, None, None

    def _grids(self, reveal_bot=False):
        return {
            'player_grid': self._serialize(self.player.get_my_grid()),
            'enemy_grid':  self._serialize(self.bot.get_my_grid(), hide_ships=not reveal_bot),
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
            self.current_turn        = 'bot'
            self.bot_shots_this_turn = []
            turn_ended               = True

        return {
            **self._grids(),
            'result':     result,
            'shots_left': self.player_shots_left,
            'game_over':  False,
            'turn_ended': turn_ended,
            'x': x, 'y': y,
        }

    def execute_bot_turn(self):
        if self.current_turn != 'bot' or self.phase != 'playing':
            return {'error': 'Not bot turn'}

        quota = self.quota_sequence[self.quota_index % len(self.quota_sequence)]
        self.quota_index += 1
        if isinstance(self.bot, CheatBot):
            self.bot.set_success_quota(quota)

        shots = []
        for _ in range(Variable.SHOTS_PER_TURN):
            result = self.game.play(self.bot)
            pos    = self.bot.last_played_pos
            sx     = pos.get_x() if pos else -1
            sy     = pos.get_y() if pos else -1
            col    = chr(65 + sx) if sx >= 0 else '?'

            shot = {'x': sx, 'y': sy, 'coord': f"{col}{sy}", 'result': result}
            shots.append(shot)
            self.bot_shots_this_turn.append({'x': sx, 'y': sy, 'result': result})
            self.action_log.insert(0, {'actor': self.bot_name, **shot, 'type': 'bot'})

            over, winner, msg = self._is_over()
            if over:
                self._save_winner(winner)
                return {**self._grids(reveal_bot=True),
                        'shots': shots, 'game_over': True, 'winner': winner, 'message': msg}

        self.game.next_turn()
        self.current_turn      = 'player'
        self.player_shots_left = Variable.SHOTS_PER_TURN
        self.turn_number      += 1

        if self.game_id:
            try:
                self.last_turn_id = turn_repo.save(
                    self.game_id, self.turn_number, quota, None, self.bot_shots_this_turn
                )
            except Exception as e:
                logger.error("save_turn error: %s", e)

        return {
            **self._grids(),
            'shots':       shots,
            'game_over':   False,
            'shots_left':  self.player_shots_left,
            'turn_number': self.turn_number,
        }

    def _save_winner(self, winner_key):
        if self.game_id:
            name = self.player_name if winner_key == 'player' else self.bot_name
            try:
                game_repo.update_winner(self.game_id, name)
            except Exception as e:
                logger.error("update_winner error: %s", e)

    def submit_turn_trust(self, score):
        if self.last_turn_id:
            try:
                turn_repo.update_trust(self.last_turn_id, score)
            except Exception as e:
                logger.error("update_turn_trust error: %s", e)

    def submit_final_trust(self, detected):
        if self.game_id:
            try:
                game_repo.update_trust_final(self.game_id, detected)
            except Exception as e:
                logger.error("update_trust_final error: %s", e)

    def submit_trust(self, score):
        if self.game_id:
            try:
                game_repo.update_trust(self.game_id, score)
            except Exception as e:
                logger.error("update_trust error: %s", e)

    def get_state(self):
        return {
            'phase':        self.phase,
            'current_turn': self.current_turn,
            'shots_left':   self.player_shots_left,
            'turn_number':  self.turn_number,
            'bot_name':     self.bot_name,
            'bot_emoji':    self.bot_emoji,
            **self._grids(),
            'action_log':   self.action_log[:10],
        }


# ══════════════════════════════════════════════════════════════════════════════
#  Routes publiques
# ══════════════════════════════════════════════════════════════════════════════

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/game')
def game_page():
    return render_template('game.html')

@app.route('/api/personas')
@limiter.limit("60 per minute")
def api_personas():
    try:
        return jsonify(persona_repo.find_all_active())
    except Exception as e:
        logger.error("api_personas error: %s", e)
        return jsonify([])

@app.route('/api/game/new', methods=['POST'])
@limiter.limit("10 per hour")
def new_game():
    cleanup_old_games()
    data       = request.json or {}
    name       = sanitize_name(data.get('player_name'))
    persona_id = validate_int(data.get('persona_id'), 1, 9999)

    bot_name  = 'Pepper Bot'
    bot_emoji = '🤖'
    if persona_id:
        persona = persona_repo.find_by_id(persona_id)
        if persona and persona['active']:
            bot_name  = persona['name']
            bot_emoji = persona['emoji'] or '🤖'

    gid        = str(uuid.uuid4())
    games[gid] = WebGame(name, bot_name, bot_emoji)
    return jsonify({'game_id': gid, 'bot_name': bot_name, 'bot_emoji': bot_emoji})

@app.route('/api/game/<gid>/preview/<int:idx>')
@limiter.limit("60 per minute")
def preview(gid, idx):
    if validate_uuid(gid) is None:
        return jsonify({'error': 'invalid id'}), 400
    if validate_int(idx, 0, 9) is None:
        return jsonify({'error': 'invalid index'}), 400
    wg = games.get(gid)
    if not wg:
        return jsonify({'error': 'not found'}), 404
    return jsonify({'cells': wg.get_grid_preview(idx)})

@app.route('/api/game/<gid>/select-grid', methods=['POST'])
def select_grid(gid):
    if validate_uuid(gid) is None:
        return jsonify({'error': 'invalid id'}), 400
    wg = games.get(gid)
    if not wg:
        return jsonify({'error': 'not found'}), 404
    idx = validate_int((request.json or {}).get('index'), 0, 9)
    if idx is None:
        return jsonify({'error': 'invalid index'}), 400
    wg.select_grid(idx)
    return jsonify(wg.get_state())

@app.route('/api/game/<gid>/shoot', methods=['POST'])
def shoot(gid):
    if validate_uuid(gid) is None:
        return jsonify({'error': 'invalid id'}), 400
    wg = games.get(gid)
    if not wg:
        return jsonify({'error': 'not found'}), 404
    data = request.json or {}
    x = validate_int(data.get('x'), 0, 9)
    y = validate_int(data.get('y'), 0, 9)
    if x is None or y is None:
        return jsonify({'error': 'invalid coordinates'}), 400
    return jsonify(wg.player_shoot(x, y))

@app.route('/api/game/<gid>/bot-turn', methods=['POST'])
def bot_turn(gid):
    if validate_uuid(gid) is None:
        return jsonify({'error': 'invalid id'}), 400
    wg = games.get(gid)
    if not wg:
        return jsonify({'error': 'not found'}), 404
    return jsonify(wg.execute_bot_turn())

@app.route('/api/game/<gid>/final-trust', methods=['POST'])
def final_trust(gid):
    if validate_uuid(gid) is None:
        return jsonify({'error': 'invalid id'}), 400
    wg = games.get(gid)
    if not wg:
        return jsonify({'error': 'not found'}), 404
    detected = (request.json or {}).get('detected')
    if not isinstance(detected, bool):
        return jsonify({'error': 'invalid value'}), 400
    wg.submit_final_trust(detected)
    return jsonify({'ok': True})

@app.route('/api/game/<gid>/turn-trust', methods=['POST'])
def turn_trust(gid):
    if validate_uuid(gid) is None:
        return jsonify({'error': 'invalid id'}), 400
    wg = games.get(gid)
    if not wg:
        return jsonify({'error': 'not found'}), 404
    score = validate_int((request.json or {}).get('score'), 0, 5)
    if score is None:
        return jsonify({'error': 'invalid score'}), 400
    wg.submit_turn_trust(score)
    return jsonify({'ok': True})

@app.route('/api/game/<gid>/trust', methods=['POST'])
def trust(gid):
    if validate_uuid(gid) is None:
        return jsonify({'error': 'invalid id'}), 400
    wg = games.get(gid)
    if not wg:
        return jsonify({'error': 'not found'}), 404
    score = validate_int((request.json or {}).get('score'), 0, 5)
    if score is None:
        return jsonify({'error': 'invalid score'}), 400
    wg.submit_trust(score)
    return jsonify({'ok': True})

@app.route('/api/stats')
@limiter.limit("30 per minute")
def api_stats():
    try:
        stats = game_repo.get_overview_stats()
        return jsonify({'total_games': stats['total_games'], 'avg_trust': None})
    except Exception as e:
        logger.error("api_stats error: %s", e)
        return jsonify({'total_games': 0, 'avg_trust': None})


# ══════════════════════════════════════════════════════════════════════════════
#  Routes admin (protégées)
# ══════════════════════════════════════════════════════════════════════════════

@app.route('/admin')
@limiter.limit("60 per minute")
@require_admin
def admin_page():
    return render_template('admin.html')

@app.route('/api/admin/personas')
@limiter.limit("30 per minute")
@require_admin
def admin_personas_list():
    try:
        return jsonify(persona_repo.find_all())
    except Exception as e:
        logger.error("admin_personas_list error: %s", e)
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/admin/personas', methods=['POST'])
@limiter.limit("20 per hour")
@require_admin
def admin_persona_create():
    try:
        data = request.json or {}
        name = str(data.get('name', '')).strip()[:32]
        emoji = str(data.get('emoji', '🤖')).strip()[:8] or '🤖'
        description = str(data.get('description', '')).strip()[:200]
        if not name:
            return jsonify({'error': 'name required'}), 400
        pid = persona_repo.create(name, emoji, description)
        return jsonify({'ok': True, 'id': pid})
    except Exception as e:
        logger.error("admin_persona_create error: %s", e)
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/admin/personas/<int:pid>', methods=['PATCH'])
@limiter.limit("30 per minute")
@require_admin
def admin_persona_toggle(pid):
    try:
        data   = request.json or {}
        active = bool(data.get('active', True))
        persona_repo.toggle_active(pid, active)
        return jsonify({'ok': True})
    except Exception as e:
        logger.error("admin_persona_toggle error: %s", e)
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/admin/personas/<int:pid>', methods=['DELETE'])
@limiter.limit("20 per minute")
@require_admin
def admin_persona_delete(pid):
    try:
        persona = persona_repo.find_by_id(pid)
        if not persona:
            return jsonify({'error': 'not found'}), 404
        if persona['name'] == 'Pepper Bot':
            return jsonify({'error': 'cannot delete default persona'}), 400
        persona_repo.delete(pid)
        return jsonify({'ok': True})
    except Exception as e:
        logger.error("admin_persona_delete error: %s", e)
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/admin/logout')
def admin_logout():
    return Response(
        'Déconnecté.',
        401,
        {'WWW-Authenticate': 'Basic realm="Admin PBattleship"'}
    )

@app.route('/api/admin/overview')
@limiter.limit("30 per minute")
@require_admin
def admin_overview():
    try:
        g_stats = game_repo.get_overview_stats()
        t_stats = turn_repo.get_overview_stats()
        detection_rate = (
            round(100 * g_stats['detected_count'] / g_stats['answered_count'], 1)
            if g_stats['answered_count'] else None
        )
        return jsonify({
            **g_stats,
            **t_stats,
            'avg_trust':      t_stats['avg_trust'],
            'detection_rate': detection_rate,
        })
    except Exception as e:
        logger.error("admin_overview error: %s", e)
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/admin/games')
@limiter.limit("30 per minute")
@require_admin
def admin_games_list():
    try:
        return jsonify(game_repo.find_all())
    except Exception as e:
        logger.error("admin_games_list error: %s", e)
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/admin/players')
@limiter.limit("30 per minute")
@require_admin
def admin_players_list():
    try:
        return jsonify(game_repo.find_all_players())
    except Exception as e:
        logger.error("admin_players_list error: %s", e)
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/admin/player/<player_name>', methods=['DELETE'])
@limiter.limit("20 per minute")
@require_admin
def admin_delete_player(player_name):
    try:
        game_repo.delete_by_player(player_name)
        return jsonify({'ok': True})
    except Exception as e:
        logger.error("admin_delete_player error: %s", e)
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/admin/game/<int:gid>', methods=['DELETE'])
@limiter.limit("20 per minute")
@require_admin
def admin_delete_game(gid):
    try:
        if not game_repo.find_by_id(gid):
            return jsonify({'error': 'not found'}), 404
        game_repo.delete_by_id(gid)
        return jsonify({'ok': True})
    except Exception as e:
        logger.error("admin_delete_game error: %s", e)
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/admin/reset', methods=['POST'])
@limiter.limit("5 per hour")
@require_admin
def admin_reset():
    try:
        game_repo.delete_all()
        return jsonify({'ok': True})
    except Exception as e:
        logger.error("admin_reset error: %s", e)
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/admin/game/<int:gid>')
@limiter.limit("30 per minute")
@require_admin
def admin_game_detail(gid):
    try:
        game = game_repo.find_by_id(gid)
        if not game:
            return jsonify({'error': 'not found'}), 404
        turns = turn_repo.find_by_game(gid)
        return jsonify({'game': game, 'turns': turns})
    except Exception as e:
        logger.error("admin_game_detail error: %s", e)
        return jsonify({'error': 'Internal server error'}), 500


# ══════════════════════════════════════════════════════════════════════════════
#  Lancement
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    host = os.environ.get('FLASK_HOST', '127.0.0.1')
    port = int(os.environ.get('FLASK_PORT', 5001))
    app.run(debug=False, host=host, port=port)
