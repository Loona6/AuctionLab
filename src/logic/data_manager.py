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
                # Filter out sessions with no items won and sort
                valid = [s for s in data if s.get('items', 0) > 0]
                return sorted(valid, key=lambda x: x['profit'], reverse=True)
        except (json.JSONDecodeError, IOError):
            return []

    @classmethod
    def save_highscore(cls, player_name, profit, items_won):
        if items_won <= 0:
            return # Don't save sessions where no items were won
            
        cls.ensure_data_dir()
        scores = cls.load_highscores()
        scores.append({
            "name": player_name,
            "profit": profit,
            "items": items_won,
            "date": "" # Could add timestamp
        })
        # Sort by profit descending and keep top 10
        scores = sorted(scores, key=lambda x: x['profit'], reverse=True)[:10]
        with open(cls.HIGHSCORES_FILE, "w") as f:
            json.dump(scores, f, indent=4)

    @classmethod
    def load_stats(cls):
        if not os.path.exists(cls.STATS_FILE):
            return {
                "total_sessions": 0,
                "lifetime_profit": 0,
                "total_items": 0,
                "playstyle_counts": {}
            }
        try:
            with open(cls.STATS_FILE, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}

    @classmethod
    def update_stats(cls, session_profit, session_items, playstyle):
        cls.ensure_data_dir()
        stats = cls.load_stats()
        stats["total_sessions"] = stats.get("total_sessions", 0) + 1
        stats["lifetime_profit"] = stats.get("lifetime_profit", 0) + session_profit
        stats["total_items"] = stats.get("total_items", 0) + session_items
        
        counts = stats.get("playstyle_counts", {})
        counts[playstyle] = counts.get(playstyle, 0) + 1
        stats["playstyle_counts"] = counts
        
        # Track items won per playstyle for win rate calculation
        wins_mapping = stats.get("playstyle_wins", {})
        wins_mapping[playstyle] = wins_mapping.get(playstyle, 0) + session_items
        stats["playstyle_wins"] = wins_mapping
        
        with open(cls.STATS_FILE, "w") as f:
            json.dump(stats, f, indent=4)
