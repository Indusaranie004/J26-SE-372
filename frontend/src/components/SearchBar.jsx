import { useRef } from 'react';
import CHIPS from '../config/chips.js';

export default function SearchBar({ query, setQuery, onSearch, activeChipId, onChipSelect, loading }) {
  const inputRef = useRef(null);

  function handleChipClick(chip) {
    setQuery(chip.query);
    onChipSelect(chip);
  }

  function handleKeyDown(e) {
    if (e.key === 'Enter') onSearch();
  }

  return (
    <div className="searchbar">
      <h1 className="sb-heading">Find Legal Precedents</h1>
      <p className="sb-subheading">
        Describe your legal issue in natural language to find relevant precedents
      </p>

      <div className="sb-row">
        <div className="sb-wrap">
          <span className="sb-icon">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none"
              stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
            </svg>
          </span>
          <input
            ref={inputRef}
            className="sb-input"
            type="text"
            placeholder="Search Sri Lankan case law…"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
          />
        </div>
        <button className="sb-btn" onClick={onSearch} disabled={loading}>
          {loading ? 'Searching…' : 'Search'}
        </button>
      </div>

      <div className="sb-chips">
        <span className="sb-chips-label">Try:</span>
        {CHIPS.map((chip) => (
          <button
            key={chip.id}
            className={`sb-chip${activeChipId === chip.id ? ' selected' : ''}`}
            onClick={() => handleChipClick(chip)}
          >
            {chip.label}
          </button>
        ))}
      </div>
    </div>
  );
}
