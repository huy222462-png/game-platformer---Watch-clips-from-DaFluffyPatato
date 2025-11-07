import math
import os
import random
import sys
import pygame


from scripts.particle import Particle
from scripts.spark import Spark
from scripts.utils import load_image, load_images, Animation
from scripts.entities import Player, Enemy, Boss
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
            'player/jump': Animation(load_images('entities/player/jump'), loop=False),
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

        # attempt to load alternate player character assets (ninja, samurai) if present
        # automatically discover character folders under data/images/entities
        self.character_dirs = {}  # map asset_prefix -> dir_name
        # per-character scale multipliers (applied relative to default player height)
        # increase samurai a bit so it looks larger than default after scaling
        self.character_scales = {
            'player_ninja': 1.0,
        }
    # reference collision height (pixels) used by default player animations
    # The default Player is created with size (8, 15) below; keep this in sync
        try:
            ent_path = os.path.join('data', 'images', 'entities')
            for entry in sorted(os.listdir(ent_path)):
                full = os.path.join(ent_path, entry)
                if not os.path.isdir(full):
                    continue
                if entry.lower() in ('player', 'enemy'):
                    continue
                # no special-case folders during discovery
                # create an asset prefix from folder name
                prefix = 'player_' + entry.lower()
                self.character_dirs[prefix] = entry
                # expected animation names (include attack/hurt if provided)
                actions = ['idle', 'run', 'jump', 'slide', 'wall_slide', 'attack', 'hurt']
                # find subdirs case-insensitively
                subs = {d.lower(): d for d in os.listdir(full) if os.path.isdir(os.path.join(full, d))}
                for act in actions:
                    if act in subs:
                        subdir = subs[act]
                        try:
                            imgs = load_images(f'entities/{entry}/{subdir}')
                            # if default player idle animation exists, scale this character's images
                            try:
                                default_idle = None
                                if 'player/idle' in self.assets and hasattr(self.assets['player/idle'], 'images'):
                                    default_idle = self.assets['player/idle'].images[0]
                                if default_idle is not None and imgs:
                                    # apply per-character scale multiplier
                                    mult = self.character_scales.get(prefix, 1.0)
                                    target_h = max(1, int(default_idle.get_height() * mult))
                                    scaled = []
                                    for im in imgs:
                                        if im.get_height() != target_h:
                                            new_w = int(im.get_width() * (target_h / im.get_height()))
                                            scaled.append(pygame.transform.scale(im, (new_w, target_h)))
                                        else:
                                            scaled.append(im)
                                    imgs = scaled
                            except Exception:
                                pass
                            # make attack/hurt/jump non-looping so they finish and don't lock the player
                            is_loop = not (act in ('attack', 'hurt', 'jump'))
                            self.assets[f'{prefix}/{act}'] = Animation(imgs, img_dur=6 if act == 'idle' else 4, loop=is_loop)
                        except Exception:
                            pass
                
                # ensure all characters have basic animations by copying from idle if missing
                if f'{prefix}/idle' in self.assets:
                    base_idle = self.assets[f'{prefix}/idle']
                    for required_action in ['wall_slide', 'jump', 'run']:
                        if f'{prefix}/{required_action}' not in self.assets:
                            try:
                                # copy idle animation but adjust img_dur and loop for the action
                                is_loop = not (required_action in ('attack', 'hurt', 'jump'))
                                self.assets[f'{prefix}/{required_action}'] = Animation(
                                    base_idle.images, 
                                    img_dur=4, 
                                    loop=is_loop
                                )
                            except Exception:
                                pass
        except Exception:
            # discovery is best-effort
            pass

        """
        SOUNDS
        """
        self.sfx = {
            'jump': pygame.mixer.Sound('data/sfx/jump.wav'),
            'dash': pygame.mixer.Sound('data/sfx/dash.wav'),
            'hit': pygame.mixer.Sound('data/sfx/hit.wav'),
            'shoot': pygame.mixer.Sound('data/sfx/shoot.wav'),
            # optional knife sound for samuraicut melee
            'knife': None,
            'ambience': pygame.mixer.Sound('data/sfx/ambience.wav'),
        }

        self.sfx['ambience'].set_volume(0.2)
        self.sfx['shoot'].set_volume(0.4)
        self.sfx['hit'].set_volume(0.7)
        self.sfx['dash'].set_volume(0.3)
        self.sfx['jump'].set_volume(0.3)
        # load knife sound if provided by user (non-fatal if missing)
        try:
            knife_sfx = pygame.mixer.Sound('data/sfx/knife.wav')
            if knife_sfx:
                self.sfx['knife'] = knife_sfx
                try:
                    self.sfx['knife'].set_volume(0.7)
                except Exception:
                    pass
        except Exception:
            # leave as None if missing
            pass

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
        # build a stable, sorted list of JSON map files (numerical order when possible)
        map_dir = os.path.join('data', 'maps')
        files = [f for f in os.listdir(map_dir) if f.lower().endswith('.json')]
        def _map_sort_key(fn):
            name = os.path.splitext(fn)[0]
            try:
                return int(name)
            except Exception:
                return name
        files.sort(key=_map_sort_key)
        self.map_files = files

        self.level = 0
        # clamp level and load first level (load_level handles errors)
        if self.map_files:
            self.level = max(0, min(self.level, len(self.map_files) - 1))
            self.load_level(self.level)

        self.screenshake = 0
        # pause flag (toggle with ESC during gameplay)
        self.paused = False


    def load_level(self, map_index):
        """Load a map by index into the sorted `self.map_files` list.

        This is more robust than assuming filenames are consecutive integers
        and avoids counting non-json files. If loading fails (invalid JSON,
        etc.) the function will log the error and fall back to an empty map
        so the game can continue instead of crashing.
        """
        # ensure we have a files list
        if not hasattr(self, 'map_files') or not self.map_files:
            # nothing to load
            self.tilemap.tilemap = {}
            self.tilemap.offgrid_tiles = []
            return

        # clamp the index
        map_index = max(0, min(map_index, len(self.map_files) - 1))
        map_path = os.path.join('data', 'maps', self.map_files[map_index])
        try:
            self.tilemap.load(map_path)
        except Exception as e:
            print(f"Failed to load map '{map_path}': {e}")
            # fallback to an empty map so the game won't crash; user can fix the JSON
            self.tilemap.tilemap = {}
            self.tilemap.offgrid_tiles = []

        self.leaf_spawners = []
        for tree in self.tilemap.extract([('large_decor', 2)], keep=True):
            self.leaf_spawners.append(pygame.Rect(4 + tree['pos'][0], 4 + tree['pos'][1], 23, 13))

        self.enemies = []
        # include variant 2 for boss spawners
        for spawner in self.tilemap.extract([('spawners', 0), ('spawners', 1), ('spawners', 2)]):
            if spawner['variant'] == 0:
                self.player.pos = spawner['pos']
                self.player.air_time = 0
                # reset player hits on (re)spawn
                try:
                    self.player.hits = 0
                except Exception:
                    pass
            elif spawner['variant'] == 1:
                self.enemies.append(Enemy(self, spawner['pos'], (8, 15)))
            elif spawner['variant'] == 2:
                # spawn a boss (bigger size and more HP)
                try:
                    boss = Boss(self, spawner['pos'], (32, 48), hp=12)
                    self.enemies.append(boss)
                except Exception:
                    # fallback to normal enemy if Boss construction fails
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
            for off in self.tilemap.offgrid_tiles:
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

    def character_select(self, screen):
        """Show a simple character selection screen. Returns chosen asset prefix string.

        The menu is generated from discovered character folders under data/images/entities.
        If no extra characters are found, the menu will offer the default 'player' entry.
        """
        font = getattr(self, 'ui_font', pygame.font.Font(None, 28))
        title = "Chọn nhân vật"
        # build choices from discovered character directories
        choices = []
        # include default player first
        choices.append(("default", 'player'))
        try:
            for prefix, dirname in self.character_dirs.items():
                # display label: capitalize dirname
                label = dirname.replace('_', ' ').title()
                choices.append((label, prefix))
        except Exception:
            pass

        while True:
            screen.fill((20, 20, 20))
            tw = font.render(title, True, (255, 255, 255))
            sw, sh = screen.get_size()
            screen.blit(tw, (sw//2 - tw.get_width()//2, sh//2 - 120))

            # draw two buttons
            btn_font = font
            btn_w, btn_h = 260, 48
            spacing = 24
            cx = sw // 2
            base_y = sh // 2 - 20

            btn_rects = []
            for i, (label, prefix) in enumerate(choices):
                x = cx - btn_w//2
                y = base_y + i * (btn_h + spacing)
                rect = pygame.Rect(x, y, btn_w, btn_h)
                btn_rects.append((rect, label, prefix))
                pygame.draw.rect(screen, (80, 80, 80), rect, border_radius=6)
                pygame.draw.rect(screen, (200, 200, 200), rect, 2, border_radius=6)
                # draw optional preview image if available (first frame)
                preview_drawn = False
                try:
                    key = prefix + '/idle'
                    if key in self.assets and hasattr(self.assets[key], 'images') and self.assets[key].images:
                        img = self.assets[key].images[0]
                        # scale preview to fit height
                        ph = btn_h - 8
                        pw = int(img.get_width() * (ph / img.get_height()))
                        preview = pygame.transform.scale(img, (pw, ph))
                        screen.blit(preview, (rect.x + 6, rect.y + 4))
                        # shift label right
                        lbl = btn_font.render(label, True, (255, 255, 255))
                        screen.blit(lbl, (rect.x + 12 + pw, rect.y + (btn_h - lbl.get_height()) // 2))
                        preview_drawn = True
                except Exception:
                    preview_drawn = False

                if not preview_drawn:
                    lbl = btn_font.render(label, True, (255, 255, 255))
                    screen.blit(lbl, (rect.x + (btn_w - lbl.get_width()) // 2, rect.y + (btn_h - lbl.get_height()) // 2))

            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return 'player'  # default
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mx, my = event.pos
                    for rect, label, prefix in btn_rects:
                        if rect.collidepoint((mx, my)):
                            # verify asset availability: look for prefix + '/idle' in assets
                            if prefix + '/idle' in self.assets:
                                return prefix
                            else:
                                # fallback to default player
                                return 'player'

    def apply_character_choice(self, prefix):
        """Recreate the player using the chosen asset prefix while preserving some state.

        If chosen prefix lacks assets, player will use default 'player'.
        """
        try:
            # preserve basic state
            old = getattr(self, 'player', None)
            pos = old.pos if old is not None else (70, 50)
            size = old.size if old is not None else (8, 15)
            hits = getattr(old, 'hits', 0)
            shurikens = getattr(old, 'shuriken_count', 0)
            kunaic = getattr(old, 'kunai_count', 0)

            # fallback if assets missing
            if prefix + '/idle' not in self.assets:
                prefix = 'player'

            # create new player
            from scripts.entities import Player
            self.player = Player(self, pos, size, asset_prefix=prefix)
            # apply visual scale if available
            try:
                self.player.visual_scale = float(self.character_scales.get(prefix, 1.0))
            except Exception:
                self.player.visual_scale = 1.0
            # apply instance visual_scale (no per-character forced test scaling)
            try:
                self.player.visual_scale = float(self.character_scales.get(prefix, 1.0))
            except Exception:
                self.player.visual_scale = 1.0
            # use the raw asset animation (no automatic per-instance rescaling)
            try:
                key = prefix + '/idle'
                if key in self.assets:
                    try:
                        self.player.animation = self.assets[key].copy()
                    except Exception:
                        self.player.animation = self.assets[key]
            except Exception:
                pass
            # reset anim_offset to default (user will edit images manually)
            try:
                self.player.anim_offset = (-3, -3)
            except Exception:
                pass
            # force-set the idle animation from assets if available (ensure correct sprite used)
            try:
                key = prefix + '/idle'
                if key in self.assets:
                    try:
                        self.player.animation = self.assets[key].copy()
                    except Exception:
                        self.player.animation = self.assets[key]
                    # adjust collision size to match visual asset height so wall_slide and
                    # other collision-based states align with the sprite dimensions
                    try:
                        # prefer to compare against the default player's idle image
                        default_idle_img = None
                        if 'player/idle' in self.assets and hasattr(self.assets['player/idle'], 'images'):
                            default_idle_img = self.assets['player/idle'].images[0]
                        chosen_img = None
                        if hasattr(self.player.animation, 'images'):
                            chosen_img = self.player.animation.images[0]
                        elif hasattr(self.player.animation, 'get_width'):
                            chosen_img = self.player.animation
                        if default_idle_img is not None and chosen_img is not None:
                            # scale factor between chosen and default idle image heights
                            scale_factor = float(chosen_img.get_height()) / float(default_idle_img.get_height())
                            old_size = size
                            try:
                                old_size = tuple(old.size) if hasattr(old, 'size') else size
                            except Exception:
                                old_size = size
                            new_w = max(1, int(old_size[0] * scale_factor))
                            new_h = max(1, int(old_size[1] * scale_factor))
                            # keep the player's feet grounded by moving the y position up by the height delta
                            try:
                                self.player.pos[1] = float(self.player.pos[1]) - (new_h - old_size[1])
                            except Exception:
                                try:
                                    self.player.pos = [self.player.pos[0], self.player.pos[1] - (new_h - old_size[1])]
                                except Exception:
                                    pass
                            self.player.size = (new_w, new_h)
                            # small vertical anim offset tweak to center the sprite better
                            try:
                                self.player.anim_offset = (self.player.anim_offset[0], int(self.player.anim_offset[1] - (chosen_img.get_height() - default_idle_img.get_height()) / 2))
                            except Exception:
                                pass
                    except Exception:
                        pass
            except Exception:
                pass
            # restore state
            try:
                self.player.hits = hits
                self.player.shuriken_count = shurikens
                self.player.kunai_count = kunaic
            except Exception:
                pass
            # configure attack mode: default to ranged (no per-character samurai behavior)
            try:
                self.player.attack_mode = 'ranged'
                # if the chosen character is the samuraicut variant, map primary attack to kunai
                try:
                    if 'samuraicut' in prefix.lower():
                        # set primary attack to sword (melee) for samuraicut and ensure it's usable without pickups
                        self.player.primary_attack_override = 'sword'
                        # no item pickups required for sword; make sure counts aren't set to force ranged
                        try:
                            if hasattr(self.player, 'kunai_count'):
                                # do not grant kunai by default for samuraicut
                                self.player.kunai_count = 0
                        except Exception:
                            pass
                except Exception:
                    pass
            except Exception:
                pass
            # update HUD to reflect new player max hits
            try:
                self.hud = HealthBar(max_hits=self.player.max_hits, pos=(4,4), size=(60,12))
            except Exception:
                pass
            self.selected_character = prefix
        except Exception:
            # best-effort fallback
            self.selected_character = 'player'

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
                        # primary attack (ranged or melee depending on chosen character)
                        try:
                            used = self.player.primary_attack()
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
                # handle mouse clicks while paused (map window -> display_2 coords)
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if self.paused and event.button == 1:
                        # map mouse (window) coords into display_2 coordinates
                        wx, wy = self.window.get_size()
                        dx, dy = self.display_2.get_size()
                        mx, my = event.pos
                        # scale from window to logical display_2
                        if wx and wy:
                            sx = mx * (dx / wx)
                            sy = my * (dy / wy)
                        else:
                            sx, sy = mx, my

                        # compute same button layout as drawn below
                        try:
                            pause_font = getattr(self, 'ui_font', pygame.font.Font(None, 24))
                            btn_w, btn_h = 120, 28
                            spacing = 12
                            center_x = dx // 2
                            base_y = dy // 2 + 24
                            play_rect = pygame.Rect(center_x - btn_w - spacing//2, base_y, btn_w, btn_h)
                            exit_rect = pygame.Rect(center_x + spacing//2, base_y, btn_w, btn_h)
                            if play_rect.collidepoint((sx, sy)):
                                # restart current level and unpause
                                self.load_level(self.level)
                                self.paused = False
                                # restore ambience volume hint
                                try:
                                    self.sfx.get('ambience', pygame.mixer.Sound('data/sfx/ambience.wav')).set_volume(0.2)
                                except Exception:
                                    pass
                            if exit_rect.collidepoint((sx, sy)):
                                pygame.quit()
                                sys.exit()
                        except Exception:
                            pass

            # If paused, skip gameplay updates but still render the current frame and overlay
            if not self.paused:
                self.screenshake = max(0, self.screenshake - 1)

                if not len(self.enemies):  # killed all the enemies
                    self.transition += 1
                    if self.transition > 30:
                        # advance to next map using the precomputed json list
                        if hasattr(self, 'map_files') and self.map_files:
                            self.level = min(self.level + 1, len(self.map_files) - 1)
                        else:
                            self.level = self.level + 1
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
                            # delegate hit handling to the enemy (Boss can take multiple hits)
                            dead = True
                            try:
                                if hasattr(hit_enemy, 'take_hit'):
                                    dead = hit_enemy.take_hit()
                                else:
                                    dead = True
                            except Exception:
                                dead = True
                            # remove projectile regardless
                            try:
                                self.projectiles.remove(projectile)
                            except Exception:
                                pass

                            if dead:
                                try:
                                    self.enemies.remove(hit_enemy)
                                except Exception:
                                    pass
                                # spawn hit effects for death
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

                # draw simple buttons: Play again (restart level) and Exit
                try:
                    # smaller font for buttons
                    btn_font = getattr(self, 'ui_font', pygame.font.Font(None, 24))
                    btn_w, btn_h = 120, 28
                    spacing = 12
                    center_x = self.display_2.get_width() // 2
                    base_y = self.display_2.get_height() // 2 + 24

                    play_rect = pygame.Rect(center_x - btn_w - spacing//2, base_y, btn_w, btn_h)
                    exit_rect = pygame.Rect(center_x + spacing//2, base_y, btn_w, btn_h)

                    # button background
                    pygame.draw.rect(self.display_2, (80, 80, 80), play_rect, border_radius=4)
                    pygame.draw.rect(self.display_2, (80, 80, 80), exit_rect, border_radius=4)
                    # button border
                    pygame.draw.rect(self.display_2, (200, 200, 200), play_rect, 2, border_radius=4)
                    pygame.draw.rect(self.display_2, (200, 200, 200), exit_rect, 2, border_radius=4)

                    # labels
                    play_label = btn_font.render('Play again', True, (255, 255, 255))
                    exit_label = btn_font.render('Exit', True, (255, 255, 255))
                    self.display_2.blit(play_label, (play_rect.x + (btn_w - play_label.get_width()) // 2, play_rect.y + (btn_h - play_label.get_height()) // 2))
                    self.display_2.blit(exit_label, (exit_rect.x + (btn_w - exit_label.get_width()) // 2, exit_rect.y + (btn_h - exit_label.get_height()) // 2))
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

    # after successful login, show character selection and apply choice
    try:
        choice = game.character_select(screen)
        game.apply_character_choice(choice)
    except Exception:
        pass

    game.run()  # 👈 Sau khi đăng nhập thì chạy game