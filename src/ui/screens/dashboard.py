import pygame
from src.constants import *
from src.ui.components import NeonButton, draw_text

# --- Theme Colors ---
THEME_BG = (20, 22, 35)
THEME_TEXT_MAIN = (236, 240, 241)
THEME_ACCENT_CYAN = (0, 255, 255)

class MenuScreen:
    def __init__(self):
        self.font_logo = pygame.font.SysFont(FONT_NAME, 80, bold=True)
        self.font_btn = pygame.font.SysFont(FONT_NAME, 22)
        
        # Center coordinates
        cx = SCREEN_WIDTH // 2
        cy = SCREEN_HEIGHT // 2
        
        # Button Dimensions
        btn_w, btn_h = 280, 55
        gap = 20
        start_y = cy + 40 
        
        self.buttons = [
            NeonButton(cx - btn_w//2, start_y, btn_w, btn_h, "START GAME", COLOR_CYAN, "start_game"),
            # RENAMED BUTTON BELOW
            NeonButton(cx - btn_w//2, start_y + (btn_h + gap), btn_w, btn_h, "HIGH SCORES", COLOR_YELLOW, "view_scores"),
            NeonButton(cx - btn_w//2, start_y + (btn_h + gap)*2, btn_w, btn_h, "OVERALL STATS", COLOR_PURPLE, "view_stats"),
            NeonButton(cx - btn_w//2, start_y + (btn_h + gap)*3, btn_w, btn_h, "EXIT SYSTEM", COLOR_RED, "exit"),
        ]

    def handle_events(self, event):
        for btn in self.buttons:
            if btn.is_clicked(event):
                return btn.action_code
        return None

    def update(self):
        mouse_pos = pygame.mouse.get_pos()
        for btn in self.buttons:
            btn.update(mouse_pos)

    def draw(self, surface):
        surface.fill(THEME_BG)
        self._draw_grid_bg(surface)
        
        # --- Logo Section ---
        cx = SCREEN_WIDTH // 2
        cy = 180 
        
        # Main Text
        text_surf = self.font_logo.render("AUCTION LAB", True, THEME_TEXT_MAIN)
        text_rect = text_surf.get_rect(center=(cx, cy))
        surface.blit(text_surf, text_rect)
        
        # Underline decoration
        line_w = text_rect.width + 60
        pygame.draw.rect(surface, THEME_ACCENT_CYAN, (cx - line_w//2, text_rect.bottom + 10, line_w, 4), border_radius=2)
        
        # --- Buttons ---
        for btn in self.buttons:
            btn.draw(surface, self.font_btn)

    def _draw_grid_bg(self, surface):
        color = (25, 28, 40)
        for x in range(0, SCREEN_WIDTH, 60):
            pygame.draw.line(surface, color, (x, 0), (x, SCREEN_HEIGHT), 1)
        for y in range(0, SCREEN_HEIGHT, 60):
            pygame.draw.line(surface, color, (0, y), (SCREEN_WIDTH, y), 1)