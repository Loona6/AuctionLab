import random
from src.config import STRATEGY_CONFIG, HINT_CONFIG, TACTIC_CONFIG

class AIAgent:
    def __init__(self, agent_id, budget, strategy_type=None):
        self.id = agent_id
        self.budget = budget
        
        if strategy_type:
            self.strategy = strategy_type
        else:
            self.strategy = random.choice(["Aggressive", "Conservative", "Balanced"])
            
        self.estimated_value = 0
        self.max_bid_limit = 0
        self.bid_history = []
        self.is_active = True
        self.session_profit = 0
        self.items_won = 0
        self.next_action_tick = 0 
        
        # --- PHASE 3: SPITE LOGIC ---
        self.has_spite_bid = False
        self.spite_cooldown = 0 # Dramatic delay

    def reset_for_new_round(self):
        self.is_active = (self.budget > 0)
        self.bid_history = []
        self.next_action_tick = 0
        self.has_spite_bid = False
        self.spite_cooldown = 0

    def on_price_update(self):
        """Trigger reaction delay"""
        strat = STRATEGY_CONFIG.get(self.strategy, STRATEGY_CONFIG["Balanced"])
        min_s, max_s = strat.get('reaction_speed', (2, 8))
        self.next_action_tick = random.randint(min_s, max_s)

    def form_belief(self, hint_text, round_num=1, total_rounds=5):
        hint_data = HINT_CONFIG.get(hint_text, HINT_CONFIG["Decent demand"])
        base_value = hint_data['base_value']
        safe_cap = hint_data['safe_cap']
        
        strat = STRATEGY_CONFIG.get(self.strategy, STRATEGY_CONFIG["Balanced"])
        noise = random.uniform(strat['noise_range'][0], strat['noise_range'][1])
        
        self.estimated_value = int(base_value * (1 + noise))
        self.max_bid_limit = int(self.estimated_value * strat['risk_ceiling'])
        
        # Desperation
        if round_num >= (total_rounds - 1) and self.items_won == 0:
            if self.strategy == "Aggressive":
                self.max_bid_limit = int(self.max_bid_limit * 1.25)
            else:
                self.max_bid_limit = int(self.max_bid_limit * 1.10)
                
        # Safety Clamp
        hard_ceiling = int(safe_cap * 1.2)
        self.max_bid_limit = min(self.max_bid_limit, hard_ceiling)

    def calculate_bid(self, auction_state, min_increment):
        ticks_left = auction_state['ticks_remaining']
        current_price = auction_state['current_price']
        
        if not self.is_active: return None
        if auction_state['highest_bidder_id'] == self.id: return None
        if current_price >= self.budget: return None

        # --- PHASE 3: SPITE COOLDOWN ---
        if self.spite_cooldown > 0:
            self.spite_cooldown -= 1
            if self.spite_cooldown == 0:
                # Surprise Attack!
                bid_amount = current_price + min_increment
                self.bid_history.append(bid_amount)
                return bid_amount
            return None

        # --- 1. ADRENALINE OVERRIDE ---
        if ticks_left < 12:
            self.next_action_tick = 0

        # Reaction Delay
        if self.next_action_tick > 0:
            self.next_action_tick -= 1
            return None

        next_min_bid = current_price + min_increment

        # --- PHASE 2: WAR MODE ---
        # If the price is already higher than our value, we ignore profit target
        # and bid blindly up to our Risk Ceiling.
        is_war_mode = (current_price >= self.estimated_value)
        
        # --- 2. THE AUDIT ---
        if next_min_bid > self.max_bid_limit:
            # --- PHASE 3: SPITE BID CHECK ---
            if self.strategy == "Aggressive" and not self.has_spite_bid:
                # Only spite against the Human Player
                if auction_state['highest_bidder_id'] == "You":
                    # Only if we are within 1 bid of our limit (The Ego Check)
                    if (next_min_bid - min_increment) <= self.max_bid_limit:
                        self.has_spite_bid = True
                        self.spite_cooldown = 10 # 2-second hesitation (5 ticks/s)
            return None

        # --- 3. PROFIT TARGET ---
        strat = STRATEGY_CONFIG.get(self.strategy, STRATEGY_CONFIG["Balanced"])
        target_margin = strat.get('profit_target', 0)
        
        # Reduce profit target in "Going Once/Twice" phase
        if auction_state.get('state') in ["Going Once", "Going Twice"]:
            target_margin *= 0.5

        potential_profit = self.estimated_value - next_min_bid
        min_profit_needed = self.estimated_value * target_margin
        
        # Only check profit if NOT in War Mode or Desperate
        if self.items_won > 0 and not is_war_mode:
            if potential_profit < min_profit_needed:
                return None

        # --- 4. TACTICS ---
        tactics = strat.get('tactics', [])
        
        # SMART SNIPER
        if 'snipe' in tactics and ticks_left > 20:
             if current_price > (self.max_bid_limit * 0.5):
                 return None

        # BAITER
        if 'bait' in tactics:
            if current_price > (self.max_bid_limit * 0.85):
                 if random.random() < 0.5: return None

        # BID SIZING
        bid_amount = next_min_bid
        
        # Intimidation
        if 'jump_bid' in tactics and current_price < (self.max_bid_limit * 0.6):
            if random.random() < TACTIC_CONFIG['jump_bid_chance']:
                jump = min_increment * random.randint(2, 3)
                if (current_price + jump) < self.max_bid_limit:
                    bid_amount = current_price + jump

        self.bid_history.append(bid_amount)
        return bid_amount

    def update_budget(self, amount):
        self.budget -= amount