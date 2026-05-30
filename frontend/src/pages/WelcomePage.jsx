import { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import './WelcomePage.css';

const STATS = [
  { value: '10K+', label: 'URLs Scraped' },
  { value: '4',    label: 'Data Formats' },
  { value: '100%', label: 'Open Source' },
  { value: '<3s',  label: 'Avg. Scrape Time' },
];

const FEATURES = [
  { icon: '⬡', title: 'Smart Detection', desc: 'Auto-detects tables, articles, JSON & PDFs' },
  { icon: '◈', title: 'JS Rendering', desc: 'Playwright fallback for dynamic sites' },
  { icon: '◷', title: 'Job Intelligence', desc: 'Market analysis & skill trending' },
  { icon: '◉', title: 'Multi-Export', desc: 'CSV, Excel, JSON in one click' },
];

export default function WelcomePage() {
  const navigate = useNavigate();
  const canvasRef = useRef(null);
  const [typed, setTyped] = useState('');
  const words = ['websites.', 'APIs.', 'PDFs.', 'job boards.'];
  const [wordIdx, setWordIdx] = useState(0);
  const [charIdx, setCharIdx] = useState(0);
  const [deleting, setDeleting] = useState(false);

  // Typewriter effect
  useEffect(() => {
    const current = words[wordIdx];
    const delay = deleting ? 50 : charIdx === current.length ? 1600 : 80;
    const t = setTimeout(() => {
      if (!deleting && charIdx < current.length) {
        setTyped(current.slice(0, charIdx + 1));
        setCharIdx(c => c + 1);
      } else if (!deleting && charIdx === current.length) {
        setDeleting(true);
      } else if (deleting && charIdx > 0) {
        setTyped(current.slice(0, charIdx - 1));
        setCharIdx(c => c - 1);
      } else {
        setDeleting(false);
        setWordIdx(i => (i + 1) % words.length);
      }
    }, delay);
    return () => clearTimeout(t);
  }, [typed, charIdx, deleting, wordIdx]);

  // Particle canvas
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    let raf;
    const particles = [];
    const resize = () => { canvas.width = window.innerWidth; canvas.height = window.innerHeight; };
    resize();
    window.addEventListener('resize', resize);

    for (let i = 0; i < 80; i++) {
      particles.push({
        x: Math.random() * canvas.width,
        y: Math.random() * canvas.height,
        r: Math.random() * 1.5 + 0.3,
        vx: (Math.random() - 0.5) * 0.3,
        vy: (Math.random() - 0.5) * 0.3,
        alpha: Math.random() * 0.4 + 0.1,
      });
    }

    const draw = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      particles.forEach(p => {
        p.x += p.vx; p.y += p.vy;
        if (p.x < 0) p.x = canvas.width;
        if (p.x > canvas.width) p.x = 0;
        if (p.y < 0) p.y = canvas.height;
        if (p.y > canvas.height) p.y = 0;

        ctx.beginPath();
        ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(0,212,170,${p.alpha})`;
        ctx.fill();
      });

      // Draw connections
      for (let i = 0; i < particles.length; i++) {
        for (let j = i + 1; j < particles.length; j++) {
          const dx = particles[i].x - particles[j].x;
          const dy = particles[i].y - particles[j].y;
          const dist = Math.sqrt(dx * dx + dy * dy);
          if (dist < 100) {
            ctx.beginPath();
            ctx.moveTo(particles[i].x, particles[i].y);
            ctx.lineTo(particles[j].x, particles[j].y);
            ctx.strokeStyle = `rgba(0,212,170,${0.06 * (1 - dist / 100)})`;
            ctx.lineWidth = 0.5;
            ctx.stroke();
          }
        }
      }
      raf = requestAnimationFrame(draw);
    };
    draw();
    return () => { cancelAnimationFrame(raf); window.removeEventListener('resize', resize); };
  }, []);

  return (
    <div className="welcome">
      <canvas ref={canvasRef} className="welcome-canvas" />

      {/* Gradient orbs */}
      <div className="orb orb-1" />
      <div className="orb orb-2" />

      {/* Nav */}
      <nav className="welcome-nav anim-fadeIn">
        <div className="welcome-logo">
          <span className="logo-dp">DP</span>
          <span className="logo-name">DataPulse</span>
        </div>
        <button className="btn btn-outline" onClick={() => navigate('/login')}>
          Sign In →
        </button>
      </nav>

      {/* Hero */}
      <section className="hero">
        <div className="hero-badge anim-fadeUp delay-1">
          <span className="status-dot green" style={{width:6,height:6}} />
          API Ready · FastAPI + Python
        </div>

        <h1 className="hero-title anim-fadeUp delay-2">
          Extract data from any<br />
          <span className="gradient-text">{typed}</span>
          <span className="cursor">|</span>
        </h1>

        <p className="hero-desc anim-fadeUp delay-3">
          Smart web scraping + market intelligence platform.<br />
          Auto-detects page type. Cleans & exports instantly.
        </p>

        <div className="hero-actions anim-fadeUp delay-4">
          <button className="btn btn-primary hero-cta" onClick={() => navigate('/login')}>
            Get Started
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
          </button>
          <button className="btn btn-outline" onClick={() => navigate('/app/scraper')}>
            View Demo
          </button>
        </div>

        {/* Stats */}
        <div className="hero-stats anim-fadeUp delay-5">
          {STATS.map((s, i) => (
            <div key={i} className="stat-item">
              <div className="stat-value">{s.value}</div>
              <div className="stat-label">{s.label}</div>
            </div>
          ))}
        </div>
      </section>

      {/* Features */}
      <section className="features-section">
        <p className="features-overline anim-fadeUp">Capabilities</p>
        <div className="features-grid">
          {FEATURES.map((f, i) => (
            <div key={i} className={`feature-card anim-fadeUp delay-${i + 2}`}>
              <div className="feature-icon">{f.icon}</div>
              <div className="feature-title">{f.title}</div>
              <div className="feature-desc">{f.desc}</div>
            </div>
          ))}
        </div>
      </section>

      {/* CTA bottom */}
      <section className="bottom-cta anim-fadeUp">
        <div className="bottom-cta-inner">
          <h2>Ready to scrape smarter?</h2>
          <button className="btn btn-primary" onClick={() => navigate('/login')}>
            Launch App →
          </button>
        </div>
      </section>
    </div>
  );
}
