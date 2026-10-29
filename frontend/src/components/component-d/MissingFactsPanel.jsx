export default function MissingFactsPanel({ facts, knownFacts, onMarkKnown }) {
  if (!facts || facts.length === 0) return null;

  return (
    <div className="cd-sidebar-card">
      <h4 className="cd-sidebar-title">Missing facts</h4>
      <p className="cd-sidebar-text">Ask the client for these. Marking one as known updates the tree.</p>
      <div className="cd-facts-list">
        {facts.map((fact, i) => {
          const isKnown = knownFacts.has(fact);
          return (
            <div key={i} className={`cd-fact-item${isKnown ? ' cd-fact-known' : ''}`}>
              <div className="cd-fact-text">
                {isKnown && <span className="cd-fact-check">✓</span>}
                <strong>{fact}</strong>
              </div>
              <button className="cd-fact-btn" onClick={() => onMarkKnown(fact)}>
                {isKnown ? 'Known' : 'Mark known'}
              </button>
            </div>
          );
        })}
      </div>
    </div>
  );
}