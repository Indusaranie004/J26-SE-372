export default function ArgumentStrengthPanel({ mapData, evidenceStatus }) {
  if (!mapData) return null;

  const allArgs = [...(mapData.supporting_arguments || []), ...(mapData.opposing_arguments || [])];
  const allAuth = allArgs.flatMap(a => a.authorities || []);
  const allEvidence = allArgs.flatMap(a => a.evidence || []);

  const supportingAuth = (mapData.supporting_arguments || []).flatMap(a => a.authorities || []).length;
  const opposingAuth = (mapData.opposing_arguments || []).flatMap(a => a.authorities || []).length;
  const evidenceGaps = allEvidence.filter(e => {
    const status = evidenceStatus[e.id] || e.status;
    return status !== 'in_hand';
  }).length;
  const missingAuth = allArgs.filter(a => !a.authorities || a.authorities.length === 0).length;
  const evidenceInHand = allEvidence.filter(e => {
    const status = evidenceStatus[e.id] || e.status;
    return status === 'in_hand';
  }).length;
  const evidencePct = allEvidence.length > 0 ? Math.round((evidenceInHand / allEvidence.length) * 100) : 0;

  const overallStrength = mapData.strength_analysis?.overall_strength || 0;
  const strengthLabel = overallStrength >= 70 ? 'Strong' : overallStrength >= 50 ? 'Moderate' : 'Weak';

  return (
    <div className="cd-strength-panel">
      <div className="cd-strength-header">
        <h4>Argument strength analysis</h4>
        <span className={`cd-strength-badge cd-strength-${strengthLabel.toLowerCase()}`}>{strengthLabel}</span>
      </div>

      <div className="cd-strength-grid">
        <div className="cd-strength-main">
          <div className="cd-strength-label">Overall argument strength</div>
          <div className="cd-strength-value">{overallStrength}%</div>
          <div className="cd-strength-bar">
            <div className="cd-strength-bar-fill" style={{ width: `${overallStrength}%` }}></div>
          </div>
          <div className="cd-strength-note">
            70% strongest supporting authority, 30% evidence in hand. A prototype heuristic.
          </div>
        </div>

        <div className="cd-strength-stat">
          <div className="cd-strength-stat-num">{supportingAuth}</div>
          <div className="cd-strength-stat-label">Supporting authorities</div>
        </div>
        <div className="cd-strength-stat">
          <div className="cd-strength-stat-num">{opposingAuth}</div>
          <div className="cd-strength-stat-label">Contradicting authorities</div>
        </div>
        <div className="cd-strength-stat">
          <div className="cd-strength-stat-num">{evidenceGaps}</div>
          <div className="cd-strength-stat-label">Evidence gaps</div>
        </div>
        <div className="cd-strength-stat">
          <div className="cd-strength-stat-num">{missingAuth}</div>
          <div className="cd-strength-stat-label">Missing authorities</div>
        </div>
        <div className="cd-strength-stat">
          <div className="cd-strength-stat-num">{evidencePct}%</div>
          <div className="cd-strength-stat-label">Evidence in hand</div>
        </div>
      </div>

      {missingAuth > 0 && (
        <div className="cd-strength-warning">
          <span className="cd-warning-icon">⚠</span>
          <div>
            <strong>Potential gap detected</strong>
            <div>{missingAuth} argument{missingAuth !== 1 ? 's' : ''} ha{missingAuth === 1 ? 's' : 've'} no authority mapped yet.</div>
          </div>
        </div>
      )}
    </div>
  );
}