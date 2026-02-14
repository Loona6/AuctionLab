import random
from src.models.item import Item
from src.models.ai_agent import AIAgent

class Auction:
    def __init__(self):
        self.round_history = []
        self.current_item = None
        self.highest_bid = 0
        self.highest_bidder = None
        self.bid_stack = [] 
        self.ticks = 0
        self.human_player = None
        self.logs = [] 
        self.round_num = 0
        self.is_active = False 
        
        # --- PACING CONFIG ---
        self.base_patience = 40  # 8 seconds (at 5 ticks/sec)
        self.current_max_patience = self.base_patience
        self.current_patience = self.base_patience
        self.auction_state = "Active" 
        self.full_session_log = [] # Persistent history for file export
        
        # Initialize 5 AI Agents
        self.agents = []
        for i in range(5):
            budget = 500
            agent = AIAgent(f"AI-{i+1}", budget)
            self.agents.append(agent)

    def log_event(self, message):
        self.logs.append(message)
        self.full_session_log.append(message)
        if len(self.logs) > 8: self.logs.pop(0)

    def get_recent_logs(self):
        return self.logs

    def start_round(self, round_num):
        self.round_num = round_num
        self.current_item = Item()
        self.highest_bid = 0
        self.highest_bidder = None
        self.bid_stack = [] 
        
        # Reset Pacing
        self.current_max_patience = self.base_patience
        self.current_patience = self.base_patience
        self.auction_state = "Active"
        self.is_active = True
        
        self.log_event(f"--- Round {round_num} Started ---")
        self.log_event(f"Item Hint: {self.current_item.get_hint()}")
        
        if self.human_player:
            self.human_player.is_passing = False
            self.human_player.has_withdrawn = False
        
        # Refresh Beliefs
        for agent in self.agents:
            agent.reset_for_new_round()
            agent.form_belief(self.current_item.get_hint(), round_num, total_rounds=5)
            agent.is_active = (agent.budget > 0)

    def add_player(self, player):
        self.human_player = player

    def place_bid(self, bidder, amount):
        if amount <= self.highest_bid:
            return False
            
        self.highest_bid = amount
        self.highest_bidder = bidder
        self.bid_stack.append((bidder, amount))
        self.log_event(f"{bidder.id} bids ${amount}")
        
        # --- PHASE 4: DYNAMIC PACING & TIMER RESET ---
        # ALL bids (Human or AI) reset the state to Active and restore timer
        if self.auction_state in ["Going Once", "Going Twice"]:
            # Accelerate! Drop max patience by 5 ticks (1s), floor at 20 ticks (4s)
            self.current_max_patience = max(20, self.current_max_patience - 5)
            self.current_patience = self.current_max_patience
        else:
            # Bid happened early, reset to full time
            self.current_patience = self.base_patience
            
        self.auction_state = "Active"
        
        # Notify Agents
        for agent in self.agents:
            agent.on_price_update()

        try:
            from src.logic.audio_manager import AudioManager
            AudioManager().play("bid")
        except: pass
        
        return True

    def withdraw_bid(self, bidder):
        if not self.highest_bidder or self.highest_bidder.id != bidder.id: return False 
        
        self.log_event(f"{bidder.id} WITHDREW bid.")
        if hasattr(bidder, 'withdrawal_count'): bidder.withdrawal_count += 1
            
        if self.bid_stack: self.bid_stack.pop()
        
        if self.bid_stack:
            prev_bidder, prev_amount = self.bid_stack[-1]
            self.highest_bid = prev_amount
            self.highest_bidder = prev_bidder
        else:
            self.highest_bid = 0
            self.highest_bidder = None
            
        return True

    def pass_player(self, player):
        self.log_event(f"{player.id} PASSED.")
        if hasattr(player, 'pass_count'): player.pass_count += 1
        if self.highest_bidder and self.highest_bidder.id == player.id:
            self.withdraw_bid(player)
        player.is_passing = True
        return True

    def run_tick(self):
        if not self.is_active: return
            
        # 1. Update Timer
        self.current_patience -= 1
        
        # --- PHASE 4: EXPLICIT STATE FLAGS ---
        if self.current_patience == 25: 
            self.auction_state = "Going Once"
            self.log_event("Going once...")
        elif self.current_patience == 10: 
            self.auction_state = "Going Twice"
            self.log_event("Going twice...")
        elif self.current_patience <= 0:
            self.log_event("SOLD!")
            self.resolve_round()
            return

        # 2. AI Turn
        active_agents = [a for a in self.agents if a.is_active]
        random.shuffle(active_agents)
        
        # Pass the EXPLICIT state to agents
        auction_state = {
            'current_price': self.highest_bid,
            'highest_bidder_id': self.highest_bidder.id if self.highest_bidder else None,
            'ticks_remaining': self.current_patience,
            'state': self.auction_state
        }
        
        from src.config import MIN_INCREMENT
        # Allow up to 2 bids per tick for chaos
        bids_this_tick = 0
        for agent in active_agents:
            if bids_this_tick >= 2: break
            
            bid = agent.calculate_bid(auction_state, min_increment=MIN_INCREMENT)
            if bid:
                if self.place_bid(agent, bid):
                    bids_this_tick += 1
        
        self.ticks += 1

    def resolve_round(self):
        self.is_active = False
        profit = 0
        winner_id = "None"
        
        if self.highest_bidder:
            winner_id = self.highest_bidder.id
            true_val = self.current_item.get_true_value()
            profit = true_val - self.highest_bid
            
            self.highest_bidder.update_budget(self.highest_bid)
            if hasattr(self.highest_bidder, 'session_profit'):
                self.highest_bidder.session_profit += profit
            if hasattr(self.highest_bidder, 'items_won'):
                self.highest_bidder.items_won += 1
            
        res = {
            "item_value": self.current_item.get_true_value(),
            "winning_bid": self.highest_bid,
            "winner": winner_id,
            "profit": profit
        }
        
        self.log_event(f"RESULT: Winner {winner_id} for ${self.highest_bid} | Value: ${res['item_value']} | Profit: ${profit}")
        return res

    def save_session_logs(self, filename="gameplay_logs.txt"):
        """Save full session history to a text file (overwrites previous session)."""
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        try:
            with open(filename, "w", encoding="utf-8") as f:
                f.write(f"========================================\n")
                f.write(f" LAST SESSION: {timestamp}\n")
                f.write(f"========================================\n")
                for line in self.full_session_log:
                    f.write(line + "\n")
            return True
        except Exception as e:
            print(f"Error saving logs: {e}")
            return False

    def get_standings(self):
        all_participants = self.agents + ([self.human_player] if self.human_player else [])
        sorted_list = sorted(all_participants, key=lambda x: x.budget, reverse=True)
        return [(p.id, p.budget) for p in sorted_list]