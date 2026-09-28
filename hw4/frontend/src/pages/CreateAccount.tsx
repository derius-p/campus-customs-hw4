import { useState, type FormEvent } from 'react'
import { Link, Navigate, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth'

const MIN_PASSWORD = 8

export default function CreateAccount() {
  const { user, register } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState({ first_name: '', last_name: '', email: '', password: '', confirm: '' })
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  if (user) return <Navigate to="/" replace />

  const update = (field: keyof typeof form) => (e: React.ChangeEvent<HTMLInputElement>) =>
    setForm({ ...form, [field]: e.target.value })

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setError(null)
    if (form.password.length < MIN_PASSWORD) {
      setError(`Password must be at least ${MIN_PASSWORD} characters.`)
      return
    }
    if (form.password !== form.confirm) {
      setError("Passwords don't match.")
      return
    }
    setBusy(true)
    try {
      const { confirm: _confirm, ...data } = form
      await register(data)
      navigate('/')
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <section className="section form-page reveal">
      <p className="eyebrow">Join the Bulldog family</p>
      <h1>Create Account</h1>
      <p className="muted">Save your chats with our assistant and pick up where you left off.</p>
      <form className="form" onSubmit={handleSubmit}>
        <div className="form-row">
          <label>
            First name
            <input autoComplete="given-name" value={form.first_name} onChange={update('first_name')} required />
          </label>
          <label>
            Last name
            <input autoComplete="family-name" value={form.last_name} onChange={update('last_name')} required />
          </label>
        </div>
        <label>
          Email
          <input type="email" autoComplete="email" value={form.email} onChange={update('email')} required />
        </label>
        <label>
          Password
          <input
            type="password"
            autoComplete="new-password"
            value={form.password}
            onChange={update('password')}
            minLength={MIN_PASSWORD}
            maxLength={128}
            required
          />
          <span className="hint">At least {MIN_PASSWORD} characters. Avoid common passwords.</span>
        </label>
        <label>
          Confirm password
          <input type="password" autoComplete="new-password" value={form.confirm} onChange={update('confirm')} required />
        </label>
        {error && <p className="error" role="alert">{error}</p>}
        <button type="submit" className="button" disabled={busy}>
          {busy ? 'Creating account…' : 'Create Account'}
        </button>
      </form>
      <p>
        Already have an account? <Link to="/login">Log in</Link>
      </p>
    </section>
  )
}
