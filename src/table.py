import pygame, sys
import numpy as np
import math
import util
from ball import Ball

WALL_THICKNESS = 30
POCKET_RADIUS = 13
FELT_GREEN = (34, 100, 34)
CUE_COLOR = (245, 245, 210, 255)

BALL_COLORS = [
    (255, 215, 0, 255),   # 1 yellow
    (30, 30, 200, 255),   # 2 blue
    (200, 30, 30, 255),   # 3 red
    (120, 0, 120, 255),   # 4 purple
    (255, 140, 0, 255),   # 5 orange
    (30, 150, 30, 255),   # 6 green
    (180, 60, 20, 255),   # 7 maroon
    (20, 20, 20, 255),    # 8 black
    (255, 215, 0, 255),   # 9 yellow again
]

SLIDER_PANEL_WIDTH = 260
SLIDER_START_X = 15
SLIDER_HEIGHT = 18
SLIDER_WIDTH = SLIDER_PANEL_WIDTH - 30

# helper: get pocket positions (with horizontal offset)
def get_pockets(win_width, win_height, wt, offset_x):
    mid_y = win_height // 2
    return [
        (offset_x + wt, wt),
        (offset_x + win_width - wt, wt),
        (offset_x + wt, mid_y),
        (offset_x + win_width - wt, mid_y),
        (offset_x + wt, win_height - wt),
        (offset_x + win_width - wt, win_height - wt),
    ]

# wall collision with offset and adjustable restitution
def wall_collision(ball, wt, win_width, win_height, pockets, offset_x):
    cx = ball.state[0] + ball.radius
    cy = ball.state[1] + ball.radius
    for px, py in pockets:
        if math.hypot(cx - px, cy - py) < POCKET_RADIUS * 1.8:
            return

    e = Ball.ball_wall_restitution
    left = offset_x + wt
    right = offset_x + win_width - wt - ball.width
    top = wt
    bottom = win_height - wt - ball.height

    if ball.state[0] < left:
        ball.state[0] = float(left)
        ball.state[2] = abs(ball.state[2]) * e
    if ball.state[0] > right:
        ball.state[0] = float(right)
        ball.state[2] = -abs(ball.state[2]) * e
    if ball.state[1] < top:
        ball.state[1] = float(top)
        ball.state[3] = abs(ball.state[3]) * e
    if ball.state[1] > bottom:
        ball.state[1] = float(bottom)
        ball.state[3] = -abs(ball.state[3]) * e

    ball.rect.x = int(ball.state[0])
    ball.rect.y = int(ball.state[1])
    ball.cx = ball.rect.centerx
    ball.cy = ball.rect.centery

# ball-ball collisions (equal mass, restitution from class)
def ball_collisions(balls):
    blist = list(balls)
    for i in range(len(blist)):
        for j in range(i+1, len(blist)):
            b1, b2 = blist[i], blist[j]
            c1 = np.array([b1.state[0]+b1.radius, b1.state[1]+b1.radius])
            c2 = np.array([b2.state[0]+b2.radius, b2.state[1]+b2.radius])
            diff = c2 - c1
            dist = np.linalg.norm(diff)
            min_dist = b1.radius + b2.radius
            if 0 < dist < min_dist:
                n = diff / dist
                overlap = min_dist - dist
                b1.state[0] -= n[0] * overlap/2
                b1.state[1] -= n[1] * overlap/2
                b2.state[0] += n[0] * overlap/2
                b2.state[1] += n[1] * overlap/2

                e = Ball.ball_ball_restitution
                v1 = b1.state[2:4].copy()
                v2 = b2.state[2:4].copy()
                impulse = np.dot(v1 - v2, n)
                if impulse > 0:
                    j = (1+e) * impulse / 2
                    b1.state[2] -= j * n[0]
                    b1.state[3] -= j * n[1]
                    b2.state[2] += j * n[0]
                    b2.state[3] += j * n[1]

                for b in (b1, b2):
                    b.rect.x = int(b.state[0])
                    b.rect.y = int(b.state[1])
                    b.cx = b.rect.centerx
                    b.cy = b.rect.centery

def check_pockets(group, pockets):
    remove = []
    for ball in group:
        cx = ball.state[0] + ball.radius
        cy = ball.state[1] + ball.radius
        for px, py in pockets:
            if math.hypot(cx-px, cy-py) < POCKET_RADIUS:
                remove.append(ball)
                break
    for ball in remove:
        ball.kill()

def all_stopped(group):
    return all(not b.is_moving() for b in group)

def draw_pockets(screen, pockets):
    for px, py in pockets:
        pygame.draw.circle(screen, (0,0,0), (int(px), int(py)), POCKET_RADIUS)

# draw slider panel with draggable sliders
def draw_sliders(screen, sliders, values, drag_idx):
    panel = pygame.Rect(0, 0, SLIDER_PANEL_WIDTH, screen.get_height())
    pygame.draw.rect(screen, (40,35,30), panel)
    pygame.draw.rect(screen, (80,70,55), panel, 2)
    font = pygame.font.SysFont("comicsansms", 13)
    title = pygame.font.SysFont("comicsansms", 18, bold=True).render("PHYSICS", True, (255,215,140))
    screen.blit(title, (SLIDER_PANEL_WIDTH//2 - title.get_width()//2, 12))

    for i, (label, rect, vmin, vmax, _) in enumerate(sliders):
        if i == drag_idx:
            pygame.draw.rect(screen, (100,90,70), rect.inflate(4,6), border_radius=4)
        txt = font.render(label, True, (220,210,180))
        screen.blit(txt, (rect.x+5, rect.y-18))
        val_txt = font.render(f"{values[i]:.2f}", True, (255,200,100))
        screen.blit(val_txt, (rect.x+rect.width-45, rect.y-18))
        pygame.draw.rect(screen, (60,55,45), rect)
        pygame.draw.rect(screen, (120,110,90), rect, 1)
        fill = int((values[i]-vmin)/(vmax-vmin)*rect.width)
        pygame.draw.rect(screen, (180,140,80), (rect.x, rect.y, fill, rect.height))
        knob = pygame.Rect(rect.x+fill-6, rect.y-2, 12, rect.height+4)
        pygame.draw.rect(screen, (220,180,100), knob)
        pygame.draw.rect(screen, (150,120,70), knob, 1)

def get_slider_at(pos, sliders):
    for i, (_, rect, _, _, _) in enumerate(sliders):
        if rect.collidepoint(pos):
            return i
    return None

def set_slider_value(i, pos, sliders, values):
    _, rect, vmin, vmax, _ = sliders[i]
    t = (pos[0] - rect.x) / rect.width
    t = max(0.0, min(1.0, t))
    values[i] = vmin + t*(vmax-vmin)
    return values[i]

# build diamond rack (9-ball)
def build_rack(win_width, win_height, wt, offset_x):
    d = 12.0
    vs = d * math.sin(math.pi/3)
    hs = d
    cx = offset_x + win_width//2
    cy = win_height - wt - 150
    positions = [
        (cx, cy),
        (cx - hs/2, cy + vs),
        (cx + hs/2, cy + vs),
        (cx - hs, cy + 2*vs),
        (cx, cy + 2*vs),
        (cx + hs, cy + 2*vs),
        (cx - hs/2, cy + 3*vs),
        (cx + hs/2, cy + 3*vs),
        (cx, cy + 4*vs),
    ]
    balls = []
    for i, pos in enumerate(positions):
        b = Ball(BALL_COLORS[i], 11, 11)
        b.set_pos((int(pos[0]), int(pos[1])))
        balls.append(b)
    return balls

def main():
    pygame.init()
    clock = pygame.time.Clock()
    wt = WALL_THICKNESS
    win_width = 440 + wt
    win_height = 880 + wt
    offset_x = SLIDER_PANEL_WIDTH
    screen = pygame.display.set_mode((win_width + offset_x, win_height))
    pygame.display.set_caption("Pool with sliders")

    # walls
    left_wall = util.MyRect(util.BLUE, wt, win_height)
    right_wall = util.MyRect(util.BLUE, wt, win_height)
    top_wall = util.MyRect(util.BLUE, win_width, wt)
    bottom_wall = util.MyRect(util.BLUE, win_width, wt)
    left_wall.set_pos((offset_x + wt/2, win_height/2))
    right_wall.set_pos((offset_x + win_width - wt/2, win_height/2))
    top_wall.set_pos((offset_x + win_width/2, wt/2))
    bottom_wall.set_pos((offset_x + win_width/2, win_height - wt/2))
    walls = pygame.sprite.Group([left_wall, right_wall, top_wall, bottom_wall])

    pockets = get_pockets(win_width, win_height, wt, offset_x)

    # balls
    balls = pygame.sprite.Group()
    for b in build_rack(win_width, win_height, wt, offset_x):
        balls.add(b)
    cue = Ball(CUE_COLOR, 11, 11)
    cue.set_pos((offset_x + win_width//2, wt + 100))
    cue.selected = True
    balls.add(cue)

    # sliders
    rects = [
        pygame.Rect(SLIDER_START_X, 70, SLIDER_WIDTH, SLIDER_HEIGHT),
        pygame.Rect(SLIDER_START_X, 135, SLIDER_WIDTH, SLIDER_HEIGHT),
        pygame.Rect(SLIDER_START_X, 200, SLIDER_WIDTH, SLIDER_HEIGHT),
        pygame.Rect(SLIDER_START_X, 265, SLIDER_WIDTH, SLIDER_HEIGHT),
    ]
    sliders = [
        ("ball-ball restitution", rects[0], 0.0, 1.0, 0.95),
        ("ball-wall restitution", rects[1], 0.0, 1.0, 0.75),
        ("rolling friction",       rects[2], 0.0, 20.0, 8.0),
        ("shot power multiplier", rects[3], 1.0, 100.0, 4.8),
    ]
    values = [0.95, 0.75, 8.0, 4.8]
    dragging = None

    # apply initial physics
    Ball.ball_ball_restitution = values[0]
    Ball.ball_wall_restitution = values[1]
    Ball.rolling_friction = values[2]
    Ball.shot_power_multiplier = values[3]
    for b in balls:
        b.c = Ball.rolling_friction

    drawing_cue = True

    while True:
        clock.tick(60)
        for b in balls:
            b.c = Ball.rolling_friction   # keep friction updated

        screen.fill((20,20,25))
        pygame.draw.rect(screen, FELT_GREEN, (offset_x, 0, win_width, win_height))
        walls.draw(screen)
        draw_pockets(screen, pockets)

        balls.update()
        pockets = get_pockets(win_width, win_height, wt, offset_x)  # refresh
        for b in list(balls):
            wall_collision(b, wt, win_width, win_height, pockets, offset_x)
        ball_collisions(balls)
        check_pockets(balls, pockets)

        if drawing_cue and not any(b.selected for b in balls):
            drawing_cue = False

        balls.draw(screen)

        if drawing_cue:
            mouse = pygame.mouse.get_pos()
            for b in balls:
                if b.selected:
                    b.draw_cue(screen, mouse)
                    break

        # hint text
        font = pygame.font.SysFont("comicsansms", 13)
        if drawing_cue:
            hint = "Click on table to shoot"
        elif not all_stopped(balls):
            hint = "Rolling..."
        else:
            hint = "Click on table to shoot"
        screen.blit(font.render(hint, True, (220,220,220)), (offset_x+8, win_height-22))

        draw_sliders(screen, sliders, values, dragging)

        # auto-select cue when stopped
        if not drawing_cue and all_stopped(balls) and cue in balls:
            cue.selected = True
            drawing_cue = True

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit(0)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                pos = event.pos
                idx = get_slider_at(pos, sliders)
                if idx is not None:
                    dragging = idx
                    set_slider_value(idx, pos, sliders, values)
                    Ball.ball_ball_restitution = values[0]
                    Ball.ball_wall_restitution = values[1]
                    Ball.rolling_friction = values[2]
                    Ball.shot_power_multiplier = values[3]
                elif drawing_cue and pos[0] > offset_x:
                    for b in balls:
                        if b.selected:
                            b.is_shot(pos)
                            b.selected = False
                            drawing_cue = False
                            break
            elif event.type == pygame.MOUSEMOTION and dragging is not None:
                set_slider_value(dragging, event.pos, sliders, values)
                Ball.ball_ball_restitution = values[0]
                Ball.ball_wall_restitution = values[1]
                Ball.rolling_friction = values[2]
                Ball.shot_power_multiplier = values[3]
            elif event.type == pygame.MOUSEBUTTONUP:
                dragging = None

        pygame.display.flip()

if __name__ == "__main__":
    main()
