import random
from src.config import HINT_CONFIG, ITEM_SPRITES, ITEM_METADATA

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
        self.premium_hint = None
        self.sprite_path = self._pick_sprite_path()
        
        # 3. Load Metadata based on sprite
        metadata = ITEM_METADATA.get(self.sprite_path, {"name": "Mystery Artifact", "description": "A mysterious item of unknown origin."})
        self.name = metadata["name"]
        self.description = metadata["description"]

    def _pick_weighted_hint(self):
        options = list(HINT_CONFIG.keys())
        # Corresponds to: Low, Below Avg, Decent, Strong, Extreme
        weights = [15, 25, 35, 20, 5] 
        return random.choices(options, weights=weights, k=1)[0]

    def get_true_value(self):
        return self.true_value
        
    def get_hint(self):
        return self.hint_text

    def _pick_sprite_path(self):
        candidates = ITEM_SPRITES.get(self.hint_text, [])
        if not candidates:
            return None
        return random.choice(candidates)

    def get_sprite_path(self):
        return self.sprite_path

    def get_premium_hint(self):
        """Returns a narrower, non-deterministic range around the true value."""
        if self.premium_hint:
            return self.premium_hint
            
        # Use a width of 20 units
        width = 20
        # Randomly offset so true value isn't always at the center
        # True value could be anywhere from 5 to 15 units from the lower bound
        offset = random.randint(5, 15)
        lower = self.true_value - offset
        upper = lower + width
        self.premium_hint = f"Expert Opinion: Value is between ${lower} and ${upper}"
        return self.premium_hint