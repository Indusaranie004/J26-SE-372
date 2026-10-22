export default function LegislationTab({ acts }) {
  if (typeof acts === 'string') {
    return <p className="empty-msg">{acts}</p>;
  }
  if (!acts || acts.length === 0) {
    return <p className="empty-msg">No legislative foundation data available.</p>;
  }

  return (
    <div className="leg-list">
      {acts.map((a, i) => (
        <div key={a.act_id ?? i} className="leg-card">
          <div className="leg-name">{a.name}</div>
          <span className="leg-section">{a.section}</span>
          <div className="leg-id">{a.act_id}</div>
        </div>
      ))}
    </div>
  );
}