import sys
import os

# src module is visible
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.models.auction import Auction
from src.config import HINT_CONFIG

from src.models.player import Player

def run_simulation():
    with open("sim_results.txt", "w", encoding="utf-8") as f:
        def log(msg):
            print(msg)
            f.write(msg + "\n")

        # 1. Setup
        auction = Auction()
        human = Player("Human", budget=500)
        auction.add_player(human)
        auction.start_round(1)
        
        # 2. Print Initial State
        item = auction.current_item
        true_val = item.get_true_value()
        hint = item.get_hint()
        signal = item.perceived_signal
        
        log("-" * 40)
        log(f"--- ROUND 1 DETAILED LOG ---")
        log("-" * 40)
        log(f"True Value: {true_val} | Signal: {signal:.2f} | Hint: \"{hint}\"")
        
        # Show theoretical base range for verification
        if hint in HINT_CONFIG:
            r = HINT_CONFIG[hint]['range']
            base = HINT_CONFIG[hint]['base_value']
            log(f"   -> Hint implies signal range {r} and base value {base}")
        else:
            log(f"   -> Hint not found in config?!")

        log("-" * 40)
        log("AGENTS & BELIEFS:")
        for agent in auction.agents:
            # Reconstruct "belief" for display since it's internalized
            base = HINT_CONFIG.get(hint, {}).get('base_value', 100)
            est = agent.estimated_value
            strategy = agent.strategy
            limit = agent.max_bid_limit
            
            log(f"Agent {agent.id} ({strategy}):")
            log(f"   -> Base {base} -> Est {est} -> Max Bid Limit {limit}")

        log("-" * 40)
        log("BIDDING LOG:")
        
        # 3. Running Ticks
        for t in range(20):
            prev_highest = auction.highest_bid
            auction.run_tick()
            
            if auction.highest_bid > prev_highest:
                bidder = auction.highest_bidder.id if auction.highest_bidder else "None"
                log(f"[Tick {t+1}] New Highest: {auction.highest_bid} by {bidder}")

            # 3b. INJECT PLAYER "JUMP BID"
            if t == 3: # At Tick 4 (0-indexed)
                 log(f"*** TRIGGER: Player attempts JUMP BID to 120 ***")
                 # Check current price first to ensure jump is valid
                 if auction.highest_bid < 110: # Ensure valid jump
                     if human.place_bid(auction, 120):
                         log(f"   >>> SUCCESS: Player holds bid at 120.")
                     else:
                         log(f"   >>> FAILED (Validation Error).")
                 else:
                     log(f"   >>> SKIPPED (Price already too high for jump test).")

        # 4. Resolve
        result = auction.resolve_round()
        
        log("-" * 40)
        log("ROUND RESOLUTION:")
        log(f"Winner: {result['winner']}")
        log(f"Winning Bid: {result['winning_bid']}")
        log(f"Item Value: {result['item_value']}")
        log(f"Profit/Loss: {result['profit']}")
        log("-" * 40)

if __name__ == "__main__":
    run_simulation()
