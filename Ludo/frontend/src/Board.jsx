import React, { useEffect, useRef, useState } from "react";

const COLORS = ["red", "green", "yellow", "blue"];
const STARTS = { red: 0, green: 13, yellow: 26, blue: 39 };

const TRACK = [
  [6,1],[6,2],[6,3],[6,4],[6,5],[5,6],[4,6],[3,6],[2,6],[1,6],[0,6],[0,7],[0,8],
  [1,8],[2,8],[3,8],[4,8],[5,8],[6,9],[6,10],[6,11],[6,12],[6,13],[6,14],[7,14],[8,14],
  [8,13],[8,12],[8,11],[8,10],[8,9],[9,8],[10,8],[11,8],[12,8],[13,8],[14,8],[14,7],[14,6],
  [13,6],[12,6],[11,6],[10,6],[9,6],[8,5],[8,4],[8,3],[8,2],[8,1],[8,0],[7,0],[6,0],
];

const HOME_PATHS = {
  red: [[7,1],[7,2],[7,3],[7,4],[7,5],[7,6]],
  green: [[1,7],[2,7],[3,7],[4,7],[5,7],[6,7]],
  yellow: [[7,13],[7,12],[7,11],[7,10],[7,9],[7,8]],
  blue: [[13,7],[12,7],[11,7],[10,7],[9,7],[8,7]],
};

const YARDS = {
  red: [[1.8,1.8],[4.2,1.8],[1.8,4.2],[4.2,4.2]],
  green: [[10.8,1.8],[13.2,1.8],[10.8,4.2],[13.2,4.2]],
  yellow: [[10.8,10.8],[13.2,10.8],[10.8,13.2],[13.2,13.2]],
  blue: [[1.8,10.8],[4.2,10.8],[1.8,13.2],[4.2,13.2]],
};

function tokenCell(player, progress, tokenIndex) {
  if (progress === -1) return YARDS[player.color][tokenIndex];
  if (progress <= 51) return TRACK[(STARTS[player.color] + progress) % 52];
  if (progress <= 56) return HOME_PATHS[player.color][progress - 52];
  return [7.5, 7.5];
}

function boardPosition(player, progress) {
  return progress >= 0 && progress <= 51 ? (STARTS[player.color] + progress) % 52 : null;
}

function hasProtectedBlock(room, player, landing) {
  if (landing === null || [0, 8, 13, 21, 26, 34, 39, 47].includes(landing)) return false;
  return room.players.some((opponent) => opponent.id !== player.id
    && opponent.tokens.filter((progress) => boardPosition(opponent, progress) === landing).length >= 2);
}

function legal(room, player, dice, tokenIndex) {
  const progress = player.tokens[tokenIndex];
  if (!dice || progress === 57) return false;
  if (progress === -1 && dice !== 6) return false;
  if (progress >= 0 && progress + dice > 57) return false;
  const destination = progress === -1 ? 0 : progress + dice;
  return !hasProtectedBlock(room, player, boardPosition(player, destination));
}

export default function Board({ room, playerId, now, onMove }) {
  const me = room.players.find((player) => player.id === playerId);
  const selectable = room.started && room.currentPlayerId === playerId && room.dice !== null && now >= (room.diceAvailableAt || 0) * 1000;
  return (
    <div className="ludo-board" aria-label="Ludo game board">
      <div className="yard-bg red-yard" /><div className="yard-bg green-yard" />
      <div className="yard-bg blue-yard" /><div className="yard-bg yellow-yard" />
      {TRACK.map(([row, col], index) => {
        const startColor = COLORS.find((color) => STARTS[color] === index);
        return <div key={`track-${index}`} className={`track-cell ${startColor ? `${startColor}-cell start-cell` : ""}`} style={{ gridRow: row + 1, gridColumn: col + 1 }}>{startColor && "★"}</div>;
      })}
      {Object.entries(HOME_PATHS).flatMap(([color, cells]) => cells.map(([row, col], index) => <div key={`${color}-${index}`} className={`track-cell home-cell ${color}-cell`} style={{ gridRow: row + 1, gridColumn: col + 1 }}>•</div>))}
      <div className="home-center"><span className="tri red-tri" /><span className="tri green-tri" /><span className="tri yellow-tri" /><span className="tri blue-tri" /><b>★</b></div>
      {room.players.flatMap((player) => player.tokens.map((progress, tokenIndex) => {
        const [row, col] = tokenCell(player, progress, tokenIndex);
        const canMove = selectable && player.id === playerId && legal(room, me, room.dice, tokenIndex);
        const stackCount = progress >= 0 && progress < 57 ? player.tokens.filter((item) => item === progress).length : 1;
        const stackLeader = player.tokens.lastIndexOf(progress) === tokenIndex;
        const sameSpotIndex = player.tokens
          .slice(0, tokenIndex)
          .filter((item, previousIndex) => tokenCell(player, item, previousIndex).join() === [row, col].join())
          .length;
        return <Token
          key={`${player.id}-${tokenIndex}`}
          player={player}
          tokenIndex={tokenIndex}
          progress={progress}
          row={row}
          col={col}
          canMove={canMove}
          sameSpotIndex={sameSpotIndex}
          stackCount={stackLeader ? stackCount : 1}
          onMove={onMove}
        />;
      }))}
    </div>
  );
}

function Token({ player, tokenIndex, progress, row, col, canMove, sameSpotIndex, stackCount, onMove }) {
  const previousProgress = useRef(progress);
  const [moving, setMoving] = useState(false);

  useEffect(() => {
    if (previousProgress.current !== progress) {
      setMoving(true);
      const timer = setTimeout(() => setMoving(false), 700);
      previousProgress.current = progress;
      return () => clearTimeout(timer);
    }
    return undefined;
  }, [progress]);

  return (
    <button
      className={`token ${player.color} ${canMove ? "can-move" : ""} ${moving ? "moving" : ""} ${progress === 57 ? "finished" : ""}`}
      style={{
        "--stack": sameSpotIndex,
        left: `${((col + 0.5) / 15) * 100}%`,
        top: `${((row + 0.5) / 15) * 100}%`,
      }}
      onClick={() => canMove && onMove(tokenIndex)}
      disabled={!canMove}
      title={`${player.name}'s token ${tokenIndex + 1}`}
    >
      <span className="token-core"><i>{tokenIndex + 1}</i></span>
      {stackCount > 1 && <b className="stack-badge">{stackCount}</b>}
    </button>
  );
}
