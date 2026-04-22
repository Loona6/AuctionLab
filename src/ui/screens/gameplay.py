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
from src.config import MIN_INCREMENT, POWERUP_COST

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
        
        # Audio & Timing State
        from src.logic.audio_manager import AudioManager
        self.audio = AudioManager()
        self.last_tick_second = -1
        self.played_round_end_sound = False
        self.last_tick_time = pygame.time.get_ticks()
        self.frozen_progress = None # Freeze timer on sale
        self.frozen_seconds = None
        
        self.show_withdrawal_confirm = False # NEW: Safety modal state
        self.pause_start_ticks = 0           # NEW: Tracking pause time
        
        # Pre-set the user's proposed bid (Highest + Increment)
        self.proposed_bid = self.auction.highest_bid + MIN_INCREMENT
        self.feedback_msg = ""
        
        # --- Animation & Screen Shake State ---
        self.shake_offset = [0, 0]
        self.shake_duration = 0
        self.screen_flash = 0 # Alpha value
        try:
            self.gavel_img = pygame.image.load("assets/images/gavel.png").convert_alpha()
            self.gavel_img = pygame.transform.smoothscale(self.gavel_img, (120, 120))
        except:
            self.gavel_img = None
            
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
        self.proposed_bid = self.auction.highest_bid + MIN_INCREMENT
        self.input_box.set_text(self.proposed_bid)
        self.frozen_progress = None
        self.frozen_seconds = None
        self.show_withdrawal_confirm = False
        self.auction.is_paused = False
        
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

        # D. Powerup Button
        self.btn_powerup = NeonButton(cx_panel3 - btn_w//2, self.start_y + 580, btn_w, 45, "EXPERT ADVICE ($15)", THEME_ACCENT_GOLD, "powerup")

        # Confirmation Dialog Buttons
        self.btn_confirm_quit = NeonButton(SCREEN_WIDTH//2 - 110, SCREEN_HEIGHT//2 + 20, 100, 40, "YES", THEME_ACCENT_RED, "confirm_exit")
        self.btn_cancel_quit = NeonButton(SCREEN_WIDTH//2 + 10, SCREEN_HEIGHT//2 + 20, 100, 40, "NO", THEME_BORDER, "cancel_exit")

        # Withdrawal Confirmation Buttons
        self.btn_confirm_wd = NeonButton(SCREEN_WIDTH//2 - 110, SCREEN_HEIGHT//2 + 20, 100, 40, "CONFIRM", THEME_ACCENT_RED, "confirm_wd")
        self.btn_cancel_wd = NeonButton(SCREEN_WIDTH//2 + 10, SCREEN_HEIGHT//2 + 20, 100, 40, "CANCEL", THEME_BORDER, "cancel_wd")

    def handle_events(self, event):
        # --- Quit Confirmation Handling ---
        if self.show_quit_confirm:
            if self.btn_confirm_quit.is_clicked(event):
                return "back"
            if self.btn_cancel_quit.is_clicked(event):
                self.show_quit_confirm = False
            return None

        # --- Withdrawal Confirmation Handling ---
        if self.show_withdrawal_confirm:
            if self.btn_confirm_wd.is_clicked(event):
                if self.auction.withdraw_bid(self.player):
                    self.player.has_withdrawn = True
                    penalty = max(10, int(self.auction.highest_bid * 0.05))
                    self.feedback_msg = f"PENALTY! -${penalty} paid."
                    self.shake_duration = 10
                self.show_withdrawal_confirm = False
                self.auction.is_paused = False
                # Compensation for pause duration
                duration = pygame.time.get_ticks() - self.pause_start_ticks
                self.auction.patience_deadline_ms += duration
            if self.btn_cancel_wd.is_clicked(event):
                self.show_withdrawal_confirm = False
                self.auction.is_paused = False
                # Compensation for pause duration
                duration = pygame.time.get_ticks() - self.pause_start_ticks
                self.auction.patience_deadline_ms += duration
            return None

        # --- Menu Navigation ---
        if self.btn_quit.is_clicked(event):
            self.audio.play("click") # Added audio trigger
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
                is_winner = self.auction.highest_bidder and self.auction.highest_bidder.id == self.player.id
                if is_winner:
                    self.show_withdrawal_confirm = True
                    self.auction.is_paused = True
                    self.pause_start_ticks = pygame.time.get_ticks()
                else:
                    if self.auction.withdraw_bid(self.player):
                        self.player.has_withdrawn = True
                        self.feedback_msg = "Bid Withdrawn!"
                    else:
                        self.feedback_msg = "Cannot Withdraw!"

            if self.btn_pass.is_clicked(event):
                was_leading = (self.auction.highest_bidder and self.auction.highest_bidder.id == self.player.id)
                self.auction.pass_player(self.player)
                self.feedback_msg = "You are already the highest bidder." if was_leading else "Passed Round."

            if self.btn_powerup.is_clicked(event):
                if self.player.powerup_used:
                    self.feedback_msg = "Advice already received!"
                elif self.player.session_profit < POWERUP_COST:
                    self.feedback_msg = "Insufficient Profit!"
                else:
                    self.player.spend_profit(POWERUP_COST)
                    self.player.powerup_used = True
                    self.audio.play("click")
                    self.feedback_msg = "Analysis complete!"

        # 4. Handle Round Over -> Next Round OR Game Over
        else:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                # If Game Over (Round 5 finished), Reset Everything
                if self.round_num >= self.max_rounds:
                    # Resolve final state -> Save -> Reset
                    session_profit = self.player.session_profit
                    style_name, style_desc = PlaystyleAnalyzer.analyze(self.player, self.max_rounds)
                    DataManager.save_highscore(self.player.name, session_profit, self.player.items_won)
                    DataManager.update_stats(session_profit, self.player.items_won, self.player.session_spent, style_name)
                    # Save final logs
                    self.auction.save_session_logs("gameplay_logs.txt")
                    self.reset()
                else:
                    # Normal Next Round
                    self.round_num += 1
                    self.auction.start_round(self.round_num)
                    # Reset timer freeze for new round
                    self.frozen_progress = None
                    self.frozen_seconds = None
                    
                    # Trigger incremental save
                    self.auction.save_session_logs("gameplay_logs.txt")
                    # Reset input
                    self.proposed_bid = self.auction.highest_bid + MIN_INCREMENT
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
            
        if getattr(self.player, 'lockout_rounds', 0) > 0:
            self.feedback_msg = "LOCKED OUT: Wait for the next round!"
            return

        val = self.proposed_bid
        
        # Use Player Class for logic
        if self.player.place_bid(self.auction, val):
            self.feedback_msg = ""
            # Prepare next increment automatically
            self.proposed_bid = val + MIN_INCREMENT # Use global MIN_INCREMENT
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

        if self.show_withdrawal_confirm:
            self.btn_confirm_wd.update(mouse_pos)
            self.btn_cancel_wd.update(mouse_pos)
            return

        # --- Simulation Tick (Every 200ms) ---
        now = pygame.time.get_ticks()
        if now - self.last_tick_time >= 200 and not self.auction.is_paused:
            self.auction.run_tick()
            self.last_tick_time = now
            
            # --- Timer Freeze Logic ---
            if not self.auction.is_active and self.frozen_progress is None:
                # Calculate final progress to freeze the bar
                ms_left = max(0, self.auction.patience_deadline_ms - now)
                total_ms = self.auction.current_max_patience * self.auction.TICK_INTERVAL_MS
                self.frozen_progress = ms_left / total_ms if total_ms > 0 else 0
                self.frozen_seconds = self._get_display_seconds()
            
            # Auto-fill bid box: always show the next minimum required bid
            # Only override if user isn't currently editing (i.e. box not focused)
            if self.auction.is_active and not self.input_box.active:
                next_min = self.auction.highest_bid + MIN_INCREMENT
                if self.proposed_bid < next_min:
                    self.proposed_bid = next_min
                    self.input_box.set_text(self.proposed_bid)
            
            # --- Ticking Clock Sounds (Final 5 seconds) ---
            if self.auction.is_active:
                seconds_left = self._get_display_seconds()
                if 0 < seconds_left <= 5:
                    if seconds_left != self.last_tick_second:
                        self.audio.play("tick")
                        self.last_tick_second = seconds_left
                else:
                    self.last_tick_second = -1
                self.played_round_end_sound = False
            else:
                # --- Result Overlay Popup Sound ---
                if not self.played_round_end_sound:
                    self.audio.play("popup")
                    self.played_round_end_sound = True
            
        self.btn_quit.update(mouse_pos)
        self.btn_minus.update(mouse_pos)
        self.btn_plus.update(mouse_pos)
        self.btn_place_bid.update(mouse_pos)
        self.btn_pass.update(mouse_pos)
        self.btn_withdraw.update(mouse_pos)
        self.btn_powerup.update(mouse_pos)
        
        # --- Animation Updates ---
        if self.shake_duration > 0:
            import random
            self.shake_offset = [random.randint(-5, 5), random.randint(-5, 5)]
            self.shake_duration -= 1
        else:
            self.shake_offset = [0, 0]
            
        if self.screen_flash > 0:
            self.screen_flash = max(0, self.screen_flash - 15)
            
        # Trigger Flash/Shake on specific state changes
        if self.auction.is_active:
            # Check if state JUST changed (within one tick)
            is_new_state = (self.auction.ticks - self.auction.last_state_change_tick) <= 1
            if is_new_state:
                if self.auction.auction_state == "Going Twice":
                    self.screen_flash = 40 # Subtle red tint flash
                elif self.auction.auction_state == "Active" and self.auction.last_state_change_tick > 0:
                     # New bid reset
                     pass 
        else:
            # Sold/Round End
            if not self.auction.is_active and self.auction.highest_bidder and self.screen_flash == 0 and not self.played_round_end_sound:
                 self.screen_flash = 120
                 self.shake_duration = 10

    def draw(self, surface):
        surface.fill(THEME_BG)
        
        # Apply Screen Shake Offset to all content
        ox, oy = self.shake_offset
        
        # Header
        self.btn_quit.draw(surface, self.font_sm) # Quit button stays fixed or shakes? Usually fixed is better for UI, but let's shake it for impact
        self._draw_top_bar(surface)
        
        # --- Layout Panels ---
        x_cursor = self.pad + ox
        y_panels = self.start_y + oy
        
        # 1. Left Panel (Item Info)
        self._draw_panel(surface, x_cursor, y_panels, self.col1_w, self.panel_h)
        self._draw_left_content(surface, x_cursor, y_panels, self.col1_w)
        
        x_cursor += self.col1_w + self.pad
        
        # 2. Center Panel (Auction Floor)
        self._draw_panel(surface, x_cursor, y_panels, self.col2_w, self.panel_h)
        self._draw_center_content(surface, x_cursor, y_panels, self.col2_w)
        
        # --- Draw Auctioneer Callout (Overlaying center panel) ---
        self._draw_auctioneer_callout(surface, x_cursor, y_panels, self.col2_w)
        
        x_cursor += self.col2_w + self.pad
        
        # 3. Right Panel (Controls)
        self._draw_panel(surface, x_cursor, y_panels, self.col3_w, self.panel_h)
        self._draw_right_content(surface, x_cursor, y_panels, self.col3_w)

        # --- Overlays ---
        if self.show_quit_confirm:
            self._draw_quit_overlay(surface)
        elif self.show_withdrawal_confirm:
            self._draw_withdrawal_confirm_overlay(surface)
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

    def _draw_withdrawal_confirm_overlay(self, surface):
        # Dim background
        s = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        s.set_alpha(180)
        s.fill((10, 10, 15))
        surface.blit(s, (0,0))
        
        # Dialog Box
        box_w, box_h = 450, 240
        rect = pygame.Rect(SCREEN_WIDTH//2 - box_w//2, SCREEN_HEIGHT//2 - box_h//2, box_w, box_h)
        pygame.draw.rect(surface, THEME_PANEL_BG, rect, border_radius=15)
        pygame.draw.rect(surface, THEME_ACCENT_RED, rect, 2, border_radius=15)
        
        # Calculate penalty for display
        penalty = max(10, int(self.auction.highest_bid * 0.05))
        
        draw_text(surface, "CONFIRM WITHDRAWAL?", rect.centerx, rect.top + 30, self.font_lg, THEME_ACCENT_RED, "center")
        draw_text(surface, f"Penalty: ${penalty}", rect.centerx, rect.top + 70, self.font_md, THEME_ACCENT_GOLD, "center")
        draw_text(surface, "You will also be locked out for the round.", rect.centerx, rect.top + 105, self.font_sm, THEME_TEXT_SUB, "center")
        
        self.btn_confirm_wd.draw(surface, self.font_md)
        self.btn_cancel_wd.draw(surface, self.font_md)

    def _get_display_seconds(self):
        """Compute remaining seconds from real-time deadline for stutter-free display."""
        try:
            import pygame
            ms_left = max(0, self.auction.patience_deadline_ms - pygame.time.get_ticks())
            return ms_left // 1000
        except Exception:
            return max(0, self.auction.current_patience // 5)

    def _draw_top_bar(self, surface):
        # --- CENTERED ROUND INFO ---
        info_text = f"ROUND {self.round_num} / {self.max_rounds}"
        draw_text(surface, info_text, SCREEN_WIDTH // 2, 40, self.font_md, THEME_TEXT_MAIN, "center")
        
        # --- PROGRESS BAR (TIMER) ---
        bar_w, bar_h = 300, 8
        bar_x = (SCREEN_WIDTH - bar_w) // 2
        bar_y = 70
        
        # Background
        pygame.draw.rect(surface, THEME_PANEL_BG, (bar_x, bar_y, bar_w, bar_h), border_radius=4)
        
        # Fill — use real-time ms for smooth animation
        if self.frozen_progress is not None:
            progress = self.frozen_progress
        else:
            try:
                ms_left = max(0, self.auction.patience_deadline_ms - pygame.time.get_ticks())
                total_ms = self.auction.current_max_patience * self.auction.TICK_INTERVAL_MS
                progress = ms_left / total_ms if total_ms > 0 else 0
            except Exception:
                progress = self.auction.current_patience / self.auction.current_max_patience
        
        fill_w = int(bar_w * max(0, progress))
        
        # Urgency Colors
        if progress > 0.3:
            color = THEME_ACCENT_GREEN
        elif progress > 0.1:
            color = (255, 165, 0) # Orange
        else:
            # Blinking red
            blink = (pygame.time.get_ticks() // 250) % 2
            color = THEME_ACCENT_RED if blink else (100, 0, 0)
        
        if fill_w > 0:
            pygame.draw.rect(surface, color, (bar_x, bar_y, fill_w, bar_h), border_radius=4)
        
        # --- TOP RIGHT TIMER TEXT ---
        if self.frozen_seconds is not None:
            seconds_left = self.frozen_seconds
        else:
            seconds_left = self._get_display_seconds()
            
        draw_text(surface, f"00:{seconds_left:02d}", SCREEN_WIDTH - 60, 40, self.font_md, color, "center")

    def _draw_auctioneer_callout(self, surface, x, y, w):
        if not self.auction.is_active and self.auction.auction_state != "Active":
            # We handle SOLD/Round End specifically
            state = self.auction.auction_state
        else:
            state = self.auction.auction_state
            
        if state not in ["Going Once", "Going Twice", "Active"] and self.auction.is_active:
             return
             
        # Center of the panel
        cx, cy = x + w // 2, y + self.panel_h // 2 + 100
        
        # Animation variables
        ticks_since_change = self.auction.ticks - self.auction.last_state_change_tick
        pulse_val = (pygame.time.get_ticks() // 5) % 100
        
        callout_text = ""
        color = THEME_ACCENT_GOLD
        scale = 1.0
        
        if state == "Going Once":
            callout_text = "GOING ONCE!"
            color = (255, 255, 0) # Yellow
            scale = 1.0 + (pulse_val / 1000) # Slight pulse
        elif state == "Going Twice":
            callout_text = "GOING TWICE!!"
            color = (255, 140, 0) # Orange
            scale = 1.1 + (pulse_val / 500) # Bigger pulse
        elif not self.auction.is_active and self.auction.highest_bidder:
            callout_text = "SOLD!!!"
            color = THEME_ACCENT_RED
            scale = 1.5
            
        if not callout_text: return
        
        # 1. Gavel Animation
        if self.gavel_img:
            # Downward snap animation based on ticks_since_change
            # First 3 ticks: -30 to 0 degrees
            angle = max(-30, -30 + (ticks_since_change * 10))
            if not self.auction.is_active: angle = 0 # Settled
            
            rotated_gavel = pygame.transform.rotate(self.gavel_img, angle)
            g_rect = rotated_gavel.get_rect(center=(cx, cy - 80))
            surface.blit(rotated_gavel, g_rect)
            
        # 2. Pulsing Text
        pulse_font = pygame.font.SysFont(FONT_NAME, int(50 * scale), bold=True)
        # Drop shadow for readability
        draw_text(surface, callout_text, cx + 2, cy + 2, pulse_font, (0,0,0), "center")
        draw_text(surface, callout_text, cx, cy, pulse_font, color, "center")
        
        # 3. Screen Flash / Shake
        if self.screen_flash > 0:
            flash_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            flash_color = (255, 255, 255) if not self.auction.is_active else (255, 0, 0)
            flash_surf.fill(flash_color)
            flash_surf.set_alpha(self.screen_flash)
            surface.blit(flash_surf, (0,0))

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
        # Show "Unknown Item" or generic name (Wrapped)
        name_y = img_rect.bottom + 25
        hint_y_start = self._draw_wrapped_text(surface, "Mystery Artifact", cx, name_y, w - 40, self.font_lg, THEME_TEXT_MAIN)
        
        # Show the HINT (Wrapped to fit panel)
        # Add 15px gap after item name
        if self.player.powerup_used:
            hint = self.auction.current_item.get_premium_hint()
            hint_color = THEME_ACCENT_CYAN
        else:
            hint = f"\"{self.auction.current_item.get_hint()}\""
            hint_color = THEME_ACCENT_GOLD
            
        tags_y_start = self._draw_wrapped_text(surface, hint, cx, hint_y_start + 15, w - 40, self.font_md, hint_color)
        
        # Tags? Maybe strategy hints later
        # Add 10px gap after hint
        draw_text(surface, "Value Hidden", cx, tags_y_start + 10, self.font_sm, THEME_TEXT_SUB, "center")

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
            elif hasattr(p_obj, 'state'):
                if p_obj.state == "Pass":
                    label += " [PASS]"
                    name_color = THEME_TEXT_SUB
                elif p_obj.state == "Withdraw":
                    label += " [WD]"
                    name_color = THEME_ACCENT_RED

            # Winner Highlight
            if is_winning and not self.auction.is_active:
                 # Flash green/gold for the winner row
                 row_rect = pygame.Rect(x + 35, row_y - 5, w - 70, 30)
                 blink = (pygame.time.get_ticks() // 200) % 2
                 if blink: pygame.draw.rect(surface, (0, 100, 0), row_rect, border_radius=5)
                 
            draw_text(surface, label, x + 40, row_y, self.font_sm, name_color, "left")
            draw_text(surface, f"${p_budget}", cx, row_y, self.font_sm, THEME_TEXT_MAIN, "center")
            draw_text(surface, f"${p_bid}" if p_bid else "-", x + w - 40, row_y, self.font_sm, name_color, "right")
            
            # Show Profit popup above winner if recently won
            if is_winning and not self.auction.is_active:
                 profit = self.auction.current_item.get_true_value() - self.auction.highest_bid
                 p_text = f"+${profit}" if profit >= 0 else f"${profit}"
                 p_color = THEME_ACCENT_GREEN if profit >= 0 else THEME_ACCENT_RED
                 # Floating effect
                 float_y = row_y - 20 - ( (pygame.time.get_ticks() // 10) % 20 )
                 draw_text(surface, p_text, x + 100, float_y, self.font_sm, p_color, "center")
            
            row_y += 35
            
        # Activity Feed Divider
        pygame.draw.line(surface, THEME_BORDER, (x+40, row_y + 20), (x+w-40, row_y + 20), 1)
        
        # Activity Feed
        draw_text(surface, "ACTIVITY LOG", x + 40, row_y + 40, self.font_sm, THEME_TEXT_SUB, "left")
        
        # Subtle Ticker Background
        log_box_rect = pygame.Rect(x + 30, row_y + 65, w - 60, self.panel_h - (row_y - y + 80))
        pygame.draw.rect(surface, (15, 17, 25), log_box_rect, border_radius=10)
        
        log_y = row_y + 75
        logs = self.auction.get_recent_logs()
        for log in logs:
            # 1. Filter Redundancy (Going once/twice is already central)
            if "Going once" in log or "Going twice" in log:
                continue
                
            # 2. Determine Event Type & Color
            accent_color = THEME_TEXT_SUB
            text_color = THEME_TEXT_MAIN
            
            if "bids" in log.lower():
                accent_color = THEME_ACCENT_CYAN
            elif "sold" in log.lower() or "result" in log.upper():
                accent_color = THEME_ACCENT_GOLD
                text_color = THEME_ACCENT_GOLD
            elif "withdrawn" in log.lower() or "disqualified" in log.upper():
                accent_color = THEME_ACCENT_RED
            elif "!!!" in log:
                accent_color = THEME_ACCENT_GOLD
            
            # 3. Draw Vertical Accent Line
            if log_y + 20 > log_box_rect.bottom:
                break
                
            pygame.draw.line(surface, accent_color, (x + 40, log_y + 2), (x + 40, log_y + 18), 3)
            
            # 4. Draw Clean Text (No ">" prefix)
            clean_log = log.replace("--- ", "").replace(" ---", "")
            log_y = self._draw_wrapped_text(surface, clean_log, x + 50, log_y, w - 90, self.font_sm, text_color, "left")
            log_y += 8 # Better spacing
            
            # Final safety: stop if we've passed the bottom
            if log_y > log_box_rect.bottom - 20:
                break

    def _draw_right_content(self, surface, x, y, w):
        cx = x + w // 2
        
        # 1. Player Finances (Side-by-side for space)
        lx, rx = x + 60, x + w - 60
        draw_text(surface, "BUDGET", lx, y + 30, self.font_sm, THEME_TEXT_SUB, "left")
        draw_text(surface, f"${self.player.budget}", lx, y + 55, self.font_lg, THEME_ACCENT_GOLD, "left")
        
        draw_text(surface, "PROFIT", rx, y + 30, self.font_sm, THEME_TEXT_SUB, "right")
        draw_text(surface, f"${self.player.session_profit}", rx, y + 55, self.font_md, THEME_ACCENT_GREEN, "right")
        
        # Player Stats Row
        stat_y = y + 90
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
        mid_zone_y = y + 185 
        pygame.draw.line(surface, THEME_BORDER, (x+30, mid_zone_y - 25), (x+w-30, mid_zone_y - 25), 1)
        draw_text(surface, "CURRENT HIGH BID", cx, mid_zone_y - 10, self.font_sm, THEME_TEXT_SUB, "center")
        draw_text(surface, f"$ {self.auction.highest_bid}", cx, mid_zone_y + 25, self.font_xl, THEME_TEXT_MAIN, "center")
        
        pygame.draw.line(surface, THEME_BORDER, (x+30, mid_zone_y + 60), (x+w-30, mid_zone_y + 60), 1)
        
        # 3. User Input Section
        input_y = mid_zone_y + 75
        min_req = self.auction.highest_bid + MIN_INCREMENT
        draw_text(surface, f"Min Required: ${min_req}", cx, input_y, self.font_sm, (100, 100, 100), "center")
        
        # Update input box position (re-centering just in case)
        self.input_box.rect.y = input_y + 25
        self.input_box.draw(surface)
        
        self.btn_minus.rect.y = input_y + 75
        self.btn_plus.rect.y = input_y + 75
        self.btn_minus.draw(surface, self.font_md)
        self.btn_plus.draw(surface, self.font_md)
        
        self.btn_place_bid.rect.y = input_y + 125
        is_locked = getattr(self.player, 'lockout_rounds', 0) > 0
        
        if is_locked:
            bid_color = (150, 70, 70) # Muted red
            self.btn_place_bid.text = "🔒 LOCKED"
        else:
            bid_color = THEME_TEXT_SUB if self.player.is_passing else THEME_ACCENT_GREEN
            self.btn_place_bid.text = "PLACE BID"
            
        self.btn_place_bid.base_color = bid_color
        self.btn_place_bid.draw(surface, self.font_md)
        
        self.btn_pass.rect.y = input_y + 190
        self.btn_pass.draw(surface, self.font_md)
        
        self.btn_withdraw.rect.y = input_y + 235
        withdraw_color = THEME_TEXT_SUB if self.player.is_passing else THEME_ACCENT_RED
        self.btn_withdraw.base_color = withdraw_color
        self.btn_withdraw.draw(surface, self.font_md)
        
        self.btn_powerup.rect.y = input_y + 280
        can_buy = self.player.session_profit >= POWERUP_COST and not self.player.powerup_used
        self.btn_powerup.base_color = THEME_ACCENT_GOLD if can_buy else THEME_TEXT_SUB
        self.btn_powerup.draw(surface, self.font_sm)
        
        if self.feedback_msg:
            draw_text(surface, self.feedback_msg, cx, input_y + 335, self.font_sm, THEME_ACCENT_RED, "center")

    def _draw_round_end_overlay(self, surface):
        # 1. Darker backdrop for focus
        s = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        s.set_alpha(220)
        s.fill((10, 12, 20))
        surface.blit(s, (0,0))
        
        cx, cy = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2
        
        if self.round_num < self.max_rounds:
            # --- INTERMEDIATE ROUND OVER ---
            winner_id = self.auction.highest_bidder.id if self.auction.highest_bidder else "None"
            profit = 0
            is_sold = winner_id != "None" and not winner_id.startswith("None (Disqualified)")
            
            if is_sold:
                 profit = self.auction.current_item.get_true_value() - self.auction.highest_bid
            
            # Draw Premium Box
            box_w, box_h = 500, 380
            rect = pygame.Rect(cx-box_w//2, cy-box_h//2, box_w, box_h)
            pygame.draw.rect(surface, THEME_PANEL_BG, rect, border_radius=20)
            
            # Border color based on outcome
            border_color = THEME_ACCENT_GOLD if is_sold else THEME_TEXT_SUB
            pygame.draw.rect(surface, border_color, rect, 2, border_radius=20)

            # Header
            header_text = "SOLD!" if is_sold else "PASSED"
            header_color = THEME_ACCENT_GOLD if is_sold else THEME_ACCENT_RED
            draw_text(surface, header_text, cx, rect.top + 50, self.font_xl, header_color, "center")
            draw_text(surface, "ROUND COMPLETE", cx, rect.top + 95, self.font_sm, THEME_TEXT_SUB, "center")
            
            # Divider
            pygame.draw.line(surface, THEME_BORDER, (cx - 150, rect.top + 120), (cx + 150, rect.top + 120), 1)
            
            # Result rows
            row_y = rect.top + 155
            self._draw_overlay_row(surface, cx, row_y, "Winner", winner_id, THEME_TEXT_MAIN)
            self._draw_overlay_row(surface, cx, row_y + 40, "Final Price", f"${self.auction.highest_bid}", THEME_TEXT_SUB)
            self._draw_overlay_row(surface, cx, row_y + 80, "Actual Value", f"${self.auction.current_item.get_true_value()}", THEME_TEXT_MAIN)
            
            # Profit/Loss Section
            if is_sold:
                p_text = f"PROFIT: ${profit}" if profit >= 0 else f"LOSS: ${abs(profit)}"
                p_color = THEME_ACCENT_GREEN if profit >= 0 else THEME_ACCENT_RED
                draw_text(surface, p_text, cx, rect.bottom - 80, self.font_lg, p_color, "center")
            else:
                draw_text(surface, "Item went unsold.", cx, rect.bottom - 80, self.font_md, THEME_TEXT_SUB, "center")
            
            draw_text(surface, "Press [SPACE] for Next Round", cx, rect.bottom - 35, self.font_sm, THEME_ACCENT_CYAN, "center")

        else:
            # --- FINAL GAME OVER SCREEN ---
            box_w, box_h = 950, 560
            box_x, box_y = cx - box_w // 2, cy - box_h // 2
            pygame.draw.rect(surface, THEME_PANEL_BG, (box_x, box_y, box_w, box_h), border_radius=20)
            pygame.draw.rect(surface, THEME_ACCENT_GOLD, (box_x, box_y, box_w, box_h), 2, border_radius=20)

            draw_text(surface, "SESSION SUMMARY", cx, box_y + 40, self.font_header if hasattr(self, 'font_header') else self.font_xl, THEME_ACCENT_GOLD, "center")
            
            # --- CALCULATE GLOBAL STANDINGS (Net Worth) ---
            participants = []
            for p in [self.player] + self.auction.agents:
                # Net Worth = Final Budget + Value of Items Won
                net_worth = p.budget + (getattr(p, 'items_value_won', 0))
                participants.append({
                    'id': p.id,
                    'is_player': p.id == self.player.id,
                    'budget': p.budget,
                    'item_val': getattr(p, 'items_value_won', 0),
                    'net_worth': net_worth
                })
            
            # Sort by Net Worth
            participants.sort(key=lambda x: x['net_worth'], reverse=True)
            winner = participants[0]

            # Divider line (Vertical)
            pygame.draw.line(surface, THEME_BORDER, (cx, box_y + 80), (cx, box_y + box_h - 60), 1)

            # --- COLUMN 1: GLOBAL (LEFT) ---
            lx = box_x + (box_w // 4)
            ly = box_y + 100
            
            # Winner Announcement
            w_text = f"Winner: {winner['id']}"
            draw_text(surface, w_text, lx, ly, self.font_lg, THEME_ACCENT_GOLD, "center")
            draw_text(surface, f"Net Worth: ${winner['net_worth']}", lx, ly + 35, self.font_md, THEME_TEXT_MAIN, "center")
            
            # Breakdown of Wealth for Winner
            draw_text(surface, f"Budget: ${winner['budget']}  |  Item Value: ${winner['item_val']}", 
                      lx, ly + 65, self.font_sm, THEME_TEXT_SUB, "center")

            # Leaderboard
            ly_board = ly + 110
            draw_text(surface, "LEADERBOARD", lx, ly_board, self.font_sm, THEME_ACCENT_CYAN, "center")
            pygame.draw.line(surface, THEME_BORDER, (lx - 150, ly_board + 15), (lx + 150, ly_board + 15), 1)
            
            ly_row = ly_board + 30
            for i, p in enumerate(participants[:6]): # Show top 6
                rank_color = THEME_ACCENT_GOLD if i == 0 else (THEME_TEXT_MAIN if p['is_player'] else THEME_TEXT_SUB)
                p_label = f"{i+1}. {p['id']}"
                if p['is_player']: p_label += " (YOU)"
                
                draw_text(surface, p_label, lx - 150, ly_row, self.font_sm, rank_color, "left")
                draw_text(surface, f"${p['net_worth']}", lx + 150, ly_row, self.font_sm, THEME_TEXT_MAIN, "right")
                ly_row += 30

            # --- COLUMN 2: PERSONAL (RIGHT) ---
            rx = box_x + (box_w * 3 // 4)
            ry = box_y + 100
            
            # Personal Session Stats
            final_profit = self.player.session_profit
            p_color = THEME_ACCENT_GREEN if final_profit >= 0 else THEME_ACCENT_RED
            
            draw_text(surface, "YOUR PERFORMANCE", rx, ry, self.font_sm, THEME_ACCENT_CYAN, "center")
            self._draw_overlay_stat(surface, rx - 100, ry + 40, "PROFIT", f"${final_profit}", p_color)
            self._draw_overlay_stat(surface, rx + 100, ry + 40, "WON", f"{self.player.items_won}", THEME_ACCENT_GOLD)
            
            # Playstyle Badge
            badge_y = ry + 120
            pygame.draw.rect(surface, (35, 40, 60), (rx - 180, badge_y, 360, 140), border_radius=15)
            
            style_name, style_desc = PlaystyleAnalyzer.analyze(self.player, self.max_rounds)
            draw_text(surface, "PLAYSTYLE", rx, badge_y + 15, self.font_sm, THEME_ACCENT_CYAN, "center")
            draw_text(surface, style_name.upper(), rx, badge_y + 45, self.font_md, THEME_ACCENT_GOLD, "center")
            
            # Description (Wrapped)
            self._draw_wrapped_text(surface, style_desc, rx, badge_y + 75, 320, self.font_sm, THEME_TEXT_MAIN)
            
            # Detailed Metrics
            metrics = PlaystyleAnalyzer.get_behavior_metrics(self.player)
            m_y = badge_y + 160
            draw_text(surface, f"Avg React: {metrics['avg_reaction']} | First: {metrics['first_bid_time']}", rx, m_y, self.font_sm, THEME_TEXT_SUB, "center")
            draw_text(surface, f"Risk: {metrics['risk']} | WD/Pass: {metrics['withdrawals']}/{metrics['passes']}", 
                      rx, m_y + 22, self.font_sm, THEME_TEXT_SUB, "center")

            draw_text(surface, "Press [SPACE] to Restart Game", cx, box_y + box_h - 35, self.font_sm, THEME_ACCENT_CYAN, "center")

    def _draw_wrapped_text(self, surface, text, x, y, max_w, font, color, align="center"):
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
        
        y_offset = 0
        line_spacing = font.get_linesize()
        for i, line in enumerate(lines):
            draw_text(surface, line, x, y + (i * line_spacing), font, color, align)
            y_offset = (i + 1) * line_spacing
            
        return y + y_offset

    def _draw_overlay_row(self, surface, cx, y, label, value, val_color):
        # Tabular alignment: labels and values both left-aligned at fixed offsets
        label_x = cx - 150
        value_x = cx + 40
        draw_text(surface, f"{label}:", label_x, y, self.font_md, THEME_TEXT_SUB, "left")
        draw_text(surface, value, value_x, y, self.font_md, val_color, "left")

    def _draw_overlay_stat(self, surface, cx, y, label, value, color):
        draw_text(surface, label, cx, y, self.font_sm, THEME_TEXT_SUB, "center")
        draw_text(surface, value, cx, y + 35, self.font_lg, color, "center")
