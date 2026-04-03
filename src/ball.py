import util
import pygame
import math
class Ball(util.MyCircle):
    def __init__(self, color, width, height):
        super().__init__(color, width, height)
        self.selected = False
        self.color = color
        self.cue = None
        
    def is_clicked(self, mouse_pos):
        return self.rect.collidepoint(mouse_pos)
    
    def draw_cue(self, screen, mouse_pos):
        self.cue = pygame.draw.line(screen, util.BROWN, (self.cx, self.cy), mouse_pos, 3)
        
        #want to return length of cue so that we can convert it to a "power" value
        length = math.sqrt(self.cue.width**2 + self.cue.height**2)
        return length