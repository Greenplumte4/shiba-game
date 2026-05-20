import array
import json
import math
import random
from pathlib import Path

import pygame

# =========================
# Pygame setup
# =========================

pygame.mixer.pre_init(44100, -16, 1, 512)
pygame.init()

WIDTH, HEIGHT = 800, 500
FPS = 60

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Shiba Bone Run - Version 5")
clock = pygame.time.Clock()

# =========================
# Paths
# =========================

BASE_DIR = Path(__file__).resolve().parent
ASSET_DIR = BASE_DIR / "assets"

# Prefer the transparent image folder created by make_transparent.py.
TRANSPARENT_IMAGE_DIR = ASSET_DIR / "images_transparent"
RAW_IMAGE_DIR = ASSET_DIR / "images"
IMAGE_DIR = TRANSPARENT_IMAGE_DIR if TRANSPARENT_IMAGE_DIR.exists() else RAW_IMAGE_DIR

SOUND_DIR = ASSET_DIR / "sounds"
SCORES_FILE = BASE_DIR / "scores.json"
OLD_HIGH_SCORE_FILE = BASE_DIR / "high_score.txt"

# =========================
# Fonts
# =========================

title_font = pygame.font.SysFont(None, 72)
big_font = pygame.font.SysFont(None, 48)
normal_font = pygame.font.SysFont(None, 32)
small_font = pygame.font.SysFont(None, 24)

# =========================
# Colors
# =========================

SKY_BLUE = (135, 206, 235)
GRASS_GREEN = (90, 190, 90)
SHIBA_ORANGE = (218, 139, 54)
SHIBA_DARK = (160, 85, 35)
CREAM = (245, 210, 160)
BONE_COLOR = (245, 245, 220)
GOLD = (255, 215, 0)
CAT_GRAY = (90, 90, 100)
CAT_DARK = (40, 40, 45)
BLACK = (30, 30, 30)
WHITE = (255, 255, 255)
RED = (220, 70, 70)
PINK = (255, 150, 170)
DARK_OVERLAY = (0, 0, 0, 135)

# =========================
# Game constants
# =========================

SHIBA_SIZE = 52
BONE_SIZE = 30
CAT_SIZE = 44
HEART_SIZE = 30

SHIBA_SPEED = 5
CAT_SPEED_MIN = 2
CAT_SPEED_MAX = 4

TIME_ATTACK_SECONDS = 60
MAX_HEALTH = 3
INVINCIBLE_TIME = 1200  # milliseconds
DIFFICULTY_STEP_SECONDS = 10
DIFFICULTY_SPEED_BONUS = 0.18
MAX_CATS = 8

HEART_SPAWN_CHANCE = 0.18
HEART_LIFETIME_MS = 9000
HEART_FULL_HEALTH_BONUS = 2

MODE_TIME_ATTACK = "time_attack"
MODE_ENDLESS = "endless"
MODE_LABELS = {
    MODE_TIME_ATTACK: "Time Attack",
    MODE_ENDLESS: "Endless",
}

# =========================
# Asset loading
# =========================

def load_image(filename, size=None):
    path = IMAGE_DIR / filename
    if not path.exists():
        return None

    try:
        image = pygame.image.load(str(path)).convert_alpha()
        if size is not None:
            image = pygame.transform.smoothscale(image, size)
        return image
    except pygame.error:
        return None


def load_sound(filename):
    path = SOUND_DIR / filename
    if not path.exists():
        return None

    try:
        return pygame.mixer.Sound(str(path))
    except pygame.error:
        return None


background_image = load_image("background.png", (WIDTH, HEIGHT))
shiba_frames = [
    load_image("shiba_1.png", (SHIBA_SIZE, SHIBA_SIZE)),
    load_image("shiba_2.png", (SHIBA_SIZE, SHIBA_SIZE)),
]
cat_image = load_image("cat.png", (CAT_SIZE, CAT_SIZE))
bone_image = load_image("bone.png", (BONE_SIZE + 6, BONE_SIZE))
golden_bone_image = load_image("golden_bone.png", (BONE_SIZE + 6, BONE_SIZE))
heart_image = load_image("heart.png", (HEART_SIZE, HEART_SIZE))

if shiba_frames[0] is not None and shiba_frames[1] is None:
    shiba_frames[1] = shiba_frames[0]
if shiba_frames[1] is not None and shiba_frames[0] is None:
    shiba_frames[0] = shiba_frames[1]

# =========================
# Sound system
# =========================

def make_tone(frequency, duration_ms, volume=0.3):
    """Create a simple beep sound without external sound files."""
    try:
        sample_rate = 44100
        sample_count = int(sample_rate * duration_ms / 1000)
        max_amplitude = int(32767 * volume)
        buffer = array.array("h")

        for i in range(sample_count):
            sample = int(max_amplitude * math.sin(2 * math.pi * frequency * i / sample_rate))
            buffer.append(sample)

        return pygame.mixer.Sound(buffer=buffer.tobytes())
    except Exception:
        return None


collect_sound = load_sound("collect.wav") or make_tone(660, 90, 0.25)
gold_sound = load_sound("gold.wav") or make_tone(880, 140, 0.3)
hit_sound = load_sound("hit.wav") or make_tone(180, 180, 0.35)
heal_sound = load_sound("heal.wav") or make_tone(520, 120, 0.3)
level_up_sound = load_sound("level_up.wav") or make_tone(980, 170, 0.25)
game_over_sound = load_sound("game_over.wav") or make_tone(140, 350, 0.35)

music_started = False


def try_start_music():
    global music_started
    if music_started:
        return

    for filename in ["bgm.mp3", "bgm.wav", "music.mp3", "music.wav"]:
        path = SOUND_DIR / filename
        if path.exists():
            try:
                pygame.mixer.music.load(str(path))
                pygame.mixer.music.set_volume(0.35)
                pygame.mixer.music.play(-1)
                music_started = True
                return
            except pygame.error:
                pass


def play_sound(sound):
    if sound is not None:
        try:
            sound.play()
        except pygame.error:
            pass

# =========================
# Score storage
# =========================

def load_scores():
    default_scores = {
        MODE_TIME_ATTACK: 0,
        MODE_ENDLESS: 0,
    }

    try:
        if SCORES_FILE.exists():
            data = json.loads(SCORES_FILE.read_text())
            return {
                MODE_TIME_ATTACK: int(data.get(MODE_TIME_ATTACK, 0)),
                MODE_ENDLESS: int(data.get(MODE_ENDLESS, 0)),
            }
    except (json.JSONDecodeError, ValueError, OSError):
        pass

    # Compatibility with Version 4's high_score.txt.
    try:
        if OLD_HIGH_SCORE_FILE.exists():
            default_scores[MODE_TIME_ATTACK] = int(OLD_HIGH_SCORE_FILE.read_text().strip())
    except (ValueError, OSError):
        pass

    return default_scores


def save_scores(scores):
    try:
        SCORES_FILE.write_text(json.dumps(scores, indent=2))
    except OSError:
        pass


scores = load_scores()

# =========================
# Drawing helpers
# =========================

def draw_text(text, font, color, x, y, center=True):
    surface = font.render(text, True, color)
    rect = surface.get_rect()
    if center:
        rect.center = (x, y)
    else:
        rect.topleft = (x, y)
    screen.blit(surface, rect)


def draw_background():
    if background_image is not None:
        screen.blit(background_image, (0, 0))
        return

    screen.fill(SKY_BLUE)
    pygame.draw.rect(screen, GRASS_GREEN, (0, HEIGHT - 70, WIDTH, 70))
    pygame.draw.circle(screen, (255, 230, 90), (710, 70), 35)

    pygame.draw.circle(screen, WHITE, (100, 80), 22)
    pygame.draw.circle(screen, WHITE, (125, 70), 28)
    pygame.draw.circle(screen, WHITE, (155, 80), 22)

    pygame.draw.circle(screen, WHITE, (420, 105), 20)
    pygame.draw.circle(screen, WHITE, (445, 95), 28)
    pygame.draw.circle(screen, WHITE, (475, 105), 20)

    for x in range(0, WIDTH, 40):
        pygame.draw.line(screen, (75, 160, 75), (x, HEIGHT - 70), (x + 15, HEIGHT - 95), 2)


def draw_overlay():
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill(DARK_OVERLAY)
    screen.blit(overlay, (0, 0))


def draw_shiba_fallback(rect, invincible=False, moving=False):
    now = pygame.time.get_ticks()
    if invincible and (now // 120) % 2 == 0:
        return

    bob = 2 if moving and (now // 160) % 2 == 0 else 0
    r = rect.move(0, -bob)

    pygame.draw.rect(screen, SHIBA_ORANGE, r, border_radius=12)
    face = pygame.Rect(r.x + 9, r.y + 13, 34, 28)
    pygame.draw.rect(screen, CREAM, face, border_radius=9)

    pygame.draw.polygon(screen, SHIBA_DARK, [(r.x + 5, r.y + 9), (r.x + 16, r.y - 12), (r.x + 25, r.y + 10)])
    pygame.draw.polygon(screen, SHIBA_DARK, [(r.x + 28, r.y + 10), (r.x + 38, r.y - 12), (r.x + 48, r.y + 9)])

    pygame.draw.circle(screen, BLACK, (r.x + 20, r.y + 27), 3)
    pygame.draw.circle(screen, BLACK, (r.x + 34, r.y + 27), 3)
    pygame.draw.circle(screen, BLACK, (r.x + 27, r.y + 36), 3)

    tail_angle = 0 if not moving else ((now // 150) % 2) * 4
    pygame.draw.circle(screen, SHIBA_ORANGE, (r.x + 54, r.y + 18 + tail_angle), 10, 4)


def draw_shiba(rect, invincible=False, moving=False):
    now = pygame.time.get_ticks()
    if invincible and (now // 120) % 2 == 0:
        return

    if shiba_frames[0] is not None and shiba_frames[1] is not None:
        frame_index = 0
        if moving:
            frame_index = (now // 160) % 2
        screen.blit(shiba_frames[frame_index], rect)
    else:
        draw_shiba_fallback(rect, invincible, moving)


def draw_bone_fallback(bone):
    rect = bone["rect"]
    x, y = rect.x, rect.y
    color = GOLD if bone["golden"] else BONE_COLOR

    pygame.draw.circle(screen, color, (x, y + 8), 8)
    pygame.draw.circle(screen, color, (x, y + 22), 8)
    pygame.draw.circle(screen, color, (x + 30, y + 8), 8)
    pygame.draw.circle(screen, color, (x + 30, y + 22), 8)
    pygame.draw.rect(screen, color, (x, y + 8, 30, 14), border_radius=7)

    if bone["golden"]:
        pygame.draw.circle(screen, WHITE, (x + 23, y + 8), 3)


def draw_bone(bone):
    image = golden_bone_image if bone["golden"] else bone_image
    if image is not None:
        screen.blit(image, bone["rect"])
    else:
        draw_bone_fallback(bone)


def draw_cat_fallback(cat):
    rect = cat["rect"]
    pygame.draw.rect(screen, CAT_GRAY, rect, border_radius=10)
    pygame.draw.polygon(screen, CAT_DARK, [(rect.x + 4, rect.y + 8), (rect.x + 12, rect.y - 10), (rect.x + 20, rect.y + 8)])
    pygame.draw.polygon(screen, CAT_DARK, [(rect.x + 24, rect.y + 8), (rect.x + 32, rect.y - 10), (rect.x + 40, rect.y + 8)])

    pygame.draw.circle(screen, WHITE, (rect.x + 16, rect.y + 21), 5)
    pygame.draw.circle(screen, WHITE, (rect.x + 30, rect.y + 21), 5)
    pygame.draw.circle(screen, BLACK, (rect.x + 16, rect.y + 21), 2)
    pygame.draw.circle(screen, BLACK, (rect.x + 30, rect.y + 21), 2)
    pygame.draw.circle(screen, PINK, (rect.x + 23, rect.y + 32), 3)
    pygame.draw.arc(screen, CAT_DARK, (rect.x + 34, rect.y + 6, 30, 30), 0, math.pi, 4)


def draw_cat(cat):
    if cat_image is not None:
        screen.blit(cat_image, cat["rect"])
    else:
        draw_cat_fallback(cat)


def draw_heart_shape(x, y, size, color):
    scale = size / 30
    left_center = (int(x + 9 * scale), int(y + 9 * scale))
    right_center = (int(x + 21 * scale), int(y + 9 * scale))
    radius = int(8 * scale)

    pygame.draw.circle(screen, color, left_center, radius)
    pygame.draw.circle(screen, color, right_center, radius)
    pygame.draw.polygon(
        screen,
        color,
        [
            (int(x + 1 * scale), int(y + 13 * scale)),
            (int(x + 29 * scale), int(y + 13 * scale)),
            (int(x + 15 * scale), int(y + 30 * scale)),
        ],
    )


def draw_pickup_heart(heart):
    if heart is None:
        return

    rect = heart["rect"]
    if heart_image is not None:
        screen.blit(heart_image, rect)
    else:
        draw_heart_shape(rect.x, rect.y, HEART_SIZE, RED)
        pygame.draw.circle(screen, WHITE, (rect.x + 21, rect.y + 7), 3)


def draw_health(health):
    for i in range(MAX_HEALTH):
        x = 20 + i * 35
        y = 60
        color = RED if i < health else (170, 170, 170)
        draw_heart_shape(x - 10, y - 10, 30, color)


def get_best_for_mode(mode):
    return scores.get(mode, 0)


def draw_hud(score, time_left, health, difficulty_level, mode, survival_seconds):
    draw_text(f"Score: {score}", normal_font, BLACK, 20, 20, center=False)
    draw_health(health)

    if mode == MODE_TIME_ATTACK:
        draw_text(f"Time: {time_left}", normal_font, BLACK, WIDTH - 135, 20, center=False)
    else:
        draw_text(f"Survive: {survival_seconds}s", normal_font, BLACK, WIDTH - 175, 20, center=False)

    draw_text(f"Best: {get_best_for_mode(mode)}", small_font, BLACK, WIDTH - 135, 55, center=False)
    draw_text(f"Lv {difficulty_level}", small_font, BLACK, WIDTH // 2, 25)
    draw_text(MODE_LABELS[mode], small_font, BLACK, WIDTH // 2, 52)

# =========================
# Game object helpers
# =========================

def random_play_area_rect(width, height):
    return pygame.Rect(
        random.randint(60, WIDTH - width - 60),
        random.randint(90, HEIGHT - height - 90),
        width,
        height,
    )


def create_random_bone():
    return {
        "rect": random_play_area_rect(BONE_SIZE, BONE_SIZE),
        "golden": random.random() < 0.22,
    }


def maybe_create_heart():
    if random.random() > HEART_SPAWN_CHANCE:
        return None

    return {
        "rect": random_play_area_rect(HEART_SIZE, HEART_SIZE),
        "spawn_time": pygame.time.get_ticks(),
    }


def create_cat():
    rect = pygame.Rect(
        random.randint(250, WIDTH - 90),
        random.randint(90, HEIGHT - 130),
        CAT_SIZE,
        CAT_SIZE,
    )

    speed_x = random.choice([-1, 1]) * random.randint(CAT_SPEED_MIN, CAT_SPEED_MAX)
    speed_y = random.choice([-1, 1]) * random.randint(CAT_SPEED_MIN, CAT_SPEED_MAX)

    return {
        "rect": rect,
        "vx": speed_x,
        "vy": speed_y,
    }


def create_cats(count):
    return [create_cat() for _ in range(count)]


def get_difficulty_level(mode, elapsed_seconds):
    if mode == MODE_TIME_ATTACK:
        # Time Attack grows more gently.
        return 1 + elapsed_seconds // 15
    return 1 + elapsed_seconds // DIFFICULTY_STEP_SECONDS


def get_target_cat_count(mode, difficulty_level):
    if mode == MODE_TIME_ATTACK:
        return min(3 + difficulty_level // 3, 5)
    return min(3 + difficulty_level // 2, MAX_CATS)


def sync_cat_count(cats, mode, difficulty_level):
    target_count = get_target_cat_count(mode, difficulty_level)
    while len(cats) < target_count:
        cats.append(create_cat())


def update_cats(cats, difficulty_level):
    speed_multiplier = 1 + (difficulty_level - 1) * DIFFICULTY_SPEED_BONUS

    for cat in cats:
        rect = cat["rect"]
        rect.x += int(cat["vx"] * speed_multiplier)
        rect.y += int(cat["vy"] * speed_multiplier)

        if rect.left <= 0:
            rect.left = 0
            cat["vx"] *= -1
        elif rect.right >= WIDTH:
            rect.right = WIDTH
            cat["vx"] *= -1

        if rect.top <= 70:
            rect.top = 70
            cat["vy"] *= -1
        elif rect.bottom >= HEIGHT - 70:
            rect.bottom = HEIGHT - 70
            cat["vy"] *= -1


def calculate_final_score(mode, score, survival_seconds):
    if mode == MODE_ENDLESS:
        return score + survival_seconds // 5
    return score


def reset_game(mode):
    shiba = pygame.Rect(100, HEIGHT - 140, SHIBA_SIZE, SHIBA_SIZE)
    bone = create_random_bone()
    heart = None
    cats = create_cats(3)
    score = 0
    health = MAX_HEALTH
    start_ticks = pygame.time.get_ticks()
    last_hit_time = -INVINCIBLE_TIME
    last_level = 1
    return shiba, bone, heart, cats, score, health, start_ticks, last_hit_time, last_level

# =========================
# Game state
# =========================

START = "start"
PLAYING = "playing"
PAUSED = "paused"
GAME_OVER = "game_over"

game_state = START
current_mode = MODE_TIME_ATTACK
shiba, bone, heart, cats, score, health, start_ticks, last_hit_time, last_level = reset_game(current_mode)

pause_start_ticks = 0
final_reason = ""
final_score = 0
last_score_was_record = False
game_over_sound_played = False
running = True

# =========================
# Main loop
# =========================

while running:
    clock.tick(FPS)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False

            if game_state == START:
                if event.key in (pygame.K_1, pygame.K_KP1):
                    try_start_music()
                    current_mode = MODE_TIME_ATTACK
                    shiba, bone, heart, cats, score, health, start_ticks, last_hit_time, last_level = reset_game(current_mode)
                    final_reason = ""
                    final_score = 0
                    last_score_was_record = False
                    game_over_sound_played = False
                    game_state = PLAYING

                elif event.key in (pygame.K_2, pygame.K_KP2):
                    try_start_music()
                    current_mode = MODE_ENDLESS
                    shiba, bone, heart, cats, score, health, start_ticks, last_hit_time, last_level = reset_game(current_mode)
                    final_reason = ""
                    final_score = 0
                    last_score_was_record = False
                    game_over_sound_played = False
                    game_state = PLAYING

            elif game_state == PLAYING:
                if event.key == pygame.K_p:
                    pause_start_ticks = pygame.time.get_ticks()
                    game_state = PAUSED

            elif game_state == PAUSED:
                if event.key == pygame.K_p:
                    start_ticks += pygame.time.get_ticks() - pause_start_ticks
                    game_state = PLAYING

            elif game_state == GAME_OVER:
                if event.key == pygame.K_r:
                    shiba, bone, heart, cats, score, health, start_ticks, last_hit_time, last_level = reset_game(current_mode)
                    final_reason = ""
                    final_score = 0
                    last_score_was_record = False
                    game_over_sound_played = False
                    game_state = PLAYING
                elif event.key == pygame.K_SPACE:
                    game_state = START

    # -------------------------
    # Start screen
    # -------------------------

    if game_state == START:
        draw_background()
        draw_overlay()
        draw_text("SHIBA BONE RUN", title_font, WHITE, WIDTH // 2, 85)
        draw_text("Version 5", normal_font, WHITE, WIDTH // 2, 140)

        draw_text("Choose a mode", big_font, WHITE, WIDTH // 2, 200)
        draw_text("Press 1: Time Attack - 60 seconds to score as much as possible", normal_font, WHITE, WIDTH // 2, 255)
        draw_text("Press 2: Endless - no timer, survive as long as you can", normal_font, WHITE, WIDTH // 2, 295)
        draw_text("Heart pickup: restore 1 heart, or +2 score when full", normal_font, WHITE, WIDTH // 2, 335)
        draw_text("WASD / Arrow Keys: Move    P: Pause    ESC: Quit", normal_font, WHITE, WIDTH // 2, 385)

        draw_text(f"Best Time Attack: {scores[MODE_TIME_ATTACK]}", small_font, WHITE, WIDTH // 2, 435)
        draw_text(f"Best Endless: {scores[MODE_ENDLESS]}", small_font, WHITE, WIDTH // 2, 462)
        pygame.display.flip()
        continue

    # -------------------------
    # Playing
    # -------------------------

    if game_state == PLAYING:
        keys = pygame.key.get_pressed()
        moving = False

        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            shiba.x -= SHIBA_SPEED
            moving = True
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            shiba.x += SHIBA_SPEED
            moving = True
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            shiba.y -= SHIBA_SPEED
            moving = True
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            shiba.y += SHIBA_SPEED
            moving = True

        shiba.x = max(0, min(WIDTH - SHIBA_SIZE, shiba.x))
        shiba.y = max(0, min(HEIGHT - SHIBA_SIZE, shiba.y))

        elapsed_seconds = (pygame.time.get_ticks() - start_ticks) // 1000
        survival_seconds = elapsed_seconds
        time_left = max(0, TIME_ATTACK_SECONDS - elapsed_seconds)
        difficulty_level = get_difficulty_level(current_mode, elapsed_seconds)

        if difficulty_level > last_level:
            last_level = difficulty_level
            play_sound(level_up_sound)

        sync_cat_count(cats, current_mode, difficulty_level)
        update_cats(cats, difficulty_level)

        # Heart expires if not collected.
        if heart is not None:
            if pygame.time.get_ticks() - heart["spawn_time"] > HEART_LIFETIME_MS:
                heart = None

        # Collect bone.
        if shiba.colliderect(bone["rect"]):
            if bone["golden"]:
                score += 3
                play_sound(gold_sound)
            else:
                score += 1
                play_sound(collect_sound)

            bone = create_random_bone()

            # Hearts appear after collecting bones, so players have a reason to keep moving.
            if heart is None:
                heart = maybe_create_heart()

        # Collect heart.
        if heart is not None and shiba.colliderect(heart["rect"]):
            if health < MAX_HEALTH:
                health += 1
            else:
                score += HEART_FULL_HEALTH_BONUS
            heart = None
            play_sound(heal_sound)

        # Cat collision.
        now = pygame.time.get_ticks()
        is_invincible = now - last_hit_time < INVINCIBLE_TIME

        if not is_invincible:
            for cat in cats:
                if shiba.colliderect(cat["rect"]):
                    health -= 1
                    last_hit_time = now
                    play_sound(hit_sound)
                    shiba.x = max(0, shiba.x - 45)

                    if health <= 0:
                        final_reason = "The cats caught the Shiba!"
                        game_state = GAME_OVER
                    break

        # Mode-specific ending.
        if current_mode == MODE_TIME_ATTACK and time_left <= 0:
            final_reason = "Time is up!"
            game_state = GAME_OVER

        if game_state == GAME_OVER:
            final_score = calculate_final_score(current_mode, score, survival_seconds)
            if final_score > scores[current_mode]:
                scores[current_mode] = final_score
                save_scores(scores)
                last_score_was_record = True
            if not game_over_sound_played:
                play_sound(game_over_sound)
                game_over_sound_played = True

        draw_background()
        draw_bone(bone)
        draw_pickup_heart(heart)
        for cat in cats:
            draw_cat(cat)

        is_invincible = pygame.time.get_ticks() - last_hit_time < INVINCIBLE_TIME
        draw_shiba(shiba, invincible=is_invincible, moving=moving)
        draw_hud(score, time_left, health, difficulty_level, current_mode, survival_seconds)

        if bone["golden"]:
            draw_text("Golden Bone!", small_font, BLACK, WIDTH // 2, 78)
        if heart is not None:
            draw_text("Heart spawned!", small_font, RED, WIDTH // 2, 103)

        pygame.display.flip()
        continue

    # -------------------------
    # Pause screen
    # -------------------------

    if game_state == PAUSED:
        elapsed_seconds = (pygame.time.get_ticks() - start_ticks) // 1000
        time_left = max(0, TIME_ATTACK_SECONDS - elapsed_seconds)
        difficulty_level = get_difficulty_level(current_mode, elapsed_seconds)

        draw_background()
        draw_bone(bone)
        draw_pickup_heart(heart)
        for cat in cats:
            draw_cat(cat)
        draw_shiba(shiba)
        draw_hud(score, time_left, health, difficulty_level, current_mode, elapsed_seconds)
        draw_overlay()
        draw_text("PAUSED", title_font, WHITE, WIDTH // 2, 180)
        draw_text("Press P to resume", big_font, WHITE, WIDTH // 2, 260)
        draw_text("Press ESC to quit", normal_font, WHITE, WIDTH // 2, 325)
        pygame.display.flip()
        continue

    # -------------------------
    # Game over screen
    # -------------------------

    if game_state == GAME_OVER:
        draw_background()
        draw_overlay()
        draw_text("GAME OVER", title_font, RED, WIDTH // 2, 80)
        draw_text(MODE_LABELS[current_mode], normal_font, WHITE, WIDTH // 2, 140)
        draw_text(f"Final Score: {final_score}", big_font, WHITE, WIDTH // 2, 200)
        draw_text(f"Best Score: {scores[current_mode]}", normal_font, WHITE, WIDTH // 2, 250)

        if current_mode == MODE_ENDLESS:
            draw_text("Endless score includes survival bonus: +1 every 5 seconds", small_font, WHITE, WIDTH // 2, 285)

        if last_score_was_record:
            draw_text("New High Score!", big_font, GOLD, WIDTH // 2, 330)
        else:
            draw_text(final_reason, normal_font, WHITE, WIDTH // 2, 330)

        draw_text("Press R to restart this mode", big_font, WHITE, WIDTH // 2, 390)
        draw_text("Press SPACE for mode select", normal_font, WHITE, WIDTH // 2, 435)
        draw_text("Press ESC to quit", small_font, WHITE, WIDTH // 2, 465)
        pygame.display.flip()

pygame.quit()
