-- Last recorded turn per game (with total turns)
SELECT
  g.id,
  g.player_name,
  g.date_played,
  g.winner,
  MAX(t.turn_number) AS last_turn_number,
  COUNT(t.id)        AS turn_count
FROM Game g
LEFT JOIN Turn t ON t.game_id = g.id
GROUP BY g.id
ORDER BY g.date_played DESC
LIMIT 20;

-- Games where the last turn is missing or incomplete (less than 4 shots)
WITH last_turn AS (
  SELECT t.*
  FROM Turn t
  JOIN (
    SELECT game_id, MAX(turn_number) AS max_turn
    FROM Turn
    GROUP BY game_id
  ) lt ON lt.game_id = t.game_id AND lt.max_turn = t.turn_number
)
SELECT
  g.id         AS game_id,
  g.date_played,
  g.trust_final AS trust_final,
  lt.turn_number,
  COUNT(bs.id) AS shots_recorded
FROM Game g
LEFT JOIN last_turn lt ON lt.game_id = g.id
LEFT JOIN BotShot bs ON bs.turn_id = lt.id
GROUP BY g.id, g.date_played, g.trust_final, lt.turn_number
HAVING lt.turn_number IS NULL OR COUNT(bs.id) < 4
ORDER BY g.date_played DESC;

-- Detailed turns for one game (replace 54 with your game_id)
SELECT
  t.id,
  t.turn_number,
  t.bot_quota,
  t.trust_score,
  COUNT(bs.id) AS shots_recorded
FROM Turn t
LEFT JOIN BotShot bs ON bs.turn_id = t.id
WHERE t.game_id = 54
GROUP BY t.id
ORDER BY t.turn_number DESC;

-- Find missing turns for a specific game (replace 54 with your game_id)
SELECT n AS missing_turn
FROM generate_series(
  1,
  (SELECT COALESCE(MAX(turn_number), 0) FROM Turn WHERE game_id = 54)
) AS n
LEFT JOIN Turn t
  ON t.game_id = 54 AND t.turn_number = n
WHERE t.id IS NULL
ORDER BY n;

-- Check for duplicate turn numbers in a specific game
SELECT turn_number, COUNT(*) AS cnt
FROM Turn
WHERE game_id = 54
GROUP BY turn_number
HAVING COUNT(*) > 1
ORDER BY turn_number;

-- Check shots recorded per turn (incomplete turn if shots_recorded < 4)
SELECT t.turn_number, COUNT(bs.id) AS shots_recorded
FROM Turn t
LEFT JOIN BotShot bs ON bs.turn_id = t.id
WHERE t.game_id = 54
GROUP BY t.turn_number
ORDER BY t.turn_number;
