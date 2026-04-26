import pygame
from src.constants import *
from src.ui.components import NeonButton, draw_text

# --- Theme Colors ---
THEME_BG = (20, 22, 35)
THEME_PANEL_BG = (32, 34, 50)
THEME_BORDER = (60, 65, 85)
THEME_ACCENT_CYAN = (0, 255, 255)
THEME_TEXT_MAIN = (236, 240, 241)
THEME_TEXT_SUB = (149, 165, 166)

class SimSetupScreen:
    def __init__(self):
        self.font_lg = pygame.font.SysFont(FONT_NAME, 40, bold=True)
        self.font_md = pygame.font.SysFont(FONT_NAME, 24)
        self.font_sm = pygame.font.SysFont(FONT_NAME, 18)
        
        self.bot_count = 4
        self.strategies = ["Balanced", "Aggressive", "Conservative", "Balanced", "Balanced", "Balanced"]
        
        self._init_ui()

    def _init_ui(self):
        cx = SCREEN_WIDTH // 2
        
        # Bot count controls
        self.btn_minus = NeonButton(cx - 150, 180, 50, 50, "-", THEME_BORDER, "dec_bots")
        self.btn_plus = NeonButton(cx + 100, 180, 50, 50, "+", THEME_BORDER, "inc_bots")
        
        # Strategy selection buttons
        self.strat_btns = []
        for i in range(6):
            y_pos = 280 + (i * 50) # Reduced from 320/55 gap
            self.strat_btns.append(NeonButton(cx + 20, y_pos, 160, 40, self.strategies[i], THEME_ACCENT_CYAN, f"strat_{i}"))
            
        # Navigation
        self.btn_start = NeonButton(cx - 140, 640, 280, 55, "LAUNCH EXPERIMENT", COLOR_CYAN, "launch_sim")
        self.btn_back = NeonButton(20, 20, 100, 40, "BACK", THEME_BORDER, "back")

    def handle_events(self, event):
        if self.btn_back.is_clicked(event):
            return "back"
            
        if self.btn_start.is_clicked(event):
            return "launch_sim"
            
        if self.btn_minus.is_clicked(event):
            self.bot_count = max(2, self.bot_count - 1)
            
        if self.btn_plus.is_clicked(event):
            self.bot_count = min(6, self.bot_count + 1)
            
        for i in range(self.bot_count):
            if self.strat_btns[i].is_clicked(event):
                strats = ["Balanced", "Aggressive", "Conservative"]
                idx = (strats.index(self.strategies[i]) + 1) % len(strats)
                self.strategies[i] = strats[idx]
                self.strat_btns[i].text = strats[idx]
                
        return None

    def update(self):
        mouse_pos = pygame.mouse.get_pos()
        self.btn_minus.update(mouse_pos)
        self.btn_plus.update(mouse_pos)
        self.btn_start.update(mouse_pos)
        self.btn_back.update(mouse_pos)
        for i in range(self.bot_count):
            self.strat_btns[i].update(mouse_pos)

    def draw(self, surface):
        surface.fill(THEME_BG)
        self._draw_grid_bg(surface)
        
        cx = SCREEN_WIDTH // 2
        draw_text(surface, "SIMULATION LABORATORY", cx, 60, self.font_lg, THEME_ACCENT_CYAN, "center")
        
        # Main Config Panel
        panel_w, panel_h = 500, 490 # Reduced from 520 to clear the button
        panel_rect = pygame.Rect(cx - panel_w//2, 130, panel_w, panel_h)
        pygame.draw.rect(surface, THEME_PANEL_BG, panel_rect, border_radius=15)
        pygame.draw.rect(surface, THEME_BORDER, panel_rect, 1, border_radius=15)
        
        # Bot Count Section
        draw_text(surface, "Number of AI Bidders", cx, 160, self.font_sm, THEME_TEXT_SUB, "center")
        self.btn_minus.rect.y = 195
        self.btn_plus.rect.y = 195
        self.btn_minus.draw(surface, self.font_md)
        draw_text(surface, str(self.bot_count), cx, 220, self.font_lg, THEME_TEXT_MAIN, "center")
        self.btn_plus.draw(surface, self.font_md)
        
        pygame.draw.line(surface, THEME_BORDER, (cx - 200, 270), (cx + 200, 270), 1)
        
        # Individual Bot Config
        draw_text(surface, "Assign Personalities", cx, 290, self.font_sm, THEME_TEXT_SUB, "center")
        for i in range(self.bot_count):
            y_pos = 320 + (i * 50)
            self.strat_btns[i].rect.y = y_pos
            # Perfect center-align: Button is 40px tall, so text center at y_pos + 20
            draw_text(surface, f"BIDDER {i+1}", cx - 40, y_pos + 20, self.font_md, THEME_TEXT_MAIN, "midright")
            self.strat_btns[i].draw(surface, self.font_sm)
            
        self.btn_start.draw(surface, self.font_md)
        self.btn_back.draw(surface, self.font_md)

    def _draw_grid_bg(self, surface):
        color = (25, 28, 40)
        for x in range(0, SCREEN_WIDTH, 80):
            pygame.draw.line(surface, color, (x, 0), (x, SCREEN_HEIGHT), 1)
        for y in range(0, SCREEN_HEIGHT, 80):
            pygame.draw.line(surface, color, (0, y), (SCREEN_WIDTH, y), 1)
