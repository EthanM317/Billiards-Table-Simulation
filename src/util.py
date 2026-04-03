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
RED = (255, 0, 0, 255) #ball colour 1
BLUE = (0, 0, 255, 255) #ball colour 2
GREEN = (0, 255, 0, 255) #selected ball colour
BROWN = (139, 69, 19) #pool cue colour



def load_image(name):
    image = pygame.image.load(name)
    return image

class MyCircle(pygame.sprite.Sprite):
    def __init__(self, color, width, height, alpha=255):
        pygame.sprite.Sprite.__init__(self)

        #need to keep track of size & location data so we can re-draw in same spot when needed
        self.width = width
        self.height = height
        self.image = pygame.Surface([width, height], flags=pygame.SRCALPHA)
        self.rect = self.image.get_rect()
        self.cx = self.rect.centerx
        self.cy = self.rect.centery
        pygame.draw.circle(self.image, color, (self.cx, self.cy), self.width/2)
#        self.rect = self.image.get_rect()

        self.picked = False

    def set_pos(self, pos):
        self.rect.x = pos[0] - self.rect.width//2
        self.rect.y = pos[1] - self.rect.height//2
        
        self.cx = self.rect.centerx
        self.cy = self.rect.centery

    def update(self):
        pass
    
    def setColor(self, newColor):
        self.color = newColor
        self.image.fill((0, 0, 0, 0))  # Clear the surface
        pygame.draw.circle(self.image, newColor, (self.width/2, self.height/2), self.width/2)
 
    
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