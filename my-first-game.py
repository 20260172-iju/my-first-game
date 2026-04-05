import pygame
import random
import sys
import math

pygame.init()

def get_korean_font(size):
    candidates = ["malgungothic", "applegothic", "nanumgothic", "notosanscjk"]
    for name in candidates:
        font = pygame.font.SysFont(name, size)
        if font.get_ascent() > 0: return font
    return pygame.font.SysFont(None, size)

# ==========================================
# 1. 전역 상수 및 데이터
# ==========================================
WIDTH, HEIGHT = 800, 600
FPS = 60
WHITE, BLACK, GRAY = (255, 255, 255), (0, 0, 0), (10, 10, 25)
BLUE, RED, YELLOW, CYAN = (50, 150, 255), (220, 50,  50), (240, 220, 0), (0, 255, 255)
PURPLE, ORANGE, GREEN = (200, 50, 255), (255, 140, 0), (50, 220, 50)
UI_BG = (10, 40, 60, 128)

FINAL_BOSS_LEVEL = 20

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Space Shooter - Shatter Effect Update")
clock = pygame.time.Clock()
font = get_korean_font(24)
font_big = get_korean_font(72)
font_small = get_korean_font(18)

PLAYER_W, PLAYER_H = 40, 40

SHIPS = [
    {"name": "BALANCED", "hp": 5, "dmg_mod": 1.0, "spd": 7, "color": CYAN, "desc": "공수 밸런스가 잡힌 표준 기체"},
    {"name": "TANK", "hp": 8, "dmg_mod": 0.6, "spd": 5, "color": GREEN, "desc": "높은 생존력, 하지만 약한 화력"},
    {"name": "ASSAULT", "hp": 3, "dmg_mod": 1.5, "spd": 9, "color": RED, "desc": "강력한 화력과 스피드, 낮은 생존력"}
]

SKILLS_DB = {
    "laser":  {"id": "laser",  "name": "LASER",   "cd": 5,  "color": CYAN,   "desc": "전방 직선 레이저 포격"},
    "nova":   {"id": "nova",   "name": "NOVA",    "cd": 10, "color": PURPLE, "desc": "주변 광역 폭발 데미지"},
    "shield": {"id": "shield", "name": "SHIELD",  "cd": 12, "color": YELLOW, "desc": "3초간 기체 무적 상태 돌입"},
    "emp":    {"id": "emp",    "name": "EMP",     "cd": 15, "color": BLUE,   "desc": "3초간 화면 내 모든 적 정지"},
    "barrage":{"id": "barrage","name": "BARRAGE", "cd": 8,  "color": ORANGE, "desc": "전방으로 거대 철갑탄 7발 산탄 발사"}
}
SKILL_KEYS = list(SKILLS_DB.keys())

AUGMENT_POOL = [
    {"id": "dmg", "name": "화력 강화", "desc": "기본 공격력 +1 증가"},
    {"id": "spd", "name": "연사 스러스터", "desc": "연사 쿨다운 20% 감소"},
    {"id": "multi", "name": "보조 포신", "desc": "다중 발사 수 +1 증가"},
    {"id": "pierce", "name": "철갑탄", "desc": "총알 관통력 +1 증가"},
    {"id": "size", "name": "대구경 탄환", "desc": "총알 크기 및 탄속 증가"}
]

# ==========================================
# 2. 엔티티 및 이펙트 시스템
# ==========================================
def generate_crack():
    x, y = random.randint(0, WIDTH), random.randint(0, HEIGHT)
    points = [(x, y)]
    for _ in range(random.randint(4, 9)):
        x += random.randint(-80, 80)
        y += random.randint(-80, 80)
        points.append((x, y))
    return points

class Bullet:
    def __init__(self, x, y, damage, pierce, size, color=YELLOW):
        self.width = max(6, int(6 * size))
        self.height = max(14, int(14 * size))
        self.rect = pygame.Rect(x - self.width//2, y, self.width, self.height)
        self.damage = damage
        self.pierce = pierce
        self.speed = 15 + (size * 2)
        self.color = color
        self.hit_enemies = set()

    def update(self): self.rect.y -= int(self.speed)
    def draw(self, surf): pygame.draw.rect(surf, self.color, self.rect)

class EnemyBullet:
    def __init__(self, x, y, speed_x, speed_y, size=1):
        self.rect = pygame.Rect(x - 4*size, y, 8*size, 16*size)
        self.speed_x = speed_x
        self.speed_y = speed_y
        self.size = size

    def update(self):
        self.rect.x += self.speed_x
        self.rect.y += self.speed_y

    def draw(self, surf):
        pygame.draw.rect(surf, RED, self.rect, border_radius=4)
        pygame.draw.rect(surf, WHITE, self.rect.inflate(-4, -4), border_radius=2)

class DropItem:
    def __init__(self, x, y, type_name):
        self.rect = pygame.Rect(x - 12, y - 12, 24, 24)
        self.type = type_name
        self.speed_y = 2 + random.random() * 2

    def update(self):
        self.rect.y += self.speed_y

    def draw(self, surf):
        if self.type == "meat":
            pygame.draw.rect(surf, WHITE, (self.rect.x + 2, self.rect.y + 10, 20, 4), border_radius=2)
            pygame.draw.circle(surf, RED, self.rect.center, 9)
            pygame.draw.circle(surf, (200, 50, 50), self.rect.center, 6)
        elif self.type == "battery":
            pygame.draw.rect(surf, BLUE, self.rect, border_radius=3)
            pygame.draw.rect(surf, YELLOW, (self.rect.x + 6, self.rect.y - 4, 12, 4), border_radius=1)
            pygame.draw.rect(surf, CYAN, self.rect.inflate(-8, -10))

class Enemy:
    def __init__(self, type_name, level):
        self.type = type_name
        self.level = level
        self.speed_x = 0
        self.id = random.random()
        
        if self.type == "minion":
            w, h = 36, 36
            self.hp = 1 + (level // 4) 
            self.score_val = 20 + (level * 5)
            self.speed_y = min(7, 1.5 + level * 0.3) 
            self.rect = pygame.Rect(random.randint(0, WIDTH - w), -h, w, h)
            self.shoot_cd = random.randint(80, 180) 
        elif self.type == "mid_boss":
            w, h = 60, 60
            self.hp = 30 + (level * 10)
            self.score_val = 400 + (level * 100) 
            self.speed_y = 2
            self.speed_x = random.choice([-3, 3])
            self.rect = pygame.Rect(WIDTH // 2 - w // 2, -h, w, h)
            self.shoot_cd = 80
        elif self.type == "boss":
            w, h = 120, 120
            self.hp = 200 + (level * 30)
            self.score_val = 1500 + (level * 200) 
            self.speed_y = 1
            self.speed_x = random.choice([-4, 4])
            self.rect = pygame.Rect(WIDTH // 2 - w // 2, -h, w, h)
            self.shoot_cd = 90
            
        self.max_hp = self.hp

    def update(self, enemy_bullets):
        if self.type in ["mid_boss", "boss"]:
            if self.rect.y < 70: self.rect.y += self.speed_y
            else:
                self.rect.x += self.speed_x
                if self.rect.left <= 0 or self.rect.right >= WIDTH: self.speed_x *= -1
        else:
            self.rect.y += self.speed_y

        self.shoot_cd -= 1
        if self.shoot_cd <= 0 and self.rect.y > 0:
            if self.type == "minion":
                enemy_bullets.append(EnemyBullet(self.rect.centerx, self.rect.bottom, 0, 5))
                self.shoot_cd = random.randint(120, 240) 
            elif self.type == "mid_boss":
                for dx in [-3, 0, 3]:
                    enemy_bullets.append(EnemyBullet(self.rect.centerx, self.rect.bottom, dx, 7, size=1.5))
                self.shoot_cd = 80
            elif self.type == "boss":
                for angle in range(0, 360, 45):
                    rad = math.radians(angle)
                    enemy_bullets.append(EnemyBullet(self.rect.centerx, self.rect.centery, math.cos(rad)*6, math.sin(rad)*6, size=2))
                self.shoot_cd = 90

    def draw(self, surf):
        cx, cy = self.rect.centerx, self.rect.centery
        if self.type == "minion":
            color = RED if self.hp <= 1 else (255, 100, 100)
            pygame.draw.polygon(surf, color, [(cx, self.rect.bottom), (self.rect.left, self.rect.top), (cx, self.rect.top + 8), (self.rect.right, self.rect.top)])
        elif self.type == "mid_boss":
            pygame.draw.polygon(surf, ORANGE, [(cx, self.rect.bottom), (self.rect.left, cy), (cx, self.rect.top), (self.rect.right, cy)])
        elif self.type == "boss":
            pygame.draw.rect(surf, RED, self.rect, border_radius=10)
            pygame.draw.circle(surf, YELLOW, (cx, cy), 25, 5)

        if self.max_hp > 1:
            bar_w, bar_h = self.rect.width, 6
            pygame.draw.rect(surf, (50, 50, 50), (self.rect.left, self.rect.top - 12, bar_w, bar_h))
            hp_ratio = max(0, self.hp / self.max_hp)
            pygame.draw.rect(surf, GREEN if hp_ratio > 0.4 else RED, (self.rect.left, self.rect.top - 12, int(bar_w * hp_ratio), bar_h))

def draw_player(surf, rect, color):
    cx = rect.centerx
    pygame.draw.polygon(surf, color, [(cx, rect.top), (rect.left, rect.bottom), (cx, rect.bottom - 8), (rect.right, rect.bottom)])
    pygame.draw.rect(surf, YELLOW, (cx - 4, rect.bottom - 10, 8, 10))

def draw_panel(surf, rect, color):
    shape_surf = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    pygame.draw.rect(shape_surf, UI_BG, (0, 0, rect.width, rect.height), border_radius=10)
    pygame.draw.rect(shape_surf, color, (0, 0, rect.width, rect.height), 2, border_radius=10)
    surf.blit(shape_surf, rect.topleft)

# ==========================================
# 3. 메인 게임 루프
# ==========================================
def main():
    game_state = "LOBBY" 
    
    selected_ship_idx = 0
    equipped_skills = ["laser", "nova"]
    stars = [[random.randint(0, WIDTH), random.randint(0, HEIGHT), random.randint(1, 3), random.choice([WHITE, BLUE, PURPLE])] for _ in range(100)]

    while True:
        player = pygame.Rect(WIDTH // 2 - PLAYER_W // 2, HEIGHT - 120, PLAYER_W, PLAYER_H)
        bullets, enemy_bullets, enemies, drop_items = [], [], [], [] 
        score, spawn_timer, invincible = 0, 0, 0
        bonus_shield = 0 
        last_boss_level, boss_active = 0, False
        
        current_level, current_exp, max_exp = 1, 0, 80
        applied_augments, pending_augments, current_choices = 0, 0, []
        p_damage, p_delay, p_multishot, p_pierce, p_size = 1, 12, 1, 1, 1.0
        shoot_cd = 0
        
        cds = {"z": 0, "x": 0}
        active_timers = {"laser": 0, "nova": 0, "nova_rad": 0, "shield": 0, "emp": 0}
        laser_rect = None
        
        cracks = [] 
        shatter_timer = 0
        shards = []

        def take_damage():
            nonlocal lives, bonus_shield, invincible, game_state
            if invincible <= 0 and active_timers["shield"] <= 0:
                if bonus_shield > 0:
                    bonus_shield -= 1
                else:
                    lives -= 1
                invincible = 120
                if lives <= 0: game_state = "GAME_OVER"
                return True
            return False

        running = True
        while running:
            clock.tick(FPS)
            
            for e in pygame.event.get():
                if e.type == pygame.QUIT: pygame.quit(); sys.exit()
                
                if e.type == pygame.KEYDOWN:
                    if game_state == "LOBBY":
                        if e.key == pygame.K_LEFT: selected_ship_idx = (selected_ship_idx - 1) % len(SHIPS)
                        elif e.key == pygame.K_RIGHT: selected_ship_idx = (selected_ship_idx + 1) % len(SHIPS)
                        elif e.key == pygame.K_b: game_state = "SKILL_SELECT"
                        elif e.key == pygame.K_SPACE:
                            game_state = "PLAYING"
                            max_lives = SHIPS[selected_ship_idx]["hp"]
                            lives = max_lives
                            p_speed = SHIPS[selected_ship_idx]["spd"]
                            dmg_mod = SHIPS[selected_ship_idx]["dmg_mod"]
                            ship_color = SHIPS[selected_ship_idx]["color"]

                    elif game_state == "SKILL_SELECT":
                        if e.key in [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5]:
                            idx = e.key - pygame.K_1
                            skill_id = SKILL_KEYS[idx]
                            if skill_id in equipped_skills: equipped_skills.remove(skill_id)
                            elif len(equipped_skills) < 2: equipped_skills.append(skill_id)
                        elif e.key == pygame.K_b or e.key == pygame.K_RETURN:
                            if len(equipped_skills) == 2: game_state = "LOBBY"

                    elif game_state == "AUGMENT":
                        picked = None
                        if e.key == pygame.K_1: picked = current_choices[0]["id"]
                        elif e.key == pygame.K_2: picked = current_choices[1]["id"]
                        elif e.key == pygame.K_3: picked = current_choices[2]["id"]

                        if picked:
                            if picked == "dmg": p_damage += 1
                            elif picked == "spd": p_delay = max(4, int(p_delay * 0.8))
                            elif picked == "multi": p_multishot += 1
                            elif picked == "pierce": p_pierce += 1
                            elif picked == "size": p_size += 0.5
                            
                            applied_augments += 1; pending_augments -= 1
                            if pending_augments <= 0: game_state = "PLAYING"
                            else: current_choices = random.sample(AUGMENT_POOL, 3)

                    elif game_state in ["GAME_OVER", "GAME_CLEAR"]:
                        if e.key == pygame.K_r: game_state = "LOBBY"; running = False
                        elif e.key == pygame.K_q: pygame.quit(); sys.exit()

            # [이펙트 렌더링] 배경 처리 (공허 상태 시 하얀 화면)
            if game_state == "GAME_CLEAR" or (game_state == "SHATTER" and shatter_timer <= 60):
                screen.fill(WHITE) 
            else:
                for s in stars: s[1] = (s[1] + s[2]) % HEIGHT
                screen.fill(GRAY)
                for s in stars: pygame.draw.circle(screen, s[3], (s[0], s[1]), s[2])
                
                for crack in cracks:
                    if len(crack) > 1:
                        ox = random.randint(-4, 4) if game_state == "SHATTER" else 0
                        oy = random.randint(-4, 4) if game_state == "SHATTER" else 0
                        shifted = [(px + ox, py + oy) for px, py in crack]
                        pygame.draw.lines(screen, (120, 30, 180), False, shifted, 3)
                        pygame.draw.lines(screen, (220, 100, 255), False, shifted, 1) 
                        if game_state == "SHATTER":
                            pygame.draw.lines(screen, WHITE, False, shifted, max(1, (150 - shatter_timer)//8))

            if game_state == "LOBBY":
                title = font_big.render("SPACE FLEET", True, CYAN)
                screen.blit(title, (WIDTH//2 - title.get_width()//2, 80))
                ship = SHIPS[selected_ship_idx]
                draw_panel(screen, pygame.Rect(WIDTH//2 - 200, 180, 400, 250), ship["color"])
                big_rect = pygame.Rect(WIDTH//2 - 30, 200, 60, 60)
                draw_player(screen, big_rect, ship["color"])
                
                screen.blit(font.render(f"<{ship['name']}>", True, ship["color"]), (WIDTH//2 - 50, 280))
                screen.blit(font_small.render(ship["desc"], True, WHITE), (WIDTH//2 - 120, 310))
                stat_txt = f"HP: {ship['hp']}  |  DMG: x{ship['dmg_mod']}  |  SPD: {ship['spd']}"
                screen.blit(font_small.render(stat_txt, True, YELLOW), (WIDTH//2 - 110, 340))
                sk1 = SKILLS_DB[equipped_skills[0]]["name"] if len(equipped_skills) > 0 else "EMPTY"
                sk2 = SKILLS_DB[equipped_skills[1]]["name"] if len(equipped_skills) > 1 else "EMPTY"
                screen.blit(font.render(f"Z: [{sk1}]   X: [{sk2}]", True, CYAN), (WIDTH//2 - 120, 380))
                screen.blit(font.render("[<-] [->] 함선 변경   [B] 스킬 장착   [SPACE] 출격", True, WHITE), (WIDTH//2 - 220, 480))

            elif game_state == "SKILL_SELECT":
                title = font_big.render("SKILL SELECT", True, PURPLE)
                screen.blit(title, (WIDTH//2 - title.get_width()//2, 50))
                screen.blit(font.render("숫자키 [1~5]를 눌러 2개의 스킬을 장착하세요. (완료: B 또는 ENTER)", True, WHITE), (WIDTH//2 - 300, 130))
                for i, key in enumerate(SKILL_KEYS):
                    sk = SKILLS_DB[key]
                    is_eq = key in equipped_skills
                    color = sk["color"] if is_eq else (100, 100, 100)
                    rect = pygame.Rect(WIDTH//2 - 250, 180 + i * 65, 500, 55)
                    draw_panel(screen, rect, color)
                    screen.blit(font.render(f"[{i+1}] {sk['name']}", True, color), (rect.x + 20, rect.y + 15))
                    screen.blit(font_small.render(sk["desc"], True, WHITE), (rect.x + 150, rect.y + 18))
                    if is_eq:
                        slot = "Z" if equipped_skills.index(key) == 0 else "X"
                        screen.blit(font.render(f"[{slot}]", True, YELLOW), (rect.right - 50, rect.y + 15))

            elif game_state in ["PLAYING", "AUGMENT", "SHATTER"]:
                if game_state == "PLAYING":
                    earned_augments = current_level // 3
                    if earned_augments > applied_augments + pending_augments: pending_augments += 1
                    if pending_augments > 0:
                        game_state = "AUGMENT"
                        current_choices = random.sample(AUGMENT_POOL, 3)

                    keys = pygame.key.get_pressed()
                    if keys[pygame.K_LEFT]  and player.left  > 0: player.x -= p_speed
                    if keys[pygame.K_RIGHT] and player.right < WIDTH: player.x += p_speed
                    if keys[pygame.K_UP]    and player.top   > 0: player.y -= p_speed
                    if keys[pygame.K_DOWN]  and player.bottom < HEIGHT: player.y += p_speed

                    shoot_cd -= 1
                    if keys[pygame.K_SPACE] and shoot_cd <= 0:
                        spread = 20
                        start_x = player.centerx - (spread * (p_multishot - 1)) / 2
                        final_dmg = max(0.5, p_damage * dmg_mod)
                        for i in range(p_multishot):
                            bx = start_x + (i * spread)
                            bullets.append(Bullet(bx, player.top, final_dmg, p_pierce, p_size, ship_color))
                        shoot_cd = p_delay

                    cds["z"] = max(0, cds["z"] - 1)
                    cds["x"] = max(0, cds["x"] - 1)
                    for slot_key, slot_idx in [("z", 0), ("x", 1)]:
                        if len(equipped_skills) > slot_idx:
                            skill = equipped_skills[slot_idx]
                            k_press = keys[pygame.K_z] if slot_key == "z" else keys[pygame.K_x]
                            if k_press and cds[slot_key] <= 0:
                                cds[slot_key] = SKILLS_DB[skill]["cd"] * FPS
                                if skill == "laser": active_timers["laser"] = 25
                                elif skill == "nova": active_timers["nova"], active_timers["nova_rad"] = 30, 0
                                elif skill == "shield": active_timers["shield"] = 180
                                elif skill == "emp": active_timers["emp"] = 180
                                elif skill == "barrage":
                                    for i in range(-3, 4):
                                        b = Bullet(player.centerx + i*15, player.top, p_damage * 3, p_pierce + 2, p_size * 2, ORANGE)
                                        b.speed = 20
                                        bullets.append(b)

                    is_emp_active = False
                    if active_timers["emp"] > 0:
                        active_timers["emp"] -= 1
                        is_emp_active = True
                        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                        overlay.fill((0, 50, 150, 60))
                        screen.blit(overlay, (0, 0))

                    if active_timers["shield"] > 0:
                        active_timers["shield"] -= 1
                        invincible = 2 
                        pygame.draw.circle(screen, YELLOW, player.center, 35, 3)

                    if active_timers["laser"] > 0:
                        active_timers["laser"] -= 1
                        laser_rect = pygame.Rect(player.centerx - 25, 0, 50, player.top)
                        for en in enemies:
                            if laser_rect.colliderect(en.rect): en.hp -= 1
                    else: laser_rect = None

                    if active_timers["nova"] > 0:
                        active_timers["nova"] -= 1
                        active_timers["nova_rad"] += 20
                        for en in enemies:
                            dist = math.hypot(player.centerx - en.rect.centerx, player.centery - en.rect.centery)
                            if dist < active_timers["nova_rad"]: en.hp -= 3

                    if not is_emp_active:
                        if current_level % 5 == 0 and current_level > last_boss_level and not boss_active:
                            boss_active = True; enemies.clear(); enemy_bullets.clear()
                            enemies.append(Enemy("boss" if current_level % 10 == 0 else "mid_boss", current_level))

                        spawn_timer += 1
                        if spawn_timer >= max(20, 80 - current_level * 2) and not boss_active:
                            enemies.append(Enemy("minion", current_level))
                            spawn_timer = 0
                            
                        for en in enemies: en.update(enemy_bullets)
                    
                    new_bullets = []
                    for b in bullets:
                        b.update()
                        if b.rect.y < -50: continue
                        destroyed = False
                        for en in enemies:
                            if b.rect.colliderect(en.rect) and en.id not in b.hit_enemies:
                                en.hp -= b.damage
                                b.hit_enemies.add(en.id)
                                b.pierce -= 1
                                if b.pierce <= 0: destroyed = True; break
                        if not destroyed: new_bullets.append(b)
                    bullets = new_bullets

                    new_enemy_bullets = []
                    if invincible > 0 and active_timers["shield"] <= 0: invincible -= 1
                    
                    for eb in enemy_bullets:
                        if not is_emp_active: eb.update()
                        if -50 <= eb.rect.x <= WIDTH + 50 and -50 <= eb.rect.y <= HEIGHT + 50:
                            if player.colliderect(eb.rect):
                                if not take_damage(): new_enemy_bullets.append(eb)
                            else:
                                new_enemy_bullets.append(eb)
                    enemy_bullets = new_enemy_bullets

                    new_enemies = []
                    for en in enemies:
                        if en.hp <= 0:
                            score += en.score_val
                            current_exp += en.score_val
                            
                            chance = random.random()
                            if en.type == "minion":
                                if chance < 0.15: drop_items.append(DropItem(en.rect.centerx, en.rect.centery, "meat"))
                                elif chance < 0.30: drop_items.append(DropItem(en.rect.centerx, en.rect.centery, "battery"))
                            elif en.type in ["mid_boss", "boss"]:
                                drop_items.append(DropItem(en.rect.centerx - 20, en.rect.centery, "meat"))
                                drop_items.append(DropItem(en.rect.centerx + 20, en.rect.centery, "battery"))
                                if en.type == "boss": drop_items.append(DropItem(en.rect.centerx, en.rect.centery - 20, "battery"))

                            while current_exp >= max_exp:
                                current_exp -= max_exp
                                current_level += 1
                                max_exp = int(max_exp * 1.25)
                                if current_level <= FINAL_BOSS_LEVEL:
                                    cracks.append(generate_crack())
                            
                            # [패치] 최종 보스 격파 시 SHATTER 이펙트 돌입
                            if en.type == "boss" and current_level >= FINAL_BOSS_LEVEL:
                                game_state = "SHATTER"
                                shatter_timer = 150
                                shards = []
                                boss_active = False
                            elif en.type in ["mid_boss", "boss"]:
                                boss_active = False; last_boss_level = current_level
                        elif en.rect.top < HEIGHT:
                            new_enemies.append(en)
                    enemies = new_enemies
                    
                    for en in enemies:
                        if player.colliderect(en.rect):
                            if take_damage() and en.type == "minion": en.hp = 0

                    new_drop_items = []
                    for item in drop_items:
                        item.update()
                        if item.rect.y > HEIGHT: continue
                        if player.colliderect(item.rect):
                            if item.type == "meat":
                                lives = min(max_lives, lives + 1)
                            elif item.type == "battery":
                                bonus_shield += 1
                        else:
                            new_drop_items.append(item)
                    drop_items = new_drop_items

                # [렌더링 로직] SHATTER 이펙트의 2단계(하얀 공허) 진입 전까지만 일반 오브젝트 렌더링
                if game_state != "SHATTER" or shatter_timer > 60:
                    if active_timers["nova"] > 0: pygame.draw.circle(screen, PURPLE, player.center, active_timers["nova_rad"], 2)
                    if laser_rect: pygame.draw.rect(screen, CYAN if active_timers["laser"] % 3 != 0 else WHITE, laser_rect)
                    for b in bullets: b.draw(screen)
                    for eb in enemy_bullets: eb.draw(screen)
                    for item in drop_items: item.draw(screen) 
                    for en in enemies: en.draw(screen)
                    
                    if (invincible // 10) % 2 == 0 or game_state in ["AUGMENT", "SHATTER"]:
                        if bonus_shield > 0 and active_timers["shield"] <= 0:
                            pygame.draw.circle(screen, CYAN, player.center, 30, 2)
                        draw_player(screen, player, ship_color)

                    draw_panel(screen, pygame.Rect(10, 10, 240, 50), CYAN)
                    screen.blit(font.render(f"SCORE: {score:06}", True, CYAN), (50, 22))
                    
                    draw_panel(screen, pygame.Rect(WIDTH//2 - 100, 10, 200, 50), YELLOW)
                    screen.blit(font.render(f"LV. {current_level}{' (MAX)' if current_level>=FINAL_BOSS_LEVEL else ''}", True, YELLOW), (WIDTH//2 - 45, 15)) 
                    pygame.draw.rect(screen, (50, 50, 50), (WIDTH//2 - 80, 42, 160, 6))
                    pygame.draw.rect(screen, PURPLE, (WIDTH//2 - 80, 42, int(160 * min(1.0, current_exp/max_exp)), 6))

                    draw_panel(screen, pygame.Rect(WIDTH - 230, 10, 220, 65), CYAN)
                    pygame.draw.rect(screen, (50, 50, 50), (WIDTH - 180, 25, 120, 12))
                    pygame.draw.rect(screen, CYAN if lives > 1 else RED, (WIDTH - 180, 25, (120 / max_lives) * lives, 12))
                    
                    if bonus_shield > 0:
                        pygame.draw.rect(screen, BLUE, (WIDTH - 180, 42, min(120, bonus_shield * 15), 8))
                        screen.blit(font_small.render(f"SHIELD +{bonus_shield}", True, CYAN), (WIDTH - 180, 52))

                    draw_panel(screen, pygame.Rect(10, HEIGHT - 110, 250, 100), PURPLE)
                    for i, slot in enumerate(["z", "x"]):
                        if len(equipped_skills) > i:
                            sk_data = SKILLS_DB[equipped_skills[i]]
                            c_down = cds[slot]
                            txt = f"{slot.upper()}: {sk_data['name']} {'[RDY]' if c_down<=0 else f'[{c_down//FPS}s]'}"
                            screen.blit(font.render(txt, True, sk_data['color'] if c_down<=0 else RED), (25, HEIGHT - 95 + i*35))

                    screen.blit(font_small.render(f"DMG:{p_damage} | MLT:{p_multishot} | PRC:{p_pierce}", True, WHITE), (WIDTH - 230, HEIGHT - 30))

                if game_state == "AUGMENT":
                    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                    overlay.fill((0, 0, 0, 150))
                    screen.blit(overlay, (0, 0))
                    title = font_big.render("SYSTEM UPGRADE", True, CYAN)
                    screen.blit(title, (WIDTH//2 - title.get_width()//2, 100))
                    screen.blit(font.render("키보드 숫자키 [1], [2], [3]을 눌러 선택하세요.", True, WHITE), (WIDTH//2 - 200, 180))

                    start_x = WIDTH//2 - (220 * 3 + 20 * 2) // 2
                    for i, choice in enumerate(current_choices):
                        px = start_x + (240) * i
                        py = HEIGHT // 2 - 20
                        draw_panel(screen, pygame.Rect(px, py, 220, 150), YELLOW)
                        screen.blit(font.render(f"[{i+1}]", True, WHITE), (px + 10, py + 10))
                        name_txt = font.render(choice["name"], True, CYAN)
                        screen.blit(name_txt, (px + 110 - name_txt.get_width()//2, py + 50))
                        desc_txt = font_small.render(choice["desc"], True, WHITE)
                        screen.blit(desc_txt, (px + 110 - desc_txt.get_width()//2, py + 100))
                
                # [이펙트 렌더링] SHATTER 애니메이션 로직
                elif game_state == "SHATTER":
                    shatter_timer -= 1
                    
                    # 1단계: 지진 및 하얀색 균열, 화면 화이트아웃
                    if shatter_timer > 60:
                        if shatter_timer % 3 == 0: cracks.append(generate_crack())
                        flash_alpha = min(255, max(0, 255 - (shatter_timer - 60) * 3))
                        if flash_alpha > 0:
                            flash = pygame.Surface((WIDTH, HEIGHT))
                            flash.fill(WHITE)
                            flash.set_alpha(flash_alpha)
                            screen.blit(flash, (0, 0))
                    
                    # 2단계: 유리가 깨지며 비산하는 효과 (하얀 공허 위에서)
                    else:
                        if shatter_timer == 60:
                            for _ in range(70): # 파편 70개 생성
                                cx, cy = random.randint(0, WIDTH), random.randint(0, HEIGHT)
                                pts = [(random.randint(-90, 90), random.randint(-90, 90)) for _ in range(3, 6)]
                                vx = (cx - WIDTH//2) * 0.15 + random.uniform(-5, 5)
                                vy = (cy - HEIGHT//2) * 0.15 + random.uniform(-5, 5)
                                shards.append({"cx": cx, "cy": cy, "pts": pts, "vx": vx, "vy": vy})
                        
                        # 깨진 맵(회색) 조각들이 날아가는 연출
                        for s in shards:
                            s["cx"] += s["vx"]
                            s["cy"] += s["vy"]
                            real_pts = [(s["cx"] + px, s["cy"] + py) for px, py in s["pts"]]
                            pygame.draw.polygon(screen, GRAY, real_pts)
                            pygame.draw.polygon(screen, WHITE, real_pts, 2)
                    
                    if shatter_timer <= 0:
                        game_state = "GAME_CLEAR"

            elif game_state == "GAME_OVER":
                overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                overlay.fill((5, 5, 20, 200))
                screen.blit(overlay, (0, 0))
                screen.blit(font_big.render("MISSION FAILED", True, RED), (WIDTH//2 - 250, HEIGHT//2 - 50))
                screen.blit(font.render(f"FINAL SCORE: {score:06}", True, WHITE), (WIDTH//2 - 90, HEIGHT//2 + 50))
                screen.blit(font.render("R: 로비로 돌아가기   Q: 종료", True, WHITE), (WIDTH//2 - 130, HEIGHT//2 + 100))

            # [클리어 렌더링] 하얀 배경에 맞는 텍스트 컬러로 변경
            elif game_state == "GAME_CLEAR":
                clear_title = font_big.render("MISSION CLEAR", True, BLUE)
                screen.blit(clear_title, (WIDTH//2 - clear_title.get_width()//2, HEIGHT//2 - 80))
                screen.blit(font.render("시공간의 붕괴를 넘어, 마침내 공허에 도달했습니다.", True, BLACK), (WIDTH//2 - 240, HEIGHT//2 + 20))
                screen.blit(font.render(f"FINAL SCORE: {score:06}", True, PURPLE), (WIDTH//2 - 100, HEIGHT//2 + 70))
                screen.blit(font.render("R: 메인 로비로 귀환   Q: 우주 닫기(종료)", True, BLACK), (WIDTH//2 - 160, HEIGHT//2 + 130))

            pygame.display.flip()

if __name__ == "__main__":
    main()