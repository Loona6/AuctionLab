import pygame
import os
import statistics
from src.constants import *
from src.ui.components import NeonButton, draw_text
from src.models.auction import Auction
from src.models.ai_agent import AIAgent

# --- Theme Colors ---
THEME_BG = (15, 17, 28)
THEME_PANEL_BG = (28, 30, 45)
THEME_BORDER = (50, 55, 75)
THEME_ACCENT_GREEN = (46, 204, 113)
THEME_ACCENT_RED = (231, 76, 60)
THEME_ACCENT_CYAN = (0, 255, 255)
THEME_ACCENT_GOLD = (255, 215, 0)
THEME_TEXT_MAIN = (236, 240, 241)
THEME_TEXT_SUB = (149, 165, 166)

class SimScreen:
    def __init__(self):
        self.font_xl = pygame.font.SysFont(FONT_NAME, 48, bold=True)
        self.font_lg = pygame.font.SysFont(FONT_NAME, 32, bold=True)
        self.font_md = pygame.font.SysFont(FONT_NAME, 24)
        self.font_sm = pygame.font.SysFont(FONT_NAME, 18)
        self.font_xs = pygame.font.SysFont(FONT_NAME, 14)
        
        # --- Layout ---
        self.pad = 20
        self.col1_w = int((SCREEN_WIDTH - (self.pad * 4)) * 0.25)
        self.col2_w = int((SCREEN_WIDTH - (self.pad * 4)) * 0.50)
        self.col3_w = int((SCREEN_WIDTH - (self.pad * 4)) * 0.25)
        self.panel_h = SCREEN_HEIGHT - 140 
        self.start_y = 90
        
        self.auction = Auction()
        self.round_num = 1
        self.max_rounds = 5
        self.is_paused = False
        self.sim_speed = 1.0
        self.speeds = [1.0, 2.0, 4.0]
        self.speed_idx = 0
        self.last_tick_time = pygame.time.get_ticks()
        
        # UI
        self.btn_exit = NeonButton(20, 20, 100, 40, "EXIT", THEME_BORDER, "back")
        self.btn_pause = NeonButton(SCREEN_WIDTH - 130, 20, 110, 40, "PAUSE", THEME_ACCENT_CYAN, "pause")
        self.btn_speed = NeonButton(SCREEN_WIDTH - 280, 20, 140, 40, "SPEED: 1x", THEME_BORDER, "cycle_speed")
        
        self.price_history = [] 
        self._item_sprite_cache = {}
        self.session_data = [] 
        self.show_final_report = False
        self.show_exit_confirm = False
        
        # Exit Confirmation Buttons
        bw, bh = 120, 40
        self.btn_yes = NeonButton(SCREEN_WIDTH//2 - 130, SCREEN_HEIGHT//2 + 20, bw, bh, "YES, EXIT", THEME_ACCENT_RED, "exit_confirm")
        self.btn_no = NeonButton(SCREEN_WIDTH//2 + 10, SCREEN_HEIGHT//2 + 20, bw, bh, "NO, STAY", THEME_ACCENT_GREEN, "exit_cancel")

    def setup_simulation(self, bot_count, strategies):
        self.auction = Auction()
        self.auction.agents = []
        for i in range(bot_count):
            agent = AIAgent(f"BOT-{i+1}", 500, strategy_type=strategies[i])
            self.auction.agents.append(agent)
        
        self.round_num = 1
        self.auction.start_round(self.round_num)
        self.is_paused = False
        self.price_history = [0]
        self.sim_speed = 1.0
        self.speed_idx = 0
        self.btn_speed.text = "SPEED: 1x"
        self.session_data = []
        self.show_final_report = False
        self.show_exit_confirm = False

    def handle_events(self, event):
        if self.show_exit_confirm:
            if self.btn_yes.is_clicked(event): return "back"
            if self.btn_no.is_clicked(event): self.show_exit_confirm = False
            return None

        if self.btn_exit.is_clicked(event):
            self.show_exit_confirm = True
            return None
        
        if self.btn_pause.is_clicked(event):
            self.is_paused = not self.is_paused
            self.btn_pause.text = "RESUME" if self.is_paused else "PAUSE"
            self.btn_pause.base_color = THEME_ACCENT_GREEN if self.is_paused else THEME_ACCENT_CYAN
            
        if self.btn_speed.is_clicked(event):
            self.speed_idx = (self.speed_idx + 1) % len(self.speeds)
            self.sim_speed = self.speeds[self.speed_idx]
            self.btn_speed.text = f"SPEED: {int(self.sim_speed)}x"

        if not self.auction.is_active:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                if self.round_num < self.max_rounds:
                    self._capture_round_data()
                    self.round_num += 1
                    self.auction.start_round(self.round_num)
                    self.price_history = [0]
                else:
                    self._capture_round_data()
                    self.show_final_report = True
            if self.show_final_report and event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return "back"
        return None

    def _capture_round_data(self):
        if len(self.session_data) >= self.round_num: return
        item = self.auction.current_item
        winner = self.auction.highest_bidder
        true_val = item.get_true_value()
        final_price = self.auction.highest_bid
        
        # Calculate Deal Quality
        profit = true_val - final_price
        if final_price == 0: quality = "Unsold"
        elif profit > true_val * 0.2: quality = "Good"
        elif profit >= 0: quality = "Fair"
        else: quality = "Overpaid"

        data = {
            'round': self.round_num,
            'true_value': true_val,
            'final_price': final_price,
            'winner_id': winner.id if (winner and not winner.id.startswith("None")) else "None",
            'winner_strat': winner.strategy if (winner and not winner.id.startswith("None")) else "None",
            'quality': quality,
            'bid_count': len(self.auction.bid_stack)
        }
        self.session_data.append(data)

    def update(self):
        mouse_pos = pygame.mouse.get_pos()
        self.btn_exit.update(mouse_pos)
        self.btn_pause.update(mouse_pos)
        self.btn_speed.update(mouse_pos)
        
        if self.show_exit_confirm:
            self.btn_yes.update(mouse_pos)
            self.btn_no.update(mouse_pos)
            return

        if self.is_paused or self.show_final_report: return
        
        interval = 200 / self.sim_speed
        now = pygame.time.get_ticks()
        if now - self.last_tick_time >= interval:
            self.auction.run_tick()
            self.last_tick_time = now
            if self.auction.is_active:
                self.price_history.append(self.auction.highest_bid)

    def draw(self, surface):
        surface.fill(THEME_BG)
        self._draw_top_bar(surface)
        
        x_cursor = self.pad
        y_panels = self.start_y
        
        self._draw_panel(surface, x_cursor, y_panels, self.col1_w, self.panel_h)
        self._draw_left_content(surface, x_cursor, y_panels, self.col1_w)
        
        x_cursor += self.col1_w + self.pad
        self._draw_panel(surface, x_cursor, y_panels, self.col2_w, self.panel_h)
        self._draw_center_content(surface, x_cursor, y_panels, self.col2_w)
        self._draw_auctioneer_callout(surface, x_cursor, y_panels, self.col2_w)
        
        x_cursor += self.col2_w + self.pad
        self._draw_panel(surface, x_cursor, y_panels, self.col3_w, self.panel_h)
        self._draw_right_content(surface, x_cursor, y_panels, self.col3_w)
        
        if not self.auction.is_active:
            if self.show_final_report:
                self._draw_final_report_overlay(surface)
            else:
                self._draw_round_end_overlay(surface)
        
        if self.show_exit_confirm:
            self._draw_exit_confirm_overlay(surface)

    def _draw_exit_confirm_overlay(self, surface):
        s = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        s.set_alpha(200)
        s.fill((10, 12, 20))
        surface.blit(s, (0,0))
        
        cx, cy = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2
        box_w, box_h = 400, 180
        rect = pygame.Rect(cx - box_w//2, cy - box_h//2, box_w, box_h)
        pygame.draw.rect(surface, THEME_PANEL_BG, rect, border_radius=15)
        pygame.draw.rect(surface, THEME_ACCENT_RED, rect, 2, border_radius=15)
        
        draw_text(surface, "EXIT AUCTION LAB?", cx, rect.top + 35, self.font_md, THEME_ACCENT_RED, "center")
        draw_text(surface, "All current experiment data will be lost.", cx, rect.top + 65, self.font_xs, THEME_TEXT_SUB, "center")
        
        self.btn_yes.draw(surface, self.font_sm)
        self.btn_no.draw(surface, self.font_sm)

    def _draw_top_bar(self, surface):
        info_text = f"SIMULATION EXPERIMENT | ROUND {self.round_num} / {self.max_rounds}"
        draw_text(surface, info_text, SCREEN_WIDTH // 2, 40, self.font_md, THEME_ACCENT_CYAN, "center")
        self.btn_exit.draw(surface, self.font_sm)
        self.btn_pause.draw(surface, self.font_sm)
        self.btn_speed.base_color = THEME_ACCENT_GOLD
        self.btn_speed.draw(surface, self.font_sm)

    def _draw_panel(self, surface, x, y, w, h):
        rect = pygame.Rect(x, y, w, h)
        pygame.draw.rect(surface, THEME_PANEL_BG, rect, border_radius=12)
        pygame.draw.rect(surface, THEME_BORDER, rect, 1, border_radius=12)

    def _draw_left_content(self, surface, x, y, w):
        cx = x + w // 2
        item = self.auction.current_item
        draw_text(surface, "ACTIVE AUCTION ITEM", cx, y + 30, self.font_md, THEME_ACCENT_CYAN, "center")
        img_rect = pygame.Rect(x + 30, y + 70, w - 60, w - 60)
        pygame.draw.rect(surface, (15, 17, 25), img_rect, border_radius=8)
        pygame.draw.rect(surface, THEME_BORDER, img_rect, 1, border_radius=8)
        sprite = self._resolve_item_sprite(item, img_rect.size)
        if sprite: surface.blit(sprite, img_rect.topleft)
        name_y = img_rect.bottom + 20
        desc_y = self._draw_wrapped_text(surface, item.name, cx, name_y, w - 40, self.font_lg, THEME_TEXT_MAIN)
        hint_y = self._draw_wrapped_text(surface, item.description, cx, desc_y + 5, w - 50, self.font_sm, THEME_TEXT_SUB)
        self._draw_wrapped_text(surface, f"\"{item.get_hint()}\"", cx, hint_y + 15, w - 40, self.font_md, THEME_ACCENT_GOLD)

    def _draw_center_content(self, surface, x, y, w):
        cx = x + w // 2
        draw_text(surface, "SIMULATION FLOOR", cx, y + 25, self.font_md, THEME_ACCENT_CYAN, "center")
        h_y = y + 60
        draw_text(surface, "PARTICIPANT", x + 40, h_y, self.font_sm, THEME_TEXT_SUB, "left")
        draw_text(surface, "STRATEGY", x + 190, h_y, self.font_sm, THEME_TEXT_SUB, "left")
        draw_text(surface, "VALUATION", x + 340, h_y, self.font_sm, THEME_TEXT_SUB, "left") 
        draw_text(surface, "BID", x + w - 40, h_y, self.font_sm, THEME_TEXT_SUB, "right")
        pygame.draw.line(surface, THEME_BORDER, (x+40, h_y + 22), (x+w-40, h_y + 22), 1)
        row_y = h_y + 35
        for agent in self.auction.agents:
            is_winning = self.auction.highest_bidder and self.auction.highest_bidder.id == agent.id
            color = THEME_ACCENT_GOLD if is_winning else THEME_TEXT_MAIN
            p_bid = next((bid for bidder, bid in reversed(self.auction.bid_stack) if bidder.id == agent.id), 0)
            draw_text(surface, agent.id, x + 40, row_y, self.font_sm, color, "left")
            draw_text(surface, agent.strategy, x + 190, row_y, self.font_sm, THEME_TEXT_MAIN, "left")
            draw_text(surface, f"${agent.estimated_value}", x + 340, row_y, self.font_sm, THEME_TEXT_SUB, "left")
            draw_text(surface, f"${p_bid}" if p_bid else "-", x + w - 40, row_y, self.font_sm, color, "right")
            row_y += 30

        data_y = row_y + 15
        pygame.draw.line(surface, THEME_BORDER, (x+40, data_y), (x+w-40, data_y), 1)
        
        # Recalculated Layout for symmetric margins
        margin = 35
        spacing = 25
        avail_w = w - (margin * 2) - spacing
        chart_w = int(avail_w * 0.48)
        log_w = avail_w - chart_w
        
        draw_text(surface, "PRICE MOMENTUM", x + margin, data_y + 15, self.font_sm, THEME_TEXT_SUB, "left")
        chart_box = pygame.Rect(x + margin, data_y + 40, chart_w, self.panel_h - (data_y - y + 55))
        pygame.draw.rect(surface, (15, 17, 25), chart_box, border_radius=10)
        pygame.draw.line(surface, (40, 45, 60), (chart_box.x, chart_box.bottom - 20), (chart_box.right, chart_box.bottom - 20), 1)
        
        true_val = self.auction.current_item.get_true_value()
        if len(self.price_history) > 1:
            max_p = max(max(self.price_history), true_val) * 1.1
            ty = chart_box.bottom - (true_val / max_p) * chart_box.height
            if ty > chart_box.top:
                pygame.draw.line(surface, THEME_ACCENT_GOLD, (chart_box.x, ty), (chart_box.right, ty), 1)
                draw_text(surface, "TRUE VALUE", chart_box.right - 5, ty - 12, self.font_xs, THEME_ACCENT_GOLD, "right")
            pts = []
            for i, p in enumerate(self.price_history):
                px = chart_box.x + (i / max(1, len(self.price_history)-1)) * chart_box.width
                py = chart_box.bottom - (p / max_p) * chart_box.height
                pts.append((px, py))
            if len(pts) > 1: pygame.draw.lines(surface, THEME_ACCENT_CYAN, False, pts, 2)

        log_x = chart_box.right + spacing
        draw_text(surface, "LIVE FEED", log_x + 10, data_y + 15, self.font_sm, THEME_TEXT_SUB, "left")
        log_box = pygame.Rect(log_x, data_y + 40, log_w, chart_box.height)
        pygame.draw.rect(surface, (15, 17, 25), log_box, border_radius=10)
        curr_y = data_y + 50
        for log in self.auction.get_recent_logs():
            if "Going once" in log or "Going twice" in log: continue
            text_color = THEME_ACCENT_GOLD if "sold" in log.lower() else THEME_TEXT_MAIN
            if curr_y + 15 > log_box.bottom: break
            clean_log = log.replace("--- ", "").replace(" ---", "")
            curr_y = self._draw_wrapped_text(surface, clean_log, log_x + 10, curr_y, log_w - 20, self.font_xs, text_color, "left")
            curr_y += 6

    def _draw_auctioneer_callout(self, surface, x, y, w):
        state = self.auction.auction_state
        if state not in ["Going Once", "Going Twice", "Active"] and self.auction.is_active: return
        cx, cy = x + w // 2, y + self.panel_h // 2 + 70
        if state == "Going Once": text, color = "GOING ONCE!", (255, 255, 0)
        elif state == "Going Twice": text, color = "GOING TWICE!!", (255, 140, 0)
        elif not self.auction.is_active and self.auction.highest_bidder: text, color = "SOLD!!!", THEME_ACCENT_RED
        else: return
        draw_text(surface, text, cx, cy, self.font_xl, color, "center")

    def _draw_right_content(self, surface, x, y, w):
        cx = x + w // 2
        draw_text(surface, "FINANCIAL ANALYTICS", cx, y + 30, self.font_md, THEME_ACCENT_CYAN, "center")
        mid_y = y + 100
        draw_text(surface, "CURRENT PRICE", cx, mid_y - 15, self.font_sm, THEME_TEXT_SUB, "center")
        draw_text(surface, f"${self.auction.highest_bid}", cx, mid_y + 30, self.font_xl, THEME_TEXT_MAIN, "center")
        timer_w = w - 100; timer_x = x + 50; timer_y = mid_y + 70
        pygame.draw.rect(surface, (15, 17, 25), (timer_x, timer_y, timer_w, 8), border_radius=4)
        ratio = max(0, self.auction.current_patience / self.auction.base_patience)
        bar_w = int(timer_w * ratio)
        t_color = THEME_ACCENT_GREEN if ratio > 0.5 else (THEME_ACCENT_GOLD if ratio > 0.2 else THEME_ACCENT_RED)
        if bar_w > 0: pygame.draw.rect(surface, t_color, (timer_x, timer_y, bar_w, 8), border_radius=4)
        draw_text(surface, f"{max(0, self.auction.current_patience/5.0):.1f}s", x + w - 40, timer_y + 4, self.font_xs, t_color, "midright")
        stand_y = mid_y + 110; pygame.draw.line(surface, THEME_BORDER, (x+30, stand_y), (x+w-30, stand_y), 1)
        draw_text(surface, "RANKINGS (NET WORTH)", x+40, stand_y + 15, self.font_sm, THEME_TEXT_SUB, "left")
        standings = sorted([{'id': a.id, 'net': a.budget + a.items_value_won} for a in self.auction.agents], key=lambda x: x['net'], reverse=True)
        for i, s in enumerate(standings[:5]):
            draw_text(surface, f"{i+1}. {s['id']}", x+40, stand_y + 45 + (i*30), self.font_sm, THEME_ACCENT_GOLD if i == 0 else THEME_TEXT_MAIN, "left")
            draw_text(surface, f"${s['net']}", x + w - 40, stand_y + 45 + (i*30), self.font_sm, THEME_TEXT_MAIN, "right")
        pot_y = stand_y + 210; pygame.draw.line(surface, THEME_BORDER, (x+30, pot_y), (x+w-30, pot_y), 1)
        draw_text(surface, "RISK ASSESSMENT", x+40, pot_y + 15, self.font_sm, THEME_TEXT_SUB, "left")
        item = self.auction.current_item; true_val = item.get_true_value(); profit = true_val - self.auction.highest_bid
        if self.auction.highest_bid == 0: cond, r_color = "WAITING...", THEME_TEXT_SUB
        elif profit > true_val * 0.2: cond, r_color = "GOOD DEAL", THEME_ACCENT_GREEN
        elif profit >= 0: cond, r_color = "FAIR DEAL", THEME_ACCENT_GOLD
        else: cond, r_color = "BAD DEAL (OVERPAY)", THEME_ACCENT_RED
        sy = pot_y + 45
        draw_text(surface, f"Target Value: ${true_val}", x+50, sy, self.font_sm, THEME_TEXT_MAIN, "left")
        draw_text(surface, f"Profit Room: ${max(0, profit)}", x+50, sy + 25, self.font_sm, THEME_ACCENT_CYAN, "left")
        draw_text(surface, f"Condition: {cond}", x+50, sy + 50, self.font_sm, r_color, "left")

    def _draw_round_end_overlay(self, surface):
        s = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT)); s.set_alpha(220); s.fill((10, 12, 20)); surface.blit(s, (0,0))
        cx, cy = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2; winner = self.auction.highest_bidder; is_sold = winner is not None and not winner.id.startswith("None")
        box_w, box_h = 450, 350; rect = pygame.Rect(cx-box_w//2, cy-box_h//2, box_w, box_h)
        pygame.draw.rect(surface, THEME_PANEL_BG, rect, border_radius=20); pygame.draw.rect(surface, THEME_ACCENT_GOLD if is_sold else THEME_TEXT_SUB, rect, 2, border_radius=20)
        draw_text(surface, "SOLD!" if is_sold else "PASSED", cx, rect.top + 35, self.font_xl, THEME_ACCENT_GOLD if is_sold else THEME_ACCENT_RED, "center")
        item = self.auction.current_item
        draw_text(surface, item.name, cx, rect.top + 85, self.font_md, THEME_TEXT_MAIN, "center")
        pygame.draw.line(surface, THEME_BORDER, (cx - 150, rect.top + 115), (cx + 150, rect.top + 115), 1)
        if is_sold:
            val = item.get_true_value(); profit = val - self.auction.highest_bid
            row_y = rect.top + 140
            self._draw_overlay_row(surface, cx, row_y, "Winner", winner.id, THEME_TEXT_MAIN)
            self._draw_overlay_row(surface, cx, row_y + 35, "Price", f"${self.auction.highest_bid}", THEME_TEXT_SUB)
            self._draw_overlay_row(surface, cx, row_y + 70, "Value", f"${val}", THEME_ACCENT_GOLD)
            p_text, p_color = (f"PROFIT: ${profit}", THEME_ACCENT_GREEN) if profit >= 0 else (f"LOSS: ${abs(profit)}", THEME_ACCENT_RED)
            draw_text(surface, p_text, cx, rect.bottom - 70, self.font_lg, p_color, "center")
        else: draw_text(surface, "Item went unsold.", cx, cy, self.font_md, THEME_TEXT_SUB, "center")
        msg = "Press [SPACE] for Final Report" if self.round_num == self.max_rounds else "Press [SPACE] to Continue"
        draw_text(surface, msg, cx, rect.bottom - 35, self.font_sm, THEME_ACCENT_CYAN, "center")

    def _draw_final_report_overlay(self, surface):
        s = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT)); s.set_alpha(252); s.fill((10, 12, 20)); surface.blit(s, (0,0))
        
        # --- DATA PREP ---
        total_bots = len(self.auction.agents)
        strats = [a.strategy for a in self.auction.agents]
        prices = [d['final_price'] for d in self.session_data]; values = [d['true_value'] for d in self.session_data]
        avg_ratio = statistics.mean([p/v for p, v in zip(prices, values)]) if values else 1
        m_type = "HOT" if avg_ratio > 1.1 else ("COLD" if avg_ratio < 0.9 else "BALANCED")
        avg_bids = statistics.mean([d['bid_count'] for d in self.session_data]) if self.session_data else 0
        comp_level = "HIGH" if avg_bids > 15 else ("MEDIUM" if avg_bids > 8 else "LOW")
        
        # --- TOP HEADER ---
        draw_text(surface, "AUCTION LAB: FINAL EXPERIMENT ANALYTICS", SCREEN_WIDTH // 2, 40, self.font_xl, THEME_ACCENT_CYAN, "center")
        header_sub = f"MARKET: {m_type} | COMPETITION: {comp_level} | ROUNDS: {len(self.session_data)}"
        draw_text(surface, header_sub, SCREEN_WIDTH // 2, 85, self.font_sm, THEME_TEXT_SUB, "center")

        # --- GRID LAYOUT (3 columns x 2 rows) ---
        m = 30; sp = 30
        bw = (SCREEN_WIDTH - (m*2) - (sp*2)) // 3
        bh = 220
        row1_y = 160 # Brought down
        row2_y = row1_y + bh + sp
        
        # 1. FINAL RANKINGS
        self._draw_report_box(surface, m, row1_y, bw, bh, "FINAL RANKINGS", THEME_ACCENT_GOLD)
        sorted_agents = sorted(self.auction.agents, key=lambda a: a.budget + a.items_value_won, reverse=True)
        for i, a in enumerate(sorted_agents[:3]):
            ry = row1_y + 70 + (i * 48)
            color = THEME_ACCENT_GOLD if i == 0 else THEME_TEXT_MAIN
            draw_text(surface, f"RANK {i+1}", m + 30, ry, self.font_xs, THEME_ACCENT_GOLD if i==0 else THEME_TEXT_SUB, "left")
            draw_text(surface, a.id, m + 90, ry, self.font_sm, color, "left")
            draw_text(surface, f"${a.budget + a.items_value_won}", m + bw - 30, ry, self.font_sm, THEME_ACCENT_GREEN, "right")

        # 2. STRATEGY PERFORMANCE
        self._draw_report_box(surface, m + bw + sp, row1_y, bw, bh, "STRATEGY ANALYSIS", THEME_ACCENT_CYAN)
        stats = {s: {'wins': 0, 'profit': 0, 'count': strats.count(s)} for s in ['Aggressive', 'Balanced', 'Conservative']}
        for d in self.session_data:
            if d['winner_strat'] in stats:
                stats[d['winner_strat']]['wins'] += 1
                stats[d['winner_strat']]['profit'] += (d['true_value'] - d['final_price'])
        
        sy = row1_y + 70
        for s, data in stats.items():
            if data['count'] == 0: continue
            color = THEME_ACCENT_RED if s == 'Aggressive' else (THEME_ACCENT_GREEN if s == 'Balanced' else THEME_ACCENT_GOLD)
            draw_text(surface, s, m + bw + sp + 30, sy, self.font_sm, color, "left")
            draw_text(surface, f"{data['wins']} Wins", m + bw + sp + 150, sy, self.font_sm, THEME_TEXT_MAIN, "left")
            draw_text(surface, f"Prof: ${data['profit']}", m + bw + sp + bw - 30, sy, self.font_sm, THEME_TEXT_SUB, "right")
            sy += 48

        # 3. MARKET BEHAVIOR
        self._draw_report_box(surface, m + (bw+sp)*2, row1_y, bw, bh, "MARKET BEHAVIOR", THEME_BORDER)
        overbid_count = sum(1 for d in self.session_data if d['quality'] == "Overpaid")
        volatility = statistics.stdev(prices) if len(prices) > 1 else 0
        my = row1_y + 70
        draw_text(surface, "Volatility:", m + (bw+sp)*2 + 30, my, self.font_sm, THEME_TEXT_SUB, "left")
        draw_text(surface, f"${volatility:.1f}", m + (bw+sp)*2 + bw - 30, my, self.font_sm, THEME_TEXT_MAIN, "right")
        draw_text(surface, "Overbid Freq:", m + (bw+sp)*2 + 30, my + 45, self.font_sm, THEME_TEXT_SUB, "left")
        draw_text(surface, f"{overbid_count/len(self.session_data)*100:.0f}%", m + (bw+sp)*2 + bw - 30, my + 45, self.font_sm, THEME_ACCENT_RED, "right")
        draw_text(surface, "Avg. Bidding:", m + (bw+sp)*2 + 30, my + 90, self.font_sm, THEME_TEXT_SUB, "left")
        draw_text(surface, f"{int(avg_bids)} Bids/Round", m + (bw+sp)*2 + bw - 30, my + 90, self.font_sm, THEME_TEXT_MAIN, "right")

        # 4. DEAL QUALITY DISTRIBUTION
        self._draw_report_box(surface, m, row2_y, bw, bh - 30, "DEAL QUALITY", THEME_BORDER)
        q_stats = {'Good': 0, 'Fair': 0, 'Overpaid': 0, 'Unsold': 0}
        for d in self.session_data: q_stats[d['quality']] += 1
        
        qy = row2_y + 70
        for q, count in q_stats.items():
            color = THEME_ACCENT_GREEN if q == "Good" else (THEME_ACCENT_GOLD if q == "Fair" else (THEME_ACCENT_RED if q == "Overpaid" else THEME_TEXT_SUB))
            draw_text(surface, q, m + 30, qy + 1, self.font_xs, color, "midleft")
            bar_max = bw - 140
            pygame.draw.rect(surface, (25, 27, 40), (m + 100, qy - 4, bar_max, 10), border_radius=5)
            bar_w = int((count / len(self.session_data)) * bar_max)
            if bar_w > 0: pygame.draw.rect(surface, color, (m + 100, qy - 4, bar_w, 10), border_radius=5)
            draw_text(surface, f"{count}", m + bw - 30, qy + 1, self.font_xs, THEME_TEXT_SUB, "midright")
            qy += 35

        # 5. PROFIT & EFFICIENCY
        self._draw_report_box(surface, m + bw + sp, row2_y, bw, bh - 30, "EFFICIENCY ANALYSIS", THEME_BORDER)
        total_p = sum(d['true_value'] - d['final_price'] for d in self.session_data if d['final_price'] > 0)
        draw_text(surface, "System Profit:", m + bw + sp + 30, row2_y + 70, self.font_sm, THEME_TEXT_SUB, "midleft")
        draw_text(surface, f"${total_p}", m + bw + sp + bw - 30, row2_y + 70, self.font_sm, THEME_ACCENT_GREEN, "midright")
        
        best_bot = None; best_eff = -999
        for a in self.auction.agents:
            if a.session_spent > 0:
                eff = (a.items_value_won - a.session_spent) / a.session_spent
                if eff > best_eff: best_eff = eff; best_bot = a
        if best_bot:
            draw_text(surface, "Most Efficient Bot:", m + bw + sp + 30, row2_y + 115, self.font_xs, THEME_TEXT_SUB, "midleft")
            draw_text(surface, f"{best_bot.id} ({best_eff*100:.0f}% ROI)", m + bw + sp + bw - 30, row2_y + 115, self.font_sm, THEME_ACCENT_CYAN, "midright")

        # 6. EXECUTIVE RESEARCH SUMMARY
        self._draw_report_box(surface, m + (bw+sp)*2, row2_y, bw, bh - 30, "EXECUTIVE SUMMARY", THEME_ACCENT_GREEN)
        
        # Sophisticated Summary Logic
        winner_strat = sorted(stats.items(), key=lambda x: x[1]['wins'], reverse=True)[0][0]
        efficiency_msg = "Market efficiency was optimal with minimal overbidding." if overbid_count == 0 else f"Bidding wars led to overpayment in {overbid_count} rounds."
        temp_msg = "Aggressive agents successfully inflated prices" if m_type == "HOT" else "Conservative agents exploited low competition"
        
        summary = (
            f"This {m_type.lower()} session was defined by {comp_level.lower()} competition levels. "
            f"{winner_strat} agents dominated the simulation by securing {stats[winner_strat]['wins']} wins. "
            f"{efficiency_msg} Overall, {temp_msg}, proving that the current environment favored "
            f"{'patience' if winner_strat == 'Conservative' else 'aggression'} as a survival trait."
        )
        
        # Highlighting summary box inner
        sum_rect = pygame.Rect(m + (bw+sp)*2 + 15, row2_y + 55, bw - 30, bh - 100)
        pygame.draw.rect(surface, (20, 22, 35), sum_rect, border_radius=10)
        self._draw_wrapped_text(surface, summary, m + (bw+sp)*2 + 30, row2_y + 70, bw - 60, self.font_xs, THEME_TEXT_MAIN, "justify")

        # Sleek Exit Prompt (Vibe Fix)
        prompt_w, prompt_h = 420, 40
        px, py = SCREEN_WIDTH // 2 - prompt_w // 2, SCREEN_HEIGHT - 65
        pygame.draw.rect(surface, (10, 12, 20), (px, py, prompt_w, prompt_h), border_radius=20)
        pygame.draw.rect(surface, THEME_ACCENT_CYAN, (px, py, prompt_w, prompt_h), 1, border_radius=20)
        draw_text(surface, "Experiment Concluded. Press [ESC] to exit Auction Lab.", SCREEN_WIDTH // 2, py + 20, self.font_sm, THEME_TEXT_MAIN, "center")

    def _draw_report_box(self, surface, x, y, w, h, title, accent_color):
        rect = pygame.Rect(x, y, w, h)
        pygame.draw.rect(surface, THEME_PANEL_BG, rect, border_radius=12)
        pygame.draw.rect(surface, THEME_BORDER, rect, 1, border_radius=12)
        # Title with accent bar
        pygame.draw.rect(surface, accent_color, (x + 20, y + 18, 4, 22), border_radius=2)
        draw_text(surface, title, x + 35, y + 29, self.font_sm, THEME_ACCENT_CYAN, "midleft")
        pygame.draw.line(surface, THEME_BORDER, (x + 20, y + 48), (x + w - 20, y + 48), 1)

    def _draw_overlay_row(self, surface, cx, y, label, value, val_color):
        draw_text(surface, f"{label}:", cx - 140, y, self.font_md, THEME_TEXT_SUB, "left"); draw_text(surface, value, cx + 40, y, self.font_md, val_color, "left")

    def _draw_wrapped_text(self, surface, text, x, y, max_w, font, color, align="center"):
        words = text.split(); lines = []; curr = []
        for w in words:
            if font.size(" ".join(curr + [w]))[0] < max_w: curr.append(w)
            else: lines.append(curr); curr = [w]
        lines.append(curr) # Last line
        
        h = font.get_linesize()
        for i, line_words in enumerate(lines):
            line_str = " ".join(line_words)
            if align == "justify" and i < len(lines) - 1 and len(line_words) > 1:
                # Calculate spacing
                total_w = sum(font.size(w)[0] for w in line_words)
                num_gaps = len(line_words) - 1
                gap_w = (max_w - total_w) / num_gaps
                
                curr_x = x
                for j, w in enumerate(line_words):
                    surface.blit(font.render(w, True, color), (curr_x, y + (i * h)))
                    curr_x += font.size(w)[0] + gap_w
            else:
                draw_text(surface, line_str, x, y + (i * h), font, color, "left" if align == "justify" else align)
        return y + (len(lines) * h)

    def _resolve_item_sprite(self, item, size):
        sprite_path = item.get_sprite_path()
        if sprite_path:
            if sprite_path not in self._item_sprite_cache:
                try:
                    img = pygame.image.load(sprite_path).convert_alpha()
                    img = pygame.transform.smoothscale(img, size)
                    self._item_sprite_cache[sprite_path] = img
                except: self._item_sprite_cache[sprite_path] = None
            return self._item_sprite_cache.get(sprite_path)
        return None
