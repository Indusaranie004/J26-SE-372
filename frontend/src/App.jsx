import { useState, useEffect } from 'react';
import Navbar from './components/Navbar.jsx';
import SearchBar from './components/SearchBar.jsx';
import ClusterList from './components/ClusterList.jsx';
import DetailPanel from './components/DetailPanel.jsx';
import CHIPS from './config/chips.js';
import { retrievePrecedents } from './api/retrieve.js';

// Import Component D modules
import IssueSpotter from './components/component-d/IssueSpotter.jsx';

// Auto-select the first chip on load
const DEFAULT_CHIP = CHIPS[0];

export default function App() {
  const [activeNav, setActiveNav] = useState('search');
  const [query, setQuery] = useState(DEFAULT_CHIP.query);
  const [activeChipId, setActiveChipId] = useState(DEFAULT_CHIP.id);
  const [clusters, setClusters] = useState([]);
  const [activeId, setActiveId] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Load first chip's mock data on mount
  useEffect(() => {
    if (DEFAULT_CHIP.mockData) {
      setClusters(DEFAULT_CHIP.mockData.clusters);
      if (DEFAULT_CHIP.mockData.clusters.length > 0) {
        setActiveId(DEFAULT_CHIP.mockData.clusters[0].case_id);
      }
    }
  }, []);

  async function handleSearch() {
    if (!query.trim()) return;
    setError(null);
    setLoading(true);
    try {
      const result = await retrievePrecedents(query.trim());
      setClusters(result);
      setActiveId(result.length > 0 ? result[0].case_id : null);
      setActiveChipId(null); // clear chip highlight when doing a free search
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  function handleChipSelect(chip) {
    setActiveChipId(chip.id);
    setQuery(chip.query);
    setError(null);

    if (chip.mockData) {
      // Use mock data immediately — no network call
      setClusters(chip.mockData.clusters);
      setActiveId(chip.mockData.clusters.length > 0 ? chip.mockData.clusters[0].case_id : null);
    } else {
      // Trigger live search
      setLoading(true);
      retrievePrecedents(chip.query)
        .then((result) => {
          setClusters(result);
          setActiveId(result.length > 0 ? result[0].case_id : null);
        })
        .catch((err) => setError(err.message))
        .finally(() => setLoading(false));
    }
  }

  const activeCluster = clusters.find((c) => c.case_id === activeId) ?? null;

  return (
    <div className="app">
      <Navbar activeNav={activeNav} onNavClick={setActiveNav} />

      {/* ✅ ONLY SHOW COMPONENT B WHEN 'search' IS ACTIVE */}
      {activeNav === 'search' && (
        <>
        { error && (
          <div className="error-banner">
            ⚠ {error}
          </div>
        )}

      <SearchBar
        query={query}
        setQuery={setQuery}
        onSearch={handleSearch}
        activeChipId={activeChipId}
        onChipSelect={handleChipSelect}
        loading={loading}
      />

      <div className="body">
        <ClusterList
          clusters={clusters}
          activeId={activeId}
          onSelect={setActiveId}
          loading={loading}
        />

        <DetailPanel cluster={activeCluster} />

        {/* Chat icon — bottom-left of the Find Legal Precedents body */}
        <button
          className="chat-fab"
          title="Chat"
          aria-label="Open chat"
          onClick={() => {/* wire up chat panel here */ }}
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none"
            stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z" />
          </svg>
        </button>
      </div>
      </>
      )}
      {/* COMPONENT D: Only renders when 'issue-spotter' is active */}
      {activeNav === 'issue-spotter' && (
        <IssueSpotter />
      )}
    </div>
  );
}
