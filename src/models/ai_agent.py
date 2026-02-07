import random
from src.config import STRATEGY_CONFIG, HINT_CONFIG

class AIAgent:
    def __init__(self, agent_id, budget, strategy_type=None):
        self.id = agent_id
        self.budget = budget
        
        if strategy_type:
            self.strategy = strategy_type
        else:
            self.strategy = random.choice(["Aggressive", "Conservative", "Random"])
            
        self.estimated_value = 0
        self.max_bid_limit = 0
        self.bid_history = []
        self.is_active = True

    def form_belief(self, hint_text):
        """Estimate the item's value based on the hint and agent strategy."""
        
        # 1. Base value from hint configuration
        if hint_text in HINT_CONFIG:
            base_value = HINT_CONFIG[hint_text]['base_value']
        else:
            base_value = 100 
            
        # 2. Apply strategy bias (noise)
        if self.strategy == "Random":
            self.estimated_value = random.randint(50, 200)
        else:
            config = STRATEGY_CONFIG[self.strategy]
            noise = random.uniform(config['noise_range'][0], config['noise_range'][1])
            self.estimated_value = int(base_value * (1 + noise))
            
        # 3. Set maximum willing bid based on estimate
        if self.strategy == "Random":
            self.max_bid_limit = self.budget
        else:
            mult = STRATEGY_CONFIG[self.strategy]['bid_limit_mult']
            self.max_bid_limit = int(self.estimated_value * mult)

    def calculate_bid(self, current_highest_bid, min_increment):
        """
        Decide whether to bid based on current state.
        Returns amount to bid, or None if passing/quitting.
        """
        if not self.is_active or self.budget <= current_highest_bid:
            return None

        # Calculate potential new bid
        target_bid = current_highest_bid + min_increment
        
        # Check against budget
        if target_bid > self.budget:
            return None

        # Decision Logic
        should_bid = False
        
        if self.strategy == "Random":
            # Randomly decides to bid or not, regardless of value
            if random.random() < 0.5: 
                should_bid = True
        else:
            # Rational(ish) agents check against their limit
            if target_bid <= self.max_bid_limit:
                # Basic logic: always bid if under limit
                # (Could add 'reaction_chance' here for more "skipping" behavior if desired,
                # but for now we assume they want to win if it's within their price)
                should_bid = True
            else:
                # Check for "Counter" reaction (over-bidding slightly)
                reaction_chance = STRATEGY_CONFIG[self.strategy]['reaction_chance']
                if random.random() < reaction_chance:
                    # One last push? (Simplified: only if it doesn't exceed budget significantly)
                    # For strictness, let's stick to the limit unless reaction logic explicitly raises the limit.
                    # Per valid design: "Stops at estimated_value * multiplier". 
                    # So if we are here, we are ALREADY past the limit.
                    should_bid = False 

        if should_bid:
            self.bid_history.append(target_bid)
            return target_bid
            
        return None

    def update_budget(self, amount):
        self.budget -= amount
