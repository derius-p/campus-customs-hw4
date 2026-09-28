import { Link } from 'react-router-dom'
import { openChat } from '../chatEvents'

export default function About() {
  return (
    <section className="section about">
      <div className="about-intro reveal">
        <p className="eyebrow">About Us</p>
        <h1>A New Haven shop for the whole Yale family.</h1>
        <p className="about-lede">
          Campus Customs runs Yale Bulldog Blue, a shop for officially licensed Yale apparel. You'll find us in the
          commercial heart of Yale at 57 Broadway, and online for everyone who can't stop by in person.
        </p>
      </div>
      <div className="about-grid">
        <div className="about-card reveal" style={{ '--i': 0 } as React.CSSProperties}>
          <h3>For every corner of campus</h3>
          <p>
            The residential colleges, graduate and professional schools, varsity and club sports, and the parents,
            grandparents, and siblings who wear the blue with pride.
          </p>
          <Link to="/products" className="section-link">
            Browse the collection →
          </Link>
        </div>
        <div className="about-card reveal" style={{ '--i': 1 } as React.CSSProperties}>
          <h3>Help when you want it</h3>
          <p>
            Have a question about sizing, stock, or finding the right gift? Our assistant checks what's on the shelves
            right now and can suggest alternatives when a size is sold out.
          </p>
          <button className="link-button section-link" onClick={openChat}>
            Chat with our assistant →
          </button>
        </div>
        <div className="about-card visit reveal" style={{ '--i': 2 } as React.CSSProperties}>
          <h3>Visit us</h3>
          <p className="about-address">
            57 Broadway
            <br />
            New Haven, CT
          </p>
        </div>
      </div>
    </section>
  )
}
