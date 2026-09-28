import { useState, type FormEvent } from 'react'
import { Link, Navigate, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth'

export default function Login() {
  const { user, login } = useAuth()
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  if (user) return <Navigate to="/" replace />

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setError(null)
    setBusy(true)
    try {
      await login(email, password)
      navigate('/')
    } catch (err) {
      setError((err as Error).message)
      setPassword('')
    } finally {
      setBusy(false)
    }
  }

  return (
    <section className="section form-page reveal">
      <p className="eyebrow">Welcome back</p>
      <h1>Log in</h1>
      <p className="muted">Pick up your saved chat and recommendations.</p>
      <form className="form" onSubmit={handleSubmit}>
        <label>
          Email
          <input
            type="email"
            autoComplete="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
        </label>
        <label>
          Password
          <input
            type="password"
            autoComplete="current-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </label>
        {error && <p className="error" role="alert">{error}</p>}
        <button type="submit" className="button" disabled={busy}>
          {busy ? 'Logging in…' : 'Log in'}
        </button>
      </form>
      <p>
        New here? <Link to="/create-account">Create an account</Link>
      </p>
    </section>
  )
}
