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
        # Back button top-left
        self.btn_back.draw(surface, self.font_btn)
        
        # Title Centered
        draw_text(surface, "HIGH SCORES", SCREEN_WIDTH//2, 60, self.font_header, THEME_ACCENT_GOLD, "center")
        draw_text(surface, "Your All-Time Best Sessions", SCREEN_WIDTH//2, 105, self.font_lbl, THEME_TEXT_SUB, "center")
        
        # --- Cards Layout System ---
        # Dimensions
        card_w = 280
        card_h = 360
        gap = 40
        
        # Calculate Total Width of the group (3 cards + 2 gaps)
        total_group_w = (card_w * 3) + (gap * 2)
        
        # Starting X to perfectly center the group
        start_x = (SCREEN_WIDTH - total_group_w) // 2
        
        # Starting Y to center vertically in the remaining space
        # (Header takes ~150px, so we center in the rest)
        available_h = SCREEN_HEIGHT - 150
        start_y = 150 + (available_h - card_h) // 2 - 20 # -20 visual optical adjustment
        
        # --- Draw The 3 Cards ---
        
        # --- Draw Real Scores ---
        scores = DataManager.load_highscores()
        
        # Determine Top 3 values (default to 0 if not enough entries)
        top_profit = scores[0]['profit'] if len(scores) > 0 else 0
        max_balance = 0 # Future: could track max balance reached
        most_items = max([s['items'] for s in scores]) if scores else 0
        
        # 1. Left Card (Highest Profit)
        self._draw_trophy_card(surface, start_x, start_y, card_w, card_h, 
                             "HIGHEST PROFIT", f"$ {top_profit:,}", 
                             scores[0]['name'] if scores else "N/A", THEME_ACCENT_GREEN)
                             
        # 2. Middle Card (Max Balance Placeholder)
        # For now, let's use the 2nd best score as "Top 2" or "Recent Best"
        second_best = scores[1]['profit'] if len(scores) > 1 else 0
        self._draw_trophy_card(surface, start_x + card_w + gap, start_y, card_w, card_h, 
                             "RUNNER UP", f"$ {second_best:,}", 
                             scores[1]['name'] if len(scores) > 1 else "N/A", THEME_ACCENT_GOLD)
                             
        # 3. Right Card (Most Items)
        self._draw_trophy_card(surface, start_x + (card_w + gap)*2, start_y, card_w, card_h, 
                             "MOST ITEMS", f"{most_items} / 5", "Best Collection", THEME_ACCENT_BLUE)

    def _draw_trophy_card(self, surface, x, y, w, h, title, value, subtext, accent_color):
        rect = pygame.Rect(x, y, w, h)
        
        # 1. Background & Border
        pygame.draw.rect(surface, THEME_CARD_BG, rect, border_radius=16)
        pygame.draw.rect(surface, accent_color, rect, 2, border_radius=16)
        
        # 2. Top Decorative Strip (Centered inside card)
        strip_w = w - 60
        pygame.draw.rect(surface, accent_color, (x + 30, y + 30, strip_w, 4), border_radius=2)
        
        # 3. Text Alignment Zones
        # We calculate exact Y centers for Title, Value, and Footer
        
        # Title Zone (Top 1/3)
        title_cy = y + 70
        draw_text(surface, title, rect.centerx, title_cy, self.font_lbl, THEME_TEXT_SUB, "center")
        
        # Value Zone (Middle)
        # Draw a faint box behind the value to anchor it visually? (Optional, kept clean for now)
        val_cy = y + (h // 2) + 10
        draw_text(surface, value, rect.centerx, val_cy, self.font_val, THEME_TEXT_MAIN, "center")
        
        # Footer Zone (Bottom)
        foot_cy = y + h - 50
        
        # Draw a pill background for the footer text
        txt_surf = self.font_btn.render(subtext, True, accent_color)
        pill_rect = txt_surf.get_rect(center=(rect.centerx, foot_cy))
        pill_rect.inflate_ip(20, 10) # Add padding
        pygame.draw.rect(surface, (20, 20, 25), pill_rect, border_radius=10) # Dark pill bg
        
        draw_text(surface, subtext, rect.centerx, foot_cy, self.font_btn, accent_color, "center")