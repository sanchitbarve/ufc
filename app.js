/**
 * UFC FIGHT PREDICTOR - PURE VANILLA JAVASCRIPT
 * Dynamic controls, weightclass-specific themes, API connection, and animated gauges
 */

(function () {
  'use strict';

  // --- APPLICATION STATE ---
  let appData = {
    weight_classes: [],
    rosters: {},
    activeWeightClass: 'All Weight Classes',
    fighterA: '',
    fighterB: '',
    predictionResult: null
  };

  // Division Subtitles and Icons Metadata
  const DIVISION_META = {
    'Heavyweight': { icon: '🛡️', subtitle: 'TITANIUM HEAVYWEIGHT DIVISION • 265 LBS (120 KG)', short: 'Heavyweight' },
    'Light Heavyweight': { icon: '⚡', subtitle: 'LIGHT HEAVYWEIGHT DIVISION • 205 LBS (93 KG)', short: 'Light Heavy' },
    'Middleweight': { icon: '⚔️', subtitle: 'MIDDLEWEIGHT DIVISION • 185 LBS (84 KG)', short: 'Middleweight' },
    'Welterweight': { icon: '🔋', subtitle: 'WELTERWEIGHT DIVISION • 170 LBS (77 KG)', short: 'Welterweight' },
    'Lightweight': { icon: '🔥', subtitle: 'LIGHTWEIGHT DIVISION • 155 LBS (70 KG) [SHARK TANK]', short: 'Lightweight' },
    'Featherweight': { icon: '🪶', subtitle: 'FEATHERWEIGHT DIVISION • 145 LBS (66 KG)', short: 'Featherweight' },
    'Bantamweight': { icon: '⚡', subtitle: 'BANTAMWEIGHT DIVISION • 135 LBS (61 KG)', short: 'Bantamweight' },
    'Flyweight': { icon: '💨', subtitle: 'FLYWEIGHT DIVISION • 125 LBS (57 KG)', short: 'Flyweight' },
    "Women's Strawweight": { icon: '👑', subtitle: "WOMEN'S STRAWWEIGHT CHAMPIONSHIP • 115 LBS", short: "W. Strawweight" },
    "Women's Flyweight": { icon: '👑', subtitle: "WOMEN'S FLYWEIGHT CHAMPIONSHIP • 125 LBS", short: "W. Flyweight" },
    "Women's Bantamweight": { icon: '👑', subtitle: "WOMEN'S BANTAMWEIGHT CHAMPIONSHIP • 135 LBS", short: "W. Bantamweight" },
    "Women's Featherweight": { icon: '👑', subtitle: "WOMEN'S FEATHERWEIGHT CHAMPIONSHIP • 145 LBS", short: "W. Featherweight" },
    'Catch Weight': { icon: '⚖️', subtitle: 'CATCH WEIGHT SPECIAL ATTRACTION', short: 'Catch Weight' },
    'All Weight Classes': { icon: '🌐', subtitle: 'OPEN ROSTER • ALL WEIGHT DIVISIONS', short: 'All Classes' }
  };

  // --- DOM ELEMENTS ---
  const themeToggleBtn = document.getElementById('themeToggleBtn');
  const themeIcon = document.getElementById('themeIcon');
  const weightClassSelect = document.getElementById('weightClassSelect');
  const wcPillsContainer = document.getElementById('wcPillsContainer');
  const activeDivisionTag = document.getElementById('activeDivisionTag');
  const divisionIcon = document.getElementById('divisionIcon');
  const divisionSubtitle = document.getElementById('divisionSubtitle');
  const redDivisionTag = document.getElementById('redDivisionTag');
  const blueDivisionTag = document.getElementById('blueDivisionTag');
  const fighterASelect = document.getElementById('fighterASelect');
  const fighterBSelect = document.getElementById('fighterBSelect');
  const fighterASearch = document.getElementById('fighterASearch');
  const fighterBSearch = document.getElementById('fighterBSearch');
  const swapCornersBtn = document.getElementById('swapCornersBtn');
  const predictBtn = document.getElementById('predictBtn');
  const randomMatchupBtn = document.getElementById('randomMatchupBtn');
  const resetMatchupBtn = document.getElementById('resetMatchupBtn');
  const toggleStatsBtn = document.getElementById('toggleStatsBtn');
  const predictionSection = document.getElementById('predictionSection');
  const statsTableCard = document.getElementById('statsTableCard');
  const winnerName = document.getElementById('winnerName');
  const winnerSubtext = document.getElementById('winnerSubtext');
  const gaugeNameA = document.getElementById('gaugeNameA');
  const gaugeNameB = document.getElementById('gaugeNameB');
  const gaugePctA = document.getElementById('gaugePctA');
  const gaugePctB = document.getElementById('gaugePctB');
  const gaugeArcA = document.getElementById('gaugeArcA');
  const gaugeArcB = document.getElementById('gaugeArcB');
  const gaugeNeedleA = document.getElementById('gaugeNeedleA');
  const gaugeNeedleB = document.getElementById('gaugeNeedleB');
  const comparisonRowsContainer = document.getElementById('comparisonRowsContainer');
  const toast = document.getElementById('toast');

  // --- INITIALIZATION ---
  async function init() {
    initTheme();
    setupEventListeners();
    await fetchAllData();
  }

  // --- THEME SYSTEM (DARK / LIGHT MODE) ---
  function initTheme() {
    const savedTheme = localStorage.getItem('ufc_theme') || 'dark';
    setTheme(savedTheme);
  }

  function setTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('ufc_theme', theme);
    if (theme === 'light') {
      themeIcon.textContent = '🌙';
      themeToggleBtn.title = 'Switch to Octagon Dark Mode';
    } else {
      themeIcon.textContent = '☀️';
      themeToggleBtn.title = 'Switch to Arena Light Mode';
    }
  }

  function toggleTheme() {
    const currentTheme = document.documentElement.getAttribute('data-theme') || 'dark';
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    setTheme(newTheme);
  }

  // --- API DATA FETCHING ---
  async function fetchAllData() {
    try {
      showToast('⚡ Connecting to UFC AI Engine...', false);
      const res = await fetch('/api/all-data');
      if (!res.ok) {
        throw new Error(`Server returned HTTP ${res.status}`);
      }
      const data = await res.json();
      appData.weight_classes = data.weight_classes || [];
      appData.rosters = data.rosters || {};

      renderWeightClassDropdown();
      renderWeightClassPills();
      setActiveWeightClass('All Weight Classes');
      showToast('✓ Engine ready: 7,000+ UFC bouts loaded', false, 2500);
    } catch (err) {
      console.error('Error fetching backend data:', err);
      showToast(`Error connecting to backend: ${err.message}`, true, 6000);
    }
  }

  // --- RENDER WEIGHT CLASS DROPDOWN & PILLS ---
  function renderWeightClassDropdown() {
    weightClassSelect.innerHTML = '';
    appData.weight_classes.forEach((wc) => {
      const opt = document.createElement('option');
      opt.value = wc;
      const meta = DIVISION_META[wc] || { icon: '🥊' };
      opt.textContent = `${meta.icon} ${wc}`;
      weightClassSelect.appendChild(opt);
    });
  }

  function renderWeightClassPills() {
    wcPillsContainer.innerHTML = '';
    appData.weight_classes.forEach((wc) => {
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'wc-pill-btn';
      if (wc === appData.activeWeightClass) btn.classList.add('active');
      const meta = DIVISION_META[wc] || { short: wc };
      btn.textContent = meta.short || wc;
      btn.addEventListener('click', () => {
        weightClassSelect.value = wc;
        setActiveWeightClass(wc);
      });
      wcPillsContainer.appendChild(btn);
    });
  }

  // --- SET ACTIVE WEIGHT CLASS & DYNAMIC THEME ---
  function setActiveWeightClass(wc) {
    appData.activeWeightClass = wc;
    weightClassSelect.value = wc;

    // Apply weight class bespoke theme attribute to DOM
    document.documentElement.setAttribute('data-weightclass', wc);

    // Update Banner & Division Badges
    const meta = DIVISION_META[wc] || { icon: '🥊', subtitle: `${wc.toUpperCase()} DIVISION`, short: wc };
    divisionIcon.textContent = meta.icon;
    divisionSubtitle.textContent = meta.subtitle;
    activeDivisionTag.textContent = meta.short.toUpperCase();
    redDivisionTag.textContent = `${meta.short.toUpperCase()} ROSTER`;
    blueDivisionTag.textContent = `${meta.short.toUpperCase()} ROSTER`;

    // Highlight active pill
    document.querySelectorAll('.wc-pill-btn').forEach((btn) => {
      if (btn.textContent === (meta.short || wc)) {
        btn.classList.add('active');
      } else {
        btn.classList.remove('active');
      }
    });

    // Populate Fighters for this weight class
    populateFighterDropdowns(wc);
  }

  // --- POPULATE FIGHTER DROPDOWNS ---
  function populateFighterDropdowns(weightClass) {
    const roster = appData.rosters[weightClass] || appData.rosters['All Weight Classes'] || [];

    if (roster.length === 0) {
      fighterASelect.innerHTML = '<option value="">No fighters found</option>';
      fighterBSelect.innerHTML = '<option value="">No fighters found</option>';
      return;
    }

    renderFighterOptions(fighterASelect, roster, fighterASearch.value);
    renderFighterOptions(fighterBSelect, roster, fighterBSearch.value);

    // Pick two default fighters
    if (roster.length > 0) {
      fighterASelect.value = roster[0];
      appData.fighterA = roster[0];
    }
    if (roster.length > 1) {
      fighterBSelect.value = roster[1];
      appData.fighterB = roster[1];
    } else {
      fighterBSelect.value = roster[0];
      appData.fighterB = roster[0];
    }

    updateFighterSnapshotStats('A', appData.fighterA);
    updateFighterSnapshotStats('B', appData.fighterB);
  }

  function renderFighterOptions(selectEl, roster, filterText = '') {
    const previousVal = selectEl.value;
    selectEl.innerHTML = '';

    const cleanFilter = filterText.trim().toLowerCase();
    const filtered = cleanFilter
      ? roster.filter((f) => f.toLowerCase().includes(cleanFilter))
      : roster;

    if (filtered.length === 0) {
      const opt = document.createElement('option');
      opt.value = '';
      opt.textContent = `No match for "${filterText}"`;
      selectEl.appendChild(opt);
      return;
    }

    filtered.forEach((fighter) => {
      const opt = document.createElement('option');
      opt.value = fighter;
      opt.textContent = fighter;
      selectEl.appendChild(opt);
    });

    if (filtered.includes(previousVal)) {
      selectEl.value = previousVal;
    }
  }

  // --- PREDICT FIGHT ACTION ---
  async function predictFight() {
    const fighterA = fighterASelect.value;
    const fighterB = fighterBSelect.value;

    if (!fighterA || !fighterB) {
      showToast('⚠️ Please select both Red and Blue corner fighters.', true);
      return;
    }

    if (fighterA === fighterB) {
      showToast('⚠️ Please select two different fighters.', true);
      return;
    }

    // Set UI loading state
    predictBtn.classList.add('loading');
    showToast(`🥊 Simulating bout: ${fighterA} vs ${fighterB}...`, false);

    try {
      const res = await fetch('/api/predict', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          fighter_a: fighterA,
          fighter_b: fighterB,
          weight_class: appData.activeWeightClass
        })
      });

      if (!res.ok) {
        const errJson = await res.json().catch(() => ({}));
        throw new Error(errJson.error || `HTTP ${res.status}`);
      }

      const result = await res.json();
      appData.predictionResult = result;

      // Render Results Dashboard
      renderPredictionResults(result);
      showToast(`🏆 Prediction complete! Winner: ${result.winner}`, false, 3500);
    } catch (err) {
      console.error('Prediction failed:', err);
      showToast(`Prediction failed: ${err.message}`, true, 5000);
    } finally {
      predictBtn.classList.remove('loading');
    }
  }

  // --- RENDER PREDICTION RESULTS & GAUGES ---
  function renderPredictionResults(data) {
    predictionSection.classList.add('active');

    // 1. Winner Proclamation
    winnerName.textContent = data.winner;
    const winProb = data.winner === data.fighter_a ? data.prob_a : data.prob_b;
    const cornerLabel = data.winner_corner === 'red' ? '🔴 RED CORNER' : '🔵 BLUE CORNER';
    winnerSubtext.textContent = `${cornerLabel} • Confidence: ${winProb}% Random Forest Probability`;

    // 2. Dual Gauge Charts
    gaugeNameA.textContent = data.fighter_a;
    gaugeNameB.textContent = data.fighter_b;

    // Update Quick Snapshot cards with exact fighter metrics
    if (data.stats_a) {
      document.getElementById('quickReachA').textContent = `${data.stats_a.reach_cms || '--'} cm`;
      document.getElementById('quickRecordA').textContent = `${data.stats_a.wins || 0}W / ${data.stats_a.losses || 0}L`;
      document.getElementById('quickStreakA').textContent = `${data.stats_a.current_win_streak || 0} Wins`;
    }
    if (data.stats_b) {
      document.getElementById('quickReachB').textContent = `${data.stats_b.reach_cms || '--'} cm`;
      document.getElementById('quickRecordB').textContent = `${data.stats_b.wins || 0}W / ${data.stats_b.losses || 0}L`;
      document.getElementById('quickStreakB').textContent = `${data.stats_b.current_win_streak || 0} Wins`;
    }

    animateGauge('A', data.prob_a);
    animateGauge('B', data.prob_b);

    // 3. Head-to-head Tale of the Tape comparison
    renderComparisonTable(data.comparison, data.fighter_a, data.fighter_b);

    // Smoothly scroll down to prediction
    predictionSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  // Custom Animated SVG Gauge
  function animateGauge(corner, percentage) {
    const pctNumber = corner === 'A' ? gaugePctA : gaugePctB;
    const gaugeArc = corner === 'A' ? gaugeArcA : gaugeArcB;
    const gaugeNeedle = corner === 'A' ? gaugeNeedleA : gaugeNeedleB;

    // Semi-circle perimeter in SVG coordinates (~330 units)
    const maxDash = 330;
    const targetOffset = maxDash - (maxDash * (percentage / 100));

    gaugeArc.style.strokeDashoffset = targetOffset;

    // Needle rotation: from -90deg (0%) to +90deg (100%)
    const needleDeg = -90 + (percentage / 100) * 180;
    gaugeNeedle.style.transform = `rotate(${needleDeg}deg)`;

    // Counter animation
    let currentPct = 0;
    const step = percentage / 30;
    const timer = setInterval(() => {
      currentPct += step;
      if (currentPct >= percentage) {
        currentPct = percentage;
        clearInterval(timer);
      }
      pctNumber.textContent = `${currentPct.toFixed(1)}%`;
    }, 25);
  }

  // Render Tale of the Tape Comparison Rows
  function renderComparisonTable(comparison, nameA, nameB) {
    comparisonRowsContainer.innerHTML = '';

    comparison.forEach((row) => {
      const div = document.createElement('div');
      div.className = 'comp-row';

      const maxVal = Math.max(row.val_a, row.val_b, 0.001);
      const fillA = Math.min(100, Math.round((row.val_a / maxVal) * 100));
      const fillB = Math.min(100, Math.round((row.val_b / maxVal) * 100));

      const isLeaderA = row.leader === 'a';
      const isLeaderB = row.leader === 'b';

      div.innerHTML = `
        <div class="comp-val-a ${isLeaderA ? 'leader' : ''}">${row.val_a}</div>
        <div class="comp-bar-container-a" title="${nameA}: ${row.val_a}">
          <div class="comp-fill-a" style="width: ${fillA}%;"></div>
        </div>
        <div class="comp-metric-name">${row.metric}</div>
        <div class="comp-bar-container-b" title="${nameB}: ${row.val_b}">
          <div class="comp-fill-b" style="width: ${fillB}%;"></div>
        </div>
        <div class="comp-val-b ${isLeaderB ? 'leader' : ''}">${row.val_b}</div>
      `;

      comparisonRowsContainer.appendChild(div);
    });
  }

  // --- SECONDARY FUNCTION BUTTONS ---

  // 1. Swap Corners Button
  function swapCorners() {
    const valA = fighterASelect.value;
    const valB = fighterBSelect.value;

    fighterASelect.value = valB;
    fighterBSelect.value = valA;
    appData.fighterA = valB;
    appData.fighterB = valA;

    updateFighterSnapshotStats('A', valB);
    updateFighterSnapshotStats('B', valA);

    showToast(`🔄 Corners swapped: Red: ${valB} | Blue: ${valA}`, false, 2000);

    // If results already visible, re-run prediction
    if (predictionSection.classList.contains('active')) {
      predictFight();
    }
  }

  // 2. Random Matchup Generator
  function randomMatchup() {
    const roster = appData.rosters[appData.activeWeightClass] || [];
    if (roster.length < 2) {
      showToast('Not enough fighters in this division for a random matchup.', true);
      return;
    }

    const idxA = Math.floor(Math.random() * roster.length);
    let idxB = Math.floor(Math.random() * roster.length);
    while (idxB === idxA) {
      idxB = Math.floor(Math.random() * roster.length);
    }

    fighterASelect.value = roster[idxA];
    fighterBSelect.value = roster[idxB];
    appData.fighterA = roster[idxA];
    appData.fighterB = roster[idxB];

    updateFighterSnapshotStats('A', roster[idxA]);
    updateFighterSnapshotStats('B', roster[idxB]);

    showToast(`🎲 Random matchup selected: ${roster[idxA]} vs ${roster[idxB]}`, false, 2500);

    predictFight();
  }

  // 3. Reset Button
  function resetMatchup() {
    const roster = appData.rosters[appData.activeWeightClass] || [];
    if (roster.length > 0) fighterASelect.value = roster[0];
    if (roster.length > 1) fighterBSelect.value = roster[1];

    fighterASearch.value = '';
    fighterBSearch.value = '';
    renderFighterOptions(fighterASelect, roster);
    renderFighterOptions(fighterBSelect, roster);

    predictionSection.classList.remove('active');
    showToast('🧹 Selections reset to default division fighters.', false, 2000);
  }

  // 4. Toggle Detailed Stats Accordion
  function toggleStats() {
    if (!predictionSection.classList.contains('active')) {
      predictFight();
    } else {
      statsTableCard.scrollIntoView({ behavior: 'smooth' });
    }
  }

  // --- FIGHTER SNAPSHOT STATS ---
  function updateFighterSnapshotStats(corner, fighterName) {
    // Quick indicator placeholder or live stats
    const reachEl = document.getElementById(`quickReach${corner}`);
    const recordEl = document.getElementById(`quickRecord${corner}`);
    const streakEl = document.getElementById(`quickStreak${corner}`);

    if (!fighterName) {
      reachEl.textContent = '-- cm';
      recordEl.textContent = '-- W / -- L';
      streakEl.textContent = '--';
      return;
    }

    reachEl.textContent = 'Active Fighter';
    recordEl.textContent = 'UFC Roster';
    streakEl.textContent = 'Division Ready';
  }

  // --- TOAST NOTIFICATIONS ---
  let toastTimer = null;
  function showToast(message, isError = false, duration = 3000) {
    clearTimeout(toastTimer);
    toast.textContent = message;
    toast.className = `toast-msg show ${isError ? 'error' : ''}`;
    toastTimer = setTimeout(() => {
      toast.classList.remove('show');
    }, duration);
  }

  // --- EVENT LISTENERS ---
  function setupEventListeners() {
    // Theme Toggle
    themeToggleBtn.addEventListener('click', toggleTheme);

    // Weight class change
    weightClassSelect.addEventListener('change', (e) => {
      setActiveWeightClass(e.target.value);
    });

    // Fighter search input filtering
    fighterASearch.addEventListener('input', () => {
      const roster = appData.rosters[appData.activeWeightClass] || [];
      renderFighterOptions(fighterASelect, roster, fighterASearch.value);
    });

    fighterBSearch.addEventListener('input', () => {
      const roster = appData.rosters[appData.activeWeightClass] || [];
      renderFighterOptions(fighterBSelect, roster, fighterBSearch.value);
    });

    // Fighter selection change
    fighterASelect.addEventListener('change', (e) => {
      appData.fighterA = e.target.value;
      updateFighterSnapshotStats('A', e.target.value);
    });

    fighterBSelect.addEventListener('change', (e) => {
      appData.fighterB = e.target.value;
      updateFighterSnapshotStats('B', e.target.value);
    });

    // Buttons
    predictBtn.addEventListener('click', predictFight);
    swapCornersBtn.addEventListener('click', swapCorners);
    randomMatchupBtn.addEventListener('click', randomMatchup);
    resetMatchupBtn.addEventListener('click', resetMatchup);
    toggleStatsBtn.addEventListener('click', toggleStats);
  }

  // Run on DOM ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

})();
