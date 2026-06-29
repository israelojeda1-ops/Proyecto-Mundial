/* World Cup 2026 Predictor — predictor.js */
(function () {
  'use strict';

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

  function winnerClass(match, side) {
    if (match.status === 'completed' && match.finalScore) {
      const fs = match.finalScore;
      if (fs.home === fs.away) return '';
      if (fs.home > fs.away && side === 'home') return 'winner';
      if (fs.away > fs.home && side === 'away') return 'winner';
      return '';
    }
    const w = match.prediction.winner;
    if (w === 'draw') return '';
    if (w === 'home' && side === 'home') return 'winner';
    if (w === 'away' && side === 'away') return 'winner';
    return '';
  }

  /* ─── Render: Forma reciente ─── */
  function renderForm(form, homeTeam, awayTeam) {
    if (!form) return '';
    function formDots(arr) {
      return arr.map(r => {
        const cls = r === 'W' ? 'form-w' : r === 'D' ? 'form-d' : 'form-l';
        return `<span class="form-dot ${cls}" title="${r === 'W' ? 'Victoria' : r === 'D' ? 'Empate' : 'Derrota'}">${r}</span>`;
      }).join('');
    }
    return `
      <div class="context-section">
        <div class="section-title">📈 Forma reciente (Mundial 2026)</div>
        <div class="form-rows">
          <div class="form-row">
            <span class="form-team-label">${homeTeam.flag} ${homeTeam.team}</span>
            <div class="form-dots">${formDots(form.home)}</div>
          </div>
          <div class="form-row">
            <span class="form-team-label">${awayTeam.flag} ${awayTeam.team}</span>
            <div class="form-dots">${formDots(form.away)}</div>
          </div>
        </div>
      </div>`;
  }

  /* ─── Render: Récord en el torneo + goles marcados ─── */
  function renderWCRecord(ctx, homeTeam, awayTeam) {
    if (!ctx || !ctx.groupRecord) return '';

    function goalsList(goals) {
      if (!goals || goals.length === 0) return '';
      return goals.map(g =>
        `<span class="wc-scorer"><span class="wc-scorer-name">${g.player}</span><span class="wc-scorer-goals">${'⚽'.repeat(Math.min(g.goals, 5))} ${g.goals}</span></span>`
      ).join('');
    }

    return `
      <div class="context-section">
        <div class="section-title">📋 Rendimiento en fase de grupos</div>
        <div class="wc-record-grid">
          <div class="wc-record-team">
            <div class="wc-record-label">${homeTeam.flag} ${homeTeam.team}</div>
            <div class="wc-record-val">${ctx.groupRecord.home}</div>
            <div class="wc-scorers-list">${goalsList(ctx.wcGoals && ctx.wcGoals.home)}</div>
          </div>
          <div class="wc-record-team">
            <div class="wc-record-label">${awayTeam.flag} ${awayTeam.team}</div>
            <div class="wc-record-val">${ctx.groupRecord.away}</div>
            <div class="wc-scorers-list">${goalsList(ctx.wcGoals && ctx.wcGoals.away)}</div>
          </div>
        </div>
      </div>`;
  }

  /* ─── Render: Alineaciones probables ─── */
  function renderLineups(ctx, homeTeam, awayTeam) {
    if (!ctx || !ctx.lineups) return '';
    return `
      <div class="context-section">
        <div class="section-title">📝 Alineaciones probables</div>
        <div class="lineups-grid">
          <div class="lineup-team">
            <div class="lineup-label">${homeTeam.flag} ${homeTeam.team}</div>
            <div class="lineup-text">${ctx.lineups.home}</div>
          </div>
          <div class="lineup-team">
            <div class="lineup-label">${awayTeam.flag} ${awayTeam.team}</div>
            <div class="lineup-text">${ctx.lineups.away}</div>
          </div>
        </div>
      </div>`;
  }

  /* ─── Render: H2H ─── */
  function renderH2H(h2h, homeTeam, awayTeam) {
    if (!h2h) return '';
    const total = h2h.homeWins + h2h.draws + h2h.awayWins;
    const homePct = Math.round((h2h.homeWins / total) * 100);
    const drawPct = Math.round((h2h.draws / total) * 100);
    const awayPct = 100 - homePct - drawPct;
    return `
      <div class="context-section">
        <div class="section-title">⚔️ Historial cara a cara (${h2h.played} encuentros)</div>
        <div class="h2h-bar-wrap">
          <div class="h2h-bar">
            <div class="h2h-seg h2h-home" style="width:${homePct}%" title="${homeTeam.team}: ${h2h.homeWins} victorias">${h2h.homeWins}V</div>
            <div class="h2h-seg h2h-draw" style="width:${drawPct}%" title="Empates: ${h2h.draws}">${h2h.draws}E</div>
            <div class="h2h-seg h2h-away" style="width:${awayPct}%" title="${awayTeam.team}: ${h2h.awayWins} victorias">${h2h.awayWins}V</div>
          </div>
          <div class="h2h-labels">
            <span style="color:var(--accent-blue)">${homeTeam.flag} ${homeTeam.team}</span>
            <span style="color:var(--text-muted);font-size:11px">Último: ${h2h.lastResult}</span>
            <span style="color:var(--accent-purple)">${awayTeam.flag} ${awayTeam.team}</span>
          </div>
        </div>
      </div>`;
  }

  /* ─── Render: Bajas, lesiones y suspendidos ─── */
  function renderInjuries(ctx, homeTeam, awayTeam) {
    const injuries = ctx.injuries || { home: [], away: [] };
    const suspensions = ctx.suspensions || { home: [], away: [] };
    const homeList = [...(injuries.home || []).map(i => ({ ...i, type: 'injury' })),
                     ...(suspensions.home || []).map(i => ({ ...i, type: 'suspension' }))];
    const awayList = [...(injuries.away || []).map(i => ({ ...i, type: 'injury' })),
                     ...(suspensions.away || []).map(i => ({ ...i, type: 'suspension' }))];

    if (homeList.length === 0 && awayList.length === 0) return '';

    function chips(list) {
      if (list.length === 0) return '<span style="color:var(--text-muted);font-size:11px">Sin bajas confirmadas</span>';
      return list.map(i => `
        <span class="injury-chip ${i.type === 'suspension' ? 'suspension' : ''}">
          <span class="injury-icon">${i.type === 'suspension' ? '🟥' : '🚫'}</span>
          <span class="injury-name">${i.player}</span>
          <span class="injury-reason">${i.reason}</span>
        </span>`).join('');
    }

    return `
      <div class="context-section">
        <div class="section-title">🏥 Bajas y suspendidos</div>
        <div class="injuries-grid">
          <div>
            <div class="injury-team-label">${homeTeam.flag} ${homeTeam.team}</div>
            <div class="injury-list">${chips(homeList)}</div>
          </div>
          <div>
            <div class="injury-team-label">${awayTeam.flag} ${awayTeam.team}</div>
            <div class="injury-list">${chips(awayList)}</div>
          </div>
        </div>
      </div>`;
  }

  /* ─── Render: xG y Jugador del partido ─── */
  function renderXgAndMotm(ctx, homeTeam, awayTeam) {
    if (!ctx) return '';
    let xgHtml = '';
    if (ctx.xg) {
      const homeXg = ctx.xg.home;
      const awayXg = ctx.xg.away;
      const [homePct, awayPct] = statPercent(homeXg, awayXg);
      xgHtml = `
        <div class="xg-row">
          <span class="xg-val" style="color:var(--accent-blue)">${homeXg}</span>
          <div class="xg-bars">
            <div class="xg-bar-home"><div class="xg-fill-home" style="width:${homePct}%"></div></div>
            <div class="xg-label">xG esperados</div>
            <div class="xg-bar-away"><div class="xg-fill-away" style="width:${awayPct}%"></div></div>
          </div>
          <span class="xg-val" style="color:var(--accent-purple)">${awayXg}</span>
        </div>`;
    }

    let motmHtml = '';
    if (ctx.motm) {
      const m = ctx.motm;
      motmHtml = `
        <div class="motm-block">
          <span class="motm-label">⭐ Jugador del partido</span>
          <span class="motm-player">${m.flag} ${m.player}</span>
          <span class="motm-prob">${m.probability}% probable</span>
        </div>`;
    }

    if (!xgHtml && !motmHtml) return '';
    return `<div class="xg-motm-section">${xgHtml}${motmHtml}</div>`;
  }

  /* ─── Render: Anotadores ─── */
  function renderScorers(scorers, match) {
    if (!scorers || scorers.length === 0) return '';
    const chips = scorers.map(s => {
      const side = s.team === match.home.team ? match.home : match.away;
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

  /* ─── Render: Barra stat ─── */
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

  /* ─── Render: Amarillas ─── */
  function renderYellows(stats, match) {
    const homeYellows = stats.home.yellowCards || [];
    const awayYellows = stats.away.yellowCards || [];
    function chips(players) {
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

  /* ─── Render: Card completa ─── */
  function renderCard(match) {
    const p = match.prediction;
    const ctx = match.context || null;
    const confClass = confidenceClass(p.confidence);
    const detailsId = `details-${match.id}`;
    const homeWC = winnerClass(match, 'home');
    const awayWC = winnerClass(match, 'away');
    const isCompleted = match.status === 'completed' && match.finalScore != null;

    const stageLabel = match.stage
      ? `<span class="stage-pill">${match.stage}</span>`
      : `<span class="group-pill">Grupo ${match.group} · J${match.matchday}</span>`;

    const statusChip = isCompleted
      ? `<span class="result-badge">Finalizado</span>`
      : `<span class="live-badge">Próximo</span>`;

    let scoreBlockHtml;
    if (isCompleted) {
      const fs = match.finalScore;
      const diff = fs.home - fs.away;
      const outcomeLabel = diff > 0
        ? `<span style="color:var(--accent-green)">Victoria ${match.home.team}</span>`
        : diff < 0
          ? `<span style="color:var(--accent-green)">Victoria ${match.away.team}</span>`
          : `<span style="color:var(--accent-orange)">Empate</span>`;
      scoreBlockHtml = `
        <div class="score-block">
          <div class="final-score">${fs.home} — ${fs.away}</div>
          <div class="score-label final">Resultado Final</div>
          <div class="predicted-subtext">Pred. ${p.result} · ${p.confidence}% conf.</div>
          <div style="margin-top:4px;font-size:11px;">${outcomeLabel}</div>
        </div>`;
    } else {
      const resultLabel = p.winner === 'draw'
        ? `<span style="color:var(--accent-orange)">Empate</span>`
        : `<span style="color:var(--accent-green)">Victoria ${p.winner === 'home' ? match.home.team : match.away.team}</span>`;
      scoreBlockHtml = `
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
        </div>`;
    }

    return `
      <article class="match-card ${isCompleted ? 'completed' : ''}" id="card-${match.id}" role="listitem">
        <div class="card-header">
          <div class="card-meta-left">
            ${stageLabel}
            ${statusChip}
            <span class="match-time">🕐 ${match.time} ET</span>
          </div>
          <span class="match-venue">📍 ${match.venue}</span>
        </div>

        <div class="matchup">
          <div class="team ${homeWC}">
            <span class="team-flag">${match.home.flag}</span>
            <span class="team-name">${match.home.team}</span>
            <span class="team-rank">FIFA #${match.home.fifaRank}</span>
          </div>

          ${scoreBlockHtml}

          <div class="team ${awayWC}">
            <span class="team-flag">${match.away.flag}</span>
            <span class="team-name">${match.away.team}</span>
            <span class="team-rank">FIFA #${match.away.fifaRank}</span>
          </div>
        </div>

        ${ctx ? renderXgAndMotm(ctx, match.home, match.away) : ''}

        ${!isCompleted ? renderScorers(p.scorers, match) : ''}

        <button class="card-toggle" onclick="toggleDetails('${detailsId}', this)" aria-expanded="false">
          <span>Ver análisis completo</span>
          <i class="toggle-icon">▼</i>
        </button>

        <div class="card-details" id="${detailsId}">
          ${ctx ? renderWCRecord(ctx, match.home, match.away) : ''}
          ${ctx ? renderForm(ctx.form, match.home, match.away) : ''}
          ${ctx ? renderH2H(ctx.h2h, match.home, match.away) : ''}
          ${ctx ? renderInjuries(ctx, match.home, match.away) : ''}
          ${ctx ? renderLineups(ctx, match.home, match.away) : ''}
          ${renderStats(p.stats, match)}
          ${renderYellows(p.stats, match)}
        </div>
      </article>`;
  }

  /* ─── Toggle ─── */
  window.toggleDetails = function (detailsId, btn) {
    const el = document.getElementById(detailsId);
    const isOpen = el.classList.contains('open');
    el.classList.toggle('open', !isOpen);
    btn.classList.toggle('open', !isOpen);
    btn.setAttribute('aria-expanded', String(!isOpen));
    btn.querySelector('span').textContent = isOpen ? 'Ver análisis completo' : 'Ocultar análisis';
  };

  /* ─── Main render ─── */
  function renderPage(fixtures, targetDate) {
    const displayDate = targetDate || TODAY;
    const todayMatches = fixtures.matches.filter(m => m.date === displayDate);

    const dateEl = document.getElementById('display-date');
    if (dateEl) dateEl.textContent = formatDisplayDate(displayDate);

    const stageEl = document.getElementById('current-stage');
    if (stageEl) stageEl.textContent = fixtures.tournament.currentStage || '';

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
    Object.keys(byTime).sort().forEach(time => {
      const matches = byTime[time];
      if (matches.length > 1) {
        html += `<div class="time-slot-label">🕐 ${time} ET — Simultáneos</div>`;
      }
      matches.forEach(m => { html += renderCard(m); });
    });

    container.innerHTML = html;
  }

  /* ─── Navegación ─── */
  function setupNavigation(fixtures) {
    const matchDates = [...new Set(fixtures.matches.map(m => m.date))].sort();
    const prevBtn = document.getElementById('btn-prev');
    const nextBtn = document.getElementById('btn-next');
    const todayBtn = document.getElementById('btn-today');

    let currentDate = matchDates.includes(TODAY)
      ? TODAY
      : matchDates[matchDates.length - 1];

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
      currentDate = matchDates.includes(TODAY) ? TODAY : matchDates[matchDates.length - 1];
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
