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
        # 2. Loop for 2 Rounds
        for round_num in range(1, 3):
            auction.start_round(round_num)
            
            # Print Initial State
            item = auction.current_item
            true_val = item.get_true_value()
            hint = item.get_hint()
            
            log("-" * 40)
            log(f"--- ROUND {round_num} START ---")
            log("-" * 40)
            log(f"Item: True {true_val} | Hint: \"{hint}\"")
            
            log("STARTING BUDGETS:")
            for agent in auction.agents:
                log(f"   {agent.id}: ${agent.budget}")
            log(f"   Player: ${human.budget}")

            # 3. Running Ticks
            for t in range(20):
                auction.run_tick()
                
                # INJECT PLAYER BID in Round 1 only to force a win/loss scenario?
                if round_num == 1 and t == 3: 
                     if auction.highest_bid < 110: 
                         human.place_bid(auction, 120)

            # 4. Resolve
            result = auction.resolve_round()
            
            log("-" * 40)
            log(f"ROUND {round_num} RESULT: Winner {result['winner']} for ${result['winning_bid']}")
            log("-" * 40)

if __name__ == "__main__":
    run_simulation()
