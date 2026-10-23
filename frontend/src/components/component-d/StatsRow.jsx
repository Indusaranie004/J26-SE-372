export default function StatsRow({ issues, missingFacts, authorities, weak }) {
  const stats = [
    { value: issues, label: 'Issues and sub-issues' },
    { value: missingFacts, label: 'Missing facts to ask for', highlight: missingFacts > 0 },
    { value: authorities, label: 'Authorities mapped' },
    { value: weak, label: 'Weak or overruled' },
  ];

  return (
    <div className="cd-stats-row">
      {stats.map((s, i) => (
        <div key={i} className="cd-stat-card">
          <div className={`cd-stat-value${s.highlight ? ' cd-stat-highlight' : ''}`}>{s.value}</div>
          <div className="cd-stat-label">{s.label}</div>
        </div>
      ))}
    </div>
  );
}