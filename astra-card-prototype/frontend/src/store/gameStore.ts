import { create } from "zustand";
import { attackLeader, cloneGame, createLocalGame, endTurn, playCard, runBotTurn } from "../game/localEngine";
import type { GameState } from "../game/types";

interface GameStore {
  game: GameState;
  notice: string;
  reset: () => void;
  play: (index: number) => void;
  attack: (index: number) => void;
  end: () => void;
  clearNotice: () => void;
}

function attempt(game: GameState, action: (draft: GameState) => void) {
  const draft = cloneGame(game);
  action(draft);
  return draft;
}

export const useGameStore = create<GameStore>((set, get) => ({
  game: createLocalGame(),
  notice: "Your turn. Spend energy, summon warriors, and shape the oath.",
  reset: () => set({ game: createLocalGame(), notice: "A new astral gate opens." }),
  play: (index) => {
    try {
      const cardName = get().game.players[0].hand[index];
      set({ game: attempt(get().game, (draft) => playCard(draft, 0, index)), notice: `Card played: ${cardName}` });
    } catch (error) {
      set({ notice: error instanceof Error ? error.message : "Action failed." });
    }
  },
  attack: (index) => {
    try {
      set({ game: attempt(get().game, (draft) => attackLeader(draft, 0, index)), notice: "Warrior sent against the rival leader." });
    } catch (error) {
      set({ notice: error instanceof Error ? error.message : "Attack failed." });
    }
  },
  end: () => {
    try {
      const next = attempt(get().game, (draft) => {
        endTurn(draft, 0);
        runBotTurn(draft);
      });
      set({ game: next, notice: next.phase === "finished" ? "The match is decided." : "The Night Court has answered. Your turn." });
    } catch (error) {
      set({ notice: error instanceof Error ? error.message : "Could not end turn." });
    }
  },
  clearNotice: () => set({ notice: "" }),
}));
