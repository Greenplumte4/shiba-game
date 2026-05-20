import random
import pygame

pygame.init()

WIDTH, HEIGHT = 800, 500
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Shiba Bone Run")

clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 36)

SHIBA_SIZE = 45
BONE_SIZE = 25

shiba = pygame.Rect(100, 100, SHIBA_SIZE, SHIBA_SIZE)
bone = pygame.Rect(
    random.randint(50, WIDTH - 50),
    random.randint(50, HEIGHT - 50),
    BONE_SIZE,
    BONE_SIZE,
)

speed = 5
score = 0
running = True


def draw_shiba(rect):
    # body
    pygame.draw.rect(screen, (218, 139, 54), rect, border_radius=10)

    # face
    face = pygame.Rect(rect.x + 8, rect.y + 10, 29, 25)
    pygame.draw.rect(screen, (245, 210, 160), face, border_radius=8)

    # ears
    pygame.draw.polygon(
        screen,
        (160, 85, 35),
        [(rect.x + 5, rect.y + 5), (rect.x + 15, rect.y - 10), (rect.x + 22, rect.y + 8)],
    )
    pygame.draw.polygon(
        screen,
        (160, 85, 35),
        [(rect.x + 25, rect.y + 8), (rect.x + 32, rect.y - 10), (rect.x + 42, rect.y + 5)],
    )

    # eyes
    pygame.draw.circle(screen, (0, 0, 0), (rect.x + 17, rect.y + 22), 3)
    pygame.draw.circle(screen, (0, 0, 0), (rect.x + 30, rect.y + 22), 3)

    # nose
    pygame.draw.circle(screen, (0, 0, 0), (rect.x + 24, rect.y + 31), 3)


def draw_bone(rect):
    color = (245, 245, 220)
    pygame.draw.circle(screen, color, (rect.x, rect.y + 8), 8)
    pygame.draw.circle(screen, color, (rect.x, rect.y + 18), 8)
    pygame.draw.circle(screen, color, (rect.x + 25, rect.y + 8), 8)
    pygame.draw.circle(screen, color, (rect.x + 25, rect.y + 18), 8)
    pygame.draw.rect(screen, color, (rect.x, rect.y + 7, 25, 12), border_radius=6)


while running:
    clock.tick(60)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    keys = pygame.key.get_pressed()

    if keys[pygame.K_ESCAPE]:
        running = False

    if keys[pygame.K_LEFT] or keys[pygame.K_a]:
        shiba.x -= speed
    if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
        shiba.x += speed
    if keys[pygame.K_UP] or keys[pygame.K_w]:
        shiba.y -= speed
    if keys[pygame.K_DOWN] or keys[pygame.K_s]:
        shiba.y += speed

    shiba.x = max(0, min(WIDTH - SHIBA_SIZE, shiba.x))
    shiba.y = max(0, min(HEIGHT - SHIBA_SIZE, shiba.y))

    if shiba.colliderect(bone):
        score += 1
        bone.x = random.randint(40, WIDTH - 60)
        bone.y = random.randint(40, HEIGHT - 60)

    screen.fill((135, 206, 235))

    draw_bone(bone)
    draw_shiba(shiba)

    score_text = font.render(f"Score: {score}", True, (30, 30, 30))
    screen.blit(score_text, (20, 20))

    pygame.display.flip()

pygame.quit()