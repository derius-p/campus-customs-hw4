import { useEffect, useState } from 'react'
import { Link, NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth'
import { openChat } from '../chatEvents'
import BrandLockup from './BrandLockup'
import YaleY from './YaleY'

const MAIN_LINKS = [
  { to: '/', label: 'Home', end: true },
  { to: '/products', label: 'Shop', end: false },
  { to: '/about', label: 'About Us', end: false },
]

export default function NavBar() {
  const { user, loading, logout } = useAuth()
  const navigate = useNavigate()
  const [scrolled, setScrolled] = useState(false)

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 8)
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => window.removeEventListener('scroll', onScroll)
  }, [])

  async function handleLogout() {
    await logout()
    navigate('/')
  }

  return (
    <header className={`site-header ${scrolled ? 'scrolled' : ''}`}>
      <div className="announcement">
        <span>Officially licensed Yale apparel</span>
        <span className="dot">•</span>
        <span>57 Broadway, New Haven</span>
        <span className="dot">•</span>
        <button className="announcement-link" onClick={openChat}>
          Questions? Ask our assistant
        </button>
      </div>
      <div className="navbar">
        <Link to="/" className="brand" aria-label="Yale Bulldog Blue by Campus Customs, home">
          <span className="brand-mark" aria-hidden="true">
            <YaleY />
          </span>
          <BrandLockup />
        </Link>
        <nav className="nav-links" aria-label="Main">
          {MAIN_LINKS.map((link) => (
            <NavLink key={link.to} to={link.to} end={link.end}>
              {link.label}
            </NavLink>
          ))}
        </nav>
        <nav className="nav-account" aria-label="Account">
          {loading ? null : user ? (
            <>
              <span className="nav-greeting">Hi, {user.first_name}</span>
              <button className="nav-cta" onClick={handleLogout}>
                Log out
              </button>
            </>
          ) : (
            <>
              <NavLink to="/login">Log in</NavLink>
              <NavLink to="/create-account" className="nav-cta">
                Create Account
              </NavLink>
            </>
          )}
        </nav>
      </div>
    </header>
  )
}
