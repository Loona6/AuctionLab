import pygame
from src.constants import *

def draw_text(surface, text, x, y, font, color, align="topleft"):
    text_surface = font.render(str(text), True, color)
    text_rect = text_surface.get_rect()
    
    if align == "topleft":
        text_rect.topleft = (x, y)
    elif align == "center":
        text_rect.center = (x, y)
    elif align == "right":
        text_rect.topright = (x, y)
    elif align == "left":
        text_rect.topleft = (x, y)
        
    surface.blit(text_surface, text_rect)
    return text_rect

class NeonButton:
    def __init__(self, x, y, w, h, text, color, action_code):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.base_color = color
        self.action_code = action_code
        self.is_hovered = False

    def update(self, mouse_pos):
        self.is_hovered = self.rect.collidepoint(mouse_pos)

    def draw(self, surface, font):
        # Determine Color (Brighter if hovered)
        color = self.base_color
        if self.is_hovered:
            # Simple brighten effect: cap at 255
            color = [min(c + 40, 255) for c in self.base_color]
        
        # Draw Glow (Outer Border)
        pygame.draw.rect(surface, color, self.rect, border_radius=8, width=2)
        
        # Draw Fill (Low opacity if hovered, else transparent)
        if self.is_hovered:
            s = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
            s.fill((*color[:3], 30)) # Low alpha
            surface.blit(s, self.rect.topleft)

        # Draw Text
        text_surf = font.render(self.text, True, color)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)

    def is_clicked(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.is_hovered:
                from src.logic.audio_manager import AudioManager
                AudioManager().play("click")
                return True
        return False

class NeonInputBox:
    def __init__(self, x, y, w, h, initial_text, font, color_active, color_passive):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = str(initial_text)
        self.font = font
        self.color_active = color_active
        self.color_passive = color_passive
        self.active = False
        self.color = self.color_passive

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            # Toggle active if clicked inside
            if self.rect.collidepoint(event.pos):
                self.active = not self.active
            else:
                self.active = False
            self.color = self.color_active if self.active else self.color_passive
            
        if event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_RETURN:
                return "submit" # Signal to submit
            elif event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            else:
                # Only allow numbers
                if event.unicode.isdigit():
                    self.text += event.unicode
        return None

    def set_text(self, text):
        self.text = str(text)

    def get_value(self):
        try:
            return int(self.text) if self.text else 0
        except ValueError:
            return 0

    def draw(self, surface):
        # Draw Background
        pygame.draw.rect(surface, (25, 28, 40), self.rect, border_radius=8)
        # Draw Border (Glow if active)
        pygame.draw.rect(surface, self.color, self.rect, 2, border_radius=8)
        
        # Render Text
        text_surface = self.font.render(f"$ {self.text}", True, (255, 255, 255))
        
        # Center text vertically
        text_rect = text_surface.get_rect(midleft=(self.rect.x + 15, self.rect.centery))
        surface.blit(text_surface, text_rect)