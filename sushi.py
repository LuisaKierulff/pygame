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
PASTA_IMAGENS = os.path.join(BASE_DIR, "imagens")
ARQUIVO_SCORES = os.path.join(BASE_DIR, "highscores.json")

SUSHI_WIDTH, SUSHI_HEIGHT = 100, 46
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
DURACAO_COMEMORACAO = 150  # frames que o sushi de óculos fica na tela durante o jogo

# Cores
BRANCO = (255, 255, 255)
ROSA = (255, 160, 180)
MARROM = (150, 90, 60)
MARROM_ESCURO = (105, 62, 40)
PRETO = (40, 40, 40)
VERDE = (80, 160, 100)
LARANJA = (255, 120, 80)
CREME = (255, 244, 226)
DOURADO = (240, 190, 60)
VERMELHO = (215, 70, 70)

window = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Empilha Sushi")

fonte_titulo = pygame.font.SysFont("arial", 68, bold=True)
fonte_grande = pygame.font.SysFont("arial", 44, bold=True)
fonte_texto = pygame.font.SysFont("arial", 30, bold=True)
fonte_pequena = pygame.font.SysFont("arial", 22, bold=True)


# =====================================================================
#  IMAGENS  (coloque seus PNGs na pasta "imagens" ao lado deste arquivo)
#    imagens/fundo.png    -> fundo (600x700)
#    imagens/logo.png     -> logo da tela inicial
#    imagens/base.png     -> prato / base da pilha
#    imagens/sushi1.png ... sushi6.png -> sushis da pilha (100x46, fundo transparente)
#    imagens/recorde.png  -> sushi de óculos no shoyo (fundo transparente)
#  Se algum arquivo não existir, o jogo desenha uma versão própria.
# =====================================================================
def carregar_imagem(nome, tamanho=None):
    caminho = os.path.join(PASTA_IMAGENS, nome)
    if not os.path.exists(caminho):
        return None
    try:
        img = pygame.image.load(caminho).convert_alpha()
    except pygame.error:
        return None
    if tamanho:
        img = pygame.transform.smoothscale(img, tamanho)
    return img


# ---------------------------------------------------------------------
#  Sprites desenhados em código (suavizados com supersampling 4x)
# ---------------------------------------------------------------------
K = 4  # fator de supersampling


def _r(*vals):
    return tuple(int(round(v * K)) for v in vals)


def _elip(s, cor, x, y, w, h, borda=0):
    pygame.draw.ellipse(s, cor, _r(x, y, w, h), int(borda * K))


def _rect(s, cor, x, y, w, h, raio=0, borda=0):
    pygame.draw.rect(s, cor, _r(x, y, w, h), int(borda * K), border_radius=int(raio * K))


def _linha(s, cor, x1, y1, x2, y2, largura):
    pygame.draw.line(s, cor, _r(x1, y1), _r(x2, y2), max(1, int(largura * K)))


def _nova(w, h):
    return pygame.Surface((w * K, h * K), pygame.SRCALPHA)


def _finalizar(s, w, h):
    return pygame.transform.smoothscale(s, (w, h))


def _rosto(s, cx, cy, tipo="normal"):
    """Carinha kawaii: olhos, bochechas e sorrisinho.
    tipo: 'normal', 'feliz' (olhos ^ ^) ou 'piscando'."""
    olho = (25, 20, 28)
    for lado in (-1, 1):
        ex = cx + lado * 13
        fechado = tipo == "feliz" or (tipo == "piscando" and lado == 1)
        if fechado:
            pygame.draw.arc(s, olho, _r(ex - 4.5, cy - 2.5, 9, 7), 0, math.pi, int(1.8 * K))
        else:
            _elip(s, olho, ex - 2.8, cy - 3.5, 5.6, 7)
            _elip(s, BRANCO, ex - 1.8, cy - 2.6, 2.2, 2.2)
            _elip(s, BRANCO, ex + 0.3, cy + 0.6, 1.2, 1.2)
        _elip(s, (255, 105, 105), cx + lado * 23 - 4.5, cy + 2.5, 9, 5)
    pygame.draw.arc(s, olho, _r(cx - 5, cy - 1.5, 10, 8), math.pi, 2 * math.pi, int(1.6 * K))


ARROZ = (250, 248, 240)
ARROZ_BORDA = (222, 218, 205)
NORI = (58, 78, 84)
NORI_BORDA = (38, 54, 60)


def _base_arroz(s):
    _rect(s, ARROZ, 3, 19, 94, 26, 13)
    _rect(s, ARROZ_BORDA, 3, 19, 94, 26, 13, 1.2)


def sprite_salmao():
    s = _nova(SUSHI_WIDTH, SUSHI_HEIGHT)
    _base_arroz(s)
    _rect(s, (255, 125, 85), 0, 3, 100, 23, 11)
    _rect(s, (222, 95, 62), 0, 3, 100, 23, 11, 1.2)
    for i in range(4):
        _linha(s, (255, 196, 165), 14 + i * 20, 7, 21 + i * 20, 22, 2.2)
    _rosto(s, 50, 35, "normal")
    return _finalizar(s, SUSHI_WIDTH, SUSHI_HEIGHT)


def sprite_tamago():
    s = _nova(SUSHI_WIDTH, SUSHI_HEIGHT)
    _base_arroz(s)
    _rect(s, (255, 205, 80), 0, 3, 100, 23, 11)
    _rect(s, (220, 165, 50), 0, 3, 100, 23, 11, 1.2)
    _rect(s, NORI, 10, 1, 13, 40, 3)
    _rosto(s, 58, 35, "piscando")
    return _finalizar(s, SUSHI_WIDTH, SUSHI_HEIGHT)


def sprite_ikura():
    s = _nova(SUSHI_WIDTH, SUSHI_HEIGHT)
    _rect(s, NORI, 6, 12, 88, 34, 9)
    _rect(s, NORI_BORDA, 6, 12, 88, 34, 9, 1.2)
    _elip(s, (196, 40, 36), 9, 5, 82, 14)
    for i in range(9):
        x = 13 + i * 9.2
        y = 3 + (i % 2) * 2.5
        _elip(s, (232, 70, 52), x - 4.4, y, 8.8, 8.8)
        _elip(s, (255, 170, 150), x - 2.4, y + 1.4, 2.6, 2.6)
    _rosto(s, 50, 31, "feliz")
    return _finalizar(s, SUSHI_WIDTH, SUSHI_HEIGHT)


def sprite_maki():
    s = _nova(SUSHI_WIDTH, SUSHI_HEIGHT)
    _rect(s, NORI, 8, 10, 84, 36, 9)
    _rect(s, NORI_BORDA, 8, 10, 84, 36, 9, 1.2)
    _rect(s, ARROZ, 5, 2, 90, 15, 7)
    _rect(s, ARROZ_BORDA, 5, 2, 90, 15, 7, 1.2)
    _elip(s, (255, 130, 90), 41, 5, 18, 8)
    _rosto(s, 50, 31, "normal")
    return _finalizar(s, SUSHI_WIDTH, SUSHI_HEIGHT)


def sprite_roll_laranja():
    s = _nova(SUSHI_WIDTH, SUSHI_HEIGHT)
    _rect(s, (246, 120, 80), 8, 10, 84, 36, 9)
    _rect(s, (205, 85, 55), 8, 10, 84, 36, 9, 1.2)
    _rect(s, ARROZ, 5, 2, 90, 15, 7)
    _rect(s, ARROZ_BORDA, 5, 2, 90, 15, 7, 1.2)
    _elip(s, (120, 190, 90), 38, 5, 12, 8)
    _elip(s, (255, 205, 80), 51, 5, 11, 8)
    _linha(s, (255, 172, 140), 16, 22, 20, 28, 1.6)
    _linha(s, (255, 172, 140), 80, 22, 84, 28, 1.6)
    _rosto(s, 50, 31, "piscando")
    return _finalizar(s, SUSHI_WIDTH, SUSHI_HEIGHT)


def sprite_ebi():
    s = _nova(SUSHI_WIDTH, SUSHI_HEIGHT)
    _base_arroz(s)
    _rect(s, (255, 206, 196), 0, 3, 100, 23, 11)
    _rect(s, (232, 150, 140), 0, 3, 100, 23, 11, 1.2)
    for i in range(4):
        _linha(s, (240, 112, 100), 14 + i * 20, 6, 20 + i * 20, 23, 2.6)
    _rosto(s, 50, 35, "feliz")
    return _finalizar(s, SUSHI_WIDTH, SUSHI_HEIGHT)


# Todos retangulares/achatados, bons para empilhar (nada de formas arredondadas)
_FABRICAS = [sprite_salmao, sprite_tamago, sprite_ikura, sprite_maki, sprite_roll_laranja, sprite_ebi]
SUSHI_SPRITES = []
for _i, _fab in enumerate(_FABRICAS):
    _img = carregar_imagem(f"sushi{_i + 1}.png", (SUSHI_WIDTH, SUSHI_HEIGHT))
    SUSHI_SPRITES.append(_img if _img else _fab())


def sprite_recorde():
    """Sushi de óculos relaxando numa tigela de shoyo (tela de novo recorde)."""
    img = carregar_imagem("recorde.png")
    if img:
        w, h = img.get_size()
        esc = min(200 / w, 200 / h)
        return pygame.transform.smoothscale(img, (int(w * esc), int(h * esc)))

    s = _nova(200, 200)
    azul, azul_escuro = (60, 150, 220), (38, 70, 120)
    laranja, laranja_escuro = (255, 125, 85), (222, 95, 62)

    _elip(s, (214, 196, 196), 25, 172, 150, 20)                       # sombra
    # hashis
    _linha(s, (250, 200, 90), 52, 20, 92, 100, 6)
    _linha(s, (250, 200, 90), 72, 16, 104, 98, 6)
    _linha(s, (200, 120, 40), 56, 28, 60, 36, 6)
    _linha(s, (200, 120, 40), 76, 24, 79, 32, 6)
    # boca da tigela + shoyo
    _elip(s, azul, 18, 79, 164, 32)
    _elip(s, azul_escuro, 18, 79, 164, 32, 2)
    _elip(s, (70, 36, 30), 24, 83, 152, 24)
    # sushi
    _rect(s, ARROZ, 62, 40, 76, 62, 14)
    _rect(s, ARROZ_BORDA, 62, 40, 76, 62, 14, 1.5)
    _rect(s, laranja, 58, 28, 84, 28, 13)
    _rect(s, laranja_escuro, 58, 28, 84, 28, 13, 1.5)
    for i in range(4):
        _linha(s, (255, 196, 165), 72 + i * 18, 33, 78 + i * 18, 51, 2.4)
    # óculos escuros
    _rect(s, (30, 25, 30), 70, 60, 26, 17, 6)
    _rect(s, (30, 25, 30), 104, 60, 26, 17, 6)
    _linha(s, (30, 25, 30), 95, 66, 105, 66, 3)
    _linha(s, (30, 25, 30), 70, 64, 63, 62, 2.4)
    _linha(s, (30, 25, 30), 130, 64, 137, 62, 2.4)
    _linha(s, (200, 200, 215), 75, 64, 80, 64, 1.6)
    _linha(s, (200, 200, 215), 109, 64, 114, 64, 1.6)
    # bochechas e boquinha aberta
    _elip(s, (255, 105, 105), 66, 79, 9, 5)
    _elip(s, (255, 105, 105), 125, 79, 9, 5)
    _elip(s, (120, 40, 50), 93, 78, 14, 10)
    _elip(s, (255, 140, 150), 96, 83, 8, 4)
    # frente da tigela (meia-lua azul)
    _rect(s, (50, 120, 190), 70, 168, 60, 10, 4)
    externo = [(100 + 82 * math.cos(math.radians(a)), 95 + 78 * math.sin(math.radians(a))) for a in range(0, 181, 3)]
    interno = [(100 + 82 * math.cos(math.radians(a)), 95 + 16 * math.sin(math.radians(a))) for a in range(180, -1, -3)]
    pontos = [(int(x * K), int(y * K)) for x, y in externo + interno]
    pygame.draw.polygon(s, azul, pontos)
    pygame.draw.polygon(s, azul_escuro, pontos, int(2 * K))
    _elip(s, (140, 205, 248), 140, 118, 14, 34)
    # fatia de salmão pendurada na borda
    _rect(s, laranja, 8, 88, 46, 52, 22)
    _rect(s, laranja_escuro, 8, 88, 46, 52, 22, 1.5)
    for i in range(3):
        _linha(s, (255, 196, 165), 16 + i * 10, 100, 12 + i * 10, 128, 2.2)
    return _finalizar(s, 200, 200)


RECORDE_IMG = sprite_recorde()
_rw, _rh = RECORDE_IMG.get_size()
RECORDE_PEQ = pygame.transform.smoothscale(RECORDE_IMG, (int(_rw * 0.55), int(_rh * 0.55)))


def criar_fundo():
    img = carregar_imagem("fundo.png", (WIDTH, HEIGHT))
    if img:
        return img.convert()
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
    img = carregar_imagem("base.png", (BASE_WIDTH, BASE_HEIGHT + 10))
    if img:
        return img
    s = pygame.Surface((BASE_WIDTH, BASE_HEIGHT), pygame.SRCALPHA)
    pygame.draw.rect(s, MARROM, (0, 0, BASE_WIDTH, BASE_HEIGHT), border_radius=8)
    pygame.draw.rect(s, MARROM_ESCURO, (0, 0, BASE_WIDTH, BASE_HEIGHT), 3, border_radius=8)
    for x in range(20, BASE_WIDTH - 10, 38):
        pygame.draw.line(s, MARROM_ESCURO, (x, 5), (x, BASE_HEIGHT - 6), 2)
    return s


FUNDO = criar_fundo()
BASE_IMG = criar_base()
LOGO = carregar_imagem("logo.png")


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
        self.recorde_inicial = self.scores[0] if self.scores else 0
        self.bateu = False       # já passou do recorde durante esta partida?
        self.comemora = 0        # frames restantes do sushi de óculos no jogo
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
        if self.comemora > 0:
            self.comemora -= 1
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

    def verificar_recorde(self):
        """Passou do recorde anterior durante a partida: comemora com o sushi de óculos."""
        if self.recorde_inicial > 0 and not self.bateu and self.pontos > self.recorde_inicial:
            self.bateu = True
            self.comemora = DURACAO_COMEMORACAO

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
        self.verificar_recorde()

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
        self.comemora = 0
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
        # título / logo
        if LOGO:
            window.blit(LOGO, LOGO.get_rect(center=(WIDTH // 2, 95)))
        else:
            texto(window, "EMPILHA", fonte_titulo, MARROM, centro=(WIDTH // 2, 70), sombra=(255, 255, 255))
            texto(window, "SUSHI", fonte_titulo, LARANJA, centro=(WIDTH // 2, 135), sombra=(255, 255, 255))

        # sushis "flutuando"
        for i, idx in enumerate((0, 2, 5)):
            bob = math.sin(self.t * 0.07 + i * 1.3) * 7
            window.blit(SUSHI_SPRITES[idx], (WIDTH // 2 - 50 + (i - 1) * 150, 203 + bob))

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

        # sushi de óculos comemorando o recorde (entra e sai deslizando pela direita)
        if self.comemora > 0:
            desl = max(0, self.comemora - (DURACAO_COMEMORACAO - 20)) * 8 + max(0, 20 - self.comemora) * 8
            rw, rh = RECORDE_PEQ.get_size()
            x = WIDTH - rw - 10 + desl
            y = HEIGHT - rh - 20
            window.blit(RECORDE_PEQ, (x, y))
            texto(window, "NOVO RECORDE!", fonte_pequena, DOURADO, centro=(x + rw // 2, y - 8), sombra=PRETO)

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
        if self.novo_recorde:
            # bateu o recorde: sushi de óculos relaxando no shoyo
            texto(window, "NOVO RECORDE!", fonte_grande, DOURADO, centro=(WIDTH // 2, 70), sombra=PRETO)
            texto(window, f"Pontos: {self.pontos}", fonte_grande, BRANCO, centro=(WIDTH // 2, 125), sombra=PRETO)
            bob = math.sin(self.t * 0.06) * 6
            window.blit(RECORDE_IMG, RECORDE_IMG.get_rect(center=(WIDTH // 2, 275 + bob)))
            texto(window, "A pilha caiu, mas que pilha!", fonte_texto, BRANCO, centro=(WIDTH // 2, 425), sombra=PRETO)
            texto(window, "Veja o ranking no menu (ESC)", fonte_pequena, ROSA, centro=(WIDTH // 2, 480), sombra=PRETO)
        else:
            texto(window, "A PILHA CAIU!", fonte_grande, BRANCO, centro=(WIDTH // 2, 120), sombra=PRETO)
            texto(window, f"Pontos: {self.pontos}", fonte_grande, DOURADO, centro=(WIDTH // 2, 180), sombra=PRETO)
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
