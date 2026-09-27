import random
from typing import List, Dict, Any, Tuple
from simulator.models import GameState, Player, Card, CardType
from simulator.strategies import get_strategy

GHOSTS = [
    ("Petni", "Save Your Breath"),
    ("Ghar Motkano Bhut", "Chiropractor"),
    ("Kolla Kata Bhut", "Good Witch"),
    ("Nishi", "Don't Answer"),
    ("Mechho Bhut", "Save Your Fish"),
    ("Skondhokata", "Save Your Head"),
    ("Mamdo Bhut", "Save Your Soul")
]

GENERAL_PROTS = [
    "Ojha's Jhar", "Gunin's Tabiz", "Bhoot Bhaga Mantra", 
    "Iron Charm", "Mustard & Salt", "Seven-Thread Raksha", "Protective Amulet"
]

class GameEngine:
    def __init__(self, num_players: int, strategy_names: List[str]):
        self.state = GameState(num_players)
        for i in range(num_players):
            self.state.players.append(Player(i, strategy_names[i], get_strategy(strategy_names[i])))
        self.setup_deck()

    def setup_deck(self):
        num_players = self.state.num_players
        num_ghosts = num_players - 1
        
        ghost_cards = []
        spec_prot_cards = []
        gen_prot_cards = []
        utils = []

        for i in range(num_ghosts):
            g_name, p_name = GHOSTS[i]
            ghost_cards.append(Card(CardType.GHOST, g_name, p_name))
            if i != 0: # First ghost is unkillable (no specific protections)
                spec_prot_cards.append(Card(CardType.SPECIFIC_PROTECTION, p_name, g_name))
                spec_prot_cards.append(Card(CardType.SPECIFIC_PROTECTION, p_name, g_name))

        # 1 General Protection per player
        for i in range(num_players):
            gen_prot_cards.append(Card(CardType.GENERAL_PROTECTION, GENERAL_PROTS[i % len(GENERAL_PROTS)]))

        # utilities setup
        util_counts = {
            "Shakchunni": 2, "Robber": 2, "Shuffle": 2, "Skip": 2, "Nope": 2, "Chor": 2, "Peek": 2, "Reverse": 2
        }
        if num_players >= 5:
            util_counts.update({"Attack": 2, "Kabiraj": 2})
        if num_players >= 7:
            util_counts.update({"Ojha": 2, "Bhoot-Bodol": 2})

        for u_name, count in util_counts.items():
            for _ in range(count):
                utils.append(Card(CardType.UTILITY, u_name))

        # Initial deal
        random.shuffle(gen_prot_cards)
        
        # Every player gets exactly 1 General Protection
        for p in self.state.players:
            p.hand.append(gen_prot_cards.pop())

        # Remaining cards include the specific protections and utilities (gen_prot_cards should be empty now)
        remaining_deck = spec_prot_cards + gen_prot_cards + utils
        random.shuffle(remaining_deck)

        for p in self.state.players:
            for _ in range(4):
                p.hand.append(remaining_deck.pop())

        self.state.deck = remaining_deck + ghost_cards
        random.shuffle(self.state.deck)

    def get_valid_actions(self, player: Player) -> List[str]:
        actions = ["DRAW"]
        utils_in_hand = [c.name for c in player.hand if c.type == CardType.UTILITY]
        
        counts = {}
        for u in utils_in_hand:
            counts[u] = counts.get(u, 0) + 1
            
        for u, count in counts.items():
            if u in ["Ojha", "Bhoot-Bodol", "Kabiraj"]:
                if count >= 2: actions.append(u)
                elif u == "Kabiraj" or u == "Bhoot-Bodol": actions.append(u)
            elif u == "Nope": continue
            else:
                actions.append(u)
        return list(set(actions))

    def play_nope(self, original_player: Player, utility: str) -> bool:
        nopes = []
        for p in self.state.get_alive_players():
            if p != original_player and p.has_card("Nope"):
                if p.strategy.play_nope(self.state, p, utility, original_player):
                    nopes.append(p)
                    break
        
        if not nopes: return False
        
        # Nope chain
        current_nope = True
        last_noper = nopes[0]
        c = Card(CardType.UTILITY, "Nope")
        last_noper.remove_card(c)
        self.state.discard_pile.append(c)
        self.state.metrics["utility_played"]["Nope"] = self.state.metrics["utility_played"].get("Nope", 0) + 1

        while True:
            chained = False
            for p in self.state.get_alive_players():
                if p != last_noper and p.has_card("Nope"):
                    if p.strategy.play_nope(self.state, p, "Nope", last_noper):
                        current_nope = not current_nope
                        last_noper = p
                        p.remove_card(c)
                        self.state.discard_pile.append(c)
                        self.state.metrics["utility_played"]["Nope"] = self.state.metrics["utility_played"].get("Nope", 0) + 1
                        chained = True
                        break
            if not chained:
                break
        return current_nope

    def run_turn(self):
        player = self.state.get_current_player()
        
        # pre-draw phase
        actions_played = 0
        while True:
            valid_actions = self.get_valid_actions(player)
            action = player.strategy.choose_action(self.state, player, valid_actions)
            if action == "DRAW" or actions_played > 50:
                break
                
            # play utility
            if action == "Skip":
                self.resolve_skip(player)
                return
            else:
                if self.play_nope(player, action):
                    self.discard_utility(player, action)
                else:
                    self.resolve_utility(player, action)
            actions_played += 1
            
        # Draw phase
        while player.owes_draws > 0 and player.is_alive:
            player.owes_draws -= 1
            if not self.state.deck:
                break
            drawn = self.state.deck.pop(0)
            if drawn.type == CardType.GHOST:
                self.resolve_ghost(player, drawn)
                break
            else:
                player.hand.append(drawn)

        self.state.next_turn()

    def discard_utility(self, player: Player, utility: str):
        c = next(c for c in player.hand if c.name == utility)
        player.remove_card(c)
        self.state.discard_pile.append(c)

    def resolve_skip(self, player: Player):
        self.discard_utility(player, "Skip")
        player.owes_draws = max(0, player.owes_draws - 1)

    def resolve_utility(self, player: Player, utility: str):
        self.state.metrics["utility_played"][utility] = self.state.metrics.get("utility_played", {}).get(utility, 0) + 1
        alive = self.state.get_alive_players()
        if utility == "Shakchunni":
            self.discard_utility(player, utility)
            # count seats
            target_idx = (self.state.turn_index + len(player.hand)) % self.state.num_players
            target = self.state.players[target_idx]
            if not target.is_alive or target == player:
                valid = [p for p in alive if p != player]
                if valid: target = random.choice(valid)
            if target != player and target.hand:
                card = random.choice(target.hand)
                target.remove_card(card)
                player.hand.append(card)
        elif utility == "Robber":
            self.discard_utility(player, utility)
            for p in alive:
                if p.hand:
                    c = p.strategy.choose_card_to_discard(self.state, p)
                    p.remove_card(c)
                    self.state.discard_pile.append(c)
        elif utility == "Shuffle":
            self.discard_utility(player, utility)
            random.shuffle(self.state.deck)
        elif utility == "Chor":
            self.discard_utility(player, utility)
            valid = [p for p in alive if p != player and p.hand]
            if valid:
                target = player.strategy.choose_target(self.state, player, valid)
                card = random.choice(target.hand)
                target.remove_card(card)
                player.hand.append(card)
        elif utility == "Peek":
            self.discard_utility(player, utility)
            # just logic-wise, strategy could use it but here we just pass
        elif utility == "Reverse":
            self.discard_utility(player, utility)
            self.state.direction *= -1
        elif utility == "Attack":
            self.discard_utility(player, utility)
            valid = [p for p in alive if p != player]
            if valid:
                target = player.strategy.choose_target(self.state, player, valid)
                target.owes_draws += 2
        elif utility == "Kabiraj":
            c_count = sum(1 for c in player.hand if c.name == "Kabiraj")
            if c_count >= 2:
                for _ in range(2): self.discard_utility(player, "Kabiraj")
            else:
                self.discard_utility(player, "Kabiraj")
        elif utility == "Ojha":
            for _ in range(2): self.discard_utility(player, "Ojha")
            valid = [p for p in alive if p != player]
            if valid:
                target = player.strategy.choose_target(self.state, player, valid)
                prots = [c for c in target.hand if c.type in (CardType.SPECIFIC_PROTECTION, CardType.GENERAL_PROTECTION)]
                if prots:
                    c = random.choice(prots)
                    target.remove_card(c)
                    self.state.discard_pile.append(c)
        elif utility == "Bhoot-Bodol":
            c_count = sum(1 for c in player.hand if c.name == "Bhoot-Bodol")
            if c_count >= 2:
                for _ in range(2): self.discard_utility(player, "Bhoot-Bodol")
                valid = [p for p in alive if p != player and p.hand]
                if len(valid) >= 2:
                    t1, t2 = random.sample(valid, 2)
                    c1, c2 = random.choice(t1.hand), random.choice(t2.hand)
                    t1.remove_card(c1)
                    t2.remove_card(c2)
                    t1.hand.append(c2)
                    t2.hand.append(c1)
            else:
                self.discard_utility(player, "Bhoot-Bodol")
                valid = [p for p in alive if p != player and p.hand]
                if valid and player.hand:
                    target = random.choice(valid)
                    c1, c2 = random.choice(player.hand), random.choice(target.hand)
                    player.remove_card(c1)
                    target.remove_card(c2)
                    player.hand.append(c2)
                    target.hand.append(c1)

    def resolve_ghost(self, player: Player, ghost: Card):
        self.state.metrics["ghost_encounters"] += 1
        current_turn = self.state.metrics["game_length_turns"]
        spec_prots = [c for c in player.hand if c.type == CardType.SPECIFIC_PROTECTION and c.ghost_target == ghost.name]
        gen_prots = [c for c in player.hand if c.type == CardType.GENERAL_PROTECTION]

        # 1. Permanent removal
        if len(spec_prots) >= 2:
            self.state.metrics["ghosts_removed"] += 1
            self.state.metrics["protection_used"] += 2
            player.remove_card(spec_prots[0])
            player.remove_card(spec_prots[1])
            self.state.discard_pile.extend([spec_prots[0], spec_prots[1], ghost])
            self.state.ghosts_in_game -= 1
            self.state.metrics["ghost_events"].append({"turn": current_turn, "event": "removed", "ghost": ghost.name})
            return
            
        # 2. Use specific
        if len(spec_prots) == 1:
            self.state.metrics["ghosts_survived"] += 1
            self.state.metrics["protection_used"] += 1
            player.remove_card(spec_prots[0])
            self.state.discard_pile.append(spec_prots[0])
            idx = player.strategy.choose_ghost_placement(self.state, player, len(self.state.deck))
            self.state.deck.insert(idx, ghost)
            self.state.metrics["ghost_events"].append({"turn": current_turn, "event": "survived_and_recycled", "ghost": ghost.name})
            return

        # 3. Use general
        if gen_prots:
            self.state.metrics["ghosts_survived"] += 1
            self.state.metrics["general_protection_used"] += 1
            player.remove_card(gen_prots[0])
            self.state.discard_pile.append(gen_prots[0])
            idx = player.strategy.choose_ghost_placement(self.state, player, len(self.state.deck))
            self.state.deck.insert(idx, ghost)
            self.state.metrics["ghost_events"].append({"turn": current_turn, "event": "survived_and_recycled", "ghost": ghost.name})
            return

        # 4. Trade
        if any(c.type in (CardType.SPECIFIC_PROTECTION, CardType.GENERAL_PROTECTION) for c in player.hand):
            for p in self.state.get_alive_players():
                if p != player:
                    trade_card = p.strategy.respond_to_trade(self.state, p, ghost.ghost_target)
                    self.state.metrics["trades_attempted"] += 1
                    if trade_card and (trade_card.type == CardType.GENERAL_PROTECTION or trade_card.ghost_target == ghost.name):
                        self.state.metrics["trades_successful"] += 1
                        # execute trade
                        my_prot = next(c for c in player.hand if c.type in (CardType.SPECIFIC_PROTECTION, CardType.GENERAL_PROTECTION))
                        player.remove_card(my_prot)
                        p.remove_card(trade_card)
                        player.hand.append(trade_card)
                        p.hand.append(my_prot)
                        
                        # Use newly acquired
                        if trade_card.type == CardType.SPECIFIC_PROTECTION:
                            self.state.metrics["protection_used"] += 1
                        else:
                            self.state.metrics["general_protection_used"] += 1
                        self.state.metrics["ghosts_survived"] += 1
                        player.remove_card(trade_card)
                        self.state.discard_pile.append(trade_card)
                        idx = player.strategy.choose_ghost_placement(self.state, player, len(self.state.deck))
                        self.state.deck.insert(idx, ghost)
                        self.state.metrics["ghost_events"].append({"turn": current_turn, "event": "survived_and_recycled", "ghost": ghost.name})
                        return

        # 5. Die
        player.is_alive = False
        self.state.metrics["death_turns"].append(self.state.metrics["game_length_turns"])
        self.state.discard_pile.extend(player.hand)
        player.hand = []
        idx = player.strategy.choose_ghost_placement(self.state, player, len(self.state.deck))
        self.state.deck.insert(idx, ghost)
        self.state.metrics["ghost_events"].append({"turn": current_turn, "event": "killed_and_recycled", "ghost": ghost.name})

    def run(self):
        while len(self.state.get_alive_players()) > 1:
            self.state.metrics["game_length_turns"] += 1
            alive = self.state.get_alive_players()
            sizes = [len(p.hand) for p in alive]
            self.state.metrics["hand_sizes"].append(sum(sizes) / len(sizes))
            
            self.run_turn()
            
            # prevent infinite games (shouldn't happen often)
            if len(self.state.deck) == 0 or self.state.metrics["game_length_turns"] > 1000:
                break
        
        return self.state.metrics
