import pygame
from src.constants import *
from src.ui.components import NeonButton, NeonInputBox, draw_text

# --- Theme Colors ---
THEME_BG = (20, 22, 35)
THEME_PANEL_BG = (32, 34, 50)
THEME_BORDER = (60, 65, 85)
THEME_ACCENT_GREEN = (46, 204, 113)
THEME_ACCENT_RED = (231, 76, 60)
THEME_ACCENT_CYAN = (0, 255, 255)
THEME_ACCENT_GOLD = (255, 215, 0)
THEME_TEXT_MAIN = (236, 240, 241)
THEME_TEXT_SUB = (149, 165, 166)

class GameScreen:
    def __init__(self):
        # Fonts
        self.font_xl = pygame.font.SysFont(FONT_NAME, 60, bold=True)
        self.font_lg = pygame.font.SysFont(FONT_NAME, 32, bold=True)
        self.font_md = pygame.font.SysFont(FONT_NAME, 24)
        self.font_sm = pygame.font.SysFont(FONT_NAME, 18)
        
        # --- Layout Constants ---
        self.pad = 20
        # 3 Columns: 25% | 50% | 25%
        self.col1_w = int((SCREEN_WIDTH - (self.pad * 4)) * 0.25)
        self.col2_w = int((SCREEN_WIDTH - (self.pad * 4)) * 0.50)
        self.col3_w = int((SCREEN_WIDTH - (self.pad * 4)) * 0.25)
        
        self.panel_h = SCREEN_HEIGHT - 120 
        self.start_y = 100
        
        # --- Game Logic / State ---
        self.player_budget = 5000
        self.current_highest_bid = 500
        self.min_increment = 50
        
        # Pre-set the user's proposed bid (Highest + Increment)
        self.proposed_bid = self.current_highest_bid + self.min_increment
        
        # Mock Item Data
        self.item_name = "Ancient Vase"
        self.item_category = "Antique"
        self.item_tags = ["Rare", "Fragile", "Historical"]
        
        # Mock Feed & Bots
        self.feed = [
            "Round 1 Started.",
            "Conservative AI joined.",
            "Aggressive AI bids $400.",
            "Current bid is $500."
        ]
        
        self.bots = [
            ("Aggressive AI", "Bidding...", THEME_ACCENT_RED), 
            ("Conservative AI", "Watching", THEME_ACCENT_GREEN),
            ("Random AI", "Withdrew", THEME_TEXT_SUB)
        ]
        
        self.timer = 15
        self.round_num = 1
        self.max_rounds = 5
        self.feedback_msg = ""
        
        # --- UI Components ---
        
        # 1. Navigation
        self.btn_quit = NeonButton(20, 20, 100, 40, "QUIT", THEME_BORDER, "back")
        
        # 2. Right Panel Controls
        # Calculate center of right panel
        cx_panel3 = (self.pad * 3) + self.col1_w + self.col2_w + (self.col3_w // 2)
        btn_w = self.col3_w - 40
        
        # A. Input Box
        # Moved down slightly to give "Highest Bid" more breathing room
        self.input_box = NeonInputBox(cx_panel3 - btn_w//2, self.start_y + 280, btn_w, 50, 
                                      self.proposed_bid, self.font_lg, THEME_ACCENT_CYAN, THEME_BORDER)
        
        # B. +/- Buttons
        small_btn_w = (btn_w // 2) - 10
        self.btn_minus = NeonButton(cx_panel3 - btn_w//2, self.start_y + 340, small_btn_w, 40, "- $50", THEME_BORDER, "decrease")
        self.btn_plus = NeonButton(cx_panel3 + 10, self.start_y + 340, small_btn_w, 40, "+ $50", THEME_BORDER, "increase")
        
        # C. Action Buttons
        self.btn_place_bid = NeonButton(cx_panel3 - btn_w//2, self.start_y + 400, btn_w, 55, "CONFIRM BID", THEME_ACCENT_GREEN, "bid")
        self.btn_withdraw = NeonButton(cx_panel3 - btn_w//2, self.start_y + 470, btn_w, 40, "WITHDRAW", THEME_ACCENT_RED, "withdraw")

    def handle_events(self, event):
        if self.btn_quit.is_clicked(event):
            return "back"
        
        # 1. Handle Input Box Typing
        res = self.input_box.handle_event(event)
        if res == "submit": 
            self._attempt_bid()

        # 2. Update proposed bid variable if user typed manually
        try:
            self.proposed_bid = self.input_box.get_value()
        except ValueError:
            self.proposed_bid = 0

        # 3. Handle Control Buttons
        if self.btn_minus.is_clicked(event):
            self._adjust_bid(-50)
        
        if self.btn_plus.is_clicked(event):
            self._adjust_bid(50)
            
        if self.btn_place_bid.is_clicked(event):
            self._attempt_bid()
            
        if self.btn_withdraw.is_clicked(event):
            self.feed.append("You withdrew from the auction.")
            self.feedback_msg = "Withdrawn"

        return None

    def _adjust_bid(self, amount):
        self.proposed_bid += amount
        if self.proposed_bid < 0: self.proposed_bid = 0
        self.input_box.set_text(self.proposed_bid)

    def _attempt_bid(self):
        val = self.proposed_bid
        
        # Validation Logic
        if val > self.player_budget:
            self.feedback_msg = "Insufficient Funds!"
        elif val <= self.current_highest_bid:
            self.feedback_msg = "Bid too low!"
        else:
            # Success
            self.current_highest_bid = val
            self.feed.append(f"You bid ${val}")
            self.feedback_msg = ""
            # Prepare next increment automatically
            self.proposed_bid = val + self.min_increment
            self.input_box.set_text(self.proposed_bid)

    def update(self):
        mouse_pos = pygame.mouse.get_pos()
        self.btn_quit.update(mouse_pos)
        self.btn_minus.update(mouse_pos)
        self.btn_plus.update(mouse_pos)
        self.btn_place_bid.update(mouse_pos)
        self.btn_withdraw.update(mouse_pos)

    def draw(self, surface):
        surface.fill(THEME_BG)
        
        # Header
        self.btn_quit.draw(surface, self.font_sm)
        self._draw_top_bar(surface)
        
        # --- Layout Panels ---
        x_cursor = self.pad
        
        # 1. Left Panel (Item Info)
        self._draw_panel(surface, x_cursor, self.start_y, self.col1_w, self.panel_h)
        self._draw_left_content(surface, x_cursor, self.start_y, self.col1_w)
        
        x_cursor += self.col1_w + self.pad
        
        # 2. Center Panel (Auction Floor)
        self._draw_panel(surface, x_cursor, self.start_y, self.col2_w, self.panel_h)
        self._draw_center_content(surface, x_cursor, self.start_y, self.col2_w)
        
        x_cursor += self.col2_w + self.pad
        
        # 3. Right Panel (Controls)
        self._draw_panel(surface, x_cursor, self.start_y, self.col3_w, self.panel_h)
        self._draw_right_content(surface, x_cursor, self.start_y, self.col3_w)

    def _draw_top_bar(self, surface):
        info_text = f"ROUND {self.round_num} / {self.max_rounds}"
        draw_text(surface, info_text, SCREEN_WIDTH - 150, 40, self.font_md, THEME_TEXT_MAIN, "center")
        
        color = THEME_ACCENT_GREEN if self.timer > 5 else THEME_ACCENT_RED
        draw_text(surface, f"00:{self.timer}", SCREEN_WIDTH - 60, 40, self.font_md, color, "center")

    def _draw_panel(self, surface, x, y, w, h):
        rect = pygame.Rect(x, y, w, h)
        pygame.draw.rect(surface, THEME_PANEL_BG, rect, border_radius=12)
        pygame.draw.rect(surface, THEME_BORDER, rect, 1, border_radius=12)

    # --- Content Drawers ---

    def _draw_left_content(self, surface, x, y, w):
        cx = x + w // 2
        
        draw_text(surface, "ITEM INFO", cx, y + 30, self.font_md, THEME_ACCENT_CYAN, "center")
        
        # Image Placeholder
        img_rect = pygame.Rect(x + 30, y + 70, w - 60, w - 60)
        pygame.draw.rect(surface, (15, 17, 25), img_rect, border_radius=8)
        pygame.draw.rect(surface, THEME_BORDER, img_rect, 1, border_radius=8)
        draw_text(surface, "[ IMAGE ]", cx, img_rect.centery, self.font_sm, THEME_TEXT_SUB, "center")
        
        # Text Details
        draw_text(surface, self.item_name, cx, img_rect.bottom + 30, self.font_lg, THEME_TEXT_MAIN, "center")
        draw_text(surface, self.item_category, cx, img_rect.bottom + 60, self.font_md, THEME_ACCENT_GOLD, "center")
        
        # Tags
        tag_start_y = img_rect.bottom + 100
        for i, tag in enumerate(self.item_tags):
            draw_text(surface, f"• {tag}", x + 40, tag_start_y + (i*30), self.font_sm, THEME_TEXT_SUB, "left")

    def _draw_center_content(self, surface, x, y, w):
        cx = x + w // 2
        
        # Opponents Section
        draw_text(surface, "OPPONENTS", cx, y + 30, self.font_md, THEME_ACCENT_CYAN, "center")
        
        row_y = y + 70
        for name, status, color in self.bots:
            # Bot Card
            bot_rect = pygame.Rect(x + 40, row_y, w - 80, 50)
            pygame.draw.rect(surface, (25, 27, 40), bot_rect, border_radius=8)
            
            draw_text(surface, name, bot_rect.left + 20, bot_rect.centery, self.font_sm, THEME_TEXT_MAIN, "left")
            draw_text(surface, status, bot_rect.right - 20, bot_rect.centery, self.font_sm, color, "right")
            row_y += 60
            
        # Divider
        pygame.draw.line(surface, THEME_BORDER, (x+40, row_y + 20), (x+w-40, row_y + 20), 1)
        
        # Activity Feed
        draw_text(surface, "ACTIVITY LOG", x + 40, row_y + 40, self.font_sm, THEME_TEXT_SUB, "left")
        
        log_y = row_y + 75
        # Show last 6 entries
        for log in self.feed[-6:]:
            draw_text(surface, f"> {log}", x + 40, log_y, self.font_sm, (200, 200, 200), "left")
            log_y += 25

    def _draw_right_content(self, surface, x, y, w):
        cx = x + w // 2
        
        # 1. Budget
        # Top section of the panel
        draw_text(surface, "BUDGET", cx, y + 30, self.font_sm, THEME_TEXT_SUB, "center")
        draw_text(surface, f"$ {self.player_budget}", cx, y + 55, self.font_lg, THEME_ACCENT_GOLD, "center")
        
        # Divider 1
        pygame.draw.line(surface, THEME_BORDER, (x+30, y+95), (x+w-30, y+95), 1)
        
        # 2. Highest Bid (Centered vertically in its zone)
        # Zone is roughly y=95 to y=215 (height 120px)
        mid_zone_y = y + 155 
        
        draw_text(surface, "HIGHEST BID", cx, mid_zone_y - 25, self.font_sm, THEME_TEXT_SUB, "center")
        draw_text(surface, f"$ {self.current_highest_bid}", cx, mid_zone_y + 10, self.font_xl, THEME_TEXT_MAIN, "center")
        
        # Divider 2
        pygame.draw.line(surface, THEME_BORDER, (x+30, y+215), (x+w-30, y+215), 1)
        
        # 3. User Input Section
        draw_text(surface, "YOUR OFFER", cx, y + 240, self.font_sm, THEME_ACCENT_CYAN, "center")
        
        # Draw Input Components (Coordinates managed in __init__)
        self.input_box.draw(surface)
        self.btn_minus.draw(surface, self.font_md)
        self.btn_plus.draw(surface, self.font_md)
        self.btn_place_bid.draw(surface, self.font_md)
        self.btn_withdraw.draw(surface, self.font_md)
        
        # 4. Feedback Message
        if self.feedback_msg:
            draw_text(surface, self.feedback_msg, cx, y + 530, self.font_sm, THEME_ACCENT_RED, "center")