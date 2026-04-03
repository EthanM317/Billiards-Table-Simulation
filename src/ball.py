import util
import pygame
class Ball(util.MyCircle):
    def __init__(self, color, width, height):
        super().__init__(color, width, height)
        self.selected = False
        self.color = color
        self.cue = pygame
        
    def is_clicked(self, mouse_pos):
        return self.rect.collidepoint(mouse_pos)
    
    def draw_cue(self, screen, mouse_pos):
        pygame.draw.line(screen, util.BROWN, (self.cx, self.cy), mouse_pos, 3)
