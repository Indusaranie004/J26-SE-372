function formatCaseId(id) {
  const match = id.match(/\d{4}-\d{2}-\d{2}-(.+)-(\d+)-(\d{4})/);
  if (!match) return id;
  const type = match[1].replace(/-/g, ' ');
  return `${type} ${match[2]}/${match[3]}`;
}

export default function ClusterList({ clusters, activeId, onSelect, loading }) {
  return (
    <div className="list-panel">
      <div className="list-header">
        Top Precedents
        <span className="list-count">{clusters.length}</span>
      </div>
      <div className="list-scroll">
        {loading && (
          <div className="loading-indicator">
            <span>Retrieving precedents…</span>
          </div>
        )}
        {!loading && clusters.length === 0 && (
          <p className="list-empty">Search to find precedents</p>
        )}
        {!loading && clusters.map((c, i) => {
          const pct = Math.round((c.rrf_score ?? 0) * 100);
          const isActive = c.case_id === activeId;
          return (
            <div
              key={c.case_id}
              className={`cluster-item${isActive ? ' active' : ''}`}
              role="button"
              tabIndex={0}
              onClick={() => onSelect(c.case_id)}
              onKeyDown={(e) => e.key === 'Enter' && onSelect(c.case_id)}
            >
              <div className="ci-head">
                <span className="ci-num">{i + 1}</span>
                <span className="ci-name">{formatCaseId(c.case_id)}</span>
              </div>
              <div className="ci-score-row">
                <div className="ci-bar">
                  <div className="ci-fill" style={{ width: `${pct}%` }} />
                </div>
                <span className="ci-score-val">{pct}%</span>
              </div>
              <div className="ci-relevance-label">Relevance</div>
            </div>
          );
        })}
      </div>
    </div>
  );
}