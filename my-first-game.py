import pygame
import random
import math

pygame.init()

WIDTH, HEIGHT = 900, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("✨ Fancy Particle Playground (Enhanced)")

clock = pygame.time.Clock()

particles = []

# 반투명 화면 (잔상 효과용)
trail_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)

class Particle:
    def __init__(self, x, y):
        self.x = x
        self.y = y

        angle = random.uniform(0, math.pi * 2)
        speed = random.uniform(2, 7)

        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed

        self.life = random.randint(50, 100)
        self.max_life = self.life

        self.size = random.randint(4, 8)

        # 부드러운 색상
        self.base_color = [
            random.randint(180, 255),
            random.randint(120, 255),
            random.randint(180, 255)
        ]

    def update(self):
        self.x += self.vx
        self.y += self.vy

        # 공기 저항 느낌
        self.vx *= 0.99
        self.vy *= 0.99

        # 중력
        self.vy += 0.07

        self.life -= 1

    def draw(self, surf):
        if self.life <= 0:
            return

        # 생명 비율 (0~1)
        life_ratio = self.life / self.max_life

        # 크기 점점 감소
        size = int(self.size * life_ratio)

        # 색 점점 어두워짐
        color = (
            int(self.base_color[0] * life_ratio),
            int(self.base_color[1] * life_ratio),
            int(self.base_color[2] * life_ratio)
        )

        # 빛나는 효과 (겹쳐 그리기)
        pygame.draw.circle(surf, color, (int(self.x), int(self.y)), size)
        pygame.draw.circle(surf, color, (int(self.x), int(self.y)), size // 2)

    def alive(self):
        return self.life > 0


def draw_background(surface, t):
    for y in range(HEIGHT):
        c = int(60 + 40 * math.sin(y * 0.01 + t))
        color = (20, c, 80 + c//2)
        pygame.draw.line(surface, color, (0, y), (WIDTH, y))


running = True
time = 0

while running:

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    mouse = pygame.mouse.get_pos()
    buttons = pygame.mouse.get_pressed()

    # 클릭하면 폭발 느낌
    if buttons[0]:
        for _ in range(12):
            particles.append(Particle(mouse[0], mouse[1]))

    time += 0.03

    # 배경
    draw_background(screen, time)

    # 잔상 효과 (살짝 덮기)
    trail_surface.fill((0, 0, 0, 40))
    screen.blit(trail_surface, (0, 0))

    # 파티클 업데이트
    for p in particles:
        p.update()
        p.draw(screen)

    particles = [p for p in particles if p.alive()]

    pygame.display.flip()
    clock.tick(60)

pygame.quit()