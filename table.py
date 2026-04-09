import pygame, sys
import numpy as np
import math
import util
from ball import Ball

# ── constants ──────────────────────────────────────────────────────────────────
WALL_THICKNESS   = 30
POCKET_RADIUS    = 21
FELT_GREEN       = (34, 100, 34)
CUE_COLOR        = (245, 245, 210, 255)
BALL_RADIUS      = 10.0  # radius of each ball (diameter 20)

BALL_COLORS = [
    (200, 200,   0, 255),   # 1  yellow
    ( 30,  30, 200, 255),   # 2  blue
    (200,  30,  30, 255),   # 3  red
    (120,   0, 120, 255),   # 4  purple
    (255, 140,   0, 255),   # 5  orange
    ( 30, 150,  30, 255),   # 6  green
    (180,  60,  20, 255),   # 7  maroon
    ( 20,  20,  20, 255),   # 8  black
    (255, 215,   0, 255),   # 9  yellow stripe
]

SLIDER_PANEL_WIDTH = 260
SLIDER_START_X     = 15
SLIDER_HEIGHT      = 18
SLIDER_WIDTH       = SLIDER_PANEL_WIDTH - 30

# ── game states ────────────────────────────────────────────────────────────────
WAITING      = "waiting"
MOVING       = "moving"
BALL_IN_HAND = "ball_in_hand"
GAME_OVER    = "game_over"


# ── pocket / wall helpers ──────────────────────────────────────────────────────

def get_pockets(win_width, win_height, wt, offset_x):
    mid_y = win_height // 2
    return [
        (offset_x + wt,             wt),
        (offset_x + win_width - wt, wt),
        (offset_x + wt,             mid_y),
        (offset_x + win_width - wt, mid_y),
        (offset_x + wt,             win_height - wt),
        (offset_x + win_width - wt, win_height - wt),
    ]


def wall_collision(ball, wt, win_width, win_height, pockets, offset_x):
    cx = ball.state[0] + ball.radius
    cy = ball.state[1] + ball.radius
    for px, py in pockets:
        if math.hypot(cx - px, cy - py) < POCKET_RADIUS * 1.8:
            return

    e     = Ball.ball_wall_restitution
    left  = offset_x + wt
    right = offset_x + win_width  - wt - ball.width
    top   = wt
    bot   = win_height - wt - ball.height

    if ball.state[0] < left:
        ball.state[0] = float(left);  ball.state[2] =  abs(ball.state[2]) * e
    if ball.state[0] > right:
        ball.state[0] = float(right); ball.state[2] = -abs(ball.state[2]) * e
    if ball.state[1] < top:
        ball.state[1] = float(top);   ball.state[3] =  abs(ball.state[3]) * e
    if ball.state[1] > bot:
        ball.state[1] = float(bot);   ball.state[3] = -abs(ball.state[3]) * e

    ball.rect.x = int(ball.state[0]); ball.rect.y = int(ball.state[1])
    ball.cx = ball.rect.centerx;      ball.cy = ball.rect.centery


def ball_collisions(balls, cue, first_contact):
    """Resolve ball-ball collisions; return first cue->object contact number, or None."""
    new_contact = None
    blist = list(balls)
    for i in range(len(blist)):
        for j in range(i + 1, len(blist)):
            b1, b2 = blist[i], blist[j]
            c1 = np.array([b1.state[0] + b1.radius, b1.state[1] + b1.radius])
            c2 = np.array([b2.state[0] + b2.radius, b2.state[1] + b2.radius])
            diff = c2 - c1
            dist = np.linalg.norm(diff)
            min_dist = b1.radius + b2.radius
            if 0 < dist < min_dist:
                n       = diff / dist
                overlap = min_dist - dist
                b1.state[0] -= n[0] * overlap / 2
                b1.state[1] -= n[1] * overlap / 2
                b2.state[0] += n[0] * overlap / 2
                b2.state[1] += n[1] * overlap / 2

                e       = Ball.ball_ball_restitution
                v1      = b1.state[2:4].copy()
                v2      = b2.state[2:4].copy()
                impulse = np.dot(v1 - v2, n)
                if impulse > 0:
                    ji = (1 + e) * impulse / 2
                    b1.state[2] -= ji * n[0]; b1.state[3] -= ji * n[1]
                    b2.state[2] += ji * n[0]; b2.state[3] += ji * n[1]

                for b in (b1, b2):
                    b.rect.x = int(b.state[0]); b.rect.y = int(b.state[1])
                    b.cx = b.rect.centerx;       b.cy = b.rect.centery

                # Detect first cue-to-object-ball contact this shot
                if first_contact is None and new_contact is None:
                    if b1 is cue and getattr(b2, 'number', 0) != 0:
                        new_contact = b2.number
                    elif b2 is cue and getattr(b1, 'number', 0) != 0:
                        new_contact = b1.number

    return new_contact


def check_pockets(group, pockets):
    """Remove pocketed balls; return set of their numbers (0 = cue)."""
    pocketed = set()
    for ball in list(group):
        cx = ball.state[0] + ball.radius
        cy = ball.state[1] + ball.radius
        for px, py in pockets:
            if math.hypot(cx - px, cy - py) < POCKET_RADIUS:
                pocketed.add(getattr(ball, 'number', -1))
                ball.kill()
                break
    return pocketed


def all_stopped(group):
    return all(not b.is_moving() for b in group)


def draw_pockets(screen, pockets):
    for px, py in pockets:
        pygame.draw.circle(screen, (0, 0, 0), (int(px), int(py)), POCKET_RADIUS)


# ── ball placement helpers ─────────────────────────────────────────────────────

def can_place(mx, my, balls, cue, wt, win_width, win_height, offset_x):
    """True if position is inside the table and doesn't overlap any live ball."""
    margin = int(BALL_RADIUS) + 3
    left   = offset_x + wt + margin
    right  = offset_x + win_width  - wt - margin
    top    = wt + margin
    bot    = win_height - wt - margin
    if not (left < mx < right and top < my < bot):
        return False
    for ball in balls:
        if ball is cue:
            continue
        bcx = ball.state[0] + ball.radius
        bcy = ball.state[1] + ball.radius
        if math.hypot(mx - bcx, my - bcy) < BALL_RADIUS * 2 + 2:
            return False
    return True


# ── rack builder ───────────────────────────────────────────────────────────────

def build_rack(win_width, win_height, wt, offset_x):
    d  = 21.0
    vs = d * math.sin(math.pi / 3)
    hs = d
    cx = offset_x + win_width // 2
    cy = win_height - wt - 150
    positions = [
        (cx,          cy),
        (cx - hs/2,   cy + vs),
        (cx + hs/2,   cy + vs),
        (cx - hs,     cy + 2*vs),
        (cx,          cy + 2*vs),   # centre → ball 9
        (cx + hs,     cy + 2*vs),
        (cx - hs/2,   cy + 3*vs),
        (cx + hs/2,   cy + 3*vs),
        (cx,          cy + 4*vs),
    ]
    # 9-ball rules: 1 at apex, 9 at centre, rest in any order
    order = [1, 2, 3, 4, 9, 5, 6, 7, 8]
    result = []
    for num, pos in zip(order, positions):
        b = Ball(BALL_COLORS[num - 1], 20, 20)
        b.number = num
        b.set_pos((int(pos[0]), int(pos[1])))
        result.append(b)
    return result


# ── slider panel drawing ───────────────────────────────────────────────────────

def draw_sliders(screen, sliders, values, drag_idx,
                 next_ball, cur_player, game_state, winner, win_height):
    panel = pygame.Rect(0, 0, SLIDER_PANEL_WIDTH, win_height)
    pygame.draw.rect(screen, (40, 35, 30), panel)
    pygame.draw.rect(screen, (80, 70, 55), panel, 2)

    font_s = pygame.font.SysFont("comicsansms", 12)
    font_b = pygame.font.SysFont("comicsansms", 15, bold=True)

    # Physics header
    title = font_b.render("PHYSICS", True, (255, 215, 140))
    screen.blit(title, (SLIDER_PANEL_WIDTH // 2 - title.get_width() // 2, 12))

    for i, (label, rect, vmin, vmax, _) in enumerate(sliders):
        if i == drag_idx:
            pygame.draw.rect(screen, (100, 90, 70), rect.inflate(4, 6), border_radius=4)
        screen.blit(font_s.render(label, True, (220, 210, 180)), (rect.x + 5, rect.y - 18))
        screen.blit(font_s.render(f"{values[i]:.2f}", True, (255, 200, 100)),
                    (rect.x + rect.width - 45, rect.y - 18))
        pygame.draw.rect(screen, (60, 55, 45), rect)
        pygame.draw.rect(screen, (120, 110, 90), rect, 1)
        fill = int((values[i] - vmin) / (vmax - vmin) * rect.width)
        pygame.draw.rect(screen, (180, 140, 80), (rect.x, rect.y, fill, rect.height))
        knob = pygame.Rect(rect.x + fill - 6, rect.y - 2, 12, rect.height + 4)
        pygame.draw.rect(screen, (220, 180, 100), knob)
        pygame.draw.rect(screen, (150, 120, 70), knob, 1)

    # Separator
    sep_y = 310
    pygame.draw.line(screen, (80, 70, 55), (10, sep_y), (SLIDER_PANEL_WIDTH - 10, sep_y), 1)
    gy = sep_y + 14

    # Game-over screen
    if game_state == GAME_OVER:
        col  = (255, 215, 0) if winner else (200, 200, 200)
        msg  = f"Player {winner} WINS!" if winner else "Game Over"
        t    = font_b.render(msg, True, col)
        screen.blit(t, t.get_rect(centerx=SLIDER_PANEL_WIDTH // 2, y=gy)); gy += 30
        t2   = font_s.render("Press R to restart", True, (180, 200, 180))
        screen.blit(t2, t2.get_rect(centerx=SLIDER_PANEL_WIDTH // 2, y=gy))
        return

    # Active player
    p_col = (90, 160, 255) if cur_player == 1 else (255, 140, 60)
    pt = font_b.render(f"Player {cur_player}", True, p_col)
    screen.blit(pt, pt.get_rect(centerx=SLIDER_PANEL_WIDTH // 2, y=gy)); gy += 28

    # State hint
    if game_state == BALL_IN_HAND:
        for line in ("Ball in hand:", "click table to place"):
            t = font_s.render(line, True, (255, 210, 80))
            screen.blit(t, t.get_rect(centerx=SLIDER_PANEL_WIDTH // 2, y=gy)); gy += 18
        gy += 4
    elif game_state == MOVING:
        t = font_s.render("Rolling...", True, (150, 200, 150))
        screen.blit(t, t.get_rect(centerx=SLIDER_PANEL_WIDTH // 2, y=gy)); gy += 22
    else:
        t = font_s.render("Aim & click to shoot", True, (150, 200, 150))
        screen.blit(t, t.get_rect(centerx=SLIDER_PANEL_WIDTH // 2, y=gy)); gy += 22

    # Next-ball tracker
    pygame.draw.line(screen, (80, 70, 55), (10, gy), (SLIDER_PANEL_WIDTH - 10, gy), 1)
    gy += 12
    nb_lbl = font_b.render("Next ball:", True, (220, 210, 180))
    screen.blit(nb_lbl, nb_lbl.get_rect(centerx=SLIDER_PANEL_WIDTH // 2, y=gy)); gy += 26

    if next_ball is not None:
        col3 = BALL_COLORS[next_ball - 1][:3]
        bx, by = SLIDER_PANEL_WIDTH // 2, gy + 18
        pygame.draw.circle(screen, (220, 220, 220), (bx, by), 20)
        pygame.draw.circle(screen, col3,             (bx, by), 18)
        nf  = pygame.font.SysFont("arial", 13, bold=True)
        nc  = (255, 255, 255) if next_ball != 8 else (160, 160, 160)
        nt  = nf.render(str(next_ball), True, nc)
        screen.blit(nt, nt.get_rect(center=(bx, by))); gy += 44
        name_map = {1:"Yellow", 2:"Blue", 3:"Red", 4:"Purple",
                    5:"Orange", 6:"Green", 7:"Maroon", 8:"Black", 9:"Yellow (9)"}
        nm = font_s.render(name_map.get(next_ball, ""), True, col3)
        screen.blit(nm, nm.get_rect(centerx=SLIDER_PANEL_WIDTH // 2, y=gy))
    else:
        t = font_s.render("(none remaining)", True, (140, 140, 140))
        screen.blit(t, t.get_rect(centerx=SLIDER_PANEL_WIDTH // 2, y=gy))


def get_slider_at(pos, sliders):
    for i, (_, rect, _, _, _) in enumerate(sliders):
        if rect.collidepoint(pos):
            return i
    return None


def set_slider_value(i, pos, sliders, values):
    _, rect, vmin, vmax, _ = sliders[i]
    t = max(0.0, min(1.0, (pos[0] - rect.x) / rect.width))
    values[i] = vmin + t * (vmax - vmin)


def apply_physics(values):
    Ball.ball_ball_restitution = values[0]
    Ball.ball_wall_restitution = values[1]
    Ball.rolling_friction      = values[2]
    Ball.shot_power_multiplier = values[3]


# ── game init ──────────────────────────────────────────────────────────────────

def init_game(win_width, win_height, wt, offset_x):
    balls = pygame.sprite.Group()
    for b in build_rack(win_width, win_height, wt, offset_x):
        balls.add(b)
    cue = Ball(CUE_COLOR, 20, 20)
    cue.number   = 0
    cue.selected = True
    cue.set_pos((offset_x + win_width // 2, wt + 100))
    balls.add(cue)
    remaining = list(range(1, 10))   # [1, 2, … 9]
    return balls, cue, remaining


# ── main ──────────────────────────────────────────────────────────────────────

def main():
    pygame.init()
    clock = pygame.time.Clock()

    wt         = WALL_THICKNESS
    win_width  = 440 + wt
    win_height = 880 + wt
    offset_x   = SLIDER_PANEL_WIDTH
    screen     = pygame.display.set_mode((win_width + offset_x, win_height))
    pygame.display.set_caption("9-Ball Pool")

    # Walls
    def make_walls():
        lw = util.MyRect(util.BLUE, wt, win_height)
        rw = util.MyRect(util.BLUE, wt, win_height)
        tw = util.MyRect(util.BLUE, win_width, wt)
        bw = util.MyRect(util.BLUE, win_width, wt)
        lw.set_pos((offset_x + wt/2,            win_height/2))
        rw.set_pos((offset_x + win_width - wt/2, win_height/2))
        tw.set_pos((offset_x + win_width/2,      wt/2))
        bw.set_pos((offset_x + win_width/2,      win_height - wt/2))
        return pygame.sprite.Group([lw, rw, tw, bw])

    walls   = make_walls()
    pockets = get_pockets(win_width, win_height, wt, offset_x)

    # Sliders
    rects = [
        pygame.Rect(SLIDER_START_X,  70, SLIDER_WIDTH, SLIDER_HEIGHT),
        pygame.Rect(SLIDER_START_X, 135, SLIDER_WIDTH, SLIDER_HEIGHT),
        pygame.Rect(SLIDER_START_X, 200, SLIDER_WIDTH, SLIDER_HEIGHT),
        pygame.Rect(SLIDER_START_X, 265, SLIDER_WIDTH, SLIDER_HEIGHT),
    ]
    sliders = [
        ("ball-ball restitution", rects[0],  0.0,  1.0, 0.95),
        ("ball-wall restitution", rects[1],  0.0,  1.0, 0.75),
        ("rolling friction",      rects[2],  0.0, 20.0, 8.0 ),
        ("shot power multiplier", rects[3],  1.0,100.0, 4.8 ),
    ]
    values   = [0.95, 0.75, 8.0, 4.8]
    dragging = None
    apply_physics(values)

    # Game state
    balls, cue, remaining = init_game(win_width, win_height, wt, offset_x)
    for b in balls:
        b.c = Ball.rolling_friction

    game_state    = WAITING
    cur_player    = 1
    first_contact = None   # number of first object ball the cue touched this shot
    shot_lowest   = None   # lowest remaining ball number when the shot was fired
    pocketed_this = set()  # object-ball numbers pocketed this shot
    cue_scratch   = False
    foul_msg      = ""
    winner        = None

    font_hint = pygame.font.SysFont("comicsansms", 13)

    # ── main loop ──────────────────────────────────────────────────────────────
    while True:
        clock.tick(60)

        # Keep friction in sync with slider
        for b in balls:
            b.c = Ball.rolling_friction

        pockets = get_pockets(win_width, win_height, wt, offset_x)

        # Background
        screen.fill((20, 20, 25))
        pygame.draw.rect(screen, FELT_GREEN, (offset_x, 0, win_width, win_height))
        walls.draw(screen)
        draw_pockets(screen, pockets)

        # ── physics ────────────────────────────────────────────────────────────
        if game_state == MOVING:
            balls.update()
            for b in list(balls):
                wall_collision(b, wt, win_width, win_height, pockets, offset_x)

            new_c = ball_collisions(balls, cue, first_contact)
            if new_c is not None and first_contact is None:
                first_contact = new_c

            newly = check_pockets(balls, pockets)
            if 0 in newly:
                cue_scratch = True
            pocketed_this |= (newly - {0})

            # ── resolve when everything has stopped ────────────────────────────
            if all_stopped(balls):
                # Drop pocketed balls from queue regardless of legality
                remaining = [n for n in remaining if n not in pocketed_this]

                nine_down = 9 in pocketed_this
                foul      = False
                foul_parts = []

                if cue_scratch:
                    foul = True
                    foul_parts.append("Scratch!")

                if first_contact is None:
                    foul = True
                    foul_parts.append("No ball hit!")
                elif shot_lowest is not None and first_contact != shot_lowest:
                    foul = True
                    foul_parts.append(f"Must hit {shot_lowest} first!")

                if nine_down:
                    if foul:
                        # Illegal 9-ball → current player loses immediately
                        winner     = 2 if cur_player == 1 else 1
                        foul_msg   = f"Illegal 9-ball — Player {winner} wins!"
                    else:
                        # Legal 9-ball → current player wins
                        winner     = cur_player
                        foul_msg   = f"Player {winner} wins!"
                    game_state = GAME_OVER

                elif foul:
                    foul_msg   = "  ".join(foul_parts) + " — ball in hand."
                    cur_player = 2 if cur_player == 1 else 1
                    # Remove cue ball; opponent will place it
                    if cue in balls:
                        cue.kill()
                    game_state = BALL_IN_HAND

                else:
                    foul_msg = ""
                    if pocketed_this:
                        # Legal pot(s) → same player shoots again
                        pass
                    else:
                        # Clean miss → switch player
                        cur_player = 2 if cur_player == 1 else 1

                    # Restore cue-ball selection for next shot
                    if cue in balls:
                        cue.selected = True
                    game_state = WAITING

                # Reset shot tracking
                first_contact = None
                shot_lowest   = None
                pocketed_this = set()
                cue_scratch   = False

        # ── draw balls ─────────────────────────────────────────────────────────
        balls.draw(screen)

        # ── aiming line ────────────────────────────────────────────────────────
        if game_state == WAITING:
            mouse = pygame.mouse.get_pos()
            for b in balls:
                if getattr(b, 'selected', False):
                    b.draw_cue(screen, mouse)
                    break

        # ── ghost ball for ball-in-hand ────────────────────────────────────────
        if game_state == BALL_IN_HAND:
            mx, my = pygame.mouse.get_pos()
            ok     = can_place(mx, my, balls, None, wt, win_width, win_height, offset_x)
            pygame.draw.circle(screen,
                               (245, 245, 210) if ok else (220, 60, 60),
                               (mx, my), int(BALL_RADIUS), 2)

        # ── status text on felt ────────────────────────────────────────────────
        if foul_msg and game_state not in (GAME_OVER,):
            t = font_hint.render(foul_msg, True, (255, 80, 80))
            screen.blit(t, (offset_x + 8, win_height - 22))
        elif game_state == MOVING:
            screen.blit(font_hint.render("Rolling...", True, (200, 200, 200)),
                        (offset_x + 8, win_height - 22))
        elif game_state == WAITING:
            screen.blit(font_hint.render("Click to shoot", True, (200, 200, 200)),
                        (offset_x + 8, win_height - 22))

        # ── slider / game-info panel ───────────────────────────────────────────
        next_ball = remaining[0] if remaining else None
        draw_sliders(screen, sliders, values, dragging,
                     next_ball, cur_player, game_state, winner, win_height)

        # ── events ─────────────────────────────────────────────────────────────
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit(0)

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    balls, cue, remaining = init_game(win_width, win_height, wt, offset_x)
                    for b in balls:
                        b.c = Ball.rolling_friction
                    game_state    = WAITING
                    cur_player    = 1
                    first_contact = None
                    shot_lowest   = None
                    pocketed_this = set()
                    cue_scratch   = False
                    foul_msg      = ""
                    winner        = None

            elif event.type == pygame.MOUSEBUTTONDOWN:
                pos = event.pos

                # Slider interaction
                idx = get_slider_at(pos, sliders)
                if idx is not None:
                    dragging = idx
                    set_slider_value(idx, pos, sliders, values)
                    apply_physics(values)
                    for b in balls:
                        b.c = Ball.rolling_friction

                # Shoot
                elif game_state == WAITING and pos[0] > offset_x:
                    for b in list(balls):
                        if getattr(b, 'selected', False):
                            shot_lowest   = remaining[0] if remaining else None
                            b.is_shot(pos)
                            b.selected    = False
                            game_state    = MOVING
                            first_contact = None
                            pocketed_this = set()
                            cue_scratch   = False
                            break

                # Place cue ball (ball-in-hand)
                elif game_state == BALL_IN_HAND and pos[0] > offset_x:
                    mx, my = pos
                    if can_place(mx, my, balls, None, wt, win_width, win_height, offset_x):
                        cue = Ball(CUE_COLOR, 20, 20)
                        cue.number   = 0
                        cue.selected = True
                        cue.c        = Ball.rolling_friction
                        cue.set_pos((mx, my))
                        balls.add(cue)
                        game_state = WAITING
                        foul_msg   = ""

            elif event.type == pygame.MOUSEMOTION and dragging is not None:
                set_slider_value(dragging, event.pos, sliders, values)
                apply_physics(values)
                for b in balls:
                    b.c = Ball.rolling_friction

            elif event.type == pygame.MOUSEBUTTONUP:
                dragging = None

        pygame.display.flip()


if __name__ == "__main__":
    main()
