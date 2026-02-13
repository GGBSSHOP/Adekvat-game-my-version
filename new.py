import pygame
import sys
import random
import math
import json
import os

SAVE_FILE = "savedata.json"

def load_save():
    if os.path.exists(SAVE_FILE):
        try:
            with open(SAVE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if "total_kills" in data and "total_score" not in data:
                    data["total_score"] = data["total_kills"]
                    del data["total_kills"]
                return {
                    "total_score": data.get("total_score", 0),
                    "total_playtime_seconds": data.get("total_playtime_seconds", 0),
                    "total_deaths": data.get("total_deaths", 0),
                    "sessions_played": data.get("sessions_played", 0),
                    "best_session_score": data.get("best_session_score", 0),
                    "music_volume": data.get("music_volume", 0.6),
                    "shoot_volume": data.get("shoot_volume", 0.2),
                    "death_volume": data.get("death_volume", 0.2),
                    "upgrade_level": data.get("upgrade_level", 0),
                    "total_money": data.get("total_money", 0),
                    "shield_purchased": data.get("shield_purchased", False),
                    "shield_active": data.get("shield_active", False),
                    "control_mode": data.get("control_mode", "keyboard")
                }
        except (json.JSONDecodeError, ValueError):
            print("Файл сохранения повреждён. Создаём новый.")
    return {
        "total_score": 0,
        "total_playtime_seconds": 0,
        "total_deaths": 0,
        "sessions_played": 0,
        "best_session_score": 0,
        "music_volume": 0.6,
        "shoot_volume": 0.2,
        "death_volume": 0.2,
        "upgrade_level": 0,
        "total_money": 0,
        "shield_purchased": False,
        "shield_active": False,
        "control_mode": "keyboard"
    }

def save_stats(stats):
    try:
        with open(SAVE_FILE, "w", encoding="utf-8") as f:
            json.dump(stats, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Ошибка сохранения: {e}")

pygame.init()
WIDTH, HEIGHT = 1280, 720
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Cyber - Arena")

font = pygame.font.SysFont(None, 36)
big_font = pygame.font.SysFont(None, 64)
game_over_font = pygame.font.SysFont(None, 48)
small_font = pygame.font.SysFont(None, 24)

pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
pygame.mixer.set_num_channels(32)

try:
    death_sound = pygame.mixer.Sound("death_sound.mp3")
    shoot_sound = pygame.mixer.Sound("shoot_sound.mp3")
    death_sound.set_volume(0.2)
    shoot_sound.set_volume(0.2)
except pygame.error as e:
    print(f"Не удалось загрузить звук: {e}")
    death_sound = None
    shoot_sound = None

try:
    pygame.mixer.music.load("music.wav")
    pygame.mixer.music.set_volume(0.6)
    pygame.mixer.music.play(-1)
except pygame.error as e:
    print(f"Не удалось загрузить музыку: {e}")

BACKGROUND = (20, 20, 35)
PLAYER_COLOR = (100, 200, 255)
RAY_COLOR = (100, 255, 200)
TEXT_COLOR = (220, 220, 255)
BUTTON_COLOR = (80, 180, 255)
BUTTON_HOVER = (120, 220, 255)
FLOOR_COLOR = (40, 40, 60)
SHIELD_COLOR = (50, 150, 255)
JOYSTICK_BG = (50, 50, 70, 150)
JOYSTICK_HANDLE = (200, 200, 255)

class VirtualJoystick:
    def __init__(self, x, y, radius=70, handle_radius=30, stick_id=0, zone="left"):
        self.base_x = x
        self.base_y = y
        self.x = x
        self.y = y
        self.radius = radius
        self.handle_radius = handle_radius
        self.active = False
        self.touch_id = None
        self.stick_id = stick_id
        self.zone = zone
        self.dx = 0
        self.dy = 0
        self.normalized_dx = 0
        self.normalized_dy = 0
        self.update_rect()
        
    def update_rect(self):
        self.rect = pygame.Rect(self.base_x - self.radius, self.base_y - self.radius, self.radius * 2, self.radius * 2)
        
    def can_control(self, pos):
        if self.zone == "left" and pos[0] < WIDTH // 2:
            return True
        elif self.zone == "right" and pos[0] >= WIDTH // 2:
            return True
        return False
        
    def update(self, touch_pos, touch_id):
        if not self.active and self.rect.collidepoint(touch_pos) and self.can_control(touch_pos):
            self.active = True
            self.touch_id = touch_id
            self.x, self.y = touch_pos
        elif self.active and self.touch_id == touch_id:
            if self.can_control(touch_pos):
                self.x, self.y = touch_pos
            else:
                self.reset()
                return False
        else:
            return False
            
        dx = self.x - self.base_x
        dy = self.y - self.base_y
        distance = math.hypot(dx, dy)
        
        if distance > self.radius:
            self.x = self.base_x + dx / distance * self.radius
            self.y = self.base_y + dy / distance * self.radius
            dx = self.x - self.base_x
            dy = self.y - self.base_y
            distance = self.radius
            
        if distance > 0:
            self.normalized_dx = dx / self.radius
            self.normalized_dy = dy / self.radius
            self.dx = dx
            self.dy = dy
        else:
            self.normalized_dx = 0
            self.normalized_dy = 0
            self.dx = 0
            self.dy = 0
        return True
            
    def reset(self):
        self.active = False
        self.touch_id = None
        self.x = self.base_x
        self.y = self.base_y
        self.dx = 0
        self.dy = 0
        self.normalized_dx = 0
        self.normalized_dy = 0
        
    def draw(self, screen):
        s = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(s, (*JOYSTICK_BG[:3], 100), (self.radius, self.radius), self.radius)
        screen.blit(s, (self.base_x - self.radius, self.base_y - self.radius))
        
        if self.active:
            pygame.draw.circle(screen, JOYSTICK_HANDLE, (int(self.x), int(self.y)), self.handle_radius)
            pygame.draw.circle(screen, (255, 255, 255), (int(self.x), int(self.y)), self.handle_radius, 2)
        else:
            pygame.draw.circle(screen, (*JOYSTICK_HANDLE, 100), (int(self.x), int(self.y)), self.handle_radius, 2)

def get_enemy_color(enemy):
    if enemy['type'] == 'basic':
        return (255, 80, 80)
    elif enemy['type'] == 'armored':
        return (100, 100, 200)
    elif enemy['type'] == 'runner':
        return (255, 255, 255)
    elif enemy['type'] == 'basic+':
        return (255, 120, 80)
    elif enemy['type'] == 'armored+':
        return (120, 120, 220)
    elif enemy['type'] == 'runner+':
        return (255, 255, 180)
    return (200, 200, 200)

player_size = 30
player_speed = 6
player_x = 0
player_y = 0
enemies = []
spawn_timer = 0
session_score = 0
start_time = 0
fullscreen = False
music_volume = 0.6
shoot_volume = 0.2
death_volume = 0.2
state = "main_menu"
money = 0
player_damage = 1.0
upgrade_level = 0
kills = 0
has_shield = False

global_stats = load_save()
music_volume = global_stats["music_volume"]
shoot_volume = global_stats["shoot_volume"]
death_volume = global_stats["death_volume"]
has_shield = global_stats["shield_active"]
control_mode = global_stats.get("control_mode", "keyboard")

if shoot_sound:
    shoot_sound.set_volume(shoot_volume)
if death_sound:
    death_sound.set_volume(death_volume)
pygame.mixer.music.set_volume(music_volume)

if fullscreen:
    screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
    
def reset_game():
    global player_x, player_y, enemies, spawn_timer, money, upgrade_level, session_score, player_damage, start_time, kills, has_shield
    player_x = WIDTH // 2 - player_size // 2
    player_y = HEIGHT // 2 - player_size // 2
    enemies = []
    spawn_timer = 0
    session_score = 0
    start_time = pygame.time.get_ticks()
    player_damage = 1.0
    money = 0
    upgrade_level = 0
    kills = 0
    has_shield = global_stats.get("shield_active", False)

reset_game()

def spawn_enemy(enemy_type="basic"):
    side = random.choice(['top', 'bottom', 'left', 'right'])
    if side == 'top':
        x = random.randint(0, WIDTH)
        y = -30
    elif side == 'bottom':
        x = random.randint(0, WIDTH)
        y = HEIGHT
    elif side == 'left':
        x = -30
        y = random.randint(0, HEIGHT)
    else:
        x = WIDTH
        y = random.randint(0, HEIGHT)
    if enemy_type == "basic":
        return {'x': x, 'y': y, 'size': 35, 'speed': 2, 'type': 'basic', 'hp': 2, 'score_value': 10}
    elif enemy_type == "armored":
        return {'x': x, 'y': y, 'size': 35, 'speed': 1, 'type': 'armored', 'hp': 3, 'score_value': 15}
    elif enemy_type == "runner":
        return {'x': x, 'y': y, 'size': 35, 'speed': 7, 'type': 'runner', 'hp': 1, 'score_value': 15}
    elif enemy_type == "basic+":
        return {'x': x, 'y': y, 'size': 35, 'speed': 2.5, 'type': 'basic+', 'hp': 3, 'score_value': 20}
    elif enemy_type == "armored+":
        return {'x': x, 'y': y, 'size': 35, 'speed': 1.5, 'type': 'armored+', 'hp': 4, 'score_value': 25}
    elif enemy_type == "runner+":
        return {'x': x, 'y': y, 'size': 35, 'speed': 7.5, 'type': 'runner+', 'hp': 2, 'score_value': 35}
    else:
        print(f"Неизвестный тип врага: {enemy_type}")
        return {'x': 0, 'y': 0, 'size': 35, 'speed': 1, 'type': 'basic', 'hp': 1, 'score_value': 0}

def check_collision(x1, y1, size1, x2, y2, size2):
    return (x1 < x2 + size2 and x1 + size1 > x2 and
            y1 < y2 + size2 and y1 + size1 > y2)

def toggle_fullscreen():
    global fullscreen, screen, WIDTH, HEIGHT, left_joystick, right_joystick, player_x, player_y, state
    fullscreen = not fullscreen
    global_stats["fullscreen"] = fullscreen
    
    if state == "playing":
        rel_x = player_x / WIDTH
        rel_y = player_y / HEIGHT
    
    if fullscreen:
        display_info = pygame.display.Info()
        WIDTH = display_info.current_w
        HEIGHT = display_info.current_h
        screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
    else:
        WIDTH = 1280
        HEIGHT = 720
        screen = pygame.display.set_mode((WIDTH, HEIGHT))
    
    if state == "playing":
        player_x = int(rel_x * WIDTH)
        player_y = int(rel_y * HEIGHT)
        player_x = max(0, min(WIDTH - player_size, player_x))
        player_y = max(0, min(HEIGHT - player_size, player_y))
    
    left_joystick = VirtualJoystick(int(WIDTH * 0.1), HEIGHT - 120, 70, 30, 0, "left")
    right_joystick = VirtualJoystick(int(WIDTH * 0.9), HEIGHT - 120, 70, 30, 1, "right")
    left_joystick.update_rect()
    right_joystick.update_rect()
    
    save_stats(global_stats)

def ray_hits_enemy(ray_start, ray_end, enemy):
    ex = enemy['x'] + enemy['size'] / 2
    ey = enemy['y'] + enemy['size'] / 2
    x0, y0 = ray_start
    x1, y1 = ray_end
    dx = x1 - x0
    dy = y1 - y0
    if abs(dx) < 1e-6 and abs(dy) < 1e-6:
        return False
    t = ((ex - x0) * dx + (ey - y0) * dy) / (dx*dx + dy*dy)
    if t < 0 or t > 1:
        return False
    closest_x = x0 + t * dx
    closest_y = y0 + t * dy
    dist = math.hypot(closest_x - ex, closest_y - ey)
    return dist <= enemy['size'] / 2

def format_time(seconds):
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes}:{secs:02d}"
        
clock = pygame.time.Clock()
running = True
mouse_down = False
last_shot_time = 0
active_laser = None
last_sound_time = 0
last_upgrade_check = 0

left_joystick = VirtualJoystick(int(WIDTH * 0.1), HEIGHT - 120, 70, 30, 0, "left")
right_joystick = VirtualJoystick(int(WIDTH * 0.9), HEIGHT - 120, 70, 30, 1, "right")
left_joystick.update_rect()
right_joystick.update_rect()

touch_counter = 0

while running:
    current_time = pygame.time.get_ticks()
    mouse_pos = pygame.mouse.get_pos()
    mouse_pressed = False
    
    keys = pygame.key.get_pressed()
    if keys[pygame.K_ESCAPE] and state == "playing":
        state = "main_menu"
        left_joystick.reset()
        right_joystick.reset()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                mouse_pressed = True
                if control_mode == "joystick":
                    touch_counter += 1
                    touch_id = f"mouse_{touch_counter}"
                    
                    if event.pos[0] < WIDTH // 2:
                        if not left_joystick.active:
                            left_joystick.update(event.pos, touch_id)
                    else:
                        if not right_joystick.active:
                            right_joystick.update(event.pos, touch_id)
                        
        if event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                mouse_down = False
                active_laser = None
                if control_mode == "joystick":
                    if left_joystick.active:
                        left_joystick.reset()
                    if right_joystick.active:
                        right_joystick.reset()
                            
        if event.type == pygame.MOUSEMOTION:
            if control_mode == "joystick" and event.buttons[0]:
                if event.pos[0] < WIDTH // 2:
                    if left_joystick.active:
                        left_joystick.update(event.pos, left_joystick.touch_id)
                else:
                    if right_joystick.active:
                        right_joystick.update(event.pos, right_joystick.touch_id)
        
        if event.type == pygame.FINGERDOWN:
            if control_mode == "joystick":
                x = event.x * WIDTH
                y = event.y * HEIGHT
                touch_id = f"finger_{event.finger_id}"
                
                if x < WIDTH // 2:
                    if not left_joystick.active:
                        left_joystick.update((x, y), touch_id)
                else:
                    if not right_joystick.active:
                        right_joystick.update((x, y), touch_id)
                    
        if event.type == pygame.FINGERUP:
            if control_mode == "joystick":
                if left_joystick.active:
                    left_joystick.reset()
                if right_joystick.active:
                    right_joystick.reset()
                        
        if event.type == pygame.FINGERMOTION:
            if control_mode == "joystick":
                x = event.x * WIDTH
                y = event.y * HEIGHT
                
                if x < WIDTH // 2:
                    if left_joystick.active:
                        left_joystick.update((x, y), left_joystick.touch_id)
                else:
                    if right_joystick.active:
                        right_joystick.update((x, y), right_joystick.touch_id)

    if state == "playing":
        if control_mode == "keyboard":
            keys = pygame.key.get_pressed()
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                player_x -= player_speed
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                player_x += player_speed
            if keys[pygame.K_UP] or keys[pygame.K_w]:
                player_y -= player_speed
            if keys[pygame.K_DOWN] or keys[pygame.K_s]:
                player_y += player_speed
        else:
            if left_joystick.active:
                player_x += left_joystick.normalized_dx * player_speed * 1.5
                player_y += left_joystick.normalized_dy * player_speed * 1.5

        player_x = max(0, min(WIDTH - player_size, player_x))
        player_y = max(0, min(HEIGHT - player_size, player_y))

        play_time_seconds = (current_time - start_time) // 1000
        
        if current_time - last_upgrade_check >= 1000:
            if play_time_seconds >= 30 and upgrade_level == 0:
                upgrade_level = 1
                player_damage = 1.2
            elif play_time_seconds >= 60 and upgrade_level == 1:
                upgrade_level = 2
                player_damage = 1.4
            elif play_time_seconds >= 90 and upgrade_level == 2:
                upgrade_level = 3
                player_damage = 1.6
            elif play_time_seconds >= 120 and upgrade_level == 3:
                upgrade_level = 4
                player_damage = 1.8
            elif play_time_seconds >= 150 and upgrade_level == 4:
                upgrade_level = 5
                player_damage = 2.0
            elif play_time_seconds >= 180 and upgrade_level == 5:
                upgrade_level = 6
                player_damage = 2.2
            elif play_time_seconds >= 210 and upgrade_level == 6:
                upgrade_level = 7
                player_damage = 2.4
            elif play_time_seconds >= 240 and upgrade_level == 7:
                upgrade_level = 8
                player_damage = 2.6
            elif play_time_seconds >= 270 and upgrade_level == 8:
                upgrade_level = 9
                player_damage = 2.8
            elif play_time_seconds >= 300 and upgrade_level == 9:
                upgrade_level = 10
                player_damage = 3.0
            
            global_stats["upgrade_level"] = upgrade_level
            save_stats(global_stats)
            last_upgrade_check = current_time

        session_score = kills + play_time_seconds // 2

        shoot_now = False
        shoot_angle = None
        
        if control_mode == "keyboard":
            if mouse_down:
                shoot_now = True
                mx, my = mouse_pos
                px = player_x + player_size / 2
                py = player_y + player_size / 2
                shoot_angle = math.atan2(my - py, mx - px)
        else:
            if right_joystick.active and (right_joystick.normalized_dx != 0 or right_joystick.normalized_dy != 0):
                shoot_now = True
                shoot_angle = math.atan2(right_joystick.normalized_dy, right_joystick.normalized_dx)

        if shoot_now and shoot_angle is not None:
            px = player_x + player_size / 2
            py = player_y + player_size / 2
            end_x = px + math.cos(shoot_angle) * 2000
            end_y = py + math.sin(shoot_angle) * 2000
            
            active_laser = {
                'start': (px, py),
                'end': (end_x, end_y)
            }
            
            if current_time - last_sound_time >= 200:
                if shoot_sound:
                    shoot_sound.play()
                last_sound_time = current_time
            
            if current_time - last_shot_time >= 1:
                enemies_sorted = sorted(
                    enemies,
                    key=lambda e: math.hypot(
                        (e['x'] + e['size']/2) - px,
                        (e['y'] + e['size']/2) - py
                    )
                )
                
                hit_any = False
                for enemy in enemies_sorted:
                    if ray_hits_enemy((px, py), (end_x, end_y), enemy):
                        enemy['hp'] -= player_damage * 0.1
                        hit_any = True
                        if enemy['hp'] <= 0:
                            score_to_add = enemy.get('score_value', 10)
                            money += score_to_add
                            kills += 1
                            enemies.remove(enemy)
                            if death_sound:
                                death_sound.play()
                                
                if hit_any:
                    last_shot_time = current_time

        spawn_timer += 1

        if upgrade_level == 0:
            available_types = ["basic"]
            spawn_interval = 120
        elif upgrade_level == 1:
            available_types = ["basic", "armored"]
            spawn_interval = 110
        elif upgrade_level == 2:
            available_types = ["armored", "runner"]
            spawn_interval = 100
        elif upgrade_level == 3:
            available_types = ["basic+", "runner+", "basic", "armored+"]
            spawn_interval = 90
        elif upgrade_level == 4:
            available_types = ["basic+", "runner+", "basic", "armored+"]
            spawn_interval = 80
        elif upgrade_level == 5:
            available_types = ["basic+", "runner+", "basic", "armored+"]
            spawn_interval = 70
        elif upgrade_level >= 6:
            available_types = ["basic+", "runner+", "basic", "armored+"]
            spawn_interval = 60
        else:
            available_types = ["basic"]
            spawn_interval = 120

        if spawn_timer >= spawn_interval:
            etype = random.choice(available_types)
            enemies.append(spawn_enemy(etype))
            spawn_timer = 0

        px = player_x + player_size / 2
        py = player_y + player_size / 2
        for enemy in enemies[:]:
            ex = enemy['x'] + enemy['size']/2
            ey = enemy['y'] + enemy['size']/2
            dx = px - ex
            dy = py - ey
            dist = max(math.hypot(dx, dy), 0.1)
            enemy['x'] += dx / dist * enemy['speed']
            enemy['y'] += dy / dist * enemy['speed']
            if check_collision(player_x, player_y, player_size, enemy['x'], enemy['y'], enemy['size']):
                if has_shield:
                    has_shield = False
                    global_stats["shield_active"] = False
                    global_stats["shield_purchased"] = False
                    save_stats(global_stats)
                    enemies.remove(enemy)
                else:
                    global_stats["total_deaths"] += 1
                    global_stats["total_score"] += session_score
                    global_stats["total_playtime_seconds"] += (current_time - start_time) // 1000
                    global_stats["sessions_played"] += 1
                    global_stats["total_money"] += money
                    if session_score > global_stats["best_session_score"]:
                        global_stats["best_session_score"] = session_score
                    save_stats(global_stats)
                    state = "game_over"
                    final_score = session_score
                    final_time = (current_time - start_time) // 1000

        screen.fill(BACKGROUND)
        pygame.draw.rect(screen, FLOOR_COLOR, (0, 0, WIDTH, HEIGHT))
        
        if active_laser:
            pygame.draw.line(screen, RAY_COLOR, active_laser['start'], active_laser['end'], 2)
            
        pygame.draw.rect(screen, PLAYER_COLOR, (player_x, player_y, player_size, player_size))
        
        if has_shield:
            pygame.draw.rect(screen, SHIELD_COLOR, (player_x-5, player_y-5, player_size+10, player_size+10), 3)
        
        for enemy in enemies:
            color = get_enemy_color(enemy)
            pygame.draw.rect(screen, color, (enemy['x'], enemy['y'], enemy['size'], enemy['size']))

        elapsed_seconds = (current_time - start_time) // 1000
        kill_text = font.render(f"Убийства: {kills}", True, TEXT_COLOR)
        time_text = font.render(f"Время: {format_time(elapsed_seconds)}", True, TEXT_COLOR)
        money_text = font.render(f"Монеты: {money}", True, TEXT_COLOR)
        score_text = font.render(f"Очки: {session_score}", True, TEXT_COLOR)
        level_text = font.render(f"Уровень: {upgrade_level}", True, TEXT_COLOR)
        damage_text = font.render(f"Урон: {player_damage:.1f}", True, TEXT_COLOR)
        shield_text = font.render(f"Щит: {'АКТИВЕН' if has_shield else 'НЕТ'}", True, TEXT_COLOR)
        
        mode_text = small_font.render(f"Управление: {'Клавиатура' if control_mode == 'keyboard' else 'Джойстики'}", True, TEXT_COLOR)
        screen.blit(mode_text, (WIDTH - mode_text.get_width() - 20, 20))
        
        screen.blit(kill_text, (20, 20))
        screen.blit(time_text, (20, 60))
        screen.blit(money_text, (20, 100))
        screen.blit(score_text, (20, 140))
        screen.blit(level_text, (20, 180))
        screen.blit(damage_text, (20, 220))
        screen.blit(shield_text, (20, 260))
        
        if control_mode == "joystick":
            left_joystick.draw(screen)
            right_joystick.draw(screen)
            move_label = small_font.render("ДВИЖЕНИЕ", True, TEXT_COLOR)
            shoot_label = small_font.render("СТРЕЛЬБА", True, TEXT_COLOR)
            screen.blit(move_label, (left_joystick.base_x - move_label.get_width()//2, left_joystick.base_y - 90))
            screen.blit(shoot_label, (right_joystick.base_x - shoot_label.get_width()//2, right_joystick.base_y - 90))
        
    elif state == "main_menu":
        screen.fill((15, 15, 30))
    
        title = big_font.render("CYBER - ARENA", True, (100, 255, 255))
        title_shadow = big_font.render("CYBER - ARENA", True, (0, 150, 200))
    
        for i in range(4):
            glow_surf = big_font.render("CYBER - ARENA", True, (50, 200, 255))
            glow_surf.set_alpha(80 - i * 20)
            screen.blit(glow_surf, (WIDTH // 2 - title.get_width() // 2 + i, 80 + i))
            screen.blit(glow_surf, (WIDTH // 2 - title.get_width() // 2 - i, 80 - i))
    
        screen.blit(title_shadow, (WIDTH // 2 - title.get_width() // 2 + 3, 83))
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 80))
    
        play_btn = pygame.Rect(WIDTH // 2 - 120, HEIGHT // 2 - 120, 240, 50)
        shop_btn = pygame.Rect(WIDTH // 2 - 120, HEIGHT // 2 - 50, 240, 50)
        settings_btn = pygame.Rect(WIDTH // 2 - 120, HEIGHT // 2 + 20, 240, 50)
        help_btn = pygame.Rect(WIDTH // 2 - 120, HEIGHT // 2 + 90, 240, 50)
    
        for btn, text in [(play_btn, "ИГРАТЬ"), (shop_btn, "МАГАЗИН"), (settings_btn, "НАСТРОЙКИ"), (help_btn, "СПРАВКА")]:
            hover = btn.collidepoint(mouse_pos)
            color = BUTTON_HOVER if hover else BUTTON_COLOR
            pygame.draw.rect(screen, color, btn, border_radius=10)
            txt = font.render(text, True, (20, 20, 30))
            screen.blit(txt, (btn.centerx - txt.get_width() // 2, btn.centery - txt.get_height() // 2))
    
        total_money_text = font.render(f"ВСЕГО МОНЕТ: {global_stats['total_money']}", True, (200, 200, 255))
        screen.blit(total_money_text, (WIDTH // 2 - total_money_text.get_width() // 2, HEIGHT // 2 + 160))
    
        if mouse_pressed:
            if play_btn.collidepoint(mouse_pos):
                state = "playing"
                reset_game()
                left_joystick.reset()
                right_joystick.reset()
            elif shop_btn.collidepoint(mouse_pos):
                state = "shop"
            elif settings_btn.collidepoint(mouse_pos):
                state = "settings"
            elif help_btn.collidepoint(mouse_pos):
                state = "help"

    elif state == "shop":
        screen.fill((25, 20, 40))
        title = big_font.render("МАГАЗИН", True, (255, 200, 100))
        screen.blit(title, (WIDTH//2 - title.get_width()//2, 50))
        
        total_money_text = font.render(f"Ваши монеты: {global_stats['total_money']}", True, TEXT_COLOR)
        screen.blit(total_money_text, (WIDTH//2 - total_money_text.get_width()//2, 130))
        
        y = 180
        item_rect = pygame.Rect(WIDTH//2 - 250, y, 500, 100)
        pygame.draw.rect(screen, BUTTON_COLOR, item_rect, border_radius=10)
        
        item_title = font.render("Одноразовый щит", True, (20, 20, 30))
        item_price = font.render("Цена: 1,000 монет", True, (20, 20, 30))
        
        screen.blit(item_title, (item_rect.centerx - item_title.get_width()//2, item_rect.y + 15))
        screen.blit(item_price, (item_rect.centerx - item_price.get_width()//2, item_rect.y + 65))
        
        y += 120
        
        buy_btn = pygame.Rect(WIDTH//2 - 250, y, 500, 50)
        buy_btn_text = "КУПИТЬ ЩИТ (1,000)" if not global_stats['shield_purchased'] else "ЩИТ КУПЛЕН"
        hover_buy = buy_btn.collidepoint(mouse_pos) and not global_stats['shield_purchased']
        buy_color = BUTTON_HOVER if hover_buy else BUTTON_COLOR
        if global_stats['shield_purchased']:
            buy_color = (100, 100, 100)
        pygame.draw.rect(screen, buy_color, buy_btn, border_radius=10)
        buy_text = font.render(buy_btn_text, True, (20, 20, 30) if not global_stats['shield_purchased'] else (100, 100, 100))
        screen.blit(buy_text, (buy_btn.centerx - buy_text.get_width()//2, buy_btn.centery - buy_text.get_height()//2))
        
        y += 70
        
        activate_btn = pygame.Rect(WIDTH//2 - 250, y, 500, 50)
        if global_stats['shield_purchased'] and not global_stats['shield_active']:
            activate_btn_text = "АКТИВИРОВАТЬ ЩИТ ДЛЯ СЛЕД. ИГРЫ"
        elif global_stats['shield_active']:
            activate_btn_text = "ЩИТ АКТИВЕН ДЛЯ СЛЕД. ИГРЫ"
        else:
            activate_btn_text = "СНАЧАЛА КУПИТЕ ЩИТ"
        
        hover_activate = activate_btn.collidepoint(mouse_pos) and global_stats['shield_purchased'] and not global_stats['shield_active']
        activate_color = BUTTON_HOVER if hover_activate else BUTTON_COLOR
        if not global_stats['shield_purchased']:
            activate_color = (100, 100, 100)
        elif global_stats['shield_active']:
            activate_color = (50, 200, 50)
        pygame.draw.rect(screen, activate_color, activate_btn, border_radius=10)
        activate_text = font.render(activate_btn_text, True, (20, 20, 30))
        screen.blit(activate_text, (activate_btn.centerx - activate_text.get_width()//2, activate_btn.centery - activate_text.get_height()//2))
        
        y += 100
        
        back_btn = pygame.Rect(WIDTH//2 - 100, y, 200, 50)
        hover_back = back_btn.collidepoint(mouse_pos)
        back_color = BUTTON_HOVER if hover_back else BUTTON_COLOR
        pygame.draw.rect(screen, back_color, back_btn, border_radius=10)
        back_text = font.render("Назад", True, (20, 20, 30))
        screen.blit(back_text, (back_btn.centerx - back_text.get_width()//2, back_btn.centery - back_text.get_height()//2))
        
        if mouse_pressed:
            if buy_btn.collidepoint(mouse_pos) and not global_stats['shield_purchased']:
                if global_stats['total_money'] >= 1000:
                    global_stats['total_money'] -= 1000
                    global_stats['shield_purchased'] = True
                    save_stats(global_stats)
            elif activate_btn.collidepoint(mouse_pos) and global_stats['shield_purchased'] and not global_stats['shield_active']:
                global_stats['shield_active'] = True
                has_shield = True
                save_stats(global_stats)
            elif back_btn.collidepoint(mouse_pos):
                state = "main_menu"

    elif state == "settings":
        screen.fill((20, 20, 40))
        title = big_font.render("НАСТРОЙКИ", True, (100, 255, 255))
        screen.blit(title, (WIDTH//2 - title.get_width()//2, 50))
        y = 150

        control_text = font.render("Режим управления:", True, TEXT_COLOR)
        screen.blit(control_text, (WIDTH//2 - control_text.get_width()//2, y))
        y += 60
        
        keyboard_btn = pygame.Rect(WIDTH//2 - 260, y, 250, 50)
        joystick_btn = pygame.Rect(WIDTH//2 + 10, y, 250, 50)
        
        kb_color = BUTTON_HOVER if control_mode == "keyboard" else BUTTON_COLOR
        pygame.draw.rect(screen, kb_color, keyboard_btn, border_radius=10)
        kb_text = font.render("Клавиатура", True, (20, 20, 30))
        screen.blit(kb_text, (keyboard_btn.centerx - kb_text.get_width()//2, keyboard_btn.centery - kb_text.get_height()//2))
        
        js_color = BUTTON_HOVER if control_mode == "joystick" else BUTTON_COLOR
        pygame.draw.rect(screen, js_color, joystick_btn, border_radius=10)
        js_text = font.render("Джойстики", True, (20, 20, 30))
        screen.blit(js_text, (joystick_btn.centerx - js_text.get_width()//2, joystick_btn.centery - js_text.get_height()//2))
        
        y += 100

        music_text = font.render(f"Музыка: {int(music_volume * 100)}%", True, TEXT_COLOR)
        screen.blit(music_text, (WIDTH//2 - music_text.get_width()//2, y))
        dec_music = pygame.Rect(WIDTH//2 - 150, y, 40, 40)
        inc_music = pygame.Rect(WIDTH//2 + 110, y, 40, 40)
        pygame.draw.rect(screen, BUTTON_COLOR, dec_music, border_radius=10)
        pygame.draw.rect(screen, BUTTON_COLOR, inc_music, border_radius=10)
        screen.blit(font.render("-", True, (20,20,30)), (dec_music.centerx - 8, dec_music.centery - 12))
        screen.blit(font.render("+", True, (20,20,30)), (inc_music.centerx - 8, inc_music.centery - 12))
        y += 60

        shoot_text = font.render(f"Выстрел: {int(shoot_volume * 100)}%", True, TEXT_COLOR)
        screen.blit(shoot_text, (WIDTH//2 - shoot_text.get_width()//2, y))
        dec_shoot = pygame.Rect(WIDTH//2 - 150, y, 40, 40)
        inc_shoot = pygame.Rect(WIDTH//2 + 110, y, 40, 40)
        pygame.draw.rect(screen, BUTTON_COLOR, dec_shoot, border_radius=10)
        pygame.draw.rect(screen, BUTTON_COLOR, inc_shoot, border_radius=10)
        screen.blit(font.render("-", True, (20,20,30)), (dec_shoot.centerx - 8, dec_shoot.centery - 12))
        screen.blit(font.render("+", True, (20,20,30)), (inc_shoot.centerx - 8, inc_shoot.centery - 12))
        y += 60

        death_text = font.render(f"Смерть: {int(death_volume * 100)}%", True, TEXT_COLOR)
        screen.blit(death_text, (WIDTH//2 - death_text.get_width()//2, y))
        dec_death = pygame.Rect(WIDTH//2 - 150, y, 40, 40)
        inc_death = pygame.Rect(WIDTH//2 + 110, y, 40, 40)
        pygame.draw.rect(screen, BUTTON_COLOR, dec_death, border_radius=10)
        pygame.draw.rect(screen, BUTTON_COLOR, inc_death, border_radius=10)
        screen.blit(font.render("-", True, (20,20,30)), (dec_death.centerx - 8, dec_death.centery - 12))
        screen.blit(font.render("+", True, (20,20,30)), (inc_death.centerx - 8, inc_death.centery - 12))
        y += 60

        fs_text = font.render("Полноэкранный режим", True, TEXT_COLOR)
        screen.blit(fs_text, (WIDTH//2 - fs_text.get_width()//2, y))
        fs_btn = pygame.Rect(WIDTH//2 - 100, y + 40, 200, 50)
        fs_label = "ВКЛ" if fullscreen else "ВЫКЛ"
        pygame.draw.rect(screen, BUTTON_HOVER if fullscreen else BUTTON_COLOR, fs_btn, border_radius=10)
        screen.blit(font.render(fs_label, True, (20,20,30)), (fs_btn.centerx - 20, fs_btn.centery - 15))
        y += 120

        back_btn = pygame.Rect(WIDTH//2 - 100, y, 200, 50)
        hover = back_btn.collidepoint(mouse_pos)
        pygame.draw.rect(screen, BUTTON_HOVER if hover else BUTTON_COLOR, back_btn, border_radius=10)
        back_text = font.render("Назад", True, (20,20,30))
        screen.blit(back_text, (back_btn.centerx - back_text.get_width()//2, back_btn.centery - back_text.get_height()//2))

        if mouse_pressed:
            if keyboard_btn.collidepoint(mouse_pos) and control_mode != "keyboard":
                control_mode = "keyboard"
                global_stats["control_mode"] = control_mode
                save_stats(global_stats)
            elif joystick_btn.collidepoint(mouse_pos) and control_mode != "joystick":
                control_mode = "joystick"
                global_stats["control_mode"] = control_mode
                save_stats(global_stats)
                left_joystick.reset()
                right_joystick.reset()
            
            if inc_music.collidepoint(mouse_pos) and music_volume < 1.0:
                music_volume = round(music_volume + 0.1, 1)
                pygame.mixer.music.set_volume(music_volume)
                global_stats["music_volume"] = music_volume
                save_stats(global_stats)
            elif dec_music.collidepoint(mouse_pos) and music_volume > 0.0:
                music_volume = round(music_volume - 0.1, 1)
                pygame.mixer.music.set_volume(music_volume)
                global_stats["music_volume"] = music_volume
                save_stats(global_stats)
            if inc_shoot.collidepoint(mouse_pos) and shoot_volume < 1.0:
                shoot_volume = round(shoot_volume + 0.1, 1)
                if shoot_sound:
                    shoot_sound.set_volume(shoot_volume)
                global_stats["shoot_volume"] = shoot_volume
                save_stats(global_stats)
            elif dec_shoot.collidepoint(mouse_pos) and shoot_volume > 0.0:
                shoot_volume = round(shoot_volume - 0.1, 1)
                if shoot_sound:
                    shoot_sound.set_volume(shoot_volume)
                global_stats["shoot_volume"] = shoot_volume
                save_stats(global_stats)
            if inc_death.collidepoint(mouse_pos) and death_volume < 1.0:
                death_volume = round(death_volume + 0.1, 1)
                if death_sound:
                    death_sound.set_volume(death_volume)
                global_stats["death_volume"] = death_volume
                save_stats(global_stats)
            elif dec_death.collidepoint(mouse_pos) and death_volume > 0.0:
                death_volume = round(death_volume - 0.1, 1)
                if death_sound:
                    death_sound.set_volume(death_volume)
                global_stats["death_volume"] = death_volume
                save_stats(global_stats)
            if fs_btn.collidepoint(mouse_pos):
                toggle_fullscreen()
            if back_btn.collidepoint(mouse_pos):
                state = "main_menu"

    elif state == "help":
        screen.fill((20, 25, 50))
        title = big_font.render("СПРАВКА", True, (100, 255, 255))
        screen.blit(title, (WIDTH//2 - title.get_width()//2, 50))
    
        lines = [
        "Связь с автором:"
        ]
    
        y = 120
        for line in lines:
            txt = font.render(line, True, TEXT_COLOR)
            screen.blit(txt, (WIDTH//2 - txt.get_width()//2, y))
            y += 35
    
        y += 40
        youtube_text = font.render("YouTube: @Adekvat_2008", True, (255, 100, 100))
        youtube_rect = youtube_text.get_rect(center=(WIDTH//2, y))
        screen.blit(youtube_text, youtube_rect)
    
        y += 40
        donate_text = font.render("DonationAlerts: @adekvat_2008", True, (100, 255, 100))
        donate_rect = donate_text.get_rect(center=(WIDTH//2, y))
        screen.blit(donate_text, donate_rect)
    
        y += 40
        telegram_text = font.render("Telegram: +7 982 758-29-51", True, (100, 200, 255))
        telegram_rect = telegram_text.get_rect(center=(WIDTH//2, y))
        screen.blit(telegram_text, telegram_rect)
    
        back_btn = pygame.Rect(WIDTH//2 - 100, HEIGHT - 120, 200, 50)
        hover = back_btn.collidepoint(mouse_pos)
        pygame.draw.rect(screen, BUTTON_HOVER if hover else BUTTON_COLOR, back_btn, border_radius=10)
        back_text = font.render("Назад", True, (20,20,30))
        screen.blit(back_text, (back_btn.centerx - back_text.get_width()//2, back_btn.centery - back_text.get_height()//2))
    
        if mouse_pressed:
            if back_btn.collidepoint(mouse_pos):
                state = "main_menu"
        
            if youtube_rect.collidepoint(mouse_pos):
                import webbrowser
                webbrowser.open("https://www.youtube.com/@Adekvat_2008")
        
            if donate_rect.collidepoint(mouse_pos):
                import webbrowser
                webbrowser.open("https://www.donationalerts.com/r/adekvat_2008")
        
            if telegram_rect.collidepoint(mouse_pos):
                import webbrowser
                webbrowser.open("https://t.me/+79827582951")
        
    elif state == "game_over":
        screen.fill((10, 10, 20))
        over_text = big_font.render("ИГРА ОКОНЧЕНА", True, (255, 100, 100))
        score_text = game_over_font.render(f"Очков: {final_score}", True, TEXT_COLOR)
        time_text = game_over_font.render(f"Время: {format_time(final_time)}", True, TEXT_COLOR)
        total_text = font.render(f"Всего: {global_stats['total_score']} очков, {global_stats['total_deaths']} смертей", True, TEXT_COLOR)
        best_text = font.render(f"Рекорд: {global_stats['best_session_score']}", True, TEXT_COLOR)
        y_offset = HEIGHT // 2 - 120
        screen.blit(over_text, (WIDTH//2 - over_text.get_width()//2, y_offset))
        y_offset += over_text.get_height() + 10
        screen.blit(score_text, (WIDTH//2 - score_text.get_width()//2, y_offset))
        y_offset += score_text.get_height() + 5
        screen.blit(time_text, (WIDTH//2 - time_text.get_width()//2, y_offset))
        y_offset += time_text.get_height() + 5
        screen.blit(total_text, (WIDTH//2 - total_text.get_width()//2, y_offset))
        y_offset += total_text.get_height() + 5
        screen.blit(best_text, (WIDTH//2 - best_text.get_width()//2, y_offset))

        restart_btn = pygame.Rect(WIDTH // 2 - 100, HEIGHT // 2 + 90, 200, 50)
        menu_btn = pygame.Rect(WIDTH // 2 - 100, HEIGHT // 2 + 150, 200, 50)
        for btn, text in [(restart_btn, "Заново"), (menu_btn, "В меню")]:
            hover = btn.collidepoint(mouse_pos)
            color = BUTTON_HOVER if hover else BUTTON_COLOR
            pygame.draw.rect(screen, color, btn, border_radius=10)
            txt = font.render(text, True, (20, 20, 30))
            screen.blit(txt, (btn.centerx - txt.get_width()//2, btn.centery - txt.get_height()//2))
        if mouse_pressed:
            if restart_btn.collidepoint(mouse_pos):
                state = "playing"
                reset_game()
                left_joystick.reset()
                right_joystick.reset()
            elif menu_btn.collidepoint(mouse_pos):
                state = "main_menu"
                left_joystick.reset()
                right_joystick.reset()

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()