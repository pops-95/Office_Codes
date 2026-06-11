import { Crown, Gem, ScrollText, Shield, Skull, Sparkles, Swords } from "lucide-react";
import { motion } from "framer-motion";
import type { Card } from "../game/types";

const typeIcons = {
  Warrior: Swords,
  Weapon: Sparkles,
  Oath: ScrollText,
  Curse: Skull,
  Realm: Crown,
};

interface Props {
  card: Card;
  compact?: boolean;
  disabled?: boolean;
  onClick?: () => void;
}

export function CardView({ card, compact = false, disabled = false, onClick }: Props) {
  const Icon = typeIcons[card.type];
  return (
    <motion.button
      type="button"
      className={`game-card ${card.faction === "Night Court" ? "night" : "oath"} rarity-${card.rarity.toLowerCase()} ${compact ? "compact" : ""}`}
      disabled={disabled}
      onClick={onClick}
      whileHover={!disabled ? { y: -7, scale: 1.02 } : undefined}
      whileTap={!disabled ? { scale: 0.98 } : undefined}
      layout
    >
      <div className="card-art">
        <Icon size={compact ? 25 : 38} strokeWidth={1.4} />
        <span className="cost">{card.cost}</span>
        <span className="sigil">{card.faction === "Oathbound" ? "ॐ" : "◈"}</span>
      </div>
      <div className="card-copy">
        <div className="card-heading"><strong>{card.name}</strong><span>{card.type}</span></div>
        {!compact && <p>{card.description}</p>}
        {card.type === "Warrior" && (
          <div className="combat-values">
            <span><Swords size={13} /> {card.attack}</span>
            <span><Shield size={13} /> {card.defense}</span>
          </div>
        )}
        {!compact && <em>“{card.flavor_text}”</em>}
        <span className="rarity"><Gem size={11} /> {card.rarity}</span>
      </div>
    </motion.button>
  );
}
