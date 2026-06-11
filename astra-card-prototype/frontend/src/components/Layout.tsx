import { Menu, Sparkles, X } from "lucide-react";
import { useState } from "react";
import { Link, NavLink, Outlet } from "react-router-dom";

export function Layout() {
  const [open, setOpen] = useState(false);
  const links = [["/", "Home"], ["/demo", "Demo Match"], ["/cards", "Card Archive"], ["/room/create", "Online Room"]];
  return (
    <div className="app-shell">
      <header className="topbar">
        <Link className="brand" to="/" onClick={() => setOpen(false)}>
          <span className="brand-mark"><Sparkles size={18} /></span>
          <span>ASTRA <small>OATH & KARMA</small></span>
        </Link>
        <button className="menu-button" onClick={() => setOpen(!open)} aria-label="Toggle navigation">
          {open ? <X /> : <Menu />}
        </button>
        <nav className={open ? "nav open" : "nav"}>
          {links.map(([to, label]) => (
            <NavLink key={to} to={to} onClick={() => setOpen(false)}>{label}</NavLink>
          ))}
        </nav>
      </header>
      <main><Outlet /></main>
      <footer>Original prototype universe · No final artwork · Built for playtesting</footer>
    </div>
  );
}
