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
        self.is_active = False
        self.human_player = None

    def start_round(self, round_num):
        self.current_item = Item()
        self.highest_bid = 0
        self.highest_bidder = None
        self.ticks = 0
        self.is_active = True
        
        # Initialize 5 AI Agents
        self.agents = []
        for i in range(5):
            # Give them some varied budget for flavor
            budget = random.randint(400, 600)
            agent = AIAgent(f"AI-{i+1}", budget)
            agent.form_belief(self.current_item.get_hint())
            self.agents.append(agent)

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
        return True

    def run_tick(self):
        """
        Simulate one moment of bidding.
        Agents shuffle order effectively by iterating.
        """
        if not self.is_active:
            return
            
        # Shuffle agents so it's not always AI-1 first
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
        
        # End condition: If no one bids for X ticks, end? 
        # For this Phase 1 sim, we can just run a fixed number of loops in the runner.

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
