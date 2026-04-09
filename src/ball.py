import util
import pygame
import math
import numpy as np

class Ball(util.MyCircle):
    # global physics settings (can be changed by sliders)
    ball_ball_restitution = 0.95
    ball_wall_restitution = 0.75
    rolling_friction = 8.0
    shot_power_multiplier = 4.80

    def __init__(self, color, width, height):
        super().__init__(color, width, height)
        self.selected = False
        self.color = color
        self.radius = width / 2

        self.m = 1.0
        self.c = Ball.rolling_friction
        self.state = np.zeros(4)
        self.state[0], self.state[1] = self.rect.x, self.rect.y
        self.cur_time = 0.0
        self.dt = 0.01

    # physics: acceleration from rolling friction
    def derivatives(self, state):
        x, y, vx, vy = state
        v = np.array([vx, vy])
        speed = np.linalg.norm(v)
        if speed > 1e-6:
            ax, ay = -self.c * 9.8 * v / speed
        else:
            ax, ay = 0.0, 0.0
        return np.array([vx, vy, ax, ay])

    # runge-kutta 4 integration
    def rk4_step(self):
        k1 = self.derivatives(self.state)
        k2 = self.derivatives(self.state + self.dt * k1 / 2)
        k3 = self.derivatives(self.state + self.dt * k2 / 2)
        k4 = self.derivatives(self.state + self.dt * k3)
        new_state = self.state + self.dt * (k1 + 2*k2 + 2*k3 + k4) / 6

        # stop if friction would reverse direction
        if np.dot(self.state[2:4], new_state[2:4]) < 0:
            new_state[2] = 0.0
            new_state[3] = 0.0

        self.state = new_state

        # dead stop when very slow
        if np.linalg.norm(self.state[2:4]) < 3.0:
            self.state[2] = 0.0
            self.state[3] = 0.0

    def update(self):
        self.rk4_step()
        self.rect.x = int(self.state[0])
        self.rect.y = int(self.state[1])
        self.cx = self.rect.centerx
        self.cy = self.rect.centery
        self.cur_time += self.dt

    def is_moving(self):
        return np.linalg.norm(self.state[2:4]) > 3.0

    # place ball at pixel position
    def set_pos(self, pos):
        self.rect.x = pos[0] - self.rect.width // 2
        self.rect.y = pos[1] - self.rect.height // 2
        self.cx = self.rect.centerx
        self.cy = self.rect.centery
        self.state[0], self.state[1] = float(self.rect.x), float(self.rect.y)

    def is_clicked(self, mouse_pos):
        return self.rect.collidepoint(mouse_pos)

    # draw aiming line
    def draw_cue(self, screen, mouse_pos):
        pygame.draw.line(screen, util.BROWN, (self.cx, self.cy), mouse_pos, 3)

    # shoot: power from drag distance
    def is_shot(self, mouse_pos):
        dx = self.cx - mouse_pos[0]
        dy = self.cy - mouse_pos[1]
        dist = math.sqrt(dx*dx + dy*dy)
        if dist < 1:
            return
        power = min(dist * Ball.shot_power_multiplier, 720.0)
        self.state[2] = power * dx / dist
        self.state[3] = power * dy / dist
