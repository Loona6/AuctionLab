import sys
import os
import random
import statistics

# Ensure src module is visible
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.models.auction import Auction
from src.config import HINT_CONFIG
from src.models.ai_agent import AIAgent

def run_evaluation_simulation(num_rounds=100):
    report_path = "sim_evaluation_report.txt"
    log_path = "sim_gameplay_logs.txt"
    
    # Clear logs at start
    with open(log_path, "w", encoding="utf-8") as lf:
        lf.write("--- SIMULATION START ---\n")
    
    stats = {
        "wins": {"Aggressive": 0, "Balanced": 0, "Conservative": 0},
        "profits": {"Aggressive": [], "Balanced": [], "Conservative": []},
        "bids": {"Aggressive": [], "Balanced": [], "Conservative": []},
        "no_winner_count": 0
    }

    auction = Auction()
    auction.agents = []
    
    strategies = ["Aggressive", "Balanced", "Conservative"]
    for i in range(2):
        for strat in strategies:
            agent = AIAgent(f"AI-{strat}-{i}", budget=3000, strategy_type=strat)
            auction.agents.append(agent)

    with open(report_path, "w", encoding="utf-8") as f:
        f.write("="*60 + "\n")
        f.write(f"AUCTION LAB SYSTEM EVALUATION REPORT - {num_rounds} ROUNDS\n")
        f.write("="*60 + "\n\n")

        for r in range(1, num_rounds + 1):
            auction.start_round(r)
            item = auction.current_item
            true_val = item.get_true_value()
            hint = item.get_hint()
            
            f.write(f"ROUND {r:03d} | Item: {true_val} | Hint: \"{hint}\"\n")
            
            # Run ticks
            for _ in range(500):
                if not auction.is_active:
                    break
                auction.run_tick()
            
            result = auction.resolve_round()
            winner_id = result['winner']
            winning_bid = result['winning_bid']
            profit = result['profit']

            if winner_id.startswith("None") or winner_id == "No one":
                stats["no_winner_count"] += 1
                f.write(f"  RESULT: NO WINNER ({winner_id})\n")
            else:
                winner_agent = next((a for a in auction.agents if a.id == winner_id), None)
                strat = winner_agent.strategy
                stats["wins"][strat] += 1
                stats["profits"][strat].append(profit)
                stats["bids"][strat].append(winning_bid)
                
                f.write(f"  RESULT: Winner {winner_id} ({strat}) for ${winning_bid} | Profit: ${profit}\n")
            
            # Save logs for this round to a dedicated sim log file
            with open("sim_gameplay_logs.txt", "a", encoding="utf-8") as lf:
                lf.write(f"\n--- ROUND {r} ---\n")
                for line in auction.round_logs:
                    lf.write(line + "\n")

            f.write("-" * 40 + "\n")

        # --- FINAL AGGREGATE SUMMARY ---
        f.write("\n\n" + "="*60 + "\n")
        f.write("FINAL AGGREGATE PERFORMANCE SUMMARY\n")
        f.write("="*60 + "\n\n")

        total_wins = sum(stats["wins"].values())
        
        for strat in strategies:
            wins = stats["wins"][strat]
            win_pct = (wins / total_wins * 100) if total_wins > 0 else 0
            
            profits = stats["profits"][strat]
            avg_profit = statistics.mean(profits) if profits else 0
            total_profit = sum(profits)
            
            bids = stats["bids"][strat]
            avg_bid = statistics.mean(bids) if bids else 0
            
            # ROI estimation
            roi = (total_profit / sum(bids) * 100) if sum(bids) > 0 else 0
            
            f.write(f"STRATEGY: {strat}\n")
            f.write(f"  Wins:            {wins} ({win_pct:.1f}%)\n")
            f.write(f"  Avg Bid:         ${avg_bid:.2f}\n")
            f.write(f"  Avg Profit/Win:  ${avg_profit:.2f}\n")
            f.write(f"  Total Profit:    ${total_profit}\n")
            f.write(f"  Est. ROI:        {roi:.1f}%\n")
            f.write("-" * 30 + "\n")

        f.write(f"\nTOTAL ROUNDS:        {num_rounds}\n")
        f.write(f"TOTAL NO-WIN ROUNDS: {stats['no_winner_count']}\n")
        f.write("="*60 + "\n")

    print(f"Simulation Complete. Evaluation report generated at: {report_path}")

if __name__ == "__main__":
    run_evaluation_simulation(100)
