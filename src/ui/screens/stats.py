import pygame
from src.constants import *
from src.ui.components import NeonButton, draw_text
from src.logic.data_manager import DataManager

# --- Theme Colors ---
THEME_BG = (20, 22, 35)
THEME_PANEL_BG = (32, 34, 50)
THEME_BORDER = (60, 65, 85)
THEME_ACCENT_PURPLE = (155, 89, 182)
THEME_ACCENT_CYAN = (0, 255, 255)
THEME_ACCENT_RED = (231, 76, 60)
THEME_TEXT_MAIN = (236, 240, 241)
THEME_TEXT_SUB = (149, 165, 166)

class StatsScreen:
    def __init__(self):
        self.font_header = pygame.font.SysFont(FONT_NAME, 40, bold=True)
        self.font_sub = pygame.font.SysFont(FONT_NAME, 22, bold=True)
        self.font_val = pygame.font.SysFont(FONT_NAME, 32, bold=True)
        self.font_txt = pygame.font.SysFont(FONT_NAME, 18)
        
        self.btn_back = NeonButton(40, 30, 100, 40, "BACK", THEME_BORDER, "back")

    def handle_events(self, event):
        if self.btn_back.is_clicked(event):
            return "back"
        return None

    def update(self):
        self.btn_back.update(pygame.mouse.get_pos())

    def draw(self, surface):
        surface.fill(THEME_BG)
        
        # --- Header ---
        self.btn_back.draw(surface, self.font_txt)
        draw_text(surface, "CUMULATIVE ANALYTICS", SCREEN_WIDTH//2, 50, self.font_header, THEME_ACCENT_PURPLE, "center")
        
        # --- Section 1: Lifetime Totals (Top Row) ---
        stats = DataManager.load_stats()
        
        start_y = 100
        gap = 20
        side_padding = 80 
        
        card_w = (SCREEN_WIDTH - side_padding - (gap * 2)) // 3
        card_h = 100
        
        x1 = 40
        x2 = x1 + card_w + gap
        x3 = x2 + card_w + gap
        
        self._draw_stat_card(surface, x1, start_y, card_w, card_h, "TOTAL SESSIONS", str(stats.get("total_sessions", 0)), THEME_TEXT_MAIN)
        self._draw_stat_card(surface, x2, start_y, card_w, card_h, "LIFETIME PROFIT", f"$ {stats.get('lifetime_profit', 0):,}", THEME_ACCENT_CYAN)
        self._draw_stat_card(surface, x3, start_y, card_w, card_h, "ITEMS ACQUIRED", str(stats.get("total_items", 0)), THEME_ACCENT_PURPLE)
        
        # --- Section 2: Performance Metrics (Middle) ---
        mid_y = start_y + card_h + 30
        
        left_w = (SCREEN_WIDTH // 2) - 50
        self._draw_panel(surface, 40, mid_y, left_w, 300, "Historical Averages")
        
        avg_profit = stats.get('lifetime_profit', 0) / stats.get('total_sessions', 1) if stats.get('total_sessions', 0) > 0 else 0
        avg_items = stats.get('total_items', 0) / stats.get('total_sessions', 1) if stats.get('total_sessions', 0) > 0 else 0
        
        row_h = 40
        curr_y = mid_y + 60
        self._draw_row(surface, 60, curr_y, left_w, "Avg. Profit / Session:", f"$ {int(avg_profit):,}")
        curr_y += row_h
        self._draw_row(surface, 60, curr_y, left_w, "Avg. Items / Session:", f"{avg_items:.1f}")
        curr_y += row_h
        self._draw_row(surface, 60, curr_y, left_w, "Total Playstyles Tracked:", str(len(stats.get("playstyle_counts", {}))))
        
        # Right Panel: Playstyle Frequency
        right_x = (SCREEN_WIDTH // 2) + 10
        self._draw_panel(surface, right_x, mid_y, left_w, 300, "Playstyle Analysis")
        
        h_y = mid_y + 60
        draw_text(surface, "STYLE", right_x + 20, h_y, self.font_txt, THEME_TEXT_SUB)
        draw_text(surface, "FREQUENCY", right_x + 200, h_y, self.font_txt, THEME_TEXT_SUB)
        pygame.draw.line(surface, THEME_BORDER, (right_x+20, h_y+25), (right_x+left_w-20, h_y+25), 1)
        
        # Table Rows for playstyles
        counts = stats.get("playstyle_counts", {})
        row_y = h_y + 35
        for style, count in list(counts.items())[:5]: # Top 5
            draw_text(surface, style, right_x + 20, row_y, self.font_txt, THEME_TEXT_MAIN)
            draw_text(surface, str(count), right_x + 200, row_y, self.font_txt, THEME_TEXT_MAIN)
            row_y += 40

    def _draw_stat_card(self, surface, x, y, w, h, label, value, color):
        rect = pygame.Rect(x, y, w, h)
        pygame.draw.rect(surface, THEME_PANEL_BG, rect, border_radius=10)
        pygame.draw.rect(surface, THEME_BORDER, rect, 1, border_radius=10)
        
        # Use centerx of the rect for alignment so text stays in the middle of the card
        draw_text(surface, label, rect.centerx, y + 25, self.font_txt, THEME_TEXT_SUB, "center")
        draw_text(surface, value, rect.centerx, y + 60, self.font_val, color, "center")

    def _draw_panel(self, surface, x, y, w, h, title):
        rect = pygame.Rect(x, y, w, h)
        pygame.draw.rect(surface, THEME_PANEL_BG, rect, border_radius=10)
        pygame.draw.rect(surface, THEME_BORDER, rect, 1, border_radius=10)
        draw_text(surface, title, x + 20, y + 20, self.font_sub, THEME_TEXT_MAIN)
        pygame.draw.line(surface, THEME_BORDER, (x+20, y+50), (x+w-20, y+50), 1)

    def _draw_row(self, surface, x, y, w, label, value):
        draw_text(surface, label, x, y, self.font_txt, THEME_TEXT_SUB)
        # Align value to the right side of the specific panel area
        draw_text(surface, value, x + w - 40, y, self.font_txt, THEME_TEXT_MAIN, "right")

    def _draw_strat_row(self, surface, x, y, name, usage, success, color):
        draw_text(surface, name, x + 20, y, self.font_txt, color)
        draw_text(surface, usage, x + 160, y, self.font_txt, THEME_TEXT_MAIN)
        draw_text(surface, success, x + 280, y, self.font_txt, THEME_TEXT_MAIN)