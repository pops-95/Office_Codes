import { Activity, Bot, CircleDot, Clock3, Flame, Heart, RotateCcw, ShieldCheck, Swords, User } from "lucide-react";
import { AnimatePresence, motion } from "framer-motion";
import { cardsById } from "../data/cards";
import type { GameState, PlayerState, Warrior } from "../game/types";
import { CardView } from "./CardView";

interface Props {
  game: GameState;
  playerIndex: number;
  notice?: string;
  connected?: boolean;
  onPlay: (index: number) => void;
  onAttack: (index: number) => void;
  onEnd: () => void;
  onReset?: () => void;
}

function Stats({ player, active }: { player: PlayerState; active: boolean }) {
  return (
    <div className={`stats ${active ? "active" : ""}`}>
      <span><Heart /> {player.health}</span>
      <span><Flame /> {player.energy}/{player.max_energy}</span>
      <span><ShieldCheck /> {player.dharma}</span>
      <span className={player.karma_debt ? "danger" : ""}><Activity /> {player.karma_debt}</span>
      {player.karma_timer > 0 && <span><Clock3 /> {player.karma_timer}</span>}
    </div>
  );
}

function Unit({ unit, canAttack, onAttack }: { unit: Warrior; canAttack: boolean; onAttack?: () => void }) {
  return (
    <motion.button
      layout
      initial={{ scale: 0.75, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      className={`unit ${unit.ready ? "ready" : ""}`}
      disabled={!canAttack}
      onClick={onAttack}
      title={canAttack ? "Attack rival leader" : unit.name}
    >
      <CircleDot className="unit-sigil" />
      <strong>{unit.name}</strong>
      <div><span><Swords /> {unit.attack}</span><span><ShieldCheck /> {unit.defense}</span></div>
      {canAttack && <small>Strike leader</small>}
    </motion.button>
  );
}

function PlayerArea({ player, opponent = false, active }: { player: PlayerState; opponent?: boolean; active: boolean }) {
  return (
    <section className={`player-strip ${opponent ? "opponent" : ""}`}>
      <div className="identity">
        <span className="avatar">{opponent ? <Bot /> : <User />}</span>
        <div><strong>{player.name}</strong><small>{player.faction}</small></div>
      </div>
      <Stats player={player} active={active} />
      <div className="deck-count">{player.deck?.length ?? player.deck_count ?? 0} deck · {player.hand_count ?? player.hand.length} hand</div>
    </section>
  );
}

export function GameBoard({ game, playerIndex, notice, connected = true, onPlay, onAttack, onEnd, onReset }: Props) {
  const player = game.players[playerIndex];
  const opponent = game.players[1 - playerIndex];
  const isTurn = game.current_player === playerIndex && game.phase === "playing" && connected;
  return (
    <div className="board-wrap">
      <div className="board-topline">
        <span>TURN {game.turn}</span>
        <strong>{game.phase === "finished" ? `${game.players[game.winner ?? 0].name} wins` : isTurn ? "YOUR ACTION" : "RIVAL'S ACTION"}</strong>
        <span>{connected ? "ASTRAL LINK ACTIVE" : "AWAITING LINK"}</span>
      </div>
      <PlayerArea player={opponent} opponent active={game.current_player === 1 - playerIndex} />
      <div className="battlefield">
        <div className="realm-label">{opponent.realm ? "Enemy realm active" : "Enemy frontier"}</div>
        <div className="unit-row enemy-row">
          {opponent.board.length ? opponent.board.map((unit) => <Unit key={unit.instance_id} unit={unit} canAttack={false} />) : <span className="empty-row">The rival frontier is quiet</span>}
        </div>
        <div className="field-divider"><span>✦</span></div>
        <div className="unit-row">
          {player.board.length ? player.board.map((unit, index) => (
            <Unit key={unit.instance_id} unit={unit} canAttack={isTurn && unit.ready} onAttack={() => onAttack(index)} />
          )) : <span className="empty-row">Summon a warrior to claim the field</span>}
        </div>
        <div className="realm-label">{player.realm ? "Your realm is shaping the field" : "Your frontier"}</div>
      </div>
      <PlayerArea player={player} active={isTurn} />
      <div className="action-bar">
        <div className="notice">{notice || game.log.at(-1)}</div>
        <button className="end-button" disabled={!isTurn} onClick={onEnd}>End turn</button>
        {onReset && <button className="icon-button" onClick={onReset} title="Restart match"><RotateCcw /></button>}
      </div>
      <div className="hand-label"><span>Your hand</span><small>Click an affordable card to play it</small></div>
      <div className="hand">
        <AnimatePresence>
          {player.hand.map((id, index) => {
            const card = cardsById.get(id);
            return card ? <CardView key={`${id}-${index}`} card={card} compact disabled={!isTurn || card.cost > player.energy} onClick={() => onPlay(index)} /> : null;
          })}
        </AnimatePresence>
      </div>
    </div>
  );
}
