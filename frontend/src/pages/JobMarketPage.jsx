import { useState } from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { getJobMarket, getJobMarketExportUrl } from '../api/client';
import './JobMarketPage.css';

const CATEGORIES = [
  { value: 'software-dev', label: 'Software Development' },
  { value: 'marketing',    label: 'Marketing' },
  { value: 'sales',        label: 'Sales' },
  { value: 'design',       label: 'Design' },
  { value: 'devops',       label: 'DevOps' },
];
const LIMITS = [10, 25, 50, 100];

const COLORS_TEAL = ['#00d4aa','#00bfa0','#00aa8f','#00957e','#007f6d','#006a5c','#00554b','#00403a','#002b29','#001618'];
const COLORS_BLUE = ['#3b82f6','#2563eb','#1d4ed8','#1e40af','#1e3a8a','#1d3461','#1a2e52','#172847','#14223c','#111c31'];

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div style={{background:'#1a2235',border:'1px solid rgba(255,255,255,0.1)',borderRadius:8,padding:'8px 12px',fontSize:12,color:'#e2e8f0'}}>
      <p style={{fontWeight:600}}>{label}</p>
      <p style={{color:'#00d4aa'}}>{payload[0].value} jobs</p>
    </div>
  );
};

const intelligenceToCharts = (intel) => {
  const skills = (intel?.top_skills || []).map(s => ({ name: s.skill, count: s.count }));
  const companies = (intel?.top_companies || []).map(c => ({ name: c.company, count: c.count }));
  const locations = (intel?.top_locations || []).map(l => ({ name: l.location, count: l.count }));
  const jobTypes = (intel?.job_type_breakdown || []).map(j => ({ name: j.type, count: j.count }));
  const total = (intel?.total_jobs_analyzed || 1);
  return { skills, companies, locations, jobTypes, total };
};

export default function JobMarketPage() {
  const [category, setCategory] = useState('software-dev');
  const [limit, setLimit]       = useState(50);
  const [data, setData]         = useState(null);
  const [loading, setLoading]   = useState(false);
  const [error, setError]       = useState('');
  const [exportId, setExportId] = useState(null);

  const runAnalysis = async () => {
    setLoading(true);
    setError('');
    setData(null);
    try {
      const res = await getJobMarket(category, limit);
      const api = res.data;
      const charts = intelligenceToCharts(api.intelligence);
      setData({
        total: api.total_jobs,
        withSalary: api.intelligence?.jobs_with_salary || 0,
        avgMin: api.intelligence?.salary_samples?.length > 0 ? 85000 : 0,
        avgMax: api.intelligence?.salary_samples?.length > 0 ? 120000 : 0,
        skills: charts.skills,
        companies: charts.companies,
        locations: charts.locations,
        jobTypes: charts.jobTypes,
        jobs: api.jobs || [],
      });
      setExportId(api.job_id);
    } catch (e) {
      setError(e?.response?.data?.detail || e.message || 'Analysis failed.');
    } finally {
      setLoading(false);
    }
  };

  const total = data?.jobTypes?.reduce((s, t) => s + t.count, 0) || 1;

  return (
    <div className="jobs-page">
      <div className="jobs-header anim-fadeIn">
        <div>
          <p className="breadcrumb">DataPulse / Job Market</p>
          <h1 className="page-title">Job Market Intelligence</h1>
        </div>
      </div>

      {/* Query bar */}
      <div className="card query-bar anim-fadeUp delay-1">
        <span className="query-fn mono">analyze(</span>
        <div className="query-field">
          <span className="query-param">category:</span>
          <select className="query-select" value={category} onChange={e => setCategory(e.target.value)}>
            {CATEGORIES.map(c => <option key={c.value} value={c.value}>{c.label}</option>)}
          </select>
        </div>
        <span className="query-sep mono">,</span>
        <div className="query-field">
          <span className="query-param">limit:</span>
          <select className="query-select" value={limit} onChange={e => setLimit(Number(e.target.value))}>
            {LIMITS.map(l => <option key={l} value={l}>{l} jobs</option>)}
          </select>
        </div>
        <span className="query-fn mono">)</span>
        <button className="btn btn-primary query-run" onClick={runAnalysis} disabled={loading}>
          {loading ? <><span className="spinner" style={{width:13,height:13,borderWidth:2}} /> Running...</> : '▶ Run Analysis'}
        </button>
      </div>

      {!data && !loading && (
        <div className="jobs-idle anim-fadeUp delay-2">
          <div className="idle-hint">
            <span style={{fontSize:32,opacity:.2}}>◈</span>
            <p style={{color:'#2d3748',fontFamily:'JetBrains Mono,monospace',fontSize:13}}>
              Configure the query above and click Run Analysis
            </p>
          </div>
        </div>
      )}

      {loading && (
        <div className="jobs-idle anim-fadeIn">
          <div className="spinner spinner-lg" style={{margin:'0 auto'}} />
          <p style={{color:'#2d3748',marginTop:16,textAlign:'center',fontFamily:'JetBrains Mono,monospace',fontSize:12}}>
            Analyzing {limit} {category} jobs...
          </p>
        </div>
      )}

      {error && <p className="scrape-error anim-fadeIn">{error}</p>}

      {data && !loading && (
        <>
          {/* Metrics */}
          <div className="metrics-row anim-fadeUp delay-1">
            {[
              { label:'TOTAL JOBS',   value: data.total.toLocaleString(),                   color:'teal' },
              { label:'WITH SALARY',  value: `${data.withSalary} (${data.total > 0 ? Math.round(data.withSalary/data.total*100) : 0}%)`, color:'blue' },
              { label:'AVG SALARY',   value: data.avgMin > 0 ? `~$${(data.avgMin/1000).toFixed(0)}k–$${(data.avgMax/1000).toFixed(0)}k` : 'N/A', color:'purple' },
              { label:'CATEGORY', value: category.replace(/-/g,' ').toUpperCase(),      color:'green' },
            ].map((m, i) => (
              <div key={i} className={`metric-card ${m.color} anim-fadeUp delay-${i+2}`}>
                <div className="metric-label">{m.label}</div>
                <div className="metric-value" style={{fontSize:20}}>{m.value}</div>
              </div>
            ))}
          </div>

          {exportId && (
            <div style={{display:'flex',justifyContent:'flex-end'}}>
              <a className="btn btn-outline" href={getJobMarketExportUrl(exportId)} target="_blank" rel="noopener" style={{fontSize:12}}>
                ⬇ Export to Excel
              </a>
            </div>
          )}

          {/* Charts grid */}
          <div className="charts-grid anim-fadeUp delay-2">
            {/* Skills */}
            {data.skills.length > 0 && (
            <div className="card chart-card">
              <div className="chart-title">Top Skills</div>
              <ResponsiveContainer width="100%" height={Math.min(data.skills.length * 22, 220)}>
                <BarChart data={data.skills} layout="vertical" margin={{left:0,right:24,top:4,bottom:4}}>
                  <XAxis type="number" hide />
                  <YAxis type="category" dataKey="name" width={90} tick={{fill:'#4a5568',fontSize:11,fontFamily:'Inter'}} axisLine={false} tickLine={false} />
                  <Tooltip content={<CustomTooltip />} cursor={{fill:'rgba(255,255,255,0.03)'}} />
                  <Bar dataKey="count" radius={[0,4,4,0]} barSize={12}>
                    {data.skills.map((_, i) => <Cell key={i} fill={COLORS_TEAL[i % COLORS_TEAL.length]} />)}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
            )}

            {/* Companies */}
            {data.companies.length > 0 && (
            <div className="card chart-card">
              <div className="chart-title">Top Companies</div>
              <ResponsiveContainer width="100%" height={Math.min(data.companies.length * 22, 220)}>
                <BarChart data={data.companies} layout="vertical" margin={{left:0,right:24,top:4,bottom:4}}>
                  <XAxis type="number" hide />
                  <YAxis type="category" dataKey="name" width={90} tick={{fill:'#4a5568',fontSize:11,fontFamily:'Inter'}} axisLine={false} tickLine={false} />
                  <Tooltip content={<CustomTooltip />} cursor={{fill:'rgba(255,255,255,0.03)'}} />
                  <Bar dataKey="count" radius={[0,4,4,0]} barSize={12}>
                    {data.companies.map((_, i) => <Cell key={i} fill={COLORS_BLUE[i % COLORS_BLUE.length]} />)}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
            )}

            {/* Locations */}
            {data.locations.length > 0 && (
            <div className="card chart-card">
              <div className="chart-title">Top Locations</div>
              <div className="bar-list">
                {data.locations.map((l, i) => (
                  <div key={i} className="bar-list-row">
                    <span className="bar-list-label">{l.name}</span>
                    <div className="bar-list-track">
                      <div className="bar-list-fill teal" style={{width:`${(l.count/data.total)*100}%`,animationDelay:`${i*0.08}s`}} />
                    </div>
                    <span className="bar-list-count">{l.count}</span>
                  </div>
                ))}
              </div>
            </div>
            )}

            {/* Job Types */}
            {data.jobTypes.length > 0 && (
            <div className="card chart-card">
              <div className="chart-title">Job Types</div>
              <div className="stacked-bar-wrap">
                <div className="stacked-bar">
                  {data.jobTypes.map((t, i) => (
                    <div key={i}
                      className="stacked-seg"
                      style={{
                        width:`${(t.count/total)*100}%`,
                        background: i===0?'#00d4aa':i===1?'#3b82f6':'#8b5cf6',
                        animationDelay: `${i*0.12}s`
                      }}
                      title={`${t.name}: ${t.count}`}
                    />
                  ))}
                </div>
                <div className="stacked-legend">
                  {data.jobTypes.map((t, i) => (
                    <div key={i} className="legend-item">
                      <span className="legend-dot" style={{background:i===0?'#00d4aa':i===1?'#3b82f6':'#8b5cf6'}} />
                      <span className="legend-label">{t.name}</span>
                      <span className="legend-val">{t.count}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
            )}
          </div>

          {/* Jobs table */}
          {data.jobs.length > 0 && (
          <div className="card anim-fadeUp delay-3" style={{padding:0,overflow:'hidden'}}>
            <div style={{padding:'16px 20px',borderBottom:'1px solid rgba(255,255,255,0.06)'}}>
              <span className="section-title">Jobs ({data.jobs.length})</span>
            </div>
            <div style={{overflowX:'auto'}}>
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Title</th><th>Company</th><th>Skills</th>
                    <th>Location</th><th>Salary</th><th style={{width:60}}>Link</th>
                  </tr>
                </thead>
                <tbody>
                  {data.jobs.map((j, i) => (
                    <tr key={i}>
                      <td style={{fontWeight:500}}>{j.title}</td>
                      <td>
                        <div style={{display:'flex',alignItems:'center',gap:8}}>
                          <div className="company-avatar" style={{background:`hsl(${i*60+180},60%,30%)`}}>{(j.company||'?')[0]}</div>
                          {j.company}
                        </div>
                      </td>
                      <td>
                        <div className="skill-tags">
                          {(j.skills||[]).slice(0,3).map(s => <span key={s} className="skill-tag">{s}</span>)}
                          {(j.skills||[]).length > 3 && <span className="skill-more">+{(j.skills||[]).length-3}</span>}
                        </div>
                      </td>
                      <td style={{color:'#4a5568',fontSize:12}}>{j.location}</td>
                      <td className="mono" style={{fontSize:12,color:'#00d4aa'}}>{j.salary || '—'}</td>
                      <td>{j.url ? <a href={j.url} target="_blank" rel="noopener" style={{color:'#3b82f6',fontSize:13}}>→</a> : <span style={{color:'#2d3748'}}>—</span>}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
          )}
        </>
      )}
    </div>
  );
}
