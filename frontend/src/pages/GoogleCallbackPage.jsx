import { useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';

export default function GoogleCallbackPage() {
  const navigate = useNavigate();
  const [params] = useSearchParams();

  useEffect(() => {
    const token = params.get('token');
    const name = params.get('name');
    const avatar = params.get('avatar');
    const error = params.get('error');

    if (error) {
      navigate(`/login?error=${error}`);
      return;
    }

    if (token) {
      localStorage.setItem('dp_token', token);
      localStorage.setItem('dp_user', JSON.stringify({
        name: name ? decodeURIComponent(name) : 'User',
        avatar: avatar ? decodeURIComponent(avatar) : ''
      }));
      navigate('/app/scraper');
    } else {
      navigate('/login?error=no_token');
    }
  }, []);

  return (
    <div style={{
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      height: '100vh', background: '#0f1117', color: '#8892a4',
      fontFamily: 'monospace', flexDirection: 'column', gap: 16
    }}>
      <div style={{
        width: 32, height: 32, border: '2px solid #00d4aa',
        borderTopColor: 'transparent', borderRadius: '50%',
        animation: 'spin 0.8s linear infinite'
      }} />
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
      <p>Signing you in with Google...</p>
    </div>
  );
}
