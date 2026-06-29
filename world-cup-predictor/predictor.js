/* World Cup 2026 Predictor — predictor.js */
(function () {
  'use strict';

  /* ─── State ─── */
  const TODAY = getLocalDateString();

  /* ─── Helpers ─── */
  function getLocalDateString(date) {
    const d = date ? new Date(date) : new Date();
    return d.toISOString().split('T')[0];
  }

  function formatDisplayDate(isoDate) {
    const [year, month, day] = isoDate.split('-').map(Number);
    const d = new Date(year, month - 1, day);
    return d.toLocaleDateString('es-ES', {
      weekday: 'long', year: 'numeric', month: 'long', day: 'numeric'
    });
  }

  function confidenceClass(pct) {
    if (pct >= 65) return 'high';
    if (pct >= 45) return 'medium';
    return 'low';
  }

  function statPercent(home, away) {
    const total = home + away;
    if (total === 0) return [50, 50];
    return [Math.round((home / total) * 100), Math.round((away / total) * 100)];
  }

  function getTeamFlag(match, side) {
    return match[side].flag || '';
  }

  function winnerClass(match, side) {
    const w = match.prediction.winner;
    if (w === 'draw') return '';
    if (w === 'home' && side === 'home') return 'winner';
    if (w === 'away' && side === 'away') return 'winner';
    return '';
  }

  /* ─── Render helpers ─── */
  function renderScorers(scorers, homeTeam, awayTeam, matchObj) {
    if (!scorers || scorers.length === 0) return '';
    const chips = scorers.map(s => {
      const side = s.team === homeTeam ? matchObj.home : matchObj.away;
      return `<span class="scorer-chip">
        <span class="flag">${side.flag}</span>
        <span class="name">${s.player}</span>
        <span class="minute">${s.minute}'</span>
        <span class="prob">${s.probability}%</span>
      </span>`;
    }).join('');
    return `
      <div class="scorers-section">
        <div class="section-title">⚽ Posibles anotadores</div>
        <div class="scorers-list">${chips}</div>
      </div>`;
  }

  function renderStatRow(label, homeVal, awayVal) {
    const [homePct, awayPct] = statPercent(homeVal, awayVal);
    return `
      <div class="stat-row">
        <div class="stat-bar-home">
          <div class="stat-fill" style="width:${homePct}%"></div>
        </div>
        <div class="stat-label-center">
          <span class="stat-name">${label}</span>
          <span class="stat-values">
            <span class="stat-val-home">${homeVal}</span>
            <span class="stat-val-sep">·</span>
            <span class="stat-val-away">${awayVal}</span>
          </span>
        </div>
        <div class="stat-bar-away">
          <div class="stat-fill" style="width:${awayPct}%"></div>
        </div>
      </div>`;
  }

  function renderStats(stats, match) {
    const h = stats.home;
    const a = stats.away;
    return `
      <div class="stats-section">
        <div class="section-title">📊 Estadísticas predichas</div>
        <div style="display:flex;gap:16px;margin-bottom:8px;">
          <span style="color:var(--accent-blue);font-size:11px;font-weight:600;">◀ ${match.home.team}</span>
          <span style="color:var(--accent-purple);font-size:11px;font-weight:600;">${match.away.team} ▶</span>
        </div>
        <div class="stats-grid">
          ${renderStatRow('Posesión %', h.possession, a.possession)}
          ${renderStatRow('Tiros al arco', h.shotsOnTarget, a.shotsOnTarget)}
          ${renderStatRow('Tiros totales', h.shotsTotal, a.shotsTotal)}
          ${renderStatRow('Corners', h.corners, a.corners)}
          ${renderStatRow('Pases', h.passes, a.passes)}
          ${renderStatRow('Faltas', h.fouls, a.fouls)}
          ${renderStatRow('Tacles', h.tackles, a.tackles)}
        </div>
      </div>`;
  }

  function renderYellows(stats, match) {
    const homeYellows = stats.home.yellowCards || [];
    const awayYellows = stats.away.yellowCards || [];

    function chips(players, flag) {
      if (players.length === 0) return '<span style="color:var(--text-muted);font-size:11px;">Ninguna prevista</span>';
      return players.map(p => `<span class="yellow-chip">${p}</span>`).join('');
    }

    return `
      <div class="yellows-section">
        <div class="yellows-team">
          <div class="section-title">${match.home.flag} ${match.home.team}</div>
          <div class="yellow-chips">${chips(homeYellows)}</div>
        </div>
        <div class="yellows-team">
          <div class="section-title">${match.away.flag} ${match.away.team}</div>
          <div class="yellow-chips">${chips(awayYellows)}</div>
        </div>
      </div>`;
  }

  function renderCard(match) {
    const p = match.prediction;
    const confClass = confidenceClass(p.confidence);
    const cardId = `card-${match.id}`;
    const detailsId = `details-${match.id}`;

    const homeWinnerClass = winnerClass(match, 'home');
    const awayWinnerClass = winnerClass(match, 'away');

    const resultLabel = p.winner === 'draw'
      ? '<span style="color:var(--accent-orange)">Empate</span>'
      : `<span style="color:var(--accent-green)">Victoria ${p.winner === 'home' ? match.home.team : match.away.team}</span>`;

    return `
      <article class="match-card" id="${cardId}">
        <div class="card-header">
          <div class="card-meta-left">
            <span class="group-pill">Grupo ${match.group}</span>
            <span class="match-time">🕐 ${match.time}</span>
            <span style="color:var(--text-muted);font-size:11px;">J${match.matchday}</span>
          </div>
          <span class="match-venue">📍 ${match.venue}</span>
        </div>

        <div class="matchup">
          <div class="team ${homeWinnerClass}">
            <span class="team-flag">${match.home.flag}</span>
            <span class="team-name">${match.home.team}</span>
            <span class="team-rank">FIFA #${match.home.fifaRank}</span>
          </div>

          <div class="score-block">
            <div class="predicted-score">${p.result}</div>
            <div class="score-label">Predicción</div>
            <div class="confidence-bar-wrap">
              <div class="confidence-bar">
                <div class="confidence-fill ${confClass}" style="width:${p.confidence}%"></div>
              </div>
              <div class="confidence-pct">${p.confidence}% confianza</div>
            </div>
            <div style="margin-top:4px;font-size:11px;">${resultLabel}</div>
          </div>

          <div class="team ${awayWinnerClass}">
            <span class="team-flag">${match.away.flag}</span>
            <span class="team-name">${match.away.team}</span>
            <span class="team-rank">FIFA #${match.away.fifaRank}</span>
          </div>
        </div>

        ${renderScorers(p.scorers, match.home.team, match.away.team, match)}

        <button class="card-toggle" onclick="toggleDetails('${detailsId}', this)" aria-expanded="false">
          <span>Ver estadísticas detalladas</span>
          <i class="toggle-icon">▼</i>
        </button>

        <div class="card-details" id="${detailsId}">
          ${renderStats(p.stats, match)}
          ${renderYellows(p.stats, match)}
        </div>
      </article>`;
  }

  /* ─── Toggle details ─── */
  window.toggleDetails = function (detailsId, btn) {
    const el = document.getElementById(detailsId);
    const isOpen = el.classList.contains('open');
    el.classList.toggle('open', !isOpen);
    btn.classList.toggle('open', !isOpen);
    btn.setAttribute('aria-expanded', String(!isOpen));
    btn.querySelector('span').textContent = isOpen
      ? 'Ver estadísticas detalladas'
      : 'Ocultar estadísticas';
  };

  /* ─── Main render ─── */
  function renderPage(fixtures, targetDate) {
    const displayDate = targetDate || TODAY;
    const todayMatches = fixtures.matches.filter(m => m.date === displayDate);

    // Update date display
    const dateEl = document.getElementById('display-date');
    if (dateEl) dateEl.textContent = formatDisplayDate(displayDate);

    const countEl = document.getElementById('match-count');
    if (countEl) countEl.textContent = todayMatches.length;

    const container = document.getElementById('matches-container');
    if (!container) return;

    if (todayMatches.length === 0) {
      container.innerHTML = `
        <div class="no-matches">
          <div class="no-matches-icon">🗓️</div>
          <h3>Sin partidos hoy</h3>
          <p>No hay partidos programados para el <strong>${formatDisplayDate(displayDate)}</strong>.</p>
        </div>`;
      return;
    }

    // Group by time slot
    const byTime = {};
    todayMatches.forEach(m => {
      if (!byTime[m.time]) byTime[m.time] = [];
      byTime[m.time].push(m);
    });

    let html = '';
    const times = Object.keys(byTime).sort();
    times.forEach(time => {
      const matches = byTime[time];
      if (matches.length > 1) {
        html += `<div style="margin-bottom:6px;margin-top:14px;">
          <span style="font-size:11px;color:var(--text-muted);text-transform:uppercase;letter-spacing:0.6px;">🕐 ${time} ET — Simultáneos</span>
        </div>`;
      }
      matches.forEach(m => { html += renderCard(m); });
    });

    container.innerHTML = html;
  }

  /* ─── Date navigation ─── */
  function setupNavigation(fixtures) {
    const matchDates = [...new Set(fixtures.matches.map(m => m.date))].sort();
    const prevBtn = document.getElementById('btn-prev');
    const nextBtn = document.getElementById('btn-next');
    const todayBtn = document.getElementById('btn-today');

    let currentDate = TODAY;
    const hasToday = matchDates.includes(TODAY);

    // If today has no matches, default to first date with matches
    if (!hasToday && matchDates.length > 0) {
      currentDate = matchDates[matchDates.length - 1];
    }

    function update() {
      renderPage(fixtures, currentDate);
      const idx = matchDates.indexOf(currentDate);
      if (prevBtn) prevBtn.disabled = idx <= 0;
      if (nextBtn) nextBtn.disabled = idx >= matchDates.length - 1;
    }

    if (prevBtn) prevBtn.addEventListener('click', () => {
      const idx = matchDates.indexOf(currentDate);
      if (idx > 0) { currentDate = matchDates[idx - 1]; update(); }
    });

    if (nextBtn) nextBtn.addEventListener('click', () => {
      const idx = matchDates.indexOf(currentDate);
      if (idx < matchDates.length - 1) { currentDate = matchDates[idx + 1]; update(); }
    });

    if (todayBtn) todayBtn.addEventListener('click', () => {
      currentDate = TODAY;
      update();
    });

    update();
  }

  /* ─── Bootstrap ─── */
  async function init() {
    try {
      const resp = await fetch('./data/fixtures_2026.json');
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      const fixtures = await resp.json();
      setupNavigation(fixtures);
    } catch (err) {
      const container = document.getElementById('matches-container');
      if (container) {
        container.innerHTML = `
          <div class="no-matches">
            <div class="no-matches-icon">⚠️</div>
            <h3>Error al cargar datos</h3>
            <p style="color:var(--text-muted)">${err.message}</p>
          </div>`;
      }
      console.error('Predictor error:', err);
    }
  }

  document.addEventListener('DOMContentLoaded', init);
})();
