import random
from src.models.item import Item
from src.models.ai_agent import AIAgent

class Auction:
    def __init__(self):
        self.round_history = []
        self.current_item = None
        self.agents = []
        self.highest_bid = 0
        self.highest_bidder = None
        self.ticks = 0
        self.human_player = None
        self.logs = [] # Activity feed
        self.max_ticks = 200 # Approx 40 seconds @ 5 ticks/sec
        self.ticks_remaining = self.max_ticks
        
        # Initialize 5 AI Agents ONCE here
        self.agents = []
        for i in range(5):
            # Fixed budget for all bots as requested
            budget = 500
            agent = AIAgent(f"AI-{i+1}", budget)
            self.agents.append(agent)

    def log_event(self, message):
        self.logs.append(message)
        if len(self.logs) > 6: # Keep last 6 for UI
            self.logs.pop(0)

    def get_recent_logs(self):
        return self.logs

    def start_round(self, round_num):
        self.current_item = Item()
        self.highest_bid = 0
        self.highest_bidder = None
        self.ticks = 0
        self.ticks_remaining = self.max_ticks
        self.is_active = True
        self.log_event(f"Round {round_num} Started.")
        self.log_event(f"Item Hint: {self.current_item.get_hint()}")
        
        # Refresh Beliefs for Existing Agents
        for agent in self.agents:
            agent.form_belief(self.current_item.get_hint())
            # Ensure they are active if they have budget? 
            # Or relying on previous round's state? 
            # For now, let's revive them if they have > 0 budget
            if agent.budget > 0:
                agent.is_active = True
            else:
                agent.is_active = False # Bankrupt

    def add_player(self, player):
        self.human_player = player

    def place_bid(self, bidder, amount):
        """
        Centralized method to process a valid bid from ANY source (AI or Player).
        Updates state immediately.
        Returns True if bid was accepted.
        """
        if amount <= self.highest_bid:
            return False
            
        self.highest_bid = amount
        self.highest_bidder = bidder
        self.log_event(f"{bidder.id} bids ${amount}")
        return True

    def run_tick(self):
        """Simulate one 'tick' of bidding activity."""
        if not self.is_active:
            return
            
        # Shuffle agents to ensure fair turn order each tick
        active_agents = [a for a in self.agents if a.is_active]
        random.shuffle(active_agents)
        
        bid_made_this_tick = False
        
        for agent in active_agents:
            # Skip the current winner (they don't outbid themselves)
            if self.highest_bidder and agent.id == self.highest_bidder.id:
                continue
                
            bid = agent.calculate_bid(self.highest_bid, min_increment=10)
            if bid:
                # Use centralized method
                if self.place_bid(agent, bid):
                    bid_made_this_tick = True
                    # In a real-time tick system, maybe only one bid happens per tick?
                    # or multiple? Let's allow multiple to speed up simulation for now.
                    # If we want "ping-pong", checking `bid_made_this_tick` and breaking might be better.
                    # Let's break to simulate "turn taking" this tick
                    break 
        
        self.ticks += 1
        self.ticks_remaining -= 1
        
        # End condition: Time ran out
        if self.ticks_remaining <= 0:
            self.resolve_round()

    def resolve_round(self):
        self.is_active = False
        profit = 0
        winner_id = "None"
        
        if self.highest_bidder:
            winner_id = self.highest_bidder.id
            true_val = self.current_item.get_true_value()
            profit = true_val - self.highest_bid
            self.highest_bidder.update_budget(self.highest_bid)
            
        return {
            "item_value": self.current_item.get_true_value(),
            "winning_bid": self.highest_bid,
            "winner": winner_id,
            "profit": profit
        }

    def get_standings(self):
        """
        Return list of (Name, Budget) tuples sorted by Budget (Descending).
        Includes Human Player.
        """
        all_participants = self.agents + ([self.human_player] if self.human_player else [])
        # Sort by budget
        sorted_list = sorted(all_participants, key=lambda x: x.budget, reverse=True)
        return [(p.id, p.budget) for p in sorted_list]
