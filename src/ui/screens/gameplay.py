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

from src.models.auction import Auction
from src.models.player import Player

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
        self.auction = Auction()
        self.player = Player("You", budget=500)
        self.auction.add_player(self.player)
        self.auction.start_round(1)
        
        self.round_num = 1
        self.max_rounds = 5
        self.feedback_msg = ""
        self.timer = 60 # Slower round for visibility

        # Pre-set the user's proposed bid (Highest + Increment)
        self.proposed_bid = self.auction.highest_bid + 10
        self.feedback_msg = ""
        
        # --- UI Components ---
        
        # 1. Navigation
        self.btn_quit = NeonButton(20, 20, 100, 40, "QUIT", THEME_BORDER, "back")
        
        # 2. Right Panel Controls
        cx_panel3 = (self.pad * 3) + self.col1_w + self.col2_w + (self.col3_w // 2)
        btn_w = self.col3_w - 40
        
        # A. Input Box
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
            # self.player.withdraw() # TODO: Implement withdraw in Player
            self.feedback_msg = "Withdrawn (Not Impl)"

        # 4. Handle Round Over -> Next Round OR Game Over
        if not self.auction.is_active:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                # If Game Over (Round 5 finished), Reset Everything
                if self.round_num >= self.max_rounds:
                    # Reset Game State completely
                    self.round_num = 1
                    # Re-init Auction to wipe agents and create fresh ones
                    self.auction = Auction()
                    self.player = Player("You", budget=500)
                    self.auction.add_player(self.player)
                    self.auction.start_round(1)
                    # Reset UI
                    self.feed = []
                    self.proposed_bid = self.auction.highest_bid + 10
                    self.input_box.set_text(self.proposed_bid)
                    self.feedback_msg = ""
                    
                else:
                    # Normal Next Round
                    self.round_num += 1
                    self.auction.start_round(self.round_num)
                    # Reset UI elements for new round
                    self.feed = [] 
                    self.proposed_bid = self.auction.highest_bid + 10
                    self.input_box.set_text(self.proposed_bid)
                    self.feedback_msg = ""

        return None

    def _adjust_bid(self, amount):
        self.proposed_bid += amount
        if self.proposed_bid < 0: self.proposed_bid = 0
        self.input_box.set_text(self.proposed_bid)

    def _attempt_bid(self):
        val = self.proposed_bid
        
        # Use Player Class for logic
        if self.player.place_bid(self.auction, val):
            self.feedback_msg = ""
            # Prepare next increment automatically
            self.proposed_bid = val + 10 # Min increment placeholder
            self.input_box.set_text(self.proposed_bid)
        else:
            # Feedback handled via return check? 
            # Ideally Player.place_bid could return a reason, but for now we infer
            if val > self.player.budget:
                self.feedback_msg = "Insufficient Funds!"
            elif val <= self.auction.highest_bid:
                self.feedback_msg = "Bid too low!"
            else:
                self.feedback_msg = "Bid Rejected (Unknown)"

    def update(self):
        # --- Simulation Tick ---
        # For now, run 1 tick per frame (very fast) or throttle?
        # Let's throttle to 5 ticks per second (12 frames per tick @ 60FPS)
        if pygame.time.get_ticks() % 200 < 20: # Crude throttle
            self.auction.run_tick()
            
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
        # --- CENTERED ROUND INFO ---
        info_text = f"ROUND {self.round_num} / {self.max_rounds}"
        # We use SCREEN_WIDTH // 2 for the X coordinate
        draw_text(surface, info_text, SCREEN_WIDTH // 2, 40, self.font_md, THEME_TEXT_MAIN, "center")
        
        # --- TOP RIGHT TIMER ---
        seconds_left = max(0, int(self.auction.ticks_remaining / 5)) # Estimating 5 ticks/sec
        color = THEME_ACCENT_GREEN if seconds_left > 10 else THEME_ACCENT_RED
        draw_text(surface, f"00:{seconds_left:02d}", SCREEN_WIDTH - 60, 40, self.font_md, color, "center")

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
        draw_text(surface, "[ ? ]", cx, img_rect.centery, self.font_xl, THEME_TEXT_SUB, "center")
        
        # Dynamic Text Details
        # Show "Unknown Item" or generic name
        draw_text(surface, "Mystery Artifact", cx, img_rect.bottom + 30, self.font_lg, THEME_TEXT_MAIN, "center")
        
        # Show the HINT
        hint = self.auction.current_item.get_hint()
        draw_text(surface, f"\"{hint}\"", cx, img_rect.bottom + 70, self.font_md, THEME_ACCENT_GOLD, "center")
        
        # Tags? Maybe strategy hints later
        draw_text(surface, "Value Hidden", cx, img_rect.bottom + 110, self.font_sm, THEME_TEXT_SUB, "center")

    def _draw_center_content(self, surface, x, y, w):
        cx = x + w // 2
        
        # Opponents Section
        draw_text(surface, "OPPONENTS", cx, y + 30, self.font_md, THEME_ACCENT_CYAN, "center")
        
        row_y = y + 70
        for agent in self.auction.agents:
            # Determine color based on Agent State (mock logic for now - active vs folded)
            # We don't have "folded" state explicitly exposed yet, but let's assume active
            status = "Ready"
            color = THEME_ACCENT_GREEN
            
            if agent.budget < self.auction.highest_bid:
                status = "Outpriced"
                color = THEME_ACCENT_RED
            
            # Bot Card
            bot_rect = pygame.Rect(x + 40, row_y, w - 80, 50)
            pygame.draw.rect(surface, (25, 27, 40), bot_rect, border_radius=8)
            
            draw_text(surface, agent.id, bot_rect.left + 20, bot_rect.centery, self.font_sm, THEME_TEXT_MAIN, "left")
            draw_text(surface, status, bot_rect.right - 20, bot_rect.centery, self.font_sm, color, "right")
            row_y += 60
            
        # Divider
        pygame.draw.line(surface, THEME_BORDER, (x+40, row_y + 20), (x+w-40, row_y + 20), 1)
        
        # Activity Feed
        draw_text(surface, "ACTIVITY LOG", x + 40, row_y + 40, self.font_sm, THEME_TEXT_SUB, "left")
        
        log_y = row_y + 75
        # Show last 6 entries from AUCTION logs
        logs = self.auction.get_recent_logs()
        for log in logs:
            draw_text(surface, f"> {log}", x + 40, log_y, self.font_sm, (200, 200, 200), "left")
            log_y += 25

    def _draw_right_content(self, surface, x, y, w):
        cx = x + w // 2
        
        # 1. Budget
        draw_text(surface, "BUDGET", cx, y + 30, self.font_sm, THEME_TEXT_SUB, "center")
        draw_text(surface, f"$ {self.player.budget}", cx, y + 55, self.font_lg, THEME_ACCENT_GOLD, "center")
        
        pygame.draw.line(surface, THEME_BORDER, (x+30, y+95), (x+w-30, y+95), 1)
        
        # 2. Highest Bid
        mid_zone_y = y + 155 
        draw_text(surface, "HIGHEST BID", cx, mid_zone_y - 25, self.font_sm, THEME_TEXT_SUB, "center")
        draw_text(surface, f"$ {self.auction.highest_bid}", cx, mid_zone_y + 10, self.font_xl, THEME_TEXT_MAIN, "center")
        
        pygame.draw.line(surface, THEME_BORDER, (x+30, y+215), (x+w-30, y+215), 1)
        
        # 3. User Input Section
        min_req = self.auction.highest_bid + 10
        draw_text(surface, f"Min Req: ${min_req}", cx, y + 215, self.font_sm, (100, 100, 100), "center")
        draw_text(surface, "YOUR OFFER", cx, y + 240, self.font_sm, THEME_ACCENT_CYAN, "center")
        
        self.input_box.draw(surface)
        self.btn_minus.draw(surface, self.font_md)
        self.btn_plus.draw(surface, self.font_md)
        self.btn_place_bid.draw(surface, self.font_md)
        self.btn_withdraw.draw(surface, self.font_md)
        
        if self.feedback_msg:
            draw_text(surface, self.feedback_msg, cx, y + 530, self.font_sm, THEME_ACCENT_RED, "center")

        # --- Round End Overlay ---
        if not self.auction.is_active:
            s = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            s.set_alpha(180)
            s.fill((0,0,0))
            surface.blit(s, (0,0))
            
            # Summary Box
            cx, cy = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2
            
            # Winner Info
            winner_id = self.auction.highest_bidder.id if self.auction.highest_bidder else "Nobody"
            profit = 0
            if self.auction.highest_bidder:
                 profit = self.auction.current_item.get_true_value() - self.auction.highest_bid
            
            draw_text(surface, "ROUND OVER", cx, cy - 80, self.font_xl, THEME_ACCENT_GOLD, "center")
            draw_text(surface, f"Winner: {winner_id}", cx, cy - 10, self.font_lg, THEME_TEXT_MAIN, "center")
            draw_text(surface, f"Winning Bid: ${self.auction.highest_bid}", cx, cy + 30, self.font_md, THEME_TEXT_SUB, "center")
            
            p_color = THEME_ACCENT_GREEN if profit >= 0 else THEME_ACCENT_RED
            draw_text(surface, f"Item Value: ${self.auction.current_item.get_true_value()}", cx, cy + 70, self.font_md, THEME_TEXT_MAIN, "center")
            draw_text(surface, f"Profit: ${profit}", cx, cy + 100, self.font_lg, p_color, "center")
            
            # Change text based on Game Over or Next Round
            if self.round_num >= self.max_rounds:
                # GAME OVER SCREEN
                # Show standings briefly or just "GAME OVER"
                # For simplicity, let's overlay "GAME OVER - FINAL STANDINGS"
                draw_text(surface, "--- GAME OVER ---", cx, cy + 140, self.font_xl, THEME_ACCENT_RED, "center")
                
                standings = self.auction.get_standings()
                y_off = cy + 180
                for rank, (name, budget) in enumerate(standings[:3]): # Top 3
                    txt = f"#{rank+1} {name}: ${budget}"
                    draw_text(surface, txt, cx, y_off, self.font_md, THEME_ACCENT_GOLD if rank==0 else THEME_TEXT_MAIN, "center")
                    y_off += 30
                    
                draw_text(surface, "Press Space to Restart", cx, y_off + 20, self.font_sm, THEME_ACCENT_CYAN, "center")
            else:
                draw_text(surface, "Press Space to Continue...", cx, cy + 180, self.font_sm, THEME_ACCENT_CYAN, "center")