import pygame, sys
import numpy as np
import math
import util
from ball import Ball


# ── constants ─────────────────────────────────────────────────────────────────

WALL_THICKNESS = 30
POCKET_RADIUS  = 13          # pixels – a ball whose centre is within this range drops
FELT_GREEN     = (34, 100,  34)
CUE_COLOR      = (245, 245, 210, 255)   # ivory

# 9-ball colours (ball 1 → 9)
BALL_COLORS = [
    (255, 215,   0, 255),   # 1 – yellow
    (30,   30, 200, 255),   # 2 – blue
    (200,  30,  30, 255),   # 3 – red
    (120,   0, 120, 255),   # 4 – purple
    (255, 140,   0, 255),   # 5 – orange
    (30,  150,  30, 255),   # 6 – green
    (180,  60,  20, 255),   # 7 – maroon
    (20,   20,  20, 255),   # 8 – black
    (255, 215,   0, 255),   # 9 – yellow (marked differently in real pool)
]


# ── helper functions ───────────────────────────────────────────────────────────

def get_pockets(win_width, win_height, wt):
    """Return (x, y) for the 6 standard pool pockets."""
    mid_y = win_height // 2
    return [
        (wt,             wt),               # top-left corner
        (win_width - wt, wt),               # top-right corner
        (wt,             mid_y),            # left side
        (win_width - wt, mid_y),            # right side
        (wt,             win_height - wt),  # bottom-left corner
        (win_width - wt, win_height - wt),  # bottom-right corner
    ]


def handle_wall_collision(ball, wt, win_width, win_height, pockets):
    """Reflect ball off walls; skip reflection near pockets so the ball can drop."""
    cx = ball.state[0] + ball.radius
    cy = ball.state[1] + ball.radius

    # Near a pocket?  Let pocket-detection handle it instead.
    for px, py in pockets:
        if math.hypot(cx - px, cy - py) < POCKET_RADIUS * 1.8:
            return

    e = 0.75   # restitution coefficient
    if ball.state[0] < wt:
        ball.state[0] = float(wt)
        ball.state[2] = abs(ball.state[2]) * e
    if ball.state[0] + ball.width > win_width - wt:
        ball.state[0] = float(win_width - wt - ball.width)
        ball.state[2] = -abs(ball.state[2]) * e
    if ball.state[1] < wt:
        ball.state[1] = float(wt)
        ball.state[3] = abs(ball.state[3]) * e
    if ball.state[1] + ball.height > win_height - wt:
        ball.state[1] = float(win_height - wt - ball.height)
        ball.state[3] = -abs(ball.state[3]) * e

    ball.rect.x = int(ball.state[0])
    ball.rect.y = int(ball.state[1])
    ball.cx = ball.rect.centerx
    ball.cy = ball.rect.centery


def handle_ball_collisions(balls):
    """Elastic equal-mass collision between every pair of balls."""
    ball_list = list(balls)
    for i in range(len(ball_list)):
        for j in range(i + 1, len(ball_list)):
            b1, b2 = ball_list[i], ball_list[j]

            c1   = np.array([b1.state[0] + b1.radius, b1.state[1] + b1.radius])
            c2   = np.array([b2.state[0] + b2.radius, b2.state[1] + b2.radius])
            diff = c2 - c1
            dist = np.linalg.norm(diff)
            min_dist = b1.radius + b2.radius

            if 0 < dist < min_dist:
                n       = diff / dist
                overlap = min_dist - dist

                # push apart so they no longer overlap
                b1.state[0] -= n[0] * overlap / 2
                b1.state[1] -= n[1] * overlap / 2
                b2.state[0] += n[0] * overlap / 2
                b2.state[1] += n[1] * overlap / 2

                # exchange velocity components along collision normal (e = 0.9)
                e       = 0.95
                v1      = b1.state[2:4].copy()
                v2      = b2.state[2:4].copy()
                impulse = np.dot(v1 - v2, n)

                if impulse > 0:          # only when approaching each other
                    j = (1 + e) * impulse / 2   # equal-mass restitution impulse
                    b1.state[2] -= j * n[0]
                    b1.state[3] -= j * n[1]
                    b2.state[2] += j * n[0]
                    b2.state[3] += j * n[1]

                for b in (b1, b2):
                    b.rect.x = int(b.state[0])
                    b.rect.y = int(b.state[1])
                    b.cx = b.rect.centerx
                    b.cy = b.rect.centery


def check_pockets(group_balls, pockets):
    """Remove any ball whose centre lies within POCKET_RADIUS of a pocket."""
    to_remove = []
    for ball in group_balls:
        cx = ball.state[0] + ball.radius
        cy = ball.state[1] + ball.radius
        for px, py in pockets:
            if math.hypot(cx - px, cy - py) < POCKET_RADIUS:
                to_remove.append(ball)
                break
    for ball in to_remove:
        ball.kill()          # removes from all sprite groups


def all_stopped(group_balls):
    return all(not b.is_moving() for b in group_balls)


def draw_pockets(screen, pockets):
    for px, py in pockets:
        pygame.draw.circle(screen, (0, 0, 0), (int(px), int(py)), POCKET_RADIUS)


def build_rack(win_width, win_height, wt):
    """Return a list of Ball objects arranged in a 9-ball diamond near the bottom."""
    d  = 12.0                            # centre-to-centre spacing
    vs = d * math.sin(math.pi / 3)      # vertical row gap
    hs = d                               # horizontal gap between same-row balls

    rack_cx = win_width // 2
    rack_y  = win_height - wt - 150     # apex of diamond near bottom

    # Diamond layout: 1 + 2 + 3 + 2 + 1 = 9 balls
    positions = [
        (rack_cx,            rack_y             ),   # row 0
        (rack_cx - hs/2,     rack_y + 1*vs      ),   # row 1
        (rack_cx + hs/2,     rack_y + 1*vs      ),
        (rack_cx - hs,       rack_y + 2*vs      ),   # row 2
        (rack_cx,            rack_y + 2*vs      ),   # ball 9 (centre)
        (rack_cx + hs,       rack_y + 2*vs      ),
        (rack_cx - hs/2,     rack_y + 3*vs      ),   # row 3
        (rack_cx + hs/2,     rack_y + 3*vs      ),
        (rack_cx,            rack_y + 4*vs      ),   # row 4
    ]

    balls = []
    for i, pos in enumerate(positions):
        b = Ball(BALL_COLORS[i], 11, 11)
        b.set_pos((int(pos[0]), int(pos[1])))
        balls.append(b)
    return balls


# ── main ──────────────────────────────────────────────────────────────────────

def main():
    pygame.init()
    clock = pygame.time.Clock()

    wt         = WALL_THICKNESS
    win_width  = 244 + wt   # 274 px  (~122 cm at 0.5 cm/px)
    win_height = 488 + wt   # 518 px  (~244 cm)
    screen = pygame.display.set_mode((win_width, win_height))
    pygame.display.set_caption("9-Ball Pool Simulation")

    # ── walls ──────────────────────────────────────────────────────────────────
    wall_left   = util.MyRect(util.BLUE, wt,         win_height)
    wall_right  = util.MyRect(util.BLUE, wt,         win_height)
    wall_top    = util.MyRect(util.BLUE, win_width,  wt)
    wall_bottom = util.MyRect(util.BLUE, win_width,  wt)

    wall_right .set_pos((win_width  - wt / 2, win_height / 2))
    wall_bottom.set_pos((win_width  / 2,       win_height - wt / 2))

    group_walls = pygame.sprite.Group([wall_left, wall_right, wall_top, wall_bottom])

    # ── pockets ─────────────────────────────────────────────────────────────────
    pockets = get_pockets(win_width, win_height, wt)

    # ── balls ───────────────────────────────────────────────────────────────────
    group_balls = pygame.sprite.Group()

    for b in build_rack(win_width, win_height, wt):
        group_balls.add(b)

    # Cue ball – placed on the upper quarter of the table, auto-selected
    cue_ball = Ball(CUE_COLOR, 11, 11)
    cue_ball.set_pos((win_width // 2, wt + 100))
    cue_ball.selected = True
    group_balls.add(cue_ball)

    # ── state flags ─────────────────────────────────────────────────────────────
    drawing_cue = True   # first turn: cue ball is already aimed

    # ── game loop ───────────────────────────────────────────────────────────────
    while True:
        clock.tick(60)

        # ── background & walls ──────────────────────────────────────────────────
        screen.fill(FELT_GREEN)
        group_walls.draw(screen)
        draw_pockets(screen, pockets)

        # ── physics ─────────────────────────────────────────────────────────────
        group_balls.update()

        for ball in list(group_balls):
            handle_wall_collision(ball, wt, win_width, win_height, pockets)

        handle_ball_collisions(group_balls)
        check_pockets(group_balls, pockets)

        # If the ball that was selected got potted, cancel the cue
        if drawing_cue and not any(b.selected for b in group_balls):
            drawing_cue = False

        # ── draw balls ──────────────────────────────────────────────────────────
        group_balls.draw(screen)

        # ── draw cue stick ──────────────────────────────────────────────────────
        if drawing_cue:
            mouse_pos = pygame.mouse.get_pos()
            for ball in group_balls:
                if ball.selected:
                    ball.draw_cue(screen, mouse_pos)
                    break

        # ── HUD ─────────────────────────────────────────────────────────────────
        font = pygame.font.SysFont("comicsansms", 13)
        if drawing_cue:
            hint = "Click to shoot"
        elif not all_stopped(group_balls):
            hint = "Balls rolling..."
        else:
            hint = "Click to shoot"
        screen.blit(font.render(hint, True, (220, 220, 220)), (8, win_height - 22))

        # Auto-select cue ball once all balls have stopped
        if not drawing_cue and all_stopped(group_balls) and cue_ball in group_balls:
            cue_ball.selected = True
            drawing_cue = True

        # ── events ──────────────────────────────────────────────────────────────
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit(0)

            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()

                if drawing_cue:
                    # ── fire the shot ──────────────────────────────────────────
                    for ball in list(group_balls):
                        if ball.selected:
                            ball.is_shot(mouse_pos)
                            ball.selected = False
                            drawing_cue   = False
                            break

        pygame.display.flip()


if __name__ == '__main__':
    main()
