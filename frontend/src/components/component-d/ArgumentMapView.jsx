import AuthorityCard from './AuthorityCard.jsx';

export default function ArgumentMapView({ mapData, selectedArgument, onSelectArgument, evidenceStatus, onEvidenceToggle }) {
  if (!mapData) return null;

  const supporting = mapData.supporting_arguments || [];
  const opposing = mapData.opposing_arguments || [];

  return (
    <div className="cd-argmap">
      {/* Conclusion */}
      <div className="cd-argmap-conclusion">
        <div className="cd-argmap-conclusion-label">Conclusion</div>
        <div className="cd-argmap-conclusion-text">{mapData.conclusion}</div>
        <div className={`cd-argmap-stance cd-stance-${mapData.conclusion_stance?.toLowerCase().replace(' ', '-') || 'contested'}`}>
          {mapData.conclusion_stance || 'Contested'}
        </div>
      </div>

      {/* Two columns */}
      <div className="cd-argmap-columns">
        <div className="cd-argmap-col cd-col-supporting">
          <div className="cd-argmap-col-header supporting">
            <div>Supporting arguments</div>
            <div className="cd-argmap-col-count">{supporting.length} argument{supporting.length !== 1 ? 's' : ''} mapped</div>
          </div>
          {supporting.map(arg => (
            <div key={arg.id} className={`cd-arg-card cd-arg-supporting${selectedArgument?.id === arg.id ? ' selected' : ''}`}
                 onClick={() => onSelectArgument(arg)}>
              <div className="cd-arg-text">{arg.text}</div>
              <div className="cd-arg-evidence">
                <div className="cd-arg-evidence-label">Evidence</div>
                {(arg.evidence || []).map(ev => {
                  const status = evidenceStatus[ev.id] || ev.status || 'needed';
                  return (
                    <div key={ev.id} className={`cd-evidence-item cd-evidence-${status}`}>
                      {status === 'in_hand' && <span className="cd-evidence-check">✓</span>}
                      {ev.text}
                    </div>
                  );
                })}
              </div>
              <div className="cd-arg-authorities">
                <div className="cd-arg-authorities-label">Legal authority</div>
                {arg.authorities?.length > 0 ? (
                  arg.authorities.map(auth => (
                    <AuthorityCard key={auth.id} authority={auth} compact />
                  ))
                ) : (
                  <div className="cd-no-authority">No authority mapped yet</div>
                )}
              </div>
            </div>
          ))}
        </div>

        <div className="cd-argmap-col cd-col-opposing">
          <div className="cd-argmap-col-header opposing">
            <div>Opposing arguments</div>
            <div className="cd-argmap-col-count">{opposing.length} argument{opposing.length !== 1 ? 's' : ''} mapped</div>
          </div>
          {opposing.map(arg => (
            <div key={arg.id} className={`cd-arg-card cd-arg-opposing${selectedArgument?.id === arg.id ? ' selected' : ''}`}
                 onClick={() => onSelectArgument(arg)}>
              <div className="cd-arg-text">{arg.text}</div>
              <div className="cd-arg-evidence">
                <div className="cd-arg-evidence-label">Evidence</div>
                {(arg.evidence || []).map(ev => {
                  const status = evidenceStatus[ev.id] || ev.status || 'needed';
                  return (
                    <div key={ev.id} className={`cd-evidence-item cd-evidence-${status}`}>
                      {status === 'in_hand' && <span className="cd-evidence-check">✓</span>}
                      {ev.text}
                    </div>
                  );
                })}
              </div>
              <div className="cd-arg-authorities">
                <div className="cd-arg-authorities-label">Legal authority</div>
                {arg.authorities?.length > 0 ? (
                  arg.authorities.map(auth => (
                    <AuthorityCard key={auth.id} authority={auth} compact />
                  ))
                ) : (
                  <div className="cd-no-authority">No authority mapped yet</div>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Relationship legend */}
      <div className="cd-argmap-legend">
        <span className="cd-legend-label">Relationship:</span>
        <span className="cd-rel-tag cd-rel-supports">Supports</span>
        <span className="cd-rel-tag cd-rel-contradicts">Contradicts</span>
        <span className="cd-rel-tag cd-rel-distinguishes">Distinguishes</span>
        <span className="cd-rel-tag cd-rel-overrules">Overrules</span>
        <span className="cd-rel-tag cd-rel-exception">Provides exception</span>
        <span className="cd-rel-tag cd-rel-interprets">Interprets</span>
        <span className="cd-rel-tag cd-rel-overruled">Overruled</span>
      </div>
      <div className="cd-argmap-legend">
        <span className="cd-evidence-legend-item"><span className="cd-evidence-dot cd-evidence-dot-needed"></span>Evidence still needed</span>
        <span className="cd-evidence-legend-item"><span className="cd-evidence-dot cd-evidence-dot-inhand"></span>Evidence in hand (✓)</span>
        <span className="cd-legend-text">Select any box for details.</span>
      </div>
    </div>
  );
}