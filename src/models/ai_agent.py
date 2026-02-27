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
        
        # --- NEW STATE LOGIC ---
        self.state = "Active" # "Active", "Pass", "Withdraw"
        self.personal_range = (0, 0)
        self.conviction_point = 0
        
        # --- SPITE LOGIC ---
        self.has_spite_bid = False
        self.spite_cooldown = 0  # Set > 0 when armed; fire only after countdown
        self.is_spite_armed = False  # Guards against immediate fire
        
        # --- BLUFF LOGIC ---
        self.is_bluffing = False   # Conservative bluff entry
        self.bluff_bids_placed = 0 # How many bids placed in bluff mode

    def reset_for_new_round(self):
        self.state = "Active"
        self.is_active = (self.budget > 0)
        self.bid_history = []
        
        # Presentation pacing: Add a 3s to 5s initial startup delay for bots
        # so they don't immediately machine-gun bids on tick 0
        self.next_action_tick = random.randint(15, 25)
        
        self.has_spite_bid = False
        self.spite_cooldown = 0
        self.is_spite_armed = False
        self.is_bluffing = False
        self.bluff_bids_placed = 0
        self.has_used_jump_bid = False

    def form_belief(self, hint_text, round_num=1, total_rounds=5):
        hint_data = HINT_CONFIG.get(hint_text, list(HINT_CONFIG.values())[2])
        h_min, h_max = hint_data['range']
        base_value = hint_data['base_value']
        
        strat = STRATEGY_CONFIG.get(self.strategy, STRATEGY_CONFIG["Balanced"])
        
        # 1. Establish Personal Range (The "Vibe")
        # Conservative thinks: "mediocre" -> Pessimistic (-15% to -5% of hint range)
        # Aggressive thinks: "underselling" -> Optimistic (+5% to +20% of hint range)
        # Balanced thinks: "could go either way" -> Balanced (-5% to +5% of hint range)
        if self.strategy == "Conservative":
            range_min_offset = random.uniform(-0.15, -0.05)
            range_max_offset = random.uniform(-0.10, 0.00)
        elif self.strategy == "Aggressive":
            range_min_offset = random.uniform(0.05, 0.15)
            range_max_offset = random.uniform(0.10, 0.20)
        else:
            range_min_offset = random.uniform(-0.05, 0.05)
            range_max_offset = random.uniform(-0.05, 0.05)
            
        self.personal_range = (
            int(h_min * (1 + range_min_offset)),
            int(h_max * (1 + range_max_offset))
        )
        
        # 2. Lock in Conviction Point 
        p_min, p_max = self.personal_range
        if self.strategy == "Conservative":
            self.conviction_point = p_min
        elif self.strategy == "Aggressive":
            self.conviction_point = p_max
        else:
            self.conviction_point = (p_min + p_max) // 2

        # Legacy compatibility for now
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
        # Bug A: Tighten safety to avoid massive losses even for Aggressive bots
        hard_ceiling = int(hint_data['safe_cap'] * 1.1) 
        self.max_bid_limit = min(self.max_bid_limit, hard_ceiling)
        
        # Part 2: Gate 6 Setup - Strategy Specific Strategic Ceiling
        if self.strategy == "Aggressive":
             self.strategic_ceiling = int(self.estimated_value * 1.05) # Allow 5% loss
        elif self.strategy == "Balanced":
             self.strategic_ceiling = int(self.estimated_value * 0.95) # Require 5% profit
        else: # Conservative
             self.strategic_ceiling = int(self.estimated_value * 0.90) # Require 10% profit

    def pre_entry_check(self, opening_bid):
        """Part 2: Pre-Entry Check (When Do They PASS?)"""
        p_min, p_max = self.personal_range
        
        # Bug 2 Fix: Relax constraints. Default to Active.
        # Only Pass if budget is destroyed or opening bid is above conviction point.
        from src.config import MIN_INCREMENT
        
        # Rule A: Price already too high (exceeds top of personal range)
        if opening_bid > p_max:
             self.state = "Pass"
             return

        # Rule B: Budget too low (less than 2 raises possible)
        if (opening_bid + 2 * MIN_INCREMENT) > self.budget:
             self.state = "Pass"
             return
             
        # Rule C: Estimate too pessimistic (Conservative only)
        # If open price leaves too thin a margin (e.g. < 10% of their base valuation)
        if self.strategy == "Conservative":
            margin = self.conviction_point - opening_bid
            if margin < (self.conviction_point * 0.1): # Too pessimistic to bother
                 # Bluff Exception (15% chance to enter anyway)
                 if random.random() < 0.15:
                     self.is_bluffing = True
                     self.state = "Active"
                     # Note: Auction handles logging this if added correctly
                     return
                 self.state = "Pass"
                 return

        self.state = "Active"

    def handle_event(self, event_type, data):
        """Part 3: Mid-Auction Events (When Do They WITHDRAW?)"""
        if self.state != "Active":
            return

        current_price = data.get('current_price', 0)
        min_increment = data.get('min_increment', 5)
        highest_bidder_id = data.get('highest_bidder_id')

        # Event 1: Someone places a new bid (General Price Check)
        if event_type == "new_bid":
            # Bug 1 Fix: Only reset delay if we don't already have a pending action
            # to avoid getting "locked in place" by rapid fire bids from others.
            if self.next_action_tick <= 1:
                strat = STRATEGY_CONFIG.get(self.strategy, STRATEGY_CONFIG["Balanced"])
                min_s, max_s = strat.get('reaction_speed', (2, 8))
                self.next_action_tick = random.randint(min_s, max_s)

            # Margin check — human reaction logic
            # Part 3, Event 1: New bid forces CP check
            if self.strategy == "Conservative":
                if current_price >= self.conviction_point:
                    # Quiet withdrawal
                    self.state = "Withdraw" if self.bid_history else "Pass"
                    return
            
            elif self.strategy == "Balanced":
                if current_price >= self.strategic_ceiling:
                    # Hesitant withdrawal (add a delay before actually folding)
                    if not getattr(self, 'is_watching', False):
                        self.is_watching = True
                        self.watch_ticks = random.randint(1, 3) # Reduced delay folding (was 3-7) because ticks take longer now
                    return
                else:
                    # If we were watching but price is now safe, stop watching
                    self.is_watching = False
            
            # Aggressive: check for War Mode or Spite Bid trigger
            if self.strategy == "Aggressive":
                # Part 3, Event 4: One-Shot Warning
                if (current_price + 2 * min_increment) > self.budget and not self.has_spite_bid:
                    self.has_spite_bid = True
                    self.spite_cooldown = data.get('spite_delay', 5)
                    self.is_spite_armed = True

        # Event 2: Their own bid gets outbid (Emotional Trigger)
        if event_type == "outbid":
            # Set shorter reaction delay for "retaliation", but still paced for readability
            self.next_action_tick = random.randint(4, 9)

            if self.strategy == "Conservative":
                # Part 3, Event 2: Chase check
                # A Conservative immediately re-checks if chasing makes sense
                if (current_price + min_increment) > self.conviction_point:
                    self.state = "Withdraw" if self.bid_history else "Pass"
                    return
            elif self.strategy == "Balanced":
                # Part 3, Event 2: Chase check
                # A Balanced might chase once more, but hesitates if near ceiling
                if (current_price + 2 * min_increment) >= self.strategic_ceiling:
                    if not getattr(self, 'is_watching', False):
                        self.is_watching = True
                        self.watch_ticks = random.randint(1, 3) # Reduced hesitation
                    return
                else:
                    # Below ceiling: retaliate
                    self.is_watching = False
                    self.next_action_tick = random.randint(4, 9)
            # Aggressive treats it as a personal attack (War Mode trigger)

        # Event 3: Timer thresholds (Hesitation vs Sniper)
        if event_type == "timer_tick":
            timer = data.get('ticks_remaining', 40)
            if timer <= 15: # "Going Once/Twice" phase
                # Part 3, Event 3: Hesitation vs Sniper
                # If current_price is uncomfortably close to CP (within 2 increments)
                if (self.conviction_point - current_price) < (2 * min_increment):
                    # They hesitate and refuse to panic-bid
                    self.state = "Withdraw" if self.bid_history else "Pass"
                    return
                # ELSE: If price is still WELL below CP, they stay in to snipe (handled in calculate_bid)

        # Event 4: The One-Shot Warning (Spite Bid Trigger)
        if event_type == "budget_warning":
            if (current_price + 2 * min_increment) > self.max_bid_limit:
                if self.strategy == "Aggressive" and not self.has_spite_bid:
                    self.has_spite_bid = True
                    self.spite_cooldown = data.get('spite_delay', 5)
                    self.is_spite_armed = True

    def calculate_bid(self, auction_state, min_increment):
        """Simplified bidding loop based on state and delays"""
        if self.state != "Active":
            return None
            
        current_price = auction_state['current_price']
        if auction_state['highest_bidder_id'] == self.id:
            return None
            
        if current_price >= self.budget:
            self.state = "Withdraw" if self.bid_history else "Pass"
            return None

        # --- SPITE BID EXECUTION (The "Wall") ---
        # ... spite logic remains ...
        if self.has_spite_bid and self.is_spite_armed:
            if self.spite_cooldown > 0:
                self.spite_cooldown -= 1
                return None
            else:
                wall_bid = min(self.budget, self.max_bid_limit) 
                if wall_bid <= current_price:
                    self.state = "Withdraw" if self.bid_history else "Pass"
                    return None
                self.state = "Withdraw"
                return wall_bid

        # --- BLUFF HANDLER ---
        if self.is_bluffing:
            if self.bluff_bids_placed >= 1:
                self.state = "Withdraw" if self.bid_history else "Pass"
                return None

        # Balanced Hesitation Delay
        if self.strategy == "Balanced" and getattr(self, 'is_watching', False):
            if self.watch_ticks > 0:
                self.watch_ticks -= 1
                return None
            else:
                # Hesitation over. Fold ONLY if price is still above ceiling.
                if current_price >= self.strategic_ceiling:
                     self.state = "Withdraw" if self.bid_history else "Pass"
                     return None
                else:
                    # Reset watching and continue bidding
                    self.is_watching = False

        # ... keep reaction delay ...
        if self.next_action_tick > 0:
            self.next_action_tick -= 1
            return None

        # ... keep first bid logic ...
        next_min_bid = current_price + min_increment
        if not self.bid_history:
             calculated_start = int(self.conviction_point * 0.30)
             bid_amount = max(next_min_bid, calculated_start)
        else:
             bid_amount = next_min_bid

        # Final safety check before bidding (Gate 6: Universal Profit Floor)
        if bid_amount > self.strategic_ceiling:
             self.state = "Withdraw" if self.bid_history else "Pass"
             return None

        # --- TACTICS (Bug 4 Fix) ---
        strat = STRATEGY_CONFIG.get(self.strategy, STRATEGY_CONFIG["Balanced"])
        tactics = strat.get('tactics', [])
        
        # SNIPER logic (Gate 7 adjustment)
        if 'snipe' in tactics and auction_state.get('ticks_remaining', 40) > 15:
            # Skip sniper delay if floor is empty OR we are the last active participant
            if not auction_state.get('highest_bidder_id') or auction_state.get('active_participant_count', 0) == 1:
                return bid_amount
                
            # Only snipe if price is very low, otherwise wait for timer
            if current_price > (self.conviction_point * 0.7):
                return None

        # Jump Bid (Intimidation): Once per round, lower third of range only.
        # Jump Bid = Current Bid + Math.floor(bot.conviction_point * 0.15).
        # Bug B Fix: Double check the flag and the range
        if 'jump_bid' in tactics and not self.has_used_jump_bid:
            p_min, p_max = self.personal_range
            range_third = p_min + (p_max - p_min) // 3
            if current_price < range_third and random.random() < TACTIC_CONFIG['jump_bid_chance']:
                jump_magnitude = int(self.conviction_point * 0.15)
                if (current_price + jump_magnitude) < self.max_bid_limit:
                    bid_amount = current_price + jump_magnitude
                    self.has_used_jump_bid = True
                    # Set extra delay after an intimidation bid
                    self.next_action_tick += 3

        if self.is_bluffing:
            if self.bluff_bids_placed == 0:
                pass # First bid log handled by Auction
            self.bluff_bids_placed += 1
        
        self.bid_history.append(bid_amount)
        return bid_amount

    def update_budget(self, amount):
        self.budget -= amount