import { useState } from 'react';
import LitigationTab  from './LitigationTab.jsx';
import JudicialTab    from './JudicialTab.jsx';
import LegislationTab from './LegislationTab.jsx';

const TABS = [
  { id: 'litigation',  label: 'Litigation History' },
  { id: 'judicial',   label: 'Judicial Treatment' },
  { id: 'legislation',label: 'Legislation'         },
];

const TAB_LABELS = {
  litigation:  'Appeal Chain',
  judicial:    'Citation Network',
  legislation: 'Acts & Sections',
};

function formatCaseId(id) {
  const match = id.match(/\d{4}-\d{2}-\d{2}-(.+)-(\d+)-(\d{4})/);
  if (!match) return id;
  const type = match[1].replace(/-/g, ' ');
  return `${type} ${match[2]}/${match[3]}`;
}

function EmptyState() {
  return (
    <div className="detail-empty">
      <svg width="40" height="40" viewBox="0 0 24 24" fill="none"
        stroke="currentColor" strokeWidth="1.5">
        <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/>
        <polyline points="14 2 14 8 20 8"/>
      </svg>
      <p>Select a precedent from the list to view its details</p>
    </div>
  );
}

export default function DetailPanel({ cluster }) {
  const [activeTab, setActiveTab] = useState('litigation');

  if (!cluster) {
    return (
      <div className="detail-panel">
        <EmptyState />
      </div>
    );
  }

  const ctx = cluster.legal_context ?? {};
  const lit = ctx.litigation_history     ?? null;
  const jt  = ctx.judicial_treatment     ?? null;
  const leg = ctx.legislative_foundation ?? null;

  const tabCounts = {
    litigation:  Array.isArray(lit) ? lit.length  : 0,
    judicial:    Array.isArray(jt)  ? jt.length   : 0,
    legislation: Array.isArray(leg) ? leg.length  : 0,
  };

  function tabContent() {
    switch (activeTab) {
      case 'litigation':  return <LitigationTab  nodes={lit} />;
      case 'judicial':    return <JudicialTab     citations={jt} />;
      case 'legislation': return <LegislationTab  acts={leg} />;
      default: return null;
    }
  }

  return (
    <div className="detail-panel">
      <div className="detail-header">
        <div className="detail-header-left">
          <div className="detail-case-id">{cluster.case_id}</div>
          <h2 className="detail-title">
            {formatCaseId(cluster.case_id)}
            <span className="seed-badge">
              <svg width="9" height="9" viewBox="0 0 24 24" fill="currentColor">
                <circle cx="12" cy="12" r="10"/>
              </svg>
              Precedent
            </span>
          </h2>
          {cluster.rrf_score != null && (
            <div className="detail-rrf">
              Relevance: {Math.round(cluster.rrf_score * 100)}%
            </div>
          )}
        </div>
        <div className="detail-header-right">
          <span className="detail-legal-ctx">Legal Context</span>
        </div>
      </div>

      <div className="detail-body">
        {cluster.summary && (
          <div className="summary-block">
            <div className="summary-label">Summary</div>
            <p className="summary-text">{cluster.summary}</p>
          </div>
        )}

        <div className="tabs">
          {TABS.map((t) => (
            <button
              key={t.id}
              className={`tab-btn${activeTab === t.id ? ' active' : ''}`}
              onClick={() => setActiveTab(t.id)}
            >
              {t.label}
              {tabCounts[t.id] > 0 && (
                <span className="tab-count">{tabCounts[t.id]}</span>
              )}
            </button>
          ))}
        </div>

        <div className="tab-content">
          <div className="panel-label">{TAB_LABELS[activeTab]}</div>
          {tabContent()}
        </div>
      </div>
    </div>
  );
}