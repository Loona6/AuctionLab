import pygame
from src.constants import *
from src.ui.components import NeonButton, draw_text
from src.logic.data_manager import DataManager
from src.config import PLAYSTYLE_DESCRIPTIONS

# --- Theme Colors ---
THEME_BG = (20, 22, 35)
THEME_PANEL_BG = (32, 34, 50)
THEME_BORDER = (60, 65, 85)
THEME_ACCENT_PURPLE = (155, 89, 182)
THEME_ACCENT_CYAN = (0, 255, 255)
THEME_ACCENT_RED = (231, 76, 60)
THEME_ACCENT_GOLD = (255, 215, 0)
THEME_TEXT_MAIN = (236, 240, 241)
THEME_TEXT_SUB = (149, 165, 166)

class StatsScreen:
    def __init__(self):
        self.font_header = pygame.font.SysFont(FONT_NAME, 40, bold=True)
        self.font_sub = pygame.font.SysFont(FONT_NAME, 22, bold=True)
        self.font_val = pygame.font.SysFont(FONT_NAME, 32, bold=True)
        self.font_txt = pygame.font.SysFont(FONT_NAME, 18)
        
        self.btn_back = NeonButton(40, 30, 100, 40, "BACK", THEME_BORDER, "back")
        self.hover_areas = [] # List of (Rect, style_name)
        self.active_tooltip = None

    def handle_events(self, event):
        if self.btn_back.is_clicked(event):
            return "back"
        return None

    def update(self):
        mouse_pos = pygame.mouse.get_pos()
        self.btn_back.update(mouse_pos)
        
        self.active_tooltip = None
        for rect, style_name in self.hover_areas:
            if rect.collidepoint(mouse_pos):
                self.active_tooltip = style_name
                break

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
        
        row_h = 35
        curr_y = mid_y + 60
        self._draw_row(surface, 60, curr_y, left_w, "Total Game Wins:", str(stats.get('total_wins', 0)))
        curr_y += row_h
        self._draw_row(surface, 60, curr_y, left_w, "Personal Best Profit:", f"$ {stats.get('max_profit', 0):,}")
        curr_y += row_h
        self._draw_row(surface, 60, curr_y, left_w, "Personal Best Collection:", f"{stats.get('max_items', 0)} Items")
        curr_y += row_h
        
        # Win ratio calculation (Items won vs total rounds played)
        total_rounds = stats.get('total_sessions', 0) * 5
        win_ratio = (stats.get('total_items', 0) / total_rounds) * 100 if total_rounds > 0 else 0
        self._draw_row(surface, 60, curr_y, left_w, "Overall Round Win Ratio:", f"{win_ratio:.1f}%")
        curr_y += row_h
        
        self._draw_row(surface, 60, curr_y, left_w, "Avg. Profit / Session:", f"$ {int(avg_profit):,}")
        curr_y += row_h
        self._draw_row(surface, 60, curr_y, left_w, "Total Playstyles Tracked:", str(len(stats.get("playstyle_counts", {}))))
        
        # Right Panel: Playstyle Frequency
        right_x = (SCREEN_WIDTH // 2) + 10
        self._draw_panel(surface, right_x, mid_y, left_w, 450, "Playstyle Success Rate")
        
        h_y = mid_y + 60
        draw_text(surface, "STYLE", right_x + 20, h_y, self.font_txt, THEME_TEXT_SUB, "left")
        draw_text(surface, "SESS", right_x + 160, h_y, self.font_txt, THEME_TEXT_SUB, "left")
        draw_text(surface, "AVG PROF", right_x + 250, h_y, self.font_txt, THEME_TEXT_SUB, "left")
        draw_text(surface, "ROI", right_x + 380, h_y, self.font_txt, THEME_TEXT_SUB, "left")
        draw_text(surface, "SUCCESS %", right_x + 480, h_y, self.font_txt, THEME_TEXT_SUB, "left")
        pygame.draw.line(surface, THEME_BORDER, (right_x+20, h_y+25), (right_x+left_w-20, h_y+25), 1)
        
        # Table Rows for playstyles
        counts = stats.get("playstyle_counts", {})
        profits_map = stats.get("playstyle_profits", {})
        success_map = stats.get("playstyle_successes", {})
        spent_map = stats.get("playstyle_spent", {})
        
        # Sort by Success % then Avg Profit
        sorted_styles = sorted(counts.items(), 
                               key=lambda x: (success_map.get(x[0], 0) / max(1, x[1])), 
                               reverse=True)
        
        row_y = h_y + 35
        self.hover_areas = []
        for style, count in sorted_styles: # Show all recorded styles
            total_profit = profits_map.get(style, 0)
            total_spent = spent_map.get(style, 0)
            avg_profit = total_profit / count if count > 0 else 0
            
            successes = success_map.get(style, 0)
            success_rate = (successes / count) * 100 if count > 0 else 0
            roi = (total_profit / total_spent) * 100 if total_spent > 0 else 0
            
            # --- Draw Rows (All Left Aligned) ---
            draw_text(surface, style, right_x + 20, row_y, self.font_txt, THEME_TEXT_MAIN, "left")
            draw_text(surface, str(count), right_x + 160, row_y, self.font_txt, THEME_TEXT_MAIN, "left")
            
            # Avg Profit
            prof_color = THEME_ACCENT_CYAN if avg_profit >= 0 else THEME_ACCENT_RED
            prof_text = f"${int(avg_profit)}" if style in profits_map else "N/A"
            draw_text(surface, prof_text, right_x + 250, row_y, self.font_txt, prof_color, "left")
            
            # ROI
            roi_color = THEME_ACCENT_CYAN if roi >= 0 else THEME_ACCENT_RED
            roi_text = f"{int(roi)}%" if style in spent_map else "N/A"
            draw_text(surface, roi_text, right_x + 380, row_y, self.font_txt, roi_color, "left")

            # Success %
            success_color = THEME_ACCENT_CYAN if success_rate > 50 else (THEME_ACCENT_GOLD if success_rate > 0 else THEME_ACCENT_RED)
            draw_text(surface, f"{success_rate:.0f}%", right_x + 480, row_y, self.font_txt, success_color, "left")
            
            # Record hover area for the style name
            style_rect = pygame.Rect(right_x + 20, row_y - 10, 130, 25)
            self.hover_areas.append((style_rect, style))
            
            row_y += 32 # Tighter spacing to fit more styles
            
        if self.active_tooltip:
            self._draw_tooltip(surface, pygame.mouse.get_pos())

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

    def _draw_tooltip(self, surface, pos):
        if self.active_tooltip not in PLAYSTYLE_DESCRIPTIONS: return
        
        text = PLAYSTYLE_DESCRIPTIONS[self.active_tooltip]
        
        # Calculate Box Size
        tw = 300
        line_h = 20
        # Preliminary wrap to get height
        lines = self._wrap_text(text, self.font_txt, tw - 20)
        total_h = len(lines) * line_h + 20
        
        # Position (Keep on screen)
        tx, ty = pos[0] + 20, pos[1] + 20
        if tx + tw > SCREEN_WIDTH: tx = pos[0] - tw - 10
        if ty + total_h > SCREEN_HEIGHT: ty = pos[1] - total_h - 10
        
        rect = pygame.Rect(tx, ty, tw, total_h)
        pygame.draw.rect(surface, (10, 12, 20), rect, border_radius=10)
        pygame.draw.rect(surface, THEME_ACCENT_PURPLE, rect, 1, border_radius=10)
        
        self._draw_justified_text(surface, text, tx + 10, ty + 10, tw - 20, self.font_txt)

    def _draw_justified_text(self, surface, text, x, y, max_w, font):
        # 1. Parse text into segments with highlight info
        segments = []
        parts = text.split("[H]")
        for i, p in enumerate(parts):
            if "[/H]" in p:
                sub, rest = p.split("[/H]")
                segments.append((sub, True))
                if rest: segments.append((rest, False))
            else:
                if p: segments.append((p, False))
        
        # 2. Break into lines based on max_w
        words_data = []
        for content, is_h in segments:
            for w in content.split():
                words_data.append({'w': w, 'h': is_h})
        
        lines = []
        curr_line = []
        curr_w = 0
        for wd in words_data:
            w_w = font.size(wd['w'] + " ")[0]
            if curr_w + w_w < max_w:
                curr_line.append(wd)
                curr_w += w_w
            else:
                lines.append(curr_line)
                curr_line = [wd]
                curr_w = w_w
        lines.append(curr_line)
        
        # 3. Draw lines
        line_h = 20
        for i, line in enumerate(lines):
            # Always left align
            curr_x = x
            for wd in line:
                color = THEME_ACCENT_GOLD if wd['h'] else THEME_TEXT_MAIN
                surface.blit(font.render(wd['w'], True, color), (curr_x, y + i * line_h))
                curr_x += font.size(wd['w'] + " ")[0]

    def _wrap_text(self, text, font, max_w):
        words = text.split()
        lines = []
        curr = []
        for w in words:
            if font.size(" ".join(curr + [w]))[0] < max_w: curr.append(w)
            else:
                lines.append(" ".join(curr))
                curr = [w]
        lines.append(" ".join(curr))
        return lines