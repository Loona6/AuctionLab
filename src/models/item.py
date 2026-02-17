import random
from src.config import HINT_CONFIG

class Item:
    def __init__(self):
        # 1. Pick a Hint Category first
        # Weighted to make "average" items more common than extreme ones
        self.hint_text = self._pick_weighted_hint()
        
        # 2. Generate True Value strictly within the Hint's range
        hint_data = HINT_CONFIG[self.hint_text]
        min_val, max_val = hint_data['range']
        base = hint_data['base_value']
        
        # Use normal distribution centered on base_value
        # Sigma is set so 3 standard deviations cover the range
        sigma = (max_val - min_val) / 6.0 
        raw_val = random.normalvariate(base, sigma)
        
        # Clamp strictly to range
        self.true_value = int(max(min_val, min(max_val, raw_val)))
        
        # Compatibility attribute (if needed by other files)
        self.perceived_signal = self.true_value

    def _pick_weighted_hint(self):
        options = list(HINT_CONFIG.keys())
        # Corresponds to: Low, Below Avg, Decent, Strong, Extreme
        weights = [15, 25, 35, 20, 5] 
        return random.choices(options, weights=weights, k=1)[0]

    def get_true_value(self):
        return self.true_value
        
    def get_hint(self):
        return self.hint_text