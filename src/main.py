import pygame
import sys
from src.constants import *
from src.ui.screens.dashboard import MenuScreen
from src.ui.screens.gameplay import GameScreen
from src.ui.screens.highscores import HighScoreScreen
from src.ui.screens.stats import StatsScreen

class AuctionGame:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("AuctionLab v1.0")
        self.clock = pygame.time.Clock()
        self.running = True
        
        # --- Audio System ---
        from src.logic.audio_manager import AudioManager
        self.audio = AudioManager()
        
        # --- Initialize All Screens ---
        self.screens = {
            "menu": MenuScreen(),
            "game": GameScreen(),
            "scores": HighScoreScreen(),
            "stats": StatsScreen()
        }
        
        # Start at Menu
        self.current_state = "menu"

    def run(self):
        while self.running:
            # 1. Handle Input
            self._handle_events()
            
            # 2. Update Logic
            self.screens[self.current_state].update()
            
            # 3. Draw Frame
            self.screens[self.current_state].draw(self.screen)
            
            # 4. Tick Clock
            pygame.display.flip()
            self.clock.tick(FPS)
            
        pygame.quit()
        sys.exit()

    def _handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            # Pass event to current screen and get 'action' back
            action = self.screens[self.current_state].handle_events(event)
            
            if action:
                self._change_state(action)

    def _change_state(self, action):
        """Logic to switch screens based on button IDs"""
        print(f"Action received: {action}") # Debugging
        
        if action == "exit":
            self.running = False
            
        elif action == "start_game":
            self.screens["game"].reset()
            self.current_state = "game"
            
        elif action == "view_scores":
            self.current_state = "scores"
            
        elif action == "view_stats":
            self.current_state = "stats"
            
        elif action == "back":
            self.current_state = "menu"
            
        # Game Specific Actions (Placeholder logic)
        elif action == "bid":
            print("Player placed a bid!")
        elif action == "withdraw":
            print("Player withdrew!")

if __name__ == "__main__":
    game = AuctionGame()
    game.run()