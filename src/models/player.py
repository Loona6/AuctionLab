from src.config import MIN_INCREMENT, HINT_CONFIG

class Player:
    def __init__(self, name="Player", budget=500):
        self.id = name # Use name as ID for compatibility with agents
        self.name = name
        self.budget = budget
        self.is_active = True
        
        # --- Analytics & Persistence ---
        self.bid_logs = [] # (round, tick, amount, is_overbid)
        self.session_profit = 0
        self.lifetime_profit = 0
        self.items_won = 0
        self.items_value_won = 0
        self.sessions_played = 0
        
        # --- Round State ---
        self.is_passing = False
        self.has_withdrawn = False
        self.first_bid_tick = -1 # Track tick of first bid in round
        
        # --- Total Session Stats (Reset on new game) ---
        self.withdrawal_count = 0
        self.pass_count = 0
        self.total_bid_count = 0
        self.total_increments = 0
    
    def place_bid(self, auction, amount):
        """
        Attempt to place a bid in the given auction.
        Returns: True if successful, False otherwise.
        """
        if not self.is_active:
            return False

        # 1. Validation: Budget
        if amount > self.budget:
            return False

        # 2. Validation: Auction Rules
        min_required = auction.highest_bid + MIN_INCREMENT 
        if amount < min_required:
             return False

        # 3. Analytics: Check if overbidding (optional logic)
        # We consider a bid 'overbid' if it is > 1.1x the base value of the hint
        is_overbid = False
        hint = auction.current_item.get_hint()
        if hint in HINT_CONFIG:
            base_val = HINT_CONFIG[hint]['base_value']
            if amount > base_val * 1.1:
                is_overbid = True

        # 4. Execute Bid
        success = auction.place_bid(self, amount)
        if success:
            # Stats for analyzer
            self.total_bid_count += 1
            increment = amount - auction.highest_bid if auction.highest_bid > 0 else amount
            self.total_increments += increment
            
            # Log the bid for analytical purposes
            current_tick = auction.ticks
            
            # Track first bid of the round
            if self.first_bid_tick == -1:
                self.first_bid_tick = current_tick
                
            self.bid_logs.append((getattr(auction, 'round_num', 0), current_tick, amount, is_overbid))
            
            # Reset round states if player bids
            self.is_passing = False
            self.has_withdrawn = False
            
            return True
            
        return False

    def update_budget(self, amount): 
        # Called by Auction when solving the round
        self.budget -= amount
