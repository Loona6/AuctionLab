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
from src.logic.data_manager import DataManager
from src.logic.analyzer import PlaystyleAnalyzer

class GameScreen:
    def __init__(self):
        # Fonts
        self.font_header = pygame.font.SysFont(FONT_NAME, 50, bold=True)
        self.font_xl = pygame.font.SysFont(FONT_NAME, 60, bold=True)
        self.font_lg = pygame.font.SysFont(FONT_NAME, 32, bold=True)
        self.font_md = pygame.font.SysFont(FONT_NAME, 24)
        self.font_sm = pygame.font.SysFont(FONT_NAME, 18)
        
        # --- State ---
        self.playstyle_result = None
        
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
        self.show_quit_confirm = False
        
        # Pre-set the user's proposed bid (Highest + Increment)
        self.proposed_bid = self.auction.highest_bid + 10
        self.feedback_msg = ""
        
        # --- UI Components ---
        self._init_ui()

    def reset(self):
        """Full reset of the game state for a new session."""
        self.auction = Auction()
        self.player = Player("You", budget=500)
        self.auction.add_player(self.player)
        self.round_num = 1
        self.auction.start_round(self.round_num)
        self.playstyle_result = None
        self.feedback_msg = ""
        self.show_quit_confirm = False
        self.proposed_bid = self.auction.highest_bid + 10
        self.input_box.set_text(self.proposed_bid)
        
        # Reset Session Counters (Though fresh player handles it, being explicit)
        self.player.withdrawal_count = 0
        self.player.pass_count = 0

    def _init_ui(self):
        # 1. Navigation
        self.btn_quit = NeonButton(20, 20, 100, 40, "QUIT", THEME_BORDER, "quit_attempt")
        
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
        self.btn_pass = NeonButton(cx_panel3 - btn_w//2, self.start_y + 470, btn_w, 40, "PASS ROUND", THEME_TEXT_SUB, "pass")
        self.btn_withdraw = NeonButton(cx_panel3 - btn_w//2, self.start_y + 520, btn_w, 40, "WITHDRAW", THEME_ACCENT_RED, "withdraw")

        # Confirmation Dialog Buttons
        self.btn_confirm_quit = NeonButton(SCREEN_WIDTH//2 - 110, SCREEN_HEIGHT//2 + 20, 100, 40, "YES", THEME_ACCENT_RED, "confirm_exit")
        self.btn_cancel_quit = NeonButton(SCREEN_WIDTH//2 + 10, SCREEN_HEIGHT//2 + 20, 100, 40, "NO", THEME_BORDER, "cancel_exit")

    def handle_events(self, event):
        # --- Quit Confirmation Handling ---
        if self.show_quit_confirm:
            if self.btn_confirm_quit.is_clicked(event):
                return "back"
            if self.btn_cancel_quit.is_clicked(event):
                self.show_quit_confirm = False
            return None

        # --- Menu Navigation ---
        if self.btn_quit.is_clicked(event):
            self.show_quit_confirm = True
            return None
        
        # --- Game Logic: Only handle if round is active ---
        if self.auction.is_active:
            # 1. Handle Input Box Typing
            res = self.input_box.handle_event(event)
            if res == "submit": 
                self._attempt_bid()

            # 2. Update proposed bid variable
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
                if self.auction.withdraw_bid(self.player):
                    self.player.has_withdrawn = True
                    self.feedback_msg = "Bid Withdrawn!"
                    # Update input box to new required bid
                    self.proposed_bid = self.auction.highest_bid + 10
                    self.input_box.set_text(self.proposed_bid)
                else:
                    self.feedback_msg = "Cannot Withdraw!"

            if self.btn_pass.is_clicked(event):
                was_leading = (self.auction.highest_bidder and self.auction.highest_bidder.id == self.player.id)
                self.auction.pass_player(self.player)
                self.feedback_msg = "Withdrawn & Passed" if was_leading else "Passed Round."

        # 4. Handle Round Over -> Next Round OR Game Over
        else:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                # If Game Over (Round 5 finished), Reset Everything
                if self.round_num >= self.max_rounds:
                    # Resolve final state -> Save -> Reset
                    session_profit = self.player.session_profit
                    style_name, style_desc = PlaystyleAnalyzer.analyze(self.player, self.max_rounds)
                    DataManager.save_highscore(self.player.name, session_profit, self.player.items_won)
                    DataManager.update_stats(session_profit, self.player.items_won, style_name)
                    self.reset()
                else:
                    # Normal Next Round
                    self.round_num += 1
                    self.auction.start_round(self.round_num)
                    # Reset input
                    self.proposed_bid = self.auction.highest_bid + 10
                    self.input_box.set_text(self.proposed_bid)
                    self.feedback_msg = ""

        return None

    def _adjust_bid(self, amount):
        self.proposed_bid += amount
        if self.proposed_bid < 0: self.proposed_bid = 0
        self.input_box.set_text(self.proposed_bid)

    def _attempt_bid(self):
        if self.player.is_passing:
            self.feedback_msg = "You have passed this round!"
            return

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
        mouse_pos = pygame.mouse.get_pos()
        
        if self.show_quit_confirm:
            self.btn_confirm_quit.update(mouse_pos)
            self.btn_cancel_quit.update(mouse_pos)
            return

        # --- Simulation Tick ---
        if pygame.time.get_ticks() % 200 < 20: 
            self.auction.run_tick()
            
        self.btn_quit.update(mouse_pos)
        self.btn_minus.update(mouse_pos)
        self.btn_plus.update(mouse_pos)
        self.btn_place_bid.update(mouse_pos)
        self.btn_pass.update(mouse_pos)
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

        # --- Overlays ---
        if self.show_quit_confirm:
            self._draw_quit_overlay(surface)
        elif not self.auction.is_active:
            self._draw_round_end_overlay(surface)

    def _draw_quit_overlay(self, surface):
        # Dim background
        s = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        s.set_alpha(180)
        s.fill((0, 0, 0))
        surface.blit(s, (0,0))
        
        # Dialog Box
        box_w, box_h = 400, 200
        rect = pygame.Rect(SCREEN_WIDTH//2 - box_w//2, SCREEN_HEIGHT//2 - box_h//2, box_w, box_h)
        pygame.draw.rect(surface, THEME_PANEL_BG, rect, border_radius=15)
        pygame.draw.rect(surface, THEME_ACCENT_RED, rect, 2, border_radius=15)
        
        draw_text(surface, "QUIT GAME?", rect.centerx, rect.top + 30, self.font_lg, THEME_ACCENT_RED, "center")
        draw_text(surface, "Progress will not be saved!", rect.centerx, rect.top + 70, self.font_sm, THEME_TEXT_SUB, "center")
        
        self.btn_confirm_quit.draw(surface, self.font_md)
        self.btn_cancel_quit.draw(surface, self.font_md)

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
        
        # Table Header
        h_y = y + 70
        header_color = THEME_TEXT_SUB
        draw_text(surface, "NAME", x + 40, h_y, self.font_sm, header_color, "left")
        draw_text(surface, "BUDGET", cx, h_y, self.font_sm, header_color, "center")
        draw_text(surface, "BID", x + w - 40, h_y, self.font_sm, header_color, "right")
        pygame.draw.line(surface, THEME_BORDER, (x+40, h_y + 25), (x+w-40, h_y + 25), 1)

        row_y = h_y + 40
        # Combine agents and human player for the table
        all_participants = [(self.player.id, self.player.budget, self.player)] + \
                           [(a.id, a.budget, a) for a in self.auction.agents]

        for p_id, p_budget, p_obj in all_participants:
            # Active status color
            is_winning = self.auction.highest_bidder and self.auction.highest_bidder.id == p_id
            name_color = THEME_ACCENT_GOLD if is_winning else THEME_TEXT_MAIN
            
            # Fetch latest bid
            p_bid = next((bid for bidder, bid in reversed(self.auction.bid_stack) if bidder.id == p_id), 0)
            
            # Row Label
            label = f"{p_id} (You)" if p_id == self.player.id else p_id
            
            # Status Indicator (Passed/Out/Won)
            if hasattr(p_obj, 'is_passing') and p_obj.is_passing:
                label += " [PASS]"
                name_color = THEME_TEXT_SUB

            draw_text(surface, label, x + 40, row_y, self.font_sm, name_color, "left")
            draw_text(surface, f"${p_budget}", cx, row_y, self.font_sm, THEME_TEXT_MAIN, "center")
            draw_text(surface, f"${p_bid}" if p_bid else "-", x + w - 40, row_y, self.font_sm, name_color, "right")
            
            row_y += 35
            
        # Activity Feed Divider
        pygame.draw.line(surface, THEME_BORDER, (x+40, row_y + 20), (x+w-40, row_y + 20), 1)
        
        # Activity Feed
        draw_text(surface, "ACTIVITY LOG", x + 40, row_y + 40, self.font_sm, THEME_TEXT_SUB, "left")
        
        log_y = row_y + 75
        logs = self.auction.get_recent_logs()
        for log in logs:
            draw_text(surface, f"> {log}", x + 40, log_y, self.font_sm, THEME_TEXT_MAIN, "left")
            log_y += 25

    def _draw_right_content(self, surface, x, y, w):
        cx = x + w // 2
        
        # 1. Player Finances
        draw_text(surface, "YOUR BUDGET", cx, y + 30, self.font_sm, THEME_TEXT_SUB, "center")
        draw_text(surface, f"$ {self.player.budget}", cx, y + 55, self.font_lg, THEME_ACCENT_GOLD, "center")
        
        # Player Stats Row
        stat_y = y + 95
        pygame.draw.line(surface, THEME_BORDER, (x+30, stat_y), (x+w-30, stat_y), 1)
        
        player_bid = next((bid for bidder, bid in reversed(self.auction.bid_stack) if bidder.id == self.player.id), 0)
        draw_text(surface, "YOUR BID", x + 40, stat_y + 15, self.font_sm, THEME_TEXT_SUB, "left")
        draw_text(surface, f"${player_bid}" if player_bid else "-", x + w - 40, stat_y + 15, self.font_sm, THEME_TEXT_MAIN, "right")
        
        status_txt = "Winner" if self.auction.highest_bidder and self.auction.highest_bidder.id == self.player.id else "Outbid"
        status_color = THEME_ACCENT_GREEN if status_txt == "Winner" else THEME_ACCENT_RED
        if self.player.is_passing: status_txt, status_color = "PASSING", THEME_TEXT_SUB
        
        draw_text(surface, "STATUS", x + 40, stat_y + 40, self.font_sm, THEME_TEXT_SUB, "left")
        draw_text(surface, status_txt, x + w - 40, stat_y + 40, self.font_sm, status_color, "right")

        # 2. Highest Bid (Central focus)
        mid_zone_y = y + 200 
        pygame.draw.line(surface, THEME_BORDER, (x+30, mid_zone_y - 30), (x+w-30, mid_zone_y - 30), 1)
        draw_text(surface, "CURRENT HIGH BID", cx, mid_zone_y - 15, self.font_sm, THEME_TEXT_SUB, "center")
        draw_text(surface, f"$ {self.auction.highest_bid}", cx, mid_zone_y + 25, self.font_xl, THEME_TEXT_MAIN, "center")
        
        pygame.draw.line(surface, THEME_BORDER, (x+30, mid_zone_y + 65), (x+w-30, mid_zone_y + 65), 1)
        
        # 3. User Input Section
        input_y = mid_zone_y + 80
        min_req = self.auction.highest_bid + 10
        draw_text(surface, f"Min Required: ${min_req}", cx, input_y, self.font_sm, (100, 100, 100), "center")
        
        # Update input box position (re-centering just in case)
        self.input_box.rect.y = input_y + 25
        self.input_box.draw(surface)
        
        self.btn_minus.rect.y = input_y + 85
        self.btn_plus.rect.y = input_y + 85
        self.btn_minus.draw(surface, self.font_md)
        self.btn_plus.draw(surface, self.font_md)
        
        self.btn_place_bid.rect.y = input_y + 140
        bid_color = THEME_TEXT_SUB if self.player.is_passing else THEME_ACCENT_GREEN
        self.btn_place_bid.base_color = bid_color
        self.btn_place_bid.draw(surface, self.font_md)
        
        self.btn_pass.rect.y = input_y + 210
        self.btn_pass.draw(surface, self.font_md)
        
        self.btn_withdraw.rect.y = input_y + 260
        withdraw_color = THEME_TEXT_SUB if self.player.is_passing else THEME_ACCENT_RED
        self.btn_withdraw.base_color = withdraw_color
        self.btn_withdraw.draw(surface, self.font_md)
        
        if self.feedback_msg:
            draw_text(surface, self.feedback_msg, cx, input_y + 310, self.font_sm, THEME_ACCENT_RED, "center")

    def _draw_round_end_overlay(self, surface):
        s = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        s.set_alpha(200)
        s.fill((10, 12, 20))
        surface.blit(s, (0,0))
        
        cx, cy = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2
        
        if self.round_num < self.max_rounds:
            # --- INTERMEDIATE ROUND OVER ---
            winner_id = self.auction.highest_bidder.id if self.auction.highest_bidder else "Nobody"
            profit = 0
            if self.auction.highest_bidder:
                 profit = self.auction.current_item.get_true_value() - self.auction.highest_bid
            
            # Draw Box
            box_w, box_h = 450, 320
            pygame.draw.rect(surface, THEME_PANEL_BG, (cx-box_w//2, cy-box_h//2, box_w, box_h), border_radius=15)
            pygame.draw.rect(surface, THEME_BORDER, (cx-box_w//2, cy-box_h//2, box_w, box_h), 1, border_radius=15)

            draw_text(surface, "ROUND COMPLETE", cx, cy - 120, self.font_lg, THEME_ACCENT_GOLD, "center")
            
            # Result rows
            row_y = cy - 60
            self._draw_overlay_row(surface, cx, row_y, "Winner", winner_id, THEME_TEXT_MAIN)
            self._draw_overlay_row(surface, cx, row_y + 35, "Final Price", f"${self.auction.highest_bid}", THEME_TEXT_SUB)
            self._draw_overlay_row(surface, cx, row_y + 70, "Actual Value", f"${self.auction.current_item.get_true_value()}", THEME_TEXT_MAIN)
            
            p_color = THEME_ACCENT_GREEN if profit >= 0 else THEME_ACCENT_RED
            draw_text(surface, f"PROFIT: ${profit}", cx, cy + 60, self.font_lg, p_color, "center")
            
            draw_text(surface, "Press [SPACE] for Next Round", cx, cy + 120, self.font_sm, THEME_ACCENT_CYAN, "center")

        else:
            # --- FINAL GAME OVER SCREEN ---
            box_w, box_h = 700, 500
            pygame.draw.rect(surface, THEME_PANEL_BG, (cx-box_w//2, cy-box_h//2, box_w, box_h), border_radius=20)
            pygame.draw.rect(surface, THEME_ACCENT_GOLD, (cx-box_w//2, cy-box_h//2, box_w, box_h), 2, border_radius=20)

            draw_text(surface, "SESSION SUMMARY", cx, cy - 210, self.font_header if hasattr(self, 'font_header') else self.font_xl, THEME_ACCENT_GOLD, "center")
            
            # Session Stats
            final_profit = self.player.session_profit
            p_color = THEME_ACCENT_GREEN if final_profit >= 0 else THEME_ACCENT_RED
            metrics = PlaystyleAnalyzer.get_behavior_metrics(self.player)
            style_name, style_desc = PlaystyleAnalyzer.analyze(self.player, self.max_rounds)
            
            # Stats Grid
            self._draw_overlay_stat(surface, cx - 220, cy - 100, "TOTAL PROFIT", f"${final_profit}", p_color)
            self._draw_overlay_stat(surface, cx,       cy - 100, "ITEMS WON", f"{self.player.items_won}", THEME_ACCENT_GOLD)
            self._draw_overlay_stat(surface, cx + 220, cy - 100, "FINAL BUDGET", f"${self.player.budget}", THEME_TEXT_MAIN)
            
            # Playstyle Badge
            pygame.draw.rect(surface, (35, 40, 60), (cx-300, cy - 10, 600, 160), border_radius=15)
            draw_text(surface, "YOUR PLAYSTYLE", cx, cy + 5, self.font_sm, THEME_ACCENT_CYAN, "center")
            draw_text(surface, style_name.upper(), cx, cy + 45, self.font_lg, THEME_ACCENT_GOLD, "center")
            
            # Description (Wrapped)
            self._draw_wrapped_text(surface, style_desc, cx, cy + 85, 550, self.font_sm, THEME_TEXT_MAIN)
            
            # Detailed Metrics
            m_y = cy + 180
            draw_text(surface, f"Avg Reaction: {metrics['avg_reaction']}", cx - 200, m_y, self.font_sm, THEME_TEXT_SUB, "center")
            draw_text(surface, f"First Bid: {metrics['first_bid_time']}", cx, m_y, self.font_sm, THEME_TEXT_SUB, "center")
            draw_text(surface, f"Risk: {metrics['risk']}", cx + 200, m_y, self.font_sm, THEME_TEXT_SUB, "center")
            
            draw_text(surface, f"Withdrawals: {metrics['withdrawals']} | Passes: {metrics['passes']}", 
                      cx, m_y + 22, self.font_sm, THEME_ACCENT_CYAN, "center")

            draw_text(surface, "Press [SPACE] to Restart Game", cx, cy + 225, self.font_sm, THEME_ACCENT_CYAN, "center")

    def _draw_wrapped_text(self, surface, text, x, y, max_w, font, color):
        words = text.split()
        lines = []
        current_line = []
        
        for word in words:
            test_line = " ".join(current_line + [word])
            if font.size(test_line)[0] < max_w:
                current_line.append(word)
            else:
                lines.append(" ".join(current_line))
                current_line = [word]
        lines.append(" ".join(current_line))
        
        for i, line in enumerate(lines):
            draw_text(surface, line, x, y + (i * 22), font, color, "center")

    def _draw_overlay_row(self, surface, cx, y, label, value, val_color):
        draw_text(surface, f"{label}:", cx - 10, y, self.font_md, THEME_TEXT_SUB, "right")
        draw_text(surface, value, cx + 10, y, self.font_md, val_color, "left")

    def _draw_overlay_stat(self, surface, cx, y, label, value, color):
        draw_text(surface, label, cx, y, self.font_sm, THEME_TEXT_SUB, "center")
        draw_text(surface, value, cx, y + 35, self.font_lg, color, "center")
