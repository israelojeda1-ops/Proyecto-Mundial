/* Análisis Tenis — odds.js */
(function () {
  'use strict';

  const TODAY = getLocalDateString();

  /* ─── Helpers de fecha ─── */
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

  /* ─── Núcleo del análisis de cuotas ───
     - impliedProb: probabilidad implícita bruta de una cuota decimal (1/cuota)
     - removeVig: normaliza un par de probabilidades implícitas para que sumen 100%,
       eliminando el margen de la casa de apuestas (overround)
  */
  function impliedProb(decimalOdds) {
    return 1 / decimalOdds;
  }

  function removeVig(p1Raw, p2Raw) {
    const total = p1Raw + p2Raw;
    return { p1: p1Raw / total, p2: p2Raw / total };
  }

  function analyzeOdds(match) {
    const bookNames = Object.keys(match.odds);
    const rows = bookNames.map(name => {
      const o = match.odds[name];
      const raw1 = impliedProb(o.p1);
      const raw2 = impliedProb(o.p2);
      const fair = removeVig(raw1, raw2);
      const overround = (raw1 + raw2 - 1) * 100;
      return { name, odds: o, fair, overround };
    });

    const avgOdds = {
      p1: rows.reduce((s, r) => s + r.odds.p1, 0) / rows.length,
      p2: rows.reduce((s, r) => s + r.odds.p2, 0) / rows.length
    };

    const consensusFair = {
      p1: (rows.reduce((s, r) => s + r.fair.p1, 0) / rows.length) * 100,
      p2: (rows.reduce((s, r) => s + r.fair.p2, 0) / rows.length) * 100
    };

    const bestOdds = {
      p1: Math.max(...rows.map(r => r.odds.p1)),
      p2: Math.max(...rows.map(r => r.odds.p2))
    };

    const projection = match.ourProjection;
    const edge = {
      p1: projection.p1 - consensusFair.p1,
      p2: projection.p2 - consensusFair.p2
    };

    return { rows, avgOdds, consensusFair, bestOdds, projection, edge };
  }

  function edgeClass(edgeVal) {
    return edgeVal >= 3 ? 'positive' : 'negative';
  }

  /* ─── Render: tabla de cuotas ─── */
  function renderOddsTable(analysis, match) {
    const rows = analysis.rows.map(r => `
      <tr>
        <td>${r.name}</td>
        <td><span class="odds-val ${r.odds.p1 === analysis.bestOdds.p1 ? 'best' : ''}">${r.odds.p1.toFixed(2)}</span></td>
        <td><span class="odds-val ${r.odds.p2 === analysis.bestOdds.p2 ? 'best' : ''}">${r.odds.p2.toFixed(2)}</span></td>
      </tr>`).join('');

    return `
      <div class="odds-section">
        <div class="section-title">💰 Cuotas por casa de apuestas</div>
        <table class="odds-table">
          <thead>
            <tr><th>Casa</th><th>${match.player1.name}</th><th>${match.player2.name}</th></tr>
          </thead>
          <tbody>
            ${rows}
            <tr class="odds-row-avg">
              <td>Promedio</td>
              <td>${analysis.avgOdds.p1.toFixed(2)}</td>
              <td>${analysis.avgOdds.p2.toFixed(2)}</td>
            </tr>
          </tbody>
        </table>
      </div>`;
  }

  /* ─── Render: bloque de valor (edge) ─── */
  function renderValueSection(analysis, match) {
    function block(side, player) {
      const fair = analysis.consensusFair[side];
      const proj = analysis.projection[side];
      const edge = analysis.edge[side];
      const cls = edgeClass(edge);
      const hasValue = edge >= 3;
      const sign = edge >= 0 ? '+' : '';
      return `
        <div class="value-block ${hasValue ? 'has-value' : ''}">
          <div class="value-player">${player.flag} ${player.name}</div>
          <div class="value-row"><span>Prob. de mercado (sin margen)</span><span>${fair.toFixed(1)}%</span></div>
          <div class="value-row"><span>Nuestra proyección</span><span>${proj}%</span></div>
          <div class="value-row"><span>Edge</span><span class="value-edge ${cls}">${sign}${edge.toFixed(1)}pp</span></div>
          ${hasValue ? '<span class="value-tag">Valor</span>' : ''}
        </div>`;
    }
    return `
      <div class="value-section">
        ${block('p1', match.player1)}
        ${block('p2', match.player2)}
      </div>`;
  }

  /* ─── Render: recomendación ─── */
  function renderRecommendation(analysis, match) {
    const bestSide = analysis.edge.p1 >= analysis.edge.p2 ? 'p1' : 'p2';
    const bestEdge = analysis.edge[bestSide];
    const player = bestSide === 'p1' ? match.player1 : match.player2;

    let text;
    if (bestEdge >= 5) {
      text = `Valor claro sobre <strong>${player.name}</strong>: nuestra proyección supera la probabilidad de mercado por ${bestEdge.toFixed(1)} puntos porcentuales.`;
    } else if (bestEdge >= 3) {
      text = `Ligero valor sobre <strong>${player.name}</strong> (+${bestEdge.toFixed(1)}pp), dentro del margen razonable para considerar la apuesta.`;
    } else {
      text = `Sin valor claro en ninguno de los dos lados — la cuota de mercado refleja de forma razonable nuestra proyección.`;
    }
    const icon = bestEdge >= 3 ? '📈' : '⚖️';
    return `<div class="recommendation"><span class="icon">${icon}</span><span>${text}</span></div>`;
  }

  /* ─── Render: probabilidad en el matchup ─── */
  function renderProbBar(analysis) {
    const p1 = analysis.consensusFair.p1;
    const p2 = analysis.consensusFair.p2;
    return `
      <div class="vs-block">
        <span class="vs-label">VS</span>
        <div class="prob-bar-wrap">
          <div class="prob-bar">
            <div class="prob-fill-p1" style="width:${p1}%"></div>
            <div class="prob-fill-p2" style="width:${p2}%"></div>
          </div>
          <div class="prob-pct-row">
            <span>${p1.toFixed(0)}%</span>
            <span>${p2.toFixed(0)}%</span>
          </div>
        </div>
      </div>`;
  }

  /* ─── Render: forma reciente ─── */
  function renderForm(ctx, p1, p2) {
    if (!ctx || !ctx.form) return '';
    function dots(arr) {
      return arr.map(r => {
        const cls = r === 'W' ? 'form-w' : r === 'D' ? 'form-d' : 'form-l';
        const label = r === 'W' ? 'Victoria' : r === 'D' ? 'Empate' : 'Derrota';
        return `<span class="form-dot ${cls}" title="${label}">${r}</span>`;
      }).join('');
    }
    return `
      <div class="context-section">
        <div class="section-title">📈 Forma reciente</div>
        <div class="form-rows">
          <div class="form-row">
            <span class="form-player-label">${p1.flag} ${p1.name}</span>
            <div class="form-dots">${dots(ctx.form.p1)}</div>
          </div>
          <div class="form-row">
            <span class="form-player-label">${p2.flag} ${p2.name}</span>
            <div class="form-dots">${dots(ctx.form.p2)}</div>
          </div>
        </div>
      </div>`;
  }

  /* ─── Render: H2H ─── */
  function renderH2H(ctx, p1, p2) {
    if (!ctx || !ctx.h2h) return '';
    const h2h = ctx.h2h;
    if (h2h.played === 0) {
      return `
        <div class="context-section">
          <div class="section-title">⚔️ Historial cara a cara</div>
          <div class="h2h-empty">Sin precedentes entre ambos jugadores.</div>
        </div>`;
    }
    const p1Pct = Math.round((h2h.p1Wins / h2h.played) * 100);
    const p2Pct = 100 - p1Pct;
    return `
      <div class="context-section">
        <div class="section-title">⚔️ Historial cara a cara (${h2h.played} enfrentamiento${h2h.played > 1 ? 's' : ''})</div>
        <div class="h2h-bar-wrap">
          <div class="h2h-bar">
            <div class="h2h-seg h2h-p1" style="width:${p1Pct}%" title="${p1.name}: ${h2h.p1Wins} victorias">${h2h.p1Wins}V</div>
            <div class="h2h-seg h2h-p2" style="width:${p2Pct}%" title="${p2.name}: ${h2h.p2Wins} victorias">${h2h.p2Wins}V</div>
          </div>
          <div class="h2h-labels">
            <span style="color:var(--accent-green)">${p1.flag} ${p1.name}</span>
            <span style="color:var(--text-muted);font-size:11px">Último: ${h2h.lastResult}</span>
            <span style="color:#c9a8ec">${p2.flag} ${p2.name}</span>
          </div>
        </div>
      </div>`;
  }

  /* ─── Render: récord en superficie + stats clave ─── */
  function renderSurfaceAndStats(ctx, p1, p2) {
    if (!ctx) return '';
    let html = '';
    if (ctx.surfaceRecord) {
      html += `
        <div class="context-section">
          <div class="section-title">🌱 Récord en césped</div>
          <div class="surface-grid">
            <div>
              <div class="surface-label">${p1.flag} ${p1.name}</div>
              <div class="surface-val">${ctx.surfaceRecord.p1}</div>
            </div>
            <div>
              <div class="surface-label">${p2.flag} ${p2.name}</div>
              <div class="surface-val">${ctx.surfaceRecord.p2}</div>
            </div>
          </div>
        </div>`;
    }
    if (ctx.keyStats) {
      function statsBlock(player, s) {
        return `
          <div>
            <div class="stats-player-label">${player.flag} ${player.name}</div>
            <div class="stat-line"><span>Aces / partido</span><span class="val">${s.acesPerMatch}</span></div>
            <div class="stat-line"><span>1er saque %</span><span class="val">${s.firstServePct}%</span></div>
            <div class="stat-line"><span>Puntos de quiebre ganados</span><span class="val">${s.breakPointsWonPct}%</span></div>
          </div>`;
      }
      html += `
        <div class="context-section">
          <div class="section-title">📊 Estadísticas clave</div>
          <div class="stats-grid-tennis">
            ${statsBlock(p1, ctx.keyStats.p1)}
            ${statsBlock(p2, ctx.keyStats.p2)}
          </div>
        </div>`;
    }
    if (ctx.notes) {
      html += `
        <div class="context-section">
          <div class="section-title">📝 Notas del analista</div>
          <p class="notes-text">${ctx.notes}</p>
        </div>`;
    }
    return html;
  }

  /* ─── Render: card completa ─── */
  function renderCard(match) {
    const analysis = analyzeOdds(match);
    const detailsId = `details-${match.id}`;
    const favSide = analysis.consensusFair.p1 >= analysis.consensusFair.p2 ? 'p1' : 'p2';

    return `
      <article class="match-card" id="card-${match.id}" role="listitem">
        <div class="card-header">
          <div class="card-meta-left">
            <span class="round-pill">${match.round}</span>
            <span class="match-time">🕐 ${match.time}</span>
          </div>
          <span class="match-court">📍 ${match.court}</span>
        </div>

        <div class="matchup">
          <div class="player ${favSide === 'p1' ? 'favorite' : ''}">
            <span class="player-flag">${match.player1.flag}</span>
            <span class="player-name">${match.player1.name}</span>
            <span class="player-rank">ATP #${match.player1.rank}</span>
          </div>

          ${renderProbBar(analysis)}

          <div class="player ${favSide === 'p2' ? 'favorite' : ''}">
            <span class="player-flag">${match.player2.flag}</span>
            <span class="player-name">${match.player2.name}</span>
            <span class="player-rank">ATP #${match.player2.rank}</span>
          </div>
        </div>

        ${renderOddsTable(analysis, match)}
        ${renderValueSection(analysis, match)}
        ${renderRecommendation(analysis, match)}

        <button class="card-toggle" onclick="toggleDetails('${detailsId}', this)" aria-expanded="false">
          <span>Ver análisis completo</span>
          <i class="toggle-icon">▼</i>
        </button>

        <div class="card-details" id="${detailsId}">
          ${renderForm(match.context, match.player1, match.player2)}
          ${renderH2H(match.context, match.player1, match.player2)}
          ${renderSurfaceAndStats(match.context, match.player1, match.player2)}
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
  function renderPage(data, targetDate) {
    const displayDate = targetDate || TODAY;
    const todayMatches = data.matches.filter(m => m.date === displayDate);

    const dateEl = document.getElementById('display-date');
    if (dateEl) dateEl.textContent = formatDisplayDate(displayDate);

    const roundEl = document.getElementById('current-round');
    if (roundEl) roundEl.textContent = data.tournament.currentRound || '';

    const badgeEl = document.getElementById('tournament-badge');
    if (badgeEl) badgeEl.textContent = data.tournament.name || 'ATP';

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
      byTime[time].forEach(m => { html += renderCard(m); });
    });

    container.innerHTML = html;
  }

  /* ─── Navegación ─── */
  function setupNavigation(data) {
    const matchDates = [...new Set(data.matches.map(m => m.date))].sort();
    const prevBtn = document.getElementById('btn-prev');
    const nextBtn = document.getElementById('btn-next');
    const todayBtn = document.getElementById('btn-today');

    let currentDate = matchDates.includes(TODAY)
      ? TODAY
      : matchDates[matchDates.length - 1];

    function update() {
      renderPage(data, currentDate);
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
      const resp = await fetch('./data/wimbledon_2026.json');
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      const data = await resp.json();
      setupNavigation(data);
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
      console.error('Análisis Tenis error:', err);
    }
  }

  document.addEventListener('DOMContentLoaded', init);
})();
