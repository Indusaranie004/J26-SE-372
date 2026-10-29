import { useState } from 'react';

const EXAMPLE_CHIPS = [
  { label: 'Wrongful termination', query: 'wrongful termination after employee complaint' },
  { label: 'Parate execution (real case)', query: 'parate execution of mortgage property Sri Lanka' },
  { label: 'FR petition time limit', query: 'fundamental rights petition time limit Article 126' },
];

export default function QueryInput({ onAnalyse, loading }) {
  const [query, setQuery] = useState('');

  const handleSubmit = () => {
    if (query.trim()) onAnalyse(query.trim());
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') handleSubmit();
  };

  return (
    <div className="cd-query-section">
      <div className="cd-search-row">
        <div className="cd-search-wrap">
          <svg className="cd-search-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
          </svg>
          <input
            className="cd-search-input"
            type="text"
            placeholder="Describe your legal issue..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
          />
        </div>
        <button className="cd-search-btn" onClick={handleSubmit} disabled={loading}>
          {loading ? 'Analysing…' : 'Analyse'}
        </button>
      </div>

      <div className="cd-chips-row">
        <span className="cd-chips-label">Try an example:</span>
        {EXAMPLE_CHIPS.map(chip => (
          <button
            key={chip.label}
            className="cd-chip"
            onClick={() => { setQuery(chip.query); onAnalyse(chip.query); }}
          >
            {chip.label}
          </button>
        ))}
      </div>
    </div>
  );
}