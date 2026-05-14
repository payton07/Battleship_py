/* ═══════════════════════════════════════════════════════════════════════════
   PEPPER BATTLESHIP — Game Client
═══════════════════════════════════════════════════════════════════════════ */

const SHOTS_PER_TURN = 4;
const COLS = 'ABCDEFGHIJ';

// ─── State ─────────────────────────────────────────────────────────────────
const S = {
  gameId:           null,
  playerName:       '',
  phase:            'setup',   // setup | grid | playing | bot | gameover
  gridIndex:        0,
  grids:            null,      // toutes les configs pré-chargées
  shotsLeft:        SHOTS_PER_TURN,
  turnNumber:       1,
  playerGrid:       null,
  enemyGrid:        null,
  locked:           false,
  pendingGameOver:  null,   // { winner, message } — set when game ends mid-bot-turn
  botTurnStats:     { touches: 0, coules: 0, rates: 0 },
  fastMode:         false,
};

// ─── DOM refs ───────────────────────────────────────────────────────────────
const $ = id => document.getElementById(id);

const screens = {
  setup: $('screen-setup'),
  grid:  $('screen-grid'),
  game:  $('screen-game'),
};

// ─── Screen transitions ──────────────────────────────────────────────────────
function showScreen(name) {
  Object.values(screens).forEach(s => { s.classList.remove('active'); });
  if (screens[name]) screens[name].classList.add('active');
}

// ─── API helpers ────────────────────────────────────────────────────────────
const API = {
  post: (url, body = {}) => fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  }).then(r => r.json()),

  get: url => fetch(url).then(r => r.json()),

  newGame: name      => API.post('/api/game/new', { player_name: name }),
  preview: (gid, i)  => API.get(`/api/game/${gid}/preview/${i}`),
  select:  (gid, i)  => API.post(`/api/game/${gid}/select-grid`, { index: i }),
  shoot:   (gid,x,y) => API.post(`/api/game/${gid}/shoot`, { x, y }),
  botTurn:    gid           => API.post(`/api/game/${gid}/bot-turn`),
  turnTrust:  (gid, s)     => API.post(`/api/game/${gid}/turn-trust`, { score: s }),
  finalTrust: (gid, det)   => API.post(`/api/game/${gid}/final-trust`, { detected: det }),
};

// ─── Grid rendering ──────────────────────────────────────────────────────────
function buildGrid(containerId, cells, isEnemy = false) {
  const container = $(containerId);
  container.innerHTML = '';
  const size = cells[0].length;

  // Corner cell
  const corner = el('div', 'grid-corner');
  container.appendChild(corner);

  // Column headers (A–J)
  for (let x = 0; x < size; x++) {
    const h = el('div', 'grid-header');
    h.textContent = COLS[x];
    container.appendChild(h);
  }

  // Rows
  for (let y = 0; y < size; y++) {
    const rowH = el('div', 'grid-header');
    rowH.textContent = y;
    container.appendChild(rowH);

    for (let x = 0; x < size; x++) {
      const cell = el('div', `grid-cell${isEnemy ? ' enemy-cell' : ''}`);
      const state = cells[y][x];
      cell.dataset.state = state;
      cell.dataset.x = x;
      cell.dataset.y = y;

      if (isEnemy) {
        cell.addEventListener('click', () => onEnemyCellClick(x, y));
      }
      container.appendChild(cell);
    }
  }
}

function updateGrid(containerId, cells, isEnemy = false, highlightCells = []) {
  const container = $(containerId);
  const size = cells[0].length;
  const highlights = new Set(highlightCells.map(c => `${c.x},${c.y}`));

  for (let y = 0; y < size; y++) {
    for (let x = 0; x < size; x++) {
      const cell = container.querySelector(`[data-x="${x}"][data-y="${y}"]`);
      if (!cell) continue;
      const newState = cells[y][x];
      const oldState = cell.dataset.state;

      if (newState !== oldState) {
        cell.dataset.state = newState;
        cell.dataset.new = 'true';
        setTimeout(() => { if (cell) cell.removeAttribute('data-new'); }, 600);
      }

      if (highlights.has(`${x},${y}`)) {
        cell.dataset.new = 'true';
        setTimeout(() => { if (cell) cell.removeAttribute('data-new'); }, 600);
      }
    }
  }
}

function el(tag, cls = '') {
  const d = document.createElement(tag);
  if (cls) d.className = cls;
  return d;
}

// ─── Shot bullets ──────────────────────────────────────────────────────────
function renderBullets(n) {
  const wrap = $('shot-bullets');
  wrap.innerHTML = '';
  for (let i = 0; i < SHOTS_PER_TURN; i++) {
    const b = el('div', `bullet${i < n ? '' : ' spent'}`);
    wrap.appendChild(b);
  }
}

// ─── Turn badge ────────────────────────────────────────────────────────────
function setTurnBadge(isPlayer) {
  const badge = $('turn-badge');
  const text  = $('turn-text');
  badge.className = `turn-badge ${isPlayer ? 'player-turn' : 'bot-turn'}`;
  text.textContent = isPlayer ? 'À VOUS' : 'PEPPER BOT';
}

// ─── Status ────────────────────────────────────────────────────────────────
function setStatus(msg, type = 'info') {
  const bar = $('status-bar');
  bar.textContent = msg;
  bar.className = `status-bar ${type}`;
}

function setBotThinking(visible) {
  const el2 = $('bot-thinking');
  el2.classList.toggle('visible', visible);
}

// ─── Board highlight ───────────────────────────────────────────────────────
function setBoardActive(side) {
  // side: 'player' | 'enemy' | 'none'
  $('board-wrap-player').classList.toggle('active',     side === 'player');
  $('board-wrap-enemy').classList.toggle('active',      side === 'enemy');
  $('board-wrap-player').classList.toggle('bot-active', side === 'bot');
  $('board-wrap-enemy').classList.toggle('bot-active',  side === 'bot');
}

// ─── Shots counter label ───────────────────────────────────────────────────
function updateShotsCounter(n) {
  $('shots-counter').textContent = `${n} tir${n > 1 ? 's' : ''} restant${n > 1 ? 's' : ''}`;
}

// ─── Action log ────────────────────────────────────────────────────────────
function addLog(actor, coord, result, type) {
  const log = $('action-log');

  // Clear placeholder
  const placeholder = log.querySelector('[data-placeholder]');
  if (placeholder) placeholder.remove();

  const entry = el('div', 'log-entry');

  const actorEl = el('span', `log-actor ${type}`);
  actorEl.textContent = actor;

  const coordEl = el('span', 'log-coord');
  coordEl.textContent = coord;

  const resultEl = el('span', `log-result ${resultClass(result)}`);
  resultEl.textContent = result;

  entry.append(actorEl, coordEl, resultEl);

  // Prepend
  log.insertBefore(entry, log.firstChild);

  // Limit to 20 entries
  while (log.children.length > 20) log.removeChild(log.lastChild);
}

function resultClass(r) {
  if (r === 'Coulé')  return 'coule';
  if (r === 'Touché') return 'touche';
  return 'rate';
}

// ══════════════════════════════════════════════════════════════════════════════
//  FLOW
// ══════════════════════════════════════════════════════════════════════════════

// ─── SETUP ─────────────────────────────────────────────────────────────────
async function onStart() {
  const name = $('input-name').value.trim() || 'Commandant';
  S.playerName = name;

  $('btn-start').textContent = '⌛ Connexion...';
  $('btn-start').disabled = true;

  try {
    const data = await API.newGame(name);
    S.gameId = data.game_id;
    $('nav-player-name').textContent = `⚓ ${name}`;

    $('btn-start').textContent = '⌛ Chargement des configurations...';
    const previews = await Promise.all(
      Array.from({ length: 10 }, (_, i) => API.preview(S.gameId, i))
    );
    S.grids = previews.map(p => p.cells);

    showGridPreview(0);
    buildDotsNav();
    showScreen('grid');
  } catch (e) {
    setStatus('Erreur de connexion au serveur.', 'warn');
    $('btn-start').textContent = '⚔ LANCER LA PARTIE';
    $('btn-start').disabled = false;
  }
}

// ─── GRID SELECTION ────────────────────────────────────────────────────────
function showGridPreview(index) {
  if (!S.grids) return;
  S.gridIndex = ((index % 10) + 10) % 10;
  buildGrid('grid-preview', S.grids[S.gridIndex], false);
  $('grid-index-badge').textContent = `Config ${S.gridIndex + 1} / 10`;
  updateDotsNav(S.gridIndex);
}

function buildDotsNav() {
  const nav = $('dots-nav');
  nav.innerHTML = '';
  for (let i = 0; i < 10; i++) {
    const d = el('div', `dot-nav${i === 0 ? ' active' : ''}`);
    d.dataset.i = i;
    d.addEventListener('click', () => showGridPreview(i));
    nav.appendChild(d);
  }
}

function updateDotsNav(active) {
  document.querySelectorAll('.dot-nav').forEach((d, i) => {
    d.classList.toggle('active', i === active);
  });
}

async function onValidateGrid() {
  $('btn-validate-grid').textContent = '⌛ Déploiement...';
  $('btn-validate-grid').disabled = true;

  const data = await API.select(S.gameId, S.gridIndex);
  S.playerGrid = data.player_grid;
  S.enemyGrid  = data.enemy_grid;
  S.shotsLeft  = SHOTS_PER_TURN;
  S.turnNumber = 1;
  S.phase      = 'playing';

  // Build both grids
  buildGrid('player-grid', S.playerGrid, false);
  buildGrid('enemy-grid',  S.enemyGrid,  true);

  $('label-player').textContent = S.playerName.toUpperCase();
  $('nav-center').style.display = 'flex';
  $('btn-speed').classList.remove('hidden');
  setTurnBadge(true);
  renderBullets(SHOTS_PER_TURN);
  updateShotsCounter(SHOTS_PER_TURN);
  $('nav-turn-num').textContent = '1';
  setBoardActive('enemy');
  setStatus('À vous de tirer ! Cliquez sur la grille ennemie.', 'info');

  showScreen('game');
}

// ─── PLAYER SHOOT ──────────────────────────────────────────────────────────
async function onEnemyCellClick(x, y) {
  if (S.phase !== 'playing' || S.locked) return;

  S.locked = true;

  const clickedCell = document.querySelector(`#enemy-grid [data-x="${x}"][data-y="${y}"]`);
  if (clickedCell) clickedCell.dataset.pending = 'true';

  const data = await API.shoot(S.gameId, x, y);
  if (clickedCell) delete clickedCell.dataset.pending;

  if (data.error || data.invalid) {
    if (data.result === 'Déjà joué') setStatus('⚠ Case déjà jouée !', 'warn');
    S.locked = false;
    return;
  }

  S.playerGrid = data.player_grid;
  S.enemyGrid  = data.enemy_grid;
  S.shotsLeft  = data.shots_left;

  updateGrid('player-grid', data.player_grid);
  updateGrid('enemy-grid',  data.enemy_grid, true, [{x, y}]);

  const col = COLS[x];
  addLog(S.playerName, `${col}${y}`, data.result, 'player');

  if (data.game_over) {
    await endGame(data.winner, data.message);
    return;
  }

  renderBullets(data.shots_left <= 0 ? 0 : data.shots_left);
  updateShotsCounter(Math.max(data.shots_left, 0));

  if (data.turn_ended) {
    setStatus('Pepper Bot prépare ses tirs...', 'warn');
    setTurnBadge(false);
    renderBullets(0);
    updateShotsCounter(0);
    setBoardActive('bot');
    S.phase = 'bot';
    S.locked = false;
    setTimeout(triggerBotTurn, 900);
  } else {
    setStatus(`À vous de tirer ! ${data.shots_left} tir${data.shots_left > 1 ? 's' : ''} restant${data.shots_left > 1 ? 's' : ''}.`, 'info');
    S.locked = false;
  }
}

// ─── BOT TURN ──────────────────────────────────────────────────────────────
async function triggerBotTurn() {
  setBotThinking(true);
  setStatus('Pepper Bot analyse et vise...', 'warn');

  const data = await API.botTurn(S.gameId);
  setBotThinking(false);

  if (data.error) {
    setStatus('Erreur lors du tour du bot.', 'warn');
    return;
  }

  const shots = data.shots || [];
  let idx = 0;

  function animateNextShot() {
    if (idx >= shots.length) {
      // All shots animated — update grids
      updateGrid('player-grid', data.player_grid);
      updateGrid('enemy-grid',  data.enemy_grid, true);

      // Calculer les stats du tour
      S.botTurnStats = shots.reduce((acc, s) => {
        if (s.result === 'Touché') acc.touches++;
        else if (s.result === 'Coulé') acc.coules++;
        else acc.rates++;
        return acc;
      }, { touches: 0, coules: 0, rates: 0 });

      setStatus('Prenez le temps d\'analyser les tirs du bot…', 'warn');

      if (data.game_over) {
        S.pendingGameOver = { winner: data.winner, message: data.message };
        setTimeout(() => showTurnRating(S.turnNumber), S.fastMode ? 600 : 2500);
        return;
      }

      S.turnNumber = data.turn_number;
      S.shotsLeft  = data.shots_left;

      setTimeout(() => showTurnRating(S.turnNumber - 1), S.fastMode ? 600 : 2500);
      return;
    }

    const shot = shots[idx++];
    updateGrid('player-grid', data.player_grid, false, [{x: shot.x, y: shot.y}]);
    addLog('Pepper Bot', shot.coord, shot.result, 'bot');
    setStatus(`Pepper Bot tire en ${shot.coord} — ${shot.result} !`, 'warn');
    setTimeout(animateNextShot, S.fastMode ? 120 : 750);
  }

  setTimeout(animateNextShot, S.fastMode ? 80 : 300);
}

// ─── PER-TURN RATING ────────────────────────────────────────────────────────
const STAR_ICONS  = ['😐','🤔','🧐','😮','😤','🚨'];
const STAR_LABELS = ['0','1','2','3','4','5'];

function showTurnRating(turnNum) {
  $('tr-turn-num').textContent = turnNum;

  // Build star buttons
  const container = $('star-rating');
  container.innerHTML = '';
  for (let i = 0; i <= 5; i++) {
    const btn = document.createElement('button');
    btn.className = 'star-btn';
    btn.dataset.score = i;
    btn.innerHTML = `<span class="star-icon">${STAR_ICONS[i]}</span><span>${STAR_LABELS[i]}</span>`;
    btn.addEventListener('click', () => onTurnRatingClick(i));
    container.appendChild(btn);
  }

  openTurnRatingModal();
}

function openTurnRatingModal() {
  $('modal-turn-rating').classList.add('active');
  $('btn-reopen-rating').classList.add('hidden');
  $('side-panel-rating').classList.add('hidden');
}

function closeTurnRatingModal() {
  $('modal-turn-rating').classList.remove('active');
  $('btn-reopen-rating').classList.remove('hidden');

  // Mettre à jour et afficher le panneau gauche
  const { touches, coules, rates } = S.botTurnStats;
  $('sp-touches').textContent = touches;
  $('sp-coules').textContent  = coules;
  $('sp-rates').textContent   = rates;
  $('side-panel-rating').classList.remove('hidden');
}

function hideSidePanel() {
  $('side-panel-rating').classList.add('hidden');
  $('btn-reopen-rating').classList.add('hidden');
}

async function onTurnRatingClick(score) {
  $('modal-turn-rating').classList.remove('active');
  hideSidePanel();

  // Submit trust for this turn (fire-and-forget, don't block UX)
  API.turnTrust(S.gameId, score).catch(() => {});

  if (S.pendingGameOver) {
    const go = S.pendingGameOver;
    S.pendingGameOver = null;
    endGame(go.winner, go.message);
    return;
  }

  // Continue to player turn
  S.phase  = 'playing';
  S.locked = false;
  setTurnBadge(true);
  renderBullets(SHOTS_PER_TURN);
  updateShotsCounter(SHOTS_PER_TURN);
  $('nav-turn-num').textContent = S.turnNumber;
  setBoardActive('enemy');
  setStatus('À vous de tirer ! Cliquez sur la grille ennemie.', 'info');
}

// ─── GAME OVER ──────────────────────────────────────────────────────────────
function endGame(winner, message) {
  S.phase  = 'gameover';
  S.locked = true;
  S._endWinner = winner;

  setBoardActive('none');
  setStatus('Partie terminée — rendez votre verdict !', 'info');

  // Montre d'abord le modal de verdict binaire
  setTimeout(() => $('modal-final-trust').classList.add('active'), 600);
}

async function onFinalTrustAnswer(detected) {
  $('modal-final-trust').classList.remove('active');

  // Enregistrement fire-and-forget
  API.finalTrust(S.gameId, detected).catch(() => {});

  // Affiche le résultat de la partie
  const isWin = S._endWinner === 'player';
  $('result-emoji').textContent    = isWin ? '🏆' : '💀';
  $('result-title').textContent    = isWin ? 'VICTOIRE !' : 'DÉFAITE';
  $('result-title').className      = `result-title ${isWin ? 'win' : 'lose'}`;
  $('result-subtitle').textContent = isWin
    ? 'Bravo Commandant ! Vous avez coulé toute la flotte de Pepper Bot.'
    : 'Pepper Bot a coulé toute votre flotte. Meilleure chance la prochaine fois !';

  setStatus(isWin ? '🏆 Victoire !' : '💀 Défaite.', isWin ? 'info' : 'warn');
  setTimeout(() => $('modal-gameover').classList.add('active'), 400);
}

// ──────────────────────────────────────────────────────────────────────────────
//  EVENT BINDING
// ──────────────────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {

  // Setup screen
  $('btn-start').addEventListener('click', onStart);
  $('input-name').addEventListener('keydown', e => { if (e.key === 'Enter') onStart(); });

  // Grid select
  $('btn-next-grid').addEventListener('click', () => showGridPreview(S.gridIndex + 1));
  $('btn-prev-grid').addEventListener('click', () => showGridPreview(S.gridIndex - 1));
  $('btn-validate-grid').addEventListener('click', onValidateGrid);

  // Keyboard navigation in grid select
  document.addEventListener('keydown', e => {
    if (S.phase === 'setup' || screens.grid.classList.contains('active')) {
      if (e.key === 'ArrowRight') showGridPreview(S.gridIndex + 1);
      if (e.key === 'ArrowLeft')  showGridPreview(S.gridIndex - 1);
      if (e.key === 'Enter' && screens.grid.classList.contains('active')) onValidateGrid();
    }
  });

  // Clic sur le fond du modal → ferme et affiche le bouton flottant
  $('modal-turn-rating').addEventListener('click', e => {
    if (e.target === $('modal-turn-rating')) closeTurnRatingModal();
  });

  // Bouton flottant → rouvre le modal
  $('btn-reopen-rating').addEventListener('click', openTurnRatingModal);

  // Bouton dans le panneau gauche → rouvre aussi le modal
  $('btn-side-evaluate').addEventListener('click', openTurnRatingModal);

  // Verdict final binaire
  $('btn-final-yes').addEventListener('click', () => onFinalTrustAnswer(true));
  $('btn-final-no').addEventListener('click',  () => onFinalTrustAnswer(false));

  // Bouton vitesse
  $('btn-speed').addEventListener('click', () => {
    S.fastMode = !S.fastMode;
    const btn = $('btn-speed');
    btn.classList.toggle('fast', S.fastMode);
    $('speed-icon').textContent  = S.fastMode ? '🐢' : '⚡';
    $('speed-label').textContent = S.fastMode ? 'Normal'    : 'Accélérer';
  });

  // Focus name input on load
  setTimeout(() => $('input-name').focus(), 100);
});
