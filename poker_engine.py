from itertools import combinations
import random
from collections import Counter
from typing import List, Tuple, Dict

RANKS = '23456789TJQKA'
SUITS = 'hdcs'
RANK_MAP = {r: i + 2 for i, r in enumerate(RANKS)}   # '2'->2 ... 'A'->14
SUIT_MAP = {'h': 0, 'd': 1, 'c': 2, 's': 3}
SUIT_SYM = {'h': '♥', 'd': '♦', 'c': '♣', 's': '♠'}
HAND_NAMES = [
    'High Card', 'One Pair', 'Two Pair', 'Three of a Kind',
    'Straight', 'Flush', 'Full House', 'Four of a Kind', 'Straight Flush'
]


def parse_card(s: str) -> Tuple[int, int]:
    s = s.strip()
    rank_str = s[:-1].upper()
    suit_str = s[-1].lower()
    if rank_str not in RANK_MAP:
        raise ValueError(f"Invalid rank: '{rank_str}'. Use 2-9, T, J, Q, K, A.")
    if suit_str not in SUIT_MAP:
        raise ValueError(f"Invalid suit: '{suit_str}'. Use h, d, c, s.")
    return RANK_MAP[rank_str], SUIT_MAP[suit_str]


def parse_cards(card_list: List[str]) -> List[Tuple[int, int]]:
    return [parse_card(c) for c in card_list if c.strip()]


def all_cards() -> List[Tuple[int, int]]:
    return [(r, s) for r in range(2, 15) for s in range(4)]


def score_5(cards: List[Tuple[int, int]]) -> Tuple:
    """Score exactly 5 cards — higher tuple wins."""
    ranks = sorted([c[0] for c in cards], reverse=True)
    suits = [c[1] for c in cards]

    is_flush = len(set(suits)) == 1
    rank_set = set(ranks)
    is_straight = len(rank_set) == 5 and (ranks[0] - ranks[4] == 4)

    # Wheel: A-5-4-3-2
    if rank_set == {14, 2, 3, 4, 5}:
        is_straight = True
        ranks = [5, 4, 3, 2, 1]

    cnt = Counter(ranks)
    freq = sorted(cnt.values(), reverse=True)
    # primary sort: count desc, secondary: rank desc
    ranked = sorted(cnt.keys(), key=lambda r: (cnt[r], r), reverse=True)

    if is_straight and is_flush:
        return (8,) + tuple(ranks)
    if freq[0] == 4:
        return (7,) + tuple(ranked)
    if freq[:2] == [3, 2]:
        return (6,) + tuple(ranked)
    if is_flush:
        return (5,) + tuple(ranks)
    if is_straight:
        return (4,) + tuple(ranks)
    if freq[0] == 3:
        return (3,) + tuple(ranked)
    if freq[:2] == [2, 2]:
        return (2,) + tuple(ranked)
    if freq[0] == 2:
        return (1,) + tuple(ranked)
    return (0,) + tuple(ranks)


def best_hand_score(cards: List[Tuple[int, int]]) -> Tuple:
    """Best 5-card score from 5–7 cards."""
    return max(score_5(list(combo)) for combo in combinations(cards, 5))


def hand_name(score: Tuple) -> str:
    return HAND_NAMES[score[0]]


def simulate(
    hole_cards: List[Tuple[int, int]],
    community_cards: List[Tuple[int, int]],
    num_players: int,
    num_simulations: int = 10_000,
) -> Dict:
    """Monte Carlo win-probability estimation."""
    known = set(tuple(c) for c in hole_cards + community_cards)
    deck = [c for c in all_cards() if c not in known]
    community_needed = 5 - len(community_cards)

    wins = ties = losses = 0
    win_hand_counts: Counter = Counter()

    for _ in range(num_simulations):
        random.shuffle(deck)
        idx = 0

        sim_community = list(community_cards) + deck[idx: idx + community_needed]
        idx += community_needed

        # Deal opponent hole cards
        opponents = []
        for _ in range(num_players - 1):
            opponents.append(deck[idx: idx + 2])
            idx += 2

        my_score = best_hand_score(hole_cards + sim_community)
        best_opp = max(best_hand_score(opp + sim_community) for opp in opponents)

        if my_score > best_opp:
            wins += 1
            win_hand_counts[hand_name(my_score)] += 1
        elif my_score == best_opp:
            ties += 1
        else:
            losses += 1

    win_pct = wins / num_simulations
    tie_pct = ties / num_simulations
    loss_pct = losses / num_simulations
    equity = win_pct + tie_pct * 0.5

    # Winning hand breakdown as % of total wins
    win_breakdown = {}
    if wins > 0:
        for name in HAND_NAMES:
            count = win_hand_counts.get(name, 0)
            if count:
                win_breakdown[name] = round(count / wins * 100, 1)

    # Determine current best hand name from known cards
    all_known = hole_cards + community_cards
    if len(all_known) >= 5:
        current_score = best_hand_score(all_known)
        current_hand = hand_name(current_score)
    elif len(community_cards) == 0:
        current_hand = _preflop_description(hole_cards)
    else:
        current_hand = "—"

    return {
        "win_pct": round(win_pct * 100, 1),
        "tie_pct": round(tie_pct * 100, 1),
        "loss_pct": round(loss_pct * 100, 1),
        "equity": round(equity * 100, 1),
        "current_hand": current_hand,
        "win_breakdown": win_breakdown,
    }


def _preflop_description(hole_cards: List[Tuple[int, int]]) -> str:
    r1, r2 = hole_cards[0][0], hole_cards[1][0]
    suited = hole_cards[0][1] == hole_cards[1][1]
    if r1 == r2:
        return f"Pocket {RANKS[r1-2]}s"
    label = f"{RANKS[max(r1,r2)-2]}{RANKS[min(r1,r2)-2]}"
    return label + (" suited" if suited else " offsuit")


def recommend(
    equity: float,        # 0–1
    pot_size: float,
    call_amount: float,
) -> Dict:
    """
    Return action, bet size, EV, and rationale.
    equity: effective win probability (wins + 0.5*ties)
    """
    pot_odds = call_amount / (pot_size + call_amount) if call_amount > 0 else 0.0

    # EV of calling (relative to folding = 0)
    ev_call = equity * pot_size - (1 - equity) * call_amount if call_amount > 0 else 0.0

    # Bet sizing when acting as aggressor (or raising)
    if equity >= 0.75:
        bet_pct = 1.0          # pot-sized bet
        action = "RAISE / BET"
        reason = "Dominant equity — extract maximum value."
    elif equity >= 0.60:
        bet_pct = 0.75
        action = "BET"
        reason = "Strong equity — value bet 3/4 pot."
    elif equity >= 0.50:
        bet_pct = 0.50
        action = "BET / CALL"
        reason = "Slight edge — half-pot bet or call."
    elif equity >= 0.40:
        bet_pct = 0.33
        action = "CHECK / CALL"
        reason = "Marginal hand — keep pot small, call if cheap."
    else:
        bet_pct = 0.0
        action = "FOLD"
        reason = "Insufficient equity relative to pot odds."

    # Override with pot-odds logic when there is a bet to call
    if call_amount > 0:
        if equity > pot_odds:
            if ev_call > 0 and action == "FOLD":
                action = "CALL"
                reason = (
                    f"Pot odds ({pot_odds*100:.1f}%) < your equity ({equity*100:.1f}%) "
                    "— calling is profitable."
                )
        elif action != "FOLD":
            action = "FOLD"
            bet_pct = 0.0
            reason = (
                f"Pot odds ({pot_odds*100:.1f}%) > your equity ({equity*100:.1f}%) "
                "— fold to this bet."
            )

    bet_size = round(bet_pct * pot_size, 2)

    return {
        "action": action,
        "bet_size": bet_size,
        "bet_pct": round(bet_pct * 100),
        "ev_call": round(ev_call, 2),
        "pot_odds_required": round(pot_odds * 100, 1),
        "reason": reason,
    }
