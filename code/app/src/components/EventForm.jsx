import React, { useState } from 'react';

const INDUSTRIES = [
  { value: 'tech',          label: 'Technology' },
  { value: 'entertainment', label: 'Entertainment' },
  { value: 'finance',       label: 'Finance' },
  { value: 'sports',        label: 'Sports' },
  { value: 'media',         label: 'Media & Marketing' },
  { value: 'general',       label: 'General / Other' },
];

const ALL_TAGS = [
  'developers', 'enterprise', 'consumer', 'investors', 'startups',
  'media', 'mobile', 'ai', 'cloud', 'gaming', 'music', 'film',
  'sports', 'marketing', 'retail', 'india',
];

export default function EventForm({ onAnalyze, loading }) {
  const today = new Date().toISOString().split('T')[0];
  const [name, setName]         = useState('');
  const [date, setDate]         = useState('');
  const [industry, setIndustry] = useState('tech');
  const [tags, setTags]         = useState([]);

  const toggleTag = (t) =>
    setTags((prev) => prev.includes(t) ? prev.filter(x => x !== t) : [...prev, t]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!name.trim() || !date) return;
    onAnalyze({ name: name.trim(), proposed_date: date, industry, audience_tags: tags });
  };

  return (
    <div className="clean-card" style={{ padding: 24 }}>
      <div style={{ marginBottom: 24 }}>
        <h2 style={{ fontSize: 16, fontWeight: 600, color: 'var(--primary)', marginBottom: 4 }}>Launch Details</h2>
        <p style={{ fontSize: 13, color: 'var(--text-secondary)' }}>
          Configure your event to calculate collision risk.
        </p>
      </div>

      <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
        
        {/* Event Name */}
        <div>
          <label className="form-label" htmlFor="event-name">Event Name</label>
          <input
            id="event-name"
            className="form-input"
            type="text"
            placeholder="e.g. Q3 Product Release"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
          />
        </div>

        {/* Proposed Date */}
        <div>
          <label className="form-label" htmlFor="proposed-date">Proposed Date</label>
          <input
            id="proposed-date"
            className="form-input"
            type="date"
            value={date}
            min={today}
            onChange={(e) => setDate(e.target.value)}
            required
          />
        </div>

        {/* Industry */}
        <div>
          <label className="form-label" htmlFor="industry-select">Primary Industry</label>
          <select
            id="industry-select"
            className="form-select"
            value={industry}
            onChange={(e) => setIndustry(e.target.value)}
          >
            {INDUSTRIES.map(({ value, label }) => (
              <option key={value} value={value}>{label}</option>
            ))}
          </select>
        </div>

        {/* Audience Tags */}
        <div>
          <label className="form-label">Target Audience</label>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
            {ALL_TAGS.map((t) => (
              <button
                type="button"
                key={t}
                className={`tag ${tags.includes(t) ? 'tag-selected' : 'tag-default'}`}
                onClick={() => toggleTag(t)}
              >
                {t}
              </button>
            ))}
          </div>
          {tags.length === 0 && (
            <p style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 8 }}>
              Select tags to improve accuracy.
            </p>
          )}
        </div>

        <div className="divider" style={{ margin: '8px 0' }} />

        <button className="btn-primary" type="submit" disabled={loading || !name || !date}>
          {loading ? (
            <><div className="spinner" /> Analyzing...</>
          ) : (
            <>Analyze Risk</>
          )}
        </button>
      </form>
    </div>
  );
}
