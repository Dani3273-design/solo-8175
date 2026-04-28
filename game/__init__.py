import pygame
import threading
import time


class SoundManager:
    def __init__(self):
        self.initialized = False
        try:
            pygame.mixer.init()
            self.initialized = True
        except:
            print("警告: 无法初始化音频系统")
    
    def play_black_stone(self):
        if not self.initialized:
            return
        try:
            frequency = 600
            duration = 100
            self._play_tone(frequency, duration)
        except:
            pass
    
    def play_white_stone(self):
        if not self.initialized:
            return
        try:
            frequency = 800
            duration = 100
            self._play_tone(frequency, duration)
        except:
            pass
    
    def _play_tone(self, frequency, duration):
        try:
            sample_rate = 44100
            import math
            n_samples = int(sample_rate * duration / 1000)
            
            import array
            buf = array.array('h', [0]) * n_samples
            max_sample = 2**15 - 1
            
            for i in range(n_samples):
                t = i / sample_rate
                value = int(max_sample * math.sin(2 * math.pi * frequency * t))
                buf[i] = value
            
            sound = pygame.mixer.Sound(buffer=buf)
            sound.set_volume(0.5)
            sound.play()
        except:
            pass
