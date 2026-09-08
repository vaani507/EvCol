import React, { useRef, useEffect } from 'react';

const INDUSTRY_COLORS = {
  tech:          '#3b82f6',
  entertainment: '#a855f7',
  finance:       '#10b981',
  sports:        '#f59e0b',
  media:         '#ef4444',
  general:       '#64748b',
};

export default function EventTimeline({ proposedDate, conflicts = [] }) {
  const containerRef = useRef(null);

  // Build timeline range: proposed date ± 14 days
  const proposed = new Date(proposedDate + 'T00:00:00');
  const days = [];
  for (let i = -14; i <= 14; i++) {
    const d = new Date(proposed);
    d.setDate(proposed.getDate() + i);
    days.push(d);
  }

  // Map conflict events to their offsets
  const conflictMap = {};
  for (const evt of conflicts) {
    const delta = evt.delta_days; // relative to proposed
    if (conflictMap[delta]) {
      conflictMap[delta].push(evt);
    } else {
      conflictMap[delta] = [evt];
    }
  }

  // Scroll to center on mount
  useEffect(() => {
    if (containerRef.current) {
      const el = containerRef.current;
      el.scrollLeft = el.scrollWidth / 2 - el.clientWidth / 2;
    }
  }, [proposedDate]);

  const dayWidth = 48;

  return (
    <div className="clean-card anim-fade-in" style={{ padding: 24 }}>
      <h3 style={{ fontSize: 16, fontWeight: 600, color: 'var(--primary)', marginBottom: 4 }}>14-Day Proximity Radar</h3>
      <p style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 24 }}>
        Distribution of competing events around your launch date.
      </p>

      <div
        ref={containerRef}
        style={{
          overflowX: 'auto', paddingBottom: 12,
          scrollbarWidth: 'thin', borderBottom: '1px solid var(--bg-subtle)'
        }}
      >
        <div style={{ display: 'flex', minWidth: `${days.length * dayWidth}px`, alignItems: 'flex-end', height: 80 }}>
          {days.map((day, idx) => {
            const offset = idx - 14;
            const isProposed = offset === 0;
            const events = conflictMap[offset] || [];
            const hasEvents = events.length > 0;
            const isWeekend = day.getDay() === 0 || day.getDay() === 6;

            return (
              <div
                key={idx}
                style={{
                  width: dayWidth,
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  position: 'relative',
                  height: '100%',
                  justifyContent: 'flex-end'
                }}
                title={hasEvents ? events.map(e => e.name).join(', ') : day.toDateString()}
              >
                {/* Event dots */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: 2, marginBottom: 8, alignItems: 'center' }}>
                  {events.slice(0, 3).map((evt, ei) => (
                    <div
                      key={ei}
                      style={{
                        width: 8, height: 8,
                        borderRadius: '50%',
                        backgroundColor: INDUSTRY_COLORS[evt.industry] || '#64748b',
                      }}
                    />
                  ))}
                  {events.length > 3 && (
                    <div style={{ fontSize: 10, color: 'var(--text-muted)', lineHeight: 1 }}>+{events.length - 3}</div>
                  )}
                </div>

                {/* Day label */}
                <div style={{
                  fontSize: 11,
                  fontWeight: isProposed ? 600 : 400,
                  color: isProposed ? 'var(--primary)' : isWeekend ? 'var(--text-muted)' : 'var(--text-secondary)',
                  textAlign: 'center',
                  paddingTop: 8,
                  borderTop: isProposed ? '2px solid var(--primary)' : '2px solid transparent',
                  width: '100%'
                }}>
                  {day.getDate()}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Legend */}
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 16, marginTop: 16 }}>
        {Object.entries(INDUSTRY_COLORS).map(([ind, col]) => {
          const hasAny = conflicts.some(e => e.industry === ind);
          if (!hasAny) return null;
          return (
            <div key={ind} style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12, color: 'var(--text-secondary)' }}>
              <div style={{ width: 8, height: 8, borderRadius: '50%', backgroundColor: col }} />
              <span style={{ textTransform: 'capitalize' }}>{ind}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
