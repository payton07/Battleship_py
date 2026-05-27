# -*- coding: utf-8 -*-
import os
import math
import statistics
import psycopg2
import psycopg2.extras
import matplotlib


SHOW_PLOT = os.environ.get('SHOW_PLOT') == '1'
if not SHOW_PLOT:
    matplotlib.use('Agg')

import matplotlib.pyplot as plt


OPPONENTS = {
    'Pepper Bot': 'machine',
    'jennu': 'machine',
    'Mallory': 'human',
    'Jayson': 'human',
}

QUERY_TURNS = """
SELECT g.id AS game_id,
       g.player_name,
       g.date_played,
       g.winner,
       t.turn_number,
       t.trust_score
FROM Game g
JOIN Turn t ON t.game_id = g.id
WHERE t.trust_score IS NOT NULL
  AND g.winner IN ('Pepper Bot', 'Mallory', 'Jayson', 'jennu')
ORDER BY g.player_name, g.date_played, t.turn_number
"""


def _load_env_file(path):
    try:
        with open(path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if line.startswith('export '):
                    line = line[len('export '):]
                if '=' not in line:
                    continue
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                if key and key not in os.environ:
                    os.environ[key] = value
        return True
    except (IOError, OSError):
        return False


def _get_database_url():
    db_url = os.environ.get('DATABASE_URL')
    if db_url:
        return db_url

    root = os.path.dirname(os.path.abspath(__file__))
    env_paths = [
        os.path.join(root, '.env'),
        os.path.join(root, 'Site', '.env'),
    ]
    for p in env_paths:
        _load_env_file(p)

    return os.environ.get('DATABASE_URL')


def _mean(values):
    return statistics.mean(values) if values else float('nan')


def _std(values):
    return statistics.stdev(values) if len(values) > 1 else 0.0


def _group_label(key):
    return 'Machine d’abord' if key == 'machine' else 'Humain d’abord'


def main():
    db_url = _get_database_url()
    if not db_url:
        raise RuntimeError(
            "DATABASE_URL is not set. Set it in the environment or add it to .env / Site/.env."
        )

    conn = psycopg2.connect(db_url)
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(QUERY_TURNS)
        rows = cur.fetchall()
        cur.close()
    finally:
        conn.close()

    if not rows:
        raise RuntimeError("No rows returned. Check that games with known winners exist.")

    game_scores = {}
    game_meta = {}
    player_scores = {}
    turn_scores = {'machine': {}, 'human': {}}

    for r in rows:
        gid = r['game_id']
        winner = r['winner']
        opponent_type = OPPONENTS.get(winner)
        if not opponent_type:
            continue

        game_meta[gid] = {
            'player_name': r['player_name'],
            'date_played': r['date_played'],
            'opponent_type': opponent_type,
        }
        game_scores.setdefault(gid, []).append(r['trust_score'])

        player_name = r['player_name']
        player_scores.setdefault(player_name, {'machine': [], 'human': []})
        player_scores[player_name][opponent_type].append(r['trust_score'])

        turn_number = r['turn_number']
        turn_scores[opponent_type].setdefault(turn_number, []).append(r['trust_score'])

    # ── Effet d'ordre (1er adversaire connu, basé sur le vainqueur) ─────────────
    first_game_by_player = {}
    for gid, meta in game_meta.items():
        name = meta['player_name']
        date = meta['date_played']
        if name not in first_game_by_player or date < first_game_by_player[name]['date']:
            first_game_by_player[name] = {
                'date': date,
                'opponent_type': meta['opponent_type'],
                'game_avg': _mean(game_scores.get(gid, [])),
            }

    order_groups = {'machine': [], 'human': []}
    for info in first_game_by_player.values():
        if info['opponent_type'] in order_groups and not math.isnan(info['game_avg']):
            order_groups[info['opponent_type']].append(info['game_avg'])

    order_means = [_mean(order_groups['machine']), _mean(order_groups['human'])]
    order_stds = [_std(order_groups['machine']), _std(order_groups['human'])]

    # ── Effet de tour (moyenne par numéro de tour) ──────────────────────────────
    all_turns = sorted(set(turn_scores['machine'].keys()) | set(turn_scores['human'].keys()))
    machine_means = [_mean(turn_scores['machine'].get(t, [])) for t in all_turns]
    human_means = [_mean(turn_scores['human'].get(t, [])) for t in all_turns]
    machine_stds = [_std(turn_scores['machine'].get(t, [])) for t in all_turns]
    human_stds = [_std(turn_scores['human'].get(t, [])) for t in all_turns]

    # ── Variabilité inter-individuelle ──────────────────────────────────────────
    scatter_x = []
    scatter_y = []
    scatter_c = []
    for name, scores in player_scores.items():
        if scores['machine'] and scores['human']:
            scatter_x.append(_mean(scores['human']))
            scatter_y.append(_mean(scores['machine']))
            first_opponent = first_game_by_player.get(name, {}).get('opponent_type', 'human')
            scatter_c.append('#1b6fa8' if first_opponent == 'machine' else '#a86f1b')

    fig, axes = plt.subplots(1, 3, figsize=(14, 4.6))

    # Panel 1: ordre
    ax0 = axes[0]
    ax0.bar([0, 1], order_means, yerr=order_stds, capsize=4,
            color=['#1b6fa8', '#a86f1b'])
    ax0.set_xticks([0, 1])
    ax0.set_xticklabels([_group_label('machine'), _group_label('human')], rotation=10)
    ax0.set_ylabel('Suspicion moyenne (1ère partie)')
    ax0.set_title("Effet d'ordre")
    ax0.grid(axis='y', alpha=0.2)

    # Panel 2: tour
    ax1 = axes[1]
    ax1.plot(all_turns, machine_means, marker='o', label='Machine')
    ax1.plot(all_turns, human_means, marker='o', label='Humain')
    ax1.fill_between(all_turns,
                     [m - s for m, s in zip(machine_means, machine_stds)],
                     [m + s for m, s in zip(machine_means, machine_stds)],
                     alpha=0.15)
    ax1.fill_between(all_turns,
                     [m - s for m, s in zip(human_means, human_stds)],
                     [m + s for m, s in zip(human_means, human_stds)],
                     alpha=0.15)
    ax1.set_xlabel('Numéro de tour')
    ax1.set_ylabel('Suspicion moyenne')
    ax1.set_title('Effet de tour')
    ax1.grid(axis='y', alpha=0.2)
    ax1.legend()

    # Panel 3: variabilité
    ax2 = axes[2]
    if scatter_x:
        ax2.scatter(scatter_x, scatter_y, c=scatter_c, alpha=0.8)
        ax2.plot([0, 5], [0, 5], linestyle='--', color='#777', linewidth=1)
        ax2.set_xlabel('Suspicion moyenne vs humain')
        ax2.set_ylabel('Suspicion moyenne vs machine')
        ax2.set_title('Variabilité inter-individuelle')
        ax2.grid(alpha=0.2)
    else:
        all_means = [
            _mean(scores['machine'] + scores['human'])
            for scores in player_scores.values()
            if scores['machine'] or scores['human']
        ]
        ax2.hist(all_means, bins=6, color='#6aa5ff', alpha=0.8)
        ax2.set_xlabel('Suspicion moyenne')
        ax2.set_ylabel('Nombre de joueurs')
        ax2.set_title('Variabilité inter-individuelle')

    fig.tight_layout()
    if SHOW_PLOT:
        plt.show()
    else:
        output_path = os.environ.get('PLOT_OUTPUT', 'plot_trust_effects.png')
        fig.savefig(output_path, dpi=150)
        print("Plot saved to {}".format(output_path))


if __name__ == '__main__':
    main()
