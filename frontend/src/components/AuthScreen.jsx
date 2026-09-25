import { useState } from 'react'

const API = 'http://localhost:8000'

export default function AuthScreen({ onAuth }) {
  const [isLogin, setIsLogin] = useState(true)
  const [username, setUsername] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async () => {
    setError('')
    setLoading(true)

    const endpoint = isLogin ? '/auth/login' : '/auth/register'
    const body = isLogin
      ? { username, password }
      : { username, email, password }

    try {
      const res = await fetch(`${API}${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })

      const data = await res.json()

      if (!res.ok) {
        setError(data.detail || 'Something went wrong')
        return
      }

      // Save token and pass to parent
      localStorage.setItem('token', data.access_token)
      localStorage.setItem('username', data.username)
      onAuth(data.access_token, data.username)
    } catch {
      setError('Cannot reach server. Is the backend running?')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-screen">
      <h1>ChatWave</h1>
      <p>{isLogin ? 'Log in to continue' : 'Create your account'}</p>

      <div className="auth-form">
        <input
          type="text"
          placeholder="Username"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSubmit()}
          autoFocus
        />

        {!isLogin && (
          <input
            type="email"
            placeholder="Email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSubmit()}
          />
        )}

        <input
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSubmit()}
        />

        {error && <div className="auth-error">{error}</div>}

        <button onClick={handleSubmit} disabled={loading}>
          {loading ? '...' : isLogin ? 'Log In' : 'Register'}
        </button>

        <div className="auth-toggle">
          {isLogin ? "Don't have an account?" : 'Already have an account?'}
          <span onClick={() => { setIsLogin(!isLogin); setError('') }}>
            {isLogin ? ' Register' : ' Log In'}
          </span>
        </div>
      </div>
    </div>
  )
}
