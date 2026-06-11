import { GameBoard } from "../components/GameBoard";
import { useGameStore } from "../store/gameStore";

export function DemoPage() {
  const { game, notice, play, attack, end, reset } = useGameStore();
  return (
    <div className="game-page">
      <div className="game-heading"><div><span>LOCAL PROVING GROUND</span><h1>Oathbound vs. Night Court</h1></div><p>The bot plays affordable cards and attacks whenever it can.</p></div>
      <GameBoard game={game} playerIndex={0} notice={notice} onPlay={play} onAttack={attack} onEnd={end} onReset={reset} />
    </div>
  );
}
