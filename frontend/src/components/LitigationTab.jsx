export default function LitigationTab({ nodes }) {
  if (typeof nodes === 'string') {
    return <p className="empty-msg">{nodes}</p>;
  }
  if (!nodes || nodes.length === 0) {
    return <p className="empty-msg">No litigation history available.</p>;
  }

  const sorted = [...nodes].sort((a, b) => b.hops - a.hops);

  return (
    <div className="lit-chain">
      {sorted.map((n, idx) => {
        const isSeed = n.hops === 0;
        return (
          <div key={n.related_id ?? idx}>
            <div className={`lit-card${isSeed ? ' seed-card' : ''}`}>
              <div className="lit-court">{n.court}</div>
              <div className="lit-judge">{n.judge}</div>
              <div className="lit-ref">{n.related_id}</div>
            </div>
            {idx < sorted.length - 1 && (
              <div className="lit-arrow">
                <svg width="20" height="24" viewBox="0 0 20 24" fill="none"
                  stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <line x1="10" y1="0" x2="10" y2="18"/>
                  <polyline points="4,12 10,20 16,12"/>
                </svg>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}