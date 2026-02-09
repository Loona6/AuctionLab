class PlaystyleAnalyzer:
    @staticmethod
    def analyze(player, total_rounds):
        """
        Sophisticated analysis based on:
        - Bids, Timing, Overbidding (Risk)
        - Withdrawals & Passes
        - Bid Increments & Frequency
        """
        logs = player.bid_logs
        total_bids = len(logs)
        withdrawals = getattr(player, 'withdrawal_count', 0)
        passes = getattr(player, 'pass_count', 0)
        
        if not logs and not passes:
            return "Absentee", "You didn't show up for the bidding! Looking for a bargain that never came?"

        # 1. Base Metrics
        avg_tick = sum(log[1] for log in logs) / max(1, total_bids)
        overbid_count = sum(1 for log in logs if log[3])
        risk_rate = overbid_count / max(1, total_bids)
        
        # 2. Advanced Physical Metrics
        # avg_increment = getattr(player, 'total_increments', 0) / max(1, total_bids)
        # bid_frequency = total_bids / total_rounds
        total_inc = getattr(player, 'total_increments', 0)
        avg_inc = total_inc / max(1, total_bids)
        freq = total_bids / total_rounds
        withdraw_rate = withdrawals / max(1, total_bids) if total_bids > 0 else 0
        
        # 3. Categorization Flags
        is_low_particip = (total_bids < 2 and passes > 2)
        is_very_passive = total_bids == 0
        is_high_risk = risk_rate > 0.4 and total_bids >= 2
        is_aggr = freq > 4.0
        is_early = avg_tick < 60
        is_late = avg_tick > 140
        is_big_spender = avg_inc > 100
        is_nickler = avg_inc < 30 and total_bids > 3
        is_fickle = withdraw_rate > 0.4
        
        # 4. Decision Tree (Priority order)
        if is_very_passive:
            return "The Ghost", "A spectral presence. You watched from the shadows but never left a mark."
        
        if is_fickle:
            return "The Hesitator", "You change your mind as often as the wind. Bidding requires commitment!"
            
        if is_low_particip:
            return "The Observer", "Selective to a fault. You're waiting for a unicorn in a horse race."
            
        if is_aggr and is_early and is_big_spender:
            return "The Bully", "You use your wallet like a sledgehammer, trying to scare others off early."
            
        if is_high_risk and is_big_spender:
            return "The High Roller", "You don't care about 'value' - you want the item, no matter the cost. Pure adrenaline."
            
        if is_high_risk:
            return "The Gambler", "You often bid based on gut feeling, frequently pushing past safe estimates."
            
        if is_late and freq < 2.0:
            return "The Sniper", "One shot, one kill. You wait for the chaos to die down before striking."
            
        if is_aggr:
            return "The Machine", "Rapid-fire bidding! You're everywhere at once, keeping the pressure high."
            
        if is_nickler and not is_high_risk:
            return "The Value Hunter", "You're all about the tiny margins. Nickel and diming your way to a deal."
            
        if avg_tick > 80 and avg_tick < 120 and freq < 3.0 and not is_high_risk:
            return "The Stoic", "Patient, rational, and immune to the hype. You bid when it makes sense."
            
        return "The Tactician", "A balanced approach. You adapt your timing and aggression to the room."

    @staticmethod
    def get_behavior_metrics(player):
        # Ensure we don't crash if logs are empty
        if not player.bid_logs:
            return {
                "avg_reaction": "N/A",
                "first_bid_time": "N/A",
                "risk": "Low",
                "overbid_rate": "0%",
                "withdrawals": getattr(player, 'withdrawal_count', 0),
                "passes": getattr(player, 'pass_count', 0)
            }
            
        # 5 ticks = 1 second
        avg_tick = sum(log[1] for log in player.bid_logs) / len(player.bid_logs)
        reaction_time = avg_tick / 5.0
        
        rounds_seen = set()
        first_ticks = []
        for log in player.bid_logs:
            r = log[0]
            if r not in rounds_seen:
                first_ticks.append(log[1])
                rounds_seen.add(r)
        
        avg_first_bid = (sum(first_ticks) / len(first_ticks)) / 5.0 if first_ticks else 0
        risk_level = "High" if sum(1 for log in player.bid_logs if log[3]) / len(player.bid_logs) > 0.3 else "Low"
        
        return {
            "avg_reaction": f"{reaction_time:.1f}s",
            "first_bid_time": f"{avg_first_bid:.1f}s",
            "risk": risk_level,
            "overbid_rate": f"{int((sum(1 for log in player.bid_logs if log[3]) / len(player.bid_logs)) * 100)}%",
            "withdrawals": getattr(player, 'withdrawal_count', 0),
            "passes": getattr(player, 'pass_count', 0)
        }
