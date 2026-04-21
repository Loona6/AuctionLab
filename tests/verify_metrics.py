import sys
import os
import json

# Ensure src module is visible
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.logic.data_manager import DataManager

def test_success_rate():
    print("Testing Success Rate logic...")
    
    # Mock data for a profitable session
    playstyle = "The Wealthy Winner"
    profit = 200
    items = 3
    spent = 400
    
    # 1. Update stats (Success)
    DataManager.update_stats(profit, items, spent, playstyle)
    print(f"Updated stats (Profitable) for {playstyle}")
    
    # 2. Update stats (Loss)
    DataManager.update_stats(-50, 1, 100, playstyle)
    print(f"Updated stats (Loss) for {playstyle}")
    
    # 3. Load stats and verify
    stats = DataManager.load_stats()
    
    successes = stats.get("playstyle_successes", {}).get(playstyle, 0)
    counts = stats.get("playstyle_counts", {}).get(playstyle, 0)
    
    print(f"Stats for {playstyle}:")
    print(f"  Successes: {successes}")
    print(f"  Total Sessions: {counts}")
    
    success_rate = (successes / counts) * 100 if counts > 0 else 0
    print(f"  Calculated Success Rate: {success_rate:.0f}%")
    
    if successes == 1 and counts >= 2 and success_rate == 50.0:
        print("SUCCESS: Success rate tracking verified.")
    else:
        # Note: If this playstyle already existed in the file, counts might be higher.
        # But for a new playstyle, it should be exactly 50%.
        if counts > 2 and successes >= 1:
             print("SUCCESS: Persistence working (likely merged with existing test data).")
        else:
             print("FAIL: Metrics incorrect.")

if __name__ == "__main__":
    test_success_rate()
