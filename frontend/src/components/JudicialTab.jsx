import { fmtDate } from '../utils/fmtDate.js';

const BADGE_CLS = {
  Followed:      'badge-followed',
  Distinguished: 'badge-distinguished',
  Overruled:     'badge-overruled',
  Doubted:       'badge-doubted',
};

const SCOPE_LABEL = {
  'ratio decidendi': 'Ratio Decidendi',
  'obiter dictum':   'Obiter Dictum',
  'full scope':      'Ratio Decidendi',
  'limited':         'Obiter Dictum',
};

function CitationCard({ c }) {
  const badgeCls  = BADGE_CLS[c.citation_type] ?? 'badge-followed';
  const scopeKey  = c.scope?.toLowerCase().trim();
  const scopeText = SCOPE_LABEL[scopeKey] ?? c.scope;
  const isRatio   = scopeText === 'Ratio Decidendi';
  const scopeCls  = isRatio ? 'scope-ratio' : 'scope-obiter';

  return (
    <div className="jt-card">
      <div className="jt-head">
        <span className={`jt-badge ${badgeCls}`}>{c.citation_type}</span>
        {c.scope && <span className={`jt-scope ${scopeCls}`}>{scopeText}</span>}
      </div>
      <div className="jt-case-id">{c.target_id}</div>
      <div className="jt-date">{fmtDate(c.effective_date)}</div>
      {c.evidence && <div className="jt-evidence">{c.evidence}</div>}
    </div>
  );
}

export default function JudicialTab({ citations }) {
  if (typeof citations === 'string') {
    return <p className="empty-msg">{citations}</p>;
  }
  if (!citations || citations.length === 0) {
    return <p className="empty-msg">No judicial treatment data available.</p>;
  }

  const subsequent = citations.filter((c) => c.direction === 'cited_by');
  const prior      = citations.filter((c) => c.direction !== 'cited_by');

  return (
    <div className="jt-list">
      {subsequent.length > 0 && (
        <>
          <div className="jt-section-label">
            Subsequent citations
            <span className="jt-section-count">{subsequent.length}</span>
          </div>
          {subsequent.map((c, i) => <CitationCard key={i} c={c} />)}
        </>
      )}
      {prior.length > 0 && (
        <>
          <div className="jt-section-label" style={{ marginTop: subsequent.length ? 14 : 0 }}>
            Prior authorities
            <span className="jt-section-count">{prior.length}</span>
          </div>
          {prior.map((c, i) => <CitationCard key={i} c={c} />)}
        </>
      )}
    </div>
  );
}