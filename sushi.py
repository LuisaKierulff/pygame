

import pygame

pygame.init()

WIDTH = 600
HEIGHT = 700


window = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Empilha Sushi")

BRANCO = (255, 255, 255)
ROSA = (255, 160, 180)
MARROM = (150, 90, 60)

game = True

SUSHI_WIDTH = 100
SUSHI_HEIGHT = 40

sushi_x = 0
sushi_y = 100

sushi_speedx = 3
sushi_speedy = 5

caindo = False
pousou = False

BASE_WIDTH = 150
BASE_HEIGHT = 20
base_x = (WIDTH - BASE_WIDTH) // 2
base_y = HEIGHT - 80

clock = pygame.time.Clock()
FPS = 60

while game:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            game = False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                if not caindo and not pousou:
                    caindo = True

    if not caindo and not pousou:
        sushi_x += sushi_speedx

        if sushi_x + SUSHI_WIDTH >= WIDTH:
            sushi_x = WIDTH - SUSHI_WIDTH
            sushi_speedx = -sushi_speedx

        if sushi_x <= 0:
            sushi_x = 0
            sushi_speedx = -sushi_speedx

    if caindo:
        sushi_y += sushi_speedy

        if sushi_y + SUSHI_HEIGHT >= base_y:
            sushi_y = base_y - SUSHI_HEIGHT
            caindo = False
            pousou = True

    window.fill(BRANCO)
    pygame.draw.rect(window,MARROM,(base_x, base_y, BASE_WIDTH, BASE_HEIGHT))
    pygame.draw.rect(window,ROSA,(sushi_x, sushi_y, SUSHI_WIDTH, SUSHI_HEIGHT))
    pygame.display.update()
    clock.tick(FPS)
pygame.quit()




