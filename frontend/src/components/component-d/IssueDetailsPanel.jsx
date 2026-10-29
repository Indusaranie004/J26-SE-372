export default function IssueDetailsPanel({ issue, knownFacts, onMarkKnown }) {
  return (
    <div className="cd-details-panel">
      <h3 className="cd-details-title">{issue.question}</h3>

      <div className="cd-details-section">
        <h4>Legal elements to establish</h4>
        <ul>
          {(issue.legal_elements || []).map((el, i) => <li key={i}>{el}</li>)}
        </ul>
      </div>

      <div className="cd-details-section">
        <h4>Relevant facts</h4>
        <ul>
          {(issue.relevant_facts || []).map((f, i) => <li key={i}>{f}</li>)}
        </ul>
      </div>

      <div className="cd-details-section">
        <h4>Missing facts</h4>
        {(issue.missing_facts || []).map((f, i) => (
          <div key={i} className="cd-details-fact-row">
            <span>{f}</span>
            <button className="cd-fact-btn-sm" onClick={() => onMarkKnown(f)}>Mark as known</button>
          </div>
        ))}
      </div>

      {issue.research_question && (
        <div className="cd-details-section">
          <h4>Research question</h4>
          <div className="cd-details-research-q">{issue.research_question}</div>
        </div>
      )}

      {issue.authority_hints?.length > 0 && (
        <div className="cd-details-section">
          <h4>Authorities mapped</h4>
          <div className="cd-details-authorities">
            {issue.authority_hints.map((h, i) => (
              <span key={i} className="cd-authority-hint-tag">{h}</span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}