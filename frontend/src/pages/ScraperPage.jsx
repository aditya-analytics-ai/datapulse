import { useState } from 'react';
import { scrapeUrl, getExportUrl } from '../api/client';
import './ScraperPage.css';

const TYPE_BADGE = {
  table:            'badge-teal',
  article:          'badge-blue',
  json:             'badge-purple',
  pdf:              'badge-orange',
  amazon_products:  'badge-green',
  flipkart_products:'badge-pink',
  products:         'badge-green',
  jsonld:           'badge-cyan',
  linkedin_jobs:    'badge-blue',
};

export default function ScraperPage() {
  const [url, setUrl]               = useState('');
  const [playwright, setPlaywright] = useState(false);
  const [loading, setLoading]       = useState(false);
  const [result, setResult]         = useState(null);
  const [error, setError]           = useState('');
  const [progress, setProgress]     = useState(0);

  const handleScrape = async () => {
    if (!url.trim()) { setError('Enter a URL first.'); return; }
    setError(''); setResult(null); setLoading(true); setProgress(0);

    // Fake progress bar
    const tick = setInterval(() => setProgress(p => Math.min(p + Math.random() * 8, 88)), 400);

    try {
      const res = await scrapeUrl(url.trim(), playwright);
      clearInterval(tick); setProgress(100);
      await new Promise(r => setTimeout(r, 300));
      setResult(res.data);
    } catch (e) {
      clearInterval(tick);
      setError(e.response?.data?.detail || e.message || 'Scrape failed.');
    } finally {
      setLoading(false);
      setTimeout(() => setProgress(0), 600);
    }
  };

  const handleExport = (format) => {
    if (!result?.job_id) return;
    window.open(getExportUrl(result.job_id, format), '_blank');
  };

  const previewRows = (() => {
    if (!result) return [];
    const pt = result.page_type;
    const cd = result.cleaned_data;
    if (pt === 'table') return cd?.tables?.[0]?.rows?.slice(0, 30) || [];
    if (pt === 'article') return (cd?.data?.paragraphs || []).slice(0, 20).map((p, i) => ({ '#': i + 1, paragraph: p }));
    if (pt === 'json') return Array.isArray(cd?.data?.data) ? cd.data.data.slice(0, 30) : [];
    if (pt === 'amazon_products' || pt === 'flipkart_products' || pt === 'products') {
      return (cd?.products || []).slice(0, 50).map((p, i) => ({
        '#': i + 1,
        name:    p.name    || '—',
        price:   p.price   || '—',
        rating:  p.rating  || '—',
        reviews: p.reviews || '—',
        discount: p.discount || '—',
        url:     p.url     || '—',
      }));
    }
    if (pt === 'jsonld') {
      return (cd?.items || []).slice(0, 30).map((item, i) => ({
        '#': i + 1,
        type:        item['@type'] || '—',
        name:        item.name?.slice(0, 60) || '—',
        description: (item.description || '—').slice(0, 80),
        url:         item.url?.slice(0, 60) || '—',
      }));
    }
    if (pt === 'linkedin_jobs') {
      return (cd?.jobs || []).slice(0, 30).map((j, i) => ({
        '#': i + 1,
        title:           j.title           || '—',
        company:         j.company         || '—',
        location:        j.location        || '—',
        salary:          j.salary          || '—',
        employment_type: j.employment_type || '—',
        posted_date:     j.posted_date     || '—',
        apply_link:      j.url?.slice(0, 60) || '—',
      }));
    }
    return [];
  })();

  const previewCols = previewRows.length > 0 ? Object.keys(previewRows[0]) : [];

  return (
    <div className="scraper-page">
      {/* Header */}
      <div className="scraper-header anim-fadeIn">
        <div>
          <p className="breadcrumb">DataPulse / Scraper</p>
          <h1 className="page-title">Web Scraper</h1>
        </div>
        {result && (
          <span className="badge badge-green anim-scaleIn">
            <span className="status-dot green" style={{width:5,height:5}} />
            Completed
          </span>
        )}
      </div>

      {/* Input card */}
      <div className="card scraper-input-card anim-fadeUp delay-1">
        <div className="input-wrap">
          <span className="terminal-prefix">❯</span>
          <input
            className="input input-mono"
            type="url"
            value={url}
            onChange={e => setUrl(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleScrape()}
            placeholder="https://example.com  —  any URL, API endpoint, or .pdf"
          />
        </div>

        <div className="scraper-controls">
          <div className="toggles-row">
            <div
              className="toggle-wrap"
              onClick={() => setPlaywright(p => !p)}
            >
              <div className={`toggle ${playwright ? 'on' : ''}`} />
              <span className="toggle-label">Force Playwright (JS-heavy)</span>
            </div>
          </div>

          <button
            className={`btn btn-primary scrape-btn ${loading ? 'loading' : ''}`}
            onClick={handleScrape}
            disabled={loading}
          >
            {loading ? (
              <><span className="spinner" style={{width:14,height:14,borderWidth:2}} /> Scraping...</>
            ) : (
              <>▶ Scrape</>
            )}
          </button>
        </div>

        {/* Progress bar */}
        {loading && (
          <div className="progress-track">
            <div className="progress-bar" style={{ width: `${progress}%` }} />
          </div>
        )}

        {error && <p className="scrape-error">{error}</p>}
      </div>

      {/* Results */}
      {result && (
        <div className="scraper-results">
          {/* Metrics */}
          <div className="metrics-row anim-fadeUp delay-1">
            {[
              { label: 'PAGE TYPE',  value: result.page_type, badge: TYPE_BADGE[result.page_type], color: 'teal' },
              { label: 'METHOD',     value: result.method,    badge: 'badge-blue',                  color: 'blue' },
              { label: 'ROWS',       value: result.row_count?.toLocaleString() || '—',              color: 'purple' },
              { label: 'JOB ID',     value: `#${result.job_id}`,                                   color: 'green' },
            ].map((m, i) => (
              <div key={i} className={`metric-card ${m.color} anim-fadeUp delay-${i + 2}`}>
                <div className="metric-label">{m.label}</div>
                {m.badge
                  ? <span className={`badge ${m.badge}`}>{m.value}</span>
                  : <div className="metric-value">{m.value}</div>
                }
              </div>
            ))}
          </div>

          {/* Data preview */}
          <div className="card anim-fadeUp delay-2" style={{overflow:'hidden', marginTop: 0}}>
            <div className="preview-header">
              <div style={{display:'flex',alignItems:'center',gap:10}}>
                <span className="section-title">Data Preview</span>
                <span className="badge badge-teal">LIVE</span>
              </div>
              <div className="export-btns">
                {['csv','excel','json'].map(fmt => (
                  <button key={fmt} className="btn btn-outline export-btn" onClick={() => handleExport(fmt)}>
                    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4M7 10l5 5 5-5M12 15V3"/></svg>
                    {fmt.toUpperCase()}
                  </button>
                ))}
              </div>
            </div>

            {previewRows.length > 0 ? (
              <div className="table-wrap">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th style={{width:40,color:'#2d3748'}}>#</th>
                      {previewCols.map(c => <th key={c}>{c}</th>)}
                    </tr>
                  </thead>
                  <tbody>
                    {previewRows.map((row, i) => (
                      <tr key={i}>
                        <td className="row-num mono">{String(i + 1).padStart(2, '0')}</td>
                        {previewCols.map(c => {
                          const val = row[c];
                          const str = String(val ?? '—');
                          if (c === 'url' || c === 'apply_link' || (typeof val === 'string' && val.startsWith('http')))
                            return <td key={c} className="mono"><a href={val} target="_blank" rel="noopener noreferrer" title={str} style={{color:'var(--teal)',textDecoration:'underline'}}>{str.slice(0, 80)}</a></td>;
                          return <td key={c} className="mono" title={str}>{str.slice(0, 80)}</td>;
                        })}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="empty-state">
                <div className="empty-state-icon">⬡</div>
                <div className="empty-state-title">No tabular data</div>
                <div className="empty-state-desc">
                  {result.page_type === 'article' ? 'Article scraped — export as JSON/CSV to see content.' : result.page_type === 'jsonld' ? 'Structured data scraped — export to see full schema.' : 'No rows extracted from this page.'}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Idle state */}
      {!result && !loading && (
        <div className="idle-state anim-fadeUp delay-2">
          <div className="idle-terminal">
            <div className="terminal-bar">
              <span/><span/><span/>
              <span className="terminal-title">datapulse.sh</span>
            </div>
            <div className="terminal-body">
              <p><span className="t-prompt">$</span> <span className="t-cmd">datapulse scrape</span> <span className="t-arg">&lt;url&gt;</span></p>
              <p className="t-comment"># Paste any URL above and press Scrape</p>
              <p className="t-comment"># Supports: HTML tables, articles, REST APIs, PDFs, e-commerce, JSON-LD</p>
              <p className="t-comment"># Auto-detects JS-heavy sites and uses Playwright</p>
              <p><span className="t-prompt">$</span> <span className="cursor-term">█</span></p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
