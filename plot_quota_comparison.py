# -*- coding: utf-8 -*-
import os
import psycopg2
import matplotlib


HAS_DISPLAY = bool(os.environ.get('DISPLAY'))
if not HAS_DISPLAY:
    matplotlib.use('Agg')

import matplotlib.pyplot as plt


QUERY = """
SELECT t.bot_quota, AVG(t.trust_score)::float AS avg_suspicion
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


def to_dict(rows):
    data = {}
    for quota, avg in rows:
        data[int(quota)] = float(avg)
    return data


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

    pepper = to_dict(pepper_rows)
    other = to_dict(other_rows)

    quotas = sorted(set(list(pepper.keys()) + list(other.keys())))
    pepper_vals = [pepper.get(q, float('nan')) for q in quotas]
    other_vals = [other.get(q, float('nan')) for q in quotas]

    x = list(range(len(quotas)))
    width = 0.35
    x_left = [i - width / 2 for i in x]
    x_right = [i + width / 2 for i in x]

    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.bar(x_left, pepper_vals, width, label='Versus IA')
    ax.bar(x_right, other_vals, width, label='Versus Humain')

    ax.set_xticks(x)
    ax.set_xticklabels([str(q) for q in quotas])
    ax.set_xlabel('Quota')
    ax.set_ylabel('Suspicion moyenne')
    ax.set_title('Suspicion moyenne par quota')
    ax.grid(axis='y', alpha=0.2)
    ax.legend()

    fig.tight_layout()
    if HAS_DISPLAY:
        plt.show()
    else:
        output_path = os.environ.get('PLOT_OUTPUT', 'plot_quota_comparison.png')
        fig.savefig(output_path, dpi=150)
        print("Plot saved to {}".format(output_path))


if __name__ == '__main__':
    main()
