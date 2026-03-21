import pygame, sys, math, random

pygame.init()
screen = pygame.display.set_mode((800, 600))
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 30)
big_font = pygame.font.SysFont(None, 60)

WHITE, BLACK = (255,255,255), (0,0,0)

x, y = 400, 300
speed, size = 10, 20

best_time = 0

def reset_game():
    return (
        400, 300,
        [[100, 100, 3, 3, False]],
        pygame.time.get_ticks()
    )

x, y, spears, start_time = reset_game()
show_record = False
record_timer = 0

while True:
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            pygame.quit(); sys.exit()

    # 🧍 이동
    k = pygame.key.get_pressed()
    x += (k[pygame.K_d] - k[pygame.K_a]) * speed
    y += (k[pygame.K_s] - k[pygame.K_w]) * speed

    x = max(size, min(800-size, x))
    y = max(size, min(600-size, y))

    screen.fill(BLACK)

    # 🧍 사람
    pygame.draw.circle(screen, WHITE, (int(x), int(y-size)), size//2)
    pygame.draw.line(screen, WHITE, (x,y-size//2),(x,y+size),2)
    pygame.draw.line(screen, WHITE, (x-size,y),(x+size,y),2)
    pygame.draw.line(screen, WHITE, (x,y+size),(x-size,y+size*2),2)
    pygame.draw.line(screen, WHITE, (x,y+size),(x+size,y+size*2),2)

    new_spears = []
    spawned_this_frame = False

    for s in spears:
        sx, sy, dx, dy, prev = s

        sx += dx
        sy += dy

        bounced = False

        # 🔹 벽 충돌 + 위치 보정
        if sx <= 0:
            sx = 5; bounced = True
        elif sx >= 800:
            sx = 795; bounced = True

        if sy <= 0:
            sy = 5; bounced = True
        elif sy >= 600:
            sy = 595; bounced = True

        # 🔥 중앙 방향으로 튕김
        if bounced and not prev and not spawned_this_frame:

            center_x, center_y = 400, 300

            # 중앙을 향한 기본 각도
            base_angle = math.atan2(center_y - sy, center_x - sx)

            # 랜덤 오차 (자연스러움)
            angle = base_angle + random.uniform(-0.5, 0.5)

            dx = math.cos(angle) * 4
            dy = math.sin(angle) * 4

            # 🔥 벽에서 밀어내기
            sx += dx * 2
            sy += dy * 2

            new_spears.append([
                sx, sy,
                math.cos(angle)*4,
                math.sin(angle)*4,
                False
            ])

            spawned_this_frame = True

        # 💥 충돌
        if math.hypot(x - sx, y - sy) < size + 10:
            elapsed = (pygame.time.get_ticks() - start_time) / 1000

            if elapsed > best_time:
                best_time = elapsed
                show_record = True
                record_timer = pygame.time.get_ticks()

            x, y, spears, start_time = reset_game()

        # ⚔️ 창 그리기
        dist = math.hypot(dx, dy)
        if dist:
            nx, ny = dx/dist, dy/dist
            tip = (sx+nx*40, sy+ny*40)
            l = (sx+nx*25-ny*5, sy+ny*25+nx*5)
            r = (sx+nx*25+ny*5, sy+ny*25-nx*5)

            pygame.draw.line(screen, WHITE,
                             (sx-nx*15,sy-ny*15), tip, 2)
            pygame.draw.polygon(screen, WHITE, [tip,l,r])

        s[0], s[1], s[2], s[3], s[4] = sx, sy, dx, dy, bounced

    spears.extend(new_spears)

    # ⏱️ 시간
    elapsed = (pygame.time.get_ticks() - start_time) / 1000

    info = font.render(
        f"FPS:{int(clock.get_fps())} TIME:{elapsed:.1f}s BEST:{best_time:.1f}s",
        True, WHITE
    )
    screen.blit(info, (10, 10))

    # 🏆 신기록 표시
    if show_record:
        if pygame.time.get_ticks() - record_timer < 2000:
            text = big_font.render("NEW RECORD!", True, WHITE)
            screen.blit(text, (250, 250))
        else:
            show_record = False

    pygame.display.flip()
    clock.tick(60)