# src/config.py

# --- ITEM GENERATION SETTINGS ---
ITEM_MEAN = 100
ITEM_STD = 25
ITEM_MIN_VALUE = 40
ITEM_MAX_VALUE = 200

# --- HINT LOGIC ---
HINT_CONFIG = {
    "Low market interest":      {'range': (10, 60),   'base_value': 35,  'safe_cap': 50},
    "Below average demand":     {'range': (50, 90),   'base_value': 70,  'safe_cap': 85},
    "Decent demand":            {'range': (80, 120),  'base_value': 100, 'safe_cap': 110},
    "Strong market interest":   {'range': (110, 150), 'base_value': 130, 'safe_cap': 140},
    "Extremely valuable item":  {'range': (140, 250), 'base_value': 180, 'safe_cap': 200}
}

# --- ITEM SPRITES (BY DEMAND TIER) ---
ITEM_SPRITES = {
    "Low market interest": ["assets/images/items/low_demand_1.png", "assets/images/items/low_demand_2.png"],
    "Below average demand": ["assets/images/items/below_average_1.png", "assets/images/items/below_average_2.png"],
    "Decent demand": ["assets/images/items/decent_1.png", "assets/images/items/decent_2.png"],
    "Strong market interest": ["assets/images/items/strong_1.png", "assets/images/items/strong_2.png"],
    "Extremely valuable item": ["assets/images/items/extreme_1.png", "assets/images/items/extreme_2.png"],
}

ITEM_METADATA = {
    "assets/images/items/low_demand_1.png": {"name": "Small Potion Bottle", "description": "Recovered experimental potion from a sealed laboratory archive."},
    "assets/images/items/low_demand_2.png": {"name": "Coin Pouch", "description": "Leather pouch of copper coins dated 1920, light historical wear."},
    "assets/images/items/below_average_1.png": {"name": "Basic Dagger", "description": "Standard forged dagger from an early expedition kit, well preserved."},
    "assets/images/items/below_average_2.png": {"name": "Leather Boots", "description": "Vintage 1988 leather boots, durable construction with visible aging."},
    "assets/images/items/decent_1.png": {"name": "Magic Scroll", "description": "Ancient scroll with faded arcane script, likely functional."},
    "assets/images/items/decent_2.png": {"name": "Silver Ring", "description": "Sterling silver ring with a polished stone, early artisan work."},
    "assets/images/items/strong_1.png": {"name": "Vintage Mirror", "description": "Ornate antique mirror with aged glass and refined frame detailing."},
    "assets/images/items/strong_2.png": {"name": "Jeweled Sword", "description": "Elegant ceremonial sword with gem-inlaid hilt and fine engraving."},
    "assets/images/items/extreme_1.png": {"name": "Crown", "description": "Royal gold crown set with rare gemstones, well-preserved condition."},
    "assets/images/items/extreme_2.png": {"name": "Vintage Vase", "description": "Exquisite antique vase with intricate craftsmanship, high collector value."}
}

# --- AI PERSONALITIES ---
STRATEGY_CONFIG = {
    "Aggressive": {
        'noise_range': (-0.05, 0.20), 'risk_ceiling': 1.08, 'profit_target': 0.01,
        'reaction_speed': (8, 14), 'aggressiveness': 0.9, 'tactics': ['jump_bid', 'intimidate']
    },
    "Balanced": {
        'noise_range': (-0.12, 0.12), 'risk_ceiling': 1.05, 'profit_target': 0.05,
        'reaction_speed': (8, 14), 'aggressiveness': 0.5, 'tactics': ['bait']
    },
    "Conservative": {
        'noise_range': (-0.20, -0.02), 'risk_ceiling': 0.98, 'profit_target': 0.10,
        'reaction_speed': (12, 18), 'aggressiveness': 0.1, 'tactics': ['snipe']
    }
}

# --- TACTIC CONFIGURATION ---
TACTIC_CONFIG = {'hesitation_chance': 0.10, 'jump_bid_chance': 0.20}

# --- GLOBAL GAMEPLAY ---
MIN_INCREMENT = 5
POWERUP_COST = 15

# --- PLAYSTYLE DESCRIPTIONS (FOR OVERALL STATS TOOLTIPS) ---
PLAYSTYLE_DESCRIPTIONS = {
    "The Strategist": "Balanced and [H]adaptive[/H]; you adjust timing based on the room's energy. Versatile but requires [H]constant focus[/H] during intense bidding wars.",
    "The Tactician": "Uses calculated risks to [H]outmaneuver[/H] others. Maintains a steady win rate but risks getting caught in [H]personal wars[/H] that slim profits.",
    "The Value Hunter": "Extremely selective; only bids on [H]guaranteed deals[/H]. Maximizes ROI but often loses items to [H]faster bidding styles[/H].",
    "The Sniper": "Waits for the [H]final seconds[/H] to strike. Minimizes bidding wars but risks being [H]locked out[/H] if the round ends prematurely.",
    "The Gambler": "Bids based on [H]gut feeling[/H] rather than estimates. Can win high-value items but faces a high risk of [H]overpayment[/H].",
    "The Bully": "Uses [H]large jump-bids[/H] to intimidate rivals early. Scares off cautious bidders but risks starting with an [H]excessive price[/H].",
    "The Hesitator": "Frequently [H]withdraws bids[/H] mid-round. Great for baiting others to bid higher, but builds a reputation for [H]indecision[/H].",
    "The Machine": "Rapid-fire bidding keeps [H]pressure and pace high[/H]. Forces opponents into emotional mistakes but can lead to [H]reckless spending[/H].",
    "Absentee": "Registered but placed [H]few or no bids[/H]. Preserves budget entirely but results in [H]zero items won[/H] and no experience gained.",
    "The Ghost": "Watches every round but [H]never commits[/H] to a bid. Offers perfect observation with [H]zero risk[/H], but misses every profitable deal.",
    "The Observer": "Only bids on [H]1 or 2 items[/H] per game. Ensures a high-quality collection but risks [H]leaving empty-handed[/H] if contested.",
    "The Stoic": "Patient and rational; [H]immune to market hype[/H]. Results in consistent long-term performance but can be [H]out-maneuvered[/H] by sudden jump bids.",
    "The High Roller": "Values [H]collection completion[/H] over profit. Guarantees winning almost any item but risks [H]total bankruptcy[/H] due to thin margins."
}
