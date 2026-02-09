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
        self.bid_stack = [] # List of (bidder, amount) to support withdrawal
        self.ticks = 0
        self.human_player = None
        self.logs = [] # Activity feed
        self.max_ticks = 200 # Approx 40 seconds @ 5 ticks/sec
        self.ticks_remaining = self.max_ticks
        self.round_num = 0
        
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
        self.round_num = round_num
        self.current_item = Item()
        self.highest_bid = 0
        self.highest_bidder = None
        self.bid_stack = [] # Reset history
        self.ticks = 0
        self.ticks_remaining = self.max_ticks
        self.is_active = True
        self.log_event(f"Round {round_num} Started.")
        self.log_event(f"Item Hint: {self.current_item.get_hint()}")
        
        # Reset Human Player for the round
        if self.human_player:
            self.human_player.is_passing = False
            self.human_player.has_withdrawn = False
            self.human_player.first_bid_tick = -1
        
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
        self.bid_stack.append((bidder, amount))
        self.log_event(f"{bidder.id} bids ${amount}")
        return True

    def withdraw_bid(self, bidder):
        """Allow the current highest bidder to withdraw their bid."""
        if not self.highest_bidder or self.highest_bidder.id != bidder.id:
            return False # Can only withdraw if you are the current winner
            
        self.log_event(f"{bidder.id} WITHDREW bid.")
        
        # Increment session count if it's the human player
        if hasattr(bidder, 'withdrawal_count'):
            bidder.withdrawal_count += 1
            
        # Remove current bid from stack
        if self.bid_stack:
            self.bid_stack.pop()
            
        # Revert to previous bid if exists
        if self.bid_stack:
            prev_bidder, prev_amount = self.bid_stack[-1]
            self.highest_bid = prev_amount
            self.highest_bidder = prev_bidder
        else:
            self.highest_bid = 0
            self.highest_bidder = None
            
        return True

    def pass_player(self, player):
        """
        Mark a player as passing for the remainder of the round.
        If they were winning, they automatically withdraw their bid first.
        """
        self.log_event(f"{player.id} PASSED.")
        
        # Increment session count
        if hasattr(player, 'pass_count'):
            player.pass_count += 1
            
        # If player was winning, auto-withdraw before passing
        if self.highest_bidder and self.highest_bidder.id == player.id:
            self.withdraw_bid(player)
            
        player.is_passing = True
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
            
            # Update winner's stats
            self.highest_bidder.update_budget(self.highest_bid)
            if hasattr(self.highest_bidder, 'session_profit'):
                self.highest_bidder.session_profit += profit
            if hasattr(self.highest_bidder, 'items_won'):
                self.highest_bidder.items_won += 1
            
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
