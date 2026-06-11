import { ArrowRight, Bolt, CircleGauge, HeartHandshake, Link2, Scale, Shield, Sparkles } from "lucide-react";
import { Link } from "react-router-dom";

const mechanics = [
  { icon: Shield, title: "Dharma", copy: "Your spiritual balance. At zero, enemy attacks strike for bonus damage." },
  { icon: Bolt, title: "Power", copy: "Energy rises each turn. Spend it on warriors, weapons, realms, and schemes." },
  { icon: Scale, title: "Karma", copy: "Borrow strength now, then face delayed damage when the debt comes due." },
  { icon: HeartHandshake, title: "Oaths", copy: "Accept a condition for a future reward. Discipline turns restraint into power." },
];

export function LandingPage() {
  return (
    <div className="landing">
      <section className="hero">
        <div className="hero-glow" />
        <div className="eyebrow"><Sparkles size={15} /> A modern fantasy card duel</div>
        <h1>ASTRA</h1>
        <h2>OATH <span>&</span> KARMA</h2>
        <p>Bind ancient energy to living vows. Command a disciplined order or bargain with the Night Court in a fast 1v1 strategy battle.</p>
        <div className="hero-actions">
          <Link className="primary-button" to="/demo">Start Demo Match <ArrowRight /></Link>
          <Link className="secondary-button" to="/room/create"><Link2 /> Create Room</Link>
          <Link className="text-button" to="/cards">View Cards</Link>
        </div>
        <div className="faction-orbit oath-orbit"><span>OATHBOUND</span><Shield /></div>
        <div className="faction-orbit night-orbit"><Bolt /><span>NIGHT COURT</span></div>
      </section>
      <section className="mechanics-section">
        <div className="section-heading"><span>THE FOUR FORCES</span><h3>Every choice leaves an echo.</h3></div>
        <div className="mechanic-grid">
          {mechanics.map(({ icon: Icon, title, copy }, index) => (
            <article key={title}><span className="number">0{index + 1}</span><Icon /><h4>{title}</h4><p>{copy}</p></article>
          ))}
        </div>
      </section>
      <section className="duel-callout">
        <div><CircleGauge /><span>40 original cards</span></div>
        <div><Link2 /><span>Live room prototype</span></div>
        <div><Bolt /><span>Playable local AI</span></div>
      </section>
    </div>
  );
}
