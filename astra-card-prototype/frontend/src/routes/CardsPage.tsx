import { Search } from "lucide-react";
import { useMemo, useState } from "react";
import { CardView } from "../components/CardView";
import { cards } from "../data/cards";

export function CardsPage() {
  const [faction, setFaction] = useState("All");
  const [type, setType] = useState("All");
  const [query, setQuery] = useState("");
  const shown = useMemo(() => cards.filter((card) =>
    (faction === "All" || card.faction === faction) &&
    (type === "All" || card.type === type) &&
    card.name.toLowerCase().includes(query.toLowerCase())
  ), [faction, type, query]);
  return (
    <div className="page archive-page">
      <div className="page-title"><span>THE CELESTIAL ARCHIVE</span><h1>Card Database</h1><p>Forty prototype cards across two rival traditions.</p></div>
      <div className="filters">
        <label><Search /><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search cards" /></label>
        <select value={faction} onChange={(event) => setFaction(event.target.value)}>
          <option>All</option><option>Oathbound</option><option>Night Court</option>
        </select>
        <select value={type} onChange={(event) => setType(event.target.value)}>
          <option>All</option><option>Warrior</option><option>Weapon</option><option>Oath</option><option>Curse</option><option>Realm</option>
        </select>
        <strong>{shown.length} cards</strong>
      </div>
      <div className="card-grid">{shown.map((card) => <CardView key={card.id} card={card} />)}</div>
    </div>
  );
}
