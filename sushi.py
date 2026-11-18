import json
import math
import os
import random

import pygame

pygame.init()

# =====================================================================
#  CONFIGURAÇÕES (mexa aqui para ajustar o equilíbrio do jogo)
# =====================================================================
WIDTH, HEIGHT = 600, 700
FPS = 60

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ARQUIVO_SCORES = os.path.join(BASE_DIR, "highscores.json")

SUSHI_WIDTH, SUSHI_HEIGHT = 100, 40
BASE_WIDTH, BASE_HEIGHT = 170, 24
BASE_X = (WIDTH - BASE_WIDTH) // 2
BASE_Y = HEIGHT - 80

SPAWN_Y = 100            # altura (na tela) de onde o sushi sai
ALVO_TOPO_TELA = 360     # altura (na tela) em que o topo da pilha é mantido

VEL_X_INICIAL = 3.0      # velocidade horizontal inicial
VEL_X_MAX = 9.0          # velocidade horizontal máxima
AUMENTO_VEL = 0.35       # quanto acelera a cada "nível"
SUSHIS_POR_NIVEL = 3     # a cada quantos sushis sobe de nível
VEL_QUEDA = 14           # velocidade de queda do sushi solto

PERFEITO_PX = 7          # distância do centro (px) para contar "perfeito"
PONTOS_NORMAL = 1
PONTOS_PERFEITO = 3
TOLERANCIA = 0           # folga (px) na regra de equilíbrio; >0 = mais fácil
MAX_SCORES = 5           # quantos high scores guardar

# Cores
BRANCO = (255, 255, 255)
ROSA = (255, 160, 180)
MARROM = (150, 90, 60)
MARROM_ESCURO = (105, 62, 40)
PRETO = (40, 40, 40)
VERDE = (80, 160, 100)
LARANJA = (255, 120, 80)
DOURADO = (240, 190, 60)

window = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Empilha Sushi")

fonte_titulo = pygame.font.SysFont("arial", 68, bold=True)
fonte_grande = pygame.font.SysFont("arial", 44, bold=True)
fonte_texto = pygame.font.SysFont("arial", 30, bold=True)
fonte_pequena = pygame.font.SysFont("arial", 22, bold=True)


# =====================================================================
#  SPRITES
# =====================================================================
def criar_sushi(cor_peixe, cor_borda):
    s = pygame.Surface((SUSHI_WIDTH, SUSHI_HEIGHT), pygame.SRCALPHA)
    pygame.draw.ellipse(s, (248, 246, 238), (4, 14, SUSHI_WIDTH - 8, SUSHI_HEIGHT - 14))
    pygame.draw.ellipse(s, (215, 212, 200), (4, 14, SUSHI_WIDTH - 8, SUSHI_HEIGHT - 14), 2)
    pygame.draw.ellipse(s, cor_peixe, (0, 2, SUSHI_WIDTH, 25))
    pygame.draw.ellipse(s, cor_borda, (0, 2, SUSHI_WIDTH, 25), 2)
    return s


SUSHI_SPRITES = [
    criar_sushi((255, 125, 85), (210, 90, 60)),     # salmão
    criar_sushi((255, 205, 80), (220, 165, 50)),    # tamago
    criar_sushi((255, 190, 190), (225, 140, 140)),  # camarão
]


def criar_fundo():
    s = pygame.Surface((WIDTH, HEIGHT))
    topo, base = (255, 226, 200), (255, 190, 175)
    for y in range(HEIGHT):
        k = y / HEIGHT
        cor = tuple(int(topo[i] + (base[i] - topo[i]) * k) for i in range(3))
        pygame.draw.line(s, cor, (0, y), (WIDTH, y))
    pygame.draw.circle(s, (255, 150, 140), (460, 170), 70)  # solzinho
    # ondas (seigaiha) no rodapé
    for fila in range(3):
        for col in range(-1, 9):
            cx = col * 80 + (40 if fila % 2 else 0)
            cy = HEIGHT - 30 + fila * 22
            for r, cor in ((40, (230, 150, 150)), (28, (255, 190, 175)), (16, (230, 150, 150))):
                pygame.draw.circle(s, cor, (cx, cy), r, 3)
    return s


def criar_base():
    s = pygame.Surface((BASE_WIDTH, BASE_HEIGHT), pygame.SRCALPHA)
    pygame.draw.rect(s, MARROM, (0, 0, BASE_WIDTH, BASE_HEIGHT), border_radius=8)
    pygame.draw.rect(s, MARROM_ESCURO, (0, 0, BASE_WIDTH, BASE_HEIGHT), 3, border_radius=8)
    for x in range(20, BASE_WIDTH - 10, 38):
        pygame.draw.line(s, MARROM_ESCURO, (x, 5), (x, BASE_HEIGHT - 6), 2)
    return s


FUNDO = criar_fundo()
BASE_IMG = criar_base()


# =====================================================================
#  HIGH SCORES
# =====================================================================
def carregar_scores():
    try:
        with open(ARQUIVO_SCORES, "r", encoding="utf-8") as f:
            dados = json.load(f)
        scores = [int(x) for x in dados if isinstance(x, (int, float))]
        return sorted(scores, reverse=True)[:MAX_SCORES]
    except (OSError, ValueError, TypeError):
        return []


def salvar_scores(scores):
    try:
        with open(ARQUIVO_SCORES, "w", encoding="utf-8") as f:
            json.dump(scores, f)
    except OSError:
        pass


# =====================================================================
#  REGRAS DE EQUILÍBRIO
#  Cada sushi da pilha precisa que o CENTRO DE MASSA de tudo que está
#  em cima dele (ele incluso) fique sobre o sushi (ou a base) de baixo.
#  Se isso falhar em algum nível, a pilha desaba a partir dali.
# =====================================================================
def analisar_pilha(pilha):
    """Retorna (falha, pior_razao).
    falha = (indice, deslocamento) do primeiro nível instável, ou None.
    pior_razao = 0..1+ ; acima de 1 a pilha cai."""
    falha = None
    pior = 0.0
    for i in range(len(pilha)):
        if i == 0:
            apoio_x, apoio_larg = BASE_X, BASE_WIDTH
        else:
            apoio_x, apoio_larg = pilha[i - 1]["x"], SUSHI_WIDTH
        grupo = pilha[i:]
        com = sum(p["x"] + SUSHI_WIDTH / 2 for p in grupo) / len(grupo)
        centro_apoio = apoio_x + apoio_larg / 2
        razao = abs(com - centro_apoio) / (apoio_larg / 2 + TOLERANCIA)
        pior = max(pior, razao)
        if razao > 1 and falha is None:
            falha = (i, com - centro_apoio)
    return falha, pior


def texto(superf, msg, fonte, cor, centro=None, topleft=None, sombra=None):
    img = fonte.render(msg, True, cor)
    rect = img.get_rect()
    if centro:
        rect.center = centro
    else:
        rect.topleft = topleft
    if sombra:
        sh = fonte.render(msg, True, sombra)
        superf.blit(sh, (rect.x + 3, rect.y + 3))
    superf.blit(img, rect)
    return rect


# =====================================================================
#  JOGO
# =====================================================================
class Jogo:
    def __init__(self):
        self.scores = carregar_scores()
        self.tela = "inicio"
        self.t = 0
        self.resetar()

    def resetar(self):
        self.pilha = []          # cada item: {"x", "y" (mundo), "tipo"}
        self.detritos = []
        self.popups = []
        self.pontos = 0
        self.camera = 0.0
        self.vel_x = VEL_X_INICIAL
        self.instabilidade = 0.0
        self.timer_queda = 0
        self.novo_recorde = False
        self.novo_sushi()

    def novo_sushi(self):
        self.caindo = False
        self.sushi_tipo = random.randrange(len(SUSHI_SPRITES))
        self.sushi_y = SPAWN_Y
        if random.random() < 0.5:
            self.sushi_x, self.direcao = 0.0, 1
        else:
            self.sushi_x, self.direcao = float(WIDTH - SUSHI_WIDTH), -1

    # ---------------------------------------------------------- entrada
    def tecla(self, key):
        if key == pygame.K_SPACE:
            if self.tela in ("inicio", "gameover"):
                self.resetar()
                self.tela = "jogando"
            elif self.tela == "jogando" and not self.caindo:
                self.caindo = True
        elif key == pygame.K_ESCAPE and self.tela != "inicio":
            self.tela = "inicio"

    # --------------------------------------------------------- lógica
    def topo_pilha_mundo(self):
        return self.pilha[-1]["y"] if self.pilha else BASE_Y

    def atualizar_camera(self):
        alvo = max(0.0, ALVO_TOPO_TELA - self.topo_pilha_mundo())
        self.camera += (alvo - self.camera) * 0.08

    def update(self):
        self.t += 1
        if self.tela == "jogando":
            self.atualizar_camera()
            self.instabilidade += (self.instab_alvo() - self.instabilidade) * 0.1
            if not self.caindo:
                self.sushi_x += self.direcao * self.vel_x
                if self.sushi_x + SUSHI_WIDTH >= WIDTH:
                    self.sushi_x = WIDTH - SUSHI_WIDTH
                    self.direcao = -1
                elif self.sushi_x <= 0:
                    self.sushi_x = 0
                    self.direcao = 1
            else:
                self.sushi_y += VEL_QUEDA
                y_pouso = self.topo_pilha_mundo() - SUSHI_HEIGHT
                if self.sushi_y >= y_pouso + self.camera:
                    self.pousar(y_pouso)
        elif self.tela == "queda":
            self.atualizar_camera()
            self.timer_queda += 1
            for d in self.detritos:
                d["vy"] += 0.6
                d["x"] += d["vx"]
                d["y"] += d["vy"]
                d["ang"] += d["vang"]
            fora = all(d["y"] + self.camera > HEIGHT + 80 for d in self.detritos)
            if fora or self.timer_queda > 170:
                self.fim_de_jogo()
        self.atualizar_popups()

    def instab_alvo(self):
        return analisar_pilha(self.pilha)[1] if self.pilha else 0.0

    def pousar(self, y_mundo):
        if self.pilha:
            apoio_x, apoio_larg = self.pilha[-1]["x"], SUSHI_WIDTH
        else:
            apoio_x, apoio_larg = BASE_X, BASE_WIDTH

        x = self.sushi_x
        sobreposicao = min(x + SUSHI_WIDTH, apoio_x + apoio_larg) - max(x, apoio_x)
        if sobreposicao <= 0:
            # errou completamente: o sushi passa direto
            lado = 1 if x + SUSHI_WIDTH / 2 > apoio_x + apoio_larg / 2 else -1
            self.criar_detrito(x, y_mundo, self.sushi_tipo, lado, 1.0)
            self.iniciar_queda()
            return

        # "Perfeito": encaixa no centro e vale mais
        offset = abs((x + SUSHI_WIDTH / 2) - (apoio_x + apoio_larg / 2))
        if offset <= PERFEITO_PX:
            x = apoio_x + apoio_larg / 2 - SUSHI_WIDTH / 2
            self.pontos += PONTOS_PERFEITO
            self.novo_popup("PERFEITO! +%d" % PONTOS_PERFEITO, x + SUSHI_WIDTH / 2, y_mundo, DOURADO)
        else:
            self.pontos += PONTOS_NORMAL
            self.novo_popup("+%d" % PONTOS_NORMAL, x + SUSHI_WIDTH / 2, y_mundo, BRANCO)

        self.pilha.append({"x": x, "y": y_mundo, "tipo": self.sushi_tipo})

        falha, _ = analisar_pilha(self.pilha)
        if falha is not None:
            indice, desloc = falha
            lado = 1 if desloc > 0 else -1
            for p in self.pilha[indice:]:
                self.criar_detrito(p["x"], p["y"], p["tipo"], lado, random.uniform(0.7, 1.3))
            self.pilha = self.pilha[:indice]
            self.iniciar_queda()
            return

        # sobreviveu: acelera a cada nível e solta o próximo
        nivel = len(self.pilha) // SUSHIS_POR_NIVEL
        self.vel_x = min(VEL_X_MAX, VEL_X_INICIAL + nivel * AUMENTO_VEL)
        self.novo_sushi()

    def criar_detrito(self, x, y, tipo, lado, forca):
        self.detritos.append({
            "x": x, "y": y, "tipo": tipo,
            "vx": lado * (1.5 + random.random() * 2.5) * forca,
            "vy": -random.random() * 4,
            "ang": 0.0,
            "vang": -lado * random.uniform(2, 5),
        })

    def iniciar_queda(self):
        self.tela = "queda"
        self.timer_queda = 0
        self.caindo = False

    def fim_de_jogo(self):
        melhor_anterior = self.scores[0] if self.scores else 0
        if self.pontos > 0:
            self.scores.append(self.pontos)
            self.scores = sorted(self.scores, reverse=True)[:MAX_SCORES]
            salvar_scores(self.scores)
            self.novo_recorde = self.pontos > melhor_anterior
        self.tela = "gameover"

    # ---------------------------------------------------------- popups
    def novo_popup(self, msg, x_mundo, y_mundo, cor):
        self.popups.append({"msg": msg, "x": x_mundo, "y": y_mundo, "cor": cor, "vida": 50})

    def atualizar_popups(self):
        for p in self.popups:
            p["vida"] -= 1
            p["y"] -= 1.2
        self.popups = [p for p in self.popups if p["vida"] > 0]

    # ---------------------------------------------------------- desenho
    def draw(self):
        window.blit(FUNDO, (0, 0))
        if self.tela == "inicio":
            self.draw_inicio()
        else:
            self.draw_jogo()
            if self.tela == "gameover":
                self.draw_gameover()
        pygame.display.update()

    def draw_painel_scores(self, topo, altura, titulo):
        painel = pygame.Surface((300, altura), pygame.SRCALPHA)
        pygame.draw.rect(painel, (255, 255, 255, 170), painel.get_rect(), border_radius=18)
        pygame.draw.rect(painel, (*MARROM, 255), painel.get_rect(), 3, border_radius=18)
        window.blit(painel, ((WIDTH - 300) // 2, topo))
        texto(window, titulo, fonte_texto, MARROM, centro=(WIDTH // 2, topo + 28))
        for i in range(MAX_SCORES):
            y = topo + 64 + i * 34
            if i < len(self.scores):
                cor = DOURADO if i == 0 else PRETO
                texto(window, f"{i + 1}.", fonte_texto, cor, topleft=(WIDTH // 2 - 110, y - 12))
                s = fonte_texto.render(str(self.scores[i]), True, cor)
                window.blit(s, (WIDTH // 2 + 110 - s.get_width(), y - 12))
            else:
                texto(window, f"{i + 1}.  ---", fonte_texto, (170, 150, 140), topleft=(WIDTH // 2 - 110, y - 12))

    def draw_inicio(self):
        texto(window, "EMPILHA", fonte_titulo, MARROM, centro=(WIDTH // 2, 70), sombra=(255, 255, 255))
        texto(window, "SUSHI", fonte_titulo, LARANJA, centro=(WIDTH // 2, 135), sombra=(255, 255, 255))

        # sushis "flutuando"
        for i in range(3):
            bob = math.sin(self.t * 0.07 + i * 1.3) * 7
            window.blit(SUSHI_SPRITES[i], (WIDTH // 2 - 50 + (i - 1) * 150, 205 + bob))

        # high score
        self.draw_painel_scores(270, 250, "HIGH SCORE")

        # chamada piscando
        escala = 1 + 0.05 * math.sin(self.t * 0.12)
        img = fonte_texto.render("Aperte ESPAÇO para começar", True, MARROM_ESCURO)
        img = pygame.transform.rotozoom(img, 0, escala)
        window.blit(img, img.get_rect(center=(WIDTH // 2, 575)))
        texto(window, "ESPAÇO solta o sushi  •  ESC volta ao menu", fonte_pequena, MARROM, centro=(WIDTH // 2, 625))

    def draw_jogo(self):
        cam = int(self.camera)
        # base
        by = BASE_Y + cam
        if by < HEIGHT + 40:
            window.blit(BASE_IMG, (BASE_X, by))

        # pilha (balança conforme a instabilidade)
        amp = min(self.instabilidade, 1.0) ** 2 * 9
        n = max(len(self.pilha), 1)
        for i, p in enumerate(self.pilha):
            sway = math.sin(self.t * 0.15) * amp * (i + 1) / n
            y = p["y"] + cam
            if -SUSHI_HEIGHT < y < HEIGHT:
                window.blit(SUSHI_SPRITES[p["tipo"]], (p["x"] + sway, y))

        # detritos girando
        for d in self.detritos:
            rot = pygame.transform.rotate(SUSHI_SPRITES[d["tipo"]], d["ang"])
            rect = rot.get_rect(center=(d["x"] + SUSHI_WIDTH / 2, d["y"] + SUSHI_HEIGHT / 2 + cam))
            window.blit(rot, rect)

        # sushi atual
        if self.tela == "jogando":
            window.blit(SUSHI_SPRITES[self.sushi_tipo], (self.sushi_x, self.sushi_y))

        # popups
        for p in self.popups:
            img = fonte_texto.render(p["msg"], True, p["cor"])
            sh = fonte_texto.render(p["msg"], True, PRETO)
            alpha = max(0, min(255, p["vida"] * 8))
            img.set_alpha(alpha)
            sh.set_alpha(alpha)
            pos = (p["x"] - img.get_width() / 2, p["y"] + cam - 30)
            window.blit(sh, (pos[0] + 2, pos[1] + 2))
            window.blit(img, pos)

        # HUD
        texto(window, f"Pontos: {self.pontos}", fonte_texto, MARROM, topleft=(15, 12), sombra=(255, 255, 255))
        melhor = max([self.pontos] + self.scores)
        s = fonte_pequena.render(f"Recorde: {melhor}", True, MARROM_ESCURO)
        window.blit(s, (WIDTH - s.get_width() - 15, 18))
        self.draw_barra_equilibrio()

    def draw_barra_equilibrio(self):
        x, y, w, h = 15, 52, 150, 14
        pygame.draw.rect(window, (255, 255, 255), (x, y, w, h), border_radius=7)
        risco = min(self.instabilidade, 1.0)
        cor = (int(80 + 135 * risco), int(170 - 100 * risco), 90)
        pygame.draw.rect(window, cor, (x, y, max(6, int(w * risco)), h), border_radius=7)
        pygame.draw.rect(window, MARROM, (x, y, w, h), 2, border_radius=7)
        texto(window, "Instabilidade", fonte_pequena, MARROM, topleft=(x + w + 8, y - 3))

    def draw_gameover(self):
        veu = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        veu.fill((40, 20, 20, 150))
        window.blit(veu, (0, 0))
        texto(window, "A PILHA CAIU!", fonte_grande, BRANCO, centro=(WIDTH // 2, 120), sombra=PRETO)
        texto(window, f"Pontos: {self.pontos}", fonte_grande, DOURADO, centro=(WIDTH // 2, 180), sombra=PRETO)
        if self.novo_recorde:
            texto(window, "NOVO RECORDE!", fonte_texto, ROSA, centro=(WIDTH // 2, 225), sombra=PRETO)
        self.draw_painel_scores(260, 250, "HIGH SCORE")
        texto(window, "ESPAÇO: jogar de novo", fonte_texto, BRANCO, centro=(WIDTH // 2, 575), sombra=PRETO)
        texto(window, "ESC: menu", fonte_pequena, BRANCO, centro=(WIDTH // 2, 615), sombra=PRETO)


def main():
    jogo = Jogo()
    clock = pygame.time.Clock()
    rodando = True
    while rodando:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                rodando = False
            elif event.type == pygame.KEYDOWN:
                jogo.tecla(event.key)
        jogo.update()
        jogo.draw()
        clock.tick(FPS)
    pygame.quit()


if __name__ == "__main__":
    main()

