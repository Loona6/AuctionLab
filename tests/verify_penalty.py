import sys
import os

# Ensure src module is visible
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.models.auction import Auction
from src.models.player import Player

def test_penalty_and_lockout():
    print("Testing Withdrawal Penalty and Lockout...")
    
    player = Player("TestUser", budget=5000)
    auction = Auction()
    auction.human_player = player
    
    # Initialize a dummy item so hints/values exist
    from src.models.item import Item
    auction.current_item = Item()
    auction.is_active = True
    
    # 1. Test Small Penalty ($100 bid)
    auction.place_bid(player, 100)
    print(f"Bidding $100. Budget: {player.budget}")
    
    # Withdraw
    auction.withdraw_bid(player)
    # Penalty: max(10, 5% of 100) = 10
    expected_budget = 5000 - 10
    print(f"After Withdraw: Budget {player.budget}, Lockout {player.lockout_rounds}")
    
    assert player.budget == expected_budget
    assert player.lockout_rounds == 1
    
    # 2. Test Scaling Penalty ($400 bid)
    player.lockout_rounds = 0 
    player.budget = 1000
    auction.place_bid(player, 400)
    
    auction.withdraw_bid(player)
    # Penalty: max(10, 5% of 400) = 20
    expected_budget = 1000 - 20
    print(f"After $400 Withdraw: Budget {player.budget}, Lockout {player.lockout_rounds}")
    
    assert player.budget == expected_budget
    
    # 3. Test Lockout Reset
    auction.resolve_round()
    print(f"After Resolve Round: Lockout {player.lockout_rounds}")
    assert player.lockout_rounds == 0

    print("SUCCESS: Penalty and Lockout verified.")

if __name__ == "__main__":
    test_penalty_and_lockout()
