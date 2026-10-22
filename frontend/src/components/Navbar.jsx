import NAV_ITEMS from '../config/nav.js';

export default function Navbar({ activeNav, onNavClick }) {
  return (
    <nav className="navbar">
      <div className="brand">
        {/* LexGraph layers icon */}
        <svg className="brand-icon" width="18" height="18" viewBox="0 0 24 24" fill="none"
          stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M12 2L2 7l10 5 10-5-10-5z"/>
          <path d="M2 17l10 5 10-5"/>
          <path d="M2 12l10 5 10-5"/>
        </svg>
        <span className="brand-text">LexGraph</span>
        <span className="brand-badge">LK</span>
      </div>

      <div className="nav-items">
        {NAV_ITEMS.map((item) => (
          <button
            key={item.id}
            className={`nav-btn${activeNav === item.id ? ' active' : ''}`}
            onClick={() => onNavClick(item.id)}
          >
            {item.label}
          </button>
        ))}
      </div>
    </nav>
  );
}
