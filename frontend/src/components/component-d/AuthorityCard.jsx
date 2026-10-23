export default function AuthorityCard({ authority, compact }) {
  if (compact) {
    return (
      <div className="cd-auth-compact">
        <div className="cd-auth-compact-name">{authority.name}</div>
        <div className="cd-auth-compact-meta">
          <span className={`cd-auth-compact-rel cd-rel-${authority.relationship?.toLowerCase()}`}>
            {authority.relationship}
          </span>
          <span className="cd-auth-compact-type">{authority.type}</span>
          <span className="cd-auth-compact-score">{authority.score}%</span>
        </div>
      </div>
    );
  }

  return (
    <div className="cd-auth-card">
      <div className="cd-auth-card-header">
        <div>
          <div className="cd-auth-name">{authority.name}</div>
          <div className="cd-auth-docid">{authority.doc_id}</div>
        </div>
        <div className="cd-auth-score-circle">
          <svg viewBox="0 0 36 36" className="cd-donut-svg">
            <circle cx="18" cy="18" r="15.9" fill="none" stroke="#e5e7eb" strokeWidth="3"/>
            <circle
              cx="18" cy="18" r="15.9" fill="none"
              stroke={authority.score >= 70 ? '#16a34a' : authority.score >= 50 ? '#d97706' : '#dc2626'}
              strokeWidth="3"
              strokeDasharray={`${authority.score} ${100 - authority.score}`}
              strokeDashoffset="25"
              strokeLinecap="round"
            />
          </svg>
          <span className="cd-donut-label">{authority.score}%</span>
        </div>
      </div>
      <div className="cd-auth-metrics">
        {Object.entries(authority.citation_metrics || {}).map(([k, v]) => (
          <span key={k} className="cd-metric-badge">
            {k.replace(/_/g, ' ')}: <strong>{v}</strong>
          </span>
        ))}
      </div>
      {authority.shap_reasoning && (
        <div className="cd-shap-box">
          <strong>AI Reasoning:</strong> {authority.shap_reasoning}
        </div>
      )}
    </div>
  );
}