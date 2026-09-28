import { Link } from 'react-router-dom'
import { openChat } from '../chatEvents'
import BrandLockup from './BrandLockup'
import YaleY from './YaleY'

export default function Footer() {
  return (
    <footer className="footer">
      <div className="footer-inner">
        <div className="footer-brand">
          <span className="brand-mark small" aria-hidden="true">
            <YaleY />
          </span>
          <div>
            <BrandLockup className="footer-lockup" />
            <p className="footer-address">57 Broadway, New Haven, CT</p>
            <p>Officially licensed Yale merchandise</p>
          </div>
        </div>
        <nav className="footer-col" aria-label="Shop">
          <p className="footer-heading">Shop</p>
          <Link to="/products">All products</Link>
          <Link to="/products?category=Hoodies">Hoodies</Link>
          <Link to="/products?category=Crewnecks+%26+sweatshirts">Crewnecks</Link>
          <Link to="/products?category=T-shirts">T-shirts</Link>
        </nav>
        <nav className="footer-col" aria-label="Help">
          <p className="footer-heading">Help</p>
          <button className="footer-link" onClick={openChat}>
            Chat with our assistant
          </button>
          <Link to="/about">About Us</Link>
          <Link to="/login">Log in</Link>
          <Link to="/create-account">Create Account</Link>
        </nav>
      </div>
      <p className="footer-fine">Boola boola! 💙</p>
    </footer>
  )
}
