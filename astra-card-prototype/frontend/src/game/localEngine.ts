import { cards, cardsById } from "../data/cards";
import type { Card, GameState, PlayerState, Warrior } from "./types";

const uid = () => Math.random().toString(36).slice(2, 10);
const shuffled = <T,>(values: T[]) => [...values].sort(() => Math.random() - 0.5);

function makePlayer(name: string, faction: "Oathbound" | "Night Court"): PlayerState {
  const deck = shuffled(cards.filter((card) => card.faction === faction).flatMap((card) => [card.id, card.id]));
  return {
    id: uid(), name, faction, health: 30, dharma: 5, karma_debt: 0, karma_timer: 0,
    energy: 0, max_energy: 0, deck, hand: [], board: [], realm: null, oaths: [], oath_rewards: [],
    attacked_this_turn: false, cards_played_this_turn: 0,
  };
}

export function createLocalGame(): GameState {
  const game: GameState = {
    id: uid(), players: [makePlayer("You", "Oathbound"), makePlayer("The Veiled Bot", "Night Court")],
    current_player: 0, turn: 1, phase: "playing", winner: null,
    log: ["The astral gate opens. Your oath is called."],
  };
  for (let index = 0; index < 2; index += 1) {
    for (let draw = 0; draw < 5; draw += 1) drawCard(game, index, false);
  }
  startTurn(game, 0);
  return game;
}

export const cloneGame = (game: GameState): GameState => structuredClone(game);

function drawCard(game: GameState, index: number, writeLog = true) {
  const player = game.players[index];
  const card = player.deck?.pop();
  if (!card) {
    player.health -= 1;
    game.log.push(`${player.name} takes 1 fatigue damage.`);
    checkWinner(game);
    return;
  }
  player.hand.push(card);
  if (writeLog) game.log.push(`${player.name} draws a card.`);
}

function damage(game: GameState, index: number, amount: number, isAttack = false) {
  const target = game.players[index];
  const dealt = amount + (isAttack && target.dharma <= 0 ? 1 : 0);
  target.health -= dealt;
  checkWinner(game);
  return dealt;
}

function addKarma(player: PlayerState, amount: number) {
  player.karma_debt += amount;
  if (!player.karma_timer) player.karma_timer = 2;
}

function buff(player: PlayerState, attack = 0, defense = 0) {
  player.board.forEach((unit) => {
    unit.attack = Math.max(0, unit.attack + attack);
    unit.defense += defense;
  });
}

function applyEffect(game: GameState, index: number, card: Card) {
  const player = game.players[index];
  const enemy = game.players[1 - index];
  const key = card.effect_key;
  if (key === "none") return;
  if (key.startsWith("gain_dharma_")) player.dharma += Number(key.at(-1));
  else if (key === "restore_dharma_if_low" && player.dharma < 5) player.dharma += 1;
  else if (key.startsWith("heal_")) player.health = Math.min(30, player.health + Number(key.at(-1)));
  else if (key.startsWith("damage_enemy_")) damage(game, 1 - index, Number(key.at(-1)));
  else if (key === "fortify_allies_1") buff(player, 0, 1);
  else if (key === "draw_1") drawCard(game, index);
  else if (key === "promise_unbroken") { player.health = Math.min(30, player.health + 3); player.dharma += 2; }
  else if (key.startsWith("self_karma_")) addKarma(player, Number(key.at(-1)));
  else if (key === "enemy_karma_1") addKarma(enemy, 1);
  else if (key.startsWith("drain_dharma_")) enemy.dharma = Math.max(0, enemy.dharma - Number(key.at(-1)));
  else if (key === "weaken_all_1") buff(enemy, -1);
  else if (key === "last_echoes") { damage(game, 1 - index, 3); addKarma(enemy, 1); }
  else if (key === "power_strike_4") { damage(game, 1 - index, 4); player.dharma = Math.max(0, player.dharma - 1); }
  else if (key === "rally_allies_1") buff(player, 1, 1);
  else if (key === "risky_damage_2") { damage(game, 1 - index, 2); addKarma(player, 1); }
  else if (key === "debtcoil") { damage(game, 1 - index, 3); addKarma(enemy, 1); }
  else if (key === "eclipse_cannon") { damage(game, 1 - index, 6); player.dharma = Math.max(0, player.dharma - 1); addKarma(player, 1); }
  else if (key === "rally_attack_2") buff(player, 2);
  else if (["oath_still_waters", "oath_open_hand", "oath_velvet_knives"].includes(key)) {
    player.oaths.push({ key, played_turn: game.turn });
  } else if (key === "oath_shared_dawn") { player.dharma += 1; buff(player, 0, 1); }
  else if (key === "oath_borrowed_hours") { player.energy += 2; addKarma(player, 1); }
  else if (key === "oath_hollow_crown") { damage(game, 1 - index, 3); enemy.dharma = Math.max(0, enemy.dharma - 1); }
  else if (key === "radiant_reckoning") {
    damage(game, 1 - index, 2); player.karma_debt = Math.max(0, player.karma_debt - 1);
    if (!player.karma_debt) player.karma_timer = 0;
  } else if (key === "discard_enemy_1" && enemy.hand.length) enemy.hand.splice(Math.floor(Math.random() * enemy.hand.length), 1);
  else if (key === "karma_burst") damage(game, 1 - index, Math.max(2, enemy.karma_debt));
}

export function playCard(game: GameState, index: number, handIndex: number) {
  assertTurn(game, index);
  const player = game.players[index];
  const card = cardsById.get(player.hand[handIndex]);
  if (!card) throw new Error("Card not found.");
  if (card.cost > player.energy) throw new Error("Not enough energy.");
  if (card.type === "Warrior" && player.board.length >= 5) throw new Error("The battlefield is full.");
  player.energy -= card.cost;
  player.hand.splice(handIndex, 1);
  player.cards_played_this_turn += 1;
  if (card.type === "Warrior") {
    const unit: Warrior = {
      instance_id: uid(), card_id: card.id, name: card.name,
      attack: (card.attack ?? 0) + (player.realm === "realm_bazaar" ? 1 : 0),
      defense: (card.defense ?? 0) + (player.realm === "realm_citadel" ? 1 : 0), ready: false,
    };
    player.board.push(unit);
  } else if (card.type === "Realm") player.realm = card.effect_key;
  applyEffect(game, index, card);
  game.log.push(`${player.name} plays ${card.name}.`);
}

export function attackLeader(game: GameState, index: number, attackerIndex: number) {
  assertTurn(game, index);
  const attacker = game.players[index].board[attackerIndex];
  if (!attacker?.ready) throw new Error("That warrior cannot attack yet.");
  attacker.ready = false;
  game.players[index].attacked_this_turn = true;
  const dealt = damage(game, 1 - index, attacker.attack, true);
  game.log.push(`${attacker.name} strikes for ${dealt}.`);
}

function resolveEnd(game: GameState, index: number) {
  const player = game.players[index];
  player.oaths.forEach((oath) => {
    let fulfilled = false;
    if (oath.key === "oath_still_waters" && !player.attacked_this_turn) fulfilled = true;
    if (oath.key === "oath_open_hand" && player.cards_played_this_turn === 1) fulfilled = true;
    if (oath.key === "oath_velvet_knives" && player.attacked_this_turn) fulfilled = true;
    if (fulfilled) player.oath_rewards.push(oath.key);
    game.log.push(`${player.name}'s oath ${fulfilled ? "is fulfilled; its reward awaits" : "fades"}.`);
  });
  player.oaths = [];
  if (player.karma_debt > 0) {
    player.karma_timer -= 1;
    if (player.karma_timer <= 0) {
      const debt = player.karma_debt;
      player.health -= debt; player.karma_debt = 0; player.karma_timer = 0;
      game.log.push(`Karma comes due: ${player.name} takes ${debt}.`);
      checkWinner(game);
    }
  }
}

function startTurn(game: GameState, index: number) {
  const player = game.players[index];
  player.oath_rewards.forEach((reward) => {
    if (reward === "oath_still_waters") player.dharma += 2;
    if (reward === "oath_open_hand") player.health = Math.min(30, player.health + 4);
    if (reward === "oath_velvet_knives") { drawCard(game, index); addKarma(player, 1); }
    game.log.push(`${player.name} receives a fulfilled oath's reward.`);
  });
  player.oath_rewards = [];
  player.max_energy = Math.min(10, player.max_energy + 1);
  player.energy = player.max_energy;
  player.attacked_this_turn = false;
  player.cards_played_this_turn = 0;
  player.board.forEach((unit) => { unit.ready = true; });
  if (player.realm === "realm_archive") player.dharma += 1;
  if (player.realm === "realm_palace") damage(game, 1 - index, 1);
  if (game.turn > 1) drawCard(game, index);
  game.log.push(`${player.name} begins turn ${game.turn}.`);
}

export function endTurn(game: GameState, index: number) {
  assertTurn(game, index);
  resolveEnd(game, index);
  if (game.phase === "finished") return;
  game.current_player = 1 - index;
  game.turn += 1;
  startTurn(game, game.current_player);
}

export function runBotTurn(game: GameState) {
  if (game.current_player !== 1 || game.phase !== "playing") return;
  let played = true;
  while (played) {
    played = false;
    const bot = game.players[1];
    const affordable = bot.hand.findIndex((id) => {
      const card = cardsById.get(id);
      return card && card.cost <= bot.energy && (card.type !== "Warrior" || bot.board.length < 5);
    });
    if (affordable >= 0) { playCard(game, 1, affordable); played = true; }
  }
  [...game.players[1].board].forEach((_, index) => {
    if (game.players[1].board[index]?.ready && game.phase === "playing") attackLeader(game, 1, index);
  });
  if (game.phase === "playing") endTurn(game, 1);
}

function checkWinner(game: GameState) {
  const dead = game.players.findIndex((player) => player.health <= 0);
  if (dead >= 0) { game.winner = 1 - dead; game.phase = "finished"; game.log.push(`${game.players[game.winner].name} wins.`); }
}

function assertTurn(game: GameState, index: number) {
  if (game.phase !== "playing") throw new Error("The match is over.");
  if (game.current_player !== index) throw new Error("It is not your turn.");
}
