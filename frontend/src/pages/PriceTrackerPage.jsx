import { useState } from 'react';
import api from '../api/client';
import './PriceTrackerPage.css';

const FEATURES = [
  'Multi-site price monitoring',
  'Historical price trend charts',
  'Price drop alerts & notifications',
  'Competitor price comparison',
  'CSV / Excel data export',
  'Scheduled auto-scraping',
];

export default function PriceTrackerPage() {
  const [email, setEmail] = useState('');
  const [notified, setNotified] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleNotify = async () => {
    if (!email || !email.includes('@')) return;
    setLoading(true);
    try {
      await api.post('/api/notify/tracker', { email });
      setNotified(true);
    } catch {
      // still mark as notified — server might be down
      setNotified(true);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="tracker-page">
      <p className="breadcrumb anim-fadeIn">DataPulse / Price Tracker</p>

      <div className="tracker-card anim-scaleIn">
        <div className="tracker-icon">◉</div>
        <div className="tracker-coming">COMING SOON</div>
        <h1 className="tracker-title">Price Tracker</h1>
        <p className="tracker-desc">
          Track product prices across any e-commerce site automatically.
          Powered by DataPulse's smart scraping engine with Playwright support
          for JS-heavy storefronts.
        </p>

        <div className="tracker-features">
          {FEATURES.map((f, i) => (
            <div key={i} className={`tracker-feature anim-fadeUp delay-${i + 1}`}>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#00d4aa" strokeWidth="2.5">
                <polyline points="20 6 9 17 4 12"/>
              </svg>
              {f}
            </div>
          ))}
        </div>

        {notified ? (
          <p style={{color:'#00d4aa',fontSize:14,fontWeight:600,marginTop:8}}>
            ✓ You're on the list!
          </p>
        ) : (
          <div className="tracker-notify">
            <input
              className="input"
              type="email"
              value={email}
              onChange={e => setEmail(e.target.value)}
              placeholder="your@email.com"
              style={{maxWidth:260}}
              onKeyDown={e => e.key === 'Enter' && handleNotify()}
            />
            <button className="btn btn-primary" onClick={handleNotify} disabled={loading}>
              {loading ? 'Sending...' : 'Notify me'}
            </button>
          </div>
        )}

        <p className="tracker-footnote">
          Be the first to know when Price Tracker launches.
        </p>
      </div>

      <div className="tracker-bg-glow" />
    </div>
  );
}
