import React, { useState } from 'react';
import './index.css';
import EventForm from './components/EventForm';
import RiskDashboard from './components/RiskDashboard';
import EventTimeline from './components/EventTimeline';
import RecommendationCard from './components/RecommendationCard';

const API = 'http://localhost:8000';

export default function App() {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError]   = useState(null);

  const handleAnalyze = async (formData) => {
    setLoading(true);
    setError(null);
    // Removed setResult(null) to prevent layout shift!
    try {
      const res = await fetch(`${API}/api/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
      });
      if (!res.ok) throw new Error(`Server error: ${res.status}`);
      const data = await res.json();
      setResult(data);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <div className="dotted-bg" />

      {/* ── Header ─────────────────────────────────────────────────────── */}
      <header style={{
        position: 'relative', zIndex: 10,
        backgroundColor: 'var(--bg-surface)',
        borderBottom: '1px solid var(--border)',
        padding: '0 32px',
      }}>
        <div style={{ maxWidth: 1200, margin: '0 auto', display: 'flex', alignItems: 'center', justifyContent: 'space-between', height: 60 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <div style={{
              width: 28, height: 28, borderRadius: 6,
              backgroundColor: 'var(--primary)', color: '#fff',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontWeight: 700, fontSize: 14, letterSpacing: '-1px'
            }}>EC</div>
            <div>
              <div style={{ fontWeight: 600, fontSize: 15, color: 'var(--primary)' }}>
                EventCollision
              </div>
            </div>
          </div>
          <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
            <span style={{ fontSize: 13, color: 'var(--text-secondary)' }}>Predictive Launch Intelligence</span>
          </div>
        </div>
      </header>

      {/* ── Main ───────────────────────────────────────────────────────── */}
      <main style={{ position: 'relative', zIndex: 1, maxWidth: 1000, margin: '0 auto', padding: '48px 24px 80px' }}>

        {/* Hero */}
        <div className="anim-fade-in" style={{ textAlign: 'center', marginBottom: 48 }}>
          <h1 style={{ fontSize: '32px', fontWeight: 700, color: 'var(--primary)', marginBottom: 12, letterSpacing: '-0.02em' }}>
            Schedule your launch with confidence
          </h1>
          <p style={{ fontSize: 16, color: 'var(--text-secondary)', maxWidth: 600, margin: '0 auto' }}>
            Identify potential conflicts with competitor launches, industry conferences, and major public events before you commit to a date.
          </p>
        </div>

        {/* Two-column layout */}
        <div style={{ display: 'grid', gridTemplateColumns: 'minmax(320px, 380px) 1fr', gap: 32, alignItems: 'start' }}>

          {/* Left: Form */}
          <div className="anim-fade-in">
            <EventForm onAnalyze={handleAnalyze} loading={loading} />
          </div>

          {/* Right: Results */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 24, minHeight: '600px' }}>
            {error && (
              <div className="clean-card anim-fade-in" style={{ padding: 24, borderColor: 'var(--red-border)', background: 'var(--red-bg)' }}>
                <div style={{ fontWeight: 600, color: 'var(--red)', marginBottom: 8, fontSize: 14 }}>Connection Error</div>
                <div style={{ fontSize: 14, color: 'var(--red)' }}>{error}</div>
              </div>
            )}

            {result ? (
              <div style={{ 
                display: 'flex', flexDirection: 'column', gap: 24,
                opacity: loading ? 0.6 : 1, transition: 'opacity 0.2s ease',
                pointerEvents: loading ? 'none' : 'auto'
              }}>
                <RiskDashboard result={result} />
                <EventTimeline
                  proposedDate={result.proposed_date}
                  conflicts={result.conflicting_events}
                />
                <RecommendationCard
                  recommendations={result.recommendations}
                  originalScore={result.score}
                />
              </div>
            ) : !error && (
              <div className="clean-card" style={{ padding: 48, textAlign: 'center', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%' }}>
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="var(--border-strong)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" style={{ marginBottom: 16 }}>
                  <rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect>
                  <line x1="16" y1="2" x2="16" y2="6"></line>
                  <line x1="8" y1="2" x2="8" y2="6"></line>
                  <line x1="3" y1="10" x2="21" y2="10"></line>
                </svg>
                <div style={{ fontWeight: 500, fontSize: 15, color: 'var(--primary)', marginBottom: 8 }}>
                  No analysis yet
                </div>
                <div style={{ fontSize: 14, color: 'var(--text-secondary)', maxWidth: 250 }}>
                  Enter your proposed launch details on the left to generate a risk report.
                </div>
              </div>
            )}
          </div>
        </div>
      </main>
    </>
  );
}
