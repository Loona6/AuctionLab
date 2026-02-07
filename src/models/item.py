import random
from src.config import ITEM_MEAN, ITEM_STD, ITEM_MIN_VALUE, ITEM_MAX_VALUE, HINT_CONFIG

class Item:
    def __init__(self):
        # 1. Generate True Value
        raw_value = random.normalvariate(ITEM_MEAN, ITEM_STD)
        self.true_value = int(max(ITEM_MIN_VALUE, min(ITEM_MAX_VALUE, raw_value)))
        
        # 2. Generate Hint immediately
        self.hint_text = self._generate_hint()

    def _generate_hint(self):
        # Step 1: Create noisy perception
        noise = random.uniform(-0.2, 0.2)
        self.perceived_signal = self.true_value * (1 + noise)

        # Step 2: Map to text category using Overlapping Logic
        candidates = []
        for text, data in HINT_CONFIG.items():
            min_s, max_s = data['range']
            if min_s <= self.perceived_signal <= max_s:
                candidates.append(text)
        
        # Fallback if somehow no range matches (shouldn't happen with 0-999 coverage)
        if not candidates:
            return "Unknown item"
            
        return random.choice(candidates)

    def get_true_value(self):
        return self.true_value
        
    def get_hint(self):
        return self.hint_text
