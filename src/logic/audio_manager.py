import pygame
import os

class AudioManager:
    _instance = None
    _sounds = {}
    _enabled = True

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AudioManager, cls).__new__(cls)
            cls._instance._init_mixer()
        return cls._instance

    def _init_mixer(self):
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            self._load_sounds()
        except pygame.error as e:
            print(f"Warning: Could not initialize audio mixer: {e}")
            self._enabled = False

    def _load_sounds(self):
        if not self._enabled:
            return

        sound_names = ["click", "tick", "win", "loss", "popup", "bid"]
        base_path = "assets/sounds"

        for name in sound_names:
            # Check for .wav first (better for performance), then .mp3
            for ext in [".wav", ".mp3"]:
                path = os.path.join(base_path, f"{name}{ext}")
                if os.path.exists(path):
                    try:
                        self._sounds[name] = pygame.mixer.Sound(path)
                        break # Found one, skip to next sound name
                    except pygame.error as e:
                        print(f"Warning: Could not load sound {path}: {e}")

    def play(self, sound_name):
        if not self._enabled or sound_name not in self._sounds:
            return

        try:
            self._sounds[sound_name].play()
        except pygame.error as e:
            print(f"Warning: Could not play sound {sound_name}: {e}")

    def stop_all(self):
        if self._enabled:
            pygame.mixer.stop()
