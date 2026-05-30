import { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { loginUser, registerUser } from '../api/client';
import './LoginPage.css';

const GOOGLE_AUTH_URL = 'http://127.0.0.1:8000/api/auth/google';

export default function LoginPage() {
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const [mode, setMode] = useState('login');
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [focused, setFocused] = useState('');

  useEffect(() => {
    const err = params.get('error');
    if (err === 'google_denied') setError('Google sign-in was cancelled.');
    if (err === 'token_failed') setError('Google sign-in failed. Try again.');
    if (err === 'no_email') setError('Could not get email from Google.');
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!email || !password) { setError('Please fill in all fields.'); return; }
    if (mode === 'register' && !name) { setError('Please enter your name.'); return; }
    setError(''); setLoading(true);
    try {
      let res;
      if (mode === 'login') {
        res = await loginUser(email, password);
      } else {
        res = await registerUser(name, email, password);
      }
      localStorage.setItem('dp_token', res.data.token);
      localStorage.setItem('dp_user', JSON.stringify(res.data.user));
      navigate('/app/scraper');
    } catch (err) {
      setError(err?.response?.data?.detail || 'Something went wrong. Try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleGoogle = () => {
    window.location.href = GOOGLE_AUTH_URL;
  };

  return (
    <div className="login-page">
      <div className="login-bg">
        <div className="login-orb login-orb-1" />
        <div className="login-orb login-orb-2" />
        <div className="login-grid-overlay" />
      </div>

      <button className="login-back anim-fadeIn" onClick={() => navigate('/')}>
        ← Back
      </button>

      <div className="login-card anim-scaleIn">
        <div className="login-header">
          <div className="login-logo"><span>DP</span></div>
          <h1 className="login-title">
            {mode === 'login' ? 'Welcome back' : 'Create account'}
          </h1>
          <p className="login-subtitle">
            {mode === 'login'
              ? 'Sign in to your DataPulse account'
              : 'Start your market intelligence journey'}
          </p>
        </div>

        {/* Google Button */}
        <button className="google-btn" onClick={handleGoogle}>
          <svg width="18" height="18" viewBox="0 0 18 18">
            <path fill="#4285F4" d="M16.51 8H8.98v3h4.3c-.18 1-.74 1.48-1.6 2.04v2.01h2.6a7.8 7.8 0 0 0 2.38-5.88c0-.57-.05-.66-.15-1.18z"/>
            <path fill="#34A853" d="M8.98 17c2.16 0 3.97-.72 5.3-1.94l-2.6-2a4.8 4.8 0 0 1-7.18-2.54H1.83v2.07A8 8 0 0 0 8.98 17z"/>
            <path fill="#FBBC05" d="M4.5 10.52a4.8 4.8 0 0 1 0-3.04V5.41H1.83a8 8 0 0 0 0 7.18l2.67-2.07z"/>
            <path fill="#EA4335" d="M8.98 4.18c1.17 0 2.23.4 3.06 1.2l2.3-2.3A8 8 0 0 0 1.83 5.4L4.5 7.49a4.77 4.77 0 0 1 4.48-3.31z"/>
          </svg>
          Continue with Google
        </button>

        <div className="login-divider"><span>or</span></div>

        {/* Toggle */}
        <div className="login-toggle">
          <button
            className={mode === 'login' ? 'active' : ''}
            onClick={() => { setMode('login'); setError(''); }}
          >Sign In</button>
          <button
            className={mode === 'register' ? 'active' : ''}
            onClick={() => { setMode('register'); setError(''); }}
          >Register</button>
        </div>

        <form onSubmit={handleSubmit} className="login-form">
          {mode === 'register' && (
            <div className={`field-wrap ${focused === 'name' ? 'focused' : ''} ${name ? 'has-value' : ''}`}>
              <label className="field-label">Full name</label>
              <input
                className="field-input" type="text" value={name}
                onChange={e => setName(e.target.value)}
                onFocus={() => setFocused('name')} onBlur={() => setFocused('')}
                placeholder="Your name"
              />
            </div>
          )}
          <div className={`field-wrap ${focused === 'email' ? 'focused' : ''} ${email ? 'has-value' : ''}`}>
            <label className="field-label">Email</label>
            <input
              className="field-input" type="email" value={email}
              onChange={e => setEmail(e.target.value)}
              onFocus={() => setFocused('email')} onBlur={() => setFocused('')}
              placeholder="you@example.com"
            />
          </div>
          <div className={`field-wrap ${focused === 'password' ? 'focused' : ''} ${password ? 'has-value' : ''}`}>
            <label className="field-label">Password</label>
            <input
              className="field-input" type="password" value={password}
              onChange={e => setPassword(e.target.value)}
              onFocus={() => setFocused('password')} onBlur={() => setFocused('')}
              placeholder="••••••••"
            />
          </div>

          {error && <p className="login-error">{error}</p>}

          <button type="submit" className="login-btn" disabled={loading}>
            {loading ? (
              <><span className="spinner" style={{width:16,height:16,borderWidth:2}} />
              {mode === 'login' ? 'Signing in...' : 'Creating account...'}</>
            ) : (
              <>{mode === 'login' ? 'Sign In →' : 'Create Account →'}</>
            )}
          </button>
        </form>

        <button className="demo-btn" onClick={() => navigate('/app/scraper')}>
          Continue without account →
        </button>

        <p className="login-footer">DataPulse v1.0 · Backend at localhost:8000</p>
      </div>
    </div>
  );
}
