
# Item Generation
ITEM_MEAN = 100
ITEM_STD = 25
ITEM_MIN_VALUE = 40
ITEM_MAX_VALUE = 200

# Hint Logic (Overlapping Ranges)
# Format: "Hint Text": {'range': (min_signal, max_signal), 'base_value': numeric_anchor}
HINT_CONFIG = {
    "Low market interest":      {'range': (0, 75),    'base_value': 60},
    "Below average demand":     {'range': (65, 105),  'base_value': 85},
    "Decent demand":            {'range': (95, 135),  'base_value': 110},
    "Strong market interest":   {'range': (125, 165), 'base_value': 145},
    "Extremely valuable item":  {'range': (155, 999), 'base_value': 180}
}

# AI Strategies
STRATEGY_CONFIG = {
    "Aggressive": {
        'noise_range': (-0.05, 0.20),
        'bid_limit_mult': 1.30,
        'reaction_chance': 0.70
    },
    "Conservative": {
        'noise_range': (-0.20, 0.05),
        'bid_limit_mult': 1.05,
        'reaction_chance': 0.30
    },
    "Random": {
        # Random AI behaves differently, handled in code
        'bid_limit_mult': 1.0, 
        'reaction_chance': 0.50
    }
}
