import { useState } from 'react';
import QueryInput from './QueryInput.jsx';
import StatsRow from './StatsRow.jsx';
import TabSelector from './TabSelector.jsx';
import IssueTreeView from './IssueTreeView.jsx';
import ArgumentMapView from './ArgumentMapView.jsx';
import MissingFactsPanel from './MissingFactsPanel.jsx';
import IssueDetailsPanel from './IssueDetailsPanel.jsx';
import ArgumentStrengthPanel from './ArgumentStrengthPanel.jsx';

export default function IssueSpotter() {
  const [issueTree, setIssueTree] = useState(null);
  const [argumentMap, setArgumentMap] = useState(null);
  const [activeTab, setActiveTab] = useState('issue-tree');
  const [selectedIssue, setSelectedIssue] = useState(null);
  const [selectedArgument, setSelectedArgument] = useState(null);
  const [knownFacts, setKnownFacts] = useState(new Set());
  const [evidenceStatus, setEvidenceStatus] = useState({});
  const [loading, setLoading] = useState(false);

  const handleAnalyse = async (query) => {
    setLoading(true);
    try {
      const res = await fetch('http://127.0.0.1:8003/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query }),
      });
      const data = await res.json();
      setIssueTree(data);
      setArgumentMap(null);
      setSelectedIssue(null);
      setSelectedArgument(null);
      setKnownFacts(new Set());
      setEvidenceStatus({});
    } catch (err) {
      console.error('Analyse error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleIssueSelect = async (issue) => {
    setSelectedIssue(issue);
    setSelectedArgument(null);
    setLoading(true);
    try {
      const res = await fetch('http://127.0.0.1:8003/generate-argument-map', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ issue_id: issue.id, issue_question: issue.question }),
      });
      const data = await res.json();
      setArgumentMap(data.data);
      setActiveTab('argument-map');
    } catch (err) {
      console.error('Argument map error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleMarkKnown = (fact) => {
    setKnownFacts(prev => {
      const next = new Set(prev);
      if (next.has(fact)) next.delete(fact);
      else next.add(fact);
      return next;
    });
  };

  const handleEvidenceToggle = (evidenceId, status) => {
    setEvidenceStatus(prev => ({ ...prev, [evidenceId]: status }));
  };

  // Compute stats
  const allIssues = issueTree?.issues?.flatMap(i => [i, ...(i.children || [])]) || [];
  const missingFactsCount = (issueTree?.global_missing_facts || []).filter(f => !knownFacts.has(f)).length;
  const authoritiesCount = argumentMap
    ? [...(argumentMap.supporting_arguments || []), ...(argumentMap.opposing_arguments || [])]
        .flatMap(a => a.authorities || []).length
    : 0;
  const weakCount = argumentMap
    ? [...(argumentMap.supporting_arguments || []), ...(argumentMap.opposing_arguments || [])]
        .flatMap(a => a.authorities || []).filter(auth => auth.score < 50).length
    : 0;

  return (
    <div className="cd-page">
      <div className="cd-page-header">
        <h1 className="cd-page-title">
          Issue Spotter & Argument Map
          <span className="cd-badge">Component D</span>
        </h1>
        <p className="cd-page-subtitle">
          Start from the same search the lawyer types in Research Assistant. See the legal issues behind it, which authorities support or oppose each one, and what is still missing, before retrieval.
        </p>
      </div>

      <QueryInput onAnalyse={handleAnalyse} loading={loading} />

      {issueTree && (
        <>
          <StatsRow
            issues={allIssues.length}
            missingFacts={missingFactsCount}
            authorities={authoritiesCount}
            weak={weakCount}
          />

          <TabSelector activeTab={activeTab} onTabChange={setActiveTab} />

          <div className="cd-main-layout">
            <div className="cd-main-content">
              {activeTab === 'issue-tree' && (
                <div className="cd-panel">
                  <h3 className="cd-panel-heading">What legal questions must be answered?</h3>
                  <p className="cd-panel-subheading">The search query broken into progressively smaller questions.</p>
                  <IssueTreeView
                    treeData={issueTree}
                    selectedIssue={selectedIssue}
                    onSelectIssue={handleIssueSelect}
                    knownFacts={knownFacts}
                  />
                  <div className="cd-legend">
                    <span className="cd-legend-item"><span className="cd-dot cd-dot-purple"></span>Main issue</span>
                    <span className="cd-legend-item"><span className="cd-dot cd-dot-orange"></span>Needs facts</span>
                    <span className="cd-legend-item"><span className="cd-dot cd-dot-green"></span>Ready to research</span>
                    <span className="cd-legend-text">Select a box for details</span>
                  </div>
                </div>
              )}

              {activeTab === 'argument-map' && argumentMap && (
                <div className="cd-panel">
                  <div className="cd-am-header">
                    <div className="cd-breadcrumb">Issue Spotter › Argument map</div>
                    <h3 className="cd-panel-heading">Argument map</h3>
                    <p className="cd-am-query">{issueTree.query}</p>
                  </div>

                  <div className="cd-am-issue-tabs">
                    {allIssues.map(issue => (
                      <button
                        key={issue.id}
                        className={`cd-am-issue-tab${selectedIssue?.id === issue.id ? ' active' : ''}`}
                        onClick={() => handleIssueSelect(issue)}
                      >
                        {issue.question.length > 30 ? issue.question.slice(0, 30) + '...' : issue.question}
                      </button>
                    ))}
                  </div>

                  {selectedIssue && (
                    <>
                      <div className="cd-am-issue-label">Issue: {selectedIssue.question}</div>
                      <ArgumentMapView
                        mapData={argumentMap}
                        selectedArgument={selectedArgument}
                        onSelectArgument={setSelectedArgument}
                        evidenceStatus={evidenceStatus}
                        onEvidenceToggle={handleEvidenceToggle}
                      />
                      <ArgumentStrengthPanel mapData={argumentMap} evidenceStatus={evidenceStatus} />
                    </>
                  )}
                </div>
              )}

              {activeTab === 'authority-strength' && (
                <div className="cd-panel">
                  <h3 className="cd-panel-heading">Authority Strength</h3>
                  <p className="cd-panel-subheading">Detailed citation strength analysis for each authority.</p>
                  {argumentMap ? (
                    <div className="cd-authority-list">
                      {[...(argumentMap.supporting_arguments || []), ...(argumentMap.opposing_arguments || [])]
                        .flatMap(a => a.authorities || [])
                        .map(auth => (
                          <div key={auth.id} className="cd-auth-detail-card">
                            <div className="cd-auth-detail-header">
                              <div>
                                <h4>{auth.name}</h4>
                                <p className="cd-auth-docid">{auth.doc_id}</p>
                              </div>
                              <div className="cd-auth-score-large">{auth.score}%</div>
                            </div>
                            <div className="cd-auth-metrics-grid">
                              {Object.entries(auth.citation_metrics || {}).map(([k, v]) => (
                                <div key={k} className="cd-metric-row">
                                  <span className="cd-metric-label">{k.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}</span>
                                  <span className="cd-metric-value">{v}</span>
                                </div>
                              ))}
                            </div>
                            {auth.shap_reasoning && (
                              <div className="cd-shap-detail">
                                <strong>SHAP Reasoning:</strong> {auth.shap_reasoning}
                              </div>
                            )}
                          </div>
                        ))}
                    </div>
                  ) : (
                    <p className="cd-empty-msg">Generate an argument map first to see authority strengths.</p>
                  )}
                </div>
              )}
            </div>

            {/* Right Sidebar */}
            {(activeTab === 'issue-tree' || activeTab === 'argument-map') && (
              <aside className="cd-sidebar">
                {activeTab === 'issue-tree' && issueTree && (
                  <>
                    <MissingFactsPanel
                      facts={issueTree.global_missing_facts || []}
                      knownFacts={knownFacts}
                      onMarkKnown={handleMarkKnown}
                    />
                    <div className="cd-sidebar-card">
                      <h4 className="cd-sidebar-title">Send to retrieval</h4>
                      <p className="cd-sidebar-text">Component B searches each sub-issue instead of the raw query.</p>
                      <button className="cd-btn-dark">→ Open in Research Assistant</button>
                      <button className="cd-btn-outline">Show structured context</button>
                    </div>
                  </>
                )}

                {activeTab === 'argument-map' && selectedArgument && (
                  <div className="cd-sidebar-card">
                    <div className="cd-sidebar-label">Selected argument</div>
                    <p className="cd-sidebar-arg-text">{selectedArgument.text}</p>
                    <span className={`cd-stance-badge cd-stance-${selectedArgument.stance}`}>
                      {selectedArgument.stance === 'supporting' ? 'Supporting' : 'Opposing'}
                    </span>

                    <div className="cd-sidebar-tabs">
                      <button className="cd-sidebar-tab active">Argument</button>
                      <button className="cd-sidebar-tab">Evidence ({(selectedArgument.evidence || []).length})</button>
                      <button className="cd-sidebar-tab">Authorities ({(selectedArgument.authorities || []).length})</button>
                    </div>

                    <div className="cd-sidebar-section">
                      <h5>Related facts</h5>
                      <ul>
                        {(selectedArgument.evidence || []).map(e => (
                          <li key={e.id}>{e.text}</li>
                        ))}
                      </ul>
                    </div>

                    {selectedArgument.authorities?.[0] && (
                      <div className="cd-sidebar-section">
                        <h5>Citation strength</h5>
                        <div className="cd-sidebar-donut-row">
                          <div className="cd-donut-small">
                            <svg viewBox="0 0 36 36" className="cd-donut-svg">
                              <circle cx="18" cy="18" r="15.9" fill="none" stroke="#e5e7eb" strokeWidth="3"/>
                              <circle
                                cx="18" cy="18" r="15.9" fill="none"
                                stroke="#16a34a" strokeWidth="3"
                                strokeDasharray={`${selectedArgument.authorities[0].score} ${100 - selectedArgument.authorities[0].score}`}
                                strokeDashoffset="25"
                                strokeLinecap="round"
                              />
                            </svg>
                            <span className="cd-donut-label">{selectedArgument.authorities[0].score}%</span>
                          </div>
                          <div className="cd-donut-metrics">
                            {Object.entries(selectedArgument.authorities[0].citation_metrics || {}).map(([k, v]) => (
                              <div key={k} className="cd-donut-metric">
                                <span>{k.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}</span>
                                <strong>{v}</strong>
                              </div>
                            ))}
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {activeTab === 'argument-map' && !selectedArgument && argumentMap && (
                  <div className="cd-sidebar-card">
                    <div className="cd-sidebar-label">Citation strength</div>
                    {argumentMap.supporting_arguments?.[0]?.authorities?.[0] && (
                      <>
                        <div className="cd-sidebar-donut-row">
                          <div className="cd-donut-small">
                            <svg viewBox="0 0 36 36" className="cd-donut-svg">
                              <circle cx="18" cy="18" r="15.9" fill="none" stroke="#e5e7eb" strokeWidth="3"/>
                              <circle
                                cx="18" cy="18" r="15.9" fill="none"
                                stroke="#16a34a" strokeWidth="3"
                                strokeDasharray={`${argumentMap.supporting_arguments[0].authorities[0].score} ${100 - argumentMap.supporting_arguments[0].authorities[0].score}`}
                                strokeDashoffset="25"
                                strokeLinecap="round"
                              />
                            </svg>
                            <span className="cd-donut-label">{argumentMap.supporting_arguments[0].authorities[0].score}%</span>
                          </div>
                          <div className="cd-donut-metrics">
                            {Object.entries(argumentMap.supporting_arguments[0].authorities[0].citation_metrics || {}).map(([k, v]) => (
                              <div key={k} className="cd-donut-metric">
                                <span>{k.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}</span>
                                <strong>{v}</strong>
                              </div>
                            ))}
                          </div>
                        </div>
                        <div className="cd-sidebar-stats-row">
                          <div className="cd-sidebar-stat">
                            <div className="cd-sidebar-stat-num">
                              {argumentMap.supporting_arguments?.reduce((sum, a) => sum + (a.authorities?.length || 0), 0) || 0}
                            </div>
                            <div className="cd-sidebar-stat-label">Supporting authorities</div>
                          </div>
                          <div className="cd-sidebar-stat">
                            <div className="cd-sidebar-stat-num">
                              {argumentMap.opposing_arguments?.reduce((sum, a) => sum + (a.authorities?.length || 0), 0) || 0}
                            </div>
                            <div className="cd-sidebar-stat-label">Contradicting authorities</div>
                          </div>
                        </div>
                      </>
                    )}
                  </div>
                )}
              </aside>
            )}
          </div>

          {activeTab === 'issue-tree' && selectedIssue && (
            <IssueDetailsPanel issue={selectedIssue} knownFacts={knownFacts} onMarkKnown={handleMarkKnown} />
          )}
        </>
      )}

      {!issueTree && !loading && (
        <div className="cd-empty-state">
          <p>Enter a legal query above to begin issue spotting.</p>
        </div>
      )}
    </div>
  );
}