"""Touch-friendly Tetris for Android (Pydroid 3) and desktop.
Install: pip install pygame
Run: python tetris_phone.py
"""
import random
import sys
import pygame

pygame.init()
W, H = 480, 800
screen = pygame.display.set_mode((W, H), pygame.RESIZABLE)
pygame.display.set_caption('Тетрис / Tetris')
clock = pygame.time.Clock()
FONT = pygame.font.Font(None, 32)
SMALL = pygame.font.Font(None, 25)
BIG = pygame.font.Font(None, 56)
COLORS = [(0, 0, 0), (0, 225, 235), (255, 212, 45), (183, 88, 255),
          (65, 230, 110), (255, 83, 89), (65, 115, 255), (255, 156, 54)]
SHAPES = [
    [(0, 1), (1, 1), (2, 1), (3, 1)],
    [(1, 0), (2, 0), (1, 1), (2, 1)],
    [(1, 0), (0, 1), (1, 1), (2, 1)],
    [(1, 0), (2, 0), (0, 1), (1, 1)],
    [(0, 0), (1, 0), (1, 1), (2, 1)],
    [(0, 0), (0, 1), (1, 1), (2, 1)],
    [(2, 0), (0, 1), (1, 1), (2, 1)],
]
COLS, ROWS = 10, 20
board = [[0] * COLS for _ in range(ROWS)]
score = lines = 0
paused = game_over = False
bag = []
current = None
next_piece = None
fall_timer = 0
last_repeat = 0
held_button = None


def pick():
    if not bag:
        bag.extend(random.sample(range(7), 7))
    return bag.pop()


def make_piece(kind):
    return {'kind': kind, 'cells': SHAPES[kind][:], 'x': 3, 'y': -1}


def valid(cells, x, y):
    for dx, dy in cells:
        xx, yy = x + dx, y + dy
        if xx < 0 or xx >= COLS or yy >= ROWS:
            return False
        if yy >= 0 and board[yy][xx]:
            return False
    return True


def spawn():
    global current, next_piece, game_over
    current = make_piece(next_piece)
    next_piece = pick()
    if not valid(current['cells'], current['x'], current['y']):
        game_over = True


def reset():
    global board, score, lines, paused, game_over, next_piece, bag, fall_timer
    board = [[0] * COLS for _ in range(ROWS)]
    score = lines = 0
    paused = game_over = False
    bag = []
    next_piece = pick()
    fall_timer = 0
    spawn()


def lock():
    global score, lines, board, game_over
    for dx, dy in current['cells']:
        x, y = current['x'] + dx, current['y'] + dy
        if y < 0:
            game_over = True
            return
        board[y][x] = current['kind'] + 1
    kept = [row for row in board if not all(row)]
    removed = ROWS - len(kept)
    if removed:
        board = [[0] * COLS for _ in range(removed)] + kept
        score += [0, 100, 300, 500, 800][removed] * (1 + lines // 10)
        lines += removed
    spawn()


def move(dx, dy):
    if valid(current['cells'], current['x'] + dx, current['y'] + dy):
        current['x'] += dx
        current['y'] += dy
        return True
    return False


def rotate():
    if current['kind'] == 1:
        return
    cells = current['cells']
    rotated = [(3 - y, x) for x, y in cells]
    for kick in (0, -1, 1, -2, 2):
        if valid(rotated, current['x'] + kick, current['y']):
            current['cells'] = rotated
            current['x'] += kick
            return


def action(name):
    global paused, score
    if name == 'restart':
        reset()
        return
    if name == 'pause':
        if not game_over:
            paused = not paused
        return
    if paused or game_over:
        return
    if name == 'left':
        move(-1, 0)
    elif name == 'right':
        move(1, 0)
    elif name == 'rotate':
        rotate()
    elif name == 'down':
        if move(0, 1):
            score += 1
        else:
            lock()
    elif name == 'drop':
        while move(0, 1):
            score += 2
        lock()


def draw_text(text, font, color, x, y, center=False):
    image = font.render(text, True, color)
    rect = image.get_rect()
    if center:
        rect.center = (x, y)
    else:
        rect.topleft = (x, y)
    screen.blit(image, rect)


def draw_cell(rect, color):
    pygame.draw.rect(screen, color, rect, border_radius=4)
    pygame.draw.rect(screen, tuple(min(255, c + 35) for c in color), rect.inflate(-5, -5), 2, border_radius=3)


def layout():
    sw, sh = screen.get_size()
    # Fit the whole interface to any portrait or landscape window.
    scale = min(sw / W, sh / H)
    ox = (sw - W * scale) / 2
    oy = (sh - H * scale) / 2
    return scale, ox, oy


BUTTONS = [
    ('left', (20, 676, 94, 82), '<'),
    ('right', (124, 676, 94, 82), '>'),
    ('rotate', (228, 676, 94, 82), 'ROT'),
    ('down', (332, 676, 60, 82), 'v'),
    ('drop', (400, 676, 60, 82), 'DROP'),
    ('pause', (332, 52, 128, 48), 'PAUSE'),
    ('restart', (332, 110, 128, 48), 'NEW'),
]


def virtual_button(pos):
    scale, ox, oy = layout()
    x, y = (pos[0] - ox) / scale, (pos[1] - oy) / scale
    for name, rect, _ in BUTTONS:
        if pygame.Rect(rect).collidepoint(x, y):
            return name
    # Tapping the playing field rotates the piece.
    if pygame.Rect(20, 74, 300, 600).collidepoint(x, y):
        return 'rotate'
    return None


def render():
    global screen
    real_screen = screen
    sw, sh = real_screen.get_size()
    canvas = pygame.Surface((W, H))
    screen = canvas
    screen.fill((13, 17, 30))
    draw_text('TETRIS', BIG, (102, 226, 244), 20, 15)
    pygame.draw.rect(screen, (29, 36, 55), (18, 72, 304, 604), border_radius=7)
    for y in range(ROWS):
        for x in range(COLS):
            rect = pygame.Rect(20 + x * 30, 74 + y * 30, 29, 29)
            pygame.draw.rect(screen, (22, 28, 44), rect, border_radius=3)
            if board[y][x]:
                draw_cell(rect, COLORS[board[y][x]])
    if not game_over:
        for dx, dy in current['cells']:
            x, y = current['x'] + dx, current['y'] + dy
            if y >= 0:
                draw_cell(pygame.Rect(20 + x * 30, 74 + y * 30, 29, 29), COLORS[current['kind'] + 1])
    draw_text('SCORE', SMALL, (177, 190, 215), 337, 192)
    draw_text(str(score), FONT, (255, 255, 255), 337, 220)
    draw_text('LINES', SMALL, (177, 190, 215), 337, 278)
    draw_text(str(lines), FONT, (255, 255, 255), 337, 306)
    draw_text('LEVEL', SMALL, (177, 190, 215), 337, 364)
    draw_text(str(lines // 10 + 1), FONT, (255, 255, 255), 337, 392)
    draw_text('NEXT', SMALL, (177, 190, 215), 337, 458)
    for dx, dy in SHAPES[next_piece]:
        draw_cell(pygame.Rect(339 + dx * 27, 500 + dy * 27, 25, 25), COLORS[next_piece + 1])
    for name, rect, label in BUTTONS:
        pygame.draw.rect(screen, (43, 68, 103) if name != 'drop' else (35, 112, 111), rect, border_radius=12)
        draw_text(label, SMALL if len(label) > 2 else BIG, (240, 247, 255),
                  rect[0] + rect[2] // 2, rect[1] + rect[3] // 2, True)
    if paused or game_over:
        shade = pygame.Surface((300, 600), pygame.SRCALPHA)
        shade.fill((6, 10, 20, 195))
        screen.blit(shade, (20, 74))
        draw_text('GAME OVER' if game_over else 'PAUSED', BIG, (255, 255, 255), 170, 350, True)
        draw_text('Tap NEW to restart' if game_over else 'Tap PAUSE to resume', SMALL,
                  (185, 210, 233), 170, 392, True)
    screen = real_screen
    scale, ox, oy = layout()
    frame = pygame.transform.smoothscale(canvas, (max(1, round(W * scale)), max(1, round(H * scale))))
    real_screen.fill((5, 8, 15))
    real_screen.blit(frame, (round(ox), round(oy)))
    pygame.display.flip()


reset()
FINGERDOWN = getattr(pygame, 'FINGERDOWN', -1)
FINGERUP = getattr(pygame, 'FINGERUP', -1)
while True:
    dt = min(clock.tick(60), 100)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        if event.type == pygame.VIDEORESIZE:
            screen = pygame.display.set_mode(event.size, pygame.RESIZABLE)
        if event.type == pygame.KEYDOWN:
            keymap = {pygame.K_LEFT: 'left', pygame.K_RIGHT: 'right', pygame.K_UP: 'rotate',
                      pygame.K_DOWN: 'down', pygame.K_SPACE: 'drop', pygame.K_p: 'pause',
                      pygame.K_r: 'restart'}
            if event.key in keymap:
                action(keymap[event.key])
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            held_button = virtual_button(event.pos)
            if held_button:
                action(held_button)
                last_repeat = pygame.time.get_ticks() + 240
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            held_button = None
        if event.type == FINGERDOWN:
            held_button = virtual_button((event.x * screen.get_width(), event.y * screen.get_height()))
            if held_button:
                action(held_button)
                last_repeat = pygame.time.get_ticks() + 240
        if event.type == FINGERUP:
            held_button = None
    if held_button in ('left', 'right', 'down') and pygame.time.get_ticks() >= last_repeat:
        action(held_button)
        last_repeat = pygame.time.get_ticks() + 90
    if not paused and not game_over:
        fall_timer += dt
        interval = max(85, 650 * (0.84 ** (lines // 10)))
        if fall_timer >= interval:
            fall_timer = 0
            if not move(0, 1):
                lock()
    render()
