import json
import os

class DataManager:
    DATA_DIR = "data"
    HIGHSCORES_FILE = os.path.join(DATA_DIR, "highscores.json")
    STATS_FILE = os.path.join(DATA_DIR, "statistics.json")

    @classmethod
    def ensure_data_dir(cls):
        if not os.path.exists(cls.DATA_DIR):
            os.makedirs(cls.DATA_DIR)

    @classmethod
    def load_highscores(cls):
        if not os.path.exists(cls.HIGHSCORES_FILE):
            return []
        try:
            with open(cls.HIGHSCORES_FILE, "r") as f:
                data = json.load(f)
                # Sort by profit descending (Full history preserved)
                return sorted(data, key=lambda x: x['profit'], reverse=True)
        except (json.JSONDecodeError, IOError):
            return []

    @classmethod
    def save_highscore(cls, player_name, profit, items_won, net_worth):
        cls.ensure_data_dir()
        scores = cls.load_highscores()
        scores.append({
            "name": player_name,
            "profit": profit,
            "items": items_won,
            "net_worth": net_worth,
            "date": "" # Placeholder for timestamp
        })
        # Note: We now keep the full history in the file
        with open(cls.HIGHSCORES_FILE, "w") as f:
            json.dump(scores, f, indent=4)

    @classmethod
    def load_stats(cls):
        if not os.path.exists(cls.STATS_FILE):
            return {
                "total_sessions": 0,
                "lifetime_profit": 0,
                "total_items": 0,
                "max_profit": 0,
                "max_items": 0,
                "total_wins": 0,
                "playstyle_counts": {}
            }
        try:
            with open(cls.STATS_FILE, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}

    @classmethod
    def update_stats(cls, session_profit, session_items, session_spent, playstyle, is_win=False):
        cls.ensure_data_dir()
        stats = cls.load_stats()
        stats["total_sessions"] = stats.get("total_sessions", 0) + 1
        stats["lifetime_profit"] = stats.get("lifetime_profit", 0) + session_profit
        stats["total_items"] = stats.get("total_items", 0) + session_items
        
        if is_win:
            stats["total_wins"] = stats.get("total_wins", 0) + 1
        
        # New Peak Metrics
        stats["max_profit"] = max(stats.get("max_profit", 0), session_profit)
        stats["max_items"] = max(stats.get("max_items", 0), session_items)
        
        counts = stats.get("playstyle_counts", {})
        counts[playstyle] = counts.get(playstyle, 0) + 1
        stats["playstyle_counts"] = counts
        
        # Track items won per playstyle for win rate calculation
        wins_mapping = stats.get("playstyle_wins", {})
        wins_mapping[playstyle] = wins_mapping.get(playstyle, 0) + session_items
        stats["playstyle_wins"] = wins_mapping
        
        # Track total profit per playstyle for avg profit calculation
        profits_mapping = stats.get("playstyle_profits", {})
        profits_mapping[playstyle] = profits_mapping.get(playstyle, 0) + session_profit
        stats["playstyle_profits"] = profits_mapping
        
        # Track total spent per playstyle for ROI calculation
        spent_mapping = stats.get("playstyle_spent", {})
        spent_mapping[playstyle] = spent_mapping.get(playstyle, 0) + session_spent
        stats["playstyle_spent"] = spent_mapping
        
        # Track number of profitable sessions (Successes)
        success_mapping = stats.get("playstyle_successes", {})
        if session_profit > 0:
            success_mapping[playstyle] = success_mapping.get(playstyle, 0) + 1
        stats["playstyle_successes"] = success_mapping
        
        with open(cls.STATS_FILE, "w") as f:
            json.dump(stats, f, indent=4)
