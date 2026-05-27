# -*- coding: utf-8 -*-
import os
import math
import psycopg2
import matplotlib


HAS_DISPLAY = bool(os.environ.get('DISPLAY'))
if not HAS_DISPLAY:
    matplotlib.use('Agg')

import matplotlib.pyplot as plt


QUERY = """
SELECT t.bot_quota,
       AVG(t.trust_score)::float AS avg_suspicion,
       STDDEV_SAMP(t.trust_score)::float AS stddev_suspicion
FROM Turn t
JOIN Game g ON g.id = t.game_id
WHERE t.trust_score IS NOT NULL
  AND t.bot_quota IS NOT NULL
  AND g.winner = ANY(%s)
GROUP BY t.bot_quota
ORDER BY t.bot_quota
"""


def fetch_avg_by_quota(conn, winners):
    cur = conn.cursor()
    cur.execute(QUERY, (winners,))
    rows = cur.fetchall()
    cur.close()
    return rows


def to_stats(rows):
    avg = {}
    std = {}
    for quota, mean, stddev in rows:
        if quota is None:
            continue
        q = int(quota)
        avg[q] = float(mean)
        std[q] = float(stddev) if stddev is not None else 0.0
    return avg, std


def add_labels(ax, xs, means, stds, y_offset, color):
    for x_pos, mean, stddev in zip(xs, means, stds):
        if math.isnan(mean):
            continue
        label = "{:.2f} +/- {:.2f}".format(mean, stddev)
        ax.text(x_pos, mean + y_offset, label,
                ha='center', va='bottom', fontsize=8, color=color)


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


def main():
    db_url = _get_database_url()
    if not db_url:
        raise RuntimeError(
            "DATABASE_URL is not set. Set it in the environment or add it to .env / Site/.env."
        )

    conn = psycopg2.connect(db_url)
    try:
        pepper_rows = fetch_avg_by_quota(conn, ['Pepper Bot'])
        other_rows = fetch_avg_by_quota(conn, ['Mallory', 'Jayson'])
    finally:
        conn.close()

    pepper_avg, pepper_std = to_stats(pepper_rows)
    other_avg, other_std = to_stats(other_rows)

    quotas = sorted(set(list(pepper_avg.keys()) + list(other_avg.keys())))
    pepper_vals = [pepper_avg.get(q, float('nan')) for q in quotas]
    other_vals = [other_avg.get(q, float('nan')) for q in quotas]
    pepper_errs = [pepper_std.get(q, 0.0) for q in quotas]
    other_errs = [other_std.get(q, 0.0) for q in quotas]

    x = list(range(len(quotas)))
    width = 0.35
    x_left = [i - width / 2 for i in x]
    x_right = [i + width / 2 for i in x]

    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.bar(x_left, pepper_vals, width, label='Pepper Bot',
           yerr=pepper_errs, capsize=3, ecolor='#1b6fa8')
    ax.bar(x_right, other_vals, width, label='Mallory + Jayson',
           yerr=other_errs, capsize=3, ecolor='#a86f1b')

    ax.set_xticks(x)
    ax.set_xticklabels([str(q) for q in quotas])
    ax.set_xlabel('Quota')
    ax.set_ylabel('Suspicion moyenne')
    ax.set_title('Suspicion moyenne par quota')
    ax.grid(axis='y', alpha=0.2)
    ax.legend()

    valid_vals = [v for v in (pepper_vals + other_vals) if not math.isnan(v)]
    max_val = max(valid_vals) if valid_vals else 0.0
    y_offset = max_val * 0.03 if max_val else 0.1
    add_labels(ax, x_left, pepper_vals, pepper_errs, y_offset, '#1b6fa8')
    add_labels(ax, x_right, other_vals, other_errs, y_offset, '#a86f1b')
    if max_val:
        ax.set_ylim(top=max_val + 4 * y_offset)

    fig.tight_layout()
    if HAS_DISPLAY:
        plt.show()
    else:
        output_path = os.environ.get('PLOT_OUTPUT', 'plot_quota_comparison.png')
        fig.savefig(output_path, dpi=150)
        print("Plot saved to {}".format(output_path))


if __name__ == '__main__':
    main()
