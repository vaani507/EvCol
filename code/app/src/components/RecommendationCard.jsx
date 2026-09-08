import React from 'react';

export default function RecommendationCard({ recommendations = [], originalScore }) {
  if (recommendations.length === 0) return null;

  return (
    <div className="clean-card anim-fade-in" style={{ padding: 24 }}>
      <div style={{ marginBottom: 20 }}>
        <h3 style={{ fontSize: 16, fontWeight: 600, color: 'var(--primary)', marginBottom: 4 }}>Alternative Launch Windows</h3>
        <p style={{ fontSize: 13, color: 'var(--text-secondary)' }}>
          Lower-risk dates within a ±30 day window.
        </p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 16 }}>
        {recommendations.map((rec, i) => {
          const delta = originalScore - rec.score;
          const isTop = i === 0;

          const formattedDate = new Date(rec.date + 'T00:00:00').toLocaleDateString('en-US', {
            weekday: 'short', month: 'short', day: 'numeric'
          });

          return (
            <div
              key={i}
              style={{
                background: isTop ? '#f8fafc' : 'var(--bg-surface)',
                border: isTop ? '1px solid var(--border-strong)' : '1px solid var(--border)',
                borderRadius: 'var(--radius)',
                padding: '16px',
                position: 'relative'
              }}
            >
              {isTop && (
                <div style={{ 
                  position: 'absolute', top: -10, left: 16, 
                  background: 'var(--primary)', color: '#fff', 
                  fontSize: 10, fontWeight: 600, padding: '2px 8px', 
                  borderRadius: 10, textTransform: 'uppercase', letterSpacing: '0.05em' 
                }}>
                  Top Pick
                </div>
              )}
              
              <div style={{ fontSize: 12, color: 'var(--text-secondary)', marginBottom: 4 }}>{rec.date.split('-')[0]}</div>
              <div style={{ fontSize: 16, fontWeight: 600, color: 'var(--primary)', marginBottom: 12 }}>
                {formattedDate}
              </div>
              
              <div style={{ display: 'flex', alignItems: 'flex-end', justifyContent: 'space-between', borderTop: '1px solid var(--bg-subtle)', paddingTop: 12 }}>
                <div>
                  <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 2 }}>Risk Score</div>
                  <div style={{ fontSize: 18, fontWeight: 700, color: 'var(--primary)', lineHeight: 1 }}>{Math.round(rec.score)}</div>
                </div>
                
                <div style={{ display: 'flex', alignItems: 'center', gap: 4, color: 'var(--green)', fontSize: 12, fontWeight: 500 }}>
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                    <line x1="12" y1="19" x2="12" y2="5"></line>
                    <polyline points="5 12 12 5 19 12"></polyline>
                  </svg>
                  {Math.round(delta)} pts
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
