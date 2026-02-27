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

# --- AI PERSONALITIES (THE "WAR MODE" REBALANCED) ---
STRATEGY_CONFIG = {
    "Aggressive": {
        'noise_range': (-0.05, 0.20),   # Widened from 0.15
        'risk_ceiling': 1.08,           # Decreased slightly from 1.10 to reduce massive overbids
        'profit_target': 0.01,
        'reaction_speed': (8, 14),      # Much slower baseline response (1.6s - 2.8s)
        'aggressiveness': 0.9,
        'tactics': ['jump_bid', 'intimidate']
    },
    "Balanced": {
        'noise_range': (-0.12, 0.12),   # Widened from 0.10
        'risk_ceiling': 1.05,           # Increased from 1.03 to help compete against Aggressive
        'profit_target': 0.05,
        'reaction_speed': (8, 14),     # Sped up slightly so they don't get locked out (was 10, 16)
        'aggressiveness': 0.5,
        'tactics': ['bait']
    },
    "Conservative": {
        'noise_range': (-0.20, -0.02),  # Widened from -0.15
        'risk_ceiling': 0.98,           # Increased from 0.93: Willing to pay near base
        'profit_target': 0.10,
        'reaction_speed': (12, 18),     # Heavily paced sniper delays (2.4s - 3.6s)
        'aggressiveness': 0.1,
        'tactics': ['snipe']
    }
}

# --- TACTIC CONFIGURATION ---
TACTIC_CONFIG = {
    'hesitation_chance': 0.10,   # Further reduced for more aggressive presence
    'jump_bid_chance': 0.20,
}

# --- GLOBAL GAMEPLAY ---
MIN_INCREMENT = 5   # Reduced from 10 to create more friction