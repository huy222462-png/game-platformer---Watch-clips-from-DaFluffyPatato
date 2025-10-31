import math
import os
import random
import sys
import pygame


from scripts.particle import Particle
from scripts.spark import Spark
from scripts.utils import load_image, load_images, Animation
from scripts.entities import Player, Enemy
from scripts.ui import HealthBar
from scripts.tilemap import Tilemap
from scripts.clouds import Clouds
from auth import login, register

class Game:
    def __init__(self):
        pygame.init()

        # UI font that supports Vietnamese glyphs; fallback to default if not available
        try:
            self.ui_font = pygame.font.SysFont('Segoe UI', 20)
        except Exception:
            self.ui_font = pygame.font.Font(None, 20)

        # change window name
        pygame.display.set_caption('Platformer')

        # Init window
        self.window = pygame.display.set_mode((640, 480))
        self.display = pygame.Surface((320, 240), pygame.SRCALPHA) # set viewport to half the resolution (pixel art)
        self.display_2 = pygame.Surface((320, 240))

        screen = pygame.display.set_mode((800, 600))
        pygame.display.set_caption("Đăng nhập")


        # Init time (clock)
        self.clock = pygame.time.Clock()

        """
        LOAD ASSETS
        """
        self.assets = {
            'decor': load_images('tiles/decor'),
            'grass': load_images('tiles/grass'),
            'large_decor': load_images('tiles/large_decor'),
            'stone': load_images('tiles/stone'),
            'player': load_image('entities/player.png'),
            'background': load_image('background.png'),
            'clouds': load_images('clouds'),
            'enemy/idle': Animation(load_images('entities/enemy/idle'), img_dur=6),
            'enemy/run': Animation(load_images('entities/enemy/run'), img_dur=4),
            'player/idle': Animation(load_images('entities/player/idle'), img_dur=6),
            'player/run': Animation(load_images('entities/player/run'), img_dur=4),
            'player/jump': Animation(load_images('entities/player/jump')),
            'player/slide': Animation(load_images('entities/player/slide')),
            'player/wall_slide': Animation(load_images('entities/player/wall_slide')),
            'particle/leaf': Animation(load_images('particles/leaf'), img_dur= 20,loop=False),
            'particle/particle': Animation(load_images('particles/particle'), img_dur=6, loop=False),
            'gun': load_image('gun.png'),
            'projectile': load_image('projectile.png'),
            'logo': None,
            # optional item icons (user placed images in data/images/entities/player/items)
            'item/kunai': None,
            'item/shuriken': None,
        }

        # if user provided a background image for login/map, prefer it
        try:
            custom_bg = load_image('backgroundDNDK.jpg')
            if custom_bg:
                self.assets['background'] = custom_bg
        except Exception:
            pass

        # try load logo image (use logogame.png in data/images root)
        try:
            logo_img = load_image('logogame.png')
            if logo_img:
                self.assets['logo'] = logo_img
        except Exception:
            self.assets['logo'] = None

        # try to load item icons if files exist
        try:
            self.assets['item/kunai'] = load_image('entities/player/items/kunai.png')
        except Exception:
            self.assets['item/kunai'] = None
        try:
            self.assets['item/shuriken'] = load_image('entities/player/items/shuriken.png')
        except Exception:
            self.assets['item/shuriken'] = None

        """
        SOUNDS
        """
        self.sfx = {
            'jump': pygame.mixer.Sound('data/sfx/jump.wav'),
            'dash': pygame.mixer.Sound('data/sfx/dash.wav'),
            'hit': pygame.mixer.Sound('data/sfx/hit.wav'),
            'shoot': pygame.mixer.Sound('data/sfx/shoot.wav'),
            'ambience': pygame.mixer.Sound('data/sfx/ambience.wav'),
        }

        self.sfx['ambience'].set_volume(0.2)
        self.sfx['shoot'].set_volume(0.4)
        self.sfx['hit'].set_volume(0.7)
        self.sfx['dash'].set_volume(0.3)
        self.sfx['jump'].set_volume(0.3)

        """
        PROBABLY WILL HAVE TO MAKE THIS (ANIMATION ASSETS LOAD) IN A SEPARATE FILE THEN CALL THE FILE.
        OR LOAD IT IN THE PLAYER SCRIPT (BETTER SOLUTION IMO)
        """

        self.clouds = Clouds(self.assets['clouds'], count=16)
        self.player = Player(self, (70,50), (8, 15))
        # HUD: health bar fixed to top-left of the screen
        self.hud = HealthBar(max_hits=self.player.max_hits, pos=(4,4), size=(60,12))
        self.movement = [False, False]

        # pickups on the map (list of dict: {'type': 'shuriken'|'kunai', 'pos': [x,y]})
        self.pickups = []

        self.tilemap = Tilemap(self, tile_size=16)
        self.level = 0
        self.load_level(self.level)

        self.screenshake = 0
        # pause flag (toggle with ESC during gameplay)
        self.paused = False


    def load_level(self, map_id):
        self.tilemap.load('data/maps/' + str(map_id) + '.json')

        self.leaf_spawners = []
        for tree in self.tilemap.extract([('large_decor', 2)], keep=True):
            self.leaf_spawners.append(pygame.Rect(4 + tree['pos'][0], 4 + tree['pos'][1], 23, 13))

        self.enemies = []
        for spawner in self.tilemap.extract([('spawners', 0), ('spawners', 1)]):
            if spawner['variant'] == 0:
                self.player.pos = spawner['pos']
                self.player.air_time = 0
                # reset player hits on (re)spawn
                try:
                    self.player.hits = 0
                except Exception:
                    pass
            else:
                self.enemies.append(Enemy(self, spawner['pos'], (8, 15)))

        # extract item pickups from map. Variant mapping:
        # 0 -> shuriken pickup, 1 -> kunai pickup
        self.pickups = []
        for it in self.tilemap.extract([('items', 0), ('items', 1)], keep=False):
            if it['variant'] == 0:
                self.pickups.append({'type': 'shuriken', 'pos': it['pos']})
            elif it['variant'] == 1:
                self.pickups.append({'type': 'kunai', 'pos': it['pos']})

        # spawn a few random pickups on the map (where not solid)
        try:
            xs = []
            ys = []
            for loc, tile in self.tilemap.tilemap.items():
                pos = tile.get('pos')
                if pos:
                    xs.append(int(pos[0] * self.tilemap.tile_size))
                    ys.append(int(pos[1] * self.tilemap.tile_size))
            for off in self.tilemap.offgrid:
                if 'pos' in off:
                    xs.append(int(off['pos'][0]))
                    ys.append(int(off['pos'][1]))
            if xs and ys:
                minx, maxx = min(xs), max(xs)
                miny, maxy = min(ys), max(ys)
            else:
                minx, maxx = 0, self.display.get_width()
                miny, maxy = 0, self.display.get_height()

            # spawn 2-5 pickups randomly
            for _ in range(random.randint(2, 5)):
                attempts = 0
                while attempts < 50:
                    rx = random.randint(minx, maxx)
                    ry = random.randint(miny, maxy)
                    # avoid solid tiles
                    if not self.tilemap.solid_check((rx, ry)):
                        self.pickups.append({'type': random.choice(['shuriken', 'kunai']), 'pos': [rx, ry]})
                        break
                    attempts += 1
        except Exception:
            pass

        self.projectiles = []
        self.particles = []
        self.sparks = []

        self.scroll = [0, 0]
        self.dead = 0
        self.transition = -30
    
    def text_input(self, screen, prompt, pos=None, password=False):
        """Improved text input that supports Unicode (Vietnamese), password masking and a caret.

        Args:
            screen: the pygame display Surface
            prompt: prompt string to show
            pos: top-left position for the prompt/input box. If None, input is centered.
            password: if True, mask the input when rendering
        Returns:
            The entered text (unicode)
        """
        font = getattr(self, 'ui_font', None) or pygame.font.Font(None, 28)
        clock = pygame.time.Clock()
        text = ''
        active = True
        caret_timer = 0
        caret_visible = True
        # determine box position/size
        sw, sh = screen.get_size()
        box_w = 420
        box_h = 48
        if pos is None:
            box_x = sw // 2 - box_w // 2
            box_y = sh // 2 - box_h // 2
        else:
            box_x, box_y = pos

        while active:
            caret_timer += clock.tick(60)
            if caret_timer >= 500:
                caret_visible = not caret_visible
                caret_timer = 0

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        active = False
                        break
                    elif event.key == pygame.K_BACKSPACE:
                        text = text[:-1]
                    elif event.key == pygame.K_ESCAPE:
                        # cancel input
                        text = ''
                        active = False
                        break
                    else:
                        # use event.unicode to support accents
                        ch = event.unicode
                        if ch:
                            text += ch

            # draw input overlay
            overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            screen.blit(overlay, (0, 0))

            # box
            pygame.draw.rect(screen, (40, 40, 40), (box_x - 8, box_y - 8, box_w + 16, box_h + 16), border_radius=6)
            pygame.draw.rect(screen, (20, 20, 20), (box_x - 6, box_y - 6, box_w + 12, box_h + 12), border_radius=6)

            # prompt
            prompt_surf = font.render(prompt, True, (255, 255, 255))
            screen.blit(prompt_surf, (box_x + 8, box_y - prompt_surf.get_height() - 6))

            # input text (mask if password)
            display_text = ('*' * len(text)) if password else text
            # add caret
            if caret_visible:
                display_text += '_'

            txt_surf = font.render(display_text, True, (230, 230, 230))
            # clip if too long
            if txt_surf.get_width() > box_w - 16:
                # show tail
                # find slice that fits
                visible = text
                while font.size(visible + '_')[0] > box_w - 24 and len(visible) > 0:
                    visible = visible[1:]
                if password:
                    display_text = '*' * len(visible) + ('_' if caret_visible else '')
                else:
                    display_text = visible + ('_' if caret_visible else '')
                txt_surf = font.render(display_text, True, (230, 230, 230))

            screen.blit(txt_surf, (box_x + 8, box_y + (box_h - txt_surf.get_height()) // 2))

            pygame.display.flip()

        return text

    def login_screen(self, screen):
        # use UI font for consistent rendering (supports Vietnamese)
        font = getattr(self, 'ui_font', pygame.font.Font(None, 48))
        small_font = getattr(self, 'ui_font', pygame.font.Font(None, 36))
        message = ""  # dòng thông báo
        
        while True:
            screen.fill((20, 20, 20))
            
            # tiêu đề menu
            title_text = "1. Đăng nhập   2. Đăng ký"
            title = font.render(title_text, True, (255, 255, 255))
            # center title
            tw, th = title.get_size()
            sw, sh = screen.get_size()
            screen.blit(title, (sw//2 - tw//2, sh//2 - 120))

            # hiển thị thông báo (nếu có)
            if message:
                msg_surface = small_font.render(message, True, (255, 200, 0))
                # center message under title
                mw = msg_surface.get_width()
                screen.blit(msg_surface, (sw//2 - mw//2, sh//2 - 80))

            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    exit()

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_1:  # Đăng nhập
                        # centered input boxes
                        w, h = screen.get_size()
                        username = self.text_input(screen, "Tên đăng nhập:", (w//2 - 200, h//2 - 20))
                        password = self.text_input(screen, "Mật khẩu:", (w//2 - 200, h//2 + 40), password=True)
                        success, msg = login(username, password)
                        message = msg
                        if success:
                            return username

                    elif event.key == pygame.K_2:  # Đăng ký
                        w, h = screen.get_size()
                        username = self.text_input(screen, "Tạo tài khoản:", (w//2 - 200, h//2 - 20))
                        password = self.text_input(screen, "Tạo mật khẩu:", (w//2 - 200, h//2 + 40), password=True)
                        success, msg = register(username, password)
                        message = msg

    def run(self):
        # MUSIC
        pygame.mixer.music.load('data/music.wav')
        pygame.mixer.music.set_volume(0.5)

        # -1 so the music loops undefinitly
        pygame.mixer.music.play(-1)
        self.sfx['ambience'].play(-1)


        # Main loop
        while True:
            # clear logical display (pixel-art surface)
            self.display.fill((0, 0, 0, 0))  # RGBA Color

            # draw background if available, otherwise fill with a fallback color
            bg = self.assets.get('background')
            if bg:
                try:
                    self.display_2.blit(bg, (0, 0))
                except Exception:
                    self.display_2.fill((12, 18, 36))
            else:
                self.display_2.fill((12, 18, 36))

            # --- event processing (do this early so ESC toggles pause immediately) ---
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()  # pygame only closes pygame
                    sys.exit()  # exit the app

                if event.type == pygame.KEYDOWN:
                    # toggle pause
                    if event.key == pygame.K_ESCAPE:
                        self.paused = not self.paused
                        # small audio hint when pausing/unpausing
                        try:
                            if self.paused:
                                self.sfx.get('ambience', pygame.mixer.Sound('data/sfx/ambience.wav')).set_volume(0.1)
                            else:
                                self.sfx.get('ambience', pygame.mixer.Sound('data/sfx/ambience.wav')).set_volume(0.2)
                        except Exception:
                            pass

                    if event.key == pygame.K_LEFT:
                        self.movement[0] = True
                    if event.key == pygame.K_RIGHT:
                        self.movement[1] = True
                    if event.key == pygame.K_UP:
                        if self.player.jump():
                            try:
                                self.sfx['jump'].play()
                            except Exception:
                                pass
                    if event.key == pygame.K_x:
                        self.player.dash()
                    # item usage keys
                    if event.key == pygame.K_z:
                        # throw shuriken
                        try:
                            used = self.player.use_shuriken()
                        except Exception:
                            used = False
                        if not used:
                            pass
                    if event.key == pygame.K_c:
                        try:
                            used = self.player.use_kunai()
                        except Exception:
                            used = False
                        if not used:
                            pass
                    # debug keys to give items (for testing/pickups)
                    if event.key == pygame.K_9:
                        self.player.give_item('shuriken', 10)
                    if event.key == pygame.K_0:
                        self.player.give_item('kunai', 10)
                    # debug: spawn pickup at player position
                    if event.key == pygame.K_p:
                        pos = (self.player.rect().centerx, self.player.rect().centery)
                        self.pickups.append({'type': 'shuriken', 'pos': [pos[0], pos[1]]})
                    if event.key == pygame.K_o:
                        pos = (self.player.rect().centerx, self.player.rect().centery)
                        self.pickups.append({'type': 'kunai', 'pos': [pos[0], pos[1]]})

                if event.type == pygame.KEYUP:
                    if event.key == pygame.K_LEFT:
                        self.movement[0] = False
                    if event.key == pygame.K_RIGHT:
                        self.movement[1] = False

            # If paused, skip gameplay updates but still render the current frame and overlay
            if not self.paused:
                self.screenshake = max(0, self.screenshake - 1)

                if not len(self.enemies):  # killed all the enemies
                    self.transition += 1
                    if self.transition > 30:
                        self.level = min(self.level + 1, len(os.listdir('data/maps')) - 1)
                        self.load_level(self.level)
                if self.transition < 0:
                    self.transition += 1

                if self.dead:
                    self.dead += 1
                    if self.dead >= 10:
                        self.transition = min(30, self.transition + 1)
                    if self.dead > 40:
                        self.load_level(self.level)

                self.scroll[0] += (self.player.rect().centerx - self.display.get_width() / 2 - self.scroll[0]) / 30
                self.scroll[1] += (self.player.rect().centery - self.display.get_height() / 2 - self.scroll[1]) / 30
                render_scroll = (int(self.scroll[0]), int(self.scroll[1]))

                for rect in self.leaf_spawners:
                    if random.random() * 49999 < rect.width * rect.height:
                        pos = (rect.x + random.random() * rect.width, rect.y + random.random() * rect.height)
                        self.particles.append(Particle(self, 'leaf', pos, velocity=[-0.1, 0.3], frame=random.randint(0, 20)))

                self.clouds.update()
                self.clouds.render(self.display, offset=render_scroll)

                self.tilemap.render(self.display, offset=render_scroll)

                for enemy in self.enemies.copy():
                    kill = enemy.update(self.tilemap, (0, 0))
                    enemy.render(self.display, offset=render_scroll)
                    if kill:
                        try:
                            self.enemies.remove(enemy)
                        except Exception:
                            pass

                if not self.dead:
                    self.player.update(self.tilemap, (self.movement[1] - self.movement[0], 0))
                    self.player.render(self.display, offset=render_scroll)

                    # render pickups in the world and check for pickup collision
                    for pu in self.pickups.copy():
                        px, py = pu['pos']
                        # draw icon smaller than player
                        icon_size = 12
                        img = None
                        if pu['type'] == 'kunai':
                            img = self.assets.get('item/kunai')
                        elif pu['type'] == 'shuriken':
                            img = self.assets.get('item/shuriken')

                        draw_x = int(px - icon_size // 2 - render_scroll[0])
                        draw_y = int(py - icon_size // 2 - render_scroll[1])
                        if img:
                            try:
                                surf_img = pygame.transform.scale(img, (icon_size, icon_size))
                                self.display.blit(surf_img, (draw_x, draw_y))
                            except Exception:
                                pygame.draw.rect(self.display, (255, 255, 0), (draw_x, draw_y, icon_size, icon_size))
                        else:
                            pygame.draw.rect(self.display, (255, 255, 0), (draw_x, draw_y, icon_size, icon_size))

                        # collision check in world coords
                        pickup_rect = pygame.Rect(px - icon_size // 2, py - icon_size // 2, icon_size, icon_size)
                        if pickup_rect.colliderect(self.player.rect()):
                            # give the item to player
                            if pu['type'] == 'shuriken':
                                self.player.give_item('shuriken', 1)
                            elif pu['type'] == 'kunai':
                                self.player.give_item('kunai', 1)
                            try:
                                self.sfx['shoot'].play()
                            except Exception:
                                pass
                            try:
                                self.pickups.remove(pu)
                            except Exception:
                                pass

                # [[x,y], direction, timer]
                for projectile in self.projectiles.copy():
                    projectile[0][0] += projectile[1]
                    projectile[2] += 1
                    img = self.assets['projectile']
                    try:
                        self.display.blit(img, (projectile[0][0] - img.get_width() / 2 - render_scroll[0], projectile[0][1] - img.get_height() / 2 - render_scroll[1]))
                    except Exception:
                        pass
                    # check collision with enemies
                    hit_enemy = None
                    for enemy in self.enemies.copy():
                        if enemy.rect().collidepoint(projectile[0]):
                            hit_enemy = enemy
                            break
                    if hit_enemy:
                        try:
                            self.enemies.remove(hit_enemy)
                        except Exception:
                            pass
                        try:
                            self.projectiles.remove(projectile)
                        except Exception:
                            pass
                        # spawn hit effects
                        for i in range(20):
                            angle = random.random() * math.pi * 2
                            speed = random.random() * 5
                            self.sparks.append(Spark(hit_enemy.rect().center, angle, 2 + random.random()))
                            self.particles.append(Particle(self, 'particle', hit_enemy.rect().center, velocity=[math.cos(angle + math.pi) * speed * 0.5, math.sin(angle + math.pi) * speed * 0.5], frame=random.randint(0,7)))
                        try:
                            self.sfx['hit'].play()
                        except Exception:
                            pass
                        continue
                    if self.tilemap.solid_check(projectile[0]):
                        try:
                            self.projectiles.remove(projectile)
                        except Exception:
                            pass
                        for i in range(4):
                            self.sparks.append(Spark(projectile[0], random.random() - 0.5 + (math.pi if projectile[1] > 0 else 0), 2 + random.random()))
                    elif projectile[2] > 360:
                        try:
                            self.projectiles.remove(projectile)
                        except Exception:
                            pass
                    elif abs(self.player.dashing) < 50:
                        if self.player.rect().collidepoint(projectile[0]):
                            # delegate hit handling to player (tracks hits and triggers death at max hits)
                            try:
                                self.projectiles.remove(projectile)
                            except Exception:
                                pass
                            self.player.take_hit()


                for spark in self.sparks.copy():
                    kill = spark.update()
                    spark.render(self.display, offset=render_scroll)
                    if kill:
                        try:
                            self.sparks.remove(spark)
                        except Exception:
                            pass

                display_mask = pygame.mask.from_surface(self.display)
                display_silhouette = display_mask.to_surface(setcolor=(0, 0, 0, 180), unsetcolor=(0, 0, 0, 0))
                for offset in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    self.display_2.blit(display_silhouette, offset)

                for particle in self.particles.copy():
                    kill = particle.update()
                    particle.render(self.display, offset=render_scroll)
                    if particle.type == 'left':
                        particle.pos[0] += math.sin(particle.animation.frame * 0.035) * 0.3
                    if kill:
                        try:
                            self.particles.remove(particle)
                        except Exception:
                            pass

            else:
                # paused: keep render_scroll stable so the current frame shows; create a no-op render_scroll
                render_scroll = (int(self.scroll[0]), int(self.scroll[1]))

            # transition effect (still draw even when paused)
            if self.transition:
                transition_surf = pygame.Surface(self.display.get_size())
                pygame.draw.circle(transition_surf, (255, 255, 255), (self.display.get_width() // 2, self.display.get_height() // 2), (30 - abs(self.transition)) * 8)
                transition_surf.set_colorkey((255, 255, 255)) # set it transparent by ignoring the white color
                self.display.blit(transition_surf, (0, 0))

            # composite logical display onto the fixed HUD display
            self.display_2.blit(self.display, (0, 0))

            # draw HUD (fixed to screen) on display_2 so it scales with the final window
            try:
                # prepare items: for kunai include cooldown ratio and image if available
                kunai_cd = 0
                if hasattr(self.player, 'kunai_cooldown_timer') and hasattr(self.player, 'kunai_cooldown'):
                    kunai_cd = self.player.kunai_cooldown_timer / max(1, self.player.kunai_cooldown)
                items = {
                    'shuriken': (self.player.shuriken_count, 0, self.assets.get('item/shuriken')),
                    'kunai': (self.player.kunai_count, kunai_cd, self.assets.get('item/kunai'))
                }
                # use new render_with_items to draw counts under healthbar (it handles image or fallback glyph)
                self.hud.render_with_items(self.display_2, self.player.hits, items)
            except Exception:
                pass

            # if paused, overlay a translucent layer with PAUSE
            if self.paused:
                try:
                    overlay = pygame.Surface(self.display_2.get_size(), pygame.SRCALPHA)
                    overlay.fill((0, 0, 0, 150))
                    self.display_2.blit(overlay, (0, 0))
                    pause_font = getattr(self, 'ui_font', pygame.font.Font(None, 36))
                    pause_surf = pause_font.render('PAUSE', True, (255, 255, 255))
                    self.display_2.blit(pause_surf, (self.display_2.get_width() // 2 - pause_surf.get_width() // 2, self.display_2.get_height() // 2 - pause_surf.get_height() // 2))
                except Exception:
                    pass

            screenshake_offset = (random.random() * self.screenshake - self.screenshake / 2, random.random() * self.screenshake - self.screenshake / 2)
            self.window.blit(pygame.transform.scale(self.display_2, self.window.get_size()), screenshake_offset)
            pygame.display.update()
            self.clock.tick(60)  # 60 Fps

if __name__ == "__main__":
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("Đăng nhập")

    game = Game()
    player_name = game.login_screen(screen)   # 👈 Hiện màn hình đăng nhập
    print(f"Xin chào, {player_name}!")         # Thông báo thành công

    game.run()  # 👈 Sau khi đăng nhập thì chạy game        