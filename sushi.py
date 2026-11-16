

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

sushis_empilhados = []
pontos = 0

BASE_WIDTH = 150
BASE_HEIGHT = 20
base_x = (WIDTH - BASE_WIDTH) // 2
base_y = HEIGHT - 80

clock = pygame.time.Clock()
FPS = 60

def verificar_colisao(x1, largura1, x2, largura2):
    return x1 + largura1 > x2 and x1 < x2 + largura2

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
        altura_pouso = base_y - SUSHI_HEIGHT

        if len(sushis_empilhados) > 0:
            ultimo_sushi = sushis_empilhados[-1]
            altura_pouso = ultimo_sushi[1] - SUSHI_HEIGHT

        if sushi_y >= altura_pouso:
            sushi_y = altura_pouso
            caindo = False

            if len(sushis_empilhados) == 0:
                acertou = verificar_colisao(
                    sushi_x, SUSHI_WIDTH,
                    base_x, BASE_WIDTH
                )

            else:
                ultimo_sushi = sushis_empilhados[-1]
                acertou = verificar_colisao(
                    sushi_x, SUSHI_WIDTH,
                    ultimo_sushi[0], SUSHI_WIDTH
                )

            if acertou:

                sushis_empilhados.append((sushi_x, sushi_y))

                pontos += 1

                sushi_x = 0
                sushi_y = 100
                pousou = False

            else:
                pousou = True
                game = False

    if pousou:

        if sushi_x + SUSHI_WIDTH > base_x and sushi_x < base_x + BASE_WIDTH:
            pass

        else:
            pousou = False
            sushi_y += sushi_speedy

    for x, y in sushis_empilhados:
        pygame.draw.rect(
            window,
            ROSA,
            (x, y, SUSHI_WIDTH, SUSHI_HEIGHT)
        )

    window.fill(BRANCO)
    pygame.draw.rect(window,MARROM,(base_x, base_y, BASE_WIDTH, BASE_HEIGHT))
    for x, y in sushis_empilhados:
        pygame.draw.rect(window,ROSA,(x, y, SUSHI_WIDTH, SUSHI_HEIGHT))
    pygame.draw.rect(window,ROSA,(sushi_x, sushi_y, SUSHI_WIDTH, SUSHI_HEIGHT))
    pygame.display.update()
    clock.tick(FPS)
pygame.quit()




