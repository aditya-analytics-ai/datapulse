import { useNavigate, useLocation } from 'react-router-dom';
import { useState, useEffect } from 'react';
import { checkHealth } from '../api/client';
import './Sidebar.css';

const NAV = [
  { path: '/app/scraper', icon: '⬡', label: 'Scraper',     title: 'Scraper' },
  { path: '/app/history', icon: '◷', label: 'History',     title: 'History' },
  { path: '/app/jobs',    icon: '◈', label: 'Job Market',  title: 'Job Market' },
  { path: '/app/tracker', icon: '◉', label: 'Price Track', title: 'Price Tracker' },
];

export default function Sidebar() {
  const navigate  = useNavigate();
  const location  = useLocation();
  const [apiOk, setApiOk]   = useState(null);
  const [tooltip, setTooltip] = useState(null);

  useEffect(() => {
    const check = async () => {
      try { await checkHealth(); setApiOk(true); }
      catch { setApiOk(false); }
    };
    check();
    const t = setInterval(check, 15000);
    return () => clearInterval(t);
  }, []);

  return (
    <aside className="sidebar">
      {/* Logo */}
      <div className="sidebar-logo" onClick={() => navigate('/')}>
        <span className="logo-mark">DP</span>
      </div>

      {/* Nav */}
      <nav className="sidebar-nav">
        {NAV.map((item) => {
          const active = location.pathname.startsWith(item.path);
          return (
            <div
              key={item.path}
              className={`nav-item ${active ? 'active' : ''}`}
              onClick={() => navigate(item.path)}
              onMouseEnter={() => setTooltip(item.title)}
              onMouseLeave={() => setTooltip(null)}
            >
              <span className="nav-icon">{item.icon}</span>
              {tooltip === item.title && (
                <span className="nav-tooltip">{item.title}</span>
              )}
            </div>
          );
        })}
      </nav>

      {/* API Status */}
      <div className="sidebar-footer">
        <div className={`api-dot ${apiOk === true ? 'live' : apiOk === false ? 'dead' : 'checking'}`} />
        <span className="api-label">{apiOk === true ? 'Live' : apiOk === false ? 'Down' : '...'}</span>
      </div>
    </aside>
  );
}
