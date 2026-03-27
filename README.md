# Poker EV Calculator

A real-time poker expected value calculator. Enter your hole cards and community cards, and get instant win probability, equity, and bet sizing recommendations powered by Monte Carlo simulation.

**Live:** https://poker-ev-calculator-production.up.railway.app

## Features

- **Monte Carlo simulation** — 10,000 hand simulations for accurate win/tie/loss probabilities
- **Tap-to-select cards** — visual 52-card grid, no dropdowns
- **Auto-calculates** — results update automatically as you enter cards or change pot size
- **Bet sizing recommendations** — fold/call/bet/raise with exact dollar amounts based on pot odds and equity
- **Winning hand breakdown** — shows which hand types (pair, flush, etc.) your wins come from
- **Pot builder** — quick-tap +0.5/+1/+5/+10/+25/+50/+100 buttons for fast pot entry, works for both pot size and amount to call
- **Hand history** — last 5 hands with mini card visuals and results
- **Mobile optimised** — designed for use on a phone at the table

## Stack

- **Backend:** Python, FastAPI, uvicorn
- **Simulation:** Pure Python Monte Carlo (no external poker libraries)
- **Frontend:** Vanilla HTML/CSS/JS — no frameworks
- **Hosting:** Railway

## Running locally

```bash
pip install -r requirements.txt
uvicorn api:app --reload --port 8000
```

Then open http://localhost:8000.

## How it works

1. Select your hole cards and set the current street (Pre-Flop / Flop / Turn / River)
2. Add community cards if applicable
3. Enter the total pot size and amount to call
4. Results calculate automatically — win %, equity, and recommended action

### Recommendation logic

| Equity | Action | Bet size |
|--------|--------|----------|
| ≥ 75% | RAISE / BET | 100% pot |
| 60–75% | BET | 75% pot |
| 50–60% | BET / CALL | 50% pot |
| 40–50% | CHECK / CALL | 33% pot |
| < 40% | FOLD | — |

Pot odds override the above — if the required equity to call profitably exceeds your actual equity, the recommendation flips to FOLD.
