import { FormEvent, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { LogIn, UserPlus } from 'lucide-react';

import { login, signup, storeToken } from '../api';
import type { AuthResponse, User } from '../types';

interface AuthPageProps {
  mode: 'login' | 'signup';
  onAuthenticated(user: User): Promise<void>;
}

function AuthPage({ mode, onAuthenticated }: AuthPageProps) {
  const navigate = useNavigate();
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState(mode === 'login' ? 'demo@reciperescue.local' : '');
  const [password, setPassword] = useState(mode === 'login' ? 'demo123' : '');
  const [error, setError] = useState<string | null>(null);
  const isSignup = mode === 'signup';

  async function handleAuthResponse(response: AuthResponse) {
    storeToken(response.access_token);
    await onAuthenticated(response.user);
    navigate('/find');
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);

    try {
      const response = isSignup
        ? await signup({ full_name: fullName, email, password })
        : await login({ email, password });
      await handleAuthResponse(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Authentication failed');
    }
  }

  async function handleDemoLogin() {
    setError(null);
    try {
      const response = await login({ email: 'demo@reciperescue.local', password: 'demo123' });
      await handleAuthResponse(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Demo login failed');
    }
  }

  return (
    <section className="auth-page">
      <div className="auth-hero panel">
        <p className="eyebrow">Account</p>
        <h1>{isSignup ? 'Create your Recipe Rescue account.' : 'Welcome back to your pantry.'}</h1>
        <p className="muted">
          Accounts keep pantry stock and custom recipes separate for each user, while the public recipe catalogue remains available to everyone.
        </p>
        <div className="auth-benefits">
          <span>Private pantry inventory</span>
          <span>User-specific custom recipes</span>
          <span>Token-based REST API access</span>
        </div>
      </div>

      <div className="panel auth-card">
        <div className="section-heading">
          <h2>{isSignup ? 'Sign up' : 'Log in'}</h2>
          {isSignup ? <UserPlus size={20} /> : <LogIn size={20} />}
        </div>

        {error && <div className="alert">{error}</div>}

        <form className="stack-form" onSubmit={handleSubmit}>
          {isSignup && (
            <label>
              Full name
              <input required value={fullName} onChange={(event) => setFullName(event.target.value)} />
            </label>
          )}
          <label>
            Email
            <input required type="email" value={email} onChange={(event) => setEmail(event.target.value)} />
          </label>
          <label>
            Password
            <input
              minLength={6}
              required
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
            />
          </label>
          <button className="primary-button" type="submit">
            {isSignup ? 'Create account' : 'Log in'}
          </button>
        </form>

        {!isSignup && (
          <button className="secondary-button full-width-button" onClick={handleDemoLogin} type="button">
            Use demo account
          </button>
        )}

        <p className="auth-switch">
          {isSignup ? 'Already have an account?' : 'Need an account?'}{' '}
          <Link to={isSignup ? '/login' : '/signup'}>{isSignup ? 'Log in' : 'Sign up'}</Link>
        </p>
      </div>
    </section>
  );
}

export default AuthPage;
