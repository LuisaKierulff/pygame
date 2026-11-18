
import math
import pygame

pygame.init()

WIDTH = 600
HEIGHT = 700


window = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Empilha Sushi")

BRANCO = (255, 255, 255)
ROSA = (255, 160, 180)
MARROM = (150, 90, 60)
MARROM_ESCURO = (105, 62, 40)
PRETO = (40, 40, 40)
VERDE = (80, 160, 100)
LARANJA = (255, 120, 80)
SALMAO = (255, 125, 85)
DOURADO = (240, 190, 60)

fonte_titulo = pygame.font.SysFont("arial", 68, bold=True)
fonte_grande = pygame.font.SysFont("arial", 44, bold=True)
fonte_texto = pygame.font.SysFont("arial", 30, bold=True)
fonte_pequena = pygame.font.SysFont("arial", 22, bold=True)

game = True
tela = "inicio"

SUSHI_WIDTH = 100
SUSHI_HEIGHT = 40

sushi_x = 0
sushi_y = 100

sushi_speedx = 3
sushi_speedy = 10

caindo = False

sushis_empilhados = []
pontos = 0
mensagem_fim = ""

BASE_WIDTH = 170
BASE_HEIGHT = 20
base_x = (WIDTH - BASE_WIDTH) // 2
base_y = HEIGHT - 80

clock = pygame.time.Clock()
FPS = 60
tempo = 0


def criar_fundo():
    fundo = pygame.Surface((WIDTH, HEIGHT))
    topo = (255, 226, 200)
    base = (255, 190, 175)
    for y in range(HEIGHT):
        k = y / HEIGHT
        cor = (
            int(topo[0] + (base[0] - topo[0]) * k),
            int(topo[1] + (base[1] - topo[1]) * k),
            int(topo[2] + (base[2] - topo[2]) * k),
        )
        pygame.draw.line(fundo, cor, (0, y), (WIDTH, y))
    pygame.draw.circle(fundo, (255, 150, 140), (460, 170), 70)
    return fundo


fundo = criar_fundo()


def texto(msg, fonte, cor, centro, sombra=None):
    img = fonte.render(msg, True, cor)
    rect = img.get_rect(center=centro)
    if sombra:
        sh = fonte.render(msg, True, sombra)
        window.blit(sh, (rect.x + 3, rect.y + 3))
    window.blit(img, rect)


def verificar_colisao(x1, largura1, x2, largura2):
    return x1 + largura1 > x2 and x1 < x2 + largura2


def desenhar_sushi(x, y):
    # arroz
    pygame.draw.ellipse(window, (248, 246, 238), (x + 4, y + 14, SUSHI_WIDTH - 8, SUSHI_HEIGHT - 14))
    pygame.draw.ellipse(window, (215, 212, 200), (x + 4, y + 14, SUSHI_WIDTH - 8, SUSHI_HEIGHT - 14), 2)
    # salmão por cima
    pygame.draw.ellipse(window, SALMAO, (x, y + 2, SUSHI_WIDTH, 25))
    pygame.draw.ellipse(window, (210, 90, 60), (x, y + 2, SUSHI_WIDTH, 25), 2)


def desenhar_base():
    pygame.draw.rect(window, MARROM, (base_x, base_y, BASE_WIDTH, BASE_HEIGHT), border_radius=8)
    pygame.draw.rect(window, MARROM_ESCURO, (base_x, base_y, BASE_WIDTH, BASE_HEIGHT), 3, border_radius=8)


def resetar_jogo():
    global sushi_x, sushi_y, sushi_speedx, caindo, sushis_empilhados, pontos, mensagem_fim
    sushi_x = 0
    sushi_y = 100
    sushi_speedx = 3
    caindo = False
    sushis_empilhados = []
    pontos = 0
    mensagem_fim = ""


while game:
    tempo += 1

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            game = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                if tela == "inicio" or tela == "fim":
                    resetar_jogo()
                    tela = "jogando"
                elif tela == "jogando" and not caindo:
                    caindo = True
            if event.key == pygame.K_ESCAPE:
                tela = "inicio"

    # ---------------------------------------------------- lógica
    if tela == "jogando" and not caindo:
        sushi_x += sushi_speedx

        if sushi_x + SUSHI_WIDTH >= WIDTH:
            sushi_x = WIDTH - SUSHI_WIDTH
            sushi_speedx = -sushi_speedx

        if sushi_x <= 0:
            sushi_x = 0
            sushi_speedx = -sushi_speedx

    if tela == "jogando" and caindo:
        sushi_y += sushi_speedy
        altura_pouso = base_y - SUSHI_HEIGHT

        if len(sushis_empilhados) > 0:
            ultimo_sushi = sushis_empilhados[-1]
            altura_pouso = ultimo_sushi[1] - SUSHI_HEIGHT

        if sushi_y >= altura_pouso:
            sushi_y = altura_pouso
            caindo = False

            if len(sushis_empilhados) == 0:
                acertou = verificar_colisao(sushi_x, SUSHI_WIDTH, base_x, BASE_WIDTH)
            else:
                ultimo_sushi = sushis_empilhados[-1]
                acertou = verificar_colisao(sushi_x, SUSHI_WIDTH, ultimo_sushi[0], SUSHI_WIDTH)

            if acertou:
                sushis_empilhados.append((sushi_x, sushi_y))
                pontos += 1

                # a cada 3 sushis o jogo fica mais rápido
                velocidade = min(9, 3 + (pontos // 3) * 0.4)
                if sushi_speedx > 0:
                    sushi_speedx = velocidade
                else:
                    sushi_speedx = -velocidade

                sushi_x = 0
                sushi_y = 100

                # ainda não temos câmera: se a torre chegar no topo, acabou
                if altura_pouso <= 170:
                    mensagem_fim = "A torre chegou ao topo!"
                    tela = "fim"
            else:
                mensagem_fim = "A pilha caiu!"
                tela = "fim"

    # ---------------------------------------------------- desenho
    window.blit(fundo, (0, 0))

    if tela == "inicio":
        texto("EMPILHA", fonte_titulo, MARROM, (WIDTH // 2, 80), BRANCO)
        texto("SUSHI", fonte_titulo, LARANJA, (WIDTH // 2, 145), BRANCO)

        for i in range(3):
            bob = math.sin(tempo * 0.07 + i * 1.3) * 7
            desenhar_sushi(WIDTH // 2 - 50 + (i - 1) * 150, 260 + bob)

        escala = 1 + 0.05 * math.sin(tempo * 0.12)
        img = fonte_texto.render("Aperte ESPAÇO para começar", True, MARROM_ESCURO)
        img = pygame.transform.rotozoom(img, 0, escala)
        window.blit(img, img.get_rect(center=(WIDTH // 2, 480)))
        texto("ESPAÇO solta o sushi  •  ESC volta ao menu", fonte_pequena, MARROM, (WIDTH // 2, 540))

    else:
        desenhar_base()

        for x, y in sushis_empilhados:
            desenhar_sushi(x, y)

        desenhar_sushi(sushi_x, sushi_y)

        texto("Pontos: " + str(pontos), fonte_texto, MARROM, (95, 28), BRANCO)

        if tela == "fim":
            veu = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            veu.fill((40, 20, 20, 150))
            window.blit(veu, (0, 0))
            texto(mensagem_fim, fonte_grande, BRANCO, (WIDTH // 2, 250), PRETO)
            texto("Pontos: " + str(pontos), fonte_grande, DOURADO, (WIDTH // 2, 320), PRETO)
            texto("ESPAÇO: jogar de novo", fonte_texto, BRANCO, (WIDTH // 2, 430), PRETO)
            texto("ESC: menu", fonte_pequena, BRANCO, (WIDTH // 2, 475), PRETO)

    pygame.display.update()
    clock.tick(FPS)

pygame.quit()
