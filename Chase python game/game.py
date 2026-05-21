"""
Skybound Scramble - A endless climber arcade game.

Features:
  - 5 progressively challenging worlds with unique visuals
  - Upgrade system for jump, speed, and coin multiplier
  - Powerups: Shield, Double Coins, Jump Boost
  - Hazards: Moving spikes on higher worlds
  - Achievement system
  - Persistent save data

Controls:
  - Arrow Keys / A-D: Move left/right
  - Space / W: Jump
  - Enter: Start game
  - S: Open shop
  - 1-5: Select/unlock worlds
  - ESC: Exit
"""

import json
import os
import random
import sys

import pygame

# ==================== CONSTANTS ====================
WIDTH = 800
HEIGHT = 600
FPS = 60
SAVE_FILE = os.path.expanduser('~/.skybound_scramble_save.json')

# Color palette
COLOR_BG_TOP = (16, 20, 29)
COLOR_BG_BOTTOM = (12, 16, 24)
COLOR_PLATFORM = (51, 65, 85)
COLOR_PLATFORM_MOVE = (37, 99, 235)
COLOR_COIN = (251, 191, 36)
COLOR_LAVA_TOP = (251, 113, 133)
COLOR_LAVA_BOTTOM = (185, 28, 40)
COLOR_TEXT = (226, 232, 240)
COLOR_MENU_BG = (15, 23, 42)
COLOR_MENU_BORDER = (148, 163, 184)
COLOR_MENU_PANEL = (8, 14, 31, 220)

# Animation constants
PLAYER_FRAME_COUNT = 3
WALK_ANIMATION_SPEED = 0.2
ENEMY_WALK_FRAME_COUNT = 4
ENEMY_ANIMATION_SPEED = 0.15

# Win condition
win_threshold = -10000

# Asset paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CHASE_MUSIC = os.path.join(SCRIPT_DIR, 'assets', 'Chase.mp3')
SHOP_MUSIC = os.path.join(SCRIPT_DIR, 'assets', 'Shop.mp3')
MAINMENU_MUSIC = os.path.join(SCRIPT_DIR, 'assets', 'Mainmenu.mp3')

# ==================== GAME STATE ====================
current_music = None
menu_anim_y = 0.0
menu_anim_target = 0.0
menu_anim_speed = 800.0
dt = 0.016  # ~60 FPS

input_state = {'left': False, 'right': False, 'jump': False}

# World and level data
platforms = []
coins = []
enemies = []
powerups = []
hazards = []
particles = []

next_enemy_platform_index = 6
platform_counter = 0
camera_y = 0
highest_platform_y = 0
coin_count = 0
best_height = 0
total_coins = 0
wins = 0
current_world = 1
unlocked_worlds = [1]

# Powerup and achievement tracking
active_powerups = {'shield': False, 'double': False, 'jump': False}
powerup_timers = {'shield': 0.0, 'double': 0.0, 'jump': 0.0}
achievements = {
    'first_win': False,
    'world_explorer': False,
    'coin_collector': False,
    'champion': False,
}
achievement_info = [
    ('first_win', 'First Win', 'Win at least once'),
    ('world_explorer', 'World Explorer', 'Unlock 3 worlds'),
    ('coin_collector', 'Coin Collector', 'Save 1000 total coins'),
    ('champion', 'Champion', 'Win 5 times'),
]

# Game state machine
game_started = False
is_game_over = False
is_game_won = False
state = 'menu'
menu_message = 'Goal: reach 1000m to earn +1 bonus and 100 coins. Use arrow keys or A/D to move, W or Space to jump.'
game_start_time = 0

# Physics and upgrades
lava = {'y': HEIGHT - 18, 'rise_speed': 0.25}
upgrades = {'jumpTier': 0, 'speedTier': 0, 'goldTier': 0, 'maxTier': 7}
gold_multiplier = 1.0

# ==================== WORLD DATA ====================
WORLD_DATA = {
    1: {
        'bg_top': (20, 28, 48), 'bg_bottom': (8, 12, 24),
        'mult': 1, 'cost': 0,
        'lava_speed': 0.25,
        'wind_strength': 0.0,
        'obstacle_rate': 0.0,
        'powerup_rate': 0.02,
        'title': 'Neon City',
        'trail': (96, 181, 255),
        'music': CHASE_MUSIC,
    },
    2: {
        'bg_top': (72, 26, 92), 'bg_bottom': (18, 8, 38),
        'mult': 2, 'cost': 3,
        'lava_speed': 0.28,
        'wind_strength': 0.05,
        'obstacle_rate': 0.06,
        'powerup_rate': 0.04,
        'title': 'Twilight Rift',
        'trail': (195, 116, 247),
        'music': CHASE_MUSIC,
    },
    3: {
        'bg_top': (16, 88, 110), 'bg_bottom': (6, 32, 44),
        'mult': 3, 'cost': 5,
        'lava_speed': 0.30,
        'wind_strength': 0.09,
        'obstacle_rate': 0.10,
        'powerup_rate': 0.05,
        'title': 'Crystal Skies',
        'trail': (72, 232, 255),
        'music': CHASE_MUSIC,
    },
    4: {
        'bg_top': (92, 58, 20), 'bg_bottom': (38, 20, 6),
        'mult': 4, 'cost': 10,
        'lava_speed': 0.32,
        'wind_strength': 0.14,
        'obstacle_rate': 0.12,
        'powerup_rate': 0.06,
        'title': 'Eclipse Gorge',
        'trail': (255, 180, 75),
        'music': CHASE_MUSIC,
    },
    5: {
        'bg_top': (36, 98, 42), 'bg_bottom': (10, 32, 12),
        'mult': 5, 'cost': 25,
        'lava_speed': 0.35,
        'wind_strength': 0.18,
        'obstacle_rate': 0.15,
        'powerup_rate': 0.08,
        'title': 'Aurora Apex',
        'trail': (102, 255, 178),
        'music': CHASE_MUSIC,
    },
}

unlocked_worlds = [1]

powerups = []
hazards = []
particles = []
active_powerups = {'shield': False, 'double': False, 'jump': False}
powerup_timers = {'shield': 0.0, 'double': 0.0, 'jump': 0.0}
achievements = {
    'first_win': False,
    'world_explorer': False,
    'coin_collector': False,
    'champion': False,
}
achievement_info = [
    ('first_win', 'First Win', 'Win at least once'),
    ('world_explorer', 'World Explorer', 'Unlock 3 worlds'),
    ('coin_collector', 'Coin Collector', 'Save 1000 total coins'),
    ('champion', 'Champion', 'Win 5 times'),
]

game_started = False
is_game_over = False
is_game_won = False
state = 'menu'
menu_message = 'Goal: reach 1000m to earn +1 bonus and 100 coins. Use arrow keys or A/D to move, W or Space to jump.'
game_start_time = 0

lava = {'y': HEIGHT - 18, 'rise_speed': 0.25}
upgrades = {'jumpTier': 0, 'speedTier': 0, 'goldTier': 0, 'maxTier': 7}
gold_multiplier = 1.0

player = {
    'x': 120,
    'y': 520,
    'width': 32,
    'height': 48,
    'vx': 0.0,
    'vy': 0.0,
    'speed': 2.16,
    'maxSpeed': 27.0,
    'jumpStrength': -16.5,
    'grounded': False,
    'jumpCutoff': 0.72,
    'facing': 1,
    'animationFrame': 0,
    'animationTimer': 0.0,
    'isMoving': False,
}

physics = {
    'gravity': 0.48,
    'fallGravity': 1.15,
    'friction': 0.83,
}


def clamp(value, minimum, maximum):
    return max(minimum, min(maximum, value))


def load_save():
    global best_height, total_coins, upgrades, gold_multiplier, wins, unlocked_worlds, current_world
    if os.path.exists(SAVE_FILE):
        try:
            with open(SAVE_FILE, 'r', encoding='utf-8') as handle:
                data = json.load(handle)
            best_height = data.get('bestHeight', 0)
            total_coins = data.get('totalCoins', 0)
            upgrades = data.get('upgrades', upgrades)
            upgrades['maxTier'] = max(upgrades.get('maxTier', 3), 7)
            wins = data.get('wins', 0)
            unlocked_worlds = data.get('unlocked_worlds', [1])
            current_world = data.get('current_world', 1)
            achievements.update(data.get('achievements', achievements))
        except Exception:
            best_height = 0
            total_coins = 0
            upgrades = {'jumpTier': 0, 'speedTier': 0, 'goldTier': 0, 'maxTier': 3}
            wins = 0
            unlocked_worlds = [1]
            current_world = 1
            achievements.update({
                'first_win': False,
                'world_explorer': False,
                'coin_collector': False,
                'champion': False,
            })
    apply_upgrades()


def save_data():
    try:
        payload = {
            'bestHeight': best_height,
            'totalCoins': total_coins,
            'upgrades': upgrades,
            'wins': wins,
            'unlocked_worlds': unlocked_worlds,
            'current_world': current_world,
            'achievements': achievements,
        }
        with open(SAVE_FILE, 'w', encoding='utf-8') as handle:
            json.dump(payload, handle, indent=2)
    except Exception as e:
        print(f'Warning: Could not save progress: {e}')


def apply_upgrades():
    global gold_multiplier
    player['jumpStrength'] = -16.5 - upgrades['jumpTier'] * 1.8
    player['maxSpeed'] = 27.0 + upgrades['speedTier'] * 3.0
    player['speed'] = 2.16 + upgrades['speedTier'] * 0.18
    gold_multiplier = (1 + upgrades['goldTier'] * 0.5) * WORLD_DATA[current_world]['mult']


def get_effective_jump_strength():
    boost = 1.2 if active_powerups['jump'] else 1.0
    return player['jumpStrength'] * boost


def activate_powerup(powerup_type):
    duration = 8.0
    if powerup_type == 'shield':
        active_powerups['shield'] = True
        powerup_timers['shield'] = duration
    elif powerup_type == 'double':
        active_powerups['double'] = True
        powerup_timers['double'] = duration
    elif powerup_type == 'jump':
        active_powerups['jump'] = True
        powerup_timers['jump'] = duration


def update_powerups():
    for ptype in list(powerup_timers):
        if powerup_timers[ptype] > 0:
            powerup_timers[ptype] -= dt
            if powerup_timers[ptype] <= 0:
                active_powerups[ptype] = False
                powerup_timers[ptype] = 0.0


def add_particle(x, y, color, vx, vy, life, radius=3):
    particles.append({'x': x, 'y': y, 'vx': vx, 'vy': vy, 'life': life, 'radius': radius, 'color': color})


def update_particles():
    for particle in particles[:]:
        particle['x'] += particle['vx'] * dt * 60
        particle['y'] += particle['vy'] * dt * 60
        particle['vy'] += 0.15 * dt * 60
        particle['life'] -= dt
        if particle['life'] <= 0:
            particles.remove(particle)


def draw_particles(surface):
    for particle in particles:
        alpha = int(240 * max(0.0, particle['life'] / 1.0))
        surf = pygame.Surface((particle['radius'] * 2, particle['radius'] * 2), pygame.SRCALPHA)
        pygame.draw.circle(surf, particle['color'] + (alpha,), (particle['radius'], particle['radius']), particle['radius'])
        surface.blit(surf, (int(particle['x'] - particle['radius']), int(particle['y'] - particle['radius'])))


def spawn_powerup(x, y, powerup_type):
    powerups.append({
        'x': x,
        'y': y,
        'width': 18,
        'height': 18,
        'type': powerup_type,
        'collected': False,
    })


def spawn_hazard(platform):
    size = 20
    hazards.append({
        'x': platform['x'] + random.uniform(10, max(10, platform['width'] - size - 10)),
        'y': platform['y'] - size,
        'width': size,
        'height': size,
        'dx': random.choice([-0.8, 0.8]),
        'platform': platform,
    })


def update_hazards():
    world = WORLD_DATA[current_world]
    for hazard in hazards[:]:
        hazard['x'] += hazard['dx'] * dt * 60
        if hazard['x'] < hazard['platform']['x']:
            hazard['x'] = hazard['platform']['x']
            hazard['dx'] *= -1
        if hazard['x'] > hazard['platform']['x'] + hazard['platform']['width'] - hazard['width']:
            hazard['x'] = hazard['platform']['x'] + hazard['platform']['width'] - hazard['width']
            hazard['dx'] *= -1
        hazard['y'] = hazard['platform']['y'] - hazard['height']
        if (player['x'] + player['width'] > hazard['x'] and
                player['x'] < hazard['x'] + hazard['width'] and
                player['y'] + player['height'] > hazard['y'] and
                player['y'] < hazard['y'] + hazard['height']):
            if active_powerups['shield']:
                active_powerups['shield'] = False
                powerup_timers['shield'] = 0.0
                menu_message = 'Shield blocked a hazard!'
            else:
                end_game()


def draw_hazards(surface):
    for hazard in hazards:
        screen_y = hazard['y'] - camera_y
        if screen_y > HEIGHT or screen_y < -50:
            continue
        pygame.draw.polygon(surface, (210, 80, 80), [
            (hazard['x'], screen_y + hazard['height']),
            (hazard['x'] + hazard['width'] / 2, screen_y),
            (hazard['x'] + hazard['width'], screen_y + hazard['height']),
        ])


def draw_powerups(surface):
    powerup_colors = {
        'shield': (200, 150, 255),
        'double': (255, 255, 150),
        'jump': (150, 255, 200),
    }
    for powerup in powerups:
        if powerup['collected']:
            continue
        screen_y = powerup['y'] - camera_y
        if screen_y > HEIGHT or screen_y < -50:
            continue
        color = powerup_colors.get(powerup['type'], (255, 255, 255))
        pygame.draw.circle(surface, color, (int(powerup['x'] + powerup['width'] / 2), int(screen_y + powerup['height'] / 2)), 10)


def update_achievements():
    achievements['first_win'] = achievements['first_win'] or wins >= 1
    achievements['world_explorer'] = achievements['world_explorer'] or len(unlocked_worlds) >= 3
    achievements['coin_collector'] = achievements['coin_collector'] or total_coins >= 1000
    achievements['champion'] = achievements['champion'] or wins >= 5


def draw_achievements(surface, small_font, panel_rect, start_y):
    surface.blit(small_font.render('Achievements', True, (180, 220, 255)), (panel_rect.x + 24, start_y))
    for i, (key, label, desc) in enumerate(achievement_info):
        earned = achievements.get(key, False)
        status = '✓' if earned else '✗'
        color = (128, 230, 130) if earned else (180, 180, 180)
        line = small_font.render(f'{status} {label}', True, color)
        surface.blit(line, (panel_rect.x + 24, start_y + 24 + i * 24))


def play_music(path, loops=-1):
    global current_music
    if not pygame.mixer.get_init():
        try:
            pygame.mixer.init()
        except Exception:
            return
    try:
        if current_music == path:
            return
        if not os.path.exists(path):
            print(f'Music file not found: {path}')
            current_music = None
            return
        try:
            pygame.mixer.music.load(path)
            pygame.mixer.music.play(loops)
            current_music = path
        except pygame.error as e:
            print(f'Pygame error loading {path}: {e}')
            current_music = None
    except Exception as e:
        print(f'Error loading music {path}: {e}')
        current_music = None


def stop_music(fade_ms=200):
    global current_music
    try:
        pygame.mixer.music.fadeout(fade_ms)
    except Exception:
        pass
    current_music = None


def get_next_cost(upgrade_type):
    costs = {
        'jump': [40, 80, 160, 320, 640, 1280, 2560],
        'speed': [40, 80, 160, 320, 640, 1280, 2560],
        'gold': [30, 60, 120, 240, 480, 960, 1920],
    }
    tier = upgrades[f'{upgrade_type}Tier']
    return costs[upgrade_type][tier] if tier < upgrades['maxTier'] else None


def purchase_world(world_num):
    global wins

    if world_num in unlocked_worlds:
        return

    cost = WORLD_DATA[world_num]['cost']

    if wins >= cost:
        unlocked_worlds.append(world_num)
        save_data()


def select_world(world_num):
    global current_world

    if world_num in unlocked_worlds:
        current_world = world_num
        apply_upgrades()
        save_data()


def purchase_upgrade(upgrade_type):
    global total_coins
    tier_key = f'{upgrade_type}Tier'
    if upgrades[tier_key] >= upgrades['maxTier']:
        return
    cost = get_next_cost(upgrade_type)
    if cost is None or total_coins < cost:
        return
    total_coins -= cost
    upgrades[tier_key] += 1
    apply_upgrades()
    save_data()


def get_score_height():
    return max(0, int((520 - player['y']) // 10))


def platform_overlaps(x, y, width, height):
    for platform in platforms:
        if (x < platform['x'] + platform['width'] and
                x + width > platform['x'] and
                y < platform['y'] + platform['height'] + 20 and
                y + height > platform['y'] - 20):
            return True
    return False


def generate_platform(x, y, width, type_roll):
    global platform_counter, next_enemy_platform_index
    if platform_overlaps(x, y, width, 18):
        return False

    platform_type = 'static'
    if type_roll < 0.18:
        platform_type = 'moveX'
    elif type_roll < 0.32:
        platform_type = 'moveY'

    platform = {'x': x, 'y': y, 'width': width, 'height': 18, 'type': platform_type}

    if platform_type == 'moveX':
        platform['dx'] = random.uniform(0.6, 2.0)
        platform['minX'] = max(10, x - 80)
        platform['maxX'] = min(WIDTH - width - 10, x + 80)
    elif platform_type == 'moveY':
        platform['dy'] = random.uniform(0.4, 1.2)
        platform['minY'] = y - 40
        platform['maxY'] = y + 40

    platforms.append(platform)
    platform_counter += 1

    if platform_counter % 3 == 0 and random.random() > 0.25:
        coins.append({
            'x': x + width / 2 - 8,
            'y': y - 34,
            'width': 16,
            'height': 16,
            'collected': False,
        })

    world = WORLD_DATA[current_world]
    if random.random() < world['powerup_rate']:
        spawn_powerup(x + width / 2 - 9, y - 42, random.choice(['shield', 'double', 'jump']))

    if random.random() < world['obstacle_rate']:
        spawn_hazard(platform)

    if len(platforms) == next_enemy_platform_index:
        spawn_enemy(platform)
        next_enemy_platform_index += 5 + random.randint(0, 3)

    return True


def spawn_enemy(platform):
    enemies.append({
        'platformIndex': len(platforms) - 1,
        'x': platform['x'] + platform['width'] / 2 - 14,
        'y': platform['y'] - 42,
        'width': 28,
        'height': 42,
        'speed': 1.4,
        'direction': 1 if random.random() > 0.5 else -1,
        'chasing': False,
        'animationFrame': 0,
        'animationTimer': 0.0,
        'facing': 1,
    })


def generate_platform_row(y):
    platform_count = 1 + random.randint(0, 1)
    extra_same_level = 1 if random.random() < 0.35 else 0
    count = platform_count + extra_same_level
    previous = platforms[-1]
    prev_center = previous['x'] + previous['width'] / 2
    anchor = clamp(prev_center + random.uniform(-110, 110), 10, WIDTH - 110 - 10)

    for i in range(count):
        attempts = 0
        placed = False
        while not placed and attempts < 10:
            width = random.uniform(110, 250)
            if i == 0:
                x = clamp(anchor, 10, WIDTH - width - 10)
            else:
                x = clamp(random.uniform(10, WIDTH - width - 10), 10, WIDTH - width - 10)
            placed = generate_platform(x, y, width, random.random())
            attempts += 1


def generate_platforms_above():
    global highest_platform_y
    while highest_platform_y > player['y'] - 700:
        gap = 80 + random.uniform(0, 70)
        highest_platform_y -= gap
        generate_platform_row(highest_platform_y)


def create_initial_platforms():
    global platforms, coins, enemies, next_enemy_platform_index, highest_platform_y, platform_counter
    platforms = [
        {'x': 0, 'y': 560, 'width': 800, 'height': 40, 'type': 'static'},
        {'x': 130, 'y': 470, 'width': 180, 'height': 18, 'type': 'static'},
        {'x': 410, 'y': 380, 'width': 220, 'height': 18, 'type': 'static'},
        {'x': 100, 'y': 290, 'width': 160, 'height': 18, 'type': 'static'},
        {'x': 520, 'y': 210, 'width': 220, 'height': 18, 'type': 'static'},
    ]
    coins = []
    enemies.clear()
    next_enemy_platform_index = 6
    platform_counter = 0
    highest_platform_y = min(platform['y'] for platform in platforms)
    generate_platforms_above()


def start_game():
    global game_started, is_game_over, is_game_won, state, menu_message, camera_y, coin_count, game_start_time, platform_counter, next_enemy_platform_index, menu_anim_y, win_threshold
    game_started = True
    is_game_over = False
    is_game_won = False
    state = 'playing'
    win_threshold = -current_world * 10000
    menu_message = 'Collect coins and climb higher.'
    menu_anim_y = 0.0  # reset animation when game starts
    camera_y = 0
    lava['y'] = HEIGHT - 18
    lava['rise_speed'] = WORLD_DATA[current_world]['lava_speed']
    coin_count = 0
    game_start_time = pygame.time.get_ticks()
    platform_counter = 0
    enemies.clear()
    hazards.clear()
    powerups.clear()
    particles.clear()
    next_enemy_platform_index = 6
    player.update({
        'x': 120,
        'y': 520,
        'vx': 0.0,
        'vy': 0.0,
        'grounded': False,
        'facing': 1,
        'animationFrame': 0,
        'animationTimer': 0.0,
        'isMoving': False,
    })
    active_powerups.update({'shield': False, 'double': False, 'jump': False})
    powerup_timers.update({'shield': 0.0, 'double': 0.0, 'jump': 0.0})
    apply_upgrades()
    create_initial_platforms()
    # start world music if available
    try:
        play_music(WORLD_DATA[current_world]['music'])
    except Exception:
        pass


def end_game():
    global game_started, is_game_over, state, menu_message, best_height, total_coins, menu_anim_y, menu_anim_target
    game_started = False
    is_game_over = True
    state = 'menu'
    # trigger menu animation from top
    menu_anim_y = -HEIGHT
    menu_anim_target = 0.0
    # stop any gameplay music and play menu music
    try:
        play_music(MAINMENU_MUSIC)
    except Exception:
        pass
    height = get_score_height()
    if height > best_height:
        best_height = height
    total_coins += coin_count
    save_data()
    menu_message = f'Game over! You climbed {height}m and collected {coin_count} coins. Press Enter to try again.'


def update_player():
    global camera_y, coin_count, is_game_won, game_started, total_coins, menu_message, state, best_height, dt, wins
    # Apply delta time to make physics frame-rate independent
    scale = dt / 0.016  # normalize to 60 FPS
    
    accel = 0.0
    if input_state['right']:
        accel = player['speed'] * scale
    elif input_state['left']:
        accel = -player['speed'] * scale

    player['vx'] += accel
    player['vx'] *= physics['friction']
    player['vx'] = clamp(player['vx'], -player['maxSpeed'], player['maxSpeed'])

    is_rising = player['vy'] < 0
    player['vy'] += physics['gravity'] * (1 if is_rising else physics['fallGravity'])

    if input_state['jump'] and player['grounded']:
        player['vy'] = get_effective_jump_strength()
        player['grounded'] = False
        for i in range(8):
            add_particle(player['x'] + player['width'] / 2, player['y'] + player['height'], (150, 210, 255), random.uniform(-1.4, 1.4), random.uniform(-3.5, -1.5), 0.4, 2)

    if not input_state['jump'] and is_rising:
        player['vy'] *= player['jumpCutoff']

    player['x'] += player['vx']
    player['y'] += player['vy']
    player['x'] = clamp(player['x'], 0, WIDTH - player['width'])
    player['grounded'] = False

    world = WORLD_DATA[current_world]
    if not player['grounded']:
        player['vx'] += world['wind_strength'] * dt * 40

    for platform in platforms:
        if platform['type'] == 'moveX':
            platform['x'] += platform['dx']
            if platform['x'] < platform['minX'] or platform['x'] > platform['maxX']:
                platform['dx'] *= -1
                platform['x'] = clamp(platform['x'], platform['minX'], platform['maxX'])
        elif platform['type'] == 'moveY':
            platform['y'] += platform['dy']
            if platform['y'] < platform['minY'] or platform['y'] > platform['maxY']:
                platform['dy'] *= -1
                platform['y'] = clamp(platform['y'], platform['minY'], platform['maxY'])

        player_bottom = player['y'] + player['height']
        platform_top = platform['y']
        if (player['x'] + player['width'] > platform['x'] and
                player['x'] < platform['x'] + platform['width'] and
                player_bottom > platform_top and
                player_bottom < platform_top + platform['height'] + 12 and
                player['vy'] >= 0):
            player['y'] = platform_top - player['height']
            player['vy'] = 0
            player['grounded'] = True

    for coin in coins:
        if not coin['collected']:
            coin_right = coin['x'] + coin['width']
            coin_bottom = coin['y'] + coin['height']
            if (player['x'] + player['width'] > coin['x'] and
                    player['x'] < coin_right and
                    player['y'] + player['height'] > coin['y'] and
                    player['y'] < coin_bottom):
                coin['collected'] = True
                amount = int(gold_multiplier * (2 if active_powerups['double'] else 1))
                coin_count += amount
                for i in range(10):
                    add_particle(coin['x'] + coin['width'] / 2, coin['y'] + coin['height'] / 2, (255, 230, 140), random.uniform(-1.8, 1.8), random.uniform(-2.4, -0.8), 0.5, 2)
                if active_powerups['double']:
                    menu_message = 'Double coin powerup active!'

    for powerup in powerups:
        if not powerup['collected']:
            powerup_right = powerup['x'] + powerup['width']
            powerup_bottom = powerup['y'] + powerup['height']
            if (player['x'] + player['width'] > powerup['x'] and
                    player['x'] < powerup_right and
                    player['y'] + player['height'] > powerup['y'] and
                    player['y'] < powerup_bottom):
                powerup['collected'] = True
                activate_powerup(powerup['type'])
                menu_message = f"Picked up {powerup['type'].capitalize()} powerup!"
                for i in range(12):
                    add_particle(powerup['x'] + powerup['width'] / 2, powerup['y'] + powerup['height'] / 2, (180, 240, 200), random.uniform(-2.0, 2.0), random.uniform(-3.0, -0.5), 0.6, 3)

    if player['y'] < camera_y + 220:
        camera_y = player['y'] - 220

    player['isMoving'] = abs(player['vx']) > 0.15
    if player['vx'] > 0.15:
        player['facing'] = 1
    elif player['vx'] < -0.15:
        player['facing'] = -1

    if player['isMoving'] and player['grounded']:
        player['animationTimer'] += WALK_ANIMATION_SPEED
        if player['animationTimer'] >= 1:
            player['animationFrame'] = (player['animationFrame'] + 1) % PLAYER_FRAME_COUNT
            player['animationTimer'] = 0.0
    else:
        player['animationFrame'] = 0
        player['animationTimer'] = 0.0

    update_enemies()
    update_hazards()
    update_powerups()
    update_particles()
    lava['y'] -= lava['rise_speed']
    generate_platforms_above()

    if win_threshold - 80 <= player['y'] <= win_threshold + 80:
        is_game_won = True
        game_started = False
        state = 'menu'
        total_coins += coin_count
        wins += 1
        target_height = current_world * 1000
        if best_height < target_height:
            best_height = target_height
        update_achievements()
        save_data()
        menu_message = f'🎉 YOU WIN! Escaped at {target_height}m with {coin_count} coins. Press Enter to play again.'

    if player['y'] + player['height'] > lava['y'] or player['y'] - camera_y > HEIGHT:
        if active_powerups['shield']:
            active_powerups['shield'] = False
            player['vy'] = player['jumpStrength'] * 0.8
            player['y'] = lava['y'] - player['height'] - 2
            add_particle(player['x'] + player['width'] / 2, player['y'] + player['height'], (200, 150, 255), random.uniform(-2.2, 2.2), random.uniform(-3.0, -1.0), 0.6, 3)
        else:
            end_game()


def update_enemies():
    for enemy in enemies:
        if enemy['platformIndex'] >= len(platforms):
            continue
        platform = platforms[enemy['platformIndex']]
        enemy['y'] = platform['y'] - enemy['height']

        on_same_platform = (player['y'] + player['height'] > platform['y'] and player['y'] < platform['y'] + platform['height'])
        if not enemy['chasing']:
            enemy['x'] += enemy['direction'] * enemy['speed']
            if enemy['x'] < platform['x']:
                enemy['x'] = platform['x']
                enemy['direction'] = 1
            if enemy['x'] > platform['x'] + platform['width'] - enemy['width']:
                enemy['x'] = platform['x'] + platform['width'] - enemy['width']
                enemy['direction'] = -1

            player_center = player['x'] + player['width'] / 2
            enemy_center = enemy['x'] + enemy['width'] / 2
            sees_player = on_same_platform and ((player_center > enemy_center) == (enemy['direction'] > 0))
            if sees_player:
                enemy['chasing'] = True

        if enemy['chasing']:
            target_x = player['x'] + player['width'] / 2 - enemy['width'] / 2
            direction = 1 if target_x > enemy['x'] else -1
            enemy['direction'] = direction
            enemy['x'] += direction * enemy['speed'] * 1.2
            enemy['x'] = clamp(enemy['x'], platform['x'], platform['x'] + platform['width'] - enemy['width'])
            enemy['y'] = platform['y'] - enemy['height']
            if not on_same_platform:
                enemy['chasing'] = False

        enemy['facing'] = enemy['direction']
        enemy['animationTimer'] += ENEMY_ANIMATION_SPEED
        if enemy['animationTimer'] >= 1:
            enemy['animationFrame'] = (enemy['animationFrame'] + 1) % ENEMY_WALK_FRAME_COUNT
            enemy['animationTimer'] = 0.0

        if (player['x'] + player['width'] > enemy['x'] and
                player['x'] < enemy['x'] + enemy['width'] and
                player['y'] + player['height'] > enemy['y'] and
                player['y'] < enemy['y'] + enemy['height']):
            end_game()


def draw_background(surface):
    world = WORLD_DATA[current_world]

    gradient = pygame.Surface((WIDTH, HEIGHT))

    for y in range(HEIGHT):
        ratio = y / HEIGHT

        r = world['bg_top'][0] + int((world['bg_bottom'][0] - world['bg_top'][0]) * ratio)
        g = world['bg_top'][1] + int((world['bg_bottom'][1] - world['bg_top'][1]) * ratio)
        b = world['bg_top'][2] + int((world['bg_bottom'][2] - world['bg_top'][2]) * ratio)

        pygame.draw.line(gradient, (r, g, b), (0, y), (WIDTH, y))

    surface.blit(gradient, (0, 0))

    # stars
    for i in range(60):
        sx = (i * 137 + int(pygame.time.get_ticks() * 0.01)) % WIDTH
        sy = (i * 73) % HEIGHT
        size = 1 + (i % 3)

        pygame.draw.circle(surface, (255, 255, 255), (sx, sy), size)

    # moon
    pygame.draw.circle(surface, (240, 240, 255), (680, 90), 55)
    pygame.draw.circle(surface, (200, 220, 255), (680, 90), 70, 4)

    # skyscrapers only in world 1
    if current_world == 1:
        building_x = 0
        building_width = 420
        building_height = max(HEIGHT + 2500, -win_threshold + HEIGHT + 500, 25000)
        building_y_offset = camera_y * 0.25

        pygame.draw.rect(
            surface,
            (43, 47, 56),
            (building_x, -building_y_offset, building_width, building_height)
        )

        for row in range(int((building_height + 100) / 28)):
            for col in range(10):
                wx = building_x + 32 + col * 28
                wy = -building_y_offset + 48 + row * 28

                pygame.draw.rect(
                    surface,
                    (180, 190, 205, 70),
                    (wx, wy, 20, 20)
                )


def draw_lava(surface):
    screen_y = lava['y'] - camera_y
    if screen_y > HEIGHT:
        return
    pygame.draw.rect(surface, COLOR_LAVA_BOTTOM, (0, screen_y, WIDTH, HEIGHT - screen_y))
    pygame.draw.rect(surface, COLOR_LAVA_TOP, (0, screen_y, WIDTH, 8))


def draw_platforms(surface):
    for platform in platforms:
        screen_y = platform['y'] - camera_y
        if screen_y > HEIGHT or screen_y < -100:
            continue
        color = COLOR_PLATFORM_MOVE if platform['type'] in ('moveX', 'moveY') else COLOR_PLATFORM
        pygame.draw.rect(surface, color, (platform['x'], screen_y, platform['width'], platform['height']))
        pygame.draw.rect(surface, COLOR_TEXT, (platform['x'], screen_y, platform['width'], platform['height']), 2)


def draw_coins(surface):
    for coin in coins:
        if coin['collected']:
            continue
        screen_y = coin['y'] - camera_y
        if screen_y > HEIGHT or screen_y < -50:
            continue
        pygame.draw.circle(surface, COLOR_COIN, (int(coin['x'] + coin['width'] / 2), int(screen_y + coin['height'] / 2)), int(coin['width'] / 2))
        pygame.draw.circle(surface, (253, 230, 138), (int(coin['x'] + coin['width'] / 2), int(screen_y + coin['height'] / 2)), int(coin['width'] / 2), 2)


def draw_player(surface):
    screen_y = player['y'] - camera_y
    x = player['x']
    if player['facing'] == -1:
        x = player['x'] + player['width']
    draw_player_character(surface, x, screen_y, player['animationFrame'], player['facing'])


def draw_player_character(surface, x, y, frame, facing):
    if facing == -1:
        transform_surface = pygame.Surface((player['width'], player['height']), pygame.SRCALPHA)
        draw_player_character_surface(transform_surface, 0, 0, frame)
        transform_surface = pygame.transform.flip(transform_surface, True, False)
        surface.blit(transform_surface, (player['x'], y))
    else:
        draw_player_character_surface(surface, x, y, frame)


def draw_player_character_surface(surface, x, y, frame):
    colors = {
        'hair': (110, 75, 50),
        'skin': (250, 220, 180),
        'shirt': (40, 135, 215),
        'shirt_dark': (18, 85, 155),
        'pants': (25, 35, 95),
        'shoe': (20, 24, 38),
        'outline': (8, 10, 18),
        'accent': (235, 230, 190),
    }
    walk_frames = [
        {'armOffset': 0, 'legOffset': 0},
        {'armOffset': 2, 'legOffset': 2},
        {'armOffset': -2, 'legOffset': -2},
    ]
    frame_data = walk_frames[frame % PLAYER_FRAME_COUNT]

    pygame.draw.circle(surface, colors['hair'], (x + 16, y + 8), 8)
    pygame.draw.rect(surface, colors['hair'], (x + 8, y + 8, 16, 6), border_radius=6)
    pygame.draw.circle(surface, colors['skin'], (x + 16, y + 14), 6)
    pygame.draw.circle(surface, colors['outline'], (x + 13, y + 13), 1)
    pygame.draw.circle(surface, colors['outline'], (x + 19, y + 13), 1)
    pygame.draw.rect(surface, colors['outline'], (x + 14, y + 16, 4, 1))

    pygame.draw.rect(surface, colors['shirt'], (x + 8, y + 20, 16, 18), border_radius=5)
    pygame.draw.rect(surface, colors['shirt_dark'], (x + 8, y + 20, 16, 8), border_radius=5)
    pygame.draw.rect(surface, colors['accent'], (x + 14, y + 28, 4, 12), border_radius=2)
    pygame.draw.rect(surface, colors['outline'], (x + 8, y + 34, 16, 4), border_radius=3)

    pygame.draw.rect(surface, colors['shirt'], (x + 4 + frame_data['armOffset'], y + 22, 6, 14), border_radius=4)
    pygame.draw.circle(surface, colors['skin'], (x + 7 + frame_data['armOffset'], y + 33), 4)
    pygame.draw.rect(surface, colors['shirt'], (x + 22 - frame_data['armOffset'], y + 22, 6, 14), border_radius=4)
    pygame.draw.circle(surface, colors['skin'], (x + 25 - frame_data['armOffset'], y + 33), 4)

    pygame.draw.rect(surface, colors['pants'], (x + 9 + frame_data['legOffset'], y + 38, 5, 12), border_radius=3)
    pygame.draw.rect(surface, colors['pants'], (x + 18 - frame_data['legOffset'], y + 38, 5, 12), border_radius=3)
    pygame.draw.rect(surface, colors['shoe'], (x + 8 + frame_data['legOffset'], y + 50, 7, 4), border_radius=2)
    pygame.draw.rect(surface, colors['shoe'], (x + 17 - frame_data['legOffset'], y + 50, 7, 4), border_radius=2)


def draw_enemy(surface, enemy):
    screen_y = enemy['y'] - camera_y
    if enemy['facing'] == -1:
        x = enemy['x'] + enemy['width']
        transform_surface = pygame.Surface((enemy['width'], enemy['height']), pygame.SRCALPHA)
        draw_enemy_character_surface(transform_surface, 0, 0, enemy['animationFrame'])
        transform_surface = pygame.transform.flip(transform_surface, True, False)
        surface.blit(transform_surface, (enemy['x'], screen_y))
    else:
        draw_enemy_character_surface(surface, enemy['x'], screen_y, enemy['animationFrame'])


def draw_enemy_character_surface(surface, x, y, frame):
    enemy_colors = {
        'body': (20, 45, 90),
        'hat': (20, 20, 25),
        'face': (240, 217, 182),
        'badge': (240, 200, 60),
        'belt': (70, 70, 80),
        'pants': (15, 30, 70),
        'shoe': (15, 15, 22),
        'weapon': (220, 210, 120),
        'outline': (10, 10, 18),
    }
    frame_data = [
        {'armOffset': 0, 'legOffset': 0, 'weaponX': 20, 'weaponY': 22},
        {'armOffset': -2, 'legOffset': 2, 'weaponX': 20, 'weaponY': 20},
        {'armOffset': 0, 'legOffset': 0, 'weaponX': 20, 'weaponY': 22},
        {'armOffset': 2, 'legOffset': -2, 'weaponX': 20, 'weaponY': 24},
    ][frame % ENEMY_WALK_FRAME_COUNT]

    pygame.draw.circle(surface, enemy_colors['face'], (int(x + 14), int(y + 14)), 6)
    pygame.draw.circle(surface, enemy_colors['outline'], (int(x + 12), int(y + 14)), 1)
    pygame.draw.circle(surface, enemy_colors['outline'], (int(x + 16), int(y + 14)), 1)
    pygame.draw.rect(surface, enemy_colors['hat'], (x + 5, y + 5, 22, 6), border_radius=3)
    pygame.draw.rect(surface, enemy_colors['hat'], (x + 9, y + 2, 12, 6), border_radius=3)
    pygame.draw.rect(surface, enemy_colors['body'], (x + 4, y + 15, 24, 18), border_radius=5)
    pygame.draw.rect(surface, enemy_colors['belt'], (x + 3, y + 20, 26, 5), border_radius=3)
    pygame.draw.rect(surface, enemy_colors['body'], (x + 6, y + 23, 20, 6), border_radius=3)
    pygame.draw.rect(surface, enemy_colors['badge'], (x + 8, y + 18, 4, 6), border_radius=2)
    pygame.draw.rect(surface, (255, 255, 255), (x + 14, y + 18, 6, 3), border_radius=2)

    pygame.draw.rect(surface, enemy_colors['body'], (x + 2 + frame_data['armOffset'], y + 18, 6, 14), border_radius=3)
    pygame.draw.rect(surface, enemy_colors['body'], (x + 24 - frame_data['armOffset'], y + 18, 6, 14), border_radius=3)
    pygame.draw.rect(surface, enemy_colors['pants'], (x + 7 + frame_data['legOffset'], y + 30, 6, 12), border_radius=3)
    pygame.draw.rect(surface, enemy_colors['pants'], (x + 18 - frame_data['legOffset'], y + 30, 6, 12), border_radius=3)
    pygame.draw.rect(surface, enemy_colors['shoe'], (x + 6 + frame_data['legOffset'], y + 42, 6, 4), border_radius=2)
    pygame.draw.rect(surface, enemy_colors['shoe'], (x + 18 - frame_data['legOffset'], y + 42, 6, 4), border_radius=2)
    pygame.draw.rect(surface, enemy_colors['weapon'], (x + frame_data['weaponX'], y + frame_data['weaponY'], 4, 8), border_radius=2)


def draw_door(surface):
    door_y = win_threshold
    screen_y = door_y - camera_y
    if screen_y > HEIGHT or screen_y < -100:
        return
    pygame.draw.rect(surface, (120, 53, 15), (WIDTH / 2 - 50, screen_y - 80, 100, 160))
    pygame.draw.rect(surface, (180, 83, 9), (WIDTH / 2 - 48, screen_y - 75, 46, 150))
    pygame.draw.rect(surface, (180, 83, 9), (WIDTH / 2 + 2, screen_y - 75, 46, 150))
    pygame.draw.circle(surface, COLOR_COIN, (WIDTH // 2 - 24, int(screen_y - 5)), 4)
    pygame.draw.circle(surface, COLOR_COIN, (WIDTH // 2 + 24, int(screen_y - 5)), 4)
    distance = abs(player['y'] - door_y)
    if distance < 200:
        alpha = int((0.5 - distance / 400) * 255)
        glow = pygame.Surface((100, 160), pygame.SRCALPHA)
        pygame.draw.rect(glow, (251, 191, 36, max(0, alpha)), (0, 0, 100, 160), 3)
        surface.blit(glow, (WIDTH / 2 - 50, screen_y - 80))


def draw_hud(surface, font):
    panel_w = 230
    panel_h = 110
    hud_panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
    pygame.draw.rect(hud_panel, (8, 16, 34, 220), (0, 0, panel_w, panel_h), border_radius=18)
    pygame.draw.rect(hud_panel, (96, 181, 255, 120), (0, 0, panel_w, panel_h), 2, border_radius=18)
    surface.blit(hud_panel, (16, 16))

    title_text = font.render('RUN STATS', True, (227, 242, 255))
    surface.blit(title_text, (30, 24))

    coin_label = font.render('Coins', True, (249, 213, 80))
    wins_label = font.render('Wins', True, (164, 219, 255))
    coin_value = font.render(str(coin_count), True, (255, 255, 255))
    wins_value = font.render(str(wins), True, (255, 255, 255))

    surface.blit(coin_label, (30, 58))
    surface.blit(coin_value, (140, 58))
    surface.blit(wins_label, (30, 86))
    surface.blit(wins_value, (140, 86))

    elapsed = 0
    if game_started:
        elapsed = int((pygame.time.get_ticks() - game_start_time) / 1000)
    timer_text = font.render(f'Time: {elapsed}s', True, COLOR_TEXT)
    surface.blit(timer_text, (16, panel_h + 30))
    hint_text = font.render('Climb higher and collect coins for a better run.', True, COLOR_TEXT)
    surface.blit(hint_text, (16, HEIGHT - 32))


def update_menu_animation():
    global menu_anim_y
    # Smooth animation from top to center
    if abs(menu_anim_y - menu_anim_target) > 1:
        diff = menu_anim_target - menu_anim_y
        menu_anim_y += diff * 0.15  # easing function
    else:
        menu_anim_y = menu_anim_target


def draw_menu(surface, font, small_font):
    # Dark gradient background
    for y in range(HEIGHT):
        ratio = y / HEIGHT
        r = 12 + int((20 - 12) * ratio)
        g = 16 + int((24 - 16) * ratio)
        b = 24 + int((36 - 24) * ratio)
        pygame.draw.line(surface, (r, g, b), (0, y), (WIDTH, y))
    
    # Animated panel sliding from top
    panel_y = int(menu_anim_y)
    panel_h = HEIGHT - 160
    panel_rect = pygame.Rect(60, panel_y + 80, WIDTH - 120, panel_h)
    
    # Draw glossy panel with gradient border
    pygame.draw.rect(surface, (20, 28, 50), panel_rect, border_radius=24)
    pygame.draw.rect(surface, (88, 166, 255), panel_rect, 3, border_radius=24)
    
    # Title with shadow effect
    title_text = 'Skyward Climb'
    title_shadow = font.render(title_text, True, (0, 0, 0))
    title_surf = font.render(title_text, True, (136, 204, 255))
    surface.blit(title_shadow, (panel_rect.x + 26, panel_rect.y + 26))
    surface.blit(title_surf, (panel_rect.x + 24, panel_rect.y + 24))
    
    # Stats boxes (best height, coins, wins)
    stats_y = panel_rect.y + 90
    stat_height = 64
    stat_width = (panel_rect.width - 44) // 3

    height_box = pygame.Rect(panel_rect.x + 16, stats_y, stat_width, stat_height)
    coins_box = pygame.Rect(panel_rect.x + 16 + stat_width + 14, stats_y, stat_width, stat_height)
    wins_box = pygame.Rect(panel_rect.x + 16 + 2 * (stat_width + 14), stats_y, stat_width, stat_height)

    for box in (height_box, coins_box, wins_box):
        pygame.draw.rect(surface, (28, 40, 72), box, border_radius=16)
        pygame.draw.rect(surface, (68, 156, 255), box, 2, border_radius=16)

    height_label = small_font.render('Best Height', True, (136, 180, 255))
    height_val = font.render(f'{best_height}m', True, (136, 204, 255))
    surface.blit(height_label, (height_box.x + 12, height_box.y + 10))
    surface.blit(height_val, (height_box.x + 12, height_box.y + 32))

    coins_label = small_font.render('Saved Coins', True, (136, 180, 255))
    coins_val = font.render(f'{total_coins}', True, (251, 191, 36))
    surface.blit(coins_label, (coins_box.x + 12, coins_box.y + 10))
    surface.blit(coins_val, (coins_box.x + 12, coins_box.y + 32))

    wins_label = small_font.render('Wins', True, (136, 180, 255))
    wins_val = font.render(f'{wins}', True, (180, 235, 120))
    surface.blit(wins_label, (wins_box.x + 12, wins_box.y + 10))
    surface.blit(wins_val, (wins_box.x + 12, wins_box.y + 32))
    
    # Main message
    msg_y = stats_y + stat_height + 24
    if state == 'shop':
        # Shop view
        shop_title = small_font.render('⭐ Upgrade Shop ⭐', True, (251, 191, 36))
        surface.blit(shop_title, (panel_rect.x + panel_rect.width // 2 - shop_title.get_width() // 2, msg_y))
        
        upgrade_rows = [
            ('🚀 Jump Boost', upgrades['jumpTier'], get_next_cost('jump')),
            ('⚡ Speed Boost', upgrades['speedTier'], get_next_cost('speed')),
            ('💰 Gold Multiplier', upgrades['goldTier'], get_next_cost('gold')),
        ]
        for i, (name, tier, cost) in enumerate(upgrade_rows):
            cost_label = 'MAX' if cost is None else str(cost)
            row_text = f'{name}: Tier {tier} — Cost {cost_label}'
            rendered = small_font.render(row_text, True, COLOR_TEXT)
            surface.blit(rendered, (panel_rect.x + 24, msg_y + 40 + i * 32))
        
        # Controls
        hint = small_font.render('Press 1/2/3 to buy upgrades, B to go back', True, (136, 180, 255))
        surface.blit(hint, (panel_rect.x + 24, msg_y + 130))
    else:
        # Main menu view
        msg_surf = small_font.render(menu_message, True, COLOR_TEXT)
        surface.blit(msg_surf, (panel_rect.x + 24, msg_y))

        world_title = small_font.render(
            f'Current World: {current_world} ({WORLD_DATA[current_world]["mult"]}x coins)',
            True,
            (255, 220, 120)
        )

        surface.blit(world_title, (panel_rect.x + 24, msg_y + 40))

        for w in range(2, 6):
            unlocked = w in unlocked_worlds

            status = 'Unlocked' if unlocked else f'Cost: {WORLD_DATA[w]["cost"]} wins'

            world_text = small_font.render(
                f'Press {w} - World {w} ({WORLD_DATA[w]["mult"]}x) [{status}]',
                True,
                (180, 220, 255)
            )

            surface.blit(world_text, (panel_rect.x + 24, msg_y + 70 + (w - 2) * 26))

        # Controls
        controls_y = msg_y + 70 + 4 * 26 + 16
        controls = [
            'Press Enter to Start',
            'Press S for Shop',
            'Arrow keys / A-D to move, Space to jump',
        ]
        for i, ctrl in enumerate(controls):
            ctrl_surf = small_font.render(ctrl, True, (136, 180, 255))
            surface.blit(ctrl_surf, (panel_rect.x + 24, controls_y + i * 28))



def main():
    global state
    pygame.init()
    # initialize mixer separately to avoid blocking if audio unavailable
    try:
        pygame.mixer.init()
    except Exception:
        pass
    pygame.display.set_caption('Skybound Scramble')
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()
    font = pygame.font.SysFont('Inter', 30)
    small_font = pygame.font.SysFont('Inter', 20)

    load_save()
    # Start with main menu music
    try:
        play_music(MAINMENU_MUSIC)
    except Exception:
        pass
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_LEFT, pygame.K_a):
                    input_state['left'] = True
                if event.key in (pygame.K_RIGHT, pygame.K_d):
                    input_state['right'] = True
                if event.key in (pygame.K_UP, pygame.K_w, pygame.K_SPACE):
                    input_state['jump'] = True
                if state == 'menu':
                    if event.key == pygame.K_RETURN:
                        start_game()
                    elif event.key == pygame.K_s:
                        state = 'shop'
                        try:
                            play_music(SHOP_MUSIC)
                        except Exception:
                            pass
                    elif event.key == pygame.K_2:
                        if 2 not in unlocked_worlds:
                            purchase_world(2)
                        select_world(2)
                    elif event.key == pygame.K_3:
                        if 3 not in unlocked_worlds:
                            purchase_world(3)
                        select_world(3)
                    elif event.key == pygame.K_4:
                        if 4 not in unlocked_worlds:
                            purchase_world(4)
                        select_world(4)
                    elif event.key == pygame.K_5:
                        if 5 not in unlocked_worlds:
                            purchase_world(5)
                        select_world(5)
                    elif event.key == pygame.K_ESCAPE:
                        running = False
                elif state == 'shop':
                    if event.key == pygame.K_b:
                        state = 'menu'
                        try:
                            play_music(MAINMENU_MUSIC)
                        except Exception:
                            pass
                    elif event.key == pygame.K_1:
                        purchase_upgrade('jump')
                    elif event.key == pygame.K_2:
                        purchase_upgrade('speed')
                    elif event.key == pygame.K_3:
                        purchase_upgrade('gold')
            elif event.type == pygame.KEYUP:
                if event.key in (pygame.K_LEFT, pygame.K_a):
                    input_state['left'] = False
                if event.key in (pygame.K_RIGHT, pygame.K_d):
                    input_state['right'] = False
                if event.key in (pygame.K_UP, pygame.K_w, pygame.K_SPACE):
                    input_state['jump'] = False

        # Calculate delta time for frame-rate independent updates
        global dt
        dt = clock.get_time() / 1000.0  # convert to seconds
        dt = max(0.016, min(0.05, dt))  # clamp between 16ms and 50ms
        
        if game_started:
            update_player()

        # Update menu animation
        update_menu_animation()

        draw_background(screen)
        draw_lava(screen)
        draw_platforms(screen)
        draw_coins(screen)
        draw_hazards(screen)
        draw_powerups(screen)
        draw_particles(screen)
        for enemy in enemies:
            draw_enemy(screen, enemy)
        draw_player(screen)
        draw_door(screen)
        draw_hud(screen, small_font)

        if state in ('menu', 'shop'):
            draw_menu(screen, font, small_font)

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()


if __name__ == '__main__':
    main()
