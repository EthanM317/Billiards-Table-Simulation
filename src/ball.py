import util
import pygame
import math
import numpy as np
class Ball(util.MyCircle):
    def __init__(self, color, width, height, state):
        super().__init__(color, width, height)
        self.selected = False
        self.color = color
        self.cue = None
        
        #simulation variables
        self.m = 1.0
        self.c = 0.01
        self.state = np.zeros(4)
        self.cur_time = 0.0
        self.dt = 0.01
        self.m = 1.0
        self.c = 0.01
        self.cur_time = 0.0

    #simulation functions
    def init(self, state): 
        self.state = np.array(state, dtype=float) 
        self.x, self.y, self.vx, self.vy = self.state 
        self.cur_time = 0.0
    
    def derivatives(self, state):
        x, y, vx, vy = state
        
        v = np.array([vx, vy])
        speed = np.linalg.norm(v)
        
        if speed > 1e-6: #checks if ball is actually moving
            ax, ay = -self.c * 9.8 * v / speed
        else:
            ax, ay = 0, 0
            
        return np.array([vx, vy, ax, ay])


    def rk4_step(self):

        k1 = self.derivatives(self.state)
        k2 = self.derivatives(self.state + self.dt*k1/2)
        k3 = self.derivatives(self.state + self.dt*k2/2)
        k4 = self.derivatives(self.state + self.dt*k3)

        new_state = self.state + self.dt*(k1 + 2*k2 + 2*k3 + k4)/6

        #stops ball from rolling backwards (velocity reversal)
        if np.dot(self.state[2:4], new_state[2:4]) < 0:
            new_state[2] = 0
            new_state[3] = 0

        self.state = new_state
        #ensures that ball stops moving eventually
        if np.linalg.norm(self.state[2:4]) < 0.01: 
            self.state[2] = 0
            self.state[3] = 0

    def update(self):
        self.rk4_step()

        self.x, self.y, self.vx, self.vy = self.state

        self.rect.x = self.x
        self.rect.y = self.y

        self.cur_time += self.dt
        
        
        
        
        
    #graphical object functions
    def is_clicked(self, mouse_pos):
        return self.rect.collidepoint(mouse_pos)
    
    def draw_cue(self, screen, mouse_pos):
        self.cue = pygame.draw.line(screen, util.BROWN, (self.cx, self.cy), mouse_pos, 3)
        
        #want to return length of cue so that we can convert it to a "power" value
        length = math.sqrt(self.cue.width**2 + self.cue.height**2)
        return length
    
    def is_shot(self, power):
        self.init(np.array([self.x, self.y, _, _]))