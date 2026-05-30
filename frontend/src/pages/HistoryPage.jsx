import React, { useState, useEffect } from 'react';
import { getAllJobs, getJobById, deleteJob, getExportUrl } from '../api/client';
import './HistoryPage.css';

const TYPE_BADGE = { table:'badge-teal', article:'badge-blue', json:'badge-purple', pdf:'badge-orange', amazon_products:'badge-green', flipkart_products:'badge-pink', products:'badge-green', jsonld:'badge-cyan', linkedin_jobs:'badge-blue', jobs:'badge-purple' };
const relTime = (iso) => {
  if (!iso) return '—';
  const diff = Date.now() - new Date(iso).getTime();
  const m = Math.floor(diff / 60000);
  if (m < 1) return 'just now';
  if (m < 60) return `${m}m ago`;
  const h = Math.floor(m / 60);
  if (h < 24) return `${h}h ago`;
  const d = Math.floor(h / 24);
  return d === 1 ? 'yesterday' : `${d}d ago`;
};

export default function HistoryPage() {
  const [jobs, setJobs]         = useState([]);
  const [loading, setLoading]   = useState(true);
  const [search, setSearch]     = useState('');
  const [expanded, setExpanded] = useState(null);
  const [detail, setDetail]     = useState({});
  const [deleting, setDeleting] = useState(null);

  const load = async () => {
    try {
      const r = await getAllJobs();
      const data = r.data;
      setJobs(Array.isArray(data) ? data : (data.jobs || []));
    } catch { /* ignore */ }
    finally { setLoading(false); }
  };

  useEffect(() => { load(); }, []);

  const toggleExpand = async (id) => {
    if (expanded === id) { setExpanded(null); return; }
    setExpanded(id);
    if (!detail[id]) {
      try {
        const r = await getJobById(id);
        setDetail(d => ({ ...d, [id]: r.data }));
      } catch { /* ignore */ }
    }
  };

  const handleDelete = async (e, id) => {
    e.stopPropagation();
    setDeleting(id);
    try { await deleteJob(id); setJobs(j => j.filter(x => x.id !== id)); setExpanded(null); }
    catch { /* ignore */ }
    finally { setDeleting(null); }
  };

  const filtered = jobs.filter(j =>
    j.url?.toLowerCase().includes(search.toLowerCase()) ||
    j.page_type?.includes(search.toLowerCase())
  );

  return (
    <div className="history-page">
      <div className="history-header anim-fadeIn">
        <div>
          <p className="breadcrumb">DataPulse / History</p>
          <h1 className="page-title">Scrape History</h1>
        </div>
        <div style={{display:'flex',alignItems:'center',gap:10}}>
          <span className="job-count">{jobs.length} jobs</span>
          <div className="search-wrap">
            <svg className="search-icon" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg>
            <input className="search-input" placeholder="filter logs..." value={search} onChange={e => setSearch(e.target.value)} />
          </div>
        </div>
      </div>

      <div className="card history-card anim-fadeUp delay-1" style={{padding:0,overflow:'hidden'}}>
        {loading ? (
          <div style={{padding:60,textAlign:'center'}}>
            <div className="spinner spinner-lg" style={{margin:'0 auto'}} />
          </div>
        ) : filtered.length === 0 ? (
          <div className="empty-state" style={{padding:'60px 20px'}}>
            <div className="idle-terminal" style={{maxWidth:400,width:'100%',margin:'0 auto'}}>
              <div className="terminal-bar" style={{padding:'8px 14px'}}>
                <span style={{width:8,height:8,borderRadius:'50%',background:'#ef4444',display:'inline-block'}} />
                <span style={{width:8,height:8,borderRadius:'50%',background:'#f97316',display:'inline-block',marginLeft:4}} />
                <span style={{width:8,height:8,borderRadius:'50%',background:'#22c55e',display:'inline-block',marginLeft:4}} />
              </div>
              <div style={{padding:'16px 20px',fontFamily:'JetBrains Mono, monospace',fontSize:12}}>
                <p style={{color:'#00d4aa'}}>$ datapulse history --list</p>
                <p style={{color:'#2d3748',marginTop:8}}>  No scrape jobs found.</p>
                <p style={{color:'#2d3748'}}>  Run your first scrape to see results here.</p>
              </div>
            </div>
          </div>
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th style={{width:40}}>#</th>
                <th>URL</th>
                <th>Type</th>
                <th>Status</th>
                <th style={{textAlign:'right'}}>Rows</th>
                <th>When</th>
                <th style={{textAlign:'center',width:120}}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((job, i) => (
                <React.Fragment key={job.id}>
                  <tr
                    className={`history-row ${expanded === job.id ? 'expanded' : ''}`}
                    onClick={() => toggleExpand(job.id)}
                    style={{ borderLeft: `3px solid ${
                      job.page_type==='table' ? '#00d4aa' :
                      job.page_type==='article' ? '#3b82f6' :
                      job.page_type==='json' ? '#8b5cf6' :
                      job.page_type==='jsonld' ? '#06b6d4' :
                      job.page_type==='amazon_products' || job.page_type==='products' ? '#22c55e' :
                      job.page_type==='flipkart_products' ? '#ec4899' :
                      job.page_type==='linkedin_jobs' ? '#3b82f6' :
                      job.page_type==='pdf' ? '#f97316' : '#f97316'
                    }` }}
                  >
                    <td className="mono" style={{color:'#2d3748'}}>{String(i+1).padStart(3,'0')}</td>
                    <td>
                      <div className="url-cell">
                        <span className="url-text mono">{job.url}</span>
                      </div>
                    </td>
                    <td><span className={`badge ${TYPE_BADGE[job.page_type]||'badge-blue'}`}>{job.page_type||'—'}</span></td>
                    <td><span className={`badge ${job.status==='completed'?'badge-green':'badge-blue'}`}>{job.status}</span></td>
                    <td className="mono" style={{textAlign:'right'}}>{(job.row_count||0).toLocaleString()}</td>
                    <td className="mono" style={{fontSize:12,color:'#4a5568'}}>{relTime(job.scraped_at)}</td>
                    <td>
                      <div className="action-btns">
                        <button className="btn btn-ghost btn-icon" title="View" onClick={() => toggleExpand(job.id)}>
                          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
                        </button>
                        {['csv','excel','json'].map(fmt => (
                          <button key={fmt} className="btn btn-ghost btn-icon" title={`Export ${fmt}`}
                            onClick={e => { e.stopPropagation(); window.open(getExportUrl(job.id, fmt), '_blank'); }}>
                            <span style={{fontSize:9,fontFamily:'JetBrains Mono',fontWeight:600,letterSpacing:'0.04em',color:'#4a5568'}}>
                              {fmt.slice(0,3).toUpperCase()}
                            </span>
                          </button>
                        ))}
                        <button
                          className="btn btn-ghost btn-icon"
                          title="Delete"
                          onClick={e => handleDelete(e, job.id)}
                          disabled={deleting === job.id}
                          style={{color: '#ef4444'}}
                        >
                          {deleting===job.id
                            ? <span className="spinner" style={{width:12,height:12,borderWidth:2}} />
                            : <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a1 1 0 011-1h4a1 1 0 011 1v2"/></svg>
                          }
                        </button>
                      </div>
                    </td>
                  </tr>
                  {expanded === job.id && (
                    <tr className="detail-row">
                      <td colSpan={7}>
                        <div className="detail-panel anim-fadeUp">
                          {!detail[job.id] ? (
                            <div style={{padding:20,textAlign:'center'}}><div className="spinner" style={{margin:'0 auto'}} /></div>
                          ) : (
                            <DetailPanel data={detail[job.id]} jobId={job.id} />
                          )}
                        </div>
                      </td>
                    </tr>
                  )}
                </React.Fragment>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

function DetailPanel({ data, jobId }) {
  const cd = data?.data;
  const pt = data?.page_type;
  const rows = (() => {
    if (pt==='table') return cd?.tables?.[0]?.rows?.slice(0,10) || [];
    if (pt==='article') return (cd?.data?.paragraphs||[]).slice(0,5).map((p,i)=>({'#':i+1,paragraph:p.slice(0,120)+'…'}));
    if (pt==='json') return Array.isArray(cd?.data?.data) ? cd.data.data.slice(0,10) : [];
    if (pt==='amazon_products' || pt==='flipkart_products' || pt==='products') return (cd?.products||[]).slice(0,10);
    if (pt==='linkedin_jobs') return (cd?.jobs||[]).slice(0,10).map((j,i)=>({'#':i+1,title:j.title||'',company:j.company||'',location:j.location||'',salary:j.salary||'—',type:j.employment_type||'—',apply:j.url?.slice(0,50)||'—'}));
    if (pt==='jsonld') return (cd?.items||[]).slice(0,10).map((item,i)=>({'#':i+1,name:item.name||'',type:item['@type']||'',description:(item.description||'').slice(0,80)+'…'}));
    return [];
  })();
  const cols = rows.length > 0 ? Object.keys(rows[0]) : [];

  return (
    <div className="detail-inner">
      <div className="detail-meta">
        <div className="meta-item"><span className="meta-label">URL</span><span className="meta-value mono">{data?.url?.slice(0,60)}…</span></div>
        <div className="meta-item"><span className="meta-label">Type</span><span className={`badge ${TYPE_BADGE[pt]||'badge-blue'}`}>{pt}</span></div>
        <div className="meta-item"><span className="meta-label">Rows</span><span className="meta-value">{(data?.row_count||0).toLocaleString()}</span></div>
      </div>
      {rows.length > 0 && (
        <div className="detail-table-wrap">
          <table className="data-table">
            <thead><tr>{cols.map(c=><th key={c}>{c}</th>)}</tr></thead>
            <tbody>{rows.map((r,i)=><tr key={i}>{cols.map(c=><td key={c} className="mono">{String(r[c]??'—').slice(0,80)}</td>)}</tr>)}</tbody>
          </table>
        </div>
      )}
    </div>
  );
}
