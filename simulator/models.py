import enum
import random
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

class CardType(enum.Enum):
    GHOST = "GHOST"
    SPECIFIC_PROTECTION = "SPECIFIC_PROTECTION"
    GENERAL_PROTECTION = "GENERAL_PROTECTION"
    UTILITY = "UTILITY"

@dataclass
class Card:
    type: CardType
    name: str
    ghost_target: Optional[str] = None  # For specific protection
    
    def __repr__(self):
        return f"Card({self.name})"
    
    def __eq__(self, other):
        if not isinstance(other, Card): return False
        return self.type == other.type and self.name == other.name and self.ghost_target == other.ghost_target

class Player:
    def __init__(self, pid: int, strategy_name: str, strategy: Any):
        self.pid = pid
        self.strategy_name = strategy_name
        self.strategy = strategy
        self.hand: List[Card] = []
        self.is_alive = True
        self.owes_draws = 1

    def remove_card(self, card: Card):
        if card in self.hand:
            self.hand.remove(card)
            
    def has_card(self, name: str) -> bool:
        return any(c.name == name for c in self.hand)

class GameState:
    def __init__(self, num_players: int):
        self.num_players = num_players
        self.players: List[Player] = []
        self.deck: List[Card] = []
        self.discard_pile: List[Card] = []
        self.turn_index = 0
        self.direction = 1
        self.ghosts_in_game = num_players - 1
        
        # Metrics
        self.metrics = {
            "game_length_turns": 0,
            "death_turns": [],
            "ghost_encounters": 0,
            "ghosts_survived": 0,
            "ghosts_removed": 0,
            "ghost_events": [],
            "utility_played": {},
            "protection_used": 0,
            "general_protection_used": 0,
            "hand_sizes": [],
            "trades_attempted": 0,
            "trades_successful": 0
        }
        
    def get_current_player(self) -> Player:
        return self.players[self.turn_index]
        
    def next_turn(self):
        # find next alive player
        for _ in range(self.num_players):
            self.turn_index = (self.turn_index + self.direction) % self.num_players
            if self.players[self.turn_index].is_alive:
                self.players[self.turn_index].owes_draws = 1
                break

    def get_alive_players(self) -> List[Player]:
        return [p for p in self.players if p.is_alive]
