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
        self.round_logs = [] # Full log for current round (unsliced)
        self.round_num = 0
        self.is_active = False 
        self.auction_locked = False # Bug 1: Atomic lock for final ticks
        self.total_rounds_sim = 5   # Default for UI play
        
        # --- PACING CONFIG ---
        self.base_patience = 60  # 12 seconds (at 5 ticks/sec) to account for slower bots
        self.current_max_patience = self.base_patience
        self.current_patience = self.base_patience
        self.auction_state = "Active" 
        self.last_state_change_tick = 0
        self.full_session_log = [] # Persistent history for file export
        
        # Real-time deadline for smooth clock display (ms)
        self.patience_deadline_ms = 0  # Set on start_round
        self.TICK_INTERVAL_MS = 200    # Must match gameplay.py update interval
        self.is_paused = False         # NEW: Support for pausing timer/AI
        
        # Initialize 5 AI Agents with randomized budgets and strategies
        self.agents = []
        for i in range(5):
            budget = 500
            agent = AIAgent(f"AI-{i+1}", budget) 
            self.agents.append(agent)
        
        # No shuffle: keep AI-1 to AI-5 order for UI consistency
        # Fairness is handled via tick-level shuffles in run_tick

        self.pending_withdrawals = [] # Bug 7: UI delay queue [(agent_id, delay_ticks)]
        self.last_bidder_standing = False # Bug 8: UI flag 

    def log_event(self, message):
        self.logs.append(message)
        self.round_logs.append(message)
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
        # Sync real-time deadline
        try:
            import pygame
            self.patience_deadline_ms = pygame.time.get_ticks() + (self.current_patience * self.TICK_INTERVAL_MS)
        except Exception:
            self.patience_deadline_ms = 0
            
        self.pending_withdrawals = []
        self.last_bidder_standing = False
        self.auction_locked = False
        self.last_state_change_tick = 0
        self.round_logs = []
        
        self.log_event(f"--- Round {round_num} Started ---")
        self.log_event(f"Item Hint: {self.current_item.get_hint()}")
        
        if self.human_player:
            self.human_player.is_passing = False
            self.human_player.has_withdrawn = False
            self.human_player.powerup_used = False
        
        # Refresh Beliefs
        # random.shuffle(self.agents) # Removed: Master list should not be shuffled.
        for agent in self.agents:
            agent.reset_for_new_round()
            agent.form_belief(self.current_item.get_hint(), round_num, total_rounds=self.total_rounds_sim)
            agent.pre_entry_check(0) # Part 2: Pre-Entry Check
            if agent.state == "Pass":
                self.log_event(f"{agent.id} decided to PASS.")
            elif agent.is_bluffing:
                self.log_event(f"{agent.id} is entering with a BLUFF.")
            agent.is_active = (agent.budget > 0 and agent.state == "Active")

    def add_player(self, player):
        self.human_player = player

    def place_bid(self, bidder, amount):
        if amount <= self.highest_bid:
            return False
        
        # Bug 1 Fix: Atomic check
        if self.auction_locked:
            self.log_event(f"REJECTED: Auction is locked (SOLD!)")
            return False
            
        self.highest_bid = amount
        self.highest_bidder = bidder
        self.bid_stack.append((bidder, amount))
        self.log_event(f"{bidder.id} bids ${amount}")
        
        # --- PHASE 4: DYNAMIC PACING & TIMER RESET ---
        # If someone bids during "Going Once/Twice", reset the timer to full!
        if self.auction_state in ["Going Once", "Going Twice"]:
            self.current_max_patience = self.base_patience
            self.current_patience = self.base_patience
        elif self.current_patience < 10:
            # Minor anti-snipe for other late-ticker states
            self.current_patience = min(self.base_patience, self.current_patience + 10)
        # else: plenty of time left — leave the clock alone, no jump
            
        self.auction_state = "Active"
        self.last_state_change_tick = self.ticks
        # Sync real-time deadline after any patience change
        try:
            import pygame
            self.patience_deadline_ms = pygame.time.get_ticks() + (self.current_patience * self.TICK_INTERVAL_MS)
        except Exception:
            pass
        
        # Notify Agents of the new bid
        from src.config import MIN_INCREMENT
        event_data = {
            'current_price': self.highest_bid,
            'highest_bidder_id': self.highest_bidder.id,
            'min_increment': MIN_INCREMENT
        }
        
        for agent in self.agents:
            # STRICT GUARD: skip folded bots entirely
            if agent.state != "Active":
                continue
            if agent.id == bidder.id:
                continue
                
            # Check if this agent was the one just outbid
            prev_state = agent.state
            if len(self.bid_stack) > 1 and self.bid_stack[-2][0].id == agent.id:
                agent.handle_event("outbid", event_data)
            else:
                agent.handle_event("new_bid", event_data)
                
            # Only log/update if this bid caused a new withdrawal
            if prev_state == "Active" and agent.state == "Withdraw":
                self._enqueue_withdrawal(agent.id)
                agent.is_active = False

        try:
            from src.logic.audio_manager import AudioManager
            AudioManager().play("bid")
        except: pass
        
        return True

    def _enqueue_withdrawal(self, agent_id):
        """Bug 7: Add withdrawal to a queue with a random delay to prevent hive-mind output."""
        delay = random.randint(1, 4) # 1-4 ticks (200ms - 800ms)
        self.pending_withdrawals.append({
            'id': agent_id,
            'ticks_left': delay
        })

    def withdraw_bid(self, bidder):
        if not self.highest_bidder or self.highest_bidder.id != bidder.id: return False 
        
        # --- Apply Penalty Logic (User Refined Design) ---
        if self.highest_bidder and self.highest_bidder.id == bidder.id:
            target = self.highest_bidder
            penalty = max(10, int(self.highest_bid * 0.05))
            
            # Deduct from budget
            if hasattr(target, 'update_budget'):
                target.update_budget(penalty) # Positive because budget -= amount
            if hasattr(target, 'session_penalties'):
                target.session_penalties += penalty
            
            # Apply Lockout Cooldown
            if hasattr(target, 'lockout_rounds'):
                target.lockout_rounds = 1
                
            self.log_event(f"PENALTY: {target.id} paid ${penalty} and is LOCKED OUT (1rd).")
        
        # Original withdrawal log
        self.log_event(f"{bidder.id} WITHDREW bid.")
        
        # Handle bid stack fallback
        if bidder and hasattr(bidder, 'withdrawal_count'): 
            bidder.withdrawal_count += 1
            
        if self.bid_stack and self.bid_stack[-1][0].id == bidder.id:
            self.bid_stack.pop()
        
        if self.bid_stack:
            prev_bidder, prev_amount = self.bid_stack[-1]
            self.highest_bid = prev_amount
            self.highest_bidder = prev_bidder
        else:
            self.highest_bid = 0
            self.highest_bidder = None
            
        return True

    def pass_player(self, player):
        # Bug 3 Fix: If player is winning, clicking "Pass" should NOT withdraw their bid.
        # It just marks them as passing for future bids.
        is_winning = (self.highest_bidder and self.highest_bidder.id == player.id)
        
        if is_winning:
            self.log_event(f"{player.id} is winning. PASS ignored.")
            # We still set passing to True so they don't get auto-bid (if that logic exists)
            # but we don't call withdraw_bid.
        else:
            self.log_event(f"{player.id} PASSED.")
            if hasattr(player, 'pass_count'): player.pass_count += 1
            # If they weren't winning, they just exit the loop.
            # (Note: withdraw_bid already checks if they are the highest bidder, 
            # but being explicit here is safer).
            
        player.is_passing = True
        return True

    def run_tick(self):
        if not self.is_active or self.is_paused: return
            
        # 1. Process Pending Withdrawal Queue (Bug 7)
        for wd in self.pending_withdrawals[:]:
            wd['ticks_left'] -= 1
            if wd['ticks_left'] <= 0:
                # Find the agent to check its bid_history
                agent_obj = next((a for a in self.agents if a.id == wd['id']), None)
                
                # Only log withdrawal if the agent actually placed a bid in this round
                if agent_obj and agent_obj.bid_history:
                    # Bug 4 Fix: Visual Signal for "Last Bot Withdrawn"
                    active_bots = [a for a in self.agents if a.is_active and a.state == "Active"]
                    if not active_bots and self.human_player and not self.human_player.has_withdrawn:
                        if not self.last_bidder_standing:
                            self.log_event(f"*** {wd['id']} has WITHDRAWN - YOU HOLD THE FLOOR ***")
                            self.last_bidder_standing = True
                        else:
                            self.log_event(f"{wd['id']} has WITHDRAWN.")
                    else:
                        self.log_event(f"{wd['id']} has WITHDRAWN.")
                else:
                    # If no bids were placed, it's a pass, not a withdrawal
                    self.log_event(f"{wd['id']} has PASSED.")
                
                self.pending_withdrawals.remove(wd)

        # 2. Update Timer
        active_participants = [a for a in self.agents if a.is_active and a.state == "Active"]
        if self.human_player and not self.human_player.has_withdrawn and not self.human_player.is_passing:
            active_participants.append(self.human_player)
            
        # Lone Bidder Acceleration: 
        # If one person is left and they ARE the high bidder, finish now!
        if len(active_participants) == 1 and self.highest_bidder:
            if active_participants[0].id == self.highest_bidder.id:
                if self.current_patience > 0:
                    self.current_patience = 0 # Snap to finish
        
        self.current_patience -= 1
        
        # Determine internal state thresholds
        new_state = "Active"
        if self.current_patience <= 0:
            self.auction_locked = True # Final lock
            if self.highest_bidder:
                self.log_event("SOLD!")
            else:
                self.log_event("PASSED (Unsold)")
            self.resolve_round()
            return
        elif self.current_patience <= 2:
            self.auction_locked = True
        elif self.current_patience <= 10:
            new_state = "Going Twice"
        elif self.current_patience <= 25:
            new_state = "Going Once"

        # 3. AI Turn
        active_agents = [a for a in self.agents if a.is_active and a.state == "Active"]
        # Use a shuffled copy for processing order, but keep self.agents order consistent
        shuffled_active_agents = list(active_agents)
        random.shuffle(shuffled_active_agents)
        
        # Notify agents of timer tick
        # Below 15 ticks (Going Once/Twice), notify every tick for fluid hesitation
        # Above 15, notify at 25 for early sniping checks
        if (self.current_patience <= 15) or (self.current_patience == 25):
            from src.config import MIN_INCREMENT
            event_data = {
                'ticks_remaining': self.current_patience,
                'current_price': self.highest_bid,
                'min_increment': MIN_INCREMENT
            }
            for agent in shuffled_active_agents: # Iterate over shuffled copy
                prev_agent_state = agent.state
                was_watching = getattr(agent, 'is_watching', False)
                agent.handle_event("timer_tick", event_data)
                
                # Log hesitation for Balanced bots
                if not was_watching and getattr(agent, 'is_watching', False):
                    self.log_event(f"{agent.id} is hesitating...")

                if prev_agent_state == "Active" and agent.state == "Withdraw":
                    self._enqueue_withdrawal(agent.id)
                    agent.is_active = False
        
        # Recalculate active list (in case agents withdrew during timer_tick)
        active_agents = [a for a in self.agents if a.is_active and a.state == "Active"]
        active_participants = list(active_agents)
        if self.human_player and not self.human_player.has_withdrawn and not self.human_player.is_passing:
            active_participants.append(self.human_player)

        shuffled_active_agents = list(active_agents)
        random.shuffle(shuffled_active_agents)

        # Context for bidding
        auction_state = {
            'current_price': self.highest_bid,
            'highest_bidder_id': self.highest_bidder.id if self.highest_bidder else None,
            'ticks_remaining': self.current_patience,
            'state': self.auction_state,
            'active_participant_count': len(active_participants)
        }
        
        from src.config import MIN_INCREMENT
        bids_this_tick = 0
        for agent in shuffled_active_agents: # Iterate over shuffled copy
            # Bug 6: Dispatch budget warning if they're near bankruptcy
            if (self.highest_bid + 2 * MIN_INCREMENT) > agent.budget:
                agent.handle_event("budget_warning", {
                    'current_price': self.highest_bid,
                    'min_increment': MIN_INCREMENT,
                    'spite_delay': random.randint(2, 5)
                })

            if bids_this_tick >= 2: continue
            
            # Bug E Logic: Check for the spite pause
            if agent.has_spite_bid and agent.is_spite_armed and agent.spite_cooldown > 0:
                 # Just wait (pause)
                 pass
            elif agent.has_spite_bid and agent.is_spite_armed and agent.spite_cooldown == 0:
                 self.log_event(f"!!! {agent.id} triggers SPITE BID (Final Stand) !!!")

            bid = agent.calculate_bid(auction_state, min_increment=MIN_INCREMENT)
            if bid:
                if self.place_bid(agent, bid):
                    bids_this_tick += 1
                    new_state = "Active" # Bid reset the timer state
        
        # Bug 1 Fix: Only log the state announcement if NO ONE bid in this tick
        if new_state != self.auction_state:
            if new_state == "Going Once": 
                self.log_event("Going once...")
            elif new_state == "Going Twice": 
                self.log_event("Going twice...")
            self.auction_state = new_state
            self.last_state_change_tick = self.ticks

        self.ticks += 1

    def resolve_round(self):
        self.is_active = False
        profit = 0
        winner_id = "None"
        
        # Win Protection: Ensure the highest bidder hasn't withdrawn or passed
        is_disqualified = False
        if self.highest_bidder:
            h = self.highest_bidder
            # Check for player or agent disqualification
            if getattr(h, 'has_withdrawn', False) or getattr(h, 'is_passing', False):
                is_disqualified = True
            elif hasattr(h, 'state') and h.state in ["Withdraw", "Pass"]:
                is_disqualified = True
                
        if self.highest_bidder and not is_disqualified:
            winner_id = self.highest_bidder.id
            true_val = self.current_item.get_true_value()
            profit = true_val - self.highest_bid
            
            self.highest_bidder.update_budget(self.highest_bid)
            if hasattr(self.highest_bidder, 'session_profit'):
                self.highest_bidder.session_profit += profit
            if hasattr(self.highest_bidder, 'session_spent'):
                self.highest_bidder.session_spent += self.highest_bid
            if hasattr(self.highest_bidder, 'items_won'):
                self.highest_bidder.items_won += 1
            if hasattr(self.highest_bidder, 'items_value_won'):
                self.highest_bidder.items_value_won += true_val
        elif is_disqualified:
             self.log_event(f"DISQUALIFIED: {self.highest_bidder.id} withdrew/passed and cannot win.")
             winner_id = "None (Disqualified)"
             # No budget update, no profit
            
        res = {
            "item_value": self.current_item.get_true_value(),
            "winning_bid": self.highest_bid,
            "winner": winner_id,
            "profit": profit
        }
        
        if winner_id.startswith("None"):
             self.log_event(f"RESULT: Item goes UNSOLD | Value: ${res['item_value']}")
        else:
             self.log_event(f"RESULT: Winner {winner_id} for ${self.highest_bid} | Value: ${res['item_value']} | Profit: ${profit}")
        # Decrement lockout rounds for all participants (User Refined Design)
        if self.human_player:
            self.human_player.lockout_rounds = max(0, self.human_player.lockout_rounds - 1)
        for agent in self.agents:
            agent.lockout_rounds = max(0, agent.lockout_rounds - 1)

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