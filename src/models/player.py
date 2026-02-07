class Player:
    def __init__(self, name="Player", budget=500):
        self.id = name # Use name as ID for compatibility with agents
        self.name = name
        self.budget = budget
        self.is_active = True
    
    def place_bid(self, auction, amount):
        """
        Attempt to place a bid in the given auction.
        Returns: True if successful, False otherwise.
        """
        if not self.is_active:
            print(f"DEBUG: Player {self.name} is inactive.")
            return False

        # 1. Validation: Budget
        if amount > self.budget:
            print(f"DEBUG: Player bid {amount} rejected. Insufficient funds (Budget: {self.budget}).")
            return False

        # 2. Validation: Auction Rules
        # Min increment check is handled by Auction, but good to check here or catch error?
        # Let's delegate to Auction's place_bid to keep logic centralized, 
        # but we should ensure it meets minimum criteria first to avoid spam.
        min_required = auction.highest_bid + 10 # Assuming min_increment is 10 for now
        if amount < min_required:
             print(f"DEBUG: Player bid {amount} rejected. Must be at least {min_required}.")
             return False

        # 3. Execute Bid
        success = auction.place_bid(self, amount)
        if success:
            # Note: We do NOT deduct budget here. Budget is deducted only upon WINNING the item.
            return True
            
        return False

    def update_budget(self, amount): 
        # Called by Auction when solving the round
        self.budget -= amount
