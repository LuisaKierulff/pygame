

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
    sushi_x += sushi_speedx

    if sushi_x + SUSHI_WIDTH >= WIDTH:
        sushi_x = WIDTH - SUSHI_WIDTH
        sushi_speedx = -sushi_speedx

    if sushi_x <= 0:
        sushi_x = 0
        sushi_speedx = -sushi_speedx

    window.fill(BRANCO)
    pygame.draw.rect(window,MARROM,(base_x, base_y, BASE_WIDTH, BASE_HEIGHT))
    pygame.draw.rect(window,ROSA,(sushi_x, sushi_y, SUSHI_WIDTH, SUSHI_HEIGHT))
    pygame.display.update()
    clock.tick(FPS)
pygame.quit()


