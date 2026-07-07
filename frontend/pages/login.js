import { useState } from 'react';
import { useRouter } from 'next/router';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';

export default function Login() {
  const router = useRouter();
  const [mode, setMode] = useState('login'); // 'login' | 'register'
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      if (mode === 'register') {
        const res = await fetch(`${API_URL}/api/auth/register`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email, password }),
        });
        if (!res.ok) {
          const data = await res.json().catch(() => ({}));
          throw new Error(data.detail || 'Registration failed');
        }
        // Auto-login after register
        setMode('login');
      }

      // Login
      const formData = new URLSearchParams();
      formData.append('username', email);
      formData.append('password', password);

      const res = await fetch(`${API_URL}/api/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: formData.toString(),
      });

      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail || 'Login failed');
      }

      const data = await res.json();
      localStorage.setItem('token', data.access_token);
      router.push('/');
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: '2rem', fontFamily: 'sans-serif', maxWidth: '400px', margin: '4rem auto' }}>
      <h1>JobMatch</h1>
      <h2>{mode === 'login' ? 'Sign In' : 'Create Account'}</h2>

      <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        <input
          type="email"
          placeholder="Email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
          style={{ padding: '0.5rem', fontSize: '1rem', borderRadius: '4px', border: '1px solid #ccc' }}
        />
        <input
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
          style={{ padding: '0.5rem', fontSize: '1rem', borderRadius: '4px', border: '1px solid #ccc' }}
        />

        {error && (
          <div style={{ padding: '0.75rem', backgroundColor: '#ffebee', color: '#c62828', borderRadius: '4px' }}>
            {error}
          </div>
        )}

        <button
          type="submit"
          disabled={loading}
          style={{ padding: '0.75rem', fontSize: '1rem', cursor: 'pointer', backgroundColor: '#1976d2', color: 'white', border: 'none', borderRadius: '4px' }}
        >
          {loading ? 'Loading...' : mode === 'login' ? 'Sign In' : 'Register'}
        </button>
      </form>

      <p style={{ marginTop: '1.5rem', textAlign: 'center' }}>
        {mode === 'login' ? "Don't have an account?" : 'Already have an account?'}{' '}
        <button
          onClick={() => { setMode(mode === 'login' ? 'register' : 'login'); setError(''); }}
          style={{ background: 'none', border: 'none', color: '#1976d2', cursor: 'pointer', fontSize: '1rem', textDecoration: 'underline' }}
        >
          {mode === 'login' ? 'Register' : 'Sign In'}
        </button>
      </p>
    </div>
  );
}
