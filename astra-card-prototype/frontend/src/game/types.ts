export type Faction = "Oathbound" | "Night Court";
export type CardType = "Warrior" | "Weapon" | "Oath" | "Curse" | "Realm";
export type Rarity = "Common" | "Uncommon" | "Rare" | "Epic" | "Legendary";

export interface Card {
  id: string;
  name: string;
  faction: Faction;
  type: CardType;
  cost: number;
  attack: number | null;
  defense: number | null;
  rarity: Rarity;
  description: string;
  effect_key: string;
  flavor_text: string;
}

export interface Warrior {
  instance_id: string;
  card_id: string;
  name: string;
  attack: number;
  defense: number;
  ready: boolean;
}

export interface PlayerState {
  id: string;
  name: string;
  faction: Faction;
  health: number;
  dharma: number;
  karma_debt: number;
  karma_timer: number;
  energy: number;
  max_energy: number;
  deck?: string[];
  deck_count?: number;
  hand: string[];
  hand_count?: number;
  board: Warrior[];
  realm: string | null;
  oaths: { key: string; played_turn: number }[];
  oath_rewards: string[];
  attacked_this_turn: boolean;
  cards_played_this_turn: number;
}

export interface GameState {
  id: string;
  players: [PlayerState, PlayerState];
  current_player: number;
  turn: number;
  phase: "playing" | "finished";
  winner: number | null;
  log: string[];
}
