const TABS = [
  { id: 'issue-tree', label: 'Issue tree', icon: '◇' },
  { id: 'argument-map', label: 'Argument map', icon: '⚖' },
  { id: 'authority-strength', label: 'Authority strength', icon: '↗' },
];

export default function TabSelector({ activeTab, onTabChange }) {
  return (
    <div className="cd-tab-row">
      {TABS.map(tab => (
        <button
          key={tab.id}
          className={`cd-tab-btn${activeTab === tab.id ? ' active' : ''}`}
          onClick={() => onTabChange(tab.id)}
        >
          <span className="cd-tab-icon">{tab.icon}</span>
          {tab.label}
        </button>
      ))}
    </div>
  );
}