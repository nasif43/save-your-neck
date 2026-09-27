import random
from typing import List, Optional, Tuple
from simulator.models import GameState, Card, CardType, Player

class BaseStrategy:
    def choose_action(self, state: GameState, player: Player, valid_actions: List[str]) -> str:
        raise NotImplementedError

    def respond_to_trade(self, state: GameState, player: Player, requested_protection: str) -> Optional[Card]:
        raise NotImplementedError
        
    def choose_target(self, state: GameState, player: Player, valid_targets: List[Player]) -> Player:
        raise NotImplementedError
        
    def choose_ghost_placement(self, state: GameState, player: Player, deck_size: int) -> int:
        raise NotImplementedError
        
    def choose_card_to_discard(self, state: GameState, player: Player) -> Card:
        raise NotImplementedError

    def play_nope(self, state: GameState, player: Player, utility: str, user: Player) -> bool:
        return False

class RandomStrategy(BaseStrategy):
    def choose_action(self, state: GameState, player: Player, valid_actions: List[str]) -> str:
        # randomly play a utility or draw
        if random.random() < 0.5 and len(valid_actions) > 1:
            actions = [a for a in valid_actions if a != "DRAW"]
            return random.choice(actions)
        return "DRAW"

    def respond_to_trade(self, state: GameState, player: Player, requested_protection: str) -> Optional[Card]:
        protections = [c for c in player.hand if c.type == CardType.GENERAL_PROTECTION or (c.type == CardType.SPECIFIC_PROTECTION and c.name == requested_protection)]
        if protections and random.random() < 0.5:
            return random.choice(protections)
        return None

    def choose_target(self, state: GameState, player: Player, valid_targets: List[Player]) -> Player:
        return random.choice(valid_targets)

    def choose_ghost_placement(self, state: GameState, player: Player, deck_size: int) -> int:
        return random.randint(0, deck_size)

    def choose_card_to_discard(self, state: GameState, player: Player) -> Card:
        return random.choice(player.hand)

    def play_nope(self, state: GameState, player: Player, utility: str, user: Player) -> bool:
        return random.random() < 0.2

class CowardStrategy(BaseStrategy):
    # Plays skip immediately, hoards protection, never trades
    def choose_action(self, state: GameState, player: Player, valid_actions: List[str]) -> str:
        if "Skip" in valid_actions:
            return "Skip"
        if "Peek" in valid_actions:
            return "Peek"
        return "DRAW"

    def respond_to_trade(self, state: GameState, player: Player, requested_protection: str) -> Optional[Card]:
        return None

    def choose_target(self, state: GameState, player: Player, valid_targets: List[Player]) -> Player:
        return random.choice(valid_targets)

    def choose_ghost_placement(self, state: GameState, player: Player, deck_size: int) -> int:
        return deck_size # bottom of deck

    def choose_card_to_discard(self, state: GameState, player: Player) -> Card:
        utils = [c for c in player.hand if c.type == CardType.UTILITY]
        if utils: return random.choice(utils)
        return random.choice(player.hand)

class AggressiveStrategy(BaseStrategy):
    # Plays attacks and thieves constantly
    def choose_action(self, state: GameState, player: Player, valid_actions: List[str]) -> str:
        aggressives = ["Attack", "Chor", "Shakchunni", "Robber", "Bhoot-Bodol", "Ojha"]
        for a in aggressives:
            if a in valid_actions: return a
        return "DRAW"

    def respond_to_trade(self, state: GameState, player: Player, requested_protection: str) -> Optional[Card]:
        # Only trade if we have multiple protections
        prots = [c for c in player.hand if c.type == CardType.GENERAL_PROTECTION or (c.type == CardType.SPECIFIC_PROTECTION and c.name == requested_protection)]
        if len(prots) > 1: return prots[0]
        return None

    def choose_target(self, state: GameState, player: Player, valid_targets: List[Player]) -> Player:
        # Target player with most cards
        return max(valid_targets, key=lambda p: len(p.hand))

    def choose_ghost_placement(self, state: GameState, player: Player, deck_size: int) -> int:
        return 0 # top of deck to kill next player

    def choose_card_to_discard(self, state: GameState, player: Player) -> Card:
        utils = [c for c in player.hand if c.type == CardType.UTILITY and c.name not in ["Attack", "Chor", "Shakchunni"]]
        if utils: return utils[0]
        return random.choice(player.hand)

class ConservativeStrategy(BaseStrategy):
    def choose_action(self, state: GameState, player: Player, valid_actions: List[str]) -> str:
        return "DRAW" # rarely plays utilities

    def respond_to_trade(self, state: GameState, player: Player, requested_protection: str) -> Optional[Card]:
        return None

    def choose_target(self, state: GameState, player: Player, valid_targets: List[Player]) -> Player:
        return random.choice(valid_targets)

    def choose_ghost_placement(self, state: GameState, player: Player, deck_size: int) -> int:
        return deck_size // 2

    def choose_card_to_discard(self, state: GameState, player: Player) -> Card:
        return random.choice(player.hand)

class OpportunistStrategy(BaseStrategy):
    def choose_action(self, state: GameState, player: Player, valid_actions: List[str]) -> str:
        if len(player.hand) < 4:
            if "Chor" in valid_actions: return "Chor"
            if "Shakchunni" in valid_actions: return "Shakchunni"
        return "DRAW"

    def respond_to_trade(self, state: GameState, player: Player, requested_protection: str) -> Optional[Card]:
        prots = [c for c in player.hand if c.type == CardType.GENERAL_PROTECTION or (c.type == CardType.SPECIFIC_PROTECTION and c.name == requested_protection)]
        if len(prots) > 0: return prots[0]
        return None

    def choose_target(self, state: GameState, player: Player, valid_targets: List[Player]) -> Player:
        # Target player with fewest cards to finish them off
        return min(valid_targets, key=lambda p: len(p.hand))

    def choose_ghost_placement(self, state: GameState, player: Player, deck_size: int) -> int:
        return random.randint(0, min(3, deck_size))

    def choose_card_to_discard(self, state: GameState, player: Player) -> Card:
        return player.hand[0]

class ProtectionHoarder(BaseStrategy):
    def choose_action(self, state: GameState, player: Player, valid_actions: List[str]) -> str:
        return "DRAW"

    def respond_to_trade(self, state: GameState, player: Player, requested_protection: str) -> Optional[Card]:
        return None

    def choose_target(self, state: GameState, player: Player, valid_targets: List[Player]) -> Player:
        return random.choice(valid_targets)

    def choose_ghost_placement(self, state: GameState, player: Player, deck_size: int) -> int:
        return deck_size

    def choose_card_to_discard(self, state: GameState, player: Player) -> Card:
        non_prots = [c for c in player.hand if c.type not in (CardType.SPECIFIC_PROTECTION, CardType.GENERAL_PROTECTION)]
        if non_prots: return random.choice(non_prots)
        return player.hand[0]

class ChaosStrategy(BaseStrategy):
    def choose_action(self, state: GameState, player: Player, valid_actions: List[str]) -> str:
        actions = [a for a in valid_actions if a != "DRAW"]
        if actions: return random.choice(actions)
        return "DRAW"

    def respond_to_trade(self, state: GameState, player: Player, requested_protection: str) -> Optional[Card]:
        prots = [c for c in player.hand if c.type == CardType.GENERAL_PROTECTION or (c.type == CardType.SPECIFIC_PROTECTION and c.name == requested_protection)]
        if prots: return random.choice(prots)
        return None

    def choose_target(self, state: GameState, player: Player, valid_targets: List[Player]) -> Player:
        return random.choice(valid_targets)

    def choose_ghost_placement(self, state: GameState, player: Player, deck_size: int) -> int:
        return random.randint(0, deck_size)

    def choose_card_to_discard(self, state: GameState, player: Player) -> Card:
        return random.choice(player.hand)

class AdaptiveStrategy(BaseStrategy):
    def choose_action(self, state: GameState, player: Player, valid_actions: List[str]) -> str:
        # Late game: aggressive
        alive = len(state.get_alive_players())
        if alive <= 3:
            if "Attack" in valid_actions: return "Attack"
            if "Skip" in valid_actions: return "Skip"
            if "Shuffle" in valid_actions: return "Shuffle"
        return "DRAW"

    def respond_to_trade(self, state: GameState, player: Player, requested_protection: str) -> Optional[Card]:
        prots = [c for c in player.hand if c.type == CardType.GENERAL_PROTECTION or (c.type == CardType.SPECIFIC_PROTECTION and c.name == requested_protection)]
        if len(prots) > 1: return prots[0]
        return None

    def choose_target(self, state: GameState, player: Player, valid_targets: List[Player]) -> Player:
        return random.choice(valid_targets)

    def choose_ghost_placement(self, state: GameState, player: Player, deck_size: int) -> int:
        if len(state.get_alive_players()) <= 2: return 0
        return random.randint(0, deck_size)

    def choose_card_to_discard(self, state: GameState, player: Player) -> Card:
        return random.choice(player.hand)

def get_strategy(name: str) -> BaseStrategy:
    strategies = {
        "Random": RandomStrategy(),
        "Coward": CowardStrategy(),
        "Aggressive": AggressiveStrategy(),
        "Conservative": ConservativeStrategy(),
        "Opportunist": OpportunistStrategy(),
        "ProtectionHoarder": ProtectionHoarder(),
        "Chaos": ChaosStrategy(),
        "Adaptive": AdaptiveStrategy()
    }
    return strategies.get(name, RandomStrategy())
