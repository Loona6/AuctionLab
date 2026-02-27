import pygame
from src.constants import *
from src.ui.components import NeonButton, draw_text
from src.logic.data_manager import DataManager

# --- Theme Colors ---
THEME_BG = (20, 22, 35)
THEME_CARD_BG = (32, 34, 50)
THEME_BORDER = (60, 65, 85)
THEME_ACCENT_GOLD = (255, 215, 0)
THEME_ACCENT_GREEN = (46, 204, 113)
THEME_ACCENT_BLUE = (52, 152, 219)
THEME_ACCENT_CYAN = (0, 255, 255)
THEME_ACCENT_RED = (231, 76, 60)
THEME_TEXT_MAIN = (236, 240, 241)
THEME_TEXT_SUB = (149, 165, 166)

class HighScoreScreen:
    def __init__(self):
        self.font_header = pygame.font.SysFont(FONT_NAME, 50, bold=True)
        self.font_val = pygame.font.SysFont(FONT_NAME, 55, bold=True)
        self.font_lbl = pygame.font.SysFont(FONT_NAME, 22)
        self.font_btn = pygame.font.SysFont(FONT_NAME, 20)
        
        self.btn_back = NeonButton(40, 40, 100, 45, "BACK", THEME_BORDER, "back")

    def handle_events(self, event):
        if self.btn_back.is_clicked(event):
            return "back"
        return None

    def update(self):
        self.btn_back.update(pygame.mouse.get_pos())

    def draw(self, surface):
        surface.fill(THEME_BG)
        
        # --- Header Section ---
        self.btn_back.draw(surface, self.font_btn)
        draw_text(surface, "HIGH SCORES", SCREEN_WIDTH//2, 60, self.font_header, THEME_ACCENT_GOLD, "center")
        
        # --- Cards Layout System ---
        card_w = 260
        card_h = 240
        gap = 30
        
        # Draw Real Scores
        scores = DataManager.load_highscores()
        if not scores:
            draw_text(surface, "No high scores yet!", SCREEN_WIDTH//2, 300, self.font_lbl, THEME_TEXT_SUB, "center")
            return
            
        # Determine Top values
        top_profit = scores[0]['profit']
        most_items = max([s['items'] for s in scores])
        
        # Load unified session count from stats
        stats = DataManager.load_stats()
        total_sessions = stats.get("total_sessions", 0)
        
        # Center cards
        start_x = (SCREEN_WIDTH - (card_w * 3 + gap * 2)) // 2
        start_y = (SCREEN_HEIGHT - card_h) // 2 + 30
        
        # 1. Highest Profit Card
        p_color = THEME_ACCENT_GREEN if top_profit >= 0 else THEME_ACCENT_RED
        self._draw_trophy_card(surface, start_x, start_y, card_w, card_h, 
                             "BEST PROFIT", f"$ {top_profit:,}", 
                             scores[0]['name'], p_color)
                             
        # 2. Most Items Card
        self._draw_trophy_card(surface, start_x + card_w + gap, start_y, card_w, card_h, 
                             "MOST ITEMS", f"{most_items} / 5", "Best Collection", THEME_ACCENT_BLUE)
                             
        # 3. Sessions Card
        self._draw_trophy_card(surface, start_x + (card_w + gap)*2, start_y, card_w, card_h, 
                             "SESSIONS", f"{total_sessions}", "Total Played", THEME_ACCENT_GOLD)

    def _draw_trophy_card(self, surface, x, y, w, h, title, value, subtext, accent_color):
        rect = pygame.Rect(x, y, w, h)
        pygame.draw.rect(surface, THEME_CARD_BG, rect, border_radius=16)
        pygame.draw.rect(surface, accent_color, rect, 2, border_radius=16)
        
        draw_text(surface, title, rect.centerx, y + 40, self.font_lbl, THEME_TEXT_SUB, "center")
        draw_text(surface, value, rect.centerx, y + h // 2, self.font_val, THEME_TEXT_MAIN, "center")
        draw_text(surface, subtext, rect.centerx, y + h - 40, self.font_lbl, accent_color, "center")