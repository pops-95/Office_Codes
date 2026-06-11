import rawCards from "../../../shared/cards.json";
import type { Card } from "../game/types";

export const cards = rawCards as Card[];
export const cardsById = new Map(cards.map((card) => [card.id, card]));
