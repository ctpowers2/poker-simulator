from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, field_validator
from typing import List, Optional
import os

from poker_engine import parse_cards, simulate, recommend

app = FastAPI(title="Poker EV Calculator")

# ── Request / Response models ─────────────────────────────────────────────────

class AnalyzeRequest(BaseModel):
    hole_cards: List[str]           # ["Ah", "Ks"]
    community_cards: List[str] = [] # up to 5: flop + turn + river
    num_players: int = 2
    pot_size: float = 100.0
    call_amount: float = 0.0
    num_simulations: int = 10_000

    @field_validator("hole_cards")
    @classmethod
    def check_hole(cls, v):
        if len(v) != 2:
            raise ValueError("hole_cards must contain exactly 2 cards.")
        return v

    @field_validator("community_cards")
    @classmethod
    def check_community(cls, v):
        if len(v) > 5:
            raise ValueError("community_cards must contain 0–5 cards.")
        return v

    @field_validator("num_players")
    @classmethod
    def check_players(cls, v):
        if not (2 <= v <= 9):
            raise ValueError("num_players must be between 2 and 9.")
        return v

    @field_validator("pot_size", "call_amount")
    @classmethod
    def check_positive(cls, v):
        if v < 0:
            raise ValueError("pot_size and call_amount must be >= 0.")
        return v


# ── Routes ────────────────────────────────────────────────────────────────────

@app.post("/analyze")
def analyze(req: AnalyzeRequest):
    # Parse cards
    try:
        hole = parse_cards(req.hole_cards)
        community = parse_cards(req.community_cards)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    # Check for duplicate cards
    all_cards = hole + community
    if len(set(all_cards)) != len(all_cards):
        raise HTTPException(status_code=422, detail="Duplicate cards detected.")

    # Validate enough cards remain in deck
    cards_needed = (5 - len(community)) + 2 * (req.num_players - 1)
    cards_available = 52 - len(all_cards)
    if cards_needed > cards_available:
        raise HTTPException(
            status_code=422,
            detail=f"Not enough cards in the deck for {req.num_players} players."
        )

    # Monte Carlo simulation
    sim = simulate(hole, community, req.num_players, req.num_simulations)
    equity = sim["equity"] / 100.0

    # Betting recommendation
    rec = recommend(equity, req.pot_size, req.call_amount)

    # Street label
    street_map = {0: "Pre-Flop", 3: "Flop", 4: "Turn", 5: "River"}
    street = street_map.get(len(community), "Unknown")

    return {
        "street": street,
        "simulation": sim,
        "recommendation": rec,
        "inputs": {
            "hole_cards": req.hole_cards,
            "community_cards": req.community_cards,
            "num_players": req.num_players,
            "pot_size": req.pot_size,
            "call_amount": req.call_amount,
        },
    }


# ── Static frontend ───────────────────────────────────────────────────────────

static_dir = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/")
def index():
    return FileResponse(os.path.join(static_dir, "index.html"))
