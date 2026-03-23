"""
author: Faisal Z. Qureshi
email: faisal.qureshi@uoit.ca
website: http://www.vclab.ca
license: BSD
"""
#This code is used to speed up and simplify pygame asset creation
import pygame

# set up the colors
BLACK = (0, 0, 0, 255)
WHITE = (255, 255, 255, 0)
RED = (255, 0, 0, 255)
GREEN = (0, 255, 0, 255)
BLUE = (0, 0, 255, 255)

def load_image(name):
    image = pygame.image.load(name)
    return image

class MyCircle(pygame.sprite.Sprite):
    def __init__(self, color, width, height, alpha=255):
        pygame.sprite.Sprite.__init__(self)

        self.image = pygame.Surface([width, height], flags=pygame.SRCALPHA)
        self.rect = self.image.get_rect()
        cx = self.rect.centerx
        cy = self.rect.centery
        pygame.draw.circle(self.image, color, (width/2, height/2), cx, cy)
#        self.rect = self.image.get_rect()

        self.picked = False

    def set_pos(self, pos):
        self.rect.x = pos[0] - self.rect.width//2
        self.rect.y = pos[1] - self.rect.height//2

    def update(self):
        pass

class MyRect(pygame.sprite.Sprite):
    def __init__(self, color, width, height, alpha=255):
        pygame.sprite.Sprite.__init__(self)

        self.image = pygame.Surface([width, height], flags=pygame.SRCALPHA)
        self.rect = self.image.get_rect()
        pygame.draw.rect(self.image, color, self.rect)

        self.picked = False

    def set_pos(self, pos):
        self.rect.x = pos[0] - self.rect.width//2
        self.rect.y = pos[1] - self.rect.height//2
    def getX(self):
        return self.rect.x
    def getY(self):
        return self.rect.y
    def update(self):
        pass

def to_screen(x, y, win_width, win_height):
    return win_width//2 + x, win_height//2 - y

def from_screen(x, y, win_width, win_height):
    return x - win_width//2, win_height//2 - y

class MyText():
    def __init__(self, color, background=WHITE, antialias=True, fontname="comicsansms", fontsize=16):
        pygame.font.init()
        self.font = pygame.font.SysFont(fontname, fontsize)
        self.color = color
        self.background = background
        self.antialias = antialias
    
    def draw(self, str1, screen, pos):
        text = self.font.render(str1, self.antialias, self.color, self.background)
        screen.blit(text, pos)