/* Análisis Tenis — combinada.js (Analizador de Combinadas) */
(function () {
  'use strict';

  const SLIPS = [
    { id: '2026-07-01', label: '1 jul · Combinada de 7', file: './data/combinada_2026-07-01.json' },
    { id: '2026-07-02', label: '2 jul · Combinada de 10', file: './data/combinada_2026-07-02.json' }
  ];

  function formatDisplayDate(isoDate) {
    const [year, month, day] = isoDate.split('-').map(Number);
    const d = new Date(year, month - 1, day);
    return d.toLocaleDateString('es-ES', {
      weekday: 'long', year: 'numeric', month: 'long', day: 'numeric'
    });
  }

  function formatMoney(n, currency) {
    if (n === null || n === undefined) return 'No especificado';
    return currency + n.toLocaleString('es-ES', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  }

  function impliedProb(decimalOdds) {
    return (1 / decimalOdds) * 100;
  }

  function riskClass(level) {
    if (level === 'bajo') return 'risk-low';
    if (level === 'medio' || level === 'bajo-medio') return 'risk-mid';
    return 'risk-high';
  }

  function riskLabel(level) {
    const map = {
      'bajo': 'Riesgo bajo',
      'bajo-medio': 'Riesgo bajo-medio',
      'medio': 'Riesgo medio',
      'alto': 'Riesgo alto'
    };
    return map[level] || level;
  }

  function typeTagLabel(tag) {
    const map = {
      'moneyline': '🎯 Ganador',
      'player-total': '📏 Ganador + Total',
      'bet-builder': '🧩 Bet Builder',
      'set-score': '📊 Marcador de set'
    };
    return map[tag] || tag;
  }

  /* ─── Render: resumen del boleto ─── */
  function renderSlipSummary(data) {
    const slip = data.slip;
    const legs = data.legs;

    const impliedTotal = (1 / slip.totalOdds) * 100;
    const ourCombined = legs.reduce((acc, leg) => acc * (leg.ourProbability / 100), 1) * 100;
    const gapPp = impliedTotal - ourCombined;

    const riskyLegsForVerdict = legs.filter(l => l.riskLevel === 'alto');
    const riskyNames = riskyLegsForVerdict.map(l => l.match).join(' y ');

    let verdictText, verdictClass;
    if (gapPp >= 8) {
      verdictClass = 'verdict-caution';
      verdictText = `Nuestra estimación (${ourCombined.toFixed(1)}%) queda bien por debajo de la probabilidad implícita por la cuota total (${impliedTotal.toFixed(1)}%). El boleto es más arriesgado de lo que sugiere el precio${riskyNames ? ` — principalmente por: ${riskyNames}` : ''}.`;
    } else if (gapPp >= 3) {
      verdictClass = 'verdict-mid';
      verdictText = `Nuestra estimación (${ourCombined.toFixed(1)}%) está algo por debajo de la probabilidad implícita (${impliedTotal.toFixed(1)}%). Riesgo moderado, razonable para el pago ofrecido.`;
    } else {
      verdictClass = 'verdict-ok';
      verdictText = `Nuestra estimación (${ourCombined.toFixed(1)}%) es cercana a la probabilidad implícita por la cuota (${impliedTotal.toFixed(1)}%) — precio razonablemente justo.`;
    }

    const riskyLegs = legs.filter(l => l.riskLevel === 'alto');

    return `
      <div class="slip-header">
        <div class="slip-title">
          <span class="slip-bookmaker">${slip.bookmaker}</span>
          <span class="slip-type">${slip.type}</span>
        </div>
        <div class="slip-odds">${slip.totalOdds.toFixed(2)}</div>
      </div>
      <div class="slip-numbers">
        <div class="slip-num-item">
          <span class="slip-num-label">Apuesta</span>
          <span class="slip-num-val">${formatMoney(slip.stake, slip.currency)}</span>
        </div>
        <div class="slip-num-item">
          <span class="slip-num-label">Ganancia potencial</span>
          <span class="slip-num-val win">${formatMoney(slip.potentialWinnings, slip.currency)}</span>
        </div>
        <div class="slip-num-item">
          <span class="slip-num-label">Prob. implícita (cuota total)</span>
          <span class="slip-num-val">${impliedTotal.toFixed(1)}%</span>
        </div>
        <div class="slip-num-item">
          <span class="slip-num-label">Nuestra prob. combinada</span>
          <span class="slip-num-val ${gapPp >= 8 ? 'danger' : ''}">${ourCombined.toFixed(1)}%</span>
        </div>
      </div>
      <div class="verdict-box ${verdictClass}">
        <span class="verdict-icon">${gapPp >= 8 ? '⚠️' : gapPp >= 3 ? '⚖️' : '✅'}</span>
        <span>${verdictText}</span>
      </div>
      ${riskyLegs.length > 0 ? `
        <div class="risky-legs-note">
          <strong>Patas de mayor riesgo real:</strong> ${riskyLegs.map(l => l.match).join(' · ')}
        </div>` : ''}
    `;
  }

  /* ─── Render: una pata ─── */
  function renderLeg(leg) {
    const implied = impliedProb(leg.odds);
    const edge = leg.ourProbability - implied;
    const edgeSign = edge >= 0 ? '+' : '';
    const r = leg.research;

    const sourcesHtml = (r.sources || []).map(s =>
      `<a href="${s.url}" target="_blank" rel="noopener" class="source-link">${s.title}</a>`
    ).join('');

    return `
      <article class="match-card leg-card" role="listitem">
        <div class="card-header">
          <div class="card-meta-left">
            <span class="round-pill">${typeTagLabel(leg.typeTag)}</span>
            <span class="match-time">🕐 ${leg.time}</span>
          </div>
          <span class="risk-badge ${riskClass(leg.riskLevel)}">${riskLabel(leg.riskLevel)}</span>
        </div>

        <div class="leg-body">
          <div class="leg-match">${leg.match}</div>
          <div class="leg-round">${leg.round}</div>
          <div class="leg-selection">${leg.selection}</div>

          <div class="leg-prob-row">
            <div class="leg-prob-item">
              <span class="leg-prob-label">Cuota</span>
              <span class="leg-prob-val">${leg.odds.toFixed(2)}</span>
            </div>
            <div class="leg-prob-item">
              <span class="leg-prob-label">Prob. implícita</span>
              <span class="leg-prob-val">${implied.toFixed(1)}%</span>
            </div>
            <div class="leg-prob-item">
              <span class="leg-prob-label">Nuestra estimación</span>
              <span class="leg-prob-val accent">${leg.ourProbability}%</span>
            </div>
            <div class="leg-prob-item">
              <span class="leg-prob-label">Edge</span>
              <span class="leg-prob-val ${edge >= 0 ? 'positive' : 'negative'}">${edgeSign}${edge.toFixed(1)}pp</span>
            </div>
          </div>
        </div>

        <div class="context-section">
          <div class="section-title">⚔️ Historial</div>
          <p class="notes-text">${r.h2h}</p>
        </div>
        <div class="context-section">
          <div class="section-title">📈 Forma y contexto</div>
          <p class="notes-text">${r.form}</p>
        </div>
        <div class="context-section">
          <div class="section-title">📝 Análisis</div>
          <p class="notes-text">${r.notes}</p>
        </div>
        ${sourcesHtml ? `
        <div class="context-section leg-sources">
          <div class="section-title">🔗 Fuentes</div>
          <div class="sources-list">${sourcesHtml}</div>
        </div>` : ''}
      </article>`;
  }

  /* ─── Selector de combinadas ─── */
  function renderSelector(activeId) {
    const el = document.getElementById('slip-selector');
    if (!el) return;
    el.innerHTML = SLIPS.map(s => `
      <button class="slip-tab ${s.id === activeId ? 'active' : ''}" data-slip-id="${s.id}">${s.label}</button>
    `).join('');
    el.querySelectorAll('.slip-tab').forEach(btn => {
      btn.addEventListener('click', () => loadSlip(btn.dataset.slipId));
    });
  }

  /* ─── Carga y render de una combinada ─── */
  async function loadSlip(slipId) {
    const slipDef = SLIPS.find(s => s.id === slipId) || SLIPS[SLIPS.length - 1];
    renderSelector(slipDef.id);

    const summaryEl = document.getElementById('slip-summary');
    if (summaryEl) summaryEl.innerHTML = `<div class="no-matches"><div class="no-matches-icon">⏳</div><h3>Cargando combinada…</h3></div>`;
    const legsEl = document.getElementById('legs-container');
    if (legsEl) legsEl.innerHTML = '';

    try {
      const resp = await fetch(slipDef.file);
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      const data = await resp.json();

      const dateEl = document.getElementById('display-date');
      if (dateEl) dateEl.textContent = formatDisplayDate(data.slip.date);

      const badgeEl = document.getElementById('bookmaker-badge');
      if (badgeEl) badgeEl.textContent = `${data.slip.bookmaker} · ${data.slip.type}`;

      if (summaryEl) summaryEl.innerHTML = renderSlipSummary(data);

      const countEl = document.getElementById('leg-count');
      if (countEl) countEl.textContent = data.legs.length;

      if (legsEl) legsEl.innerHTML = data.legs.map(renderLeg).join('');

      const disclaimerEl = document.getElementById('disclaimer-text');
      if (disclaimerEl) disclaimerEl.textContent = data.disclaimer;

    } catch (err) {
      if (legsEl) {
        legsEl.innerHTML = `
          <div class="no-matches">
            <div class="no-matches-icon">⚠️</div>
            <h3>Error al cargar la combinada</h3>
            <p style="color:var(--text-muted)">${err.message}</p>
          </div>`;
      }
      console.error('Analizador de Combinadas error:', err);
    }
  }

  /* ─── Bootstrap ─── */
  function init() {
    const defaultSlip = SLIPS[SLIPS.length - 1];
    loadSlip(defaultSlip.id);
  }

  document.addEventListener('DOMContentLoaded', init);
})();
