/* =========================================================
   EVCOL — app.js
   Connects the SPA frontend to the FastAPI backend at :8000
   ========================================================= */

const API = 'http://localhost:8000';

// ---- NAVIGATION ----
const PAGES = ['home','dashboard','analyze','results','radar','calendar','history'];
let currentPage = 'home';

function navigate(page) {
  PAGES.forEach(p => {
    const el = document.getElementById('page-' + p);
    if (el) el.classList.remove('active');
    const nav = document.getElementById('nav-' + p);
    if (nav) nav.classList.remove('active');
  });

  const target = document.getElementById('page-' + page);
  if (target) { target.classList.add('active'); window.scrollTo({ top: 0, behavior: 'smooth' }); }
  const navLink = document.getElementById('nav-' + page);
  if (navLink) navLink.classList.add('active');

  const navLinks = document.getElementById('navLinks');
  if (navLinks) navLinks.classList.remove('open');

  currentPage = page;

  if (page === 'dashboard') { initCalendar(); loadDashboard(); }
  if (page === 'calendar') initFullCalendar();
  if (page === 'radar') loadRadar();
  if (page === 'history') loadHistory();
}

function toggleMenu() {
  document.getElementById('navLinks').classList.toggle('open');
}

window.addEventListener('scroll', () => {
  const nb = document.getElementById('navbar');
  if (nb) nb.classList.toggle('scrolled', window.scrollY > 20);
});

// ---- HELPERS ----
function showToast(msg, type = 'info') {
  const t = document.getElementById('toast');
  if (!t) return;
  t.textContent = msg;
  t.className = 'toast' + (type === 'error' ? ' toast-error' : '');
  clearTimeout(window._toastTimer);
  window._toastTimer = setTimeout(() => t.classList.add('hidden'), 4000);
}

function riskColor(level) {
  if (!level) return '#8a9e80';
  const l = level.toLowerCase();
  if (l === 'high')   return '#e05050';
  if (l === 'medium') return '#d4a820';
  return '#7aad6a';
}

function fmt(dateStr) {
  if (!dateStr) return '';
  const d = new Date(dateStr + 'T00:00:00');
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
}

// ---- ANALYSIS FLOW ----
const loadingMessages = [
  'Scanning 1,200+ global events...',
  'Calculating temporal proximity...',
  'Measuring audience overlap...',
  'Computing media friction index...',
  'Generating smart alternatives...',
  'Finalizing collision report...'
];

async function runAnalysis() {
  const name     = (document.getElementById('launchName').value || '').trim();
  const date     = (document.getElementById('launchDate').value || '').trim();
  const industry = (document.getElementById('launchIndustry').value || 'general').trim();

  if (!name) { showToast('Please enter a launch name.', 'error'); return; }
  if (!date) { showToast('Please select a proposed launch date.', 'error'); return; }

  // Collect audience tags from checkboxes
  const tags = [];
  document.querySelectorAll('.audience-cb:checked').forEach(cb => tags.push(cb.value));

  const overlay  = document.getElementById('loadingOverlay');
  const progress = document.getElementById('loadingProgress');
  const bar      = document.getElementById('loadingBar');

  overlay.classList.remove('hidden');
  bar.style.width = '0%';

  // Animate loading messages while fetch runs
  let step = 0;
  const msgInterval = setInterval(() => {
    if (step < loadingMessages.length) {
      progress.textContent = loadingMessages[step];
      bar.style.width = `${Math.round(((step + 1) / loadingMessages.length) * 100)}%`;
      step++;
    }
  }, 500);

  try {
    const res = await fetch(`${API}/api/analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, proposed_date: date, industry, audience_tags: tags })
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Server error ${res.status}`);
    }

    const data = await res.json();
    clearInterval(msgInterval);
    bar.style.width = '100%';

    setTimeout(() => {
      overlay.classList.add('hidden');
      renderResults(data);
      navigate('results');
    }, 400);

  } catch (e) {
    clearInterval(msgInterval);
    overlay.classList.add('hidden');
    showToast('Analysis failed: ' + e.message, 'error');
  }
}

// ---- RENDER RESULTS (dynamic from API) ----
let lastResult = null;

function renderResults(data) {
  lastResult = data;
  const level = (data.risk_level || 'Low');
  const score = Math.round(data.score || 0);
  const color = riskColor(level);

  // Score gauge
  const scoreNum  = document.getElementById('resultScore');
  const scoreLbl  = document.getElementById('resultLevel');
  const scoreSub  = document.getElementById('resultDate');
  const scoreArc  = document.getElementById('scoreArc');
  const scoreBox  = document.getElementById('scoreRec');
  const scoreDesc = document.getElementById('scoreDesc');

  if (scoreNum)  scoreNum.textContent  = score;
  if (scoreLbl)  { scoreLbl.textContent = level.toUpperCase(); scoreLbl.style.color = color; }
  if (scoreNum)  scoreNum.style.color   = color;
  if (scoreSub)  scoreSub.textContent   = fmt(data.proposed_date);
  if (scoreArc)  {
    const circ = 2 * Math.PI * 50; // r=50, so circumference ~314
    const offset = circ - (score / 100) * circ;
    scoreArc.style.stroke = color;
    scoreArc.style.strokeDashoffset = offset;
  }
  if (scoreDesc) {
    scoreDesc.textContent = score >= 65
      ? `High collision risk detected. ${data.conflicting_events.length} competing events found nearby.`
      : score >= 30
      ? `Moderate risk. ${data.conflicting_events.length} events could reduce your visibility.`
      : `Low risk. Great timing — only ${data.conflicting_events.length} minor conflicts detected.`;
  }
  if (scoreBox) {
    scoreBox.textContent = data.recommendations.length
      ? `AI recommends: ${fmt(data.recommendations[0].date)} (score: ${data.recommendations[0].score})`
      : 'No better alternatives found in ±30 days.';
  }

  // Factor bars — compute from score breakdown
  renderFactorBars(data);

  // Conflicting events
  renderConflicts(data.conflicting_events || []);

  // Alternative dates
  renderAlternatives(data.recommendations || [], data.proposed_date);

  // Update page header
  const hTitle = document.getElementById('resultsTitle');
  const hSub   = document.getElementById('resultsMeta');
  if (hTitle) hTitle.textContent = `Risk Report: ${data.event_name}`;
  if (hSub)   hSub.innerHTML = `
    <span class="meta-tag">${fmt(data.proposed_date)}</span>
    <span class="meta-sep">·</span>
    <span class="meta-tag">${data.industry}</span>
    <span class="meta-sep">·</span>
    <span class="meta-tag">Report #${data.report_id}</span>`;
}

function renderFactorBars(data) {
  const score = data.score || 0;
  const events = data.conflicting_events || [];

  // Estimate factors from real data
  const maxContrib = events.length ? events[0].contribution : 0;
  const temporal  = Math.min(100, Math.round(score * 0.9));
  const audience  = Math.min(100, Math.round(score * 0.7 + (events.length * 2)));
  const media     = Math.min(100, Math.round(score * 0.5 + maxContrib));
  const industry  = Math.min(100, Math.round(score * 0.6));
  const magnitude = Math.min(100, Math.round(events.reduce((s, e) => s + e.magnitude, 0) / Math.max(events.length, 1) * 20));

  const bars = [
    { id: 'barTemporal',  val: temporal,  score: temporal,  color: '#e05050' },
    { id: 'barAudience',  val: audience,  score: audience,  color: '#d4a820' },
    { id: 'barMedia',     val: media,     score: media,     color: '#e8541a' },
    { id: 'barIndustry',  val: industry,  score: industry,  color: '#d4a820' },
    { id: 'barMagnitude', val: magnitude, score: magnitude, color: '#e05050' },
  ];

  bars.forEach(b => {
    const fill = document.getElementById(b.id);
    const num  = document.getElementById(b.id + 'Num');
    if (fill) { fill.style.width = b.val + '%'; fill.style.background = b.color; }
    if (num)  num.textContent = b.score;
  });
}

function renderConflicts(events) {
  const container = document.getElementById('conflictsList');
  if (!container) return;

  if (!events.length) {
    container.innerHTML = '<p style="color:var(--text2);font-size:14px;">No major conflicting events detected nearby.</p>';
    return;
  }

  container.innerHTML = events.map(evt => {
    const col = evt.magnitude >= 5 ? 'tech' : evt.magnitude >= 4 ? 'blue-icon' : 'purple-icon';
    const badge = evt.magnitude >= 5 ? 'high-badge' : evt.magnitude >= 4 ? 'medium-badge' : 'low-badge';
    const dayLabel = evt.delta_days === 0 ? 'Same day' :
                     Math.abs(evt.delta_days) === 1 ? `${Math.abs(evt.delta_days)} day ${evt.delta_days > 0 ? 'after' : 'before'}` :
                     `${Math.abs(evt.delta_days)} days ${evt.delta_days > 0 ? 'after' : 'before'}`;
    return `
      <div class="conflict-event-card">
        <div class="ce-header">
          <div class="ce-icon ${col}">${evt.industry[0].toUpperCase()}</div>
          <div class="ce-title-block">
            <div class="ce-name">${evt.name}</div>
            <div class="ce-date">${fmt(evt.date)} · ${dayLabel}</div>
          </div>
          <span class="risk-badge ${badge}">${evt.magnitude >= 5 ? 'HIGH' : evt.magnitude >= 4 ? 'MED' : 'LOW'}</span>
        </div>
        <div class="ce-details">
          <span class="ce-detail">📊 Magnitude: ${evt.magnitude}/5</span>
          <span class="ce-detail-tag ${evt.contribution > 10 ? 'audience-tag' : ''}">${evt.industry}</span>
          <span class="ce-detail">Collision score: ${evt.contribution}</span>
        </div>
      </div>`;
  }).join('');
}

function renderAlternatives(recs, currentDate) {
  const container = document.getElementById('altDatesList');
  if (!container) return;

  if (!recs.length) {
    container.innerHTML = '<p style="color:var(--text2);font-size:14px;">No better alternatives found in the search window.</p>';
    return;
  }

  container.innerHTML = recs.map((r, i) => {
    const isTop = i === 0;
    const level = r.score >= 65 ? 'High' : r.score >= 30 ? 'Medium' : 'Low';
    const color = riskColor(level);
    return `
      <div class="alt-date-card ${isTop ? 'recommended' : ''}">
        ${isTop ? '<div class="recommended-badge">⭐ TOP RECOMMENDATION</div>' : ''}
        <div class="alt-date-header">${fmt(r.date)}</div>
        <div class="alt-score-row">
          <span class="risk-badge" style="background:${color}20;color:${color};border:1px solid ${color}40">${level}</span>
          <span class="alt-score" style="color:${color}">${r.score}/100</span>
        </div>
        <div class="alt-bullets">
          <span>✓ ${r.score < 20 ? 'Very clear' : r.score < 40 ? 'Clear' : 'Moderate'} launch window</span>
          <span>✓ ${Math.round(100 - r.score)}% less competitive pressure</span>
        </div>
        <button class="btn-alt-select" onclick="selectDate('${r.date}')">Select This Date</button>
      </div>`;
  }).join('');
}

// ---- LOAD DASHBOARD ----
async function loadDashboard() {
  try {
    const [eventsRes] = await Promise.all([
      fetch(`${API}/api/events`)
    ]);
    const events = await eventsRes.json();

    // Update tracked count
    const trackedEl = document.getElementById('eventsTracked');
    if (trackedEl) animateNumber(trackedEl, events.length, 1000);

    // Load recent reports from localStorage
    const history = getHistory();
    const recentEl = document.getElementById('recentAnalysesList');
    if (recentEl && history.length) {
      recentEl.innerHTML = history.slice(0, 4).map(r => `
        <div class="recent-item" onclick="navigate('results')">
          <div class="recent-icon ${r.risk_level.toLowerCase()}">
            ${r.risk_level === 'High' ? '⚠' : r.risk_level === 'Medium' ? '~' : '✓'}
          </div>
          <div class="recent-info">
            <div class="recent-name">${r.event_name}</div>
            <div class="recent-date">${fmt(r.proposed_date)} · ${r.industry}</div>
          </div>
          <div class="recent-score-wrap">
            <span class="risk-badge ${r.risk_level.toLowerCase()}-badge">${r.risk_level}</span>
            <span class="recent-score">${Math.round(r.score)}/100</span>
          </div>
        </div>`).join('');
    }
  } catch(e) {
    // Dashboard works in offline mode too — just skip dynamic numbers
  }
}

// ---- LOAD RADAR ----
async function loadRadar() {
  const container = document.getElementById('radarEventsList');
  if (!container) return;

  try {
    const res = await fetch(`${API}/api/events`);
    const events = await res.json();

    // Show upcoming events (next 90 days)
    const now = new Date();
    const cutoff = new Date(now); cutoff.setDate(cutoff.getDate() + 90);

    const upcoming = events
      .filter(e => { const d = new Date(e.date); return d >= now && d <= cutoff; })
      .sort((a,b) => a.date.localeCompare(b.date))
      .slice(0, 12);

    if (!upcoming.length) {
      container.innerHTML = '<p style="color:var(--text2);padding:20px;">No events found in the next 90 days.</p>';
      return;
    }

    container.innerHTML = upcoming.map(evt => {
      const tagClass = evt.industry === 'tech' ? 'tech-tag' :
                       evt.industry === 'entertainment' ? 'entertainment-tag' :
                       evt.industry === 'finance' ? 'finance-tag' :
                       evt.industry === 'sports' ? 'sports-tag' : 'tech-tag';
      const mag = evt.magnitude;
      const overlapClass = mag >= 5 ? 'high-overlap' : mag >= 4 ? 'medium-overlap' : 'low-overlap';
      const overlapText  = mag >= 5 ? '🔴 High Overlap' : mag >= 4 ? '🟡 Med Overlap' : '🟢 Low Overlap';
      return `
        <div class="radar-event-card">
          <div class="radar-event-header">
            <span class="radar-industry-tag ${tagClass}">${evt.industry}</span>
            <span class="radar-overlap ${overlapClass}">${overlapText}</span>
          </div>
          <h4>${evt.name}</h4>
          <div class="radar-event-meta">
            <span>📅 ${fmt(evt.date)}</span>
            <span>⚡ Magnitude ${evt.magnitude}/5</span>
          </div>
          <button class="btn-alt-select" onclick="prefillDate('${evt.date}')">Analyze vs This</button>
        </div>`;
    }).join('');

  } catch(e) {
    container.innerHTML = '<p style="color:var(--text2);padding:20px;">Could not load radar events.</p>';
  }
}

// ---- HISTORY ----
function getHistory() {
  try { return JSON.parse(localStorage.getItem('evcol_history') || '[]'); }
  catch(e) { return []; }
}

function saveToHistory(data) {
  const h = getHistory();
  h.unshift(data);
  localStorage.setItem('evcol_history', JSON.stringify(h.slice(0, 20)));
}

function loadHistory() {
  const tbody = document.getElementById('historyTableBody');
  if (!tbody) return;

  const history = getHistory();
  if (!history.length) {
    tbody.innerHTML = '<tr><td colspan="7" style="text-align:center;color:var(--text2);padding:32px">No analyses yet. <a class="link-btn" onclick="navigate(\'analyze\')">Run your first analysis →</a></td></tr>';
    return;
  }

  tbody.innerHTML = history.map((r, i) => {
    const level = r.risk_level || 'Low';
    const color = riskColor(level);
    const badgeCls = level.toLowerCase() + '-badge';
    return `
      <tr>
        <td><div class="launch-name-cell"><span class="ln-dot" style="background:${color}"></span>${r.event_name}</div></td>
        <td>${fmt(r.proposed_date)}</td>
        <td><span class="industry-chip tech-chip">${r.industry}</span></td>
        <td>
          <div class="risk-cell">
            <span class="risk-badge ${badgeCls}">${level}</span>
            <span class="risk-num">${Math.round(r.score)}/100</span>
          </div>
        </td>
        <td>${r.conflicting_events ? r.conflicting_events.length : 0}</td>
        <td><span class="status-badge confirmed">Analyzed</span></td>
        <td>
          <div class="action-btns">
            <button class="action-btn view" onclick="reloadResult(${i})">View</button>
            <button class="action-btn reschedule" onclick="prefillDate('${r.proposed_date}')">Re-analyze</button>
            <button class="action-btn delete" onclick="deleteHistory(${i}, this)">Delete</button>
          </div>
        </td>
      </tr>`;
  }).join('');
}

function reloadResult(index) {
  const h = getHistory();
  if (h[index]) { renderResults(h[index]); navigate('results'); }
}

function deleteHistory(index, btn) {
  const h = getHistory();
  h.splice(index, 1);
  localStorage.setItem('evcol_history', JSON.stringify(h));
  btn.closest('tr').style.opacity = '0';
  btn.closest('tr').style.transition = 'opacity 0.3s';
  setTimeout(() => loadHistory(), 300);
}

// ---- HELPERS ----
function prefillDate(dateStr) {
  navigate('analyze');
  setTimeout(() => {
    const d = document.getElementById('launchDate');
    if (d) d.value = dateStr;
  }, 150);
}

function selectDate(dateStr) {
  showToast(`✅ Launch date set to ${fmt(dateStr)}`);
  prefillDate(dateStr);
}

// ---- CALENDAR ----
let calYear = 2026, calMonth = 9;

function initCalendar() { renderMiniCalendar(); }

function renderMiniCalendar() {
  const grid = document.getElementById('calendarGrid');
  const label = document.getElementById('calMonthLabel');
  if (!grid || !label) return;

  const months = ['January','February','March','April','May','June','July','August','September','October','November','December'];
  label.textContent = `${months[calMonth]} ${calYear}`;
  grid.innerHTML = '';

  ['Mon','Tue','Wed','Thu','Fri','Sat','Sun'].forEach(d => {
    const el = document.createElement('div');
    el.className = 'cal-day-header'; el.textContent = d; grid.appendChild(el);
  });

  const firstDay = new Date(calYear, calMonth, 1).getDay();
  const offset   = firstDay === 0 ? 6 : firstDay - 1;
  const days     = new Date(calYear, calMonth + 1, 0).getDate();

  for (let i = 0; i < offset; i++) {
    const el = document.createElement('div'); el.className = 'cal-day empty'; grid.appendChild(el);
  }

  // Color-code from history
  const history = getHistory();
  const launchDates = new Set(history.map(r => r.proposed_date));

  for (let d = 1; d <= days; d++) {
    const el = document.createElement('div');
    const dateStr = `${calYear}-${String(calMonth+1).padStart(2,'0')}-${String(d).padStart(2,'0')}`;
    const hit = history.find(r => r.proposed_date === dateStr);
    let cls = 'cal-day';
    if (hit) {
      const l = hit.risk_level.toLowerCase();
      cls += l === 'high' ? ' risk-high your-launch' : l === 'medium' ? ' risk-medium your-launch' : ' risk-low your-launch';
    }
    el.className = cls; el.textContent = d;
    el.onclick = () => { if (hit) { renderResults(hit); navigate('results'); } };
    grid.appendChild(el);
  }
}

function prevMonth() { if (calMonth === 0) { calMonth = 11; calYear--; } else calMonth--; renderMiniCalendar(); }
function nextMonth() { if (calMonth === 11) { calMonth = 0; calYear++; } else calMonth++; renderMiniCalendar(); }

// ---- FULL CALENDAR ----
let fcYear = 2026, fcMonth = 9;
function initFullCalendar() { renderFullCalendar(); }

function renderFullCalendar() {
  const days  = document.getElementById('fullCalDays');
  const label = document.getElementById('fullCalLabel');
  if (!days || !label) return;

  const months = ['January','February','March','April','May','June','July','August','September','October','November','December'];
  label.textContent = `${months[fcMonth]} ${fcYear}`;
  days.innerHTML = '';

  const firstDay   = new Date(fcYear, fcMonth, 1).getDay();
  const totalDays  = new Date(fcYear, fcMonth + 1, 0).getDate();
  const history    = getHistory();

  for (let i = 0; i < firstDay; i++) {
    const el = document.createElement('div'); el.className = 'fcal-day fcal-empty'; days.appendChild(el);
  }

  for (let d = 1; d <= totalDays; d++) {
    const dateStr = `${fcYear}-${String(fcMonth+1).padStart(2,'0')}-${String(d).padStart(2,'0')}`;
    const hit = history.find(r => r.proposed_date === dateStr);
    const el  = document.createElement('div');
    let cls = 'fcal-day', tag = '', tagColor = '';
    if (hit) {
      const l = hit.risk_level.toLowerCase();
      cls += l === 'high' ? ' fcal-risk-high' : l === 'medium' ? ' fcal-risk-medium' : ' fcal-risk-low';
      tag = hit.risk_level; tagColor = riskColor(hit.risk_level);
    }
    el.className = cls;
    el.innerHTML = `<div class="fcal-day-num">${d}</div>${tag ? `<div class="fcal-day-tag" style="background:${tagColor}20;color:${tagColor}">${tag}</div>` : ''}`;
    el.onclick = () => { if (hit) { renderResults(hit); navigate('results'); } };
    days.appendChild(el);
  }
}

function prevMonthFull() { if (fcMonth === 0) { fcMonth = 11; fcYear--; } else fcMonth--; renderFullCalendar(); }
function nextMonthFull() { if (fcMonth === 11) { fcMonth = 0; fcYear++; } else fcMonth++; renderFullCalendar(); }

function syncCalendar(provider) { showToast(`✅ ${provider} Calendar sync coming in v2!`); }

// ---- RADAR FILTER ----
function filterRadar() { loadRadar(); }

// ---- ANIMATED NUMBERS ----
function animateNumber(el, target, duration = 1200) {
  const start = performance.now();
  const update = now => {
    const p = Math.min((now - start) / duration, 1);
    const e = 1 - Math.pow(1 - p, 3);
    el.textContent = Math.round(target * e).toLocaleString();
    if (p < 1) requestAnimationFrame(update);
  };
  requestAnimationFrame(update);
}

// ---- ADMIN ----
function showAddSource()   { showToast('Add Event Source — coming in v2'); }
function showAddIndustry() { showToast('Add Industry — coming in v2'); }

// ---- KEYBOARD ----
document.addEventListener('keydown', e => {
  if (e.key === 'Escape') {
    const o = document.getElementById('loadingOverlay');
    if (o && !o.classList.contains('hidden')) o.classList.add('hidden');
  }
});

// ---- INIT ----
document.addEventListener('DOMContentLoaded', () => {
  // Hero stat animation
  document.querySelectorAll('.stat-num').forEach(el => {
    const raw = parseInt(el.textContent.replace(/[^0-9]/g, ''));
    if (raw) { el.textContent = '0'; setTimeout(() => animateNumber(el, raw, 1500), 400); }
  });

  // Animate cards on scroll
  const obs = new IntersectionObserver(entries => {
    entries.forEach(e => {
      if (e.isIntersecting) { e.target.style.opacity = '1'; e.target.style.transform = 'translateY(0)'; obs.unobserve(e.target); }
    });
  }, { threshold: 0.1, rootMargin: '0px 0px -40px 0px' });

  document.querySelectorAll('.feature-card, .glass-card').forEach((el, i) => {
    el.style.opacity = '0';
    el.style.transform = 'translateY(18px)';
    el.style.transition = `opacity 0.5s ease ${i * 0.04}s, transform 0.5s ease ${i * 0.04}s`;
    obs.observe(el);
  });

  // Patch runAnalysis: after success, save to history
  const origRun = runAnalysis;
  window.runAnalysis = async function() {
    // Wrap fetch to intercept result and save history
    const name     = (document.getElementById('launchName').value || '').trim();
    const date     = (document.getElementById('launchDate').value || '').trim();
    const industry = (document.getElementById('launchIndustry').value || 'general').trim();
    if (!name || !date) { showToast(name ? 'Please select a launch date.' : 'Please enter a launch name.', 'error'); return; }
    const tags = [];
    document.querySelectorAll('.audience-cb:checked').forEach(cb => tags.push(cb.value));

    const overlay  = document.getElementById('loadingOverlay');
    const progress = document.getElementById('loadingProgress');
    const bar      = document.getElementById('loadingBar');
    overlay.classList.remove('hidden'); bar.style.width = '0%';

    let step = 0;
    const msgInterval = setInterval(() => {
      if (step < loadingMessages.length) {
        progress.textContent = loadingMessages[step];
        bar.style.width = `${Math.round(((step + 1) / loadingMessages.length) * 100)}%`;
        step++;
      }
    }, 500);

    try {
      const res = await fetch(`${API}/api/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, proposed_date: date, industry, audience_tags: tags })
      });
      if (!res.ok) { const err = await res.json().catch(() => ({})); throw new Error(err.detail || `Server error ${res.status}`); }
      const data = await res.json();
      clearInterval(msgInterval); bar.style.width = '100%';
      saveToHistory(data);
      setTimeout(() => { overlay.classList.add('hidden'); renderResults(data); navigate('results'); showToast(`✅ Analysis complete — ${data.risk_level} risk`); }, 400);
    } catch(e) {
      clearInterval(msgInterval); overlay.classList.add('hidden');
      showToast('Analysis failed: ' + e.message + '. Is the backend running on port 8000?', 'error');
    }
  };

  console.log('🚀 EvCol loaded — backend at', API);
});
