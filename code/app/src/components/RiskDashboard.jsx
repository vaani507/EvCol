import React from 'react';

const RISK_CONFIG = {
  High:   { color: 'var(--red)',   bg: 'var(--red-bg)',   border: 'var(--red-border)',   label: 'High Risk',   desc: 'Major competing events detected. High likelihood of audience dilution.' },
  Medium: { color: '#d97706',      bg: 'var(--amber-bg)', border: 'var(--amber-border)', label: 'Medium Risk', desc: 'Some competing events present. Proceed with awareness.' },
  Low:    { color: '#059669',      bg: 'var(--green-bg)', border: 'var(--green-border)', label: 'Low Risk',    desc: 'Minimal competing events detected. Optimal launch window.' },
};

function ScoreRing({ score, riskLevel }) {
  const config = RISK_CONFIG[riskLevel] || RISK_CONFIG.Low;
  const size = 120;
  const strokeWidth = 10;
  const center = size / 2;
  const radius = center - strokeWidth;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - ((score / 100) * circumference);

  return (
    <div style={{ position: 'relative', width: size, height: size }}>
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
        <circle
          cx={center} cy={center} r={radius}
          fill="none" stroke="var(--bg-subtle)" strokeWidth={strokeWidth}
        />
        <circle
          cx={center} cy={center} r={radius}
          fill="none" stroke={config.color} strokeWidth={strokeWidth}
          strokeDasharray={circumference} strokeDashoffset={offset}
          strokeLinecap="round"
          style={{ transform: 'rotate(-90deg)', transformOrigin: 'center', transition: 'stroke-dashoffset 1s ease-out' }}
        />
      </svg>
      <div style={{
        position: 'absolute', top: 0, left: 0, right: 0, bottom: 0,
        display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center'
      }}>
        <span style={{ fontSize: 32, fontWeight: 700, color: 'var(--primary)', lineHeight: 1 }}>
          {Math.round(score)}
        </span>
        <span style={{ fontSize: 11, color: 'var(--text-muted)', fontWeight: 500 }}>/ 100</span>
      </div>
    </div>
  );
}

export default function RiskDashboard({ result }) {
  const { risk_level, score, event_name, proposed_date, conflicting_events = [] } = result;
  const config = RISK_CONFIG[risk_level] || RISK_CONFIG.Low;

  const formattedDate = new Date(proposed_date + 'T00:00:00').toLocaleDateString('en-US', {
    weekday: 'long', year: 'numeric', month: 'long', day: 'numeric',
  });

  return (
    <div className="clean-card anim-fade-in" style={{ padding: 24 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 24 }}>
        <div>
          <h3 style={{ fontSize: 18, fontWeight: 600, color: 'var(--primary)', marginBottom: 4 }}>{event_name}</h3>
          <div style={{ fontSize: 14, color: 'var(--text-secondary)' }}>{formattedDate}</div>
        </div>
        <div className={`risk-badge risk-${risk_level.toLowerCase()}`}>
          {risk_level} Risk
        </div>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '16px 0' }}>
        <ScoreRing score={score} riskLevel={risk_level} />
        <p style={{ textAlign: 'center', fontSize: 14, color: 'var(--text-secondary)', marginTop: 20, maxWidth: 300 }}>
          {config.desc}
        </p>
      </div>

      <div className="divider" />

      <div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
          <h4 style={{ fontSize: 14, fontWeight: 600, color: 'var(--primary)' }}>Conflict Analysis</h4>
          <span style={{ fontSize: 13, color: 'var(--text-muted)' }}>
            {conflicting_events.length} event{conflicting_events.length !== 1 ? 's' : ''} found
          </span>
        </div>
        
        {conflicting_events.length === 0 ? (
          <div style={{ padding: 16, background: 'var(--bg-subtle)', borderRadius: 'var(--radius)', fontSize: 13, color: 'var(--text-secondary)', textAlign: 'center' }}>
            No significant events detected in the ±14-day window.
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {conflicting_events.map((evt, i) => (
              <ConflictRow key={i} evt={evt} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function ConflictRow({ evt }) {
  const delta = evt.delta_days;
  const sign  = delta > 0 ? `+${delta}d` : delta < 0 ? `${delta}d` : 'Same day';
  
  // Format the date properly
  const evtDate = new Date(evt.date + 'T00:00:00').toLocaleDateString('en-US', { month: 'short', day: 'numeric' });

  return (
    <div style={{
      display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      padding: '12px', borderBottom: '1px solid var(--bg-subtle)',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, flex: 1, minWidth: 0 }}>
        <div style={{ 
          width: 48, fontSize: 12, fontWeight: 500, color: 'var(--text-secondary)', 
          textAlign: 'center', background: 'var(--bg-subtle)', padding: '4px 0', borderRadius: 4
        }}>
          {sign}
        </div>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ fontWeight: 500, fontSize: 14, color: 'var(--primary)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
            {evt.name}
          </div>
          <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>{evtDate}</div>
        </div>
      </div>
      <div style={{ display: 'flex', gap: 12, alignItems: 'center', flexShrink: 0 }}>
        <span className="industry-chip">{evt.industry}</span>
        <div style={{ display: 'flex', gap: 2 }}>
          {[1, 2, 3, 4, 5].map(star => (
            <svg key={star} width="12" height="12" viewBox="0 0 24 24" fill={star <= evt.magnitude ? "var(--text-muted)" : "none"} stroke={star <= evt.magnitude ? "var(--text-muted)" : "var(--border-strong)"} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon>
            </svg>
          ))}
        </div>
      </div>
    </div>
  );
}
