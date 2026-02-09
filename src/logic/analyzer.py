class PlaystyleAnalyzer:
    @staticmethod
    def analyze(player, total_rounds):
        """
        Analyze player logs and categorize their playstyle.
        Incorporates bids, timing, withdrawals, and passing behavior.
        """
        if not player.bid_logs and not getattr(player, 'pass_count', 0):
            return "Absentee", "You didn't show up for the bidding! Looking for a bargain that never came?"

        total_bids = len(player.bid_logs)
        avg_tick = sum(log[1] for log in player.bid_logs) / max(1, total_bids)
        overbid_count = sum(1 for log in player.bid_logs if log[3])
        withdrawals = getattr(player, 'withdrawal_count', 0)
        passes = getattr(player, 'pass_count', 0)
        
        # Heuristics
        participation_rate = total_bids / total_rounds
        is_low_participation = participation_rate < 0.6 and total_bids < 3
        is_high_risk = (overbid_count / max(1, total_bids) > 0.3) and (total_bids > 1)
        is_aggressive = participation_rate > 3.0
        is_early = avg_tick < 70
        is_late = avg_tick > 140
        is_indecisive = (withdrawals > 2) or (withdrawals > 0 and total_bids < 2)
        is_cautious = passes > (total_rounds // 2) and total_bids < 3
        
        if is_indecisive:
            return "The Hesitator", "You often second-guess your bids. Withdrawing is safe, but fortune favors the bold!"
        elif is_cautious:
            return "The Minimalist", "You pass frequently, wait-and-see is your motto. Very selective!"
        elif is_low_participation:
            return "The Observer", "You were very selective with your bids, perhaps waiting for a value that never appeared."
        elif is_late and not is_aggressive:
            return "The Sniper", "You wait for the perfect moment to strike, often bidding at the last second."
        elif is_early and is_aggressive:
            return "The Aggressor", "You dominate the auction floor early on, driving prices up quickly."
        elif is_high_risk:
            return "The Gambler", "You often bid above estimated values, relying on guts rather than math."
        elif not is_aggressive and not is_high_risk:
            return "The Stoic", "You bid conservatively and only when the price is right."
        else:
            return "The Tactician", "A balanced approach, adapting your timing and bids to the competition."

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
